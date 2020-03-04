import logging
import sys

LOGGER = logging.getLogger("__main__.hvac.py")

__version__ = "0.1.0"

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
	def __init__(self, board, mqtt=None):
		self.LOGGER = logging.getLogger("__main__.hvac.Thermostat")

		self.board = board
		self._mqtt = mqtt

		self.modes = ["AUTO", "MANUAL"]
		self._mode = self.modes["AUTO"]

		self.tempSensors = []
		self.groups = {}

		self._desiredTemp = None

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
	def desiredTemp(self):
		return self._desiredTemp

	@desiredTemp.setter
	def desiredTemp(self, temp):
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

	def addSensor(self, sensor):
		if sensor not in self.tempSensors:
			self.board.set_pin_mode(sensor.controlPin, Constants.ANALOG)
			self.tempSensors.append(sensor)
			self.LOGGER.info("Sensor {} with control pin {} added to Thermostat".format(sensor.name, sensor.controlPin))

	def createSensorGroup(self, groupName):
		groupName = groupName.upper()
		if groupName not in self.groups:
			self.groups[groupName] = []
			self.LOGGER.info("Group {} created".format(groupName))

	def addSensorToGroup(self, sensor, group):
		if group in self.groups:
			if sensor in self.tempSensors:
				if sensor not in self.groups[group]:
					self.groups[group].append(sensor)
					self.LOGGER.info("Sensor {} added to group {}".format(sensor.name, group))
				else:
					self.LOGGER.warning("Sensor {} is already in group {}".format(sensor.name, group))
			else:
				self.LOGGER.warning("You must add the sensor {} to the Thermostat before adding to a group".format(sensor.name))
		else:
			self.LOGGER.warning("Group {} does not exist to add a sensor to".format(group))

	def updateSensors(self):
		for sensor in self.tempSensors:
			sensor.tempC = self.board.analog_read(sensor.controlPin)
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
			if area.upper() = sensor.name:
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
			# Publish each sensor temp first
			for sensor in self.tempSensors:
				temp = self.getTemp(sensor.name)
				topic = "/".join(self.mqtt["PATH"], sensor.name.lower())
				mqtt_pub.single(topic, payload=temp, qos=1, retain=True, hostname=self.mqtt["HOST"], port=int(self.mqtt["PORT"]), auth={"username": self.mqtt["USER"], "password": self.mqtt["PASSWORD"]})
			# Now publish the groups
			for area in self.groups:
				temp = self.getTemp(area)
				topic = "/".join(self.mqtt["PATH"], area.lower())
				mqtt_pub.single(topic, payload=temp, qos=1, retain=True, hostname=self.mqtt["HOST"], port=int(self.mqtt["PORT"]), auth={"username": self.mqtt["USER"], "password": self.mqtt["PASSWORD"]})
		else:
			self.LOGGER.warning("MQTT is either not enabled, or not setup correct")

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

		for pin is self.controlPins:
			self.board.set_pin_mode(pin, Constants.OUTPUT)

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
			 self.turnOff

	def turnOn(self):
		self.board.digital_write(self.controlPins[0], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[0], 0)
		self.board.sleep(0.1)

	def turnOff(self):
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

		for pin is self.controlPins:
			self.board.set_pin_mode(pin, Constants.OUTPUT)

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
			 self.turnOff

	def turnOn(self):
		self.board.digital_write(self.controlPins[0], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[0], 0)
		self.board.sleep(0.1)

	def turnOff(self):
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

		for pin is self.controlPins:
			self.board.set_pin_mode(pin, Constants.OUTPUT)

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
			 self.turnOff

	def turnOn(self):
		self.board.digital_write(self.controlPins[0], 1)
		self.board.sleep(0.1)
		self.board.digital_write(self.controlPins[0], 0)
		self.board.sleep(0.1)

	def turnOff(self):
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

	def changeHeatState(self, state):
		self.heater.state = state

	def changeACState(self, state):
		self.ac.state = state

	def changeVentState(self, state):
		self.vent.state = state

