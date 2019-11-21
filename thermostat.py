# Builtins
import logging
import json
from pathlib import Path
import sys

LOGGER = logging.getLogger("__main__.thermostat.py")

CONFIG_FILE = "config/default.json"

class Thermostat:
	"""
	A class to create a Thermostat module.
	
	It can contain any number or types of sensors as long as a formula is 
	created to convert to celsius.
	
	You can also group the sensors to get an average temp of the group.
	"""
	
	STATES = ["OFF", "FAN", "HEAT", "COOL"]
	
	def __init__(self, *args, board=None, **kwargs):
		"""
		args => Not used yet
		
		kwargs => When called, any setting can be overridden here in the 
				format   SETTING=VALUE
				
		NOTE: A board must be passed in the kwargs.
				The board is a PyMata3 instance.
				Pass in the form -- board=PyMata3.board
				
				if "config" is declared, all other settings, minus the board, declared will be ignored.
		"""
		self.LOGGER = logging.getLogger("__main__.thermostat.Thermostat")

		# Load the default settings first
		self.settings = self.loadConfig(CONFIG_FILE)
		if type(self.settings) != dict:
			self.LOGGER.error("Settings did not load.  Check log file.  Exiting")
			sys.exit()
		self.LOGGER.debug("Default Settings:  {}".format(self.settings))
		
		# Check for user setting in default location
		userSettings = self.loadConfig(Path(Path.home().joinpath(self.settings["USER_DIR"]).joinpath(self.settings["USER_CONFIG"])))
		if type(userSettings) != dict:
			self.LOGGER.warning("User settings did not load.  Check log file")
		else:
			self.updateConfig(userSettings)
		self.LOGGER.debug("Settings after default user update:  {}".format(self.settings))
		
		# Check for custom settings path
		if "config" in kwargs:
			customSettings = self.loadConfig(kwargs["config"])
			if type(customSettings) != dict:
				self.LOGGER.error("Custom settings did not load")
			else:
				self.updateConfig(customSettings)
		self.LOGGER.debug("Settings after custom call update:  {}".format(self.settings))
		
		# If no custom config file declared, change any declared settings
		if "config" not in kwargs:
			for setting, value in kwargs.items():
				self.changeSetting(setting, value)
		self.LOGGER.debug("Settings after changing settings with __init__:  {}".format(self.settings))
		
		if board == None:
		#if "board" not in kwargs:
			self.LOGGER.error("No board was passed.  This will not work")
			sys.exit()
		else:
			self.board = board
		
		# Now the not so boring stuff
		self.tempSensors = {}
		self.groups = {}
		
		self._state = self.settings["DEFAULT_STATE"]
		self._mode = self.settings["DEFAULT_MODE"]
		
		self._cooling = False
		self._heating = False
		
	@property
	def state(self):
		return self._state
	
	@state.setter
	def state(self, state):
		if state in STATES:
			self._state = state
		else:
			LOGGER.debug("{} is not a valid STATE for Thermostat").format(state)
			LOGGER.debug("Defaulting to OFF state")
			self._state = "OFF"
	
	@property
	def mode(self):
		return self._mode
	
	@mode.setter
	def mode(self, change):
		if change:
			if self.mode == "AUTO":
				self._mode = "MANUAL"
			else:
				self._mode = "AUTO"
	
	@property
	def cooling(self):
		return self._cooling
	
	@cooling.setter
	def cooling(self, pin):
		boardReading = self.board.digital_read(pin)
		if boardReading:
			board.digital_write(pin, 0)
			self.LOGGER.info("Turned cooling off")
			self._cooling = False
		else:
			if self.state == "COOL":
				board.digital_write(pin, 1)
				self.LOGGER.info("Turned cooling on")
				self._cooling = True
			else:
				self.LOGGER.error("The thermostat is not in COOL mode")
		boardReading = self.board.digital_read(pin)
		
	@property
	def heating(self):
		return self._heating
	
	@heating.setter
	def heating(self, pin):
		boardReading = self.board.digital_read(pin)
		if boardReading:
			board.digital_write(pin, 0)
			self.LOGGER.info("Turned heating off")
			self._heating = False
		else:
			if self.state == "HEAT":
				board.digital_write(pin, 1)
				self.LOGGER.info("Turned heating on")
				self._heating = True
			else:
				self.LOGGER.error("The thermostat is not in HEAT mode")
		boardReading = self.board.digital_read(pin)

	def loadConfig(self, configFile):
		try:
			with open(configFile, "r") as config:
				return json.load(config)
		except FileNotFoundError as e:
			return self.LOGGER.error(e)
		except json.decoder.JSONDecodeError as e:
			return self.LOGGER.error(e)
	
	def updateConfig(self, configDict):
		if type(configDict) != dict:
			return None
		else:
			for setting, value in configDict.items():
				self.LOGGER.debug("Thermostat.updateConfig  -  Setting:  {}  Value:  {}".format(setting, value))
				if setting in self.settings:
					# Check for acceptable setting values when needed
					if self.checkSettingValue(setting, value):
						self.settings[setting] = value
				else:
					self.LOGGER.warning("{} is not a valid setting".format(setting))
	
	def changeSetting(self, setting, value):
		if setting in self.settings:
			if self.checkSettingValue(setting, value):
				self.settings[setting] = value
				self.LOGGER.debug("Setting {} changed to {}".format(setting, value))
				
	def checkSettingValue(self, setting, value):
		"""
		Used to varify that the given value for the setting will work with the 
		script.
		
		Add specific settings that need attention here with a return value of
		'False' if it is not satisfied.
		"""
		if setting == "USER_DIR" and Path.is_dir(Path(value)) == False:
			self.LOGGER.warning("{} is not a valid directory".format(value))
			return False
		if setting == "OUTPUT_FORMAT" and value != "F" and value != "C":
			self.LOGGER.warning("OUTPUT_FORMAT must be either 'F' or 'C'")
			return False
		return True
		
	def addSensor(self, sensor, location):
		"""
		sensor => A type of temperature sensor
		location => <str> Where the sensor is located.  Used for id
		"""
		self.tempSensors[location.upper()] = sensor
		self.LOGGER.debug("Sensor {} is added.  {}".format(location.upper(), type(sensor)))
		
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
			self.LOGGER.info("The group {} was created".format(name))
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
				self.LOGGER.info("Sensor {} is added to group {}".format(sensor, group))
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
		def getAverage(sensor):
			try:
				self.LOGGER.debug((sensor.moduleType, sensor.controlPin))
				temps = []
				i = 0
				reading = []
				while i < 100:
					#sensor.tempC = self.board.analog_read(sensor.controlPin)
					r = self.board.analog_read(sensor.controlPin)
					self.LOGGER.debug(r)
					reading.append(r)
					self.board.sleep(.005)
					i = i + 1
				sensor.tempC = sum(reading) / len(reading)
			except Exception as e:
				self.LOGGER.error("Bad reading pin {} -- {}".format(sensor.controlPin, e))
			return sensor.tempC
		
		area = area.upper()
		temp = None
		
		# Check the single areas first
		if area in self.tempSensors:
			temp = getAverage(self.tempSensors[area])
			
		# If not there, check if a group is asked for
		elif area in self.groups:
			tempList = []
			for sensor in self.groups[area]:
				tempList.append(getAverage(sensor))
			temp = sum(tempList) / len(tempList)
			
		else:
			self.LOGGER.warning("No area {} in senors or groups".format(area))
			return None
		
		self.LOGGER.debug("OUTPUT_FORMAT:  {}".format(self.settings["OUTPUT_FORMAT"]))
		
		if self.settings["OUTPUT_FORMAT"] == "F":
			temp = (temp * 1.8) + 32
		return temp

