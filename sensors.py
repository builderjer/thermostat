"""
This script is to hold a variety of sensors used in my personal smarthome.
https://github.com/builderjer/ZiggyAI
"""

__author__ = "builderjer"
__version__ = "0.1.3"

import logging

LOGGER = logging.getLogger("__main__.sensors.py")

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
		self.LOGGER = logging.getLogger("__main__.sensors.TempSensor")
		self.LOGGER.debug("Created TempSensor with moduleType {} and controlPin {}".format(moduleType, controlPin))
		
		self.moduleType = moduleType.upper()
		
		self._tempC = 0
		
		if type(controlPin) == int:
			self.controlPin = controlPin
		else:
			self.controlPin = None
	
	@property
	def tempC(self):
		return self._tempC
	
	@tempC.setter
	def tempC(self, temp):
		# Put your conversions for each type of sensor here
		if self.moduleType == "LM35":
			temp = temp * 0.48828125
		self._tempC = temp
		self.LOGGER.debug("Setting tempC with temp {}".format(temp))
			
	def getTemp(self, dataList):
		self.tempC = dataList[1]		
	
