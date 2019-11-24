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

# Set up the signal handler for shutdown
def shutdown(sig, frame):
	if board:
		board.shutdown()
	sys.exit()

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

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
FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s'))
CONSOLE_LOGGER = logging.StreamHandler()
CONSOLE_LOGGER.setFormatter(logging.Formatter("%(levelname)s : %(name)s : %(message)s"))
LOGGER.addHandler(FILE_LOGGER)

# FIXME:  Logging is not quite right

# Set the logging level
if args.debug:
	FILE_LOGGER.setLevel(logging.DEBUG)
else:
	FILE_LOGGER.setLevel(logging.INFO)

if args.verbose:
	CONSOLE_LOGGER.setLevel(logging.DEBUG)
	LOGGER.addHandler(CONSOLE_LOGGER)
	
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

# A few required functions
def changeBoardState(pin):
	"""
	Sends a signal to the board to momentarily turn on and off a pin.
	Used for latching relays
	"""
	try:
		board.digital_write(pin, 1)
		board.sleep(.1)
		board.digital_write(pin, 0)
		board.sleep(.1)
	except Exception as e:
		LOGGER.warning("Could not turn on pin {}".format(pin))
	LOGGER.debug("changeBoardState pin {}".format(pin))
		
def setOutput(temp):
	if SETTINGS["OUTPUT_FORMAT"] == "F":
		temp = (temp * 1.8) + 32
	return temp
		
# Turn everything off
if HVAC.turnHeatOff():
	changeBoardState(HVAC.heatControl[1])
if HVAC.turnCoolOff():
	changeBoardState(HVAC.coolControl[1])
	
# Add the sensor pins to the board
board.set_pin_mode(HVAC.heatControl[2], Constants.INPUT, HVAC.setState)
board.set_pin_mode(HVAC.coolControl[2], Constants.INPUT, HVAC.setState)

# TODO:  This is a temp solution to turn the Thermostat into heat mode -- It's winter here
THERMOSTAT.state = "HEAT"

# Main loop
while True:
	
	while THERMOSTAT.state == "HEAT":
		while HVAC.state == "OFF":
			# While it is off, keep checking the temp to make appropriate adjustments		
			houseTemp = setOutput(THERMOSTAT.getTemp("house"))
			# I use round to keep the temp +- 0.5 deg of desired temp
			if round(houseTemp) < SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
				# Its cold, turn the heater on
				if HVAC.turnHeatOn():
					changeBoardState(HVAC.heatControl[0])
					LOGGER.info("Turned heat on")
				else:
					LOGGER.warning("Could not turn heat on")
			if args.debug:
				for area, sensor in THERMOSTAT.tempSensors.items():
					t = sensor.tempC
					LOGGER.debug("Temp in {}:  {}".format(area, ((t * 1.8) + 32)))
			# Only poll every so often.  Change this if you would like
			board.sleep(15)
	
		while HVAC.state == "HEATING":
			# Still have to keep checking the temp so it knows when to turn off.
			houseTemp = setOutput(THERMOSTAT.getTemp("house"))
			# Keeps the heater on until the house temp reaches 1 deg above default temp
			if round(houseTemp) >= SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"] + 1:
				if HVAC.turnHeatOff():
					changeBoardState(HVAC.heatControl[1])
					LOGGER.info("Turned heat off")
				else:
					LOGGER.warning("Could not turn heat off")
			if args.debug:
				for area, sensor in THERMOSTAT.tempSensors.items():
					t = sensor.tempC
					LOGGER.debug("Temp in {}:  {}".format(area, ((t * 1.8) + 32)))
			# Only poll every so often.  Change this if you would like
			board.sleep(15)
		
		# BUG:  Hack to make sure the HVAC stays out of COOLING state while Thermostat is in HEAT mode
		if HVAC.state == "COOLING":
			if HVAC.turnCoolOff():
				changeBoardState(HVAC.coolControl[1])

			#HVAC.turnHeatOff()
		#for area, sensor in THERMOSTAT.tempSensors.items():
			#t = sensor.tempC
			#print("Temp in {}:  {}".format(area, ((t * 1.8) + 32)))
		#print(houseTemp)
		#board.sleep(15)

	#if HVAC.state == "COOLING":
		#continue
				
	#if round(houseTemp) > SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
	##if round(houseTemp) > IDEALTEMP:
		#if HVAC.heat == 1:
			#LOGGER.debug(HVAC.heat)
			#HVAC.turnHeatOff()
	#if round(houseTemp) < SETTINGS["TEMP_SETTINGS"]["DEFAULT_TEMP"]:
	##if round(houseTemp) < IDEALTEMP:
		#if HVAC.heat == 0:
			#LOGGER.debug(HVAC.heat)
			#HVAC.turnHeatOn()
			
	#LOGGER.debug(HVAC.heat)
	#if args.verbose:
		#print("heat is {}".format(HVAC.heat))
		#print("house temp is {}".format(houseTemp))
		#print("hallway: {}".format(THERMOSTAT.getTemp("hallway")))
		#print("masterbed: {}".format(THERMOSTAT.getTemp("masterbed")))
		#print("livingroom: {}".format(THERMOSTAT.getTemp("livingroom")))
	#time.sleep(30)
	
board.shutdown()
