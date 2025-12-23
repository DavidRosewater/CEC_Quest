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
import os
import csv
import ast
import markdown
import webbrowser
import json
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

import zipfile
import logging
import requests
from datetime import datetime, timedelta
import calendar

# Create a custom logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG

# Create handlers
file_handler = logging.FileHandler('app.log')  # Log to a file
console_handler = logging.StreamHandler()        # Log to the console

# Set the logging level for handlers
file_handler.setLevel(logging.WARNING)  # Log warnings and above to the file
console_handler.setLevel(logging.ERROR)  # Log errors and above to the console

# Create formatters and add them to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# IMPORT / GUI AND MODULES AND WIDGETS
# ///////////////////////////////////////////////////////////////

from PyQt5 import QtCore, QtGui, QtWidgets

#from modules.app_functions import AppFunctions
from modules.app_settings import Settings
from modules.mod_solar import Solar
from modules.mod_btm_analysis import BTMAalysisManager
from modules.mod_reporting import BtmGenerateReport
import modules.resources_rc
from modules.ui_main import Ui_MainWindow

from widgets.custom_grips.custom_grips import CustomGrip, Widgets

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

# os.environ["QT_FONT_DPI"] = "96" # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////

# GLOBALS
# ///////////////////////////////////////////////////////////////
GLOBAL_STATE = False
GLOBAL_TITLE_BAR = True

class CustomMessageBox(QtWidgets.QMessageBox):
    def __init__(self, message_type, message):
        super().__init__()
        self.setFixedSize(300, 150)
        if message_type == "Error":
            self.setIcon(QtWidgets.QMessageBox.Critical)
            self.setWindowTitle("Error")
            self.setText("An error occurred")
        if message_type == "Warning":
            self.setIcon(QtWidgets.QMessageBox.Warning)
            self.setWindowTitle("Warning")
            self.setText("There may be a problem")
        if message_type == "Success":
            self.setIcon(QtWidgets.QMessageBox.Information)
            self.setWindowTitle("Success!")
            self.setText("The operation completed successfully")
        if message_type == "Information":
            self.setIcon(QtWidgets.QMessageBox.Information)
            self.setWindowTitle("Information")
            self.setText("The operation completed successfully")  

        self.setInformativeText(message)

        # Set a custom style sheet for the popup
        try:
            style_sheet = self.load_style_sheet('./themes/py_quest_dark.qss')
        except FileNotFoundError as e:
            logging.error('Theme file for CustomMessageBox not found: ', str(e))
        else: 
            self.setStyleSheet(style_sheet)
        
        self.exec_()

    def load_style_sheet(self,filename):
        """Load a style sheet from a file."""
        with open(filename, 'r') as file:
            return file.read()

