# ///////////////////////////////////////////////////////////////
#
# BY: David Rosewater
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.3
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

import sys
import json
import time
import io
from contextlib import redirect_stdout
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QProgressBar
from PyQt5.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot, QThreadPool
import ast
import pandas as pd
import numpy as np 
from scipy.interpolate import interp1d
from pyomo.environ import *
from datetime import timedelta
import matplotlib.pyplot as plt
import csv
from functools import cmp_to_key
import os


class BTMAalysisSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    status = pyqtSignal(str)
    error = pyqtSignal(tuple)
    results = pyqtSignal(str)
    progress = pyqtSignal(int)

class BTMAalysisManager(QRunnable):    
    MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December']

    def __init__(self,analysis_inputs) -> None:
        super().__init__()
        '''analysis_inputs = {"grid_load_and_limits" : self.grid_load_and_limits, \
                           "MOER_Signal" : self.MOER_Signal, \
                           "selected_utility_rate" : self.selected_utility_rate, \
                           "system_data" : self.system_data, \
                           "solar_site_data" : self.solar_site_data}'''
        self.analysis_inputs = analysis_inputs
        #self.results_widget = results_widget
        #self.output_widget = output_widget
        #self.progress_widget = progress_widget

        self.analysis_name = self.analysis_inputs['analysis_configuration']['analysis_name']   
        self.timestep = int(self.analysis_inputs['analysis_configuration']['timestep'])
        self.carbon_weight = float(self.analysis_inputs['analysis_configuration']['carbon_weight'])
        self.net_meter_price = float(self.analysis_inputs['analysis_configuration']['net_meter_price'])
        self.results = {}
        
        self._running = True
        self.month_number_to_analyze = 0
        self.signals = BTMAalysisSignals()

        pass

    @pyqtSlot()
    def run(self):
        for self.month_number_to_analyze in range(12):
            if self._running:
                month = self.MONTH_NAMES[self.month_number_to_analyze]
                try:
                    self.signals.status.emit("Prepairing data for {month} ".format(month=month))
                    self.load_single_month(self.month_number_to_analyze+1)
                    self.signals.status.emit("Starting opptimization ... ")
                    self.optimize_dispatch()
                    self.signals.progress.emit(int(self.month_number_to_analyze+1))
                except Exception as e:
                    print('Something whent wrong with {month} : {error}'.format(month=month,error=e))
                    self.signals.status.emit('Something whent wrong with {month} : {error}'.format(month=month,error=e))
        self.signals.finished.emit()  # Done
        pass

    def stop(self):
        self._running = False

    def load_single_month(self,month_number):
        ''' This function loads all the imput signals for a single month defined by month_number'''
        self.month_number = month_number
        
        with open(self.analysis_inputs['solar_site_data']['Data File Path'],'r') as csvfile:
            # Create a CSV reader object
            csv_reader = csv.reader(csvfile)
            
            # Read the first row
            first_row = next(csv_reader)

            if first_row[0] == 'ï»¿PVWatts Hourly PV Performance Data':
                print('PV data from PVWatts')
                self.pv_signal = pd.read_csv(self.analysis_inputs['solar_site_data']['Data File Path'], skiprows=31)
                # Combine Month, Day, and Hour into a single datetime column
                self.pv_signal['datetime'] = pd.to_datetime(self.pv_signal[['Month', 'Day', 'Hour']].astype(str).agg('-'.join, axis=1), format='%m-%d-%H')
                # Drop the original Month, Day, and Hour columns
                self.pv_signal = self.pv_signal.drop(columns=['Month', 'Day', 'Hour'])  # Rename blank column
                self.pv_signal['AC System Output (W)'] = self.pv_signal['AC System Output (W)']/1000  # convert into kW
                self.pv_signal.rename(columns={'AC System Output (W)': 'PV Power (kW)'}, inplace=True)
                self.pv_signal = self.pv_signal[self.pv_signal['datetime'].dt.month == self.month_number]
                self.pv_signal['time_diff'] = self.pv_signal['datetime'].diff()  # Rename blank column
                self.dt_pv = self.pv_signal['time_diff'].mean()
            if first_row[0] == 'Source':
                print('PV data from automatic download')
                self.pv_signal = pd.read_csv(self.analysis_inputs['solar_site_data']['Data File Path'])
                pv_time_stamp_key = self.pv_signal.keys()[0]
                self.pv_signal.rename(columns={pv_time_stamp_key: 'datetime'}, inplace=True)  # Rename blank column
                self.pv_signal['datetime'] = pd.to_datetime(self.pv_signal['datetime'])
                self.pv_signal['PV Power (MW)'] = self.pv_signal['PV Power (MW)']*1000  # convert into kW
                self.pv_signal.rename(columns={'PV Power (MW)': 'PV Power (kW)'}, inplace=True)
                self.pv_signal.set_index('datetime', inplace=True)
                self.pv_signal = self.pv_signal[self.pv_signal['datetime'].dt.month == self.month_number]
                self.pv_signal['time_diff'] = self.pv_signal['datetime'].diff()  # Rename blank column
                self.dt_pv = self.pv_signal['time_diff'].mean()
        MOER_data_path = 'data/MOER/' + self.analysis_inputs['MOER_Signal']['Grid Region'] + '/'
        self.moer_signal = pd.read_csv(MOER_data_path + self.analysis_inputs['MOER_Signal']['Selected Files'][self.month_number-1])
        moer_time_stamp_key = self.moer_signal.keys()[0]
        self.moer_signal.rename(columns={moer_time_stamp_key: 'datetime'}, inplace=True)  # Rename 'timestamp' column
        self.moer_signal['datetime'] = pd.to_datetime(self.moer_signal['datetime'])
        self.moer_signal['time_diff'] = self.moer_signal['datetime'].diff()
        self.moer_signal.set_index('datetime', inplace=True)
        self.dt_moer = self.moer_signal['time_diff'].mean()

        # Read the Electrcial Load Singal from the CSV file and Convert the 'Date' column to 'datetime'
        self.month_name = self.MONTH_NAMES[self.month_number-1]
        self.load_signal = pd.read_csv(self.analysis_inputs['grid_load_and_limits']['saved_electrical_load_files'][self.month_name]['File'])
        load_time_stamp_key = self.load_signal.keys()[0]
        self.load_signal.rename(columns={load_time_stamp_key: 'datetime'}, inplace=True)  # Rename 'Date' column
        self.load_signal['datetime'] = pd.to_datetime(self.load_signal['datetime'])
        self.load_signal['time_diff'] = self.load_signal['datetime'].diff()
        self.dt_load = self.load_signal['time_diff'].mean()
        # change the kWh signal in electrical load into a kW signal.
        time_in_hours = (self.dt_load.total_seconds() / 3600.0)
        self.load_signal['kW'] = self.load_signal['KWH'] / time_in_hours
        
        demandweakdaydata = ast.literal_eval(self.analysis_inputs['selected_utility_rate']['demandweekdayschedule'])[self.month_number-1]
        demandweakenddata = ast.literal_eval(self.analysis_inputs['selected_utility_rate']['demandweekendschedule'])[self.month_number-1]
        energyweakdaydata = ast.literal_eval(self.analysis_inputs['selected_utility_rate']['energyweekdayschedule'])[self.month_number-1]
        energyweakenddata = ast.literal_eval(self.analysis_inputs['selected_utility_rate']['energyweekendschedule'])[self.month_number-1]

       # Loop through each row in the DataFrame
        for index, row in self.load_signal.iterrows():
            # Determine if the day is a weekday or weekend
            
            if row['datetime'].weekday() < 5:  # Monday to Friday are 0-4
                # Weekday
                hour = row['datetime'].hour
                demand_rate_index = demandweakdaydata[hour]
                energy_rate_index = energyweakdaydata[hour]
            else:
                # Weekend
                hour = row['datetime'].hour
                demand_rate_index = demandweakenddata[hour]
                energy_rate_index = energyweakenddata[hour]

            # Get the corresponding rate from the analysis inputs
            demand_rate_key = 'demandratestructure/period{index}/tier0rate'.format(index=demand_rate_index)
            demand_rate_adj_key = 'demandratestructure/period{index}/tier0adj'.format(index=demand_rate_index)
            if demand_rate_key in self.analysis_inputs['selected_utility_rate']:
                self.load_signal.at[index, 'Demand Rate'] = self.analysis_inputs['selected_utility_rate'][demand_rate_key] 
                if demand_rate_adj_key in self.analysis_inputs['selected_utility_rate']:
                    self.load_signal.at[index, 'Demand Rate'] = self.load_signal.at[index, 'Demand Rate'] + self.analysis_inputs['selected_utility_rate'][demand_rate_adj_key]  

            energy_rate_key = 'energyratestructure/period{index}/tier0rate'.format(index=energy_rate_index)
            energy_rate_adj_key = 'energyratestructure/period{index}/tier0adj'.format(index=energy_rate_index)
            if energy_rate_key in self.analysis_inputs['selected_utility_rate']:
                self.load_signal.at[index, 'Energy Rate'] = self.analysis_inputs['selected_utility_rate'][energy_rate_key] 
                if energy_rate_adj_key in self.analysis_inputs['selected_utility_rate']:
                    self.load_signal.at[index, 'Energy Rate'] = self.load_signal.at[index, 'Energy Rate'] + self.analysis_inputs['selected_utility_rate'][energy_rate_adj_key]  
        self.load_signal.set_index('datetime', inplace=True)

        
        #housekeeping
        self.load_signal.drop('time_diff', axis=1, inplace=True)
        self.load_signal.drop('KWH', axis=1, inplace=True)

        self.demand_rate = self.load_signal[['Demand Rate']].copy() 
        self.energy_rate = self.load_signal[['Energy Rate']].copy() 
        self.load_signal.drop('Demand Rate', axis=1, inplace=True)
        self.load_signal.drop('Energy Rate', axis=1, inplace=True)
        
        self.pv_signal.drop('time_diff', axis=1, inplace=True)
        self.moer_signal.drop('time_diff', axis=1, inplace=True)

        self._interpolate_signals()

    def _interpolate_signals(self):
        # Interpolate self.load_signal (15 min) and self.pv_signal (1 hour) to 5 min
        self.dt = self.timestep/60

        print(self.dt_pv)
        #print(len(self.moer_signal)*5/60)

        original_time_load_signal = np.arange(0, len(self.load_signal) * 15/60, 15/60)  # Time in hours
        original_time_energy_rate = np.arange(0, len(self.energy_rate) * 15/60, 15/60)  # Time in hours
        original_time_demand_rate= np.arange(0, len(self.demand_rate) * 15/60, 15/60)  # Time in hours
        
        if self.dt_pv == timedelta(minutes=30):
            original_time_pv_signal = np.arange(0, len(self.pv_signal) * 30/60, 30/60)  # Time in hours
        elif self.dt_pv == timedelta(hours=1):
            original_time_pv_signal = np.arange(0, len(self.pv_signal) * 60/60, 60/60)  # Time in hours
        
        original_time_moer_signal = np.arange(0, len(self.moer_signal) * 5/60, 5/60)  # Time in hours
        new_time = np.arange(0, len(self.moer_signal)*5/60, self.dt)  # Time in hours

        if len(original_time_energy_rate) >= len(new_time):        
            self.energy_rate = np.interp(new_time, original_time_energy_rate, list(self.energy_rate['Energy Rate'])).tolist()
        elif len(original_time_energy_rate) < len(new_time):        
            self.energy_rate = self.zero_order_hold(new_time, original_time_energy_rate, list(self.energy_rate['Energy Rate'])).tolist()

        if len(original_time_energy_rate) >= len(new_time):        
            self.demand_rate = np.interp(new_time, original_time_demand_rate, list(self.demand_rate['Demand Rate'])).tolist()
        elif len(original_time_energy_rate) < len(new_time):        
            self.demand_rate = self.zero_order_hold(new_time, original_time_demand_rate, list(self.demand_rate['Demand Rate'])).tolist()

        self.load_signal = np.interp(new_time, original_time_load_signal, list(self.load_signal['kW'])).tolist()
        self.pv_signal   = np.interp(new_time, original_time_pv_signal, list(self.pv_signal['PV Power (kW)'])).tolist()
        self.moer_signal = np.interp(new_time, original_time_moer_signal, list(self.moer_signal['MOER version 2.0'])).tolist()
        '''
        # Create subplots
        fig, axs = plt.subplots(5, 1, figsize=(12, 8), sharex=True)

        # Plot KWH
        axs[0].plot([i for i in range(len(self.load_signal))], self.load_signal, color='blue', label='KWH', linewidth=2)
        axs[0].set_title('Load Signal (KWH)')
        axs[0].set_ylabel('kW')
        axs[0].legend()
        axs[0].grid()

        # Plot Rate
        axs[1].plot([i for i in range(len(self.demand_rate))], self.demand_rate, color='orange', label='Demand Price', linewidth=2)
        axs[1].set_title('Demand Rate Schedule')
        axs[1].set_ylabel('Rate ($/kW)')
        axs[1].legend()
        axs[1].grid()

        axs[2].plot([i for i in range(len(self.energy_rate))],  self.energy_rate, color='green', label='Energy Price', linewidth=2)
        axs[2].set_title('Energy Rate Schedule')
        axs[2].set_ylabel('Rate ($/kWh)')
        axs[2].legend()
        axs[2].grid()

        axs[3].plot([i for i in range(len(self.pv_signal))],  self.pv_signal, color='yellow', label='PV', linewidth=2)
        axs[3].set_title('pv_signal')
        axs[3].set_ylabel('Power (kW)')
        axs[3].legend()
        axs[3].grid()

        axs[4].plot([i for i in range(len(self.moer_signal))],  self.moer_signal, color='black', label='MOER', linewidth=2)
        axs[4].set_title('moer_signal')
        axs[4].set_ylabel('Rate (ton/MWh)')
        axs[4].legend()
        axs[4].grid()
        plt.show()'''


    def zero_order_hold(self, x, xp, yp, left=np.nan, assume_sorted=False):
        """
        Interpolates a function by holding at the most recent value.

        Parameters
        ----------
        x : array_like
            The x-coordinates at which to evaluate the interpolated values.
        xp: 1-D sequence of floats
            The x-coordinates of the data points, must be increasing if argument period is not specified. Otherwise, xp is internally sorted after normalizing the periodic boundaries with xp = xp % period.
        yp: 1-D sequence of float or complex
            The y-coordinates of the data points, same length as xp.
        left: int or float, optional, default is np.nan
            Value to use for any value less that all points in xp
        assume_sorted : bool, optional, default is False
            Whether you can assume the data is sorted and do simpler (i.e. faster) calculations

        Returns
        -------
        y : float or complex (corresponding to fp) or ndarray
            The interpolated values, same shape as x.

        Notes
        -----
        #.  Written by DStauffman in July 2020.

        """
        # force arrays
        x  = np.asanyarray(x)
        xp = np.asanyarray(xp)
        yp = np.asanyarray(yp)
        # find the minimum value, as anything left of this is considered extrapolated
        xmin = xp[0] if assume_sorted else np.min(xp)
        # check that xp data is sorted, if not, use slower scipy version
        if assume_sorted or np.all(xp[:-1] <= xp[1:]):
            ix = np.searchsorted(xp, x, side='right') - 1
            return np.where(np.asanyarray(x) < xmin, left, yp[ix])
        func = interp1d(xp, yp, kind='zero', fill_value='extrapolate', assume_sorted=False)
        return np.where(np.asanyarray(x) < xmin, left, func(x))

    def plot_load_and_rate_signal(self):
        #print(self.load_signal)

        # Create subplots
        fig, axs = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

        # Plot KWH
        axs[0].plot(self.load_signal.index, self.load_signal['kW'], color='blue', label='KWH', linewidth=2)
        axs[0].set_title('Load Signal (KWH)')
        axs[0].set_ylabel('kW')
        axs[0].legend()
        axs[0].grid()

        # Plot Rate
        axs[1].plot(self.demand_rate.index, self.demand_rate['Demand Rate'], color='orange', label='Demand Price', linewidth=2)
        axs[1].set_title('Demand Rate Schedule')
        axs[1].set_ylabel('Rate ($/kW)')
        axs[1].legend()
        axs[1].grid()

        axs[2].plot(self.energy_rate.index, self.energy_rate['Energy Rate'], color='green', label='Energy Price', linewidth=2)
        axs[2].set_title('Energy Rate Schedule')
        axs[2].set_ylabel('Rate ($/kWh)')
        axs[2].legend()
        axs[2].grid()

        # Set common x-axis label
        plt.xlabel('Date and Time')

        # Adjust layout
        plt.tight_layout()

        # Show the plot
        plt.show()
                
        return True

    def optimize_dispatch(self):
        # model parameter initilization
        self.n = len(self.moer_signal) 
        self.nS = len(self.analysis_inputs['system_data'])
        

        self.MOER = [self.moer_signal[i]/907.2 for i in range(len(self.moer_signal))] #convert to tons/ kWh
        #print(self.analysis_inputs['solar_site_data'])
        UTC_points_shift = int(-float(self.analysis_inputs['solar_site_data']['Local Time Zone']) / self.dt)
        #print(UTC_points_shift)
        for _ in range(UTC_points_shift):# this operation corrects for the fact that MOER is reported in UTC - 0 time while all other signals are in local time. 
            first_element = self.MOER.pop(0)  # Remove the first element
            self.MOER.append(first_element)    # Append it to the end of the list

        self.PV = self.pv_signal
        gap = len(self.MOER) - len(self.PV)
        self.PV.extend(list([self.PV[-1] for i in range(gap)]))

        self.LOAD = self.load_signal
        gap = len(self.MOER) - len(self.LOAD)
        self.LOAD.extend([self.LOAD[-1] for i in range(gap)])
        self.DEMAND_PRICE = self.demand_rate
        self.DEMAND_PRICE.extend([self.DEMAND_PRICE[-1] for i in range(gap)])
        self.unique_demand_prices = set(self.DEMAND_PRICE)

        self.ENERGY_PRICE = self.energy_rate
        self.ENERGY_PRICE.extend([self.ENERGY_PRICE[-1] for i in range(gap)])
        #print('maximum load -------------------------------------------------------------------- = ' + str(max(self.LOAD)))
        
        #model predictive control
        m =  ConcreteModel("MPC")
        # Define the time set 
        m.time = Set(initialize=range(self.n))  
        m.soc_time = Set(initialize=range(self.n+1))  
        flat_rate = self.analysis_inputs['selected_utility_rate']['flatdemandstructure/period0/tier0rate']
        if 0.0 in self.unique_demand_prices:
            self.unique_demand_prices.remove(0.0)  # Remove 0.0 from the set
        #    self.unique_demand_prices.add(flat_rate)    # Add the flat demand rate structure in place of where the TOU demand rate is 0.0   
        m.subsets = {price: [t for t in range(self.n) if self.DEMAND_PRICE[t] == price] for price in self.unique_demand_prices}
        m.Prices = Set(initialize=self.unique_demand_prices)     
            
        
        #print("---------------------------------------------------------------------------------" + str([price  for price in self.unique_demand_prices]))
        #self.DEMAND_PRICE = [price if price != 0.0 else flat_rate for price in self.DEMAND_PRICE]

        # Define the systems set
        m.Systems = Set(initialize=list(self.analysis_inputs['system_data'].keys()))
       
        m.energy_capacity = Param(m.Systems, initialize={s: self.analysis_inputs['system_data'][s]['Energy Capacity']*1000 for s in list(self.analysis_inputs['system_data'].keys())}) # convert from MWh to kWh by multiplying by 1000
        m.rte = Param(m.Systems, initialize={s: self.analysis_inputs['system_data'][s]['Round-Trip-Efficiency']/100 for s in list(self.analysis_inputs['system_data'].keys())}) # convert from % to decimal efficiency
        m.self_discharge = Param(m.Systems, initialize={s: self.analysis_inputs['system_data'][s]['Self-Discharge Rate'] for s in list(self.analysis_inputs['system_data'].keys())})
        #print({s: self.analysis_inputs['system_data'][s]['Energy Capacity']*1000  for s in list(self.analysis_inputs['system_data'].keys())})
        #print({s: self.analysis_inputs['system_data'][s]['Round-Trip-Efficiency'] for s in list(self.analysis_inputs['system_data'].keys())})

        ADis = {}
        bDis = {}
        ACha = {}
        bCha = {}

        for s in list(self.analysis_inputs['system_data'].keys()):
            for l in self.analysis_inputs['system_data'][s]['Dynamic Power Limits']:
                #print(self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l])
                if self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l]['Region'] == 'Discharge':
                    ADis[s,l] = self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l]['Slope'] * 1000 # convert from MW/% to kW/% by multiplying by 1000
                    bDis[s,l] = self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l]['Intercept'] * 1000 # convert from MW to kW by multiplying by 1000
                else:  # if self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l]['Region'] == 'Charge':
                    ACha[s,l] = self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l]['Slope'] * 1000 # convert from MW/% to kW/% by multiplying by 1000
                    bCha[s,l] = self.analysis_inputs['system_data'][s]['Dynamic Power Limits'][l]['Intercept'] * 1000 # convert from MW to kW by multiplying by 1000
            
        highest_limit_number = (max(max([int(list(ADis.keys())[i][1].split(' ')[1]) for i in range(len(list(ADis.keys())))]), max([int(list(ACha.keys())[i][1].split(' ')[1]) for i in range(len(list(ACha.keys())))])))
        # Define the set of dynamic limits 
        m.Limits = Set(initialize=['Limit {limit_number}'.format(limit_number=l+1) for l in range(highest_limit_number)])
        #print(['Limit {limit_number}'.format(limit_number=l+1) for l in range(highest_limit_number)])
        
        # Define the state variables
        m.soc = Var(m.Systems,m.soc_time,bounds=(0.0,100.0), within=NonNegativeReals)
        m.p_charge = Var(m.Systems,m.time, within=NonNegativeReals)
        m.p_discharge = Var(m.Systems,m.time, within=NonPositiveReals)
        m.pv_curtailment = Var(m.time,domain=NonNegativeReals,bounds=(0,max(self.PV)))#PV Curtailment 
        m.pv_only_curtailment = Var(m.time,domain=NonNegativeReals,bounds=(0,max(self.PV)))# PV Curtailment when the Energy Storage is not considered 
        m.peak_demand = Var(m.Prices,domain=NonNegativeReals) # 
        m.flat_rate_peak_demand = Var(domain=NonNegativeReals) # 
        m.Ce = Var(domain=NonNegativeReals) # 
        m.Cn = Var(domain=Reals) # 
        m.Cg = Var(domain=Reals) # 

        def obj_expression(m):
            return m.Ce + m.Cg + m.Cn +\
                    sum([m.pv_only_curtailment[t] for t in m.time]) + \
                    sum([m.pv_curtailment[t] for t in m.time]) + \
                    m.flat_rate_peak_demand*flat_rate + \
                    sum([m.peak_demand[p]*p for p in m.Prices]) #+ \
                    #100*sum([100 - m.soc[s, self.n] for s in m.Systems])
        
        m.OBJ = Objective(rule=obj_expression, sense=minimize)

        #Add a net metering value for energy > load 

        def energy_cost_rule(m):
            return m.Ce >=  sum([self.ENERGY_PRICE[t]*(self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] + sum([m.p_discharge[s, t] + m.p_charge[s, t] for s in m.Systems])) for t in m.time]) 
        m.energy_cost =  Constraint(rule=energy_cost_rule)

        def net_meter_cost_rule(m):
            # In post processing the net-metering cost is only applyed when net load is negitive. However, this is a non-convex consraint that could lead to local minima when net_meter_price > min(ENERGY_PRICE) 
            return  m.Cn == self.net_meter_price *sum([(self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] + sum([m.p_discharge[s, t] + m.p_charge[s, t] for s in m.Systems])) for t in m.time])
        m.net_meter_cost =  Constraint(rule=net_meter_cost_rule)

        def ghg_cost_rule(m):
            return m.Cg >=  sum([(self.carbon_weight*self.MOER[t])*(self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] + sum([m.p_discharge[s, t] + m.p_charge[s, t] for s in m.Systems])) for t in m.time])
        m.ghg_cost =  Constraint(rule=ghg_cost_rule)

        def soc_constraint_rule(m, s, t):
            if t == 0:
                #set the initial and fianl SOC to it's Max SOC
                return m.soc[s, t] == self.analysis_inputs['system_data'][s]['Min SOC'] 
            else:
                return m.soc[s, t] - m.soc[s, t-1] ==  100.0 * self.dt * (
                        m.p_discharge[s, t-1] + m.p_charge[s, t-1]*m.rte[s] + m.self_discharge[s]) / m.energy_capacity[s]
        m.soc_constraints = Constraint(m.Systems, m.soc_time, rule=soc_constraint_rule)

        def soc_end_rule(m, s):
            return m.soc[s, self.n] == self.analysis_inputs['system_data'][s]['Max SOC'] 
        #m.soc_end = Constraint(m.Systems, rule=soc_end_rule)

        def dis_rule(m, s, t, l):
            if (s, l) in ADis.keys():
                return m.p_discharge[s, t] >= ADis[s, l]*m.soc[s, t] + bDis[s, l]
            else:
                return Constraint.Skip
        m.dis= Constraint(m.Systems, m.time, m.Limits, rule=dis_rule)

        def cha_rule(m, s, t, l):
            if (s, l) in ACha.keys():
                return m.p_charge[s, t] <= ACha[s, l]*m.soc[s, t] + bCha[s, l]
            else:
                return Constraint.Skip
        m.cha= Constraint(m.Systems, m.time, m.Limits, rule=cha_rule)

        def max_discharge_power_rule(m, s, t):
            return m.p_discharge[s, t] >= -self.analysis_inputs['system_data'][s]['Discharge Power Limit'] *1000  # convert from MW to kW by multiplying by 1000
        m.max_discharge_power = Constraint(m.Systems, m.time, rule=max_discharge_power_rule)

        def max_charge_power_rule(m, s, t):
            return m.p_charge[s, t] <= self.analysis_inputs['system_data'][s]['Charge Power Limit'] *1000  # convert from MW to kW by multiplying by 1000
        m.max_charge_power = Constraint(m.Systems, m.time, rule=max_charge_power_rule)

        def max_soc_rule(m, s, t):
            return m.soc[s, t] <= self.analysis_inputs['system_data'][s]['Max SOC'] 
        m.max_soc = Constraint(m.Systems, m.time, rule=max_soc_rule)

        def min_soc_rule(m, s, t):
            return m.soc[s, t] >= self.analysis_inputs['system_data'][s]['Min SOC']  
        m.min_soc = Constraint(m.Systems, m.time, rule=min_soc_rule)

        def power_export_limit_rule(m, t):
            return self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] + sum([m.p_charge[s, t] + m.p_discharge[s, t] for s in m.Systems])  >= -self.analysis_inputs['grid_load_and_limits']['powerExportLimitInput'] *1000  # convert from MW to kW by multiplying by 1000
        m.power_export_limit = Constraint(m.time, rule=power_export_limit_rule)

        def power_import_limit_rule(m, t):
            return self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] +  sum([m.p_charge[s, t] + m.p_discharge[s, t] for s in m.Systems]) <= self.analysis_inputs['grid_load_and_limits']['powerImportLimitInput'] *1000  # convert from MW to kW by multiplying by 1000
        m.power_import_limit = Constraint(m.time, rule=power_import_limit_rule)

        def power_export_limit_rule_pv_only(m, t):
            return self.LOAD[t] - self.PV[t] + m.pv_only_curtailment[t] >= -self.analysis_inputs['grid_load_and_limits']['powerExportLimitInput'] *1000  # convert from MW to kW by multiplying by 1000
        m.power_export_limit_pv_only = Constraint(m.time, rule=power_export_limit_rule_pv_only)

        def pv_constraint_rule(m, t):
            return self.PV[t] >= m.pv_curtailment[t]
        m.pv_constraint = Constraint(m.time, rule=pv_constraint_rule)

        def availability_restrictions_rule(m, s, t):
            if len(self.analysis_inputs['system_data'][s]['Availability Restrictions'])>0:
                for key in self.analysis_inputs['system_data'][s]['Availability Restrictions']:
                    period_days = self.analysis_inputs['system_data'][s]['Availability Restrictions'][key]['Period'] # days
                    period_hours = period_days*24
                    duration_hours = self.analysis_inputs['system_data'][s]['Availability Restrictions'][key]['Duration'] # days
                    if self.analysis_inputs['system_data'][s]['Availability Restrictions'][key]['Type'] == "Conditioning Cycle":
                        if t*self.dt % period_hours == 0 and t*self.dt >= period_hours:  # Every 7 days (168 hours)
                            return m.soc[s,t] == 100.0  # Charge to 100% SOC
                        elif t*self.dt % period_hours == duration_hours and t*self.dt >= period_hours:  # The 'duration' after charging needs to reach 0% soc
                            return m.soc[s,t]  == 0.0  # Discharge to 0% SOC
                        else:
                            return Constraint.Skip  # Skip other hours    
                    if self.analysis_inputs['system_data'][s]['Availability Restrictions'][key]['Type'] == "Maintenance":
                        if t*self.dt % period_hours >= 0 and t*self.dt % period_hours <= duration_hours:  # Every X days (168 hours)
                            return m.p_discharge[s,t] == 0.0 and m.p_charge[s,t] == 0.0 # Charge and discharge power is set to 0 kWC
                        else:
                            return Constraint.Skip  # Skip other hours    
            else:
                return Constraint.Skip            

        m.availability_restrictions_constraint = Constraint(m.Systems,m.time, rule=availability_restrictions_rule)

        
        period_days = self.analysis_inputs['system_data']['System 1']['Availability Restrictions']['Restriction 0']['Period'] # days
        period_hours = period_days*24
        duration_hours = self.analysis_inputs['system_data']['System 1']['Availability Restrictions']['Restriction 0']['Duration'] # days
        #print("period_hours  " + str(period_hours))
        #print("duration_hours  " + str(duration_hours))
        #print("100%   " + str([t*self.dt for t in range(self.n) if  t*self.dt % period_hours == 0 and t*self.dt >= period_hours]))
        #print("0%   " + str([t*self.dt for t in range(self.n) if  t*self.dt % period_hours == duration_hours and t*self.dt >= period_hours]))
       

        def peak_demand_constraints(m, price, t):
            # Get the subset of time indices for the current price
            subset = m.subsets[price]
            # peak demand for each price subset must be greater than the net load in each subset
            if t in subset:
                return m.peak_demand[price] >= self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] +  sum([m.p_charge[s, t] + m.p_discharge[s, t] for s in m.Systems])
            else:
                return Constraint.Skip
        m.peak_demand_constraint = Constraint(m.Prices, m.time, rule=peak_demand_constraints)

        def flat_rate_peak_demand_constraints(m, t):
            # flat rate peak demand for greater than the net load durring the whole month
            return m.flat_rate_peak_demand >= self.LOAD[t] - self.PV[t] + m.pv_curtailment[t] +  sum([m.p_charge[s, t] + m.p_discharge[s, t] for s in m.Systems])

        m.flat_rate_peak_demand_constraint = Constraint(m.time, rule=flat_rate_peak_demand_constraints)

        #m.pprint()
        # Capture output
        try:
            # Redirect stdout to capture solver output
            #with io.StringIO() as buf, redirect_stdout(buf):
            solver = SolverFactory(self.analysis_inputs['analysis_configuration']['solver'])  
            #solver.options['tmlim'] = 1000
            results = solver.solve(m, tee=True)
            #output = buf.getvalue()
            #self.signals.status.emit(output)  # Display the solver output
            self.m = m
            self.signals.status.emit("Optimization Finished Sucessfully...")
            self.signals.status.emit("Organizing Results...")
            self.collect_results()
            self.signals.status.emit("Results Organized...")
            self.signals.status.emit("Saving Results...")
            self.save_results()
            self.signals.status.emit("Results Saved...")
        except Exception as e:
            self.signals.status.emit(f"An error occurred when solving the model: {str(e)}\n")

    def collect_results(self):
        plot_time = range(self.n)
        soc_time = range(self.n+1)
        sys = range(self.nS)
        t = [value(plot_time[t])*self.dt for t in plot_time]
        pe = [[(value(self.m.p_charge[s, t]) + value(self.m.p_discharge[s, t])) for t in plot_time ] for s in self.m.Systems]
        #print(len(pe))   

        subsets = {price: [t for t in range(self.n) if self.DEMAND_PRICE[t] == price] for price in self.unique_demand_prices}

        ess_cycles = {}
        for system in self.m.Systems:
            ess_cycles[system] = sum([abs(value(self.m.p_discharge[system, t]))*self.dt for t in plot_time]) / (self.analysis_inputs['system_data'][system]['Energy Capacity'] * 1000)
        #print(ess_cycles)
        # I need to add fractional net metering revenue calculation to the total cost for each senario 

        pv_only_c = [value(self.m.pv_only_curtailment[t]) for t in plot_time]
        pvc = [value(self.m.pv_curtailment[t]) for t in plot_time]
        soc = [[value(self.m.soc[s, t]) for t in soc_time]  for s in self.m.Systems]

        netload = [self.LOAD[t]+sum([pe[s][t] for s in sys]) - self.PV[t] + pvc[t] for t in plot_time]

        fixed_cost = self.analysis_inputs['selected_utility_rate']['fixedchargefirstmeter']

        baseline_energy_cost = max(sum([self.LOAD[t]*self.ENERGY_PRICE[t]*self.dt for t in plot_time]),0.0)
        print(baseline_energy_cost)


        baseline_demand_cost = max(sum([max([self.LOAD[t] for t in subsets[price]])*price  for price in self.unique_demand_prices]),0.0)
        baseline_net_meter_cost = 0.0
        print(baseline_demand_cost)
        baseline_cost = baseline_energy_cost + baseline_net_meter_cost + baseline_demand_cost + fixed_cost
        baseline_ghg  = sum([self.LOAD[t]*self.MOER[t]*self.dt for t in plot_time])
        baseline_energy_in = sum([self.LOAD[t]*self.dt for t in plot_time])

        pv_only_energy_cost = max(sum([(self.LOAD[t] - self.PV[t] + pv_only_c[t])*self.ENERGY_PRICE[t]*self.dt for t in plot_time]),0.0) # energy cost will be positive or 0
        print(pv_only_energy_cost)
        pv_only_demand_cost = max(sum([max([self.LOAD[t] - self.PV[t] + pv_only_c[t] for t in subsets[price]])*price  for price in self.unique_demand_prices]),0.0) # demand cost will be positive or 0
        print(pv_only_demand_cost)
        pv_only_energy_pro = sum([(self.PV[t]  - pv_only_c[t])*self.dt for t in plot_time])
        pv_only_energy_net = sum([(self.LOAD[t] - self.PV[t]  + pv_only_c[t])*self.dt for t in plot_time])
        pv_only_net_meter_cost = min(pv_only_energy_net*self.net_meter_price,0.0) # net meter cost will be negative or 0
        pv_only_cost = pv_only_energy_cost + pv_only_net_meter_cost + pv_only_demand_cost + fixed_cost
        pv_only_ghg = sum([(self.LOAD[t] - self.PV[t] + pv_only_c[t])*self.MOER[t]*self.dt for t in plot_time])

        pv_es_energy_cost = max(sum([(self.LOAD[t] - self.PV[t] + pvc[t] + sum([pe[s][t] for s in sys]))*self.ENERGY_PRICE[t]*self.dt for t in plot_time]) ,0.0)
        print(pv_es_energy_cost)
        pv_es_demand_cost = max(sum([max([self.LOAD[t] - self.PV[t] + pvc[t] + sum([pe[s][t] for s in sys]) for t in subsets[price]])*price  for price in self.unique_demand_prices]),0.0)
        print(pv_es_demand_cost)
        
        pv_es_energy_pro = sum([(self.PV[t]  - pvc[t])*self.dt for t in plot_time])
        pv_es_energy_net = sum([(self.LOAD[t] - self.PV[t]  + pvc[t] + sum([pe[s][t] for s in sys]))*self.dt for t in plot_time])
        pv_es_net_meter_cost = min(pv_es_energy_net*self.net_meter_price,0.0) # net meter cost will be negative or 0
        pv_es_cost = pv_es_energy_cost + pv_es_net_meter_cost + pv_es_demand_cost + fixed_cost
        pv_es_ghg = sum([(self.LOAD[t] - self.PV[t] + pvc[t] + sum([pe[s][t] for s in sys]))*self.MOER[t]*self.dt for t in plot_time])

        formatted_cost = "PV Only Cost          : ${:,.2f}".format(abs(pv_only_cost)) if pv_only_cost >= 0 else "PV Only Cost          : -${:,.2f}".format(abs(pv_only_cost))

        self.signals.results.emit('---------------------------------')
        self.signals.results.emit("Analysis Month        : {var1}".format(var1=self.month_name))
        self.signals.results.emit("Baseline Energy (load): {var1:,.2f}".format(var1=baseline_energy_in)+ " kWh")
        self.signals.results.emit("Fixed Cost   : ${var1:,.2f}".format(var1=fixed_cost) if fixed_cost>=0 else "Fixed Cost         : -${var1:,.2f}".format(var1=abs(fixed_cost)))
        self.signals.results.emit("Baseline Energy Cost   : ${var1:,.2f}".format(var1=baseline_energy_cost) if baseline_energy_cost>=0 else "Baseline Energy Cost         : -${var1:,.2f}".format(var1=abs(baseline_energy_cost)))
        self.signals.results.emit("Baseline Net Metering Cost   : ${var1:,.2f}".format(var1=baseline_net_meter_cost) if baseline_net_meter_cost>=0 else "Baseline Net Metering Cost         : -${var1:,.2f}".format(var1=abs(baseline_net_meter_cost)))
        self.signals.results.emit("Baseline Demand Cost   : ${var1:,.2f}".format(var1=baseline_demand_cost) if baseline_demand_cost>=0 else "Baseline Demand Cost         : -${var1:,.2f}".format(var1=abs(baseline_demand_cost)))
        self.signals.results.emit("Baseline Total Cost   : ${var1:,.2f}".format(var1=baseline_cost) if baseline_cost>=0 else "Baseline Total Cost         : -${var1:,.2f}".format(var1=abs(baseline_cost)))
        self.signals.results.emit("Baseline GHG          : {var1:,.2f}".format(var1=baseline_ghg)+ " tons")
        self.signals.results.emit("PV Only Energy (pro)  : {var1:,.2f}".format(var1=pv_only_energy_pro)+ " kWh")
        self.signals.results.emit("PV Only Energy (net)  : {var1:,.2f}".format(var1=pv_only_energy_net)+ " kWh")
        self.signals.results.emit("PV Only Curtailed PV  : {var1:,.2f}".format(var1=sum(pv_only_c)*self.dt)+ " kWh")
        self.signals.results.emit("PV Only Energy Cost          : ${var1:,.2f}".format(var1=pv_only_energy_cost) if pv_only_energy_cost>=0 else "PV Only Energy Cost          : -${var1:,.2f}".format(var1=abs(pv_only_energy_cost)))
        self.signals.results.emit("PV Only Net Metering Cost          : ${var1:,.2f}".format(var1=pv_only_net_meter_cost) if pv_only_net_meter_cost>=0 else "PV Only Net Metering Cost          : -${var1:,.2f}".format(var1=abs(pv_only_net_meter_cost)))
        self.signals.results.emit("PV Only Demand Cost          : ${var1:,.2f}".format(var1=pv_only_demand_cost) if pv_only_demand_cost>=0 else "PV Only Demand Cost          : -${var1:,.2f}".format(var1=abs(pv_only_demand_cost)))
        self.signals.results.emit("PV Only Total Cost          : ${var1:,.2f}".format(var1=pv_only_cost) if pv_only_cost>=0 else "PV Only Total Cost          : -${var1:,.2f}".format(var1=abs(pv_only_cost)))
        self.signals.results.emit("PV Only Cost Impact   : ${var1:,.2f}".format(var1=pv_only_cost - baseline_cost)  if pv_only_cost - baseline_cost>=0 else "PV Only Cost Impact   : -${var1:,.2f}".format(var1=abs(pv_only_cost - baseline_cost)))
        self.signals.results.emit("PV Only GHG           : {var1:,.2f}".format(var1=pv_only_ghg)+ " tons")
        self.signals.results.emit("PV Only GHG Impact    : {var1:,.2f}".format(var1=pv_only_ghg-baseline_ghg)+ " tons")
        self.signals.results.emit("ES + PV Energy (pro)  : {var1:,.2f}".format(var1=pv_es_energy_pro)+ " kWh")
        self.signals.results.emit("ES + PV Energy (net)  : {var1:,.2f}".format(var1=pv_es_energy_net)+ " kWh")
        self.signals.results.emit("ES + PV Curtailed PV  : {var1:,.2f}".format(var1=sum(pvc)*self.dt)+ " kWh")
        self.signals.results.emit("ES + PV Energy Cost          : ${var1:,.2f}".format(var1=pv_es_energy_cost) if pv_es_energy_cost>=0 else "ES + PV Energy Cost          : -${var1:,.2f}".format(var1=abs(pv_es_energy_cost)))
        self.signals.results.emit("ES + PV Net Metering Cost          : ${var1:,.2f}".format(var1=pv_es_net_meter_cost) if pv_es_net_meter_cost>=0 else "ES + PV Net Metering Cost          : -${var1:,.2f}".format(var1=abs(pv_es_net_meter_cost)))
        self.signals.results.emit("ES + PV Demand Cost          : ${var1:,.2f}".format(var1=pv_es_demand_cost) if pv_es_demand_cost>=0 else "ES + PV Demand Cost          : -${var1:,.2f}".format(var1=abs(pv_es_demand_cost)))
        self.signals.results.emit("ES + PV Total Cost          : ${var1:,.2f}".format(var1=pv_es_cost) if pv_es_cost>=0 else "ES + PV Total Cost          : -${var1:,.2f}".format(var1=abs(pv_es_cost)))
        self.signals.results.emit("ES + PV Cost Impact   : ${var1:,.2f}".format(var1=pv_es_cost - baseline_cost) if pv_es_cost - baseline_cost>=0 else "ES + PV Cost Impact   : -${var1:,.2f}".format(var1=abs(pv_es_cost - baseline_cost)))
        self.signals.results.emit("ES + PV GHG           : {var1:,.2f}".format(var1=pv_es_ghg)+ " tons")
        self.signals.results.emit("ES + PV GHG Impact    : {var1:,.2f}".format(var1=pv_es_ghg - baseline_ghg)+ " tons")
        for system in self.m.Systems:
            self.signals.results.emit("ES Cycles             : {var1}   :   {var2:,.2f}".format(var1=system,var2=ess_cycles[system]))
        self.signals.results.emit('---------------------------------')

        self.results[self.analysis_name] = {}
        
        self.results[self.analysis_name][self.month_name] = {}

        
        self.results[self.analysis_name][self.month_name]['Baseline Energy (load)'] = baseline_energy_in
        self.results[self.analysis_name][self.month_name]['Baseline Cost'] = baseline_cost
        self.results[self.analysis_name][self.month_name]['Baseline GHG'] = baseline_ghg


        self.results[self.analysis_name][self.month_name]['PV Only Energy (pro)'] = pv_only_energy_pro
        self.results[self.analysis_name][self.month_name]['PV Only Energy (net)'] = pv_only_energy_net
        self.results[self.analysis_name][self.month_name]['PV Only Curtailed PV'] = sum(pv_only_c)*self.dt
        self.results[self.analysis_name][self.month_name]['PV Only Cost'] = pv_only_cost
        self.results[self.analysis_name][self.month_name]['PV Only Cost Impact'] = pv_only_cost - baseline_cost
        self.results[self.analysis_name][self.month_name]['PV Only GHG'] = pv_only_ghg
        self.results[self.analysis_name][self.month_name]['PV Only GHG Impact'] = pv_only_ghg - baseline_ghg

        self.results[self.analysis_name][self.month_name]['ES + PV Energy (pro)'] = pv_es_energy_pro
        self.results[self.analysis_name][self.month_name]['ES + PV Energy (net)'] = pv_es_energy_net
        self.results[self.analysis_name][self.month_name]['ES + PV Curtailed PV'] = sum(pvc)*self.dt
        self.results[self.analysis_name][self.month_name]['ES + PV Cost'] = pv_es_cost
        self.results[self.analysis_name][self.month_name]['ES + PV Cost Impact'] = pv_es_cost - baseline_cost
        self.results[self.analysis_name][self.month_name]['ES + PV GHG'] = pv_es_ghg
        self.results[self.analysis_name][self.month_name]['ES + PV GHG Impact'] = pv_es_ghg - baseline_ghg

        self.results[self.analysis_name][self.month_name]['t'] = t
        self.results[self.analysis_name][self.month_name]['pe'] = pe
        self.results[self.analysis_name][self.month_name]['subsets'] = subsets
        self.results[self.analysis_name][self.month_name]['pvc'] = pvc
        self.results[self.analysis_name][self.month_name]['pv_only_c'] = pv_only_c
        self.results[self.analysis_name][self.month_name]['soc'] = soc
        self.results[self.analysis_name][self.month_name]['netload'] = netload

        self.results[self.analysis_name][self.month_name]['analysis_inputs'] = self.analysis_inputs
        
    def plot_results(self):    
        plot_time = range(self.n)
        soc_time = range(self.n+1)
        sys = range(self.nS)
        #plot_time = self.results[self.analysis_name][self.month_name]['plot_time'] 
        #soc_time = self.results[self.analysis_name][self.month_name]['soc_time'] 
        #sys = self.results[self.analysis_name][self.month_name]['sys'] 
        t = self.results[self.analysis_name][self.month_name]['t']
        pe = self.results[self.analysis_name][self.month_name]['pe'] 
        subsets = self.results[self.analysis_name][self.month_name]['subsets'] 
        pvc = self.results[self.analysis_name][self.month_name]['pvc'] 
        soc = self.results[self.analysis_name][self.month_name]['soc']
        netload = self.results[self.analysis_name][self.month_name]['netload']

        plt.style.use('dark_background')
        plt.figure(figsize=(15, 4))
        plt.plot([t[i]/24 for i in plot_time], [self.ENERGY_PRICE[t] for t in plot_time], label='$/kWh LMP', color='green')
        plt.plot([t[i]/24 for i in plot_time], [self.carbon_weight*self.MOER[t] for t in plot_time], label='$co2/kWh', color='gray')
        for price in self.unique_demand_prices:
            plt.plot([t[i]/24 for i in subsets[price]], [price for i in subsets[price]],'*', label='$/kW', color='orange')
        plt.xlabel('time (days)')
        plt.ylabel('Price ($/kWh) ')
        #plt.grid(True)
        plt.legend()

        plt.figure(figsize=(10, 6))
        plt.plot([self.ENERGY_PRICE[t] for t in plot_time], [self.carbon_weight*self.MOER[t]  for t in plot_time], '*', color='green')
        plt.xlabel('Price ($/kWh)')
        plt.ylabel('MOER x Carbon Weight ($co2/kWh) ')
        #plt.grid(True)

        plt.figure(figsize=(15, 4))
        plt.plot([t[i]/24 for i in plot_time], [self.LOAD[t] for t in plot_time], label='load (kW)', color='gray')
        plt.plot([t[i]/24 for i in plot_time], [netload[t] for t in plot_time], label='net load (kW)', color='darkred')
        plt.xlabel('time (days)')
        plt.ylabel('Power (kW) ')
        #plt.grid(True)
        plt.legend()

        plt.figure(figsize=(15, 4))
        plt.plot([t[i]/24 for i in plot_time], [self.PV[t] for t in plot_time], label='pv (kW)', color='green')
        plt.plot([t[i]/24 for i in plot_time], [self.PV[t] - pvc[t] for t in plot_time], label='net pv (kW)', color='darkred')
        plt.xlabel('time (days)')
        plt.ylabel('PV Power (kW)')
        #plt.grid(True)
        plt.legend()
                                    
        plt.figure(figsize=(15, 4))
        for s in sys:
            system = 'System ' + str(s+1)
            plt.plot([t[i]/24 for i in plot_time], [pe[s][t] for t in plot_time], label=self.analysis_inputs['system_data'][system]['System Name'])
        plt.xlabel('time (days)')
        plt.ylabel('ESS Power')
        #plt.grid(True)
        plt.legend()

        plt.figure(figsize=(15, 4))
        for s in sys:
            system = 'System ' + str(s+1)
            plt.plot([self.dt*i/24 for i in soc_time], [soc[s][t] for t in soc_time], label=self.analysis_inputs['system_data'][system]['System Name'])
        plt.xlabel('time (days)')
        plt.ylabel('ESS SOC (%)')
        #plt.grid(True)
        plt.legend().set_loc('right')

        plt.figure(figsize=(15, 4))
        for s in sys:
            system = 'System ' + str(s+1)
            plt.plot([soc[s][t] for t in plot_time], [pe[s][t] for t in plot_time],'*', label=self.analysis_inputs['system_data'][system]['System Name'])
        plt.xlabel('ESS SOC (%)')
        plt.ylabel('ESS Power')
        #plt.grid(True)
        plt.legend().set_loc('right')
        plt.show()

    def save_results(self):
        #plot_time = self.results[self.analysis_name][self.month_name]['plot_time'] 
        #sys = self.results[self.analysis_name][self.month_name]['sys'] 
        
        self.results[self.analysis_name][self.month_name]['DEMAND_PRICE'] = self.DEMAND_PRICE
        self.results[self.analysis_name][self.month_name]['ENERGY_PRICE'] = self.ENERGY_PRICE
        self.results[self.analysis_name][self.month_name]['MOER'] = self.MOER
        self.results[self.analysis_name][self.month_name]['LOAD'] = self.LOAD
        self.results[self.analysis_name][self.month_name]['PV'] = self.PV

        # Save data
        
        results_path = 'results/'
        json_file_path = results_path + self.analysis_name + '.json'
        
        try: 
            # Check if the JSON file exists
            if os.path.exists(json_file_path):
                # If it exists, read the existing data
                with open(json_file_path, 'r') as json_file:
                    try:
                        existing_data = json.load(json_file)
                    except json.JSONDecodeError:
                        existing_data = {}  # Handle empty or invalid JSON file
                        existing_data[self.analysis_name] = {}  # Handle empty or invalid JSON file
            else:
                # If it does not exist, initialize existing_data as an empty dictionary
                existing_data = {}# Update existing data with new results
                existing_data[self.analysis_name] = {}  # Update existing data with new results
            existing_data[self.analysis_name].update(self.results[self.analysis_name])
            #existing_data[self.analysis_name][self.month_name].pop('plot_time')
            #existing_data[self.analysis_name][self.month_name].pop('sys')
            #existing_data[self.analysis_name][self.month_name].pop('soc_time')
            # Write the updated data back to the JSON file
            with open(json_file_path, 'w') as json_file:
                json.dump(existing_data, json_file, indent=4)
            
            print('.json file saved')
        except Exception as e: 
            print('There was an error when trying to save the .json results : {error}'.format(error=e))
        return json_file_path


        
if __name__ == '__main__':
    '''app = QApplication(sys.argv)
    ex = OptimizationApp()
    ex.show()
    sys.exit(app.exec_())'''

    

