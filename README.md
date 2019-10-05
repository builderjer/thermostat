# Personal Thermostat
Idea of building a smart thermostat with a raspberry pi or arduino.  Either way, it needs the same interfaces and such.

## Web interface
What does this need to show?  Who can adjust it?

  * Indoor temp
  * Outdoor temp
  * Projected high/low temp
  * Current setting
  * Adjust buttons  - Password protected

## Control functions
What does this need to do?

  * Poll an outdoor temp sensor, or weather API
  * Poll multiple indoor temp sensors to get an average temp
  * Get current desired setting
  * Poll for occupancy
    1.  Ping for WiFi
    2.  Ping for Bluetooth
    3.  Check motion detectors
  * Check configuration for specific settings
    1.  Should it stay activated
    2.  Should it turn on or off at specific time
    3.  Should it be heating or cooling
