#! /usr/bin/env python3

"""
The main script which is run on the controller, specifically designed for a
raspberry pi.

Requirements:
	pymata-aio => https://github.com/MrYsLab/pymata-aio

The default config file is hard coded here.  Changing this is not recommended.
To override, create a json encoded file at <your home directory>/.config/thermostat/config.json
Any settings you find in the default config file can be overridden there.
"""

__author__ = "builderjer"
__version__ = "0.3.0"

# Builtins
import logging
import json
from pathlib import Path
import argparse
import sys
import os
import time
import signal

# Set up the parser
parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="Output debuging symbols", action="store_true")
parser.add_argument("-v", "--verbose", help="Verbose symbols", action="store_true")
args = parser.parse_args()

# Define some global variables
CONFIG_FILE = Path(sys.path[0]).joinpath("config/default.json")

# Get the default settings
SETTINGS = {}
with open(CONFIG_FILE, "r") as settings:
	SETTINGS = json.load(settings)

# Check if there is already a log file
if Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"])).exists():

	# Move it to a backup file
	Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"])).rename(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"] + ".old"))
else:
	os.makedirs(Path(Path.home().joinpath(SETTINGS["USER_DIR"])), exist_ok=True)

# Create a logger
LOGGER = logging.getLogger(__name__)
FILE_LOGGER = logging.FileHandler(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"]))
FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(lineno)d : %(message)s'))
CONSOLE_LOGGER = logging.StreamHandler()
CONSOLE_LOGGER.setFormatter(logging.Formatter("%(levelname)s : %(name)s : %(lineno)d : %(message)s"))
LOGGER.addHandler(FILE_LOGGER)

# FIXME:  Logging is not quite right

# Set the logging level
if args.debug:
	FILE_LOGGER.setLevel(logging.DEBUG)
	LOGGER.setLevel(logging.DEBUG)

if args.verbose:
	CONSOLE_LOGGER.setLevel(logging.DEBUG)
	LOGGER.addHandler(CONSOLE_LOGGER)
	LOGGER.setLevel(logging.DEBUG)

else:
	FILE_LOGGER.setLevel(logging.INFO)
	LOGGER.setLevel(logging.INFO)

# Import PyMata libraries
try:
	from pymata_aio.pymata3 import PyMata3
	from pymata_aio.constants import Constants
except ModuleNotFoundError as e:
	LOGGER.error(e)

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

# Import local libraries
import thermostat
from sensors import TempSensor
from hvac import HVAC as hvac

thermostat_time = time.ctime(time.time())

# Start up the Arduino board
# Specify a com_port so that more than one board can be used
board = PyMata3(com_port="/dev/ttyACM0")

# Setup the thermostat

#THERMOSTAT = thermostat.Thermostat(board=board)
THERMOSTAT = thermostat.Thermostat()

# Add the temp sensors to the thermostat
if SETTINGS["SENSORS"]:
	for area, sensor in SETTINGS["SENSORS"].items():
		THERMOSTAT.addSensor(TempSensor(sensor[0], sensor[1]), area)
		# Add it to the board
		board.set_pin_mode(THERMOSTAT.tempSensors[area].controlPin, Constants.ANALOG)
		LOGGER.debug("Sensor {} of type {} added on pin {}".format(sensor, THERMOSTAT.tempSensors[area].moduleType, THERMOSTAT.tempSensors[area].controlPin))
else:
	LOGGER.error("No sensors in config file")
	sys.exit()

# Create a group to get an average temp of the house
if SETTINGS["SENSOR_GROUPS"]:
	for group, sensors in SETTINGS["SENSOR_GROUPS"].items():
		THERMOSTAT.createGroup(group)
		# Add the sensors to the group
		for sensor in sensors:
			if sensor in THERMOSTAT.tempSensors:
				THERMOSTAT.addSensorToGroup(group, THERMOSTAT.tempSensors[sensor])
				LOGGER.debug("Sensor {} added to group {}".format(sensor, group))

# Set up the HVAC
HVAC = hvac()

# Set the pins for heating and cooling control
HVAC.heatControl = (SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_ON"], SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_SENSE"])
HVAC.coolControl = (SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_ON"], SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_SENSE"])

