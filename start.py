#! /usr/bin/env python3

"""
This is the script that is called to setup everything needed to start the loop
that is held in the 'main.py' script.
"""

__author__ = "builderjer"
__version__ = "0.5.0"

# Import builtins
import logging
import json
import argparse
import sys
import os
from pathlib import Path
import signal
import time

# Create a Logger
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

# Global variables
CONFIG_FILE = Path(sys.path[0]).joinpath("config/default.json")
LOG_FILE = Path("/var/tmp/thermostat/thermostat.log")
DEFAULT_PORT = "/dev/ttyACM0"
SETTINGS = {}
ERROR = None

# Set up the parser
parser = argparse.ArgumentParser()
parser.add_argument("-b", action="store_true", help="Save a backup of the previous logfile")
parser.add_argument("-p", action="store", help="Specify a single port to use on a single PyMata board", default=DEFAULT_PORT)
parser.add_argument("-v", action="count", help="Increase verbosity output")
parser.add_argument("--config", action="store", help="/path/to/custom/config.json", default=CONFIG_FILE)
parser.add_argument("--debug", action="store_true", help="Output debuging symbols")
parser.add_argument("--log", action="store", help="/path/to/logfile/location.log", default=LOG_FILE)
#parser.add_argument("--ports", action="store", help="A comma seperated list of dev ports to attach boards too", default=None)
args = parser.parse_args()

# Parse the arguments if there are any
# Run the parser in sections so that items can be created when needed

# TODO:  Possibly make the logger config from file
# Logger output
if Path(args.log).exists():
	LOGGER.warning("Log file exists")
	if args.b:
		LOGGER.warning("Trying to create backup")
		try:
			Path(args.log).rename(Path(args.log).with_suffix(".old.log"))
		except PermissionError as error:
			ERROR = error
else:
	LOGGER.warning("Log file does not exist")
	LOGGER.warning("Trying to create log file at {}".format(args.log))
	try:
		Path(args.log).parent.mkdir(parents=True, exist_ok=True)
	except PermissionError as error:
		ERROR = error
try:
	LOG_FILE = Path(args.log)
	FILE_LOGGER = logging.FileHandler(LOG_FILE, "w")
	if args.debug:
		FILE_LOGGER.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(lineno)d : %(message)s'))
		FILE_LOGGER.setLevel(logging.DEBUG)
	else:
		FILE_LOGGER.setFormatter(logging.Formatter("%(levelname)s : %(message)s"))
		FILE_LOGGER.setLevel(logging.INFO)
	LOGGER.addHandler(FILE_LOGGER)
	LOGGER.info("Log file created")
except PermissionError as error:
	ERROR = error

if ERROR:
	LOGGER.warning("You do not have permission to write to this file {}".format(args.log))
	LOGGER.warning("Log file not created.  {}".format(ERROR))

