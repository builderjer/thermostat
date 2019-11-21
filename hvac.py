import logging
import sys

LOGGER = logging.getLogger("__main__.hvac.py")

CONFIG_FILE = "config/default.json"

class HVAC:
	def __init__(self, board=None):
		self.LOGGER = logging.getLogger("__main__.hvac.HVAC")

		self._heat = 0
		self._cool = 0
		self._heatControl = ()
		self._coolControl = ()
		
		if board == None:
		#if "board" not in kwargs:
			self.LOGGER.error("No board was passed.  This will not work")
			sys.exit()
		else:
			self.board = board
		
	@property
	def heat(self):
		return self._heat
	
	@heat.setter
	def heat(self, pin):
		self._heat = self.board.digital_read(pin)
		self.LOGGER.debug("Set heat to {}".format(self.heat))
		
	@property
	def cool(self):
		return self._cool
	
	@cool.setter
	def cool(self, pin):
		self._cool = self.board.digital_read(pin)
		self.LOGGER.debug("Set cool to {}".format(self.cool))
		
	def setPins(self, heatOrCool, onPin, offPin, sensePin):
		if heatOrCool.upper() == "HEAT":
			self._heatControl = (onPin, offPin, sensePin)
		elif heatOrCool.upper() == "COOL":
			self._coolControl == (onPin, offPin, sensePin)
		else:
			LOGGER.error("Control pins must be HEAT or COOL")
			self._heatControl = ()
			self._coolControl = ()
	
	def turnHeatOn(self):
		try:
			self.board.digital_write(self._heatControl[0], 1)
			self.board.sleep(.1)
			
			self.board.digital_write(self._heatControl[0], 0)
			self.board.sleep(.5)
			self.board.digital_read(self._heatControl[2])
			self.heat = self._heatControl[2]
		except Exception as e:
			self.LOGGER.error("Error turning on heat -- {}".format(e))
		self.LOGGER.info("Turned heat on")
		#print("turned heat on")
		
	def turnHeatOff(self):
		try:
			self.board.digital_write(self._heatControl[1], 1)
			self.board.sleep(.1)
			self.board.digital_write(self._heatControl[1], 0)
			self.board.sleep(.5)
			self.board.digital_read(self._heatControl[2])
			self.heat = self._heatControl[2]
		except Exception as e:
			self.LOGGER.error("Error turning on heat -- {}".format(e))
		self.LOGGER.info("Turned heat off")
		#print("turned heat off")
		
	def turnCoolOn(self):
		self.board.digital_write(self._coolControl[0], 1)
		self.board.sleep(.1)
		self.board.digital_write(self._coolControl[0], 0)
		self.board.sleep(.5)
		self.board.digital_read(self._coolControl[2])
		self.cool = self._coolControl[2]
		
	def turnCoolOff(self):
		self.board.digital_write(self._coolControl[1], 1)
		self.board.sleep(.1)
		self.board.digital_write(self._heatControl[1], 0)
		self.board.sleep(.5)
		self.board.digital_read(self._coolControl[2])
		self.cool = self._coolControl[2]
