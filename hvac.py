import logging
import sys

LOGGER = logging.getLogger("__main__.hvac.py")

STATES = ["OFF", "HEAT", "COOL"]

class HVAC:
	def __init__(self):
		self.LOGGER = logging.getLogger("__main__.hvac.HVAC")

		self._heatControl = ()
		self._coolControl = ()
		self._state = "OFF"

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
		self.LOGGER.info("HVAC state set to {}".format(self.state))

	#def setHeatState(self):
		#if self.state == "OFF":
			#self.state = "HEAT"
			#self.LOGGER.info("HVAC state set to {}".format(self.state))
			#return self.state
		#if self.state == "HEAT":
			#self.state = "OFF"
			#self.LOGGER.info("HVAC state set to {}".format(self.state))
			#return self.state
		#else:
			#return False

	#def setCoolState(self, dataList):
		#self.LOGGER.debug("in setCoolState")
		#if dataList[0] == self.coolControl[2]:
			#if dataList[1]:
				#self.state = "COOL"
			#else:
				#self.state = "OFF"
			#self.LOGGER.info("HVAC state set to {}".format(self.state))
			#return

	#def turnHeatOn(self):
		#"""
		#"""
		#if self.state == "OFF":
			#return True
		#else:
			#return False

	#def turnHeatOff(self):
		#if self.state == "HEAT":
			#return True
		#else:
			#return False

	#def changeHeatState(self, onOff):
		#"""
		#onOff => Self explanitory
			#Must be either "ON" or "OFF"
		#"""
		#if onOff.upper() == "OFF":
			#if self.state
	#def turnCoolOn(self):
		#if self.state == "OFF":
			#return True
		#else:
			#return False

	#def turnCoolOff(self):
		#if self.state == "COOL":
			#return True
		#else:
			#return False
