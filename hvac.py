"""
hvac.py -- A set of classes designed for a simple HVAC system.

To be a complete HVAC system, it should have a heating system, cooling system,
and a vent.  All of these need a thermostat to control all of these.

Each one of these elements have thier own class, and should be created as a
property of a HVAC object.

These classes are designed to be run with an Arduino running PyMata found at
https://github.com/MrYsLab/pymata-aio.  The main script can be run from any
machine that can interface with the said Arduino.
"""

import logging
import sys
import datetime
import copy

LOGGER = logging.getLogger("__main__.hvac.py")

__version__ = "0.2.0"

# HVAC is controlled by an Arduino board with PyMata installed
try:
	from pymata_aio.pymata3 import PyMata3
	from pymata_aio.constants import Constants
except ModuleNotFoundError as e:
	LOGGER.error("PyMata3 is required for use.  https://github.com/MrYsLab/pymata-aio")
	#sys.exit()

# MQTT is optional but recommended
try:
	import paho.mqtt.client as mqtt
	import paho.mqtt.publish as mqtt_pub
	MQTT_ENABLED = True
except ModuleNotFoundError:
	MQTT_ENABLED = False
	LOGGER.warning("Package paho-mqtt is not installed.  MQTT communication will be disabled")

class Thermostat:
	"""
	class Thermostat => The main control class for the HVAC object

	This class does everything from getting the temperature of the house, to
	publishing the results to a mqtt broker.

	This is where the "Smart Stuff" happens
	"""
	def __init__(self, board, mqtt=None, tempSettings=None):
		"""
		board => Only required argument.  It is an initiated Arduino board with PyMata.
		mqtt => Optional => A dictionary contaning all of the required settings to connect
			with a mqtt broker.
		tempSettings => Maybe shoud be required but optional for now. => A dictionary of
			times and conditions to modify the temperature to keep the area at.

		properties:

		board => Arduino PyMata board
		tempSettings => Dictionary of times to modify the temperature
		modes => AUTO or MANUAL => When in AUTO, all temperatures are automaticaly controlled.
			When in MANUAL, it will run the HVAC for 2 cycles at that setting and then return
			to AUTO mode.
		tempSensors => A list of temperature sensors to use for various inputs
		groups => A set of tempSensors that are grouped as one single ententy
		_mqtt => MQTT connection settings

		"""
		self.LOGGER = logging.getLogger("__main__.hvac.Thermostat")

		self.board = board
		self._mqtt = mqtt
		self.tempSettings = tempSettings

		self.modes = ["AUTO", "MANUAL"]
		self._mode = "AUTO"

		self.tempSensors = []
		self.groups = {}

		self._defaultTemp = None
		self._desiredTemp = None
		self._occupied = None
		self._timeOfYear = None

	@property
	def mode(self):
		return self._mode

	@mode.setter
	def mode(self, mode):
		if mode in self.modes and mode != self.mode:
			self._mode = mode
			self.LOGGER.info("Thermostat mode changed to {}".format(self.mode))
		else:
			self.LOGGER.warning("{} is not a valid mode for this Thermostat".format(mode))

	@property
	def defaultTemp(self):
		return self._defaultTemp

	@defaultTemp.setter
	def defaultTemp(self, temp):
		self._defaultTemp = temp

	@property
	def desiredTemp(self):
		return self._desiredTemp

	@desiredTemp.setter
	def desiredTemp(self, temp):
		self.LOGGER.debug("In desiredTemp setter {}".format(temp))
		if temp:
			self.mode = "MANUAL"
			self._desiredTemp = temp
			return
		try:
			tempDict = {}
			current = datetime.datetime.now()
			self.LOGGER.debug("current time: {}".format(current))
			if current.month >= 11 or current.month <= 3:
				tempDict = copy.deepcopy(self.tempSettings["WINTER"])
				self.timeOfYear = current.month
			elif current.month >= 7 or current.month <= 9:
				tempDict = copy.deepcopy(self.tempSettings["SUMMER"])
				self.timeOfYear = current.month
			else:
				self._desiredTemp = None
				return
			self.defaultTemp = tempDict.pop("DEFAULT_TEMP")
			modList = []
			try:
				occupiedSettings = tempDict.pop("OCCUPIED_SETTINGS")
				if self.occupied:
					modList.append(occupiedSettings["HOME"])
				else:
					modList.append(occupiedSettings["AWAY"])
			except KeyError:
				pass
			for settingType in tempDict:
				modList.extend(tempDict[settingType].values())
			modTemp = 0
			self.LOGGER.debug("modList: {}".format(modList))
			for mlist in modList:
				if self.getBetweenTime([mlist[0], mlist[1]], current):
					modTemp += mlist[2]
			self.LOGGER.debug("defaultTemp: {}  modTemp: {}".format(self.defaultTemp, modTemp))
			self._desiredTemp = self.defaultTemp + modTemp

		except KeyError as e:
			self.LOGGER.info("No temp modifications")
			self._desiredTemp = temp

	@property
	def mqtt(self):
		return self._mqtt

	@mqtt.setter
	def mqtt(self, mqtt_variables):
		if MQTT_ENABLED:
			self._mqtt = mqtt_variables
		else:
			self._mqtt = None

	@property
	def occupied(self):
		return self._occupied

	@occupied.setter
	def occupied(self, homeList):
		if homeList:
			self._occupied = True
		else:
			self._occupied = False

	@property
	def timeOfYear(self):
		return self._timeOfYear

	@timeOfYear.setter
	def timeOfYear(self, month):
		if month >= 11 or month <= 3:
			self._timeOfYear = "WINTER"
		elif month >= 7 or month <= 9:
			self._timeOfYear = "SUMMER"
		else:
			self._timeOfYear = None
		self.LOGGER.debug(self.timeOfYear)

	def addSensor(self, sensor):
		if sensor not in self.tempSensors:
			self.board.set_pin_mode(sensor.controlPin, Constants.ANALOG)
			self.tempSensors.append(sensor)
			self.LOGGER.info("Sensor {} with control pin {} added to Thermostat".format(sensor.name, sensor.controlPin))
			self.LOGGER.debug(sensor)
		else:
			self.LOGGER.info("Sensor {} already added".format(sensor))

	def createSensorGroup(self, groupName):
		groupName = groupName.upper()
		if groupName not in self.groups:
			self.groups[groupName] = []
			self.LOGGER.info("Group {} created".format(groupName))

	def addSensorToGroup(self, sensor, group):
		if group in self.groups:
			self.LOGGER.debug((group, sensor))
			if sensor in self.tempSensors:
				self.LOGGER.info(sensor.name)
				if sensor not in self.groups[group]:
					self.groups[group].append(sensor)
					self.LOGGER.info("Sensor {} added to group {}".format(sensor.name, group))
				else:
					self.LOGGER.warning("Sensor {} is already in group {}".format(sensor.name, group))
			else:
				self.LOGGER.info(sensor)
				self.LOGGER.warning("You must add the sensor {} to the Thermostat before adding to a group".format(sensor.name))
		else:
			self.LOGGER.warning("Group {} does not exist to add a sensor to".format(group))

	def updateSensors(self):
		for sensor in self.tempSensors:
			temp = 0
			for _ in range(10):
				#sensor.tempC = self.board.analog_read(sensor.controlPin)
				temp += self.board.analog_read(sensor.controlPin)
				self.LOGGER.debug("temp in updateSensors: {}".format(temp))
				self.board.sleep(.1)
			sensor.tempC = temp / 10
			self.LOGGER.debug(sensor.tempC)
			self.LOGGER.debug("Updated sensor {}".format(sensor.name))

	def getTemp(self, area, tempFormat="F"):
		if area.upper() in self.groups:
			temp = 0
			for sensor in self.groups[area.upper()]:
				if tempFormat == "F":
					temp += sensor.tempF
				else:
					temp += sensor.tempC
			groupTemp = temp / len(self.groups[area.upper()])
			self.LOGGER.debug("{} temp is {}".format(area, groupTemp))
			return groupTemp

		for sensor in self.tempSensors:
			if area.upper() == sensor.name:
				if tempFormat == "F":
					temp = sensor.tempF
				else:
					temp = sensor.tempC
				self.LOGGER.debug("Sensor {}: {}".format(area, temp))
				return temp

		self.LOGGER.warning("No area {} in Thermostat sensors or groups".format(area.upper()))
		return None

	def publish(self):
		if MQTT_ENABLED and self.mqtt:
			try:
				# Publish each sensor temp first
				for sensor in self.tempSensors:
					temp = round(self.getTemp(sensor.name), 1)
					topic = "/".join((self.mqtt["PATH"], sensor.name.lower()))
					mqtt_pub.single(topic, payload=temp, qos=1, retain=True, hostname=self.mqtt["HOST"], port=int(self.mqtt["PORT"]), auth={"username": self.mqtt["USER"], "password": self.mqtt["PASSWORD"]})
				# Now publish the groups
				for area in self.groups:
					temp = round(self.getTemp(area), 1)
					topic = "/".join((self.mqtt["PATH"], area.lower()))
					mqtt_pub.single(topic, payload=temp, qos=1, retain=True, hostname=self.mqtt["HOST"], port=int(self.mqtt["PORT"]), auth={"username": self.mqtt["USER"], "password": self.mqtt["PASSWORD"]})
				# Publish misc stuff
				topic = "/".join((self.mqtt["PATH"], "desired"))
				mqtt_pub.single(topic, payload=self.desiredTemp, qos=1, retain=True, hostname=self.mqtt["HOST"], port=int(self.mqtt["PORT"]), auth={"username": self.mqtt["USER"], "password": self.mqtt["PASSWORD"]})
			except:
				self.LOGGER.warning("Could not connect to MQTT.  Skipping publish")
		else:
			self.LOGGER.warning("MQTT is either not enabled, or not setup correct")

	def getBetweenTime(self, timeList, currentTime):
		"""
		timeList => 2 - 4 digit string in 24 hr time format
				ex:		["startTime", "endTime"]
				ex:		["0600", "0930"] 6:00 am to 9:30 am
				ex:		["0", "0"] all 24 hours
		"""
		if int(timeList[0]) == 0 or int(timeList[1]) == 0:
			return True

		#now = datetime.datetime.now()
		startHour = int(timeList[0][:2])
		#self.LOGGER.debug("startHour: {}".format(startHour))
		startMinute = int(timeList[0][2:])
		#self.LOGGER.debug("startMinute: {}".format(startMinute))
		endHour = int(timeList[1][:2])
		#self.LOGGER.debug("endHour: {}".format(endHour))
		endMinute = int(timeList[1][2:])
		#self.LOGGER.debug("endMinute: {}".format(endMinute))
		startTime = currentTime.replace(hour=startHour, minute=startMinute, second=0, microsecond=0)
		endTime = currentTime.replace(hour=endHour, minute=endMinute, second=0, microsecond=0)

		self.LOGGER.debug("Start time: {}  End time {}".format(startTime, endTime))

		if startTime <= currentTime and endTime >= currentTime:
			self.LOGGER.debug("Good Times")
			return True
		return False
		#if currentTime.hour >= startHour and currentTime.minute >= startMinute:
			#self.LOGGER.debug("Within start time")
			#if currentTime.hour <= endHour and currentTime.minute <= endMinute:
				#self.LOGGER.debug("Within end time")
				#return True
		#return False

