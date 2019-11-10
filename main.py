#! /usr/bin/env python3

"""
The main script which is run on the controller, specifically designed for a 
raspberry pi.

Requirements:
	pymata-aio => https://github.com/MrYsLab/pymata-aio
	
Optional:
	paho-mqtt => https://github.com/eclipse/paho.mqtt.python
		This module is required if you want to connect to a MQTT broker
"""

__author__ = "builderjer"
__version__ = "0.2.0"

# Builtins
import logging
import json
from pathlib import Path
import argparse
import sys

# Get the default settings
SETTINGS = {}
with open("config/default.json", "r") as settings:
    SETTINGS = json.load(settings)

# Check if there is already a log file
if Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"])).exists():
	# Move it to a backup file
	Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"])).rename(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"] + ".old"))

# Create a logger
LOGGER = logging.getLogger(__name__)
FILE_LOGGER = logging.FileHandler(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["LOG_FILE"]))
FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s'))
LOGGER.addHandler(FILE_LOGGER)

# Set up the parser
parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="Output debuging symbols", action="store_true")
parser.add_argument("-v", "--verbose", help="Verbose symbols", action="store_true")
args = parser.parse_args()

if args.debug:
	LOGGER.setLevel(logging.DEBUG)
	FILE_LOGGER.setLevel(logging.DEBUG)
	LOGGER.debug("Logging set to DEBUG")
else:
	LOGGER.setLevel(logging.INFO)
	FILE_LOGGER.setLevel(logging.INFO)
	LOGGER.info("Logging set to INFO")

# Import PyMata libraries
from pymata_aio.pymata3 import PyMata3
from pymata_aio.constants import Constants

# paho-mqtt is optional, but recommended for ease of communication
try:
	import paho.mqtt.client as mqtt
	MQTT_ENABLED = True
except ModuleNotFoundError:
	MQTT_ENABLED = False
	LOGGER.warning("Package paho-mqtt is not installed.  MQTT communication will be disabled")

# Import local libraries
import thermostat
from sensors import TempSensor

# Override with user settings
try:
	with open(Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["USER_CONFIG"]))) as usersettings:
		settings = json.load(usersettings)
		for setting, value in settings.items():
			SETTINGS[setting] = value
except FileNotFoundError:
	LOGGER.warning("No user config file.  Using default")

# Start up the Arduino board
board = PyMata3()

# Setup the thermostat
THERMOSTAT = thermostat.Thermostat()
	
# Add the temp sensors to the thermostat
THERMOSTAT.addSensor(TempSensor("lm35", 0), "livingroom")
#THERMOSTAT.addSensor(TempSensor("lm35", 1), "livingroom")

# Add the sensors to the board
for sensor in THERMOSTAT.tempSensors:
	board.set_pin_mode(THERMOSTAT.tempSensors[sensor].controlPin, Constants.ANALOG)
	LOGGER.info("Sensor {} of type {} added on pin {}".format(sensor, THERMOSTAT.tempSensors[sensor].moduleType, THERMOSTAT.tempSensors[sensor].controlPin))

# Get the reading from the sensors
# We want to run the reading a few times to get a good average
temps = []
for sensor in THERMOSTAT.tempSensors:
	i = 0
	reading = []
	while i < 100:
		reading.append(board.analog_read(THERMOSTAT.tempSensors[sensor].controlPin))
		board.sleep(.005)
		if args.debug:
			print(reading[i])
		i = i + 1
	ave = sum(reading) / len(reading)
	LOGGER.debug("Average: {}".format(ave))
	THERMOSTAT.tempSensors[sensor].tempC = (THERMOSTAT.tempSensors[sensor].moduleType, ave)
	temps.append(THERMOSTAT.tempSensors[sensor].tempC)
	
mainTemp = round(THERMOSTAT.getTemp("livingroom"), 1)

LOGGER.info("Temp in {} is {}\xB0".format("livingroom", mainTemp))
print(mainTemp)
board.shutdown()
