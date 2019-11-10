#! /usr/bin/env python3

"""
This is the main script for the thermostat.  It relies on a few libraries namly
pymata_aio.  
You can find this on Github at https://github.com/MrYsLab/pymata-aio
"""

__author__ = "builderjer"
__version__ = "0.1.2"

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
thermostat = thermostat.Thermostat()

# Add the sensors to the thermostat
#thermostat.addSensor(TempSensor("lm35", 0, location="kitchen"))
#thermostat.addSensor(TempSensor("lm35", 1, location="livingroom"))
thermostat.addSensor(TempSensor("lm35", 0), "kitchen")
thermostat.addSensor(TempSensor("lm35", 1), "livingroom")

# Add the sensors to the board
for sensor in thermostat.tempSensors:
	print(sensor)
	board.set_pin_mode(thermostat.tempSensors[sensor].controlPin, Constants.ANALOG)
	if args.debug:
		print("sensor {} of type {} on pin {} added".format(sensor.location, sensor.moduleType, sensor.controlPin))

# Get the reading from the sensors
# We want to run the reading a few times to get a good average
temps = []
for sensor in thermostat.tempSensors:
	i = 0
	reading = []
	while i < 100:
		reading.append(board.analog_read(thermostat.tempSensors[sensor].controlPin))
		board.sleep(.005)
		#if args.debug:
			#print(reading[i])
		i = i + 1
	#if args.debug:
		#print("{}  :  {}".format(sum(reading), len(reading)))
	ave = sum(reading) / len(reading)
	#if args.debug:
		#print("ave:  {}".format(ave))
	thermostat.tempSensors[sensor].value = ave
	#if args.debug:
		#print("average reading: {}  sensor.value:  {}".format(ave, sensor.value))
	temps.append(thermostat.tempSensors[sensor].value)
	#if args.debug:
		#print(temps)

aveReading = sum(temps) / len(temps)
#thermostat.currentTemp = aveReading
if args.debug:
	print("aveReading: {}".format(aveReading))
thermostat.houseTemp = aveReading
#if args.debug or args.verbose:
	#print("current temp is {}{}".format(thermostat.currentTemp, thermostat.outputFormat))
print("Current house temp is {}\xb0F".format(round(thermostat.houseTemp, 1)))

board.shutdown()


