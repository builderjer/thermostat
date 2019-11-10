#! /usr/bin/env python3

from pathlib import Path
import logging

import time
t = time.ctime(time.time())

LOGGER = logging.getLogger(__name__)
FILE_LOGGER = logging.FileHandler(Path.home().joinpath("PhotoSensor_daily.log"))
format_str = '{} - %(levelname)-8s - %(message)s'.format(t)
date_format = '%Y-%m-%d %H:%M:%S'
FILE_LOGGER.setFormatter(logging.Formatter(format_str, date_format))
LOGGER.addHandler(FILE_LOGGER)
LOGGER.setLevel(logging.DEBUG)

# Import PyMata libraries
from pymata_aio.pymata3 import PyMata3
from pymata_aio.constants import Constants

from sensors import PhotoSensor

# Start up the Arduino board
board = PyMata3()

# Add the sensor
ps = PhotoSensor(0)
board.set_pin_mode(ps.controlPin, Constants.ANALOG)

i = 0
reading = []
while i < 25:
	r = board.analog_read(ps.controlPin)
	reading.append(r)
	board.sleep(1)
	i = i + 1
	print(r)
ave = sum(reading) / len(reading)
print(sum(reading), len(reading), sum(reading) / len(reading))

LOGGER.info(ave)

board.shutdown()
