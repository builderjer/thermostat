"""
This script is to hold a variety of sensors used in my personal smarthome.
https://github.com/builderjer/ZiggyAI
"""

__author__ = "builderjer"
__version__ = "0.1.1"

class TempSensor:
	"""
	A class to create a temperature sensor for use with an Arduino or other microcontroller
	"""
	#def __init__(self, moduleType, controlPin, location, outputFormat="F"):
	def __init__(self, moduleType, controlPin, location="DEFAULT"):
		"""
		<string> moduleType => type of sensor (LM35, etc...)
			It is required because each sensor uses a different forumla to determine the temp
			
		<int> controlPin => The pin on the microcontroller the sensor is connected to.
		
		<string> location => The place the sensor is locatated (KITCHEN, LIVINGROOM)
		"""
		self.moduleType = moduleType.upper()
		
		if type(controlPin) == int:
			self._controlPin = controlPin
		else:
			self._controlPin = None
		
		self._location = location.upper()
		
		# Assign a variable to store the value the sensor returns
		self._value = None
		
	@property
	def controlPin(self):
		return self._controlPin
	
	@controlPin.setter
	def controlPin(self, pinNumber):
		self._controlPin = pinNumber
		
	@property
	def location(self):
		return self._location
	
	@location.setter
	def location(self, location):
		"""
		Automatically converts to uppercase
		"""
		self._location = location.upper()
	
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, data):
		"""
		data => The raw value sent from the microcontroller.
		
		Usage:  Add the module type after the 'v' decloration.
			Use the "LM35" module as a model.  The module must assign a value to 'v'
		"""
		v = 0.0
		if self.moduleType == "LM35":
			"""
			The LM35 defaults to Celsius, and at a 5v input, it needs this conversion
			"""
			v = data * 0.48828125
		
		self._value = v
		
		
		