class Heater:
	def __init__(self, board, controlPins):
		"""
		board => A pymata instance passed from the HVAC

		controlPins => list of arduino pins to use with pymata
				[off, on]
		"""
		self.LOGGER = logging.getLogger("__main__.hvac.Heater")
		self.board = board
		self.controlPins = controlPins
		self._state = "OFF"

		for pin in self.controlPins:
			self.board.set_pin_mode(pin, Constants.OUTPUT)

		self.LOGGER.debug("Created Heater object")

	@property
	def state(self):
		return self._state

	@state.setter
	def state(self, onOff):
		if onOff.upper() == "ON" and self.state == "OFF":
			self._state = onOff
			self.turnOn()
		if onOff.upper() == "OFF" and self.state == "ON":
			 self._state = onOff
			 self.turnOff()

	def turnOff(self):
		self.LOGGER.debug("In Heater turnOff")
		self.board.digital_write(self.controlPins[0], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[0], 0)
		self.board.sleep(0.1)

	def turnOn(self):
		self.LOGGER.debug("In Heater turnOn")
		self.board.digital_write(self.controlPins[1], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[1], 0)
		self.board.sleep(0.1)

class AirConditioner:
	def __init__(self, board, controlPins):
		"""
		board => A pymata instance passed from the HVAC

		controlPins => list of arduino pins to use with pymata
				[off, on]
		"""
		self.LOGGER = logging.getLogger("__main__.hvac.AirConditioner")
		self.board = board
		self.controlPins = controlPins
		self._state = "OFF"

		for pin in self.controlPins:
			self.board.set_pin_mode(pin, Constants.OUTPUT)

		self.LOGGER.debug("Created AirConditioner object")

	@property
	def state(self):
		return self._state

	@state.setter
	def state(self, onOff):
		if onOff.upper() == "ON":
			self._state = onOff
			self.turnOn()
		if onOff.upper() == "OFF":
			 self._state = onOff
			 self.turnOff()

	def turnOff(self):
		self.LOGGER.debug("turning off AC")
		self.board.digital_write(self.controlPins[0], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[0], 0)
		self.board.sleep(0.1)

	def turnOn(self):
		self.LOGGER.debug("turning on AC")
		self.board.digital_write(self.controlPins[1], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[1], 0)
		self.board.sleep(0.1)

