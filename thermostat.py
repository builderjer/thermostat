"""
class Thermostat

Controls all of the temperature settings and retrieves the temps of the rooms associated.
"""

__author__ = "builderjer"
__version__ = "0.1.1"

class Thermostat:
	def __init__(self, outputFormat="F"):
		"""
		<string> outputFormat => Output into either Celsius or Fahrenheit
			Defaults to "F"ahrenheit
		"""
		self.tempSensors = []
		if outputFormat.upper().startswith("F") or outputFormat.upper().startswith("C"):
			self._outputFormat = outputFormat.upper()
		else:
			self._outputFormat = "F"
		self._houseTemp = None
		self._desiredTemp = None
	
	@property
	def outputFormat(self):
		return self._outputFormat
	
	@outputFormat.setter
	def outputFormat(self, outputFormat):
		if outputFormat.upper().startswith("F") or outputFormat.upper().startswith("C"):
			self._outputFormat = outputFormat.upper()
		
	@property
	def houseTemp(self):
		if self.outputFormat == "C":
			return self._houseTemp
		else:
			return (self._houseTemp * 1.8) + 32
	
	@houseTemp.setter
	def houseTemp(self, outputFormat):
		temps = []
		for sensor in self.tempSensors:
			temps.append(sensor.value)
		self._houseTemp = (sum(temps)/len(temps)) * 0.48828125
	
	@property
	def desiredTemp(self):
		return self._desiredTemp
	
	@desiredTemp.setter
	def desiredTemp(self, temp):
		self._desiredTemp = temp
	
	def addSensor(self, sensor):
		self.tempSensors.append(sensor)
	
	def getRoomTemp(self, room):
		for sensor in self.tempSensors:
			if sensor.location == room.upper():
				return sensor.value
		return None
	

