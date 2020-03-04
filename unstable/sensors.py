"""
This script is to hold a variety of sensors used in my personal smarthome.
https://github.com/builderjer/ZiggyAI
"""

__author__ = "builderjer"
__version__ = "0.1.2"

import logging

LOGGER = logging.getLogger("__main__.sensors.py")

class Sensor:
	"""
	Base class for all sensors in this file.
	"""
	def __init__(self, name):
		"""
		name => Must be initiated with a name.
		"""
		self._name = name.upper()

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, name):
		self._name = name.upper()

class TempSensor(Sensor):
#class TempSensor:
	"""
	A class to create a temperature sensor for use with an Arduino or other microcontroller
	"""
	def __init__(self, name, moduleType, controlPin):
		"""
		<string> moduleType => type of sensor (LM35, etc...)
			It is required because each sensor uses a different forumla to determine the temp

		<int> controlPin => The pin on the microcontroller the sensor is connected to.
		"""
		self.LOGGER = logging.getLogger("__main__.sensors.TempSensor")
		self.LOGGER.debug("Created TempSensor {} with moduleType {} and controlPin {}".format(name, moduleType, controlPin))

		super().__init__(name)

		self._moduleType = moduleType.upper()

		if type(controlPin) == int:
			self._controlPin = controlPin
		else:
			self._controlPin = None

		self._tempC = None
		self._tempF = None

	# Purposly no setter for this property.  It can not be changed.
	@property
	def moduleType(self):
		return self._moduleType

	@property
	def controlPin(self):
		return self._controlPin

	@controlPin.setter
	def controlPin(self, pinNumber):
		self.LOGGER.debug("Setting controlPin number {}".format(pinNumber))
		self._controlPin = pinNumber

	@property
	def tempC(self):
		return self._tempC

	@tempC.setter
	def tempC(self, rawValue):
		"""
		rawValue => The raw sensor value before any conversions
		"""
		self.LOGGER.debug("Setting tempC with rawValue {}".format(rawValue))
		# Do all of the conversions here.  It uses the moduleType to determine what conversion to use.
		if self.moduleType == "LM35":
			self._tempC = rawValue * 0.48828125
		else:
			self._tempC = None

	# Most sensors use Centigrade, but this converts it to Fahernheit
	@property
	def tempF(self):
		if self.tempC:
			return (self.tempC * 1.8) + 32
		else:
			return None

#class PhotoSensor:
	#"""
	#A photo resistor sensing the amount of light in a given area.
	#"""
	#def __init__(self, controlPin):
		#self.controlPin = controlPin

