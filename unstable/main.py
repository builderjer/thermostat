#! /usr/bin/env python3

"""
The main script which is run on the controller, specifically designed for a
raspberry pi.

Requirements:
	pymata-aio => https://github.com/MrYsLab/pymata-aio

	paho-mqtt => https://github.com/eclipse/paho.mqtt.python
		This module is required if you want to connect to a MQTT broker

The default config file is hard coded here.  Changing this is not recommended.
To override, create a json encoded file at <your home directory>/.config/thermostat/config.json
Any settings you find in the default config file can be overridden there.
"""

#__author__ = "builderjer"
#__version__ = "0.3.0"

## Builtins
#import logging
#import json
#from pathlib import Path
#import argparse
#import sys

#from signal import signal as sig

## Set up the parser
#parser = argparse.ArgumentParser()
#parser.add_argument("--debug", help="Output debuging symbols", action="store_true")
#parser.add_argument("-v", "--verbose", help="Verbose symbols", action="store_true")
#parser.add_argument("-c", action="store", dest="cl_config", help="/Path/to/custom/config.json")
#args = parser.parse_args()

# Define some global variables

## The default configuration file - Must be valid json.
## All arguments can be overridden in either "/home/<user>/.config/thermostat/config.json"
## or by the command line argument "-c /path/to/custom/config.json"
#CONFIG_FILE = Path(sys.path[0]).joinpath("config/default.json")

## Load the default file so that all settings are accounted for.
#SETTINGS = {}
#with open(CONFIG_FILE, "r") as settings:
    #SETTINGS = json.load(settings)

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
	CONSOLE_LOGGER.setLevel(logging.WARNING)
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

# Override with user settings
try:
	with open(Path(Path.home().joinpath(SETTINGS["USER_DIR"]).joinpath(SETTINGS["USER_CONFIG"]))) as usersettings:
		settings = json.load(usersettings)
		for setting, value in settings.items():
			SETTINGS[setting] = value
except FileNotFoundError:
	LOGGER.warning("No user config file.  Using default")

# Start up the Arduino board
# Specify a com_port so that more than one board can be used
board = PyMata3(com_port="/dev/ttyACM0")

# Setup the thermostat
THERMOSTAT = thermostat.Thermostat(board=board)

# Add the temp sensors to the thermostat
THERMOSTAT.addSensor(TempSensor("lm35", 3), "hallway")
THERMOSTAT.addSensor(TempSensor("lm35", 4), "masterbed")
THERMOSTAT.addSensor(TempSensor("lm35", 5), "livingroom")

# Add the sensors to the board
for sensor in THERMOSTAT.tempSensors:
	board.set_pin_mode(THERMOSTAT.tempSensors[sensor].controlPin, Constants.ANALOG)
	LOGGER.info("Sensor {} of type {} added on pin {}".format(sensor, THERMOSTAT.tempSensors[sensor].moduleType, THERMOSTAT.tempSensors[sensor].controlPin))

# Create a group to get an average temp of the house
THERMOSTAT.createGroup("house")

# Add the thermostats to the group
THERMOSTAT.addSensorToGroup("house", THERMOSTAT.tempSensors["HALLWAY"])
THERMOSTAT.addSensorToGroup("house", THERMOSTAT.tempSensors["MASTERBED"])
THERMOSTAT.addSensorToGroup("house", THERMOSTAT.tempSensors["LIVINGROOM"])

def publishTemp():
	baseTopic = "ziggy/house/climate/temp/"
	for location, sensor in THERMOSTAT.tempSensors.items():
		# Get the value from the sensor
		temp = str(round(THERMOSTAT.getTemp(location)))
		topic = baseTopic + location.lower()
		mqtt_pub.single(topic, temp, hostname="ziggyhome.mooo.com", port=8884, auth={"username": "ziggy", "password": "ziggy"}, qos=1, retain=True)
	LOGGER.debug("Published main temp of {}".format(mainTemp))
	print("Published main temp of {}".format(mainTemp))

mainTemp = (THERMOSTAT.getTemp("house"))

LOGGER.info("Temp in {} is {}\xB0".format("house", mainTemp))
print("mainTemp:  " + str(mainTemp))
for sensor in THERMOSTAT.tempSensors:
  print(sensor + ":  " + str(THERMOSTAT.getTemp(sensor)))

if MQTT_ENABLED:
	try:
		publishTemp()
	except Exception as e:
		print(e)
		LOGGER.error("Something went wrong with publish.  {}".format(e))

# Set up the signal handler for shutdown
def shutdown(sig, frame):
	if board:
		board.shutdown()
	sys.exit()

sig(signal.SIGTERM, shutdown)
sig(signal.SIGINT, shutdown)

board.shutdown()