class Vent:
	def __init__(self, board, controlPins):
		"""
		controlPins => list of arduino pins to use with pymata
				[off, on]
		"""
		self.LOGGER = logging.getLogger("__main__.hvac.Vent")
		self.board = board
		self.controlPins = controlPins
		self._state = "OFF"

		for pin in self.controlPins:
			self.board.set_pin_mode(pin, Constants.OUTPUT)

		self.LOGGER.debug("Created Vent object")

	@property
	def state(self):
		return self._state

	@state.setter
	def state(self, onOff):
		if onOff.upper() == "ON":
			self._state = onOff
			self.turnOn()
		if onOff.upper() == "OFF":
			 self._state = onOff
			 self.turnOff()

	def turnOff(self):
		self.board.digital_write(self.controlPins[0], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[0], 0)
		self.board.sleep(0.1)

	def turnOn(self):
		self.board.digital_write(self.controlPins[1], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[1], 0)
		self.board.sleep(0.1)

class HVAC:
	"""
	class HVAC
		Controls a typical HVAC unit consisting of a heater, air conditioner,
		and a vent.

		You must add each object to the HVAC object for it to work
	"""
	def __init__(self, name, port=None):
		self.LOGGER = logging.getLogger("__main__.hvac.HVAC")
		if port:
			try:
				self.board = PyMata3(com_port=port)
			except Exception as e:
				self.LOGGER.error("Cannot connect to com port {}".format(port))
				#sys.exit()
		else:
			try:
				self.board = PyMata3()
			except Exception as e:
				self.LOGGER.error("Cannot connect to default com port")
				#sys.exit()

		self.heater = None
		self.ac = None
		self.vent = None
		self.thermostat = None

		self.LOGGER.debug("Created HVAC object")

	def changeHeatState(self, state):
		self.LOGGER.info("Heat state changed to {}".format(state))
		self.heater.state = state

	def changeACState(self, state):
		self.LOGGER.info("AC state changed to {}".format(state))
		self.ac.state = state

	def changeVentState(self, state):
		self.LOGGER.info("Vent state changed to {}".format(state))
		self.vent.state = state

