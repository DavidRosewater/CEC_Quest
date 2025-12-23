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

from jinja2 import Environment, FileSystemLoader, select_autoescape

import matplotlib.pyplot as plt

import os
from time import sleep
import datetime
import webbrowser
import logging 
import pandas as pd
import json
import numpy as np

class BtmGenerateReport():
    host_report = None
    graphics_locations = {}
    report_id = None
    MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December']

    def __init__(self, results_data, **kwargs):
        super(BtmGenerateReport, self).__init__(**kwargs)

        self.results_data = results_data

        self.report_id = datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S')

    def generate_report_from_template(self):
        # Get current date.
        now = datetime.datetime.now()
        today = now.strftime("%B %d, %Y")

        # Get report-specific data.
        '''
        op_handler_requests = self.host_report.report_attributes
        load_profile = op_handler_requests['load_profile']
        pv_profile = op_handler_requests['pv_profile']
        system_params = op_handler_requests['param desc']
        rate_structure = op_handler_requests['rate_structure']'''


        '''grid_load_and_limits = {'saved_electrical_load_files': {'January': {'File': 'data/load/Load-01.csv'}, 
                                                        'February': {'File': 'data/load/Load-02.csv'}, 
                                                        'March': {'File': 'data/load/Load-03.csv'}, 
                                                        'April': {'File': 'data/load/Load-04.csv'}, 
                                                        'May': {'File': 'data/load/Load-05.csv'}, 
                                                        'June': {'File': 'data/load/Load-06.csv'}, 
                                                        'July': {'File': 'data/load/Load-07.csv'}, 
                                                        'August': {'File': 'data/load/Load-08.csv'}, 
                                                        'September': {'File': 'data/load/Load-09.csv'}, 
                                                        'October': {'File': 'data/load/Load-10.csv'}, 
                                                        'November': {'File': 'data/load/Load-11.csv'}, 
                                                        'December': {'File': 'data/load/Load-12.csv'}}, 
                        'powerImportLimitInput': 7.0, 'powerExportLimitInput': 7.0}
        MOER_Signal = {'Grid Region': 'SGIP_CAISO_SDGE', 'Start Date': '2024-01-01 00:00:00', 'End Date': '2024-12-31 00:00:00', \
                        'Selected Files': ['SGIP_CAISO_SDGE_2024-01_ALL_MOER_VERSIONS.csv', 'SGIP_CAISO_SDGE_2024-02_ALL_MOER_VERSIONS.csv', \
                                        'SGIP_CAISO_SDGE_2024-03_ALL_MOER_VERSIONS.csv', 'SGIP_CAISO_SDGE_2024-04_ALL_MOER_VERSIONS.csv', \
                                        'SGIP_CAISO_SDGE_2024-05_ALL_MOER_VERSIONS.csv', 'SGIP_CAISO_SDGE_2024-06_ALL_MOER_VERSIONS.csv', \
                                        'SGIP_CAISO_SDGE_2024-07_ALL_MOER_VERSIONS.csv', 'SGIP_CAISO_SDGE_2024-08_ALL_MOER_VERSIONS.csv', \
                                        'SGIP_CAISO_SDGE_2024-09_ALL_MOER_VERSIONS.csv', 'SGIP_CAISO_SDGE_2024-10_ALL_MOER_VERSIONS.csv',\
                                        'SGIP_CAISO_SDGE_2024-11_ALL_MOER_VERSIONS.csv', 'SGIP_CAISO_SDGE_2024-12_ALL_MOER_VERSIONS.csv'], \
                        'Data Check': 'Enough Data'}
        selected_utility_rate = {'label': '6772f03ab5f9d561220ececd', 'eiaid': 16609.0, 'name': 'AL-TOU Primary (Above 500kW)', \
                                    'is_default': False, 'startdate': '2024-09-30 23:00:00', 'latest_update': '2024-12-30 14:51:30', \
                                'utility': 'San Diego Gas & Electric Co', 'sector': 'Commercial', 'servicetype': 'Bundled', \
                                'source': 'blob:https://tariffsprd.sdge.com/9e83b5a4-9102-4a78-9e94-d72779a41fa9', \
                                'sourceparent': 'https://www.sdge.com/rates-and-regulations/current-and-effective-tariffs', \
                                'peakkwcapacitymin': 20.0, 'voltagecategory': 'Primary', 'fixedchargefirstmeter': 68.43, \
                                'fixedchargeunits': '$/month', 'flatdemandstructure/period0/tier0rate': 30.01, \
                                'flatDemandMonth_jan': 0.0, 'flatDemandMonth_feb': 0.0, 'flatDemandMonth_mar': 0.0, \
                                'flatDemandMonth_apr': 0.0, 'flatDemandMonth_may': 0.0, 'flatDemandMonth_jun': 0.0, \
                                'flatDemandMonth_jul': 0.0, 'flatDemandMonth_aug': 0.0, 'flatDemandMonth_sep': 0.0, \
                                'flatDemandMonth_oct': 0.0, 'flatDemandMonth_nov': 0.0, 'flatDemandMonth_dec': 0.0, \
                                'demandratestructure/period0/tier0rate': 0.0, 'demandratestructure/period1/tier0rate': 30.54, \
                                'demandratestructure/period1/tier0adj': 14.74, 'demandratestructure/period2/tier0rate': 32.74, \
                                'demandweekdayschedule': '[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0]]', \
                                'demandweekendschedule': '[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]', \
                                'demandcomments': 'Adjustment = Electric Energy Commodity Cost', 'energyratestructure/period0/tier0rate': 0.01874, \
                                'energyratestructure/period0/tier0adj': 0.20866, 'energyratestructure/period1/tier0rate': 0.01874, \
                                'energyratestructure/period1/tier0adj': 0.12891, 'energyratestructure/period2/tier0rate': 0.01874, \
                                'energyratestructure/period2/tier0adj': 0.10522, 'energyratestructure/period3/tier0rate': 0.01874, \
                                'energyratestructure/period3/tier0adj': 0.22016, 'energyratestructure/period4/tier0rate': 0.01874, \
                                'energyratestructure/period4/tier0adj': 0.12374, 'energyratestructure/period5/tier0rate': 0.01874, \
                                'energyratestructure/period5/tier0adj': 0.09568, \
                                'energyweekdayschedule': '[[5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4]]', \
                                'energyweekendschedule': '[[5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4]]', \
                                'energycomments': 'Adjustment = Electric Energy Commodity Cost (EECC) https://tariff.sdge.com/tm2/pdf/tariffs/ELEC_ELEC-SCHEDS_EECC.pdf', \
                                'supersedes': '663e732e846f522f700aecce'}
        system_data = {'System 1': {'System Name': 'EOS Battery Model', 'Energy Capacity': 66.34, 'Charge Power Limit': 11.98, 'Discharge Power Limit': 11.98, \
                                    'Round-Trip-Efficiency': 75.0, 'Self-Discharge Rate': 0.0, 'Max SOC': 100.0, 'Min SOC': 0.0, 'Degradation Rate in Year 1': 11.0, \
                                    'Degradation Rate Year > 1': 1.5, 'Dynamic Power Limits': {'Limit 0': {'Region': 'Discharge', 'Slope': -0.5324, 'Intercept': 0.0}, 
                                                                                                'Limit 1': {'Region': 'Discharge', 'Slope': -0.2892, 'Intercept': -4.2848}, 
                                                                                                'Limit 2': {'Region': 'Discharge', 'Slope': -0.00427, 'Intercept': -11.5526}},
                                                                        "Availability Restrictions": {"Restriction 0": {"Type": "Conditioning Cycle","Period": 6.5,"Duration": 12.0}}}, \
                        'System 2': {'System Name': 'Invinity Battery Model', 'Energy Capacity': 10.0, 'Charge Power Limit': 3.432, 'Discharge Power Limit': 3.432, \
                                        'Round-Trip-Efficiency': 65.0, 'Self-Discharge Rate': 0.0, 'Max SOC': 96.0, 'Min SOC': 5.0, 'Degradation Rate in Year 1': 0.5, \
                                        'Degradation Rate Year > 1': 0.5, 'Dynamic Power Limits': {'Limit 0': {'Region': 'Charge', 'Slope': -0.000118, 'Intercept': 3.4321}, 
                                                                                                'Limit 1': {'Region': 'Charge', 'Slope': -0.05397, 'Intercept': 7.2152}, 
                                                                                                'Limit 2': {'Region': 'Charge', 'Slope': -0.05603, 'Intercept': 7.3794}, 
                                                                                                'Limit 3': {'Region': 'Charge', 'Slope': -0.06452, 'Intercept': 8.132}, 
                                                                                                'Limit 4': {'Region': 'Charge', 'Slope': -0.07067, 'Intercept': 8.7068}, 
                                                                                                'Limit 5': {'Region': 'Discharge', 'Slope': -0.1535, 'Intercept': -2.4325}, 
                                                                                                'Limit 6': {'Region': 'Discharge', 'Slope': -0.1321, 'Intercept': -2.4741}, 
                                                                                                'Limit 7': {'Region': 'Discharge', 'Slope': -0.1225, 'Intercept': -2.5153}},
                                                                        "Availability Restrictions": {}}}
        solar_site_data = {'Source': 'NSRDB', 'Location ID': '72883', 'City': '-', 'State': '-', 'Country': '-', 'Latitude': '32.85', 'Longitude': '-116.7', 'Time Zone': '-8', \
                            'Elevation': '779', 'Local Time Zone': '-8', 'Clearsky DHI Units': 'w/m2', 'Clearsky DNI Units': 'w/m2', 'Clearsky GHI Units': 'w/m2', \
                            'Dew Point Units': 'c', 'DHI Units': 'w/m2', 'DNI Units': 'w/m2', 'GHI Units': 'w/m2', 'Solar Zenith Angle Units': 'Degree', 'Temperature Units': 'c', \
                            'Pressure Units': 'mbar', 'Relative Humidity Units': '%', 'Precipitable Water Units': 'cm', 'Wind Direction Units': 'Degrees', 'Wind Speed Units': 'm/s', \
                            'Cloud Type -15': 'nan', 'Cloud Type 0': 'Clear', 'Cloud Type 1': 'Probably Clear', 'Cloud Type 2': 'Fog', 'Cloud Type 3': 'Water', 'Cloud Type 4': 'Super-Cooled Water', \
                            'Cloud Type 5': 'Mixed', 'Cloud Type 6': 'Opaque Ice', 'Cloud Type 7': 'Cirrus', 'Cloud Type 8': 'Overlapping', 'Cloud Type 9': 'Overshooting', 'Cloud Type 10': 'Unknown', \
                            'Cloud Type 11': 'Dust', 'Cloud Type 12': 'Smoke', 'Fill Flag 0': 'nan', 'Fill Flag 1': 'Missing Image', 'Fill Flag 2': 'Low Irradiance', 'Fill Flag 3': 'Exceeds Clearsky', \
                            'Fill Flag 4': 'Missing CLoud Properties', 'Fill Flag 5': 'Rayleigh Violation', 'Surface Albedo Units': 'nan', 'Version': '3.2.0', \
                            'AC Power Rating': 15.0,'DC Power Rating': 18.0,'Tracking': 0,'Year': 2020, \
                            'Data File Path': 'data/solar/2020/TestSite101_sgen_sat.csv', 'Data File Name': 'TestSite101.csv','Solar DegradationRate in Year 1': 2.0,'Solar DegradationRate Year >1': 0.5}
        analysis_configuration = {'analysis_name':"test_analysis",
                                        'timestep':30,
                                        'plot_results':True,
                                        'carbon_weight':50.0,
                                        }   
        
        lifetime_analysis = {'project_life': 20, 'grid_pen': [50.0, 52.631578947368425, 55.26315789473684, 57.89473684210526, 60.526315789473685, 63.1578947368421, 65.78947368421052, 68.42105263157895, 71.05263157894737, 73.6842105263158, 76.3157894736842, 78.94736842105263, 81.57894736842105, 84.21052631578948, 86.84210526315789, 89.47368421052632, 92.10526315789474, 94.73684210526315, 97.36842105263159, 100.0], 'pv_capacity': [100, 98.0, 97.5, 97.0, 96.5, 96.0, 95.5, 95.0, 94.5, 94.0, 93.5, 93.0, 92.5, 92.0, 91.5, 91.0, 90.5, 90.0, 89.5, 89.0], 'ess_capacity': {0: [100, 89.0, 87.5, 86.0, 84.5, 83.0, 81.5, 80.0, 78.5, 77.0, 75.5, 74.0, 72.5, 71.0, 69.5, 68.0, 66.5, 65.0, 63.5, 62.0], 1: [100, 99.5, 99.0, 98.5, 98.0, 97.5, 97.0, 96.5, 96.0, 95.5, 95.0, 94.5, 94.0, 93.5, 93.0, 92.5, 92.0, 91.5, 91.0, 90.5]}, 'baseline_cost': [4620099.496371329, 4485533.49162265, 4354886.885070534, 4228045.519485955, 4104898.5626077233, 3985338.4102987605, 3869260.5925230677, 3756563.6820612308, 3647149.2058846904, 3540921.5591113493, 3437787.92146733, 3337658.176181873, 3240444.831244537, 3146062.9429558613, 3054430.0417047194, 2965466.059907494, 2879093.262046111, 2795236.176743798, 2713821.5308192205, 2634778.185261379], 'baseline_total_cost': 70797476.53336962, 'pv_only_cost': [454122.7766264236, 520551.94240108255, 524724.2263029389, 528211.8614223504, 531051.1907126996, 533277.0208745506, 534922.6810150575, 536020.079193579, 536599.7569268689, 536690.9417247346, 536321.5977246527, 535518.474491517, 534307.1540464439, 532712.0961864052, 530756.6821543508, 528463.256717464, 525853.1687092327, 522946.8100891276, 519763.65357184474, 516322.28887630557], 'pv_only_total_cost': 10519137.659767631, 'pv_only_total_cost_change': -60278338.87360199, 'es_pv_cost': [-1673077.2856418313, -1403796.2599298835, -1323082.2527789788, -1245869.8357553424, -1172030.129844, -1101434.849395135, -1033957.6396549885, -969476.7539769456, -907874.892579432, -849039.0467873358, -792860.3485743048, -739233.9252292691, -688058.758976331, -639237.5513827626, -592676.592395287, -548285.6338500602, -505977.7673068495, -465669.3060628239, -427279.6712061152, -390731.2815739218], 'es_pv_total_cost': -17469649.7829016, 'es_pv_total_cost_change': -88267126.31627122, 'baseline_ghg': [8592.344382834217, 8140.115731106102, 7687.887079377984, 7235.658427649868, 6783.429775921752, 6331.201124193636, 5878.97247246552, 5426.743820737402, 4974.515169009285, 4522.286517281166, 4070.0578655530517, 3617.829213824934, 3165.600562096817, 2713.3719103686994, 2261.1432586405845, 1808.914606912467, 1356.6859551843497, 904.4573034562349, 452.2286517281149, 0.0], 'baseline_total_ghg': 85923.4438283422, 'pv_only_ghg': [1893.6959098354944, 1920.9494645957075, 1844.1976878014664, 1763.9203065477532, 1680.1173208345656, 1592.7887306619057, 1501.9345360297732, 1407.554736938167, 1309.649333387088, 1208.2183253765356, 1103.2617129065104, 994.7794959770127, 882.7716745880416, 767.2382487395971, 648.1792184316807, 525.5945836642904, 399.48434443742707, 269.8485007510916, 136.68705260528156, 0.0], 'pv_only_total_ghg': 21850.871184109386, 'pv_only_total_ghg_change': -64072.572644232794, 'es_pv_ghg': [-3377.207796050349, -2619.469930855495, -2383.063771227981, -2157.349382466086, -1942.3267645698104, -1737.9959175391543, -1544.3568413741177, -1361.4095360747, -1189.1540016409017, -1027.590238072723, -876.7182453701643, -736.538023533224, -607.0495725619032, -488.2528924562016, -380.14798321611994, -282.7348448416572, -196.01347733281378, -119.98388068959005, -54.64605491198504, 0.0], 'es_pv_total_ghg': -23082.009154784977, 'es_pv_total_ghg_change': -109005.45298312716}
        analysis_inputs = {"grid_load_and_limits" : grid_load_and_limits, \
                        "MOER_Signal" : MOER_Signal, \
                        "selected_utility_rate" : selected_utility_rate, \
                        "system_data" : system_data, \
                        "solar_site_data" : solar_site_data, \
                        "analysis_configuration" : analysis_configuration, \
                        "lifetime_analysis" : lifetime_analysis
                        }'''
    
        analysis_name = list(self.results_data.keys())[0]

        MOER_Info = [{'name': 'Grid Region', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['MOER_Signal']['Grid Region'], 'units': ''},
                     {'name': 'Start Date', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['MOER_Signal']['Start Date'], 'units': ''},
                     {'name': 'End Date', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['MOER_Signal']['End Date'], 'units': ''}] 
        print(self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data'])
        if self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Data File Name'] == 'PVWatts Data':
            SOLAR_Info = [{'name': 'Latitude', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Latitude (DD)']},
                      {'name': 'Longitude', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Longitude (DD)']},
                      {'name': 'Elevation', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Elevation (m)']},
                      {'name': 'DC Power', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['DC System Size (kW)'], 'units': 'kW'}, 
                      {'name': 'DC to AC Size Ratio', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['DC to AC Size Ratio'], 'units': 'MW'},
                      {'name': 'Module Type', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Module Type']},
                      {'name': 'Inverter Efficiency (%)', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Inverter Efficiency (%)'], 'units': '%'}, 
                      {'name': 'Data File Name', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Data File Name']},
                      {'name': 'Solar Degradation Rate in Year 1', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Solar Degradation Rate in Year 1']},
                      {'name': 'Solar Degradation Rate Year >1', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Solar Degradation Rate Year >1']}] 
        else:
            SOLAR_Info = [{'name': 'Latitude', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Latitude']},
                      {'name': 'Longitude', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Longitude']},
                      {'name': 'Elevation', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Elevation']},
                      {'name': 'AC Power', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['AC Power Rating'], 'units': 'MW'},
                      {'name': 'DC Power', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['DC Power Rating'], 'units': 'MW'}, 
                      {'name': 'Tracking', 'value': ('yes' if self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['DC Power Rating'] == 1 else 'no'), 'units': ''},
                      {'name': 'Year', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Year'], 'units': ''}, 
                      {'name': 'Data File Name', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Data File Name']},
                      {'name': 'Solar Degradation Rate in Year 1', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Solar Degradation Rate in Year 1']},
                      {'name': 'Solar Degradation Rate Year >1', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Solar Degradation Rate Year >1']}] 
        
        sys_num = 1
        ESS_System_Info = []
        for system in self.results_data[analysis_name]['January']['analysis_inputs']['system_data']:
            energy_capacity = {'name': 'Energy Capacity', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Energy Capacity'], 'units': 'MWh'}
            charge_power_limit = {'name': 'Charge Power Limit', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Charge Power Limit'], 'units': 'MW'}
            discharge_power_limit = {'name': 'Discharge Power Limit', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Discharge Power Limit'], 'units': 'MW'}
            round_trip_efficiency = {'name': 'Round-Trip-Efficiency', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Round-Trip-Efficiency'], 'units': '%'}
            self_dischage_rate = {'name': 'Self-Discharge Rate', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Self-Discharge Rate'], 'units': 'W'}
            max_soc = {'name': 'Max SOC', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Max SOC'], 'units': '%'}
            min_soc = {'name': 'Min SOC', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Min SOC'], 'units': '%'}
            initial_degredation_rate = {'name': 'Degradation Rate in Year 1', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Degradation Rate in Year 1'], 'units': '%'}
            degredation_rate = {'name': 'Degradation Rate Year > 1', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Degradation Rate Year > 1'], 'units': '%'}
            Parameters = [energy_capacity,charge_power_limit,discharge_power_limit,round_trip_efficiency,self_dischage_rate,max_soc,min_soc,initial_degredation_rate,degredation_rate]

            for limit in self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits']:
                region = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits'][limit]['Region']
                slope = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits'][limit]['Slope']
                intercept = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits'][limit]['Intercept']
                Parameters.append({'name': limit, 'value': 'Region: ' + str(region) + ',  Slope: ' + str(slope) +  ',  Intercept: ' + str(intercept), 'units': ''})

            for restriction in self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Availability Restrictions']:
                type = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Availability Restrictions'][restriction]['Type']
                period = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Availability Restrictions'][restriction]['Period']
                duration = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Availability Restrictions'][restriction]['Duration']
                Parameters.append({'name': restriction, 'value': 'Type: ' + str(type) + ',  Period: ' + str(period) +  ',  Duration: ' + str(duration), 'units': ''})

            ESS_System_Info.append({'SystemName' : self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['System Name'],
                                    'SystemNum' : sys_num,
                                    'parameters' : Parameters})
            sys_num += 1

    
        Utility_Info = [{'name': 'Utility', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['selected_utility_rate']['utility']},
                        {'name': 'Rate Structure', 'value':  self.results_data[analysis_name]['January']['analysis_inputs']['selected_utility_rate']['name']},
                        {'name': 'Sector', 'value':  self.results_data[analysis_name]['January']['analysis_inputs']['selected_utility_rate']['sector']}]
        

        GRID_Limit_Info = [{'name': 'Power Import Limit (MW)', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['grid_load_and_limits']['powerImportLimitInput']},
                           {'name': 'Power Export Limit (MW)', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['grid_load_and_limits']['powerExportLimitInput']}]
        
        ANALSYS_Configuration = [{'name': 'Analysis Name', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['analysis_configuration']['analysis_name'], 'units': ''},
                                 {'name': 'Time Step', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['analysis_configuration']['timestep'], 'units': 'minutes'},
                                 {'name': 'Controller Carbon Weight', 'value': self.results_data[analysis_name]['January']['analysis_inputs']['analysis_configuration']['carbon_weight'], 'units': ' $/ton'},
                                 {'name': 'Quantification Period', 'value': self.results_data[analysis_name]['lifetime_analysis']['project_life'], 'units': 'years'}]


        RESULTS_Monthly_Energy = []
        RESULTS_Monthly_Cost = []
        RESULTS_Monthly_GHG = []
        self.results_data[analysis_name]['lifetime_analysis']['baseline_yearly_load'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_produced'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_net'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_cur'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['es_pv_yearly_produced'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['es_pv_only_yearly_net'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['es_pv_only_yearly_cur'] = 0
        for month in self.MONTH_NAMES:
            RESULTS_Monthly_Energy.append({'month': month, 
                                           'Baseline Energy (load)': format_energy_string(self.results_data[analysis_name][month]['Baseline Energy (load)']), 
                                           'PV Only Energy (pro)': format_energy_string(self.results_data[analysis_name][month]['PV Only Energy (pro)']), 
                                           'PV Only Energy (net)': format_energy_string(self.results_data[analysis_name][month]['PV Only Energy (net)']), 
                                           'PV Only Curtailed PV': format_energy_string(self.results_data[analysis_name][month]['PV Only Curtailed PV']), 
                                           'ES + PV Energy (pro)': format_energy_string(self.results_data[analysis_name][month]['ES + PV Energy (pro)']), 
                                           'ES + PV Energy (net)': format_energy_string(self.results_data[analysis_name][month]['ES + PV Energy (net)']), 
                                           'ES + PV Curtailed PV': format_energy_string(self.results_data[analysis_name][month]['ES + PV Curtailed PV'])})
            RESULTS_Monthly_Cost.append({'month': month, 'Baseline Cost': format_dollar_string(self.results_data[analysis_name][month]['Baseline Cost']),
                                           'PV Only Cost': format_dollar_string(self.results_data[analysis_name][month]['PV Only Cost']), 
                                           'PV Only Cost Impact': format_dollar_string(self.results_data[analysis_name][month]['PV Only Cost Impact']), 
                                           'ES + PV Cost': format_dollar_string(self.results_data[analysis_name][month]['ES + PV Cost']), 
                                           'ES + PV Cost Impact': format_dollar_string(self.results_data[analysis_name][month]['ES + PV Cost Impact'])})
            RESULTS_Monthly_GHG.append({'month': month, 'Baseline GHG': format_tons_string(self.results_data[analysis_name][month]['Baseline GHG']),
                                           'PV Only GHG': format_tons_string(self.results_data[analysis_name][month]['PV Only GHG']), 
                                           'PV Only GHG Impact': format_tons_string(self.results_data[analysis_name][month]['PV Only GHG Impact']), 
                                           'ES + PV GHG': format_tons_string(self.results_data[analysis_name][month]['ES + PV GHG']), 
                                           'ES + PV GHG Impact': format_tons_string(self.results_data[analysis_name][month]['ES + PV GHG Impact'])})
            self.results_data[analysis_name]['lifetime_analysis']['baseline_yearly_load'] += self.results_data[analysis_name][month]['Baseline Energy (load)']
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_produced'] += self.results_data[analysis_name][month]['PV Only Energy (pro)']
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_net'] += self.results_data[analysis_name][month]['PV Only Energy (net)']
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_cur'] += self.results_data[analysis_name][month]['PV Only Curtailed PV']
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_yearly_produced'] += self.results_data[analysis_name][month]['ES + PV Energy (pro)']
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_only_yearly_net'] += self.results_data[analysis_name][month]['ES + PV Energy (net)']
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_only_yearly_cur'] += self.results_data[analysis_name][month]['ES + PV Curtailed PV']

        RESULTS_Monthly_Energy.append({'month': '-TOTAL-', 
                                           'Baseline Energy (load)': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_yearly_load'] ), 
                                           'PV Only Energy (pro)': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_produced'] ), 
                                           'PV Only Energy (net)': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_net'] ), 
                                           'PV Only Curtailed PV': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_cur'] ), 
                                           'ES + PV Energy (pro)': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_yearly_produced'] ), 
                                           'ES + PV Energy (net)': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_only_yearly_net'] ), 
                                           'ES + PV Curtailed PV': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_only_yearly_cur'] )})
        RESULTS_Monthly_Cost.append({'month': '-TOTAL-', 'Baseline Cost': format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][0]),
                                        'PV Only Cost': format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'][0]), 
                                        'PV Only Cost Impact': format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][0] - self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'][0]), 
                                        'ES + PV Cost': format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'][0]), 
                                        'ES + PV Cost Impact': format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][0] - self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'][0])})
        RESULTS_Monthly_GHG.append({'month': '-TOTAL-', 'Baseline GHG': format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][0]),
                                        'PV Only GHG': format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][0]), 
                                        'PV Only GHG Impact': format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][0] - self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][0]), 
                                        'ES + PV GHG': format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][0]), 
                                        'ES + PV GHG Impact': format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][0] - self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][0])})
        
        lifetime_analysis = {'project_life': 20, 
                         'discount_rate': 3.0, 
                         'grid_pen': [50.0, 52.631578947368425, 55.26315789473684, 57.89473684210526, 60.526315789473685, 63.1578947368421, 65.78947368421052, 68.42105263157895, 71.05263157894737, 73.6842105263158, 76.3157894736842, 78.94736842105263, 81.57894736842105, 84.21052631578948, 86.84210526315789, 89.47368421052632, 92.10526315789474, 94.73684210526315, 97.36842105263159, 100.0], 
                         'pv_capacity': [100, 98.0, 97.5, 97.0, 96.5, 96.0, 95.5, 95.0, 94.5, 94.0, 93.5, 93.0, 92.5, 92.0, 91.5, 91.0, 90.5, 90.0, 89.5, 89.0], 
                         'ess_capacity': {0: [100, 89.0, 87.5, 86.0, 84.5, 83.0, 81.5, 80.0, 78.5, 77.0, 75.5, 74.0, 72.5, 71.0, 69.5, 68.0, 66.5, 65.0, 63.5, 62.0], 
                                          1: [100, 99.5, 99.0, 98.5, 98.0, 97.5, 97.0, 96.5, 96.0, 95.5, 95.0, 94.5, 94.0, 93.5, 93.0, 92.5, 92.0, 91.5, 91.0, 90.5]}, 
                        'baseline_cost': [4620099.496371329, 4485533.49162265, 4354886.885070534, 4228045.519485955, 4104898.5626077233, 3985338.4102987605, 3869260.5925230677, 3756563.6820612308, 3647149.2058846904, 3540921.5591113493, 3437787.92146733, 3337658.176181873, 3240444.831244537, 3146062.9429558613, 3054430.0417047194, 2965466.059907494, 2879093.262046111, 2795236.176743798, 2713821.5308192205, 2634778.185261379], 
                        'baseline_total_cost': 70797476.53336962, 
                        'pv_only_cost': [454122.7766264236, 520551.94240108255, 524724.2263029389, 528211.8614223504, 531051.1907126996, 533277.0208745506, 534922.6810150575, 536020.079193579, 536599.7569268689, 536690.9417247346, 536321.5977246527, 535518.474491517, 534307.1540464439, 532712.0961864052, 530756.6821543508, 528463.256717464, 525853.1687092327, 522946.8100891276, 519763.65357184474, 516322.28887630557], 
                        'pv_only_total_cost': 10519137.659767631, 
                        'pv_only_total_cost_change': -60278338.87360199, 
                        'es_pv_cost': [-1673077.2856418313, -1403796.2599298835, -1323082.2527789788, -1245869.8357553424, -1172030.129844, -1101434.849395135, -1033957.6396549885, -969476.7539769456, -907874.892579432, -849039.0467873358, -792860.3485743048, -739233.9252292691, -688058.758976331, -639237.5513827626, -592676.592395287, -548285.6338500602, -505977.7673068495, -465669.3060628239, -427279.6712061152, -390731.2815739218], 
                        'es_pv_total_cost': -17469649.7829016, 
                        'es_pv_total_cost_change': -88267126.31627122, 
                        'baseline_ghg': [8592.344382834217, 8140.115731106102, 7687.887079377984, 7235.658427649868, 6783.429775921752, 6331.201124193636, 5878.97247246552, 5426.743820737402, 4974.515169009285, 4522.286517281166, 4070.0578655530517, 3617.829213824934, 3165.600562096817, 2713.3719103686994, 2261.1432586405845, 1808.914606912467, 1356.6859551843497, 904.4573034562349, 452.2286517281149, 0.0], 
                        'baseline_total_ghg': 85923.4438283422, 
                        'pv_only_ghg': [1893.6959098354944, 1920.9494645957075, 1844.1976878014664, 1763.9203065477532, 1680.1173208345656, 1592.7887306619057, 1501.9345360297732, 1407.554736938167, 1309.649333387088, 1208.2183253765356, 1103.2617129065104, 994.7794959770127, 882.7716745880416, 767.2382487395971, 648.1792184316807, 525.5945836642904, 399.48434443742707, 269.8485007510916, 136.68705260528156, 0.0], 
                        'pv_only_total_ghg': 21850.871184109386, 
                        'pv_only_total_ghg_change': -64072.572644232794, 
                        'es_pv_ghg': [-3377.207796050349, -2619.469930855495, -2383.063771227981, -2157.349382466086, -1942.3267645698104, -1737.9959175391543, -1544.3568413741177, -1361.4095360747, -1189.1540016409017, -1027.590238072723, -876.7182453701643, -736.538023533224, -607.0495725619032, -488.2528924562016, -380.14798321611994, -282.7348448416572, -196.01347733281378, -119.98388068959005, -54.64605491198504, 0.0], 
                        'es_pv_total_ghg': -23082.009154784977, 
                        'es_pv_total_ghg_change': -109005.45298312716}

        RESULTS_Yearly_Capacity = []
        RESULTS_Yearly_Energy = []
        RESULTS_Yearly_Cost = []
        RESULTS_Yearly_GHG = []
        self.results_data[analysis_name]['lifetime_analysis']['baseline_total_load'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_produced'] = 0
        self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_produced'] = 0

        for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life']):
            RESULTS_Yearly_Capacity_element = {'year': year+1, 
                                            'grid_pen': "{:.2f}%".format(self.results_data[analysis_name]['lifetime_analysis']['grid_pen'][year]),
                                            'pv_capacity': "{:.1f}%".format(self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year])}
            RESULTS_Yearly_Capacity_element['ess_capacity'] = {}
            for system in self.results_data[analysis_name]['lifetime_analysis']['ess_capacity']:
                RESULTS_Yearly_Capacity_element['ess_capacity'][system] = "{:.1f}%".format(self.results_data[analysis_name]['lifetime_analysis']['ess_capacity'][system][year])
            RESULTS_Yearly_Capacity.append(RESULTS_Yearly_Capacity_element)
            RESULTS_Yearly_Energy.append({'year': year+1, 
                                          "load": format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_yearly_load']),
                                          'pv_only_produced': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]*self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_produced']/100),
                                          'es_pv_produced': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]*self.results_data[analysis_name]['lifetime_analysis']['es_pv_yearly_produced']/100)})
            
            self.results_data[analysis_name]['lifetime_analysis']['baseline_total_load'] += self.results_data[analysis_name]['lifetime_analysis']['baseline_yearly_load']
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_produced'] += self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]*self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_produced']/100
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_produced'] += self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]*self.results_data[analysis_name]['lifetime_analysis']['es_pv_yearly_produced']/100

            RESULTS_Yearly_Cost.append({'year': year+1, 
                                          "baseline_cost": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][year]),
                                          "pv_only_cost": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'][year]),
                                          "pv_only_cost_impact": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][year]-self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'][year]),
                                          "es_pv_cost": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'][year]),
                                          "es_pv_cost_impact": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][year]-self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'][year])})
            RESULTS_Yearly_GHG.append({'year': year+1, 
                                          "baseline_ghg": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][year]),
                                          "pv_only_ghg": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][year]),
                                          "pv_only_ghg_impact": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][year]-self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][year]),
                                          "es_pv_ghg": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][year]),
                                          "es_pv_ghg_impact": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][year]-self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][year])})
            
        RESULTS_Yearly_Energy.append({'year': '-TOTAL-', 'load': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_load']),
                                        'pv_only_produced': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_produced']), 
                                        'es_pv_produced': format_energy_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_produced'])})
        
        RESULTS_Yearly_Cost.append({'year': '-TOTAL-', 
                                          "baseline_cost": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_cost']),
                                          "pv_only_cost": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_cost']),
                                          "pv_only_cost_impact": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_cost']-self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_cost']),
                                          "es_pv_cost": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_cost']),
                                          "es_pv_cost_impact": format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_cost']-self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_cost'])})
        RESULTS_Yearly_GHG.append({'year': '-TOTAL-', 
                                          "baseline_ghg": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_ghg']),
                                          "pv_only_ghg": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_ghg']),
                                          "pv_only_ghg_impact": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_ghg']-self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_ghg']),
                                          "es_pv_ghg": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_ghg']),
                                          "es_pv_ghg_impact": format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_ghg']-self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_ghg'])})

        
        executive_summary = self.generate_executive_summary()

        template_dir = os.path.join('report_templates')

        output_dir = self.results_data['report_information']['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        moer_chart_file = self.plot_moer_data(output_dir)
        pv_chart_file = self.plot_solar_data(output_dir)
        load_chart_file = self.plot_load_data(output_dir)
        energy_price_chart_file = self.plot_energy_price_data(output_dir)
        demand_price_chart_file = self.plot_demand_price_data(output_dir)
        #time (hr),Demand Price ($/kW),Energy Price ($/kWh),CO2 Rate (tons/kWh),Load (kW),Net Load (kW),PV_Avalible (kW),PV_Curtailment (kW),EOS Battery Model Power (kW),EOS Battery Model SOC (%),Invinity Battery Model Power (kW),Invinity Battery Model SOC (%)

        #print(pv_chart_file)

        #chart_list = find_images_in_directory(output_dir)

        dynamic_power_limits_charts = self.plot_system_constraints_data(output_dir)
        monthly_energy_bar_chart_file = self.monthly_energy_bar_chart(output_dir)
        monthly_cost_bar_chart_file = self.monthly_cost_bar_chart(output_dir)
        monthly_ghg_bar_chart_file = self.monthly_ghg_bar_chart(output_dir)
        yearly_capacity_bar_chart_file = self.yearly_capacity_bar_chart(output_dir)
        yearly_energy_bar_chart_file = self.yearly_energy_bar_chart(output_dir)
        yearly_cost_bar_chart_file = self.yearly_cost_bar_chart(output_dir)
        yearly_ghg_bar_chart_file = self.yearly_ghg_bar_chart(output_dir)

        # Print the chart_list for verification
        #for chart in dynamic_power_limits_charts:
            #print(chart)

        # Initialize Jinja environment.
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(['html']))
        #print(executive_summary)
        template = env.get_template('btm_cost_ghg_impacts.html')
        fname = os.path.join(output_dir, 'BTM_cost_ghg_impacts.html')

        # Render output file.
        output = template.render(
                        # GENERAL OUTPUT
                        today=today,
                        header="This report shows the results for " + analysis_name,
                        ANALSYS_Configuration=ANALSYS_Configuration,
                        MOER_Info=MOER_Info,
                        SOLAR_Info=SOLAR_Info,
                        ESS_System_Info=ESS_System_Info,
                        Utility_Info=Utility_Info,
                        GRID_Limit_Info=GRID_Limit_Info,
                        QuESt_Logo=os.path.join(os.getcwd(), 'images', 'images', 'Quest_Logo_RGB.png'),
                        SNL_image=os.path.join(os.getcwd(), 'images', 'images', 'SNL_Stacked_Black_Blue.jpg'),
                        DOE_image=os.path.join(os.getcwd(), 'images', 'images', '0052_state-of-ca-energy-commission.jpg'),
                        acknowledgement="Sandia National Laboratories is a multimission laboratory managed and operated by National Technology & Engineering Solutions of Sandia, LLC, a wholly owned subsidiary of Honeywell International Inc., for the U.S. Department of Energy's National Nuclear Security Administration under contract DE-NA0003525.",
                        executive_summary=executive_summary,
                        report_information = self.results_data['report_information'],
                        results_data = self.results_data[analysis_name],
                        RESULTS_Monthly_Energy = RESULTS_Monthly_Energy,
                        RESULTS_Monthly_Cost = RESULTS_Monthly_Cost,
                        RESULTS_Monthly_GHG = RESULTS_Monthly_GHG,
                        RESULTS_Yearly_Capacity = RESULTS_Yearly_Capacity,
                        RESULTS_Yearly_Energy = RESULTS_Yearly_Energy,
                        RESULTS_Yearly_Cost = RESULTS_Yearly_Cost,
                        RESULTS_Yearly_GHG = RESULTS_Yearly_GHG,
                        # FIGURES
                        moer_chart = {'path': moer_chart_file, 'idx' : '1-1', 'caption': 'Monthly MOER Timeseries Plot'},
                        pv_chart = {'path': pv_chart_file, 'idx' : '1-2', 'caption': 'Monthly Solar Timeseries Plot'},
                        energy_price_chart = {'path': energy_price_chart_file, 'idx' : '1-3', 'caption': 'Monthly Energy Price Timeseries Plot'},
                        demand_price_chart = {'path': demand_price_chart_file, 'idx' : '1-4', 'caption': 'Monthly Demand Price Timeseries Plot'},
                        load_chart = {'path': load_chart_file, 'idx' : '1-5', 'caption': 'Monthly Site Load Timeseries Plot'},
                        monthly_energy_bar_chart = {'path': monthly_energy_bar_chart_file, 'idx' : '3-1', 'caption': '  Monthly Energy Bar Chart'},
                        monthly_cost_bar_chart = {'path': monthly_cost_bar_chart_file, 'idx' : '3-2', 'caption': '  Monthly Cost Bar Chart'},
                        monthly_ghg_bar_chart = {'path': monthly_ghg_bar_chart_file, 'idx' : '3-3', 'caption': '  Monthly Emissions Bar Chart'},
                        yearly_capacity_bar_chart = {'path': yearly_capacity_bar_chart_file, 'idx' : '3-4', 'caption': '  Yearly Capacity Bar Chart'},
                        yearly_energy_bar_chart = {'path': yearly_energy_bar_chart_file, 'idx' : '3-5', 'caption': '  Yearly Energy Bar Chart'},
                        yearly_cost_bar_chart = {'path': yearly_cost_bar_chart_file, 'idx' : '3-6', 'caption': '  Yearly Cost Bar Chart'},
                        yearly_ghg_bar_chart = {'path': yearly_ghg_bar_chart_file, 'idx' : '3-7', 'caption': '  Yearly Emissions Bar Chart'},
                        dynamic_power_limits_charts = dynamic_power_limits_charts
					)

        with open(fname,"w") as f:
            f.write(output)
        
        webbrowser.open('file://' + os.path.realpath(fname))

    def generate_executive_summary(self):
        """Generates an executive summary similar to the report screen using chart data."""

        keys = list(self.results_data.keys())
        analysis_name = keys[0]

        chart_data = range(10)
        month = "January"
        if self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['Data File Name'] == 'PVWatts Data':
            pv_ac_power = (float(self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['DC System Size (kW)'])/  
                           float(self.results_data[analysis_name]['January']['analysis_inputs']['solar_site_data']['DC to AC Size Ratio']))/1000
        else:
            pv_ac_power = self.results_data[analysis_name][month]['analysis_inputs']['solar_site_data']['AC Power Rating']

        es_power = sum([self.results_data[analysis_name][month]['analysis_inputs']['system_data']['System {num}'.format(num=i+1)]['Discharge Power Limit'] for i in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data']))])
        es_energy = sum([self.results_data[analysis_name][month]['analysis_inputs']['system_data']['System {num}'.format(num=i+1)]['Energy Capacity'] for i in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data']))])
        
        
        
        executive_summary_strings = []
        intro_string_1 = "This report presents an analysis of the greenhouse gas (GHG) impact and cost implications of an energy storage project in California.  " 
        intro_string_2 = "The analysis employs the marginal operating emissions rate (MOER) signal to establish GHG emissions impact and the local utility ({utility}) rates to estimate electricity costs. ".format(utility=self.results_data[analysis_name][month]['analysis_inputs']['selected_utility_rate']['utility'])
        intro_string_3 = "The report's results are divided into three parts: baseline results, solar only results, and solar + energy storage results.  "
        intro_string_4 = "The baseline results include estimates for the emissions and electricity costs incurred by the site load during the Quantification Period.  "
        intro_string_5 = "The solar only results and solar + energy storage results assess Energy Cost Savings ($), Renewable Energy Generation (kWh), and GHG Reductions (TCO2e) in each scenario.   "
        
        baseline_string_1 = "Baseline Assessment: The customer's electric load generates approximately {baseline_co2} annually, with an associated electricity bill of {baseline_cost} per year. ".format(
            baseline_co2=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][0]),
            baseline_cost=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][0]))
        baseline_string_2 = "Over the {project_life} year Quantification Period, accounting for increasing renewable penetration levels on California's grid, the total emissions in the baseline scenario is estimated at {baseline_total_co2}. ".format(
            project_life=self.results_data[analysis_name]['lifetime_analysis']['project_life'],
            baseline_total_co2=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_ghg']))
        baseline_string_3 = "With a {discount_rate} % annual discount rate, the net present value of future electricity bills is estimated to be {baseline_total_cost}. ".format(
            discount_rate=self.results_data[analysis_name]['lifetime_analysis']['discount_rate'], 
            baseline_total_cost=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_total_cost']))
        
        solar_only_string_1 = "Impact of Solar Installation: The report further examines the emissions and cost reductions achieved through the installation of a solar power. "


        pv_only_energy = 0
        pv_only_c_energy = 0
        pvc_energy = 0
        pvc_net_energy = 0

        for month in self.MONTH_NAMES:
            pv_only_energy += sum([(self.results_data[analysis_name][month]['PV'][i] - self.results_data[analysis_name][month]['pv_only_c'][i])*self.results_data[analysis_name][month]['analysis_inputs']['analysis_configuration']['timestep']/60 for i in range(len(self.results_data[analysis_name][month]['PV']))]) 
            pv_only_c_energy += sum([self.results_data[analysis_name][month]['pv_only_c'][i]*self.results_data[analysis_name][month]['analysis_inputs']['analysis_configuration']['timestep']/60 for i in range(len(self.results_data[analysis_name][month]['PV']))]) 
            pvc_energy += sum([self.results_data[analysis_name][month]['pvc'][i]*self.results_data[analysis_name][month]['analysis_inputs']['analysis_configuration']['timestep']/60 for i in range(len(self.results_data[analysis_name][month]['PV']))]) 
            pvc_net_energy += sum([(self.results_data[analysis_name][month]['PV'][i] - self.results_data[analysis_name][month]['pvc'][i])*self.results_data[analysis_name][month]['analysis_inputs']['analysis_configuration']['timestep']/60 for i in range(len(self.results_data[analysis_name][month]['PV']))]) 
            

        solar_only_string_2 = "With an ac rating of {pv_ac_power} MW, the solar installation alone is estimated to produce {pv_energy} of renewable energy per year (with {pv_only_c_energy} of solar curtailed). ".format(
            pv_ac_power=pv_ac_power, 
            pv_energy = format_energy_string(pv_only_energy),
            pv_only_c_energy = format_energy_string(pv_only_c_energy))
        solar_only_string_3 = "This would reduce the customer's annual emissions by {pv_only_ghg_change}, resulting in a new total of {pv_only_ghg} per year. ".format(
            pv_only_ghg_change=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'][0]-self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][0]),
            pv_only_ghg=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][0]))
        solar_only_string_4 = "Additionally, the solar system decreases the electricity bill by {pv_only_cost_change} per year, resulting in a annual cost of {pv_only_cost}. ".format(
            pv_only_cost=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'][0]), 
            pv_only_cost_change=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][0]-self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'][0]))
        

        total_RE = 0
        for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life']):
            total_RE += (self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]/100)*pv_only_energy

        solar_only_string_5 = "The impact of the solar power system over the quantification period is estimated to produce {total_RE} kWh of renewable energy, reduce emissions by {pv_only_ghg_change} to {pv_only_ghg}, ".format(
            total_RE = format_energy_string(total_RE),
            pv_only_ghg_change=format_tons_string(-self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_ghg_change']),
            pv_only_ghg=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_ghg']))  +\
                              "reduce the net present value of future electricity bills by {pv_only_total_cost_change} to {pv_only_total_cost}.".format(
            pv_only_total_cost_change= format_dollar_string(-self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_cost_change']), 
            pv_only_total_cost= format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_cost']))
        
        es_pv_string_1 = "Combined Impact of Solar and Battery Storage: The final assessment evaluates the synergistic effects of integrating a long-duration battery storage system with the solar installation. " 
        es_pv_string_2 = "The battery system(s), with a capacity of {ess_power_total} MW and {ess_energy_total} MWh, allows for enhanced energy management, further reducing the customer's annual emissions and costs. ".format(
            ess_power_total=es_power,
            ess_energy_total=es_energy)
        es_pv_string_3 = "The energy storage reduces annual solar curtailment to {pvc_energy}, increasing the estimated renewable energy production to {pvc_net_energy} per year. ".format(
            pvc_energy=format_energy_string(pvc_energy),
            pvc_net_energy=format_energy_string(pvc_net_energy))     
        es_pv_string_4 = "This has the impact of reducing the customer's annual emissions by an additional {change_from_pv_only_to_ess_and_pv_ghg} to a new total of {es_pv_ghg} annually. ".format(
            change_from_pv_only_to_ess_and_pv_ghg=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'][0] - self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][0]),
            es_pv_ghg=format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][0]))      
        if self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'][0] < 0:
            es_pv_string_4 += "This negative value means that the project offsets the GHG emissions of other electrical loads on the California grid. "

        es_pv_string_5 = "The combined solar and battery systems also lead to a further reduction in the electricity bill by {change_from_pv_only_to_ess_and_pv_cost} to {es_pv_cost} per year. ".format(
            change_from_pv_only_to_ess_and_pv_cost=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'][0] - self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'][0]),
            es_pv_cost=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'][0]))
        es_pv_string_6 = "The project manages to reduce the quantification period emissions of the site by {es_pv_total_ghg_change} to {es_pv_total_ghg}, and reduce the net present value of future electricity bills by {es_pv_total_cost_change} to {es_pv_total_cost}.".format(
            es_pv_total_ghg_change= format_tons_string(-self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_ghg_change']), 
            es_pv_total_ghg= format_tons_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_ghg']), 
            es_pv_total_cost_change=format_dollar_string(-self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_cost_change']), 
            es_pv_total_cost=format_dollar_string(self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_cost']))

        executive_summary_strings.append(intro_string_1 + intro_string_2 +intro_string_3 +intro_string_4 +intro_string_5)
        executive_summary_strings.append(baseline_string_1 +baseline_string_2 + baseline_string_3)
        executive_summary_strings.append(solar_only_string_1 + solar_only_string_2 + solar_only_string_3  + solar_only_string_4 + solar_only_string_5)
        executive_summary_strings.append(es_pv_string_1 + es_pv_string_2 + es_pv_string_3 + es_pv_string_4 + es_pv_string_5 + es_pv_string_6)

        return executive_summary_strings

    def plot_moer_data(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(12, 12))
            ax = plt.subplot(6,2,1)

            # Plot each month as a separate line
            plot_num = 1
            for month in self.MONTH_NAMES:
                ax = plt.subplot(6,2,plot_num)
                t = [self.results_data[analysis_name][month]['t'][i]/24 for i in range(len(self.results_data[analysis_name][month]['t']))]
                MOER = self.results_data[analysis_name][month]['MOER']
                ax.plot(t, MOER, label=month, linewidth=2)
                ax.axis([0,31,0,1.1*max(MOER)])
                ax.set_ylabel('MOER (tons/kWh)', fontsize=14)
                ax.set_title(month)
                plot_num += 1


            ax.set_xlabel('Day of the Month', fontsize=14)
            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_moer_timeseries_plot.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the plot_moer_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    

    def monthly_energy_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set up the bar chart
            bar_width = 0.2
            baseline_load = []
            pv_only_pro = []
            pv_only_net = []
            pv_only_cur = []
            es_pv_pro = []
            es_pv_net = []
            es_pv_cur = []

            for month in self.MONTH_NAMES:
                baseline_load.append(self.results_data[analysis_name][month]['Baseline Energy (load)'])
                pv_only_pro.append(self.results_data[analysis_name][month]['PV Only Energy (pro)'])
                pv_only_net.append(self.results_data[analysis_name][month]['PV Only Energy (net)'])
                pv_only_cur.append(self.results_data[analysis_name][month]['PV Only Curtailed PV'])
                es_pv_pro.append(self.results_data[analysis_name][month]['ES + PV Energy (pro)'])
                es_pv_net.append(self.results_data[analysis_name][month]['ES + PV Energy (net)'])
                es_pv_cur.append(self.results_data[analysis_name][month]['ES + PV Curtailed PV'])

            
            x = np.arange(len(baseline_load))


            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x - bar_width*1.5, baseline_load, width=bar_width, label='Baseline Load')
            ax.bar(x, pv_only_pro, width=bar_width, label='PV Only RE Produced')
            ax.bar(x + bar_width*1.5, es_pv_pro, width=bar_width, label='ES + PV RE Produced')

            ax.set_xticks(x, [self.MONTH_NAMES[month] for month in range(len(x))], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Energy (kWh)', fontsize=14)
            ax.legend()

            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_energy_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            plt.close()

            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the monthly_energy_bar_chart function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def monthly_cost_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set up the bar chart
            bar_width = 0.2
            baseline_cost = []
            pv_only_cost = []
            es_pv_cost = []

            for month in self.MONTH_NAMES:
                baseline_cost.append(self.results_data[analysis_name][month]['Baseline Cost'])
                pv_only_cost.append(self.results_data[analysis_name][month]['PV Only Cost'])
                es_pv_cost.append(self.results_data[analysis_name][month]['ES + PV Cost'])
            
            x = np.arange(len(baseline_cost))

            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x - bar_width*1.5, baseline_cost, width=bar_width, label='Baseline Cost')
            ax.bar(x, pv_only_cost, width=bar_width, label='PV Only Cost')
            ax.bar(x + bar_width*1.5, es_pv_cost, width=bar_width, label='ES + PV Cost')

            ax.set_xticks(x, [self.MONTH_NAMES[month] for month in range(len(x))], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Cost ($)', fontsize=14)
            ax.legend()

            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_cost_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the monthly_cost_bar_chart function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def monthly_ghg_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set up the bar chart
            bar_width = 0.2
            baseline_ghg = []
            pv_only_ghg = []
            es_pv_ghg = []

            for month in self.MONTH_NAMES:
                baseline_ghg.append(self.results_data[analysis_name][month]['Baseline GHG'])
                pv_only_ghg.append(self.results_data[analysis_name][month]['PV Only GHG'])
                es_pv_ghg.append(self.results_data[analysis_name][month]['ES + PV GHG'])
            
            x = np.arange(len(baseline_ghg))

            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x - bar_width*1.5, baseline_ghg, width=bar_width, label='Baseline Emissions ')
            ax.bar(x, pv_only_ghg, width=bar_width, label='PV Only Emissions ')
            ax.bar(x + bar_width*1.5, es_pv_ghg, width=bar_width, label='ES + PV Emissions ')

            ax.set_xticks(x, [self.MONTH_NAMES[month] for month in range(len(x))], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Emissions  (TCO2e)', fontsize=14)
            ax.legend()

            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_ghg_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the monthly_ghg_bar_chart function of the BtmGenerateReport Class  : %s", str(e))

        return filename

    def yearly_capacity_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]

        try:
            # Set up the bar chart
            x = np.arange(self.results_data[analysis_name]['lifetime_analysis']['project_life'])

            re_pen = self.results_data[analysis_name]['lifetime_analysis']['grid_pen']
            pv_capacity = self.results_data[analysis_name]['lifetime_analysis']['pv_capacity']
            
            # Set the figure size and style

            num_bars = 2 + len(self.results_data[analysis_name]['lifetime_analysis']['ess_capacity'])
            #print("num_bars : " + str(num_bars))
            bar_width = 0.6 / num_bars
            bar_offset = np.linspace(-0.3,0.3,num_bars)
            #print("bar_offset : " + str(bar_offset))

            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x + bar_offset[0], re_pen, width=bar_width, label='Baseline Cost')
            ax.bar(x + bar_offset[1], pv_capacity, width=bar_width, label='PV Only Cost')
            
            for system in self.results_data[analysis_name]['lifetime_analysis']['ess_capacity']:
                sys = 'System '+str(system+1)
                ax.bar(x + bar_offset[2+system], self.results_data[analysis_name]['lifetime_analysis']['ess_capacity'][system], width=bar_width, label=self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][sys]['System Name'])

            ax.set_xticks(x, ["Year {var1}".format(var1=year+1) for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life'])], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Capacity (%)', fontsize=14)

            #plt.tight_layout()  # Adjust layout to make room for labels
            # Shrink current axis by 20%
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

            # Put a legend to the right of the current axis
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'yearly_capacity_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the yearly_capacity_bar_chart function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def yearly_energy_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set up the bar chart
            x = np.arange(self.results_data[analysis_name]['lifetime_analysis']['project_life'])

            baseline_energy = []
            pv_only_energy = []
            es_pv_energy = []
            num_bars = 2
            for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life']):
                baseline_energy.append(self.results_data[analysis_name]['lifetime_analysis']['baseline_yearly_load'])
                pv_only_energy.append(self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]*self.results_data[analysis_name]['lifetime_analysis']['pv_only_yearly_produced']/100)
                es_pv_energy.append(self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'][year]*self.results_data[analysis_name]['lifetime_analysis']['es_pv_yearly_produced']/100)

            bar_width = 0.2
            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x - bar_width*1.5, baseline_energy, width=bar_width, label='Baseline Load')
            ax.bar(x, pv_only_energy, width=bar_width, label='PV Only RE Produced')
            ax.bar(x + bar_width*1.5, es_pv_energy, width=bar_width, label='ES + PV RE Produced')

            ax.set_xticks(x, ["Year {var1}".format(var1=year+1) for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life'])], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Energy  (kWh)', fontsize=14)

            plt.tight_layout()  # Adjust layout to make room for labels
            ax.legend()

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'yearly_energy_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the yearly_energy_bar_chart function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def yearly_cost_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set up the bar chart
            bar_width = 0.2
            x = np.arange(self.results_data[analysis_name]['lifetime_analysis']['project_life'])

            baseline_cost = self.results_data[analysis_name]['lifetime_analysis']['baseline_cost']
            pv_only_cost = self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost']
            es_pv_cost = self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost']

            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x - bar_width*1.5, baseline_cost, width=bar_width, label='Baseline Cost')
            ax.bar(x, pv_only_cost, width=bar_width, label='PV Only Cost')
            ax.bar(x + bar_width*1.5, es_pv_cost, width=bar_width, label='ES + PV Cost')

            ax.set_ylabel('Net Present Cost ($)')
            ax.set_xticks(x, ["Year {var1}".format(var1=year+1) for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life'])], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Cost ($)', fontsize=14)

            plt.tight_layout()  # Adjust layout to make room for labels
            ax.legend()

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'yearly_cost_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the plot_timeseries_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def yearly_ghg_bar_chart(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set up the bar chart
            bar_width = 0.2
            x = np.arange(self.results_data[analysis_name]['lifetime_analysis']['project_life'])

            baseline_ghg = self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg']
            pv_only_ghg = self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg']
            es_pv_ghg = self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg']

            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(8, 4))
            ax = plt.subplot(1,1,1)
            ax.bar(x - bar_width*1.5, baseline_ghg, width=bar_width, label='Baseline Emissions ')
            ax.bar(x, pv_only_ghg, width=bar_width, label='PV Only Emissions ')
            ax.bar(x + bar_width*1.5, es_pv_ghg, width=bar_width, label='ES + PV Emissions ')

            ax.set_xticks(x, ["Year {var1}".format(var1=year+1) for year in range(self.results_data[analysis_name]['lifetime_analysis']['project_life'])], rotation=90)  # Rotate month names 90 degrees
            ax.set_ylabel('Emissions  (TCO2e)', fontsize=14)

            plt.tight_layout()  # Adjust layout to make room for labels
            ax.legend()

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'yearly_ghg_bar_chart.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
            
            plt.close()
            # Show the plot (optional)
            #plt.show()
        except Exception as e:
            logging.error("There was an error in the plot_timeseries_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def plot_system_constraints_data(self,path_to_save):
        check = True
        analysis_name = list(self.results_data.keys())[0]
        chart_list = []
        try:
            AChaEOS = []
            bChaEOS = []
            ADisEOS = []
            bDisEOS = []
            sys_num = 1

            for system in self.results_data[analysis_name]['January']['analysis_inputs']['system_data']:
                system_name =  self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['System Name']
                energy_capacity =  self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Energy Capacity']
                charge_power_limit = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Charge Power Limit']
                discharge_power_limit = -self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Discharge Power Limit']
                round_trip_efficiency = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Round-Trip-Efficiency']
                self_dischage_rate = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Self-Discharge Rate']
                max_soc = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Max SOC']
                min_soc = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Min SOC']
                initial_degredation_rate = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Degradation Rate in Year 1']
                degredation_rate = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Degradation Rate Year > 1']

                for limit in self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits']:
                    region = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits'][limit]['Region']
                    slope = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits'][limit]['Slope']
                    intercept = self.results_data[analysis_name]['January']['analysis_inputs']['system_data'][system]['Dynamic Power Limits'][limit]['Intercept']
                    if region == "Charge":
                        AChaEOS.append(slope)
                        bChaEOS.append(intercept)
                    if region == "Discharge":
                        ADisEOS.append(slope)
                        bDisEOS.append(intercept)
                
                AChaEOS.append(0)
                bChaEOS.append(charge_power_limit)
                ADisEOS.append(0)
                bDisEOS.append(discharge_power_limit)

                #print("AChaEOS: " + str(AChaEOS))
                #print("bChaEOS: " + str(bChaEOS))
                #print("ADisEOS: " + str(ADisEOS))
                #print("bDisEOS: " + str(bDisEOS))

                N = 101
                x = range(N)
                soc_x = np.linspace(min_soc,max_soc,N)

                CHA_LIM = [min([AChaEOS[i]*j + bChaEOS[i] for i in range(len(bChaEOS))]) for j in x]
                DIS_LIM = [max([ADisEOS[i]*j + bDisEOS[i] for i in range(len(bDisEOS))]) for j in x]

                plt.style.use('seaborn-v0_8-darkgrid')
                plt.figure(figsize=(8, 4))

                # plot area charts
                plt.fill_between(soc_x,CHA_LIM,0, label='Charge Region', color='darkblue', linewidth=4)
                plt.fill_between(soc_x,DIS_LIM,0, label='Disharge Region', color='darkred', linewidth=4)

                # Add titles and labels
                plt.xlabel('SOC (%)', fontsize=14)
                plt.ylabel('Power (MW)', fontsize=14)
                plt.tight_layout()  # Adjust layout to make room for labels
                plt.axis([0,100, 1.1*discharge_power_limit,1.1*charge_power_limit])
                plt.grid(True)

                # Save the figure with full resolution
                filename = os.path.join(path_to_save, system_name.replace(' ', '_') + '_dynamic_limits_plot' + '.png')
                plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI
                plt.close()

                chart_info = {'path': filename, 'idx' : '2-'+str(sys_num), 'caption': system_name + ' Dynamic Power Limits Plot'}
                chart_list.append(chart_info)

                #plt.show()
                sys_num += 1

        except Exception as e:
            logging.error("There was an error in the plot_system_constraints_data function of the BtmGenerateReport Class  : %s", str(e))
        
        return chart_list
    
    def plot_solar_data(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(12, 12))
            ax = plt.subplot(6,2,1)

            # Plot each month as a separate line
            plot_num = 1
            for month in self.MONTH_NAMES:
                ax = plt.subplot(6,2,plot_num)
                t = [self.results_data[analysis_name][month]['t'][i]/24 for i in range(len(self.results_data[analysis_name][month]['t']))]
                PV = self.results_data[analysis_name][month]['PV']
                ax.plot(t, PV, label=month, linewidth=2, color='green')
                ax.axis([0,31,0,1.1*max(PV)])
                ax.set_ylabel('Power (kW)', fontsize=14)
                ax.set_title(month)
                plot_num += 1


            ax.set_xlabel('Day of the Month', fontsize=14)
            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_solar_timeseries_plot.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI

            plt.close()
            # Show the plot (optional)
            #plt.show()

        except Exception as e:
            logging.error("There was an error in the plot_solar_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename

    
    def plot_load_data(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(12, 12))
            ax = plt.subplot(6,2,1)

            # Plot each month as a separate line
            plot_num = 1
            for month in self.MONTH_NAMES:
                ax = plt.subplot(6,2,plot_num)
                t = [self.results_data[analysis_name][month]['t'][i]/24 for i in range(len(self.results_data[analysis_name][month]['t']))]
                LOAD = self.results_data[analysis_name][month]['LOAD']
                ax.plot(t, LOAD, label=month, linewidth=2, color='orange')
                ax.axis([0,31,0,1.1*max(LOAD)])
                ax.set_ylabel('Load (kW)', fontsize=14)
                ax.set_title(month)
                plot_num += 1


            ax.set_xlabel('Day of the Month', fontsize=14)
            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_load_timeseries_plot.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI

            plt.close()
            # Show the plot (optional)
            #plt.show()

        except Exception as e:
            logging.error("There was an error in the plot_load_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename

    def plot_energy_price_data(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(12, 12))
            ax = plt.subplot(6,2,1)

            # Plot each month as a separate line
            plot_num = 1
            for month in self.MONTH_NAMES:
                ax = plt.subplot(6,2,plot_num)
                t = [self.results_data[analysis_name][month]['t'][i]/24 for i in range(len(self.results_data[analysis_name][month]['t']))]
                ENERGY_PRICE = self.results_data[analysis_name][month]['ENERGY_PRICE']
                ax.plot(t, ENERGY_PRICE, label=month, linewidth=2, color='c')
                ax.axis([0,31,0,1.1*max(ENERGY_PRICE)])
                ax.set_ylabel('Energy Price ($/kWh)', fontsize=14)
                ax.set_title(month)
                plot_num += 1


            ax.set_xlabel('Day of the Month', fontsize=14)
            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_energy_price_timeseries_plot.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI

            plt.close()
            # Show the plot (optional)
            #plt.show()

        except Exception as e:
            logging.error("There was an error in the plot_energy_price_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename
    
    def plot_demand_price_data(self, path_to_save):
        analysis_name = list(self.results_data.keys())[0]
        try:
            # Set the figure size and style
            plt.style.use('seaborn-v0_8-darkgrid')
            plt.figure(figsize=(12, 12))
            ax = plt.subplot(6,2,1)

            # Plot each month as a separate line
            plot_num = 1
            for month in self.MONTH_NAMES:
                ax = plt.subplot(6,2,plot_num)
                t = [self.results_data[analysis_name][month]['t'][i]/24 for i in range(len(self.results_data[analysis_name][month]['t']))]
                DEMAND_PRICE = self.results_data[analysis_name][month]['DEMAND_PRICE']
                ax.plot(t, DEMAND_PRICE, label=month, linewidth=2, color='darkred')
                ax.axis([0,31,0,1.1*max(DEMAND_PRICE)])
                ax.set_ylabel('Demand Price ($/kW)', fontsize=14)
                ax.set_title(month)
                plot_num += 1


            ax.set_xlabel('Day of the Month', fontsize=14)
            plt.tight_layout()  # Adjust layout to make room for labels

            # Save the figure with full resolution
            filename = os.path.join(path_to_save,'monthly_demand_price_timeseries_plot.png')
            plt.savefig(filename, dpi=300)  # Save as PNG with 300 DPI

            plt.close()
            # Show the plot (optional)
            #plt.show()

        except Exception as e:
            logging.error("There was an error in the plot_demand_price_data function of the BtmGenerateReport Class  : %s", str(e))

        return filename


def format_caption(filename):
    # Remove the file extension
    name_without_extension = os.path.splitext(filename)[0]
    # Split by underscores and capitalize each word
    words = name_without_extension.split('_')
    capitalized_words = [word.capitalize() for word in words]
    # Join the words back into a single string
    caption = ' '.join(capitalized_words)
    # Replace 'ghg' with the desired replacement string
    caption = caption.replace('Ghg', 'GHG')  # Change 'YourReplacementString' to your desired text
    return caption

def find_images_in_directory(directory):
    chart_list = []
    # Supported image file extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')

    for root, dirs, files in os.walk(directory):
        idx = 0
        for file in files:
            if file.lower().endswith(image_extensions):
                # Create chart_info dictionary
                chart_info = {
                    'path':  file,
                    'idx' : idx,
                    'caption': format_caption(file)
                }
                chart_list.append(chart_info)
                idx +=1

    return chart_list

def format_dollar_string(amount):
    if amount < 0:
        sign = '-'
        amount = abs(amount)
    else:
        sign = ''

    if amount < 1_000:
        if amount < 10:
            formatted_amount = f"${amount:.3f}"
        elif amount < 100:
            formatted_amount = f"${amount:.2f}"
        else:
            formatted_amount = f"${amount:.1f}"
    elif amount < 1_000_000:
        if amount / 1_000 < 10:
            formatted_amount = f"${amount / 1_000:.3f}k"
        elif amount / 1_000 < 100:
            formatted_amount = f"${amount / 1_000:.2f}k"
        else:
            formatted_amount = f"${amount / 1_000:.1f}k"   
    elif amount < 1_000_000_000:
        if amount / 1_000_000 < 10:
            formatted_amount = f"${amount / 1_000_000:.3f}M"
        elif amount / 1_000_000 < 100:
            formatted_amount = f"${amount / 1_000_000:.2f}M"
        else:
            formatted_amount = f"${amount / 1_000_000:.1f}M"
    elif amount < 1_000_000_000_000:
        if amount / 1_000_000_000 < 10:
            formatted_amount = f"${amount / 1_000_000_000:.3f}B"
        elif amount / 1_000_000_000 < 100:
            formatted_amount = f"${amount / 1_000_000_000:.2f}B"
        else:
            formatted_amount = f"${amount / 1_000_000_000:.1f}B"
    else:
        if amount / 1_000_000_000_000 < 10:
            formatted_amount = f"${amount / 1_000_000_000_000:.3f}T"
        elif amount / 1_000_000_000_000 < 100:
            formatted_amount = f"${amount / 1_000_000_000_000:.2f}T"
        else:
            formatted_amount = f"${amount / 1_000_000_000_000:.1f}T"

    return sign + formatted_amount

def format_tons_string(amount):
    if amount < 0:
        sign = '-'
        amount = abs(amount)
    else:
        sign = ''

    if amount < 1_000:
        if amount < 10:
            formatted_amount = f"{amount:.3f} TCO2e"
        elif amount < 100:
            formatted_amount = f"{amount:.2f} TCO2e"
        else:
            formatted_amount = f"{amount:.1f} TCO2e"
    elif amount < 1_000_000:
        if amount / 1_000 < 10:
            formatted_amount = f"{amount / 1_000:.3f} kTCO2e"
        elif amount / 1_000 < 100:
            formatted_amount = f"{amount / 1_000:.2f} kTCO2e"
        else:
            formatted_amount = f"{amount / 1_000:.1f} kTCO2e"   
    elif amount < 1_000_000_000:
        if amount / 1_000_000 < 10:
            formatted_amount = f"{amount / 1_000_000:.3f} MTCO2e"
        elif amount / 1_000_000 < 100:
            formatted_amount = f"{amount / 1_000_000:.2f} MTCO2e"
        else:
            formatted_amount = f"{amount / 1_000_000:.1f} MTCO2e"
    elif amount < 1_000_000_000_000:
        if amount / 1_000_000_000 < 10:
            formatted_amount = f"{amount / 1_000_000_000:.3f} GTCO2e"
        elif amount / 1_000_000_000 < 100:
            formatted_amount = f"{amount / 1_000_000_000:.2f} GTCO2e"
        else:
            formatted_amount = f"{amount / 1_000_000_000:.1f} GTCO2e"

    return sign + formatted_amount

def format_energy_string(amount):
    if amount < 0:
        sign = '-'
        amount = abs(amount)
    else:
        sign = ''

    if amount < 1_000:
        if amount < 10:
            formatted_amount = f"{amount:.3f} Wh"
        elif amount < 100:
            formatted_amount = f"{amount:.2f} Wh"
        else:
            formatted_amount = f"{amount:.1f} Wh"
    elif amount < 1_000_000:
        if amount / 1_000 < 10:
            formatted_amount = f"{amount / 1_000:.3f} kWh"
        elif amount / 1_000 < 100:
            formatted_amount = f"{amount / 1_000:.2f} kWh"
        else:
            formatted_amount = f"{amount / 1_000:.1f} kWh"   
    elif amount < 1_000_000_000:
        if amount / 1_000_000 < 10:
            formatted_amount = f"{amount / 1_000_000:.3f} MWh"
        elif amount / 1_000_000 < 100:
            formatted_amount = f"{amount / 1_000_000:.2f} MWh"
        else:
            formatted_amount = f"{amount / 1_000_000:.1f} MWh"
    elif amount < 1_000_000_000_000:
        if amount / 1_000_000_000 < 10:
            formatted_amount = f"{amount / 1_000_000_000:.3f} GWh"
        elif amount / 1_000_000_000 < 100:
            formatted_amount = f"{amount / 1_000_000_000:.2f} GWh"
        else:
            formatted_amount = f"{amount / 1_000_000_000:.1f} GWh"

    return sign + formatted_amount

