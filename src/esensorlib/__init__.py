"""
SensorDevice
============

Provides a driver library with functions to configure and read sensor data
from an attached Epson Sensing System device. Low level register read/write
functions, higher level configuration functions, and burst reading of sensor
data is available.

Available subpackages
---------------------
mcore
mg320
mg354
mg364pdc0
mg364pdca
mg365pdf1
mg366pdg0
mg370pdf1
mg370pds0 

The above simply are stored in "model" directory and provides model specific
definitions and constants that is imported into the SensorDevice class
during initialization.

mcore contains bare minimum definitions which is imported into "mdef" namespace
early to be able to readback the device product ID, serial number, etc...
for auto detecting the device.

After the product ID is determined or overridden by user specified model,
the identified model subpackage is imported and overwrites the mcore namespace
"""