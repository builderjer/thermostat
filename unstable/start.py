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
from signal import signal as sig

# Create a Logger
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

# Global variables
CONFIG_FILE = Path(sys.path[0]).joinpath("config/default.json")
LOG_FILE = Path("/var/tmp/thermostat/thermostat.log")
SETTINGS = {}
ERROR = None
# Set up the parser
parser = argparse.ArgumentParser()
parser.add_argument("-b", action="store_true", help="Save a backup of the previous logfile")
parser.add_argument("-v", action="count", help="Increase verbosity output")
parser.add_argument("--config", action="store", help="/path/to/custom/config.json", default=CONFIG_FILE)
parser.add_argument("--debug", action="store_true", help="Output debuging symbols")
parser.add_argument("--log", action="store", help="/path/to/logfile/location.log", default=LOG_FILE)
args = parser.parse_args()

# Parse the arguments if there are any
# Run the parser in sections so that items can be created when needed

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

# Configuration File - CONFIG_FILE

# All configuration files must be in valid json format
# Load order:  Default => User => Command Line

# Take care of all loading and subsitutions here
# Default Config
try:
	with open(CONFIG_FILE, "r") as config:
		SETTINGS = json.load(config)
except ValueError as e:
	LOGGER.error("The main config file {} has an error.  Check and retry.  {}".format(str(CONFIG_FILE), e))
	sys.exit()

# User config - Location stored in Default Config file
defaultUserConfig = Path(Path.home(), SETTINGS["USER_DIR"], SETTINGS["USER_CONFIG"])
if defaultUserConfig.exists():
	try:
		with open(defaultUserConfig, "r") as uConfig:
			defaultUserConfig = json.load(uConfig)
		for setting, value in defaultUserConfig.items():
			SETTINGS[setting] = value
	except ValueError as e:
		LOGGER.warning("{} is not a valid json file.  Configuration will be ignored.  {}".format(str(defaultUserConfig), e))
else:
	# Create a default file as a starting point for the user config
	try:
		Path.mkdir(defaultUserConfig.parent)
		s = {"MIN_VERSION": SETTINGS["MIN_VERSION"]}
		with open(defaultUserConfig, "w") as uConfig:
			json.dump(s, uConfig, indent=4)
	except Exception as e:
		LOGGER.warning("Could not create default user config file.  {}".format(e))

# Command Line config - Only if the option exists and is in valid json format
if args.config and Path(args.config).exists():
	try:
		with open(Path(args.config), "r") as config:
			clineConfig = json.load(config)
		for setting, value in clineConfig.items():
			SETTINGS[setting] = value
	except ValueError:
		LOGGER.warning("{} is not a valid json file.  Falling back to default".format(args.config))
else:
	LOGGER.warning("Could not read {}.  Check path and formatting".format(args.config))

# Check for required version of config file
if SETTINGS["MIN_VERSION"] > __version__:
	LOGGER.error("Update your configuration file to version {} to run this script".format(__version__))
	sys.exit()
LOGGER.info("Configuration loaded")