# Add them to the board
board.set_pin_mode(HVAC.heatControl[0], Constants.OUTPUT)
board.set_pin_mode(HVAC.heatControl[1], Constants.OUTPUT)

board.set_pin_mode(HVAC.coolControl[0], Constants.OUTPUT)
board.set_pin_mode(HVAC.coolControl[1], Constants.OUTPUT)

# Set up the signal handler for shutdown
def shutdown(sig, frame):
	if board:
		board.shutdown()
	sys.exit()

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

def turnOnOff(heatCool, onOff):
	"""
	heatCool => Either the heater or A/C
		Valid entrys -- "heat"  "cool"
	onOff => Turn the HVAC on or off
		Valid entrys -- "on"  "off"
	"""
	if heatCool.upper() == "HEAT":
		hc = HVAC.heatControl
	elif heatCool.upper() == "COOL":
		hc = HVAC.coolControl
	else:
		raise AttributeError("Only 'heat' and 'cool' are valid attributes")

	if onOff.upper() == "ON":
		board.digital_write(hc[0], 1)
		board.sleep(0.1)
		board.digital_write(hc[0], 0)
		board.sleep(0.1)
	elif onOff.upper() == "OFF":
		board.digital_write(hc[1], 1)
		board.sleep(0.1)
		board.digital_write(hc[1], 0)
		board.sleep(0.1)
	else:
		raise AttributeError("Only 'on' or 'off' are valid attributes")

	HVAC.setHeatState()

def setOutput(temp):
	if SETTINGS["OUTPUT_FORMAT"] == "F":
		temp = (temp * 1.8) + 32
	LOGGER.debug(temp)
	return temp

def readSensors():
	for sensor in THERMOSTAT.tempSensors:
		THERMOSTAT.tempSensors[sensor].tempC = board.analog_read(THERMOSTAT.tempSensors[sensor].controlPin)
		LOGGER.debug(THERMOSTAT.tempSensors[sensor].tempC)

HVAC.state = "OFF"
THERMOSTAT.state = "HEAT"

while True:
	while THERMOSTAT.state == "HEAT":
		while HVAC.state == "OFF":
			# Get the readings from the sensors
			for sensor in THERMOSTAT.tempSensors:
				THERMOSTAT.tempSensors[sensor].tempC = board.analog_read(THERMOSTAT.tempSensors[sensor].controlPin)
			# Get the average temp of the house
			houseTemp = setOutput(THERMOSTAT.getTemp("HOUSE"))
			# Use round to keep the temp +- 0.5 deg
			if round(houseTemp) < SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
				# It's cold, turn the heater on
				# Check and make sure the HVAC is in "OFF" state
				if HVAC.setHeatState():
				#if HVAC.turnHeatOn():
					try:
						turnOnOff("heat", "on")
					except AttributeError:
						# Put log entry here
						pass
					except Exception as e:
						LOGGER.error("Could not change HVAC state.  {}".format(e))
			board.sleep(15)
		while HVAC.state == "HEATING":
			# The heater is on, check to see if the temp is warm enough
			for sensor in THERMOSTAT.tempSensors:
				THERMOSTAT.tempSensors[sensor].tempC = board.analog_read(THERMOSTAT.tempSensors[sensor].controlPin)
			# Get the average temp of the house
			houseTemp = setOutput(THERMOSTAT.getTemp("HOUSE"))
			# Use round to keep the temp +- 0.5 deg
			if round(houseTemp) > SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
				# Warm enough, turn the heater off
				if HVAC.setHeatState():
				#if HVAC.turnHeatOff:
					try:
						turnOnOff("heat", "off")
						#HVAC.setHeatState()
					except AttributeError:
						# Put log entry here
						pass
					except Exception as e:
						LOGGER.error("Could not change HVAC state.  {}".format(e))
			board.sleep(15)

	while THERMOSTAT.state == "COOL":
		# Enable the cool sensor pin callback
		board.set_pin_mode(HVAC.coolControl[2], Constants.INPUT, HVAC.setCoolState)
		# Disable the heat sensor callback
		board.set_pin_mode(HVAC.heatControl[2], Constants.INPUT)
		while HVAC.state == "OFF":
			pass
		while HVAC.state == "COOLING":
			pass


