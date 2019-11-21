#! /usr/bin/env python3

"""
The main script which is run on the controller, specifically designed for a 
raspberry pi.

Requirements:
	pymata-aio => https://github.com/MrYsLab/pymata-aio
	
Optional:
	paho-mqtt => https://github.com/eclipse/paho.mqtt.python
		This module is required if you want to connect to a MQTT broker
		
The default config file is hard coded here.  Changing this is not recommended.
To override, create a json encoded file at <your home directory>/.config/thermostat/config.json
Any settings you find in the default config file can be overridden there.
"""

__author__ = "builderjer"
__version__ = "0.2.0"

# Builtins
import logging
import json
from pathlib import Path
import argparse
import sys
import time
import signal

# Temperary settings to just make sure this works
MAXTEMP= 69
MINTEMP = 67
IDEALTEMP = 68

# Set up the signal handler for shutdown
def shutdown(sig, frame):
	if board:
		board.shutdown()
	sys.exit()

signal.signal(signal.SIGTERM, shutdown)

# Set up the parser
parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="Output debuging symbols", action="store_true")
parser.add_argument("-v", "--verbose", help="Verbose symbols", action="store_true")
args = parser.parse_args()

# Define some global variables
CONFIG_FILE = "config/default.json"

# Get the default settings
SETTINGS = {}
with open(CONFIG_FILE, "r") as settings:
    SETTINGS = json.load(settings)

# Check if there is already a log file
if Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"])).exists():

	# Move it to a backup file
	Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"])).rename(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"] + ".old"))

# Create a logger
LOGGER = logging.getLogger(__name__)
FILE_LOGGER = logging.FileHandler(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"]))
FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s'))
CONSOLE_LOGGER = logging.StreamHandler()
CONSOLE_LOGGER.setFormatter(logging.Formatter("%(levelname)s : %(name)s : %(message)s"))
LOGGER.addHandler(FILE_LOGGER)

# Set the logging level
if args.debug:
	LOGGER.setLevel(logging.DEBUG)
	FILE_LOGGER.setLevel(logging.DEBUG)
	LOGGER.debug("Logging set to DEBUG")
else:
	LOGGER.setLevel(logging.INFO)
	FILE_LOGGER.setLevel(logging.INFO)
	LOGGER.info("Logging set to INFO")
if args.verbose:
	CONSOLE_LOGGER.setLevel(logging.INFO)
	LOGGER.addHandler(CONSOLE_LOGGER)

# Import PyMata libraries
try:
	from pymata_aio.pymata3 import PyMata3
	from pymata_aio.constants import Constants
except ModuleNotFoundError as e:
	LOGGER.error(e)

# paho-mqtt is optional, but recommended for ease of communication
try:
	import paho.mqtt.client as mqtt
	import paho.mqtt.publish as mqtt_pub
	MQTT_ENABLED = True
except ModuleNotFoundError:
	MQTT_ENABLED = False
	LOGGER.warning("Package paho-mqtt is not installed.  MQTT communication will be disabled")

# Import local libraries
import thermostat
from sensors import TempSensor
from hvac import HVAC as hvac

# Override with user settings
try:
	with open(Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["USER_CONFIG"]))) as usersettings:
		settings = json.load(usersettings)
		for setting, value in settings.items():
			if setting in SETTINGS:
				SETTINGS[setting] = value
			else:
				LOGGER.warning("{} is not a valid setting.  Please refer to the default settings for valid settings".format(setting))
except FileNotFoundError:
	LOGGER.warning("No user config file.  Using default")

t_time = time.ctime(time.time())

# Start up the Arduino board
# Specify a com_port so that more than one board can be used
board = PyMata3(com_port="/dev/ttyACM0")

# Setup the thermostat

THERMOSTAT = thermostat.Thermostat(board=board)

# Add the temp sensors to the thermostat
if SETTINGS["SENSORS"]:
	for area, sensor in SETTINGS["SENSORS"].items():
		THERMOSTAT.addSensor(TempSensor(sensor[0], sensor[1]), area)
		# Add it to the board
		board.set_pin_mode(THERMOSTAT.tempSensors[area].controlPin, Constants.ANALOG)
		print(THERMOSTAT.tempSensors)
		#LOGGER.debug("Sensor {} of type {} added on pin {}".format(sensor, THERMOSTAT.tempSensors[sensor].moduleType, THERMOSTAT.tempSensors[sensor].controlPin))
else:
	LOGGER.error("No sensors in config file")
	sys.exit()

# Create a group to get an average temp of the house
if SETTINGS["SENSOR_GROUPS"]:
	for group, sensors in SETTINGS["SENSOR_GROUPS"].items():
		THERMOSTAT.createGroup(group)
		for sensor in sensors:
			if sensor in THERMOSTAT.tempSensors:
				THERMOSTAT.addSensorToGroup(group, THERMOSTAT.tempSensors[sensor])

# Set up the HVAC

HVAC = hvac(board=board)

# Set the pins for heating and cooling control
HVAC.setPins("heat", SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_ON"], SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_SENSE"])
HVAC.setPins("cool", SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_ON"], SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_SENSE"])

# Main loop
while True:
	houseTemp = THERMOSTAT.getTemp("house")
	if round(houseTemp) > SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
	#if round(houseTemp) > IDEALTEMP:
		if HVAC.heat == 1:
			LOGGER.debug(HVAC.heat)
			HVAC.turnHeatOff()
	if round(houseTemp) < SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
	#if round(houseTemp) < IDEALTEMP:
		if HVAC.heat == 0:
			LOGGER.debug(HVAC.heat)
			HVAC.turnHeatOn()
			
	LOGGER.debug(HVAC.heat)
	if args.verbose:
		print("heat is {}".format(HVAC.heat))
		print("house temp is {}".format(houseTemp))
		print("hallway: {}".format(THERMOSTAT.getTemp("hallway")))
		print("masterbed: {}".format(THERMOSTAT.getTemp("masterbed")))
		print("livingroom: {}".format(THERMOSTAT.getTemp("livingroom")))
	time.sleep(30)
	
board.shutdown()
