import logging
import sys

from pymata_aio.constants import Constants

LOGGER = logging.getLogger("__main__.hvac.py")

STATES = ["OFF", "HEATING", "COOLING"]

class HVAC:
	def __init__(self):
		self.LOGGER = logging.getLogger("__main__.hvac.HVAC")

		#self._heat = 0
		#self._cool = 0
		self._heatControl = ()
		self._coolControl = ()
		self._state = "OFF"
		
		#if board == None:
		##if "board" not in kwargs:
			#self.LOGGER.error("No board was passed.  This will not work")
			#sys.exit()
		#else:
			#self.board = board
		
	#@property
	#def heat(self):
		#return self._heat
	
	#@heat.setter
	#def heat(self, state):
		#self._heat = state
		#self.LOGGER.debug("Set heat to {}".format(self.heat))
		
	#@property
	#def cool(self):
		#return self._cool
	
	#@cool.setter
	#def cool(self, state):
		#self._cool = state
		#self.LOGGER.debug("Set cool to {}".format(self.cool))
		
	@property
	def heatControl(self):
		return self._heatControl
	
	@heatControl.setter
	def heatControl(self, controlPins):
		"""
		controlPins => (on pin, off pin, sensor pin)
			on pin:  The pin used to turn the heater on
			off pin:  The pin used to turn the heater off
			sensor pin: Used with latching relays.  If power outage, the state of the heater stays
		"""
		self._heatControl = controlPins
		
	@property
	def coolControl(self):
		return self._coolControl
	
	@coolControl.setter
	def coolControl(self, controlPins):
		"""
		controlPins => (on pin, off pin, sensor pin)
			on pin:  The pin used to turn the cooler on
			off pin:  The pin used to turn the cooler off
			sensor pin: Used with latching relays.  If power outage, the state of the cooler stays
		"""
		self._coolControl = controlPins
		
	@property
	def state(self):
		return self._state
	
	@state.setter
	def state(self, state):
		if state in STATES:
			self._state = state
		else:
			self._state = "OFF"
			
	def setState(self, dataList):
		# Check if it is for the heater or cooler
		if dataList[0] == self.heatControl[2]:
			if dataList[1]:
				self.state = "HEATING"
			else:
				self.state = "OFF"
				
		if dataList[0] == self.coolControl[2]:
			if dataList[1]:
				self.state = "COOLING"
			else:
				self.state = "OFF"
		self.LOGGER.info("HVAC state set to {}".format(self.state))

	def turnHeatOn(self):
		"""
		returns boolean to use in main code to trigger a change
		"""
		if self.state == "OFF":
			return True
		else:
			return False
		#try:
			#self.board.digital_write(self._heatControl[0], 1)
			#self.board.sleep(.1)
			#self.board.digital_write(self._heatControl[0], 0)
			#self.board.sleep(.1)
			
		#except Exception as e:
			#self.LOGGER.error("Error turning on heat -- {}".format(e))
		#self.LOGGER.info("Turned heat on")
		#print("turned heat on")
		
	def turnHeatOff(self):
		if self.state == "HEATING":
			return True
		else:
			return False
		#try:
			#self.board.digital_write(self._heatControl[1], 1)
			#self.board.sleep(.1)
			#self.board.digital_write(self._heatControl[1], 0)
			#self.board.sleep(.1)
		#except Exception as e:
			#self.LOGGER.error("Error turning on heat -- {}".format(e))
		#self.LOGGER.info("Turned heat off")
		#print("turned heat off")
		
	def turnCoolOn(self):
		if self.state == "OFF":
			return True
		else:
			return False
		#self.board.digital_write(self._coolControl[0], 1)
		#self.board.sleep(.1)
		#self.board.digital_write(self._coolControl[0], 0)
		#self.board.sleep(.5)
		#self.board.digital_read(self._coolControl[2])
		#self.cool = self._coolControl[2]
		
	def turnCoolOff(self):
		if self.state == "COOLING":
			return True
		else:
			return False
		#self.board.digital_write(self._coolControl[1], 1)
		#self.board.sleep(.1)
		#self.board.digital_write(self._heatControl[1], 0)
		#self.board.sleep(.5)
		#self.board.digital_read(self._coolControl[2])
		#self.cool = self._coolControl[2]