# Verbosity Output:  -v => INFO  -vv => DEBUG -vvv more-verbose-DEBUG
if args.v:
	CONSOLE_LOGGER = logging.StreamHandler()
	if args.v == 1:
		CONSOLE_LOGGER.setLevel(logging.INFO)
		CONSOLE_LOGGER.setFormatter(logging.Formatter("%(message)s"))
	if args.v == 2:
		CONSOLE_LOGGER.setLevel(logging.DEBUG)
		CONSOLE_LOGGER.setFormatter(logging.Formatter("%(levelname)s : %(name)s : %(message)s"))
	if args.v >= 3:
		CONSOLE_LOGGER.setFormatter(logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(lineno)d : %(message)s"))
		CONSOLE_LOGGER.setLevel(logging.DEBUG)

	LOGGER.addHandler(CONSOLE_LOGGER)
LOGGER.info("Log file configured")

# Configuration File - CONFIG_FILE

# All configuration files must be in valid json format
# Load order:  Default => User => Command Line

# Take care of all loading and subsitutions here
# Default Config
try:
	with open(CONFIG_FILE, "r") as config:
		SETTINGS = json.load(config)
		LOGGER.debug("Default config:  {}\n{}".format(CONFIG_FILE, SETTINGS))
except ValueError as e:
	LOGGER.error("The main config file {} has an error.  Check and retry.  {}".format(str(CONFIG_FILE), e))
	sys.exit()

# Command Line config - Only if the option exists and is in valid json format
if args.config and Path(args.config).exists():
	try:
		with open(Path(args.config), "r") as config:
			clineConfig = json.load(config)
		for setting, value in clineConfig.items():
			SETTINGS[setting] = value
		LOGGER.debug("Command Line config file loaded from {}\n{}".format(args.config, SETTINGS))
	except ValueError:
		LOGGER.warning("{} is not a valid json file.  Falling back to default".format(args.config))
else:
	LOGGER.warning("Could not load {}.  Check path and formatting".format(args.config))

# User config - Location stored in Default Config file
defaultUserConfig = Path(Path.home(), SETTINGS["USER_DIR"], SETTINGS["USER_CONFIG"])

if defaultUserConfig.exists():
	try:
		with open(defaultUserConfig, "r") as uConfig:
			defaultUserConfig = json.load(uConfig)
		for setting, value in defaultUserConfig.items():
			SETTINGS[setting] = value
		LOGGER.debug("User config:  {}\n{}".format(defaultUserConfig, SETTINGS))
	except ValueError as e:
		LOGGER.warning("{} is not a valid json file.  Configuration will be ignored.  {}".format(str(defaultUserConfig), e))
else:
	# Create a default file as a starting point for the user config
	try:
		Path.mkdir(defaultUserConfig.parent)
		s = {"MIN_VERSION": SETTINGS["MIN_VERSION"]}
		with open(defaultUserConfig, "w") as uConfig:
			json.dump(s, uConfig, indent=4)
		LOGGER.debug("No user config found.  Creating default at {}".format(defaultUserConfig))
	except Exception as e:
		LOGGER.warning("Could not create default user config file.  {}".format(e))

# Check for required version of config file
if SETTINGS["MIN_VERSION"] >= __version__:
	LOGGER.error("Update your configuration file to version {} to run this script".format(__version__))
	sys.exit()
LOGGER.info("Configuration loaded")

# Configuration and logging loaded.  Time to continue

# If a port on the command line is specified, set it as the DEFAULT_PORT
if (args.p):
	DEFAULT_PORT = args.p

import hvac
import sensors

HVAC = hvac.HVAC(DEFAULT_PORT)
HVAC.heater = hvac.Heater(HVAC.board, [SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["HEAT_ON"]])
HVAC.ac = hvac.AirConditioner(HVAC.board, [SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["COOL_ON"]])
HVAC.vent = hvac.Vent(HVAC.board, [SETTINGS["HVAC"]["CONTROL_PINS"]["VENT_OFF"], SETTINGS["HVAC"]["CONTROL_PINS"]["VENT_ON"]])
HVAC.thermostat = hvac.Thermostat(HVAC.board, tempSettings=SETTINGS["TEMP_SETTINGS"])

# Add the sensors to the Thermostat
if SETTINGS["SENSORS"]:
	for area, sensor in SETTINGS["SENSORS"].items():
		LOGGER.debug(SETTINGS["SENSORS"].items())
		HVAC.thermostat.addSensor(sensors.TempSensor(area, sensor[0], sensor[1]))
else:
	LOGGER.error("Must have sensors configured to work.  Exiting")
	sys.exit()

if SETTINGS["SENSOR_GROUPS"]:
	for groupName, sensorNames in SETTINGS["SENSOR_GROUPS"].items():
		LOGGER.debug("groupname: {}  sensorNames: {}".format(groupName, sensorNames))
		HVAC.thermostat.createSensorGroup(groupName)
		for sensor in sensorNames:
			for s in HVAC.thermostat.tempSensors:
				if sensor == s.name:
					HVAC.thermostat.addSensorToGroup(s, groupName)

# Set up MQTT information if avaliable
if SETTINGS["MQTT"]:
	HVAC.thermostat.mqtt = SETTINGS["MQTT"]

# Set up the presence detector
OCCUPIED = sensors.PresenceDetector()
if SETTINGS["OCCUPANCY"]:
	OCCUPIED.addresses = SETTINGS["OCCUPANCY"]
else:
	OCCUPIED.addresses = []

def stop():
	HVAC.board.shutdown()

# Set up the signal handler for Ctrl-C shutdown
def shutdown(sig, frame):
	if HVAC.board:
		stop()
	sys.exit()
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

# Make sure everything is turned off before starting main loop
def turnAllOff():
	HVAC.changeHeatState("OFF")
	HVAC.changeACState("OFF")
	#HVAC.changeVentState("OFF")


def start():
	OCCUPIED.homeList = OCCUPIED.addresses
	HVAC.thermostat.occupied = OCCUPIED.homeList
	HVAC.thermostat.updateSensors()
	HVAC.thermostat.desiredTemp = None
	# Use a round temperature to keep within +- 1 deg
	roundTemp = round(HVAC.thermostat.getTemp("HOUSE"))
	LOGGER.debug("Round temp of house {}  Desired temp of house {}".format(roundTemp, HVAC.thermostat.desiredTemp))

	if roundTemp < HVAC.thermostat.desiredTemp:
		LOGGER.debug("round less than desired")

		# Winter time, turn on the heat
		if HVAC.thermostat.timeOfYear == "WINTER":
			LOGGER.debug("WINTER turn heat on")
			HVAC.changeHeatState("ON")
			# To be implemented soon
			# Let the burner heat up for 5 seconds before turning on the blower
			#time.sleep(5)
			#HVAC.changeVentState("ON")

		# Summer time, turn off the AC
		elif HVAC.thermostat.timeOfYear == "SUMMER":
			LOGGER.debug("SUMMER turn AC off")
			HVAC.changeACState("OFF")
			# To be implemented soon
			# Keep the blower on for 5 seconds after turning off AC
			#time.sleep(5)
			#HVAC.changeVentState("OFF")

		# Its not summer or winter, so make sure everything is turned off
		else:
			turnAllOff()

	if roundTemp > HVAC.thermostat.desiredTemp:
		LOGGER.debug("round greater than desired")
		if HVAC.thermostat.timeOfYear == "WINTER":
			LOGGER.debug("WINTER turn heat off")
			HVAC.changeHeatState("OFF")
			# To be implemented soon
			#time.sleep(5)
			#HVAC.changeVentState("OFF")
		elif HVAC.thermostat.timeOfYear == "SUMMER":
			LOGGER.debug("SUMMER turn AC on")
			HVAC.changeACState("ON")
			# To be implemented soon
			#time.sleep(5)
			#HVAC.changeVentState("OFF")
		else:
			turnAllOff()

	# Publish the temperatures to the MQTT broker
	HVAC.thermostat.publish()

	# Give the board a rest
	HVAC.thermostat.board.sleep(1)
	LOGGER.debug("End of start loop")

if __name__ == "__main__":
	turnAllOff()
	while True:
		start()
	stop()


