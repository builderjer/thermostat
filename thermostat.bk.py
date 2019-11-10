"""
class Thermostat

Controls all of the temperature settings and retrieves the temps of the rooms associated.
"""

__author__ = "builderjer"
__version__ = "0.1.2"

class Thermostat:
	def __init__(self, *args, **kwargs):
		"""
		The default ouput temperature format can be changed with the keyword argument
				outputFormat="C"  or outputFormat="F" when Thermostat is called.
		"""
		
		# Check for outputFormat and assign default if needed
		try:
			if "outputFormat" in kwargs and kwargs["outputFormat"].upper().startswith("C") or kwargs["outputFormat"].upper().startswith("F"):
				self._outputFormat = kwargs["outputFormat"]
			else:
			# Set a default
				self._outputFormat = "F"
		except KeyError:
			# TODO:  Put defaults into file
			self._outputFormat = "F"
			
		self.tempSensors = {}
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
			"""
			Put any special calculations for specific sensors here
			"""
			if self.tempSensors[sensor].moduleType == "LM35":
				temps.append(self.tempSensors[sensor].value * 0.48828125)
		#  Get the average and set it
		self._houseTemp = (sum(temps)/len(temps)) 
	
	@property
	def desiredTemp(self):
		return self._desiredTemp
	
	@desiredTemp.setter
	def desiredTemp(self, temp):
		self._desiredTemp = temp
	
	def addSensor(self, sensor, location):
		self.tempSensors[location.upper()] = sensor
	
	def getRoomTemp(self, room):
		if room.upper() in tempSensors.keys():
			return tempSensors[room.upper()].value
		return None
	

