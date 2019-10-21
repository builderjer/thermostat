"""
This script is to hold a variety of sensos used in my personal smarthome.
https://github.com/builderjer/ZiggyAI
"""

class TempSensor:
	"""
	A class to create a temperature sensor for use with an Arduino and the firmata library
	"""
	def __init__(self, moduleType, controlPin, location, outputFormat="F"):
		"""
		moduleType => type of sensor (LM35, etc...)
			It is required because each sensor uses a different forumla to determine the temp
		controlPin => The Arduino pin the sensor is connected to.  Must be an intiger
		location => The place it is locatated (KITCHEN, LIVINGROOM)
			Required for id purposes.
		outputFormat => Show the ouput as Celsius "C" or Fahrenheit "F"
		
		"""
		self.moduleType = moduleType.upper()
		self._controlPin = int(controlPin)
		if location is not None:
			self._location = location.upper()
		else:
			self._location = None
		self.outputFormat = outputFormat
		self._value = None
		
	@property
	def controlPin(self):
		return self._controlPin
	
	@controlPin.setter
	def controlPin(self, pinNumber):
		self._controlPin = pinNumber
		
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, data):
	#def value(self, moduleType, data, outputFormat):
		"""
		data => The raw value sent from the Arduino
		"""
		v = 0.0
		if self.moduleType == "LM35":
			"""
			The LM35 defaults to Celsius, and at a 5v input, it needs this conversion
			"""
			v = data * 0.48828125
		
		self._value = v
		
	@property
	def location(self):
		return self._location
	
	@location.setter
	def location(self, location):
		"""
		Automatically converts to uppercase
		"""
		self._location = location.upper()
		
		
		
