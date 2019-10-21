"""
class Thermostat

Controls all of the temperature settings and retrieves the temps of the rooms associated.
"""

__author__ = "builderjer"
__version__ = "0.1.0"

class Thermostat:
	def __init__(self, outputFormat):
		"""
		outputFormat => Output into either Celsius or Fahrenheit
		"""
		self.outputFormat = outputFormat.upper()
		self.tempSensors = []
		self._currentTemp = 0
		self._desiredTemp = 0
	
	def addSensor(self, sensor):
		self.tempSensors.append(sensor)
	
	@property
	def currentTemp(self):
		return self._currentTemp
	
	@currentTemp.setter
	def currentTemp(self, temp):
		
		if self.outputFormat.upper().startswith("C"):
			self._currentTemp = round(temp, 1)
		
		if self.outputFormat.upper().startswith("F"):
			self._currentTemp = round((temp * 1.8) + 32, 1)
			
	@property
	def desiredTemp(self):
		return self._desiredTemp
	
	@desiredTemp.setter
	def desiredTemp(self, temp):
		self._desiredTemp = temp



