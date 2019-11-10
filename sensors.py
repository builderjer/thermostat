"""
This script is to hold a variety of sensors used in my personal smarthome.
https://github.com/builderjer/ZiggyAI
"""

__author__ = "builderjer"
__version__ = "0.1.2"

import logging

LOGGER = logging.getLogger("__main__.  sensors.py")

class TempSensor:
	"""
	A class to create a temperature sensor for use with an Arduino or other microcontroller
	"""
	def __init__(self, moduleType, controlPin):
		"""
		<string> moduleType => type of sensor (LM35, etc...)
			It is required because each sensor uses a different forumla to determine the temp
			
		<int> controlPin => The pin on the microcontroller the sensor is connected to.
		"""
		self.LOGGER = logging.getLogger("__main__.  sensors.TempSensor")
		self.LOGGER.debug("Created TempSensor with moduleType {} and controlPin {}".format(moduleType, controlPin))
		
		self.moduleType = moduleType.upper()
		
		if type(controlPin) == int:
			self._controlPin = controlPin
		else:
			self._controlPin = None
		
		self._tempC = None
		
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
	def tempC(self, dataList):
		"""
		dataList => A two value touple containing the sensor type and raw value
				from the sensor
		"""
		self.LOGGER.debug("Setting tempC with dataList {}".format(dataList))
		if dataList[0] == "LM35":
			self._tempC = dataList[1] * 0.48828125
		else:
			self._tempC = None

class PhotoSensor:
	"""
	A photo resistor sensing the amount of light in a given area.
	"""
	def __init__(self, controlPin):
		self.controlPin = controlPin
	
