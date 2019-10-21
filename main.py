#! /usr/bin/env python3

"""
This is the main script for the thermostat.  It relies on a few libraries namly
pymata_aio.  
You can find this on Github at https://github.com/MrYsLab/pymata-aio
"""

# Do some imports

# Built in libraries
import argparse
import sys

# Import the PyMata libraries
from pymata_aio.pymata3 import PyMata3
from pymata_aio.constants import Constants

# Import some local libraries
import thermostat
from sensors import TempSensor

# Set up the parser
parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="Output debuging symbols", action="store_true")
parser.add_argument("-v", "--verbose", help="Verbose symbols", action="store_true")
args = parser.parse_args()

if args.debug:
	print("Debuging is turned on")

# Start up the Arduino board
board = PyMata3()

# Setup the thermostat
thermostat = thermostat.Thermostat("F")

# Add the sensors to the thermostat
thermostat.addSensor(TempSensor("lm35", 0, location="kitchen"))
thermostat.addSensor(TempSensor("lm35", 1, location="livingroom"))

if args.debug:
	for sensor in thermostat.tempSensors:
		print("sensor {} of type {} on pin {} added".format(sensor.location, sensor.moduleType, sensor.controlPin))

# Add the sensors to the board
for sensor in thermostat.tempSensors:
	board.set_pin_mode(sensor.controlPin, Constants.ANALOG)
	#

# Get the reading from the sensors
# We want to run the reading a few times to get a good average
temps = []
for sensor in thermostat.tempSensors:
	i = 0
	reading = []
	while i < 10:
		reading.append(board.analog_read(sensor.controlPin))
		board.sleep(.005)
		if args.debug:
			print(reading[i])
		i = i + 1
	ave = sum(reading) / len(reading)
	sensor.value = ave
	if args.debug:
		print("average reading: {}".format(ave))
	temps.append(sensor.value)

aveReading = sum(temps) / len(temps)
thermostat.currentTemp = aveReading

if args.debug or args.verbose:
	print("current temp is {}{}".format(thermostat.currentTemp, thermostat.outputFormat))
	
board.shutdown()


