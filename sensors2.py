class Sensor:
	"""
	Base class for all other sensors.
	"""
	def __init__(self, name):
		self.name = name
		self._controlPin = None
		
	@property
	def controlPin(self):
		return self._controlPin
	
	@controlPin.setter
	def controlPin(self, pinNumber):
		self._controlPin = pinNumber
	
class TempSensor(Sensor):
	pass
		
