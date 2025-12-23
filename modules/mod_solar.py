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

import pandas as pd
import requests
import os
import glob
import numpy as np
from datetime import datetime, timedelta

import logging

import pvlib.pvsystem as pv
import pvlib.location as loc
import pvlib.modelchain as mc
import pvlib

class Solar:
    """
    A class to handle solar generation data, downloading weather data, calculating solar generation using PVLib,
    and processing the data for Monte Carlo Simulation (MCS).
    """

    def __init__(self, site_name, lat, lon, tracking, ac, dc, directory, proxy_settings):
        """
        Initializes the Solar class with site data and directory.

        Parameters:
            site_name (str): Path to the CSV file containing site data.
            lat (str): Directory to save the data.
            long ():
            tracking ():
            ac ():
            dc (): 
            directory():
        """
        self.site_name = site_name
        self.lat = lat
        self.lon = lon
        self.tracking = tracking
        self.ac = ac
        self.dc = dc
        self.directory = directory
        self.proxy_settings = proxy_settings
        pass

    def SolarGen(self, api_key, your_name, your_affiliation, your_email, year_start, year_end):
        """
        Downloads weather data from NREL NSRDB and calculates solar generation using PVLib. 
        This function raises errors to allow calling function to notify the user of what error occured.

        Parameters:
            api_key (str): API key for NREL NSRDB.
            your_name (str): Your full name.
            your_affiliation (str): Your affiliation.
            your_email (str): Your email address.
            year_start (int): Start year for data download.
            year_end (int): End year for data download.
        """
        interval = '30'; utc = 'false'; reason = 'sandiaquest+testing'; mailing_list = 'false'

        self.year_range = range(year_start, year_end + 1)
        self.years = [str(num) for num in self.year_range]

        for year in self.years:

            # check if leap year
            if int(year)%4==0:
                leap_year = 'true'
            else:
                leap_year = 'false'

            name = self.site_name
            lat = self.lat
            lon = self.lon
            
            # download data for satellite
            url = 'https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}'\
                .format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, \
                email=your_email, mailing_list=mailing_list, affiliation=your_affiliation, reason=reason, \
                api=api_key)
            try: 
                response = requests.get(url, proxies=self.proxy_settings, verify=True)
                if response.status_code == 404:
                    raise requests.exceptions.HTTPError
            except requests.exceptions.HTTPError as http_err:
                # Handle HTTP errors (e.g., 404, 500)
                logging.error("HTTP error occurred: {http_err}".format(http_err=http_err))
                raise
            except requests.exceptions.ConnectionError as conn_err:
                # Handle connection errors
                logging.error("Connection error occurred: {conn_err}".format(conn_err=conn_err))
                raise
            except requests.exceptions.Timeout as timeout_err:
                # Handle timeout errors
                logging.error("Request timed out: {timeout_err}".format(timeout_err=timeout_err))
                raise
            except requests.exceptions.RequestException as req_err:
                # Handle any other request-related errors
                logging.error("An error occurred: {req_err}".format(req_err=req_err))
                raise
            else:
                # store data in csv file
                csv_data = response.text
                print(response)
                print(csv_data)

                # Split the original CSV data into lines
                lines = csv_data.strip().split('\n')

                print(lines)
                # Update the metadata in the first two rows
                lines[0] += ',AC Power Rating,DC Power Rating,Tracking,Year'
                lines[1] += f',{self.ac},{self.dc},{self.tracking},{year}'
                lines[2] += ',PV Power (MW)'

                # Join the lines back into a single string
                updated_csv_data = '\n'.join(lines)

                if not os.path.exists(f"{self.directory}/data/solar/{year}"):
                    os.makedirs(f"{self.directory}/data/solar/{year}")
                with open(f"{self.directory}/data/solar/{year}/{name}.csv", "w") as csv_file:                  
                    csv_file.write(updated_csv_data)
                print(lines[1].split(',')[7])
                timezone = pd.read_csv(f'{self.directory}/data/solar/{year}/{name}.csv', nrows=1)['Time Zone'][0]
                dataF = pd.read_csv(f'{self.directory}/data/solar/{year}/{name}.csv', skiprows=[0, 1])

                logging.info('NSRDB weather data for', name, 'for the year', year, 'obtained and saved to csv file.')

                # calculate weather data to solar generation data using pvlib
                ac = self.ac
                dc = self.dc
                tilt = round((lat*0.76+3.1), 0)

                system = pv.PVSystem(surface_tilt=tilt, surface_azimuth=180,
                                module_parameters={'pdc0': dc, 'gamma_pdc': -0.004},
                                inverter_parameters={'pdc0': ac},
                                temperature_model_parameters=pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
                                    'sapm']
                                ['open_rack_glass_glass'])

                location = loc.Location(lat, lon)
                mchain = mc.ModelChain.with_pvwatts(system, location)

                # prep weather data for mchain
                dataF.index = pd.to_datetime(dataF[['Year','Month','Day','Hour','Minute']])
                dataF.index = dataF.index.tz_localize(int(timezone)*3600)
                weather_sat = dataF[['DNI','GHI','DHI','Temperature','Wind Speed']].copy()
                weather_sat.columns = ['dni','ghi','dhi','temp_air','wind_speed']
                weather_cs = dataF[['Clearsky DNI','Clearsky GHI','Clearsky DHI','Temperature','Wind Speed']].copy()
                weather_cs.columns = ['dni','ghi','dhi','temp_air','wind_speed']

                # run mchain model for satellite data
                mchain.run_model(weather_sat)
                ac_power_sat = pd.DataFrame(mchain.results.ac)
                ac_power_sat.rename(columns={'p_mp': 'PV Power (MW)'}, inplace=True)

                ac_power_sat.to_csv(f'{self.directory}/data/solar/{year}/{name}_sgen_sat.csv')

                # run mchain model for clearsky data
                mchain.run_model(weather_cs)
                ac_power_cs = pd.DataFrame(mchain.results.ac)
                ac_power_cs.rename(columns={'p_mp': 'PV Power (MW)'}, inplace=True)

                ac_power_cs.to_csv(f'{self.directory}/data/solar/{year}/{name}_sgen_cs.csv')

proxy_settings = {}
proxy_settings['http'] = 'http://proxy.sandia.gov:80'
proxy_settings['https'] = 'http://proxy.sandia.gov:80'

if __name__ == '__main__':
    site_name = "TestSite101"   
    lat = 32.8423
    lon = -116.7054
    tracking = 'False'
    ac = 10
    dc = 13
    directory = "data/solar/"
    s = Solar(site_name,lat,lon,tracking,ac,dc,directory,proxy_settings=proxy_settings)
    api_key="UjChqcbtsDS8GGOtxwDxzBd99J26HQE2ZdiArlxh"
    your_name="David Rosewater"
    your_affiliation="Sandia National Laboratories"
    your_email="dmrose@sandia.gov"
    year_start=2020
    year_end=2020
    s.SolarGen(api_key, your_name, your_affiliation, your_email, year_start, year_end)