class MainAppWindow(QtWidgets.QMainWindow):

    GRID_REGION_LIST = {'CAISO San Diego Gas & Electric DLAP' : 'SGIP_CAISO_SDGE',
                        'CAISO Pacific Gas & Electric DLAP' : 'SGIP_CAISO_PGE',
                        'CAISO Southern California Edison DLAP': 'SGIP_CAISO_SCE',
                        'Los Angeles Department of Water & Power':'SGIP_LADWP',
                        'BANC Sacramento Municipal Utility District':'SGIP_BANC_SMUD',
                        'Balancing Authority of Northern California':'SGIP_BANC_P2',
                        'Imperial Irrigation District':'SGIP_IID',
                        'PacifiCorp West':'SGIP_PACW',
                        'NV Energy':'SGIP_NVENERGY',
                        'Turlock Irrigation District':'SGIP_TID',
                        'Western Area Lower Colorado' : 'SGIP_WALC'} 
    MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December']
 
    previous_page = None
    current_page = None

    def __init__(self, parent=None):
        super(MainAppWindow, self).__init__(parent)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "CEC Quest - LDES Impact Analysis Tool"
        description = "CEC Quest - Long Duration Energy Storage Impact Analysis Tool."
        # APPLY TEXTS
        self.setWindowTitle(title)
        self.ui.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        self.ui.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////
        self.ui.dynamicPowerLimitsTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # Fill in Defauilt inputs
        # ///////////////////////////////////////////////////////////////
        self.input_field_parameters_file_path  = 'modules/__static__/input_field_parameters.json'
        self.input_field_parameters_data = self.read_json_file(self.input_field_parameters_file_path)
        for entry in self.input_field_parameters_data:
            method = getattr(self.ui, entry.get('object name'), None)
            try:
                method.setText(str(entry.get('default')))
                method.textChanged.connect(self.validator)
            except Exception as e:
                logging.error("Initilization Error when setting input_field_parameters_data to default text. Either the Object {object_name} has no setText method, the 'default' entry in the modules/__static__/input_field_parameters.json produced an error, or the method could not be connected to the self.validator() function. The error was : {error}".format(object_name=entry.get('object name'),error=e))

        # Enforce only valid inputs 
        # ///////////////////////////////////////////////////////////////
        latitude_validator = QtGui.QDoubleValidator(-90.0, 90.0, 2)  # Min, Max, Decimals
        latitude_validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.ui.latitudeInput.setValidator(latitude_validator)

        longitude_validator = QtGui.QDoubleValidator(-180.0, 180.0, 2)  # Min, Max, Decimals
        longitude_validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.ui.longitudeInput.setValidator(longitude_validator)

        year_validator = QtGui.QDoubleValidator(0, 2099, 0)  # Min, Max, Decimals
        year_validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.ui.yearEndInput.setValidator(year_validator)
        self.ui.yearStartInput.setValidator(year_validator)

        # LOAD utility rate data if it has already been downloaded 
        utility_rate_file_path = 'data/rates/usurdb.csv.gz'
        if os.path.exists(utility_rate_file_path):
            self.utility_rate_data = pd.read_csv(utility_rate_file_path, compression='gzip',low_memory=False)  # Load the CSV file into a DataFrame
        # FIGURE PLOTTING
        # ///////////////////////////////////////////////////////////////
        # Set a dark theme
        plt.style.use('seaborn-v0_8-darkgrid')

        # Create a matplotlib figure and axis
        fig_width = 4
        fig_hight = 3
        self.figure, self.ax = plt.subplots(figsize = (fig_width,fig_hight))
        self.results_figure, self.results_ax = plt.subplots(figsize = (fig_width,4))
        self.cost_results_bar_chart, self.cost_results_ax = plt.subplots(figsize = (fig_width,fig_hight))
        self.ghg_results_bar_chart, self.ghg_results_ax = plt.subplots(figsize = (fig_width,fig_hight))
        self.yearly_cost_results_bar_chart, self.yearly_cost_results_ax = plt.subplots(figsize = (fig_width,fig_hight))
        self.yearly_ghg_results_bar_chart, self.yearly_ghg_results_ax = plt.subplots(figsize = (fig_width,fig_hight))


        # Create a canvas to display the figure
        self.canvas = FigureCanvas(self.figure)
        self.results_canvas = FigureCanvas(self.results_figure)
        self.cost_results_canvas = FigureCanvas(self.cost_results_bar_chart)
        self.ghg_results_canvas = FigureCanvas(self.ghg_results_bar_chart)
        self.yearly_cost_results_canvas = FigureCanvas(self.yearly_cost_results_bar_chart)
        self.yearly_ghg_results_canvas = FigureCanvas(self.yearly_ghg_results_bar_chart)

        # Create a navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.results_toolbar = NavigationToolbar(self.results_canvas, self)
        self.cost_results_toolbar = NavigationToolbar(self.cost_results_canvas, self)
        self.ghg_results_toolbar = NavigationToolbar(self.ghg_results_canvas, self)
        self.yearly_cost_results_toolbar = NavigationToolbar(self.yearly_cost_results_canvas, self)
        self.yearly_ghg_results_toolbar = NavigationToolbar(self.yearly_ghg_results_canvas, self)

        # Add the toolbar and canvas to the layout
        self.ui.figureQVBoxLayout.addWidget(self.toolbar)
        self.ui.figureQVBoxLayout.addWidget(self.canvas)

        self.ui.resultsQVBoxLayout.addWidget(self.results_toolbar)
        self.ui.resultsQVBoxLayout.addWidget(self.results_canvas)
        
        self.ui.resultsCostBarChartLayout.addWidget(self.cost_results_toolbar)
        self.ui.resultsCostBarChartLayout.addWidget(self.cost_results_canvas)
        
        self.ui.resultsGHGBarChartLayout.addWidget(self.ghg_results_toolbar)
        self.ui.resultsGHGBarChartLayout.addWidget(self.ghg_results_canvas)

        self.ui.resultsYearlyCostBarChartLayout.addWidget(self.yearly_cost_results_toolbar)
        self.ui.resultsYearlyCostBarChartLayout.addWidget(self.yearly_cost_results_canvas)

        self.ui.resultsYearlyGHGBarChartLayout.addWidget(self.yearly_ghg_results_toolbar)
        self.ui.resultsYearlyGHGBarChartLayout.addWidget(self.yearly_ghg_results_canvas)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////
        
        # RIGHT MENUS
        self.ui.openAnalysisTemplateButton.clicked.connect(self.open_analysis_template)
        self.ui.saveAnalysisTemplateButton.clicked.connect(self.save_analysis_template)
        self.ui.contactUsButton.clicked.connect(self.contact_us)

        # LEFT MENUS
        self.ui.btn_home.clicked.connect(self.menuButtonClick)
        self.ui.btn_ess_model.clicked.connect(self.menuButtonClick)
        self.ui.btn_MOER.clicked.connect(self.menuButtonClick)
        self.ui.btn_btm_analysis.clicked.connect(self.menuButtonClick)
        self.ui.btn_energy_market_analysis.clicked.connect(self.menuButtonClick)
        self.ui.btn_results.clicked.connect(self.menuButtonClick)
        self.ui.figureViewPageBackButton.clicked.connect(self.menuButtonClick)

        # README BUTTON
        self.ui.btn_readme.clicked.connect(self.otherButtonClick)
        
        # ENERGY STORAGE MODEL BUTTONS
        self.system_data = {}  # Dictionary to store system data indexed by system number
        self.ui.openESSModelButton.clicked.connect(self.otherButtonClick)
        self.ui.numberOfSystemsComboBox.currentIndexChanged.connect(self.populate_select_system_combo_box)
        self.ui.selectSystemComboBox.currentIndexChanged.connect(self.update_system_data_inputs)
        self.ui.saveSystemParameters.clicked.connect(self.otherButtonClick)
        self.ui.saveESSModelFile.clicked.connect(self.otherButtonClick)
        self.ui.addDynamicPowerLimitButton.clicked.connect(self.add_row_to_dynamic_power_limits)
        self.ui.removeDynamicPowerLimitButton.clicked.connect(self.remove_row_from_dynamic_power_limits)
        self.ui.maxSOCLimitSlider.valueChanged.connect(self.update_max_soc_input)
        self.ui.minSOCLimitSlider.valueChanged.connect(self.update_min_soc_input)
        self.ui.plotSystemConstraintsButton.clicked.connect(self.otherButtonClick)

        self.ui.maxSOCLimitInput.editingFinished.connect(self.update_max_soc_input)
        self.ui.minSOCLimitInput.editingFinished.connect(self.update_min_soc_input)
        self.ui.addAvailabilityRestrictionButton.clicked.connect(self.add_row_to_availability_restrictions)
        self.ui.removeAvailabilityRestrictionButton.clicked.connect(self.remove_row_from_availability_restrictions)

        self.ui.dynamicPowerLimitsTable.setColumnCount(3)
        self.ui.dynamicPowerLimitsTable.setHorizontalHeaderLabels(['Region', 'Slope', 'Intercept'])
        self.ui.availabilityRestrictionsTable.setColumnCount(3)
        self.ui.availabilityRestrictionsTable.setHorizontalHeaderLabels(['Type', 'Period (days)', 'Duration (hours)'])

        if self.ui.openESSModelFileInput.text() != '':
            success = self.load_json_ess_model_data(self.ui.openESSModelFileInput.text())
            if success:
                print('len(self.system_data) : ' +str(len(self.system_data)))
                self.ui.numberOfSystemsComboBox.setCurrentIndex(len(self.system_data)-1)
                self.update_system_data_inputs()

        # MARGIONAL OPERATING EMISIONS RATE DOWNLOAD PAGE BUTTONS
        self.ui.downloadMOERDataButton.clicked.connect(self.otherButtonClick)
        self.ui.openMOERDataFile.clicked.connect(self.otherButtonClick)
        self.ui.viewMOERResourceFile.clicked.connect(self.otherButtonClick)
        self.ui.selectMOERFilesButton.clicked.connect(self.otherButtonClick)
        self.ui.MOERFilesSelectedTable.setColumnCount(1)
        self.ui.MOERFilesSelectedTable.setHorizontalHeaderLabels(['Selected Files'])
        self.ui.labelNotEnoughMOERData.hide()
        self.ui.labelEnoughMOERData.hide() 
        self.populate_date_combos()

        # BEHIND THE METER ANALYSIS BUTTONS
        self.btm_analyis_ready = False
        self.ui.requestAPIKeyButton.clicked.connect(self.otherButtonClick)
        self.ui.downloadSolarDataButton.clicked.connect(self.otherButtonClick)
        self.ui.openSolarResourceFile.clicked.connect(self.otherButtonClick)
        self.ui.viewSolarResourceFile.clicked.connect(self.otherButtonClick)
        self.ui.downloadRateDataButton.clicked.connect(self.download_and_extract_utility_rate_data)
        self.ui.rateSearchInput.setPlaceholderText('Enter utility to search...')
        self.ui.rateSearchButton.clicked.connect(self.search_utilities)
        self.ui.rateSearchResultsTable.setColumnCount(5)
        self.ui.rateSearchResultsTable.setHorizontalHeaderLabels(['Label', 'Utility', 'Name', 'Start Date', 'Sector'])
        self.ui.rateSearchResultsTable.itemClicked.connect(self.on_rate_item_clicked) 
        self.ui.rateInformationTable.setColumnCount(2)
        self.ui.rateInformationTable.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.ui.viewRateSchedule.clicked.connect(self.otherButtonClick)
        self.ui.saveLoadFilesButton.clicked.connect(self.otherButtonClick)
        self.ui.openLoadFileButton.clicked.connect(self.otherButtonClick)
        self.ui.viewLoadFileButton.clicked.connect(self.otherButtonClick)
        self.ui.splitLoadFileByMonthButton.clicked.connect(self.otherButtonClick)

        self.selectedUtilityRateLabel = self.ui.selectedUtilityRateInput.text()
        if not self.selectedUtilityRateLabel:
            self.selectedUtilityRateLabel = None
        
        self.saved_electrical_load_files_path  = self.ui.saveLoadFileListInput.text()
        if not self.saved_electrical_load_files_path:
            self.saved_electrical_load_files_path = None
        else:
            self.saved_electrical_load_files = self.read_json_file(self.saved_electrical_load_files_path)
            self.ui.loadFilesInputTable.setRowCount(12)
            self.ui.loadFilesInputTable.setColumnCount(1)
            row = 0
            for month in self.saved_electrical_load_files:
                self.ui.loadFilesInputTable.setItem(row, 0, QtWidgets.QTableWidgetItem(self.saved_electrical_load_files[month]['File']))
                row = row + 1

        # RUN BEHIND THE METER ANALYSIS BUTTONS
        self.ui.BTMAnalysisProgressBar.hide()
        self.ui.updateBTMAnalysisInptsButton.clicked.connect(self.otherButtonClick)
        self.ui.runBTMAnalysisButton.clicked.connect(self.otherButtonClick)

        # RESULTS PAGE
        self.ui.stopAnalysisProcessButton.clicked.connect(self.stop_analysis)
        self.ui.stopAnalysisProcessButton.setEnabled(False)
        self.ui.openResultsFile.clicked.connect(self.otherButtonClick)
        self.ui.plotResultsSignalButton.clicked.connect(self.otherButtonClick)
        self.ui.lifetimeAnalysisPageButton.clicked.connect(self.otherButtonClick)
        self.ui.runLifetimeAnalysisButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsBackButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsCostTableButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsGHGTableButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsCostBatChartButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsGHGBarChartButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsYearlyCostBarButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsYearlyGHGBarButton.clicked.connect(self.otherButtonClick)
        self.ui.openResultsFileListButton.clicked.connect(self.otherButtonClick)
        self.ui.yearlyCapacityResultsButton.clicked.connect(self.otherButtonClick)
        self.ui.resultsSummaryTableButton.clicked.connect(self.otherButtonClick)
        self.ui.genLifetimeAnalysisReportButton.clicked.connect(self.otherButtonClick)
        if self.ui.openResultsFileInput.text() != '':
            self.populate_results_plot_combos()
    
        # EXTRA LEFT BOX
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)
        self.ui.toggleLeftBox.clicked.connect(openCloseLeftBox)
        self.ui.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        # EXTRA RIGHT BOX
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)
        self.ui.templatesButton.clicked.connect(openCloseRightBox)
        self.ui.settingsTopBtn.clicked.connect(self.menuButtonClick)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # Multithreading
        # ///////////////////////////////////////////////////////////////
        self.threadpool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        self.ui.stackedWidget.setCurrentWidget(self.ui.home)
        self.previous_page = self.ui.home
        self.current_page = self.ui.home
        self.ui.btn_home.setStyleSheet(UIFunctions.selectMenu(self.ui.btn_home.styleSheet()))

        self.proxy_settings = {}
        self.proxy_settings['http'] =  self.ui.httpProxyInput.text()
        self.proxy_settings['https'] = self.ui.httpsProxyInput.text()

        self.solver = self.ui.solverInput.text()

    # BUTTONS CLICK FUNCTIONS
    # ///////////////////////////////////////////////////////////////
        
    def menuButtonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            self.ui.stackedWidget.setCurrentWidget(self.ui.home)
            self.previous_page = self.current_page
            self.current_page = self.ui.home
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW ESS MODEL PAGE
        if btnName == "btn_ess_model":
            self.ui.stackedWidget.setCurrentWidget(self.ui.ess_model)
            self.previous_page = self.current_page
            self.current_page = self.ui.ess_model
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
        
        # SHOW MARGINAL EMISSIONS PAGE
        if btnName == "btn_MOER":
            self.ui.stackedWidget.setCurrentWidget(self.ui.marginal_emissions) 
            self.previous_page = self.current_page
            self.current_page = self.ui.marginal_emissions
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 

        # SHOW Behind the meter analysis page
        if btnName == "btn_btm_analysis":
            self.ui.stackedWidget.setCurrentWidget(self.ui.btm_analysis) 
            self.previous_page = self.current_page
            self.current_page = self.ui.btm_analysis
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 

        # SHOW energy market analysis page
        if btnName == "btn_energy_market_analysis":
            self.ui.stackedWidget.setCurrentWidget(self.ui.energy_market_analysis) 
            self.previous_page = self.current_page
            self.current_page = self.ui.energy_market_analysis
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 

        # SHOW RESULTS PAGE
        if btnName == "btn_results":
            self.ui.stackedWidget.setCurrentWidget(self.ui.results) 
            self.previous_page = self.current_page
            self.current_page = self.ui.results
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 

        if btnName == "figureViewPageBackButton":
            self.current_page = self.previous_page 
            self.ui.stackedWidget.setCurrentWidget(self.previous_page) 

        if btnName == "settingsTopBtn":
            self.ui.stackedWidget.setCurrentWidget(self.ui.settings_page)
            self.previous_page = self.current_page
            self.current_page = self.ui.settings_page



        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')
        #print('Previous_page' + str(self.previous_page))
        #print('Current_page' + str(self.current_page))

    def save_settings(self):  
        self.proxy_settings = {}
        self.proxy_settings['http'] =  self.ui.httpProxyInput.text()
        self.proxy_settings['https'] = self.ui.httpsProxyInput.text()

        self.solver = self.ui.solverInput.text()

    def otherButtonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        if btnName == "saveSettingsButton":
            self.save_settings()

        # OPEN THE README FILE
        if btnName == "btn_readme":
            self.ui.stackedWidget.setCurrentWidget(self.ui.READMEWindow) 
            self.previous_page = self.current_page
            self.current_page = self.ui.READMEWindow
            self.open_readme()
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 

        if btnName == "downloadMOERDataButton": 
            self.download_and_extract_MOER_data()

        if btnName == "openMOERDataFile":
            success = self.ui.openMOERFileInput.setText(self.open_csv())
            print(success)

        if btnName == "selectMOERFilesButton":
            success = self.select_MOER_files()
            print(success)

        if btnName == "openESSModelButton":
            self.system_data = {}
            self.clear_ess_model_page()
            self.ui.openESSModelFileInput.setText(self.open_json())
            success = self.load_json_ess_model_data(self.ui.openESSModelFileInput.text())
            print(success)
            if success:
                self.ui.numberOfSystemsComboBox.setCurrentIndex(len(self.system_data)-1)
                self.update_system_data_inputs()

        if btnName == "addDynamicPowerLimitButton":
            self.add_row_to_dynamic_power_limits()

        if btnName == "saveSystemParameters":
            self.store_system_data()

        if btnName == "saveESSModelFile":
            self.save_system_data()

        if btnName == "plotSystemConstraintsButton":
            if self.plot_system_constraints_data():
                self.previous_page = self.current_page
                self.current_page = self.ui.figureViewPage
                self.ui.stackedWidget.setCurrentWidget(self.ui.figureViewPage) 

        if btnName == "viewMOERResourceFile":
            if self.plot_timeseries_data(self.ui.openMOERFileInput.text()):
                self.previous_page = self.current_page
                self.current_page = self.ui.figureViewPage
                self.ui.stackedWidget.setCurrentWidget(self.ui.figureViewPage) 

        if btnName == "viewSolarResourceFile":
            if self.plot_timeseries_data(self.ui.openSolarResourceFileInput.text()):
                self.previous_page = self.current_page
                self.current_page = self.ui.figureViewPage
                self.ui.stackedWidget.setCurrentWidget(self.ui.figureViewPage) 

        if btnName == "requestAPIKeyButton":
            url = "https://developer.nrel.gov/signup/"
            webbrowser.open(url)

        if btnName == "downloadSolarDataButton":
            self.download_solar_data()

        if btnName == "openSolarResourceFile":
            success = self.ui.openSolarResourceFileInput.setText(self.open_csv())
            print(success)

        if btnName == "viewRateSchedule":
            if self.plot_rate_schedule_data(self.ui.selectedUtilityRateInput.text()):
                self.previous_page = self.current_page
                self.current_page = self.ui.figureViewPage
                self.ui.stackedWidget.setCurrentWidget(self.ui.figureViewPage) 

        if btnName == "openLoadFileButton":
            success = self.ui.loadFileInput.setText(self.open_csv())
            print(success)
        
        if btnName == "saveLoadFilesButton":
            self.save_electrical_load_files(self.ui.saveLoadFileListInput.text())
            
        if btnName == "viewLoadFileButton":
            if self.plot_timeseries_data(self.ui.loadFileInput.text()):
                self.previous_page = self.current_page
                self.current_page = self.ui.figureViewPage
                self.ui.stackedWidget.setCurrentWidget(self.ui.figureViewPage) 

        if btnName == "splitLoadFileByMonthButton":
            self.split_load_file_by_month(self.ui.loadFileInput.text())

        if btnName == "updateBTMAnalysisInptsButton":
            self.update_btm_analysis_inputs()

        if btnName == "runBTMAnalysisButton":
            self.ui.stackedWidget.setCurrentWidget(self.ui.results) 
            self.ui.stackedWidget_3.setCurrentWidget(self.ui.resultsPage_2) 
            self.previous_page = self.current_page
            self.current_page = self.ui.figureViewPage
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            self.run_btm_analysis()
        
        if btnName == "openResultsFile":
            try:
                file_name = self.open_json()
                if file_name:
                    self.ui.openResultsFileInput.setText(file_name)
            except Exception as e:
                logging.error("There was an error when trying to open a results file list : {error}".format(error=e))

        if btnName == "plotResultsSignalButton":
            success = self.plot_results_signal_data(self.ui.openResultsFileInput.text())
            print(success)

        if btnName == "lifetimeAnalysisPageButton":
            self.ui.stackedWidget_3.setCurrentWidget(self.ui.resultsPage_1) 

        if btnName == "runLifetimeAnalysisButton":
            if self.ui.openResultsFileListInput.text() != '':
                self.run_lifetime_analysis()

        if btnName == "resultsBackButton":
            self.ui.stackedWidget_3.setCurrentWidget(self.ui.resultsPage_2) 
            
        if btnName == "resultsCostTableButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.resultsPage_CostTable) 
            
        if btnName == "resultsGHGTableButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.resultsPage_GHGTable) 
            
        if btnName == "resultsCostBatChartButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.resultsPage_CostBarChart) 
            
        if btnName == "resultsGHGBarChartButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.resultsPage_GHGBarChat) 

        if btnName == "yearlyCapacityResultsButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.resultsPage_Capacity) 

        if btnName == "resultsSummaryTableButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.resultsPage_Summary) 

        if btnName == "openResultsFileListButton":
            try:
                file_name = self.open_json()
                if file_name:
                    self.ui.openResultsFileListInput.setText(file_name)
            except Exception as e:
                logging.error("There was an error when trying to open a results file list : {error}".format(error=e))

        if btnName == "resultsYearlyCostBarButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.results_Page_YearlyCost) 

        if btnName == "resultsYearlyGHGBarButton":
            self.ui.stackedWidget_4.setCurrentWidget(self.ui.results_Page_YearlyGHG) 

        if btnName == "genLifetimeAnalysisReportButton":
            success = self.generate_analysis_report()
            print(success)

        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')
        #print('Previous_page' + str(self.previous_page))
        #print('Current_page' + str(self.current_page))

    # RIGHT MENUE BUTTON FUNCTIONS 
    # ///////////////////////////////////////////////////////////////     

    def open_analysis_template(self):
        check = True
        try:
            # Fill in Defauilt inputs
            # ///////////////////////////////////////////////////////////////
            self.input_field_parameters_file_path  = self.open_json()
            self.input_field_parameters_data = self.read_json_file(self.input_field_parameters_file_path)
            for entry in self.input_field_parameters_data:
                method = getattr(self.ui, entry.get('object name'), None)
                try:
                    method.setText(str(entry.get('default')))
                    method.textChanged.connect(self.validator)
                except Exception as e:
                    logging.error("Initilization Error when setting input_field_parameters_data to default text. Either the Object {object_name} has no setText method, the 'default' entry in the modules/__static__/input_field_parameters.json produced an error, or the method could not be connected to the self.validator() function. The error was : {error}".format(object_name=entry.get('object name'),error=e))

            if self.ui.openESSModelFileInput.text() != '':
                success = self.load_json_ess_model_data(self.ui.openESSModelFileInput.text())
                if success:
                    print('len(self.system_data) : ' +str(len(self.system_data)))
                    self.ui.numberOfSystemsComboBox.setCurrentIndex(len(self.system_data)-1)
                    self.update_system_data_inputs()
            
            self.populate_date_combos()

            self.saved_electrical_load_files_path  = self.ui.saveLoadFileListInput.text()
            if not self.saved_electrical_load_files_path:
                self.saved_electrical_load_files_path = None
            else:
                self.saved_electrical_load_files = self.read_json_file(self.saved_electrical_load_files_path)
                self.ui.loadFilesInputTable.setRowCount(12)
                self.ui.loadFilesInputTable.setColumnCount(1)
                row = 0
                for month in self.saved_electrical_load_files:
                    self.ui.loadFilesInputTable.setItem(row, 0, QtWidgets.QTableWidgetItem(self.saved_electrical_load_files[month]['File']))
                    row = row + 1

            self.selectedUtilityRateLabel = self.ui.selectedUtilityRateInput.text()
            if not self.selectedUtilityRateLabel:
                self.selectedUtilityRateLabel = None   
            CustomMessageBox('Success', 'Analysis template {file} has loaded successfully.'.format(file=self.input_field_parameters_file_path))
        
        except Exception as e:
            logging.error("An error occured in select_MOER_files() method of MainWindow : {error}".format(error=e))
            CustomMessageBox('Error', 'An error occured when trying to load analysis template {file}. Error output: {err}'.format(file=self.input_field_parameters_file_path,err=e))
            check = False
        return check
    
    def save_analysis_template(self):
        
        # Set the default file path and name
        path = "analysis_templates/"
        file_name = "input_field_parameters_example_viejas.json"

        # Open the file dialog
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save as",
            os.path.join(path, file_name),
            "JSON files (*.json);;All files (*)"
        )

        # Update Defauilt inputs
        self.input_field_parameters_file_path  = 'modules/__static__/input_field_parameters.json'
        self.input_field_parameters_data = self.read_json_file(self.input_field_parameters_file_path)
        idx = 0
        for entry in self.input_field_parameters_data:
            method = getattr(self.ui, entry.get('object name'), None)
            try:
                self.input_field_parameters_data[idx]['default'] = method.text()
            except Exception as e:
                logging.error("Error when updateing default text in save_analysis_template. The error was : {error}".format(object_name=entry.get('object name'),error=e))
            idx += 1
        with open(file_path, 'w') as json_file:
            json.dump(self.input_field_parameters_data, json_file) 


        print(f'Button save_analysis_template pressed!')

    def contact_us(self):
        # Define the email address
        email_address = "dmrose@sandia.gov"
        
        # Create the mailto URL
        mailto_url = f"mailto:{email_address}"
        
        # Open the default email client
        webbrowser.open(mailto_url)


        print(f'Button contact_us pressed!')


    # MOER SIGNAL DOWNLOAD PAGE FUNCTIONS 
    # ///////////////////////////////////////////////////////////////     
    def populate_date_combos(self):
        current_year = datetime.now().year
        for year in range(2017, current_year + 1):
            self.ui.MOERStartYearComboBox.addItem(str(year))
        for month in range(1, 13):
            self.ui.MOERStartMonthComboBox.addItem(f"{month:02d}")
        self.ui.MOERStartYearComboBox.setCurrentText('2024')

    def load_MOER_files(self):
        files = []
        MOER_data_path = 'data/MOER/' + self.GRID_REGION_LIST[self.ui.gridRegionComboBox.currentText()]
        for file in os.listdir(MOER_data_path):
            if file.startswith('SGIP_CAISO_') and file.endswith('_ALL_MOER_VERSIONS.csv'):
                files.append(file)
        return files

    def select_MOER_files(self):
        check = True
        try:
            self.MOER_Signal = {}
            self.MOER_Signal['Grid Region'] = self.GRID_REGION_LIST[self.ui.gridRegionComboBox.currentText()]
            

            selected_year = int(self.ui.MOERStartYearComboBox.currentText())
            selected_month = int(self.ui.MOERStartMonthComboBox.currentText())
            selected_date = datetime(selected_year, selected_month, 1)

            one_year_later = selected_date + timedelta(days=365)

            self.MOER_Signal['Start Date'] = str(selected_date)
            self.MOER_Signal['End Date'] = str(one_year_later)

            files = self.load_MOER_files()
            filtered_files = []
            
            for file in files:
                file_date_str = file.split('_')[3]  # Extracting the date part
                file_date = datetime.strptime(file_date_str, '%Y-%m')
                if selected_date <= file_date < one_year_later:
                    filtered_files.append(file)
            
            if not filtered_files:
                self.ui.labelNotEnoughMOERData.hide()
                self.ui.labelEnoughMOERData.hide() 
                CustomMessageBox('Warning', 'No files found within one year of the selected date.')
            else:
                self.populate_MOER_table(filtered_files)
                self.MOER_Signal['Selected Files'] = filtered_files
                if len(filtered_files)==12:
                    self.ui.labelNotEnoughMOERData.hide()
                    self.ui.labelEnoughMOERData.show() 
                    self.MOER_Signal['Data Check'] = "Enough Data"
                else:
                    self.ui.labelNotEnoughMOERData.show()
                    self.ui.labelEnoughMOERData.hide() 
                    self.MOER_Signal['Data Check'] = "Not Enough Data"

            

        except Exception as e:
            logging.error("An error occured in select_MOER_files() method of MainWindow : {error}".format(error=e))
            check = False
        return check
    
    def populate_MOER_table(self, files):
        self.ui.MOERFilesSelectedTable.setRowCount(len(files))
        for row, file in enumerate(files):
            self.ui.MOERFilesSelectedTable.setItem(row, 0, QtWidgets.QTableWidgetItem(file))

    def download_and_extract_MOER_data(self):
        # look at the combo box selection for grid region and construct the download link 
        grid_region = self.GRID_REGION_LIST[self.ui.gridRegionComboBox.currentText()]
        url = 'https://data.sgipsignal.com/historical/' + grid_region + '.zip'
        zip_file_path = grid_region + '.zip'
        destination_folder = 'data/MOER/' + grid_region

        # Check if the destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Download the ZIP file
        try:
            response = requests.get(url,proxies=self.proxy_settings,verify=True)
            response.raise_for_status()  # Raise an error for bad responses

            # Save the ZIP file
            with open(zip_file_path, 'wb') as zip_file:
                zip_file.write(response.content)

            # Extract the ZIP file
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(destination_folder)

            CustomMessageBox('Success', 'MOER data files downloaded and extracted successfully.')

        except requests.exceptions.RequestException as e:
            logging.error(f'Failed to download the MOER data file: {e}')
            CustomMessageBox('Error', f'Failed to download the MOER data file: {e}')
        except zipfile.BadZipFile:
            logging.error('The downloaded MOER data file is not a valid ZIP file.')
            CustomMessageBox('Error', 'The downloaded MOER data file is not a valid ZIP file.')
        except Exception as e:
            logging.error(f'An error occurred: {e}')
            CustomMessageBox('Error', f'An error occurred: {e}')
        finally:
            # Clean up the downloaded ZIP file
            if os.path.exists(zip_file_path):
                os.remove(zip_file_path)

    # ESS MODEL CONFIGURATION PAGE FUNCTIONS 
    # ///////////////////////////////////////////////////////////////
                
    def clear_ess_model_page(self):
        self.ui.selectSystemComboBox.setCurrentIndex(0) 
        self.ui.systemName.setText('name')
        self.ui.energyCapacityInput.setText('0')
        self.ui.chargePowerLimitInput.setText('0')
        self.ui.diachargePowerLimitInput.setText('0')
        self.ui.roundTripEfficiencyInput.setText('100')
        self.ui.selfDischargeRateInput.setText('0')
        self.ui.maxSOCLimitInput.setText('100')
        self.ui.minSOCLimitInput.setText('0')
        self.ui.maxSOCLimitSlider.setValue(100)
        self.ui.minSOCLimitSlider.setValue(0)
        self.ui.degradationInFirstYearInput.setText('0')
        self.ui.degradationPerYearAferFirstInput.setText('0')
        self.ui.dynamicPowerLimitsTable.setRowCount(0)
        self.ui.availabilityRestrictionsTable.setRowCount(0)
   
    def load_json_ess_model_data(self,filename):
        success = None
        self.system_data = {}
        try:
            with open(filename,'r') as jsonfile:
                self.system_data = json.load(jsonfile)
            success = True
        except Exception as e:
            logging.error('Error in loading ESS model data from : {file} with error {error}'.format(file=filename,error=e))
            success = False
        return success 

    def populate_select_system_combo_box(self):
        """Populate selectSystemComboBox based on the selection in combobox1."""
        self.ui.selectSystemComboBox.clear()  # Clear previous items
        n = int(self.ui.numberOfSystemsComboBox.currentText())  # Get the selected number
        systems = [f'System {i}' for i in range(1, n + 1)]  # Create system names
        self.ui.selectSystemComboBox.addItems(systems)  # Add systems to combobox2

        # Clear the system name input when the selection changes
        self.init_system_data()

    def init_system_data(self):
        systems = []
        for i in range(self.ui.selectSystemComboBox.count()):  # Loop through all items
            systems.append(self.ui.selectSystemComboBox.itemText(i))  # Get the text of each item
        new_system_data = {}
        for system in systems:
            #print(system)
            #print(self.system_data)
            if system in self.system_data:
                system_number = system
                print('saving: ' + str(system_number))
                new_system_data[system_number] = {}
                new_system_data[system_number]['System Name'] = self.system_data[system_number]['System Name'] 
                new_system_data[system_number]['Energy Capacity'] =  self.system_data[system_number]['Energy Capacity'] 
                new_system_data[system_number]['Charge Power Limit'] =  self.system_data[system_number]['Charge Power Limit'] 
                new_system_data[system_number]['Discharge Power Limit'] = self.system_data[system_number]['Discharge Power Limit']  
                new_system_data[system_number]['Round-Trip-Efficiency'] = self.system_data[system_number]['Round-Trip-Efficiency']  
                new_system_data[system_number]['Self-Discharge Rate'] = self.system_data[system_number]['Self-Discharge Rate']   
                new_system_data[system_number]['Max SOC'] = self.system_data[system_number]['Max SOC']   
                new_system_data[system_number]['Min SOC'] = self.system_data[system_number]['Min SOC'] 

                new_system_data[system_number]['Degradation Rate in Year 1'] = self.system_data[system_number]['Degradation Rate in Year 1']   
                new_system_data[system_number]['Degradation Rate Year > 1'] = self.system_data[system_number]['Degradation Rate Year > 1'] 

                new_system_data[system_number]['Dynamic Power Limits'] = {}
                for i in range(len(self.system_data[system_number]['Dynamic Power Limits'])):
                    LimitIdx = 'Limit '+str(i)
                    new_system_data[system_number]['Dynamic Power Limits'][LimitIdx] = {}
                    new_system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Region'] = self.system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Region']
                    new_system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Slope'] = self.system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Slope']
                    new_system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Intercept'] = self.system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Intercept']
                
                new_system_data[system_number]['Availability Restrictions'] = {}
                for i in range(len(self.system_data[system_number]['Availability Restrictions'])):
                    RestrictionIdx = 'Restriction '+str(i)
                    new_system_data[system_number]['Availability Restrictions'][RestrictionIdx] = {}
                    new_system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Type'] = self.system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Type']
                    new_system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Period'] = self.system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Period']
                    new_system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Duration'] = self.system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Duration']
            else:
                system_number = system
                new_system_data[system_number] = {}
                new_system_data[system_number]['System Name'] = 'ESS ' + str(system_number)
                new_system_data[system_number]['Energy Capacity'] = 0.0
                new_system_data[system_number]['Charge Power Limit'] = 0.0
                new_system_data[system_number]['Discharge Power Limit'] = 0.0
                new_system_data[system_number]['Round-Trip-Efficiency'] = 100.0
                new_system_data[system_number]['Self-Discharge Rate'] = 0.0
                new_system_data[system_number]['Max SOC'] = 100.0
                new_system_data[system_number]['Min SOC'] = 0.0
                new_system_data[system_number]['Degradation Rate in Year 1'] = 0.0
                new_system_data[system_number]['Degradation Rate Year > 1'] = 0.0
                new_system_data[system_number]['Dynamic Power Limits'] = {}
                new_system_data[system_number]['Availability Restrictions'] = {}


        self.system_data = new_system_data
        
    def store_system_data(self):
        """Store the system data in a dictionary."""
        selected_system = self.ui.selectSystemComboBox.currentText()
        if selected_system:
            system_number = selected_system
            self.system_data[system_number] = {}
            self.system_data[system_number]['System Name'] = self.ui.systemName.text() 

            if self.is_float(self.ui.energyCapacityInput.text()):
                self.system_data[system_number]['Energy Capacity'] = float(self.ui.energyCapacityInput.text()) 

            if self.is_float(self.ui.chargePowerLimitInput.text()): 
                self.system_data[system_number]['Charge Power Limit'] = float(self.ui.chargePowerLimitInput.text())  

            if self.is_float(self.ui.diachargePowerLimitInput.text()): 
                self.system_data[system_number]['Discharge Power Limit'] = float(self.ui.diachargePowerLimitInput.text()) 

            if self.is_float(self.ui.roundTripEfficiencyInput.text()):
                self.system_data[system_number]['Round-Trip-Efficiency'] = float(self.ui.roundTripEfficiencyInput.text()) 

            if self.is_float(self.ui.selfDischargeRateInput.text()): 
                self.system_data[system_number]['Self-Discharge Rate'] = float(self.ui.selfDischargeRateInput.text())  
            
            if self.is_float(self.ui.maxSOCLimitInput.text()): 
                self.system_data[system_number]['Max SOC'] = float(self.ui.maxSOCLimitInput.text())  
            
            if self.is_float(self.ui.minSOCLimitInput.text()): 
                self.system_data[system_number]['Min SOC'] = float(self.ui.minSOCLimitInput.text())  

            if self.is_float(self.ui.degradationInFirstYearInput.text()): 
                self.system_data[system_number]['Degradation Rate in Year 1'] = float(self.ui.degradationInFirstYearInput.text())  

            if self.is_float(self.ui.degradationPerYearAferFirstInput.text()): 
                self.system_data[system_number]['Degradation Rate Year > 1'] = float(self.ui.degradationPerYearAferFirstInput.text())  

            if self.ui.dynamicPowerLimitsTable.rowCount() != 0:
                self.system_data[system_number]['Dynamic Power Limits'] = {}
                for row in range(self.ui.dynamicPowerLimitsTable.rowCount()):
                    LimitIdx = 'Limit '+str(row)
                    row_data = {
                        "Region": self.ui.dynamicPowerLimitsTable.cellWidget(row, 0).currentText(),  # Get the text from the combo box
                        "Slope": float(self.ui.dynamicPowerLimitsTable.item(row, 1).text()),  # Get the text from the second column
                        "Intercept": float(self.ui.dynamicPowerLimitsTable.item(row, 2).text())   # Get the text from the third column
                    }
                    self.system_data[system_number]['Dynamic Power Limits'][LimitIdx] = row_data  # Use the row index as the key

            if self.ui.availabilityRestrictionsTable.rowCount() != 0:
                self.system_data[system_number]['Availability Restrictions'] = {}
                for row in range(self.ui.availabilityRestrictionsTable.rowCount()):
                    LimitIdx = 'Limit '+str(row)
                    row_data = {
                        "Type": self.ui.availabilityRestrictionsTable.cellWidget(row, 0).currentText(),  # Get the text from the combo box
                        "Period": float(self.ui.availabilityRestrictionsTable.item(row, 1).text()),  # Get the text from the second column
                        "Duration": float(self.ui.availabilityRestrictionsTable.item(row, 2).text())   # Get the text from the third column
                    }
                    self.system_data[system_number]['Availability Restrictions'][LimitIdx] = row_data  # Use the row index as the key

    def is_float(self,text):
        isFloat = True
        try: 
            number = float(text)
        except:   
            isFloat = False
        return isFloat

    def update_system_data_inputs(self):
        """Update the QLineEdit with the selected system's name."""
        selected_system = self.ui.selectSystemComboBox.currentText()
        if selected_system:
            # Set the QLineEdit text to the stored name if it exists
            system_number = selected_system
            self.ui.systemName.setText(self.system_data[system_number]['System Name'])
            self.ui.energyCapacityInput.setText(str(self.system_data[system_number]['Energy Capacity']))
            self.ui.chargePowerLimitInput.setText(str(self.system_data[system_number]['Charge Power Limit']))
            self.ui.diachargePowerLimitInput.setText(str(self.system_data[system_number]['Discharge Power Limit']))
            self.ui.roundTripEfficiencyInput.setText(str(self.system_data[system_number]['Round-Trip-Efficiency']))
            self.ui.selfDischargeRateInput.setText(str(self.system_data[system_number]['Self-Discharge Rate']))
            self.ui.maxSOCLimitInput.setText(str(self.system_data[system_number]['Max SOC']))
            self.ui.minSOCLimitInput.setText(str(self.system_data[system_number]['Min SOC']))
            self.ui.maxSOCLimitSlider.setValue(int(self.system_data[system_number]['Max SOC']))
            self.ui.minSOCLimitSlider.setValue(int(self.system_data[system_number]['Min SOC']))
            self.ui.degradationInFirstYearInput.setText(str(self.system_data[system_number]['Degradation Rate in Year 1']))
            self.ui.degradationPerYearAferFirstInput.setText(str(self.system_data[system_number]['Degradation Rate Year > 1']))
            self.ui.dynamicPowerLimitsTable.setRowCount(0)
            if len(self.system_data[system_number]['Dynamic Power Limits'])>0:
                for i in range(len(self.system_data[system_number]['Dynamic Power Limits'])):
                    LimitIdx = 'Limit '+str(i)
                    row_position = self.ui.dynamicPowerLimitsTable.rowCount()
                    self.ui.dynamicPowerLimitsTable.insertRow(row_position)
                    # Create a combo box for the first column
                    combo_box = QtWidgets.QComboBox()
                    combo_box.addItems(["Charge", "Discharge"])
                    currentIdx = 0
                    if self.system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Region'] == 'Discharge':
                        currentIdx = 1
                    combo_box.setCurrentIndex(currentIdx)
                    self.ui.dynamicPowerLimitsTable.setCellWidget(row_position, 0, combo_box)

                    # Create float input fields for the second and third columns
                    value1_item = QtWidgets.QTableWidgetItem(str(self.system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Slope']))
                    self.ui.dynamicPowerLimitsTable.setItem(row_position, 1, value1_item)

                    value2_item = QtWidgets.QTableWidgetItem(str(self.system_data[system_number]['Dynamic Power Limits'][LimitIdx]['Intercept']))
                    self.ui.dynamicPowerLimitsTable.setItem(row_position, 2, value2_item)
            self.ui.availabilityRestrictionsTable.setRowCount(0)
            if len(self.system_data[system_number]['Availability Restrictions'])>0:
                for i in range(len(self.system_data[system_number]['Availability Restrictions'])):
                    RestrictionIdx = 'Restriction '+str(i)
                    row_position = self.ui.availabilityRestrictionsTable.rowCount()
                    self.ui.availabilityRestrictionsTable.insertRow(row_position)
                    # Create a combo box for the first column
                    combo_box2 = QtWidgets.QComboBox()
                    combo_box2.addItems(["Conditioning Cycle", "Maintenance"])
                    currentIdx = 0
                    if self.system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Type'] == 'Maintenance':
                        currentIdx = 1
                    combo_box2.setCurrentIndex(currentIdx)
                    self.ui.availabilityRestrictionsTable.setCellWidget(row_position, 0, combo_box2)

                    # Create float input fields for the second and third columns
                    value1_item = QtWidgets.QTableWidgetItem(str(self.system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Period']))
                    self.ui.availabilityRestrictionsTable.setItem(row_position, 1, value1_item)

                    value2_item = QtWidgets.QTableWidgetItem(str(self.system_data[system_number]['Availability Restrictions'][RestrictionIdx]['Duration']))
                    self.ui.availabilityRestrictionsTable.setItem(row_position, 2, value2_item)

    def add_row_to_dynamic_power_limits(self):
        row_position = self.ui.dynamicPowerLimitsTable.rowCount()
        self.ui.dynamicPowerLimitsTable.insertRow(row_position)

        # Create a combo box for the first column
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(["Charge", "Discharge"])
        self.ui.dynamicPowerLimitsTable.setCellWidget(row_position, 0, combo_box)

        # Create float input fields for the second and third columns
        value1_item = QtWidgets.QTableWidgetItem("0.0")
        self.ui.dynamicPowerLimitsTable.setItem(row_position, 1, value1_item)

        value2_item = QtWidgets.QTableWidgetItem("0.0")
        self.ui.dynamicPowerLimitsTable.setItem(row_position, 2, value2_item)

    def remove_row_from_dynamic_power_limits(self):
        selected_row = self.ui.dynamicPowerLimitsTable.currentRow()
        if selected_row >= 0:
            self.ui.dynamicPowerLimitsTable.removeRow(selected_row)

    def save_system_data(self):
        #print(self.system_data)
        self.ess_model_file_path = 'data/ESS Models/'
        self.ui.essModelNameInput.text()
        file_path = self.ess_model_file_path + self.ui.essModelNameInput.text() + '.json'
        with open(file_path, 'w') as json_file:
            json.dump(self.system_data,json_file,indent=4)
        CustomMessageBox('Information',"ESS Model Saved as {model_name}".format(model_name=file_path))

    def open_json(self):
        # Open a file dialog to select the JSON file
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        return file_name

    def read_json_file(self,file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)  # Load the JSON data
                return data
        except Exception as e:
            logging.error("There was a in the read_json_file function of the MainWindow Class  : %s", str(e))
            return None
     
    def open_csv(self):
        # Open a file dialog to select the CSV file
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        return file_name

    def update_max_soc_input(self, value):
        """Update the maxSOCLimitInput with the value from the maxSOCLimitSlider."""
        try:  
            self.ui.maxSOCLimitInput.setText(str(value))
            if self.ui.minSOCLimitSlider.value() > int(value):
                self.ui.minSOCLimitSlider.setValue(int(value))
        except ValueError:
            pass  # Ignore invalid input

    def update_min_soc_input(self, value):
        """Update the minSOCLimitInput with the value from the minSOCLimitSlider."""
        self.ui.minSOCLimitInput.setText(str(value))
        if self.ui.maxSOCLimitSlider.value() < int(value):
            self.ui.maxSOCLimitSlider.setValue(int(value))

    def plot_system_constraints_data(self):

        if self.ui.selectSystemComboBox.currentText():
            check = True
        else:
            check = False
            CustomMessageBox('Warning', 'Please select a system to plot it\'s constraints.')
            return check

        try:
            selected_system = self.ui.selectSystemComboBox.currentText()
            if selected_system:
                AChaEOS = []
                bChaEOS = []
                ADisEOS = []
                bDisEOS = []
                system_number = selected_system

                if self.is_float(self.ui.energyCapacityInput.text()):
                    energyCapacity = float(self.ui.energyCapacityInput.text()) 

                if self.is_float(self.ui.chargePowerLimitInput.text()): 
                    chargePowerLimit = float(self.ui.chargePowerLimitInput.text())  
                    AChaEOS.append(0)
                    bChaEOS.append(chargePowerLimit)

                if self.is_float(self.ui.diachargePowerLimitInput.text()): 
                    dischargePowerLimit = -float(self.ui.diachargePowerLimitInput.text()) 
                    ADisEOS.append(0)
                    bDisEOS.append(dischargePowerLimit)

                if self.is_float(self.ui.maxSOCLimitInput.text()): 
                    maxSOC = float(self.ui.maxSOCLimitInput.text())  
                
                if self.is_float(self.ui.minSOCLimitInput.text()): 
                    minSOC = float(self.ui.minSOCLimitInput.text())  

                if self.ui.dynamicPowerLimitsTable.rowCount() != 0:
                    for row in range(self.ui.dynamicPowerLimitsTable.rowCount()):
                        LimitIdx = 'Limit '+str(row)
                        row_data = {
                            "Region": self.ui.dynamicPowerLimitsTable.cellWidget(row, 0).currentText(),  # Get the text from the combo box
                            "Slope": float(self.ui.dynamicPowerLimitsTable.item(row, 1).text()),  # Get the text from the second column
                            "Intercept": float(self.ui.dynamicPowerLimitsTable.item(row, 2).text())   # Get the text from the third column
                        }
                        if row_data['Region'] == "Charge":
                            AChaEOS.append(row_data['Slope'])
                            bChaEOS.append(row_data['Intercept'])
                        elif row_data['Region'] == "Discharge":
                            ADisEOS.append(row_data['Slope'])
                            bDisEOS.append(row_data['Intercept'])

            print("AChaEOS: " + str(AChaEOS))
            print("bChaEOS: " + str(bChaEOS))
            print("ADisEOS: " + str(ADisEOS))
            print("bDisEOS: " + str(bDisEOS))

            N = 101
            x = range(N)
            soc_x = np.linspace(minSOC,maxSOC,N)

            CHA_LIM = [min([AChaEOS[i]*j + bChaEOS[i] for i in range(len(bChaEOS))]) for j in x]
            DIS_LIM = [max([ADisEOS[i]*j + bDisEOS[i] for i in range(len(bDisEOS))]) for j in x]

            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            '''plt.plot(soc1, PowerMaxCha,'*', color='green')
            plt.plot(soc2, PowerMaxDis,'*', color='red')'''


            self.ax.fill_between(soc_x,CHA_LIM,0, label='Charge Region', color='darkblue', linewidth=4)
            self.ax.fill_between(soc_x,DIS_LIM,0, label='Disharge Region', color='darkred', linewidth=4)

            '''n11 = len(ansCha)
            plt.plot([ansCha[i][0] for i in range(n11)],[ansCha[i][1] for i in range(n11)],'*', color='lightgreen', markersize=15)
            n22 = len(ansDis)
            plt.plot([ansDis[i][0] for i in range(n22)],[ansDis[i][1] for i in range(n22)],'*', label='Corner Points', color='lightgreen', markersize=15)'''

            #plt.plot(soc, p_dis,'-', color='blue')
            self.ax.set_xlabel('SOC (%)')
            self.ax.set_ylabel('Power (MW)')
            self.ax.axis([0,100, 1.1*dischargePowerLimit,1.1*chargePowerLimit])
            self.ax.grid(True)

            self.canvas.draw()

        except Exception as e:
            logging.error("There was an error in the plot_system_constraints_data function of the MainWindow Class  : %s", str(e))
            CustomMessageBox('Warning', "There was an error when trying to plot the data : {err}>".format(err=e))
            check = False
        
        return check
    
    def add_row_to_availability_restrictions(self):
        row_position = self.ui.availabilityRestrictionsTable.rowCount()
        self.ui.availabilityRestrictionsTable.insertRow(row_position)

        # Create a combo box for the first column
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(["Conditioning Cycle", "Maintenance"])
        self.ui.availabilityRestrictionsTable.setCellWidget(row_position, 0, combo_box)

        # Create float input fields for the second and third columns
        value1_item = QtWidgets.QTableWidgetItem("0.0")
        self.ui.availabilityRestrictionsTable.setItem(row_position, 1, value1_item)

        value2_item = QtWidgets.QTableWidgetItem("0.0")
        self.ui.availabilityRestrictionsTable.setItem(row_position, 2, value2_item)

    def remove_row_from_availability_restrictions(self):
        selected_row = self.ui.availabilityRestrictionsTable.currentRow()
        if selected_row >= 0:
            self.ui.availabilityRestrictionsTable.removeRow(selected_row)


    # BTM ANALYSIS FUNCTIONS 
    # ///////////////////////////////////////////////////////////////

    # ---- SOLAR SIGNAL DOWNLOAD FUNCTIONS ----
    
    def download_solar_data(self):
        site_name = self.ui.siteNameInput.text()
        lat = float(self.ui.latitudeInput.text())
        lon = float(self.ui.longitudeInput.text())
        if self.ui.trackingCheckBox.isChecked():
            tracking = 1
        else:
            tracking = 0
        ac = float(self.ui.acPowerInput.text())
        dc = float(self.ui.dcPowerInput.text())
        directory = "."
        #print('site_name : ' + str(site_name) + '   lat : ' + str(lat) + '   lon : ' + str(lon) + '   tracking : ' + str(tracking) + '   ac : ' + str(ac)  + '   dc : ' + str(dc) + '   directory : ' + str(directory))
        downloadSolar = Solar(site_name,lat,lon,tracking,ac,dc,directory)
        api_key = self.ui.APIKeyInput.text()
        your_name = self.ui.nameInput.text()
        your_affiliation = self.ui.affiliationInput.text()
        your_email = self.ui.emailInput.text()
        year_start = int(self.ui.yearStartInput.text())
        year_end = int(self.ui.yearEndInput.text())
        #print('api_key : ' + str(api_key) + '   your_name : ' + str(your_name) + '   your_affiliation : ' + str(your_affiliation) + '   your_email : ' + str(your_email) + '   year_start : ' + str(year_start)  + '   year_end : ' + str(year_end))
        
        # Check to make sure that yearEndInput is greater than or equal to yearStartInput
        if year_end < year_start:
            logging.error("Value error on year range inputs : %s", 'year_end < year_start')
            CustomMessageBox("Error", "Value error on year range inputs : year_end < year_start")
        else:
            try: 
                downloadSolar.SolarGen(api_key, your_name, your_affiliation, your_email, year_start, year_end)
            except Exception as e:
                # Log the error
                logging.error("An error occurred: %s", str(e))
                # Show the error in a popup
                CustomMessageBox("Error", "An error occured in downloadSolar.SolarGen(...) with the following Exception : {error}".format(error=e))
            else:
                CustomMessageBox("Success","Solar has been retrived and saved in the ./data/solar")

    def plot_timeseries_data(self, csv_file):
        
        if not csv_file:
            CustomMessageBox('Warning', 'Please enter a filename of csv formated data to plot.')
            check = False
            return
        else:
            check = True

        try:
            
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            data = pd.read_csv(csv_file)
            keys = data.keys()
            key = keys[1] # plot the selected column
            x = [i for i in range(len(data[key]))]

            # Plot the data
            self.ax.plot(x, data[key], label=key)
            self.ax.set_xlabel('Time (hours)')
            self.ax.set_ylabel(key)
            self.ax.legend()

            self.canvas.draw()
        except Exception as e:
            logging.error("There was an error in the plot_timeseries_data function of the MainWindow Class  : %s", str(e))
            CustomMessageBox('Warning', "There was an error when trying to plot the data : {err}>".format(err=e))
            check = False
        
        return check
  
    # ---- UTILITY RATE DATA DOWNLOAD FUNCTIONS ----
    
    def download_and_extract_utility_rate_data(self):
        # this function downloads utility rate information from OpenEI
        # look at the combo box selection for grid region and construct the download link 
        url = 'https://openei.org/apps/USURDB/download/usurdb.csv.gz'
        file_name = os.path.basename(url)
        destination_folder = 'data/rates' 
        file_path = os.path.join(destination_folder, file_name)

        # Check if the destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Download the GZIP file
        try:
            response = requests.get(url,proxies=self.proxy_settings,verify=True)
            response.raise_for_status()  # Raise an error for bad responses

            # Save the GZIP file
            with open(file_path, 'wb') as gzip_file_path:
                gzip_file_path.write(response.content)

            CustomMessageBox('Success', 'Utility rate data files downloaded and extracted successfully.')

        except requests.exceptions.RequestException as e:
            logging.error(f'Failed to download the utility rate data file: {e}')
            CustomMessageBox('Error', f'Failed to download the utility rate data file: {e}')
        except zipfile.BadZipFile:
            logging.error('The downloaded utility rate data file is not a valid ZIP file.')
            CustomMessageBox('Error', 'The downloaded utility rate data file is not a valid ZIP file.')
        except Exception as e:
            logging.error(f'An error occurred: {e}')
            CustomMessageBox('Error', f'An error occurred: {e}')
        else:
            self.utility_rate_data = pd.read_csv(file_path, compression='gzip')  # Load the CSV file into a DataFrame

    def search_utilities(self):
        search_text = self.ui.rateSearchInput.text().strip()
        if not search_text:
            CustomMessageBox('Warning', 'Please enter a utility to search.')
            return

        # Filter the DataFrame based on the search text
        filtered_data = self.utility_rate_data[
            self.utility_rate_data['utility'].str.contains(search_text, case=False, na=False) & 
            (self.utility_rate_data['enddate'].isna() | (self.utility_rate_data['enddate'] == ''))
            ]
        
        if filtered_data.empty:
            filtered_data = self.utility_rate_data[
                self.utility_rate_data['label'].str.contains(search_text, case=False, na=False) & 
                (self.utility_rate_data['enddate'].isna() | (self.utility_rate_data['enddate'] == ''))
                ]

        # Clear previous results
        self.ui.rateSearchResultsTable.setRowCount(0)

        if filtered_data.empty:
            CustomMessageBox('No Results', 'No matching entries found.')
            return

        # Populate the search results table with the filtered results
        self.ui.rateSearchResultsTable.setRowCount(len(filtered_data))
        for row_index, (index, row) in enumerate(filtered_data.iterrows()):
            self.ui.rateSearchResultsTable.setItem(row_index, 0, QtWidgets.QTableWidgetItem(row['label']))
            self.ui.rateSearchResultsTable.setItem(row_index, 1, QtWidgets.QTableWidgetItem(row['utility']))
            self.ui.rateSearchResultsTable.setItem(row_index, 2, QtWidgets.QTableWidgetItem(row['name']))
            self.ui.rateSearchResultsTable.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(row['startdate'])))
            self.ui.rateSearchResultsTable.setItem(row_index, 4, QtWidgets.QTableWidgetItem(str(row['sector'])))

    def on_rate_item_clicked(self, item):
        # Get the row of the clicked utility rate
        row = item.row()
        # Get the 'name' entry from the second column (index 1)
        label_item = self.ui.rateSearchResultsTable.item(row,0)
        if label_item:
            # Set the text of selectedUtilityRateInput to the selected rate label
            self.ui.selectedUtilityRateInput.setText(label_item.text())
            self.selectedUtilityRateLabel = label_item.text()

            selected_data = self.utility_rate_data[
            self.utility_rate_data['label'].str.contains(label_item.text(), case=False, na=False) & 
            (self.utility_rate_data['enddate'].isna() | (self.utility_rate_data['enddate'] == ''))
            ]
            # Populate the rate information table with the selected data
            column_names = selected_data.columns.tolist()
            # Clear previous results
            self.ui.rateInformationTable.setRowCount(0)
            row_position = 0
            for column_index in range(len(column_names)):
                if str(selected_data[column_names[column_index]].iloc[0]) != 'nan':
                    self.ui.rateInformationTable.insertRow(row_position)
                    self.ui.rateInformationTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(column_names[column_index]))
                    self.ui.rateInformationTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(selected_data[column_names[column_index]].iloc[0])))
                    row_position = row_position + 1

    def plot_rate_schedule_data(self,selected_rate):
        check = True
        if not self.selectedUtilityRateLabel is None:
            idx = self.utility_rate_data.index[self.utility_rate_data['label'] == selected_rate].tolist()
            if len(idx)==0:
                check = False
                logging.warning('The utility rate label could not be located in the database.')
                CustomMessageBox('Warning','The utility rate label could not be located in the database.')
                return check
            
            row = self.utility_rate_data.iloc[idx[0]]


            if pd.notna(row['energyweekdayschedule']):
                self.figure.clear()
                self.ax1 = self.figure.add_subplot(211)
                self.ax2 = self.figure.add_subplot(212)
                weakdaydata = ast.literal_eval(self.utility_rate_data.at[idx[0], 'energyweekdayschedule'])
                weakenddata = ast.literal_eval(self.utility_rate_data.at[idx[0], 'energyweekendschedule'])
                # Create a colormap
                unique_values1 = np.unique(weakdaydata)
                unique_values2 = np.unique(weakenddata)
                cmap = plt.get_cmap('Pastel1')

                # Create a color mapping for the unique values
                norm1 = mcolors.BoundaryNorm(boundaries=np.arange(len(unique_values1) + 1) - 0.5, ncolors=len(unique_values1))
                norm2 = mcolors.BoundaryNorm(boundaries=np.arange(len(unique_values2) + 1) - 0.5, ncolors=len(unique_values2))

                # Create the plot
                self.ax1.imshow(weakdaydata, cmap=cmap, norm=norm1)
                self.ax2.imshow(weakenddata, cmap=cmap, norm=norm2)

                # Add text annotations for each cell
                for (i, j), value in np.ndenumerate(weakdaydata):
                    self.ax1.text(j, i, value, ha='center', va='center', color='black')
                # Add text annotations for each cell
                for (i, j), value in np.ndenumerate(weakdaydata):
                    self.ax2.text(j, i, value, ha='center', va='center', color='black')

                # Set ticks and labels
                self.ax1.set_title('Weakday Schedule')
                self.ax1.set_xticks(np.arange(24))
                self.ax1.set_yticks(np.arange(12))
                #self.ax1.set_xticklabels([f'{h}:00' for h in range(24)], rotation=90, text='black')
                self.ax1.set_xticklabels(['' for h in range(24)], rotation=90, text='black')
                self.ax1.set_yticklabels(self.MONTH_NAMES, text='black')
                self.ax2.set_title('Weakend Schedule')
                self.ax2.set_xticks(np.arange(24))
                self.ax2.set_yticks(np.arange(12))
                self.ax2.set_xticklabels([f'{h}:00' for h in range(24)], rotation=90, text='black')
                self.ax2.set_yticklabels(self.MONTH_NAMES, text='black')

                # Set grid
                self.ax1.grid(False)
                self.ax2.grid(False)
                self.canvas.draw()
                '''except Exception as e:
                    logging.error("There was an error in the plot_rate_schedule_data function of the MainWindow Class  : %s", str(e))
                    check = False'''
            else:
                logging.error('Selected utility rate has a schedule of NaN')
                CustomMessageBox('Error','Selected utility rate has a schedule of NaN')
                check = False
        return check

    def save_electrical_load_files(self, file_path):
        check = True
        try:
            self.saved_electrical_load_files_path = file_path
            self.electrical_load_files = {}
            for row in range(self.ui.loadFilesInputTable.rowCount()):
                Month = self.MONTH_NAMES[row]
                row_data = {
                    "File": self.ui.loadFilesInputTable.item(row, 0).text(),  # Get the text from the input item 
                }
                self.electrical_load_files[Month] = row_data  # Use the row index as the key
            with open(self.saved_electrical_load_files_path, "w") as json_file:
                json.dump(self.electrical_load_files,json_file,indent=4)
        except Exception as e:
            logging.error("There was an error in the save_electrical_load_files function of the MainWindow Class  : %s", str(e))
            check = False
        
        return check
    
    def split_load_file_by_month(self,csv_file):
        if self.ui.selectSystemComboBox.currentText():
            check = True
        else:
            check = False
            CustomMessageBox('Warning', 'Please select a electrical load file to split.')
            return check
        try:
            data = pd.read_csv(csv_file, parse_dates=['Date'], dayfirst=True)
            if data['Date'].dtype == 'object':
                # Custom date parser function
                def custom_date_parser(date_str):
                    return datetime.strptime(date_str, "%m/%d/%Y %H:%M")
                data = pd.read_csv(csv_file, parse_dates=['Date'], date_parser=custom_date_parser)

            # Check for non-numeric KWH values
            non_numeric = data[~data['KWH'].apply(lambda x: isinstance(x, (int, float)))]
            if not non_numeric.empty:
                print("Warning: The following rows have non-numeric KWH values:")
                print(non_numeric)

            # Calculate the time step (dt)
            data['Time Step'] = data['Date'].diff().dt.total_seconds()
            dt = data['Time Step'].mode()[0] if not data['Time Step'].isnull().all() else None

            if dt:
                print(f"Calculated time step (dt): {dt} seconds")
            else:
                print("Could not determine the time step (dt).")

            # Determine the base file name
            base_file_name = os.path.splitext(os.path.basename(csv_file))[0]

            # Create a dictionary to hold monthly data
            monthly_data = {i: [] for i in range(1, 13)}
            missing_data = {i: [] for i in range(1, 13)}

            # Split data by month
            for index, row in data.iterrows():
                month = row['Date'].month
                monthly_data[month].append(row)

            # Prepare to collect month file names and month names
            month_file_names = []
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]

            # Check for completeness and save monthly files
            for month, rows in monthly_data.items():
                if not rows:
                    continue
                
                # Create a DataFrame for the month
                month_df = pd.DataFrame(rows)
                
                # Get the year from the first date in the month
                year = month_df['Date'].dt.year.iloc[0]
                
                # Get the number of days in the month
                num_days = calendar.monthrange(year, month)[1]
                
                # Calculate expected rows based on the time step
                expected_rows = num_days * (86400 // dt) if dt else 0  # 86400 seconds in a day
                if len(month_df) < expected_rows:
                    missing_data[month].append(f"Missing {expected_rows - len(month_df)} time intervals.")
                
                
                # Construct the month file name
                month_file_name = f'data/load/{base_file_name}-{month:02d}.csv'
                
                month_file_names.append(month_file_name)
                
                # Save the month file
                month_df.to_csv(month_file_name, index=False)
                print(f"Saved: {month_file_name}")

            # Check if all months are present
            all_months_present = all(len(monthly_data[i]) > 0 for i in range(1, 13))
            if all_months_present:
                print("All months are present.")
            else:
                print("Warning: Some months are missing data.")
            
            # Prepare JSON output
            file_list = {month_names[i]: {"File": month_file_names[i]} for i in range(12)}
            self.ui.loadFilesInputTable.setRowCount(12)
            self.ui.loadFilesInputTable.setColumnCount(1)
            row = 0
            for month in file_list:
                self.ui.loadFilesInputTable.setItem(row, 0, QtWidgets.QTableWidgetItem(file_list[month]['File']))
                row = row + 1

        except Exception as e:
            logging.error("There was an error in the split_load_file_by_month function of the MainWindow Class  : %s", str(e))
            CustomMessageBox('Error', 'There was an error in the split_load_file_by_month function of the MainWindow Class : {err}'.format(err=e))
            check = False


    # ---- RUN BTM ANALYSIS FUNCTIONS ----

    def update_btm_analysis_inputs(self):
        # Energy Storage System Model Inputs        
        # ///////////////////////////////////////////////////////////////
        self.ui.summaryESSModelInputsTable.setRowCount(1)
        self.ui.summaryESSModelInputsTable.setColumnCount(3)
        model_path = self.ui.openESSModelFileInput.text()
        self.load_json_ess_model_data(model_path)
        self.ui.summaryESSModelInputsTable.setItem(0, 0, QtWidgets.QTableWidgetItem('Model Name'))
        model_name = model_path.split('/')[-1]
        self.ui.summaryESSModelInputsTable.setItem(0, 1, QtWidgets.QTableWidgetItem(model_name))
        for system in self.system_data:
            keys = self.system_data[system].keys()
            for key in keys:
                if key != "Dynamic Power Limits":
                    row_position = self.ui.summaryESSModelInputsTable.rowCount()
                    self.ui.summaryESSModelInputsTable.insertRow(row_position)
                    self.ui.summaryESSModelInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(self.system_data[system]['System Name']))
                    self.ui.summaryESSModelInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(key))
                    self.ui.summaryESSModelInputsTable.setItem(row_position, 2, QtWidgets.QTableWidgetItem(str(self.system_data[system][key])))
                elif key == "Dynamic Power Limits":
                    row_position = self.ui.summaryESSModelInputsTable.rowCount()
                    self.ui.summaryESSModelInputsTable.insertRow(row_position)
                    self.ui.summaryESSModelInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(self.system_data[system]['System Name']))
                    self.ui.summaryESSModelInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem("# of D.P.L."))
                    num_dynamic_power_limits = len(self.system_data[system][key].keys())
                    self.ui.summaryESSModelInputsTable.setItem(row_position, 2, QtWidgets.QTableWidgetItem(str(num_dynamic_power_limits)))


        # Site Load and Grid Import Export Power Limit Inputs 
        # ///////////////////////////////////////////////////////////////
        self.grid_load_and_limits = {}
        self.grid_load_and_limits['saved_electrical_load_files'] = self.saved_electrical_load_files
        self.grid_load_and_limits['powerImportLimitInput'] = float(self.ui.powerImportLimitInput.text())
        self.grid_load_and_limits['powerExportLimitInput'] = float(self.ui.powerExportLimitInput.text())
 
        self.ui.summaryGridLimitsInputsTable.setRowCount(0)
        self.ui.summaryGridLimitsInputsTable.setColumnCount(2)
        
        keys = self.grid_load_and_limits.keys()
        for key in keys:
            if key != 'saved_electrical_load_files':
                row_position = self.ui.summaryGridLimitsInputsTable.rowCount()
                self.ui.summaryGridLimitsInputsTable.insertRow(row_position)
                self.ui.summaryGridLimitsInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(key))
                self.ui.summaryGridLimitsInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(self.grid_load_and_limits[key])))
            else:
                if len(self.saved_electrical_load_files)>0:
                    for month in self.saved_electrical_load_files:   
                        row_position = self.ui.summaryGridLimitsInputsTable.rowCount()
                        self.ui.summaryGridLimitsInputsTable.insertRow(row_position)
                        self.ui.summaryGridLimitsInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(month + " data"))
                        self.ui.summaryGridLimitsInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(self.saved_electrical_load_files[month]['File']))

        # MOER Signal Inputs 
        # ///////////////////////////////////////////////////////////////
        self.ui.summaryMOERSignalInputsTable.setRowCount(0)
        self.ui.summaryMOERSignalInputsTable.setColumnCount(2)
        self.select_MOER_files() # populates the self.MOER_Signal directory
        keys = self.MOER_Signal.keys()
        for key in keys:
            if key != 'Selected Files':
                row_position = self.ui.summaryMOERSignalInputsTable.rowCount()
                self.ui.summaryMOERSignalInputsTable.insertRow(row_position)
                self.ui.summaryMOERSignalInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(key))
                self.ui.summaryMOERSignalInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(self.MOER_Signal[key])))
            else:
                for file in self.MOER_Signal['Selected Files']:
                    row_position = self.ui.summaryMOERSignalInputsTable.rowCount()
                    self.ui.summaryMOERSignalInputsTable.insertRow(row_position)
                    file_date_str = file.split('_')[3]  # Extracting the date part
                    file_date = datetime.strptime(file_date_str, '%Y-%m')
                    self.ui.summaryMOERSignalInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(str(file_date)))
                    self.ui.summaryMOERSignalInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(file)))

        
        # Solar Signal Inputs 
        # ///////////////////////////////////////////////////////////////  
        self.ui.summarySolarSignalInputsTable.setRowCount(0)
        self.ui.summarySolarSignalInputsTable.setColumnCount(2)
        solar_data_path = self.ui.openSolarResourceFileInput.text()

        with open(solar_data_path,'r') as csvfile:
            # Create a CSV reader object
            csv_reader = csv.reader(csvfile)
            
            # Read the first row
            first_row = next(csv_reader)
            if first_row[0] == 'ï»¿PVWatts Hourly PV Performance Data':
                print('PVWatts Data')
                meta_data_dict = {}
                ii = 1
                for row in csv_reader:
                    if len(row) >= 2:  # Ensure there are at least two columns
                        key = row[0]
                        value = row[1]
                        meta_data_dict[key] = value
                    ii = ii + 1
                    if ii >=17:
                        break
                self.solar_site_data = meta_data_dict
                self.solar_site_data['Data File Path'] = solar_data_path
                solar_data_name = 'PVWatts Data'
                self.solar_site_data['Data File Name'] = solar_data_name
                self.solar_site_data['Local Time Zone'] = '0'
            if first_row[0] == 'Source':
                print('Automatic download')
                solar_data_name = solar_data_path.split('/')[-1]
                meta_data_path = solar_data_path.split('_')[0] +'.csv'
                meta_data = pd.read_csv(meta_data_path, header=None)

                solar_metadata_keys = meta_data.iloc[0].tolist()  # First row as keys
                solar_metadata_values = meta_data.iloc[1].tolist()  # Second row as values
                
                # Create a dictionary from keys and values=
                self.solar_site_data = dict(zip(solar_metadata_keys, solar_metadata_values))
                self.solar_site_data['Data File Path'] = solar_data_path
                self.solar_site_data['Data File Name'] = solar_data_name

        self.ui.summarySolarSignalInputsTable.setRowCount(2)
        self.ui.summarySolarSignalInputsTable.setItem(0, 0, QtWidgets.QTableWidgetItem('Data File Name'))
        self.ui.summarySolarSignalInputsTable.setItem(1, 1, QtWidgets.QTableWidgetItem(str(solar_data_name)))  

        keys = self.solar_site_data.keys()
        for key in keys:
            row_position = self.ui.summarySolarSignalInputsTable.rowCount()
            self.ui.summarySolarSignalInputsTable.insertRow(row_position)
            self.ui.summarySolarSignalInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(key))
            self.ui.summarySolarSignalInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(self.solar_site_data[key])))
        
        self.solar_site_data['Solar Degradation Rate in Year 1'] = float(self.ui.solarDegradationInFirstYearInput.text())
        self.solar_site_data['Solar Degradation Rate Year >1'] = float(self.ui.solarDegradationPerYearAferFirstInput.text())

        # Utility Rate Inputs 
        # ///////////////////////////////////////////////////////////////
        self.ui.summaryUtilityRateInputsTable.setRowCount(0)
        self.ui.summaryUtilityRateInputsTable.setColumnCount(2)
        self.selected_utility_rate = {}
        self.selected_utility_rate['label'] = self.ui.selectedUtilityRateInput.text()
        selected_data = self.utility_rate_data[
            self.utility_rate_data['label'].str.contains(self.selected_utility_rate['label'], case=False, na=False) & 
            (self.utility_rate_data['enddate'].isna() | (self.utility_rate_data['enddate'] == ''))
            ]
        
        # Populate the rate summaary table with the selected data
        column_names = selected_data.columns.tolist()
        # Clear previous results
        self.ui.summaryUtilityRateInputsTable.setRowCount(0)
        self.ui.summaryUtilityRateInputsTable.setColumnCount(2)
        row_position = 0
        for column_index in range(len(column_names)):
            if str(selected_data[column_names[column_index]].iloc[0]) != 'nan':
                self.ui.summaryUtilityRateInputsTable.insertRow(row_position)
                self.selected_utility_rate[column_names[column_index]] = selected_data[column_names[column_index]].iloc[0]
                self.ui.summaryUtilityRateInputsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(column_names[column_index]))
                self.ui.summaryUtilityRateInputsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(selected_data[column_names[column_index]].iloc[0])))
                row_position = row_position + 1

        # Analysis Configuration Inputs
        # ///////////////////////////////////////////////////////////////
        analysis_name = self.ui.analysisNameInput.text()
        timestep = self.check_selected_time_step()
        plot_results = False
        carbon_weight = float(self.ui.assumedCarbonWeightInput.text())
        net_meter_price = float(self.ui.netMeterPriceInput.text())
        project_life  = int(self.ui.projectLifeInput.text())
        discount_rate  = float(self.ui.discountRateInput.text())
        self.analysis_configuration = {'analysis_name':analysis_name,
                                  'timestep':timestep,
                                  'plot_results':plot_results,
                                  'carbon_weight':carbon_weight,
                                  'net_meter_price': net_meter_price,
                                  'project_life':project_life,
                                  'discount_rate':discount_rate,
                                  'solver': self.solver
                                  }      

        self.btm_analyis_ready = True  
        return 

    def run_btm_analysis(self):
        if self.btm_analyis_ready:
            analysis_inputs = {"grid_load_and_limits" : self.grid_load_and_limits, \
                            "MOER_Signal" : self.MOER_Signal, \
                            "selected_utility_rate" : self.selected_utility_rate, \
                            "system_data" : self.system_data, \
                            "solar_site_data" : self.solar_site_data,
                            "analysis_configuration" : self.analysis_configuration}
            
            self.analysis_thread = BTMAalysisManager(analysis_inputs)
            self.analysis_thread.signals.status.connect(self.print_output)
            self.analysis_thread.signals.results.connect(self.print_results)
            self.analysis_thread.signals.finished.connect(self.thread_complete)
            self.analysis_thread.signals.progress.connect(self.progress_fn)

            self.ui.stopAnalysisProcessButton.setEnabled(True)
            self.ui.BTMAnalysisProgressBar.show()
            self.ui.BTMAnalysisProgressBar.setValue(int(0))

            # Execute
            self.threadpool.start(self.analysis_thread)

        else:
            CustomMessageBox("Error","The analysis inputs are emtpy. Plase push the Update Analysis Inputs button first.")
        return

    def check_selected_time_step(self):
        if self.ui.timeStepRadioButton1hr.isChecked():
            selected_time_step = 60
        elif self.ui.timeStepRadioButton30min.isChecked():
            selected_time_step = 30
        elif self.ui.timeStepRadioButton15min.isChecked():
            selected_time_step = 15
        elif self.ui.timeStepRadioButton5min.isChecked():
            selected_time_step = 5
        else:
            logging.warning("No timestep selected when running analysis")
            selected_time_step = 'None selected'
        return selected_time_step
    
    def progress_fn(self, n):
        self.ui.BTMAnalysisProgressBar.setValue(int(100*n/12))

    def print_output(self, s):
        self.ui.pyomoSolverOutputTextDisplay.append(s)

    def print_results(self, s):
        self.ui.resultsTextDisplay.append(s)

    def thread_complete(self):
        self.print_output("Processing thread has closed.")

    def stop_analysis(self):
        self.analysis_thread.stop()
        self.ui.stopAnalysisProcessButton.setEnabled(False)
        pass

    def populate_results_plot_combos(self):
        success = None
        self.results_data = {}
        try:
            filename = self.ui.openResultsFileInput.text()
            with open(filename,'r') as jsonfile:
                results_data = json.load(jsonfile)
            success = True
            analysis_name = list(results_data.keys())[0]
            month = self.ui.resultsMonthlSelectComboBox.currentText() 
            data = results_data[analysis_name][month]

            if 'LOAD' in data:
                self.ui.resultsSignalSelectComboBox.addItem('Load')
            if 'DEMAND_PRICE' in data:
                self.ui.resultsSignalSelectComboBox.addItem('Demand Price')
            if 'ENERGY_PRICE' in data:
                self.ui.resultsSignalSelectComboBox.addItem('Eenergy Price')
            if 'MOER' in data:
                self.ui.resultsSignalSelectComboBox.addItem('MOER')
            if 'netload' in data:
                self.ui.resultsSignalSelectComboBox.addItem('Net Load')
            if 'PV' in data:
                self.ui.resultsSignalSelectComboBox.addItem('PV Available')
            if 'pv_only_c' in data:
                self.ui.resultsSignalSelectComboBox.addItem('PV Only Curtailment')
            if 'pvc' in data:
                self.ui.resultsSignalSelectComboBox.addItem('PV + ES Curtailment')
            
            if 'pe' in data:
                i = 0
                for system in results_data[analysis_name][month]['analysis_inputs']['system_data']:
                    name = results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['System Name']
                    self.ui.resultsSignalSelectComboBox.addItem(name + ' Power')
                    i += 1
            if 'soc' in data:
                i = 0
                for system in results_data[analysis_name][month]['analysis_inputs']['system_data']:
                    name = results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['System Name']
                    self.ui.resultsSignalSelectComboBox.addItem(name + ' SOC')
                    i += 1



            # use the elements of the results data to populate self.ui.resultsSignalSelectComboBox.addItem(str(element))
        except Exception as e:
            print('There was an error when trying to populate the results plot combo box : {error}'.format(error=e))
            success = False
        
        return success

    def plot_results_signal_data(self,csv_file):
        check = True

        file_name = self.ui.openResultsFileInput.text()
        data_loaded = False
        if os.path.exists(file_name):
            # If it exists, read the existing data
            with open(file_name, 'r') as json_file:
                try:
                    results_data = json.load(json_file)
                    data_loaded = True
                except json.JSONDecodeError:
                    CustomMessageBox("Warning","Results file is empty or there was another error when using json.load(json_file) in run_lifetime_analysis")
        else:
            # If it does not exist, initialize existing_data as an empty dictionary
            CustomMessageBox("Warning","Results file does not exist.")

        try:
            self.results_figure.clear()
            self.results_ax = self.results_figure.add_subplot(111)
            time_key = 't'
            month = self.ui.resultsMonthlSelectComboBox.currentText()
            key_text = self.ui.resultsSignalSelectComboBox.currentText()
            analysis_name = list(results_data.keys())[0]

            if key_text == 'Load':
                key = 'LOAD'
            elif key_text == 'Demand Price':
                key = 'DEMAND_PRICE'
            elif key_text == 'Eenergy Price':
                key = 'ENERGY_PRICE'
            elif key_text == 'MOER':
                key = 'MOER'
            elif key_text == 'Net Load':
                key = 'netload'
            elif key_text == 'PV Available':
                key = 'PV'
            elif key_text == 'PV Only Curtailment':
                key = 'pv_only_c'
            elif key_text == 'PV + ES Curtailment':
                key = 'pvc'
            
            sys = 0
            for system in results_data[analysis_name][month]['analysis_inputs']['system_data']:
                name = results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['System Name']
                if key_text == name + ' Power':
                    key = 'pe'
                    sys = int(system.split(' ')[1])

            for system in results_data[analysis_name][month]['analysis_inputs']['system_data']:
                name = results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['System Name']
                if key_text == name + ' SOC':
                    key = 'soc'
                    sys = int(system.split(' ')[1])

            data = results_data[analysis_name][month]

            hour_start = 24 * (int(self.ui.startDayPlotResultsInput.text()) - 1)
            hour_end = 24 * (int(self.ui.endDayPlotResultsInput.text()))
            index_range = [i for i in range(len(data[time_key])) if hour_start <= data[time_key][i] <= hour_end]
            # Plot the data
            if sys == 0:
                self.results_ax.plot([data[time_key][i] for i in index_range], [data[key][i] for i in index_range], label=key_text)
            elif sys > 0:
                self.results_ax.plot([data[time_key][i] for i in index_range], [data[key][sys-1][i] for i in index_range], label=key_text)

            self.results_ax.set_xlabel("Time (hr)")
            self.results_ax.set_ylabel(key)
            self.results_ax.legend()

            self.results_canvas.draw()
        except Exception as e:
            check = False
            logging.error('An error occured when plotting the results in plot_results_signal_data : {error}'.format(error=e))
        return check

    def run_lifetime_analysis(self):
        file_name = self.ui.openResultsFileListInput.text()
        data_loaded = False
        if os.path.exists(file_name):
            # If it exists, read the existing data
            with open(file_name, 'r') as json_file:
                try:
                    self.results_data = json.load(json_file)
                    data_loaded = True
                except json.JSONDecodeError:
                    CustomMessageBox("Warning","Results file is empty or there was another error when using json.load(json_file) in run_lifetime_analysis")
        else:
            # If it does not exist, initialize existing_data as an empty dictionary
            CustomMessageBox("Warning","Results file does not exist.")
        if data_loaded:
            keys = list(self.results_data.keys())
            analysis_name = keys[0]
            #self.ui.resultsTable_1.setRowCount(len(list(self.results_data[analysis_name].keys())))
            total_baseline_cost = 0
            total_pv_cost = 0
            total_pv_cost_change = 0
            total_es_pv_cost = 0
            total_es_pv_cost_change = 0

            total_baseline_ghg = 0
            total_pv_ghg = 0
            total_pv_ghg_change = 0
            total_es_pv_ghg = 0
            total_es_pv_ghg_change = 0
            months = self.results_data[analysis_name]

            # Display the Cost and GHG resutlts in tables 
            for month in months:
                row_index = self.MONTH_NAMES.index(month)

                total_baseline_cost     += self.results_data[analysis_name][month]["Baseline Cost"]
                total_pv_cost           += self.results_data[analysis_name][month]["PV Only Cost"]
                total_pv_cost_change    += self.results_data[analysis_name][month]["PV Only Cost Impact"]
                total_es_pv_cost        += self.results_data[analysis_name][month]["ES + PV Cost"]
                total_es_pv_cost_change += self.results_data[analysis_name][month]["ES + PV Cost Impact"]
                
                self.ui.resultsTable_1.setItem(row_index, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["Baseline Cost"])))
                self.ui.resultsTable_1.setItem(row_index, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["PV Only Cost"])))
                self.ui.resultsTable_1.setItem(row_index, 2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["PV Only Cost Impact"])))
                self.ui.resultsTable_1.setItem(row_index, 3, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["ES + PV Cost"])))
                self.ui.resultsTable_1.setItem(row_index, 4, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["ES + PV Cost Impact"])))

                total_baseline_ghg      += self.results_data[analysis_name][month]["Baseline GHG"]
                total_pv_ghg            += self.results_data[analysis_name][month]["PV Only GHG"]
                total_pv_ghg_change     += self.results_data[analysis_name][month]["PV Only GHG Impact"]
                total_es_pv_ghg         += self.results_data[analysis_name][month]["ES + PV GHG"]
                total_es_pv_ghg_change  += self.results_data[analysis_name][month]["ES + PV GHG Impact"]

                self.ui.resultsTable_2.setItem(row_index, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["Baseline GHG"])))
                self.ui.resultsTable_2.setItem(row_index, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["PV Only GHG"])))
                self.ui.resultsTable_2.setItem(row_index, 2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["PV Only GHG Impact"])))
                self.ui.resultsTable_2.setItem(row_index, 3, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["ES + PV GHG"])))
                self.ui.resultsTable_2.setItem(row_index, 4, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=self.results_data[analysis_name][month]["ES + PV GHG Impact"])))

            row_index = 12
            self.ui.resultsTable_1.setItem(row_index, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_baseline_cost)))
            self.ui.resultsTable_1.setItem(row_index, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_pv_cost)))
            self.ui.resultsTable_1.setItem(row_index, 2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_pv_cost_change)))
            self.ui.resultsTable_1.setItem(row_index, 3, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_es_pv_cost)))
            self.ui.resultsTable_1.setItem(row_index, 4, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_es_pv_cost_change)))

            self.ui.resultsTable_2.setItem(row_index, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_baseline_ghg)))
            self.ui.resultsTable_2.setItem(row_index, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_pv_ghg)))
            self.ui.resultsTable_2.setItem(row_index, 2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_pv_ghg_change)))
            self.ui.resultsTable_2.setItem(row_index, 3, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_es_pv_ghg)))
            self.ui.resultsTable_2.setItem(row_index, 4, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_es_pv_ghg_change)))

            # Display the Cost and GHG results in Bar Charts
            # Cost Bar Chart
            pv_only_cost = [self.results_data[analysis_name][month]['PV Only Cost Impact'] for month in months]
            es_pv_cost = [self.results_data[analysis_name][month]['ES + PV Cost Impact'] for month in months]

            # Set up the bar chart
            bar_width = 0.35
            x = np.arange(len(months))


            self.cost_results_bar_chart.clear()
            self.cost_results_ax = self.cost_results_bar_chart.add_subplot(111)

            # Create the bar chart
            self.cost_results_ax.bar(x - bar_width/2, pv_only_cost, width=bar_width, label='PV Only Cost Impact')
            self.cost_results_ax.bar(x + bar_width/2, es_pv_cost, width=bar_width, label='ES + PV Cost Impact')

            # Add labels and title
            self.cost_results_ax.set_ylabel('Reduction in Cost ($)')
            self.cost_results_ax.set_xticks(x, months, rotation=90)  # Rotate month names 90 degrees
            self.cost_results_ax.legend()    
            self.cost_results_bar_chart.tight_layout()      # Adjust layout to make room for rotated x labels       

            self.cost_results_canvas.draw()

            # GHG Bar Chart
            pv_only_ghg = [self.results_data[analysis_name][month]['PV Only GHG Impact'] for month in months]
            es_pv_ghg = [self.results_data[analysis_name][month]['ES + PV GHG Impact'] for month in months]

            # Set up the bar chart
            bar_width = 0.35
            x = np.arange(len(months))


            self.ghg_results_bar_chart.clear()
            self.ghg_results_ax = self.ghg_results_bar_chart.add_subplot(111)

            # Create the bar chart
            self.ghg_results_ax.bar(x - bar_width/2, pv_only_ghg, width=bar_width, label='PV Only GHG Impact')
            self.ghg_results_ax.bar(x + bar_width/2, es_pv_ghg, width=bar_width, label='ES + PV GHG Impact')

            # Add labels and title
            self.ghg_results_ax.set_ylabel('Reduction in GHG (tons)')
            self.ghg_results_ax.set_xticks(x, months, rotation=90)  # Rotate month names 90 degrees
            self.ghg_results_ax.legend()   
            self.ghg_results_bar_chart.tight_layout()         # Adjust layout to make room for rotated x labels

            self.ghg_results_canvas.draw()



            # Plot out the yearly capacity degredation schedule for each resource
            self.results_data[analysis_name]['lifetime_analysis'] = {}

            project_life = int(self.results_data[analysis_name][month]['analysis_inputs']['analysis_configuration']['project_life'])
            self.results_data[analysis_name]['lifetime_analysis']['project_life'] = project_life

            discount_rate = self.results_data[analysis_name][month]['analysis_inputs']["analysis_configuration"]['discount_rate']
            self.results_data[analysis_name]['lifetime_analysis']['discount_rate'] = discount_rate

            grid_pen = [50 + i*50/19 for i in range(20)] # neet to update this with a user selected schedule.
            self.results_data[analysis_name]['lifetime_analysis']['grid_pen'] = grid_pen
            
            if project_life > 1:
                pv_capacity = [100, 100-self.results_data[analysis_name][month]['analysis_inputs']['solar_site_data']['Solar Degradation Rate in Year 1']]
                ess_capacity = {}
                for j in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data'])):
                    ess_capacity[j] = [100]
                    system = "System " + str(j+1)
                    ess_capacity[j].append(100 - self.results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['Degradation Rate in Year 1'])
                if project_life > 2:
                    for i in range (project_life-2):
                        pv_capacity.append(100 - self.results_data[analysis_name][month]['analysis_inputs']['solar_site_data']['Solar Degradation Rate in Year 1'] - self.results_data[analysis_name][month]['analysis_inputs']['solar_site_data']['Solar Degradation Rate Year >1']*(i+1))
                        for j in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data'])):
                            system = "System " + str(j+1)
                            ess_capacity[j].append(100 - self.results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['Degradation Rate in Year 1'] - self.results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['Degradation Rate Year > 1']*(i+1))
            else:
                pv_capacity = [100]
                ess_capacity = {}
                for j in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data'])):
                    ess_capacity[j] = [100]
            
            self.results_data[analysis_name]['lifetime_analysis']['pv_capacity'] = pv_capacity
            self.results_data[analysis_name]['lifetime_analysis']['ess_capacity'] = ess_capacity
            
            self.ui.capacityDegradationTable.setColumnCount(2)
            header_labels = ['Grid Zero-GHG Energy','PV capacity']
            
            for j in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data'])):
                system = "System " + str(j+1)
                header_labels.append(self.results_data[analysis_name][month]['analysis_inputs']['system_data'][system]['System Name'])
                column_position = self.ui.capacityDegradationTable.columnCount()
                self.ui.capacityDegradationTable.insertColumn(column_position)
            self.ui.capacityDegradationTable.setHorizontalHeaderLabels(header_labels)
            self.ui.capacityDegradationTable.setRowCount(project_life)

            for i in range (project_life):
                self.ui.capacityDegradationTable.setItem(i, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=grid_pen[i])))
                self.ui.capacityDegradationTable.setItem(i, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=pv_capacity[i])))
                for j in range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data'])):
                    self.ui.capacityDegradationTable.setItem(i, j+2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=ess_capacity[j][i])))

            # Rerun the analysis with the pv power and es capacity degredation for each year and display the results in a table
            self.ui.resultsSummaryTable.horizontalHeader().setVisible(True)
            self.ui.resultsSummaryTable.setRowCount(project_life+1)
            header_labels = ["Year {year}".format(year=y+1) for y in range(20)]
            header_labels.append('Total = ')
            self.ui.resultsSummaryTable.setVerticalHeaderLabels(header_labels)
            total_row_cost = [0,0,0,0,0]
            total_row_ghg = [0,0,0,0,0]
            row_cost_list = []
            row_ghg_list = []
            for year in range(project_life):
                row_cost, row_ghg = self.run_simulation_with_performace_degredation(year, grid_pen, pv_capacity, ess_capacity)
                total_row_cost = [total_row_cost[i]+row_cost[i] for i in range(5)]
                total_row_ghg = [total_row_ghg[i]+row_ghg[i] for i in range(5)]
                row_cost_list.append(row_cost)
                row_ghg_list.append(row_ghg)
                self.ui.resultsSummaryTable.setItem(year, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_cost[0])))
                self.ui.resultsSummaryTable.setItem(year, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_cost[1])))
                self.ui.resultsSummaryTable.setItem(year, 2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_cost[2])))
                self.ui.resultsSummaryTable.setItem(year, 3, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_cost[3])))
                self.ui.resultsSummaryTable.setItem(year, 4, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_cost[4])))
                
                self.ui.resultsSummaryTable.setItem(year, 5, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_ghg[0])))
                self.ui.resultsSummaryTable.setItem(year, 6, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_ghg[1])))
                self.ui.resultsSummaryTable.setItem(year, 7, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_ghg[2])))
                self.ui.resultsSummaryTable.setItem(year, 8, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_ghg[3])))
                self.ui.resultsSummaryTable.setItem(year, 9, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=row_ghg[4])))
            
            self.ui.resultsSummaryTable.setItem(project_life, 0, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_cost[0])))
            self.ui.resultsSummaryTable.setItem(project_life, 1, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_cost[1])))
            self.ui.resultsSummaryTable.setItem(project_life, 2, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_cost[2])))
            self.ui.resultsSummaryTable.setItem(project_life, 3, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_cost[3])))
            self.ui.resultsSummaryTable.setItem(project_life, 4, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_cost[4])))
            
            self.ui.resultsSummaryTable.setItem(project_life, 5, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_ghg[0])))
            self.ui.resultsSummaryTable.setItem(project_life, 6, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_ghg[1])))
            self.ui.resultsSummaryTable.setItem(project_life, 7, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_ghg[2])))
            self.ui.resultsSummaryTable.setItem(project_life, 8, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_ghg[3])))
            self.ui.resultsSummaryTable.setItem(project_life, 9, QtWidgets.QTableWidgetItem("{var1:,.2f}".format(var1=total_row_ghg[4])))

            # Display the YEARLY Cost and GHG results in Bar Charts
            # YEARLY Cost Bar Chart
            baseline_cost = [row_cost_list[year][0] for year in range(project_life)]
            pv_only_cost = [row_cost_list[year][1] for year in range(project_life)]
            es_pv_cost = [row_cost_list[year][3] for year in range(project_life)]
            
            self.results_data[analysis_name]['lifetime_analysis']['baseline_cost'] = baseline_cost
            self.results_data[analysis_name]['lifetime_analysis']['baseline_total_cost'] = total_row_cost[0]

            self.results_data[analysis_name]['lifetime_analysis']['pv_only_cost'] = pv_only_cost
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_cost'] = total_row_cost[1]
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_cost_change'] = total_row_cost[2]

            self.results_data[analysis_name]['lifetime_analysis']['es_pv_cost'] = es_pv_cost
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_cost'] = total_row_cost[3]
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_cost_change'] = total_row_cost[4]

            # Set up the bar chart
            bar_width = 0.2
            x = np.arange(project_life)

            self.yearly_cost_results_bar_chart.clear()
            self.yearly_cost_results_ax = self.yearly_cost_results_bar_chart.add_subplot(111)

            # Create the bar chart
            self.yearly_cost_results_ax.bar(x - bar_width*1.5, baseline_cost, width=bar_width, label='Baseline Cost')
            self.yearly_cost_results_ax.bar(x, pv_only_cost, width=bar_width, label='PV Only Cost')
            self.yearly_cost_results_ax.bar(x + bar_width*1.5, es_pv_cost, width=bar_width, label='ES + PV Cost')

            # Add labels and title
            self.yearly_cost_results_ax.set_ylabel('Net Presnt Cost ($)')
            self.yearly_cost_results_ax.set_xticks(x, ["Year {var1}".format(var1=year+1) for year in range(project_life)], rotation=90)  # Rotate month names 90 degrees
            self.yearly_cost_results_ax.legend()    
            self.yearly_cost_results_bar_chart.tight_layout()      # Adjust layout to make room for rotated x labels       

            self.yearly_cost_results_canvas.draw()


            # GHG Bar Chart
            baseline_ghg = [row_ghg_list[year][0] for year in range(project_life)]
            pv_only_ghg = [row_ghg_list[year][1] for year in range(project_life)]
            es_pv_ghg = [row_ghg_list[year][3] for year in range(project_life)]
            
            self.results_data[analysis_name]['lifetime_analysis']['baseline_ghg'] = baseline_ghg
            self.results_data[analysis_name]['lifetime_analysis']['baseline_total_ghg'] = total_row_ghg[0]

            self.results_data[analysis_name]['lifetime_analysis']['pv_only_ghg'] = pv_only_ghg
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_ghg'] = total_row_ghg[1]
            self.results_data[analysis_name]['lifetime_analysis']['pv_only_total_ghg_change'] = total_row_ghg[2]

            self.results_data[analysis_name]['lifetime_analysis']['es_pv_ghg'] = es_pv_ghg
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_ghg'] = total_row_ghg[3]
            self.results_data[analysis_name]['lifetime_analysis']['es_pv_total_ghg_change'] = total_row_ghg[4]

            # Set up the bar chart
            bar_width = 0.2
            x = np.arange(project_life)

            self.yearly_ghg_results_bar_chart.clear()
            self.yearly_ghg_results_ax = self.yearly_ghg_results_bar_chart.add_subplot(111)

            # Create the bar chart
            self.yearly_ghg_results_ax.bar(x - bar_width*1.5, baseline_ghg, width=bar_width, label='Baseline GHG')
            self.yearly_ghg_results_ax.bar(x, pv_only_ghg, width=bar_width, label='PV Only GHG')
            self.yearly_ghg_results_ax.bar(x + bar_width*1.5, es_pv_ghg, width=bar_width, label='ES + PV GHG')

            # Add labels and title
            self.yearly_ghg_results_ax.set_ylabel('Net GHG Emissions (tons)')
            self.yearly_ghg_results_ax.set_xticks(x, ["Year {var1}".format(var1=year+1) for year in range(project_life)], rotation=90)  # Rotate month names 90 degrees
            self.yearly_ghg_results_ax.legend()   
            self.yearly_ghg_results_bar_chart.tight_layout()         # Adjust layout to make room for rotated x labels

            self.yearly_ghg_results_canvas.draw()

            print(self.results_data[analysis_name]['lifetime_analysis'])

    def run_simulation_with_performace_degredation(self,year, Grid_Pen, PV_Capacity, ESS_Capacity):
        ''' This function takes all the data and runs a simulation accounting for the degredation in future years
            It then returns the cost and GHG iompact expected performace with those assumptions.         
        
        
        '''
        keys = list(self.results_data.keys())
        analysis_name = keys[0]

        total_baseline_cost = 0
        total_pv_cost = 0
        total_pv_cost_change = 0
        total_es_pv_cost = 0
        total_es_pv_cost_change = 0

        total_baseline_ghg = 0
        total_pv_ghg = 0
        total_pv_ghg_change = 0
        total_es_pv_ghg = 0
        total_es_pv_ghg_change = 0
        for month in self.MONTH_NAMES:            
            # Assign columns to local variables
            energy_price = self.results_data[analysis_name][month]['ENERGY_PRICE']
            plot_time = range(len(energy_price))
            co2_rate_baseline = self.results_data[analysis_name][month]['MOER']
            co2_rate = [co2_rate_baseline[i] * ((100-Grid_Pen[year]) / 50) for i in plot_time]
            load_kw = self.results_data[analysis_name][month]['LOAD']
            unique_demand_prices = list(self.results_data[analysis_name][month]["subsets"].keys())
            Sys = range(len(self.results_data[analysis_name][month]['analysis_inputs']['system_data']))

            pv_available_kw_baseline = self.results_data[analysis_name][month]['PV']
            pv_available_kw = [pv_available_kw_baseline[t] * (PV_Capacity[year] / 100) for t in plot_time]

            #t =self.results_data[analysis_name][month]["t"]
            pe_baseline = self.results_data[analysis_name][month]["pe"]

            pe = [[pe_baseline[s][t] * (ESS_Capacity[s][year] / 100) for t in plot_time] for s in Sys]

            subsets =self.results_data[analysis_name][month]["subsets"]
            dt = self.results_data[analysis_name][month]['analysis_inputs']["analysis_configuration"]['timestep'] / 60 
            discount_rate = self.results_data[analysis_name][month]['analysis_inputs']["analysis_configuration"]['discount_rate']

            pvc_baseline =self.results_data[analysis_name][month]["pvc"]
            pvc = [pvc_baseline[t] * (PV_Capacity[year] / 100) for t in plot_time]
            pv_only_c_baseline =self.results_data[analysis_name][month]["pv_only_c"] 
            pv_only_c = [pv_only_c_baseline[t] * (PV_Capacity[year] / 100) for t in plot_time]

            fixed_cost = self.results_data[analysis_name][month]['analysis_inputs']['selected_utility_rate']['fixedchargefirstmeter']
            net_meter_price = self.results_data[analysis_name][month]['analysis_inputs']['analysis_configuration']['net_meter_price']

            '''energy_cost = sum([load_kw[t]*energy_price[t]*dt for t in plot_time]) 
            demand_cost = max(sum([max([load_kw[t] for t in subsets[price]])*float(price)  for price in unique_demand_prices]),0.0)
            baseline_cost = (energy_cost + demand_cost) / ((1 + discount_rate/100)**year)
            baseline_ghg = sum([load_kw[t]*co2_rate[t]*dt for t in plot_time])
            
            energy_cost = sum([(load_kw[t] - pv_available_kw[t] + pv_only_c[t])*energy_price[t]*dt for t in plot_time]) 
            demand_cost = max(sum([max([load_kw[t] - pv_available_kw[t] + pv_only_c[t] for t in subsets[price]])*float(price)  for price in unique_demand_prices]),0.0)
            pv_only_cost = (energy_cost + demand_cost) / ((1 + discount_rate/100)**year)
            pv_only_ghg = sum([(load_kw[t] - pv_available_kw[t] + pv_only_c[t])*co2_rate[t]*dt for t in plot_time])

            energy_cost = sum([(load_kw[t] - pv_available_kw[t] + pvc[t] + sum([pe[s][t] for s in Sys]))*energy_price[t]*dt for t in plot_time]) 
            demand_cost = max(sum([max([load_kw[t] - pv_available_kw[t] + pvc[t] + sum([pe[s][t] for s in Sys]) for t in subsets[price]])*float(price)  for price in unique_demand_prices]),0.0)
            pv_es_cost = (energy_cost + demand_cost) / ((1 + discount_rate/100)**year)
            pv_es_ghg = sum([(load_kw[t] - pv_available_kw[t] + pvc[t] + sum([pe[s][t] for s in Sys]))*co2_rate[t]*dt for t in plot_time])'''

            #netload = [load_kw[t]+sum([pe[s][t] for s in sys]) - pv_available_kw[t] + pvc[t] for t in plot_time]

            baseline_energy_cost = max(sum([load_kw[t]*energy_price[t]*dt for t in plot_time]),0.0)
            baseline_demand_cost = max(sum([max([load_kw[t] for t in subsets[price]])*float(price) for price in unique_demand_prices]),0.0)
            baseline_net_meter_cost = 0.0
            baseline_cost = baseline_energy_cost + baseline_net_meter_cost + baseline_demand_cost + fixed_cost
            baseline_ghg  = sum([load_kw[t]*co2_rate[t]*dt for t in plot_time])

            pv_only_energy_cost = max(sum([(load_kw[t] - pv_available_kw[t] + pv_only_c[t])*energy_price[t]*dt for t in plot_time]),0.0) # energy cost will be positive or 0
            pv_only_demand_cost = max(sum([max([load_kw[t] - pv_available_kw[t] + pv_only_c[t] for t in subsets[price]])*float(price)  for price in unique_demand_prices]),0.0) # demand cost will be positive or 0
            pv_only_energy_net = sum([(load_kw[t] - pv_available_kw[t]  + pv_only_c[t])*dt for t in plot_time])
            pv_only_net_meter_cost = min(pv_only_energy_net*net_meter_price,0.0) # net meter cost will be negative or 0
            pv_only_cost = pv_only_energy_cost + pv_only_net_meter_cost + pv_only_demand_cost + fixed_cost
            pv_only_ghg = sum([(load_kw[t] - pv_available_kw[t] + pv_only_c[t])*co2_rate[t]*dt for t in plot_time])

            pv_es_energy_cost = max(sum([(load_kw[t] - pv_available_kw[t] + pvc[t] + sum([pe[s][t] for s in Sys]))*energy_price[t]*dt for t in plot_time]) ,0.0)
            pv_es_demand_cost = max(sum([max([load_kw[t] - pv_available_kw[t] + pvc[t] + sum([pe[s][t] for s in Sys]) for t in subsets[price]])*float(price)  for price in unique_demand_prices]),0.0)
            pv_es_energy_net = sum([(load_kw[t] - pv_available_kw[t]  + pvc[t] + sum([pe[s][t] for s in Sys]))*dt for t in plot_time])
            pv_es_net_meter_cost = min(pv_es_energy_net*net_meter_price,0.0) # net meter cost will be negative or 0
            pv_es_cost = pv_es_energy_cost + pv_es_net_meter_cost + pv_es_demand_cost + fixed_cost
            pv_es_ghg = sum([(load_kw[t] - pv_available_kw[t] + pvc[t] + sum([pe[s][t] for s in Sys]))*co2_rate[t]*dt for t in plot_time])

            total_baseline_cost += baseline_cost
            total_pv_cost += pv_only_cost
            total_pv_cost_change += pv_only_cost - baseline_cost
            total_es_pv_cost += pv_es_cost
            total_es_pv_cost_change += pv_es_cost - baseline_cost

            total_baseline_ghg += baseline_ghg
            total_pv_ghg += pv_only_ghg
            total_pv_ghg_change += pv_only_ghg - baseline_ghg
            total_es_pv_ghg += pv_es_ghg
            total_es_pv_ghg_change += pv_es_ghg - baseline_ghg

        row_cost = [total_baseline_cost, total_pv_cost, total_pv_cost_change, total_es_pv_cost, total_es_pv_cost_change]
        row_ghg  = [total_baseline_ghg, total_pv_ghg, total_pv_ghg_change, total_es_pv_ghg, total_es_pv_ghg_change]
        return row_cost, row_ghg

    def generate_analysis_report(self):

        self.cost_results_bar_chart, self.cost_results_ax = plt.subplots()
        self.ghg_results_bar_chart, self.ghg_results_ax = plt.subplots()
        self.yearly_cost_results_bar_chart, self.yearly_cost_results_ax = plt.subplots()
        self.yearly_ghg_results_bar_chart, self.yearly_ghg_results_ax = plt.subplots()


        check = True
        #try:
        print("under construction")
        
        self.report_id = datetime.now().strftime('%Y_%m_%d_%H%M%S')
        base_dir = os.getcwd()
        output_dir_name = self.report_id 
        output_dir = os.path.join(base_dir,'results', output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        '''fnamestr_cost_results_bar_chart = os.path.join(output_dir, "cost_results_bar_chart.png")
        fnamestr_ghg_results_bar_chart = os.path.join(output_dir, "ghg_results_bar_chart.png")
        fnamestr_yearly_cost_results_bar_chart = os.path.join(output_dir, "yearly_cost_results_bar_chart.png")
        fnamestr_yearly_ghg_results_bar_chart = os.path.join(output_dir, "yearly_ghg_results_bar_chart.png")

        self.cost_results_bar_chart.savefig(fnamestr_cost_results_bar_chart)
        self.ghg_results_bar_chart.savefig(fnamestr_ghg_results_bar_chart)
        self.yearly_cost_results_bar_chart.savefig(fnamestr_yearly_cost_results_bar_chart)
        self.yearly_ghg_results_bar_chart.savefig(fnamestr_yearly_ghg_results_bar_chart)'''

        report_information = {}
        report_information['output_dir'] = output_dir

        self.results_data['report_information'] = report_information
        analsys_name = list(self.results_data.keys())[0]
        print(self.results_data.keys())
        print(self.results_data[analsys_name]['January']['analysis_inputs'])
        report = BtmGenerateReport(self.results_data)
        report.generate_report_from_template()

        #except Exception as e:
        #    logging.error("There was an error when trying to generate the results report : {error}".format(error=e))
        #    check = False

        return check

    # README PAGE FUNCTIONS
    # ///////////////////////////////////////////////////////////////

    def open_readme(self):
        # Open a file dialog to select the README file
        file_name = "README.md"
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    content = file.read()
                    # Convert Markdown to HTML
                    html_content = markdown.markdown(content)
                    # Display the HTML content in the QTextBrowser
                    self.ui.READMETextBrowser.setHtml(html_content)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
         
    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

        # PRINT MOUSE EVENTS
        if event.buttons() == QtCore.Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == QtCore.Qt.RightButton:
            print('Mouse click: RIGHT CLICK')
  
    def validator(self):
        """Validate inputs in real-time."""
        for entry in self.input_field_parameters_data:
            method = getattr(self.ui, entry.get('object name'), None)

            if entry.get('type') == "float":
                Max = entry.get('max')
                Min = entry.get('min')
                try:
                    if not method.text() == '-':
                        if float(method.text()) > Max:
                            method.setText(str(Max))
                        if float(method.text()) < Min:
                            method.setText(str(Min))
                        if method.text() == '':
                            method.setText(str(0))
                except ValueError:
                    logging.error("Value error on numeric input : %s", str(entry.get('object name')))
                    pass
            if entry.get('type') == "string":
                max_length = entry.get('max length')
                s = method.text()
                truncated_string = s[:max_length]
                method.setText(truncated_string)

class UIFunctions(MainAppWindow):
    # MAXIMIZE/RESTORE
    # ///////////////////////////////////////////////////////////////
    def maximize_restore(self):
        global GLOBAL_STATE
        status = GLOBAL_STATE
        if status == False:
            self.showMaximized()
            GLOBAL_STATE = True
            self.ui.appMargins.setContentsMargins(0, 0, 0, 0)
            self.ui.maximizeRestoreAppBtn.setToolTip("Restore")
            self.ui.maximizeRestoreAppBtn.setIcon(QtGui.QIcon(u":/icons/images/icons/icon_restore.png"))
            self.ui.frame_size_grip.hide()
            self.left_grip.hide()
            self.right_grip.hide()
            self.top_grip.hide()
            self.bottom_grip.hide()
        else:
            GLOBAL_STATE = False
            self.showNormal()
            self.resize(self.width()+1, self.height()+1)
            self.ui.appMargins.setContentsMargins(10, 10, 10, 10)
            self.ui.maximizeRestoreAppBtn.setToolTip("Maximize")
            self.ui.maximizeRestoreAppBtn.setIcon(QtGui.QIcon(u":/icons/images/icons/icon_maximize.png"))
            self.ui.frame_size_grip.show()
            self.left_grip.show()
            self.right_grip.show()
            self.top_grip.show()
            self.bottom_grip.show()

    # RETURN STATUS
    # ///////////////////////////////////////////////////////////////
    def returStatus(self):
        return GLOBAL_STATE

    # SET STATUS
    # ///////////////////////////////////////////////////////////////
    def setStatus(self, status):
        global GLOBAL_STATE
        GLOBAL_STATE = status

    # TOGGLE MENU
    # ///////////////////////////////////////////////////////////////
    def toggleMenu(self, enable):
        if enable:
            # GET WIDTH
            width = self.ui.leftMenuBg.width()
            maxExtend = Settings.MENU_WIDTH
            standard = 60

            # SET MAX WIDTH
            if width == 60:
                widthExtended = maxExtend
            else:
                widthExtended = standard

            # ANIMATION
            self.animation = QtCore.QPropertyAnimation(self.ui.leftMenuBg, b"minimumWidth")
            self.animation.setDuration(Settings.TIME_ANIMATION)
            self.animation.setStartValue(width)
            self.animation.setEndValue(widthExtended)
            self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation.start()

    # TOGGLE LEFT BOX
    # ///////////////////////////////////////////////////////////////
    def toggleLeftBox(self, enable):
        if enable:
            # GET WIDTH
            width = self.ui.extraLeftBox.width()
            widthRightBox = self.ui.extraRightBox.width()
            maxExtend = Settings.LEFT_BOX_WIDTH
            color = Settings.BTN_LEFT_BOX_COLOR
            standard = 0

            # GET BTN STYLE
            style = self.ui.toggleLeftBox.styleSheet()

            # SET MAX WIDTH
            if width == 0:
                widthExtended = maxExtend
                # SELECT BTN
                self.ui.toggleLeftBox.setStyleSheet(style + color)
                if widthRightBox != 0:
                    style = self.ui.templatesButton.styleSheet()
                    self.ui.templatesButton.setStyleSheet(style.replace(Settings.BTN_RIGHT_BOX_COLOR, ''))
            else:
                widthExtended = standard
                # RESET BTN
                self.ui.toggleLeftBox.setStyleSheet(style.replace(color, ''))
                
        UIFunctions.start_box_animation(self, width, widthRightBox, "left")

    # TOGGLE RIGHT BOX
    # ///////////////////////////////////////////////////////////////
    def toggleRightBox(self, enable):
        if enable:
            # GET WIDTH
            width = self.ui.extraRightBox.width()
            widthLeftBox = self.ui.extraLeftBox.width()
            maxExtend = Settings.RIGHT_BOX_WIDTH
            color = Settings.BTN_RIGHT_BOX_COLOR
            standard = 0

            # GET BTN STYLE
            style = self.ui.templatesButton.styleSheet()

            # SET MAX WIDTH
            if width == 0:
                widthExtended = maxExtend
                # SELECT BTN
                self.ui.templatesButton.setStyleSheet(style + color)
                if widthLeftBox != 0:
                    style = self.ui.toggleLeftBox.styleSheet()
                    self.ui.toggleLeftBox.setStyleSheet(style.replace(Settings.BTN_LEFT_BOX_COLOR, ''))
            else:
                widthExtended = standard
                # RESET BTN
                self.ui.templatesButton.setStyleSheet(style.replace(color, ''))

            UIFunctions.start_box_animation(self, widthLeftBox, width, "right")

    def start_box_animation(self, left_box_width, right_box_width, direction):
        right_width = 0
        left_width = 0 

        # Check values
        if left_box_width == 0 and direction == "left":
            left_width = 240
        else:
            left_width = 0
        # Check values
        if right_box_width == 0 and direction == "right":
            right_width = 240
        else:
            right_width = 0       

        # ANIMATION LEFT BOX        
        self.left_box = QtCore.QPropertyAnimation(self.ui.extraLeftBox, b"minimumWidth")
        self.left_box.setDuration(Settings.TIME_ANIMATION)
        self.left_box.setStartValue(left_box_width)
        self.left_box.setEndValue(left_width)
        self.left_box.setEasingCurve(QtCore.QEasingCurve.InOutQuart)

        # ANIMATION RIGHT BOX        
        self.right_box = QtCore.QPropertyAnimation(self.ui.extraRightBox, b"minimumWidth")
        self.right_box.setDuration(Settings.TIME_ANIMATION)
        self.right_box.setStartValue(right_box_width)
        self.right_box.setEndValue(right_width)
        self.right_box.setEasingCurve(QtCore.QEasingCurve.InOutQuart)

        # GROUP ANIMATION
        self.group = QtCore.QParallelAnimationGroup()
        self.group.addAnimation(self.left_box)
        self.group.addAnimation(self.right_box)
        self.group.start()

    # SELECT/DESELECT MENU
    # ///////////////////////////////////////////////////////////////
    # SELECT
    def selectMenu(getStyle):
        select = getStyle + Settings.MENU_SELECTED_STYLESHEET
        return select

    # DESELECT
    def deselectMenu(getStyle):
        deselect = getStyle.replace(Settings.MENU_SELECTED_STYLESHEET, "")
        return deselect

    # START SELECTION
    def selectStandardMenu(self, widget):
        for w in self.ui.topMenu.findChildren(QtWidgets.QPushButton):
            if w.objectName() == widget:
                w.setStyleSheet(UIFunctions.selectMenu(w.styleSheet()))

    # RESET SELECTION
    def resetStyle(self, widget):
        for w in self.ui.topMenu.findChildren(QtWidgets.QPushButton):
            if w.objectName() != widget:
                w.setStyleSheet(UIFunctions.deselectMenu(w.styleSheet()))

    # IMPORT THEMES FILES QSS/CSS
    # ///////////////////////////////////////////////////////////////
    def theme(self, file, useCustomTheme):
        if useCustomTheme:
            str = open(file, 'r').read()
            self.ui.styleSheet.setStyleSheet(str)

    # START - GUI DEFINITIONS
    # ///////////////////////////////////////////////////////////////
    def uiDefinitions(self):
        def dobleClickMaximizeRestore(event):
            # IF DOUBLE CLICK CHANGE STATUS
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                QtCore.QTimer.singleShot(250, lambda: UIFunctions.maximize_restore(self))
        self.ui.titleRightInfo.mouseDoubleClickEvent = dobleClickMaximizeRestore

        if Settings.ENABLE_CUSTOM_TITLE_BAR:
            #STANDARD TITLE BAR
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

            # MOVE WINDOW / MAXIMIZE / RESTORE
            def moveWindow(event):
                # IF MAXIMIZED CHANGE TO NORMAL
                if UIFunctions.returStatus(self):
                    UIFunctions.maximize_restore(self)
                # MOVE WINDOW
                if event.buttons() == QtCore.Qt.LeftButton:
                    self.move(self.pos() + event.globalPos() - self.dragPos)
                    self.dragPos = event.globalPos()
                    event.accept()
            self.ui.titleRightInfo.mouseMoveEvent = moveWindow

            # CUSTOM GRIPS
            self.left_grip = CustomGrip(self, QtCore.Qt.LeftEdge, True)
            self.right_grip = CustomGrip(self, QtCore.Qt.RightEdge, True)
            self.top_grip = CustomGrip(self, QtCore.Qt.TopEdge, True)
            self.bottom_grip = CustomGrip(self, QtCore.Qt.BottomEdge, True)

        else:
            self.ui.appMargins.setContentsMargins(0, 0, 0, 0)
            self.ui.minimizeAppBtn.hide()
            self.ui.maximizeRestoreAppBtn.hide()
            self.ui.closeAppBtn.hide()
            self.ui.frame_size_grip.hide()

        # DROP SHADOW
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(17)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 150))
        self.ui.bgApp.setGraphicsEffect(self.shadow)

        # RESIZE WINDOW
        self.sizegrip = QtWidgets.QSizeGrip(self.ui.frame_size_grip)
        self.sizegrip.setStyleSheet("width: 20px; height: 20px; margin 0px; padding: 0px;")

        # MINIMIZE
        self.ui.minimizeAppBtn.clicked.connect(lambda: self.showMinimized())

        # MAXIMIZE/RESTORE
        self.ui.maximizeRestoreAppBtn.clicked.connect(lambda: UIFunctions.maximize_restore(self))

        # CLOSE APPLICATION
        self.ui.closeAppBtn.clicked.connect(lambda: self.close())

    def resize_grips(self):
        if Settings.ENABLE_CUSTOM_TITLE_BAR:
            self.left_grip.setGeometry(0, 10, 10, self.height())
            self.right_grip.setGeometry(self.width() - 10, 10, 10, self.height())
            self.top_grip.setGeometry(0, 0, self.width(), 10)
            self.bottom_grip.setGeometry(0, self.height() - 10, self.width(), 10)

    # ///////////////////////////////////////////////////////////////
    # END - GUI DEFINITIONS




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("icon.ico"))
    window = MainAppWindow()
    sys.exit(app.exec_())
