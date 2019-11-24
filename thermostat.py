# Builtins
import logging
import json
from pathlib import Path
import sys
import os

LOGGER = logging.getLogger("__main__.  thermostat.py")

MODE = ["AUTO", "MANUAL"]
STATES = ["OFF", "FAN", "HEAT", "COOL"]

class Thermostat:
	"""
	A class to create a Thermostat module.
	
	It can contain any number of sensors as long as a formula is created.
	
	You can also group the sensors to get an average temp of the group.
	"""
	# STATES.FAN is not implemented yet
	
	def __init__(self, *args, **kwargs):
		"""
		args => Not used yet
		
		kwargs => When called, any setting can be overridden here in the 
				format   SETTING=VALUE
		"""

		
		self.LOGGER = logging.getLogger("__main__.thermostat.Thermostat")
		
		self.tempSensors = {}
		self.groups = {}
		
		self._state = "OFF"
		self._mode = "AUTO"
		
	@property
	def state(self):
		return self._state
	
	@state.setter
	def state(self, state):
		if state in STATES:
			if state != self.state:
				self._state = state
				self.LOGGER.debug("Thermostat state changed to {}".format(state))
		else:
			self.LOGGER.warning("{} is not a valid STATE for Thermostat").format(state)
	
	@property
	def mode(self):
		return self._mode
	
	@mode.setter
	def mode(self, mode):
		if mode in MODE:
			if mode != self.mode:
				self._mode = mode
				self.LOGGER.info("Thermostat mode changed to {}".format(mode))
		else:
			self.LOGGER.warning("{} is not a valid MODE for Thermostat".format(mode))
		
	def addSensor(self, sensor, location):
		"""
		sensor => A type of temperature sensor
		location => <str> Where the sensor is located.  Used for id
		"""
		self.tempSensors[location.upper()] = sensor
		self.LOGGER.debug("Sensor {} is added.".format(location.upper()))
		
	def createGroup(self, name, *args):
		"""
		name => Name of the group to be created.
		
		<optional> args => Sensors to add when created
		"""
		name = name.upper()
		if name not in self.groups:
			groupedSensors = []
			for sensor in args:
				groupedSensors.append(sensor)
			self.groups[name] = groupedSensors
			self.LOGGER.debug("Created the group {}".format(name))
			return True
		self.LOGGER.warning("The group {} already exists".format(name))
		return False
	
	def addSensorToGroup(self, group, sensor):
		"""
		This function adds a senor to a group so that it's value is added to the
		average of all in the group.
		
		group => The name of the group to add the sensor to
		
		sensor => The sensor to add to the group
		"""
		group = group.upper()
		
		if group in self.groups:
			if sensor not in self.groups[group]:
				self.groups[group].append(sensor)
				self.LOGGER.info("Added sensor {} to group {}".format(sensor, group))
				return True
			self.LOGGER.warning("{} sensor is already a member of the group {}".format(sensor, group))
			return False
		self.LOGGER.warning("There is no group {}".format(group))
		return False
	
	def getTemp(self, area):
		"""
		area => <str> Can either be the specific location of the sensor, 
			or a group of senors.
		"""
		area = area.upper()
		temp = None
		# Check the single areas first
		if area in self.tempSensors:
			temp = self.tempSensors[area].tempC
			self.LOGGER.debug("Temp in area {} is {}C".format(area, self.tempSensors[area].tempC))
			
		# If not there, check if a group is asked for
		elif area in self.groups:
			tempList = []
			for sensor in self.groups[area]:
				tempList.append(sensor.tempC)
			temp = sum(tempList) / len(tempList)
			self.LOGGER.debug("Temp in area {} is {}C".format(area, sensor.tempC))
			
		else:
			self.LOGGER.warning("No area {} in senors or groups".format(area))
			return None
		
		return temp

