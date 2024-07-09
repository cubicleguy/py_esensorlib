
# Table of Contents
-------------
<!---toc start-->

* [Table of Contents](#table-of-contents)
* [Python Library for Epson Sensing System Devices](#python-library-for-epson-sensing-system-devices)
  * [Test Machines](#test-machines)
  * [Requirements](#requirements)
  * [Precautionary Notes](#precautionary-notes)
* [Installation](#installation)
* [SensorDevice Class Usage](#sensordevice-class-usage)
  * [Importing Package](#importing-package)
  * [Instantiating Class](#instantiating-class)
    * [Initialization Parameters](#initialization-parameters)
    * [IMU Instantiation Example](#imu-instantiation-example)
    * [ACCL Instantiation Example](#accl-instantiation-example)
    * [VIBE Instantiation Example](#vibe-instantiation-example)
  * [General Device Configuration](#general-device-configuration)
    * [IMU Configuration](#imu-configuration)
      * [Basic Configuration](#basic-configuration)
      * [Delta Angle / Velocity Configuration](#delta-angle--velocity-configuration)
      * [Attitude / Quaternion Configuration](#attitude--quaternion-configuration)
    * [ACCL Configuration](#accl-configuration)
    * [VIBE Configuration](#vibe-configuration)
  * [Entering Sampling Mode or Config Mode](#entering-sampling-mode-or-config-mode)
  * [Reading Sensor Data](#reading-sensor-data)
  * [SensorDevice Class Public Properties and Methods](#sensordevice-class-public-properties-and-methods)
    * [Public Properties](#public-properties)
    * [Settings in Status Property for IMU](#settings-in-status-property-for-imu)
    * [Settings in Status Property for ACCL](#settings-in-status-property-for-accl)
    * [Settings in Status Property for VIBE](#settings-in-status-property-for-vibe)
    * [Public Methods](#public-methods)
* [LoggerHelper Class Library Usage](#loggerhelper-class-library-usage)
  * [Importing Helper](#importing-helper)
  * [Instantiating Helper](#instantiating-helper)
  * [Setting Output to CSV File](#setting-output-to-csv-file)
  * [Writing Header](#writing-header)
  * [Writing Sample Data](#writing-sample-data)
  * [Writing Footer](#writing-footer)
  * [Printing Device Status](#printing-device-status)
  * [Helper Public Methods and Properties](#helper-public-methods-and-properties)
    * [Helper Public Properties](#helper-public-properties)
    * [Helper Public Method](#helper-public-method)

<!---toc end-->

# Python Library for Epson Sensing System Devices
-------------
This a general python library for evaluating the Epson Sensing System
devices and building evaluation software in a Python 3.x environment using the UART interface.

This package consists of two main parts:
  * *SensorDevice()* main class is composed of 5 subclasses *UartPort*, *RegInterface*, and one of the following *AcclFn*, *ImuFn*, or *VibFn* depending on the type of device
    * Primary purpose is to communicate and control the sensing device
    * Provide low-level functions to read/write registers
    * Provide functions to perform self-tests, software reset, flash-related functions
    * Provide functions to configure the device, and enter CONFIG/SAMPLING mode
    * Provide functions to read a burst sample when in SAMPLING mode
    * Expose properties to read various statuses and device model information
    * For more detailed information on using the *SensorDevice()* class refer to the README.md in the `src/esensorlib/` folder
  * A example logger comes in 3 variants based on the sensing device types: *accl_logger.py*, *imu_logger.py*, *vibe_logger.py*
    * It is intended as evaluation software and as a reference on how to use the *SensorDevice()* class to control and read sensor data
    * It uses the *LoggerHelper()* class for parsing and formatting sensor device status and sensor data
    * It is a command line driven application for configuring the device and logging the sensor output using arguments:
      * Serial port setting such as port name, baudrate
      * Time duration for collecting sensor data
      * Device configuration settings i.e. output rate, filter setting, model, etc
      * Flash operations
      * Output to console or CSV file
      * Some settings are unique to the specific device type

## Test Machines
  * Windows 10 Pro 64-bit, Intel Core i5-6500 @ 3.2GHz, 16GB RAM
  * Ubuntu Mate 22.04.3 LTS, RaspberryPi 4, 1.8 GB RAM
  * Ubuntu Mate 20.04.6 LTS, Intel Core i7 @ 2.0 GHz, 8GB RAM


## Requirements
  * Python 3.7+
  * Python packages (can be installed using [pypi](https://pypi.org)):
    * [serial](https://pypi.org/project/pyserial)
    * [tqdm](https://pypi.org/project/tqdm)
    * [tabulate](https://pypi.org/project/tabulate)
  * Epson sensing device connected to the host UART interface i.e. WIN/PC, Linux/PC or any embedded Linux system with serial port
    * M-G320PDG0, M-G354PDH0, M-G364PDC0, M-G364PDCA
    * M-G365PDC1, M-G365PDF1, M-G370PDF1, M-G370PDS0
    * M-G330PDG0, M-G366PDG0, M-G370PDG0, M-G370PDT0
    * M-G570PR20
    * M-A352AD10, M-A342VD10
  * Epson evaluation board
    * Epson USB evaluation board [M-G32EV041](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev041_e_rev201910.pdf)
  * Alternatively, a direct connection to host digital UART port (**NOTE:** 3.3V CMOS I/O signaling) using an adapter such as:
    * Epson PCB Breakout board [M-G32EV031](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev031_e_rev201910.pdf), or
    * Epson Relay board [M-G32EV051](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev051_e_rev201910.pdf)


## Precautionary Notes
For WIN/PC Only:

  * Before running the logger using the Epson IMU USB evaluation board (or equivalent FTDI USB-UART bridge IC) on a WIN/PC host, please set the Window's BM Options -> Latency Timer to 1msec
  * This is especially necessary for sampling rates faster than 125sps
  * By default the BM latency timer is set to 16ms, which may cause the serial handling on the PC to be sluggish and drop bytes during transmission
  * Change the serial port BM latency timer to 1msec in Windows 10, go to:
    * Control Panel -> Hardware and Sound -> Device Manager -> Ports (COM & LPT) -> USB Serial Port (COMx) -> Properties ->  Port Settings -> Advanced -> BM Options -> Latency Timer (msec) -> set to 1

For all systems:

  * Mount the Epson device to the USB Evalboard (or equivalent)
  * Connect the USB Evalboard to the PC via USB cable
  * Make sure both the host and device are unpowered when connecting the Epson device directly to a host UART interface

# Installation
--------------
  * The conventional method to install this package is to use [pip](https://pip.pypa.io/en/stable/)
  * Read more about [installing python packages](https://packaging.python.org/en/latest/tutorials/installing-packages/)
  * As an example, this package is installed from [PyPi](https://pypi.org/) using the following command:

```
python3 -m pip install esensorlib
```
  * Alternatively, if you downloaded the package to install from local hard drive, use the following command:

 For tar.gz file:
```
python3 -m pip install <path to file>/esensorlib-x.x.x.tar.gz
```
 For whl file:
```
python3 -m pip install <path to file>/esensorlib-x.x.x-py3-none-any.whl
```

# SensorDevice Class Usage
--------------------------
  * *SensorDevice()* is the main class in the *esensorlib* package to be used for communicating and controlling the Epson sensor device
  * Provides low-level functions to read/write registers
  * Provides functions to perform selftests, software reset, etc.
  * Provides flash-related functions
  * Provides functions to configure the device, or enter CONFIG/SAMPLING modes
  * Provides function to read a burst sample when in SAMPLING mode
  * Exposes properties to check device statuses, model information, burst configuration


## Importing Package
  * Assuming the *esensorlib* package has been properly installed (see [Installation](#Installation)), the package can be imported into the current python environment
  * *SensorDevice()* class and other supporting classes are contained in the files in directory *src/esensorlib*

```
from esensorlib import sensor_device
```

## Instantiating Class
 * After importing the package, instantiate the SensorDevice() class with parameters during initialization
 * Regardless of the device type (IMU, ACCL, VIBE) instantiation process is the same typically just specifying the `port`

### Initialization Parameters

Parameter    | Type         | Description / Comment
-------------|--------------|-----------------------
port         | str          | Name of the port i.e. on WIN/PC `com3`, Linux `/dev/ttyUSB0`
speed        | int          | UART baudrate (defaults to 460800) or SPI clock rate (not implemented yet)
if_type      | str          | `uart` (default) or `spi` (not implemented yet)
model        | str          | Set to `auto` (default) for auto-detect or specify to override with a specific model

### IMU Instantiation Example
```
dev = sensor_device.SensorDevice("com7")
Open:  com7 ,  460800
Detected: G366PDG0
```

### ACCL Instantiation Example
```
dev = sensor_device.SensorDevice("com11")
Open:  com11 ,  460800
Detected: A352AD10
```

### VIBE Instantiation Example
```
dev = sensor_device.SensorDevice("com12")
Open:  com12 ,  460800
Detected: A342VD10
```

## General Device Configuration
  * The instantiated *SensorDevice()* object is then configured by passing a series of keyword arguments or as an unpacked dict when calling the *set_config()* method
  * Each type of device have some common arguments and unique arguments specific to the device type
  * If no configuration parameters are passed when calling the *set_config()* method, defaults are used

### IMU Configuration
  * The *set_config()* method for IMU configuration is sequenced into calling 3 internal methods:
    * basic settings - core settings for sensor output
    * delta angle / velocity settings - optional additional settings for delta angle / velocity output
    * attitude / quaternion settings - optional additional settings for attitude and/or quaternion output
  * **NOTE:** Delta angle / velocity and attitude / quaternion can not both be enabled at the same time
  * By default delta angle / velocity and attitude / quaternion is disabled when keyword parameters related to these functions are not provided to the *set_config()* method
  * If no parameters are passed to *set_config()*, then the following defaults are used


**Basic Defaults**

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
dout_rate       | 200          | 200 Hz
filter_sel      | None         | auto-select Moving Average TAP=16
ndflags         | False        | Do not include ND/EA FLAGS field
tempc           | False        | Do not include temperature sensor field
counter         | ""           | Do not include counter field
chksm           | False        | Do not include 16-bit checksum field
auto_start      | False        | Disable AUTO_START function
is_32bit        | True         | All sensor data is 32-bit resolution i.e. Gyro, Accl, Temperature, etc
a_range         | False        | Set accelerometer output range to 8G (ignored for models that do not selectable range i.e. 16G)
ext_trigger     | False        | Disable external trigger
uart_auto       | True         | Enable UART_AUTO mode

**IMU Delta Angle / Velocity Defaults**

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
dlta            | False        | Delta Angle output disabled
dltv            | False        | Delta Velocity output disabled
dlta_sf_range   | 12           | Delta Angle Scale Factor setting is 12
dltv_sf_range   | 12           | Delta Velocity Scale Factor setting is 12

**Attitude / Quaternion Defaults**

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
atti            | False        | Attitude output disabled
atti_mode       | "euler"      | Attitude mode is Euler mode
atti_conv       | 0            | Attitude conversion mode is 0
atti_profile    | "modea"      | Attitude Motion Profile is ModeA
qtn             | False        | Quaternion output is disabled


#### Basic Configuration
  * Create a dict with desired basic settings and pass it as keyword parameters or as an unpacked dict when calling the *set_config()* method
  * **NOTE:** Not all key, value parameter pairs need to be provided when passing to *set_config()*

Below example performs basic configuration and reads back the devices status properties.

```
>>> my_cfg = {
...     "dout_rate": 250,
...     "filter_sel": "mv_avg16",
...     "ndflags": True,
...     "tempc": True,
...     "counter": "sample",
...     "chksm": False,
...     "is_32bit": True,
...     "a_range": 0,
...     "uart_auto": True,
... }
>>> dev.set_config(**my_cfg)
Configured basic
Delta angle / velocity function disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> dev.status
mappingproxy({'dout_rate': 250, 'filter_sel': 'MV_AVG16', 'ndflags': True, 'tempc': True, 'counter': 'sample', 'chksm': False, 'auto_start': False, 'is_32bit': True, 'a_range': 0, 'ext_trigger': False, 'uart_auto': True, 'is_config': True, 'dlta': False, 'dltv': False, 'dlta_sf_range': 12, 'dltv_sf_range': 12, 'atti': False, 'atti_mode': 'euler', 'atti_conv': 0, 'atti_profile': 'modea', 'qtn': False, 'drdy_pol': True})
```

#### Delta Angle / Velocity Configuration
  * Create a dict which also includes delta angle/velocity settings and pass it as keyword parameters or as an unpacked dict when calling the *set_config()* method
  * **NOTE:** Not all IMU models support delta angle / velocity output

Below example performs basic, delta angle / velocity configuration and reads back the devices status properties.

```
>>> my_cfg = {
...     "dout_rate": 250,
...     "filter_sel": "mv_avg16",
...     "ndflags": True,
...     "tempc": True,
...     "counter": "sample",
...     "chksm": False,
...     "is_32bit": True,
...     "a_range": 0,
...     "uart_auto": True,
...     "dlta": True,
...     "dltv": True,
...     "dlta_sf_range": 4,
...     "dltv_sf_range": 4,
... }
>>> dev.set_config(**my_cfg)
Configured basic
Configured delta angle / velocity
Attitude or quaternion disabled. Bypassing.
>>> dev.status
mappingproxy({'dout_rate': 250, 'filter_sel': 'MV_AVG16', 'ndflags': True, 'tempc': True, 'counter': 'sample', 'chksm': False, 'auto_start': False, 'is_32bit': True, 'a_range': 0, 'ext_trigger': False, 'uart_auto': True, 'is_config': True, 'dlta': True, 'dltv': True, 'dlta_sf_range': 4, 'dltv_sf_range': 4, 'atti': False, 'atti_mode': 'euler', 'atti_conv': 0, 'atti_profile': 'modea', 'qtn': False, 'drdy_pol': True})
```

#### Attitude / Quaternion Configuration
  * Create a dict which also includes attitude / quaternion settings and pass it as keyword parameters or as an unpacked dict when calling the *set_config()* method
  * **NOTE:** Not all IMU models support attitude or quaternion output

Below example performs basic and attitude / quaternion configuration and reads back the devices status properties.

```
>>> my_cfg = {
...     "dout_rate": 125,
...     "filter_sel": "mv_avg32",
...     "ndflags": True,
...     "tempc": True,
...     "counter": "sample",
...     "chksm": False,
...     "is_32bit": True,
...     "a_range": 0,
...     "uart_auto": True,
...
...     "atti": True,
...     "mode": "euler",
...     "conv": 0,
...     "profile": "modea",
...     "qtn": True,
... }
>>> dev.set_config(**my_cfg)
Configured basic
Delta angle / velocity function disabled. Bypassing.
Configured attitude / quaternion
>>> dev.status
mappingproxy({'dout_rate': 125, 'filter_sel': 'MV_AVG32', 'ndflags': True, 'tempc': True, 'counter': 'sample', 'chksm': False, 'auto_start': False, 'is_32bit': True, 'a_range': 0, 'ext_trigger': False, 'uart_auto': True, 'is_config': True, 'dlta': False, 'dltv': False, 'dlta_sf_range': 12, 'dltv_sf_range': 12, 'atti': True, 'atti_mode': None, 'atti_conv': 0, 'atti_profile': 'modea', 'qtn': True, 'drdy_pol': True})
```

### ACCL Configuration
  * The ACCL configuration is executed when calling *set_config()*
  * If no parameters are passed to *set_config()*, then the following defaults are used

**ACCL Defaults**

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
dout_rate       | 200          | 200 Hz
filter_sel      | None         | Auto-select K512_FC60
ndflags         | False        | Do not include ND/EA FLAGS field
tempc           | False        | Do not include temperature sensor field
counter         | False        | Do not include counter field
chksm           | False        | Do not include 16-bit checksum field
auto_start      | False        | Disable AUTO_START function
ext_trigger     | False        | Disable external trigger
uart_auto       | True         | Enable UART_AUTO mode
drdy_pol        | True         | DRDY output signal is active HIGH
tilt            | 0            | 3-bit enable are 000b for TILT X, Y, Z

  * Create a dict with desired settings and pass it as keyword parameters or as an unpacked dict when calling the *set_config()* method
  * **NOTE:** Not all key, value parameter pairs need to be included when passing to *set_config()*

Below example performs configuration and reads back the devices status properties.

```
>>> my_cfg = {
...     "dout_rate": 100,
...     "filter_sel": "k512_fc16",
...     "ndflags": True,
...     "tempc": True,
...     "counter": True,
...     "chksm": False,
...     "uart_auto": True,
... }
>>> dev.set_config(**my_cfg)
Configured
>>> dev.status
mappingproxy({'dout_rate': 100, 'filter_sel': 'K512_FC16', 'ndflags': True, 'tempc': True, 'counter': True, 'chksm': False, 'auto_start': False, 'ext_trigger': False, 'uart_auto': True, 'drdy_pol': True, 'tilt': 0, 'is_config': True})
```

### VIBE Configuration
  * The VIBE configuration is executed when calling *set_config()*
  * If no parameters are passed to *set_config()*, then the following defaults are used

**VIBE Defaults**

Key               | Value        | Description / Comment
------------------|--------------|-----------------------
output_sel        | VELOCITY_RMS | Sensor output type (velocity_raw, velocity_rms, velocity_pp, displacement_raw, displacement_rms, displacement_pp)
dout_rate_rmspp   | 1            | Output rate (depends on output_sel)
update_rate_rmspp | 4            | Update rate determines the # of samples used for internal calculation of RMS or peak-peak for velocity or displacement
ndflags           | False        | Do not include NDFLAGS field
tempc             | False        | Do not include temperature sensor field
sensx             | True         | Include X-axis sensor field
sensy             | True         | Include Y-axis sensor field
sensz             | True         | Include Z-axis sensor field
counter           | False        | Do not include counter field
chksm             | False        | Do not include 16-bit checksum field
is_tempc16        | True         | Temperature sensor data is 16-bit
auto_start        | False        | Disable AUTO_START function
uart_auto         | True         | Enable UART_AUTO mode
ext_pol           | False        | EXT input signal is active HIGH

 * Create a dict with desired settings and pass it as keyword parameters or as an unpacked dict when calling the *set_config()* method
 * **NOTE:** Not all key, value parameter pairs need to be included when passing to *set_config()*

Below example performs basic configuration and reads back the devices status properties.

```
>>> my_cfg = {
... "output_sel": "disp_pp",
... "dout_rate_rmspp": 1,
... "update_rate_rmspp": 4,
... "ndflags": True,
... "tempc": True,
... "counter": True,
... "is_tempc16": True,
... "uart_auto": True,
... }
>>> dev.set_config(**my_cfg)
Configured
>>> dev.status
mappingproxy({'output_sel': 'DISP_PP', 'dout_rate_rmspp': 1, 'update_rate_rmspp': 4, 'ndflags': True, 'tempc': True, 'sensx': True, 'sensy': True, 'sensz': True, 'counter': True, 'chksm': False, 'is_tempc16': True, 'auto_start': False, 'uart_auto': True, 'ext_pol': False, 'is_config': True, 'drdy_pol': True})
```

## Entering Sampling Mode or Config Mode
  * By default, the sensor device should start in CONFIG mode to allow *set_config()* method to program registers
  * After the device has been configured, it can be put into SAMPLING mode to allow read back of sensor data
  * Call the method `goto('sampling')` to place the device in SAMPLING mode (from CONFIG mode)
  * **NOTE:** When the device is in SAMPLING mode with *UART_AUTO* enabled, the user can only read device sensor data, go to CONFIG mode, or issue a software reset
  * Call the method `goto('config')` to place the device in CONFIG mode (from SAMPLING mode)


## Reading Sensor Data
  * When the device is in SAMPLING mode, calling *read_sample()* will return a tuple containing scaled sensor values
  * When the device is in SAMPLING mode, calling *read_sample_unscaled()* will return a tuple containing unscaled sensor values
  * The type of fields returned in the sensor data depends on the configuration of the device by *set_config()*
  * To check the burst field names and data ordering of the sensor data, read the *burst_fields* property of the *SensorDevice()*

```
>>> from esensorlib import sensor_device
>>> imu = sensor_device.SensorDevice('com7')
Detected: G366PDG0
>>> imu.set_config()
Configured basic
Delta angle / velocity disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> imu.goto('sampling')
>>> imu.read_sample()
(0.96928175, -0.32923658, -0.1102651, 11.83782196, -78.78177643, 1006.86695099)
>>> imu.burst_fields
('gyro32_X', 'gyro32_Y', 'gyro32_Z', 'accl32_X', 'accl32_Y', 'accl32_Z')
>>> imu.read_sample_unscaled()
(2451156, -1951249, -400732, 3177658, -20486224, 263143144)
```

## SensorDevice Class Public Properties and Methods
  * *SensorDevice()* class is the primary class intended for the user to instantiate and use
  * Other classes are used internally for composing the *SensorDevice()* and is not intended to be instantiated directly by the user

### Public Properties

Key          | Type         | Description / Comment
-------------|--------------|-----------------------
info         | mappingproxy | Device info such as port, if_type, model
status       | mappingproxy | Device configuration status depending on device type. Refer to Status Attribute for each device type below
burst_out    | mappingproxy | Burst output settings such as ndflags, tempc, gyro, accl, dlta, dltv, qtn, atti, gpio, counter, chksm depending on device type
burst_field  | tuple        | Fields contained in sensor burst read
mdef         | object       | Object containing device specific definitions, register addresses, and constants

### Settings in Status Property for IMU

Parameter     | Type         | Description / Comment
--------------|--------------|-----------------------
dout_rate     | int          | Output rate setting in Hz
filter_sel    | str          | Filter setting as a string parameter
ndflags       | bool         | True=ND/EA flag enabled in burst
tempc         | bool         | True=temperature data enabled in burst
counter       | str          | Set to "" to disable counter, otherwise enable counter field in burst by setting to "reset" or "sample" counter
chksm         | bool         | True=16-bit checksum enabled in burst
auto_start    | bool         | True=AUTO_START is enabled
is_32bit      | bool         | True=sensor data is 32-bit resolution (otherwise it is 16-bit)
a_range       | bool         | True=16G accelerometer range for IMU devices that support it
ext_trigger   | bool         | True=external trigger is enabled
uart_auto     | bool         | True=UART_AUTO mode is enabled (recommended)
is_config     | bool         | True=device is in CONFIG mode
dlta          | bool         | True=delta angle field enabled in burst for IMUs that support it
dltv          | bool         | True=delta velocity field enabled in burst for IMUs that support it
dlta_sf_range | int          | DLTA_RANGE_CTRL (scale factor) setting for IMUs that support it
dltv_sf_range | int          | DLTV_RANGE_CTRL (scale factor) setting for IMUs that support it
atti          | bool         | True=attitude fields ANG1, ANG2, ANG3 are enabled in burst for IMUs that support it
atti_mode     | str          | If attitude enabled, indicates "euler" or "incl" mode for IMUs that support it
atti_conv     | int          | Indicates attitude axis conversion for ANG1, ANG2, ANG3 for IMUs that support it
atti_profile  | str          | Indicates attitude motion profile "modea", "modeb", or "modec" for IMUs that support it
qtn           | bool         | True=quaternion fields q0, q1, q2, q3, q4 are enabled in burst for IMUs that support it
verbose       | bool         | True=debug messages display

### Settings in Status Property for ACCL

Parameter     | Type         | Description / Comment
--------------|--------------|-----------------------
dout_rate     | int          | Output rate setting in Hz
filter_sel    | str          | Filter setting as a string parameter
ndflags       | bool         | True=ND/EA flag enabled in burst
tempc         | bool         | True=temperature data enabled in burst
counter       | bool         | True=counter field is enabled in burst
chksm         | bool         | True=16-bit checksum enabled in burst
auto_start    | bool         | True=AUTO_START is enabled
ext_trigger   | bool         | True=external trigger is enabled
uart_auto     | bool         | True=UART_AUTO mode is enabled (recommended)
drdy_pol      | bool         | True=DRDY output pin is active HIGH
tilt          | int          | 3-bit enable to designate X, Y, Z axis to output tilt instead of acceleration
is_config     | bool         | True=device is in CONFIG mode
verbose       | bool         | True=debug messages displayed during program operation

### Settings in Status Property for VIBE

Parameter         | Type         | Description / Comment
------------------|--------------|-----------------------
output_sel        | str          | Indicates the output selection type as velocity_raw, velocity_rms, velocity_pp, disp_raw, disp_rms, or disp_pp
dout_rate_rmspp   | int          | Output rate setting as register value (ignored for velocity_raw or disp_raw)
update_rate_rmspp | int          | Update rate setting for internally calculating RMS or Peak-Peak as register value (ignored for velocity_raw or disp_raw)
ndflags           | bool         | True=ND/EA flag enabled in burst
tempc             | bool         | True=temperature data enabled in burst
sensx             | bool         | True=X-axis sensor data field is enabled in burst
sensy             | bool         | True=Y-axis sensor data field is enabled in burst
sensz             | bool         | True=Z-axis sensor data field is enabled in burst
counter           | bool         | True=counter field is enabled in burst
chksm             | bool         | True=16-bit checksum enabled in burst
is_tempc16        | bool         | True=temperature data is 16-bit (otherwise it is 8-bit)
auto_start        | bool         | True=AUTO_START is enabled
uart_auto         | bool         | True=UART_AUTO mode is enabled (recommended)
ext_pol           | bool         | True=EXT input pin is active LOW
is_config         | bool         | True=device is in CONFIG mode
verbose           | bool         | True=debug messages displayed during program operation

### Public Methods

Method                                | Description / Comment
--------------------------------------|-------------------------------
get_reg(winnum, regaddr)              | Perform 16-bit read from specified WIN_ID and register address
set_reg(winnum, regaddr, write_byte)  | Perform 8-bit write to WIN_ID and register address with specified byte
get_regdump(columns)                  | Print out all registers (specify number of columns to format to)
set_config(key=value,...)             | Configure device settings with key, value arguments
init_check()                          | Read status for hardware error (HARD_ERR)
do_selftest()                         | Perform selftest and check for errors (ST_ERR)
do_softreset()                        | Perform software reset
do_flashtest()                        | Perform flash test and check for errors (FLASH_ERR)
backup_flash()                        | Backup current register settings to flash and check for errors (FLASH_BU_ERR)
init_backup()                         | Clear flash setting to factory defaults
goto(mode, post_delay)                | Put device in CONFIG or SAMPLING mode and delay for specified time(post_delay) in seconds
get_mode()                            | Read current mode status (CONFIG or SAMPLING)
read_sample()                         | Read a set of burst data from device with scale factor applied
read_sample_unscaled()                | Read a set of burst data from device without scale factor applied

# LoggerHelper Class Library Usage
-----------------------------------
  * This *LoggerHelper()* class is used by the *xxxx_logger.py* to handle formatting of the sensor data for output to console or csv file
  * NOTE: *LoggerHelper()* is instantiated and initialized by passing in a configured *SensorDevice()* object as a parameter

## Importing Helper
  * NOTE: Before using *LoggerHelper()* class library, a *SensorDevice()* should be instantiated from the *esensorlib* package and configured
  * *LoggerHelper()* class is located in the *helper.py* file in the *example* subdirectory where the *esensorlib* package is installed in your system (i.e. <python>\Lib\site-packages\esensorlib\example)

```
from esensorlib.example import helper
```

## Instantiating Helper
  * After importing the *helper.py*, instantiate a LoggerHelper class while passing the *SensorDevice()* instance

```
>>> from esensorlib import sensor_device
>>> dev = sensor_device.SensorDevice('com7')
Detected: G366PDG0
>>> dev.set_config()
Configured basic
Delta angle / velocity disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> from esensorlib.example import helper
>>> log = helper.LoggerHelper(sensor=dev)
```

## Setting Output to CSV File
  * By default, *LoggerHelper()* class methods *write()*, *write_header()*, *write_footer()* will send output to the console
  * To redirect to a CSV file instead of the console, call the *LoggerHelper()* *set_writer()* method specifying the *to* parameter
  * In the *to* parameter pass a list of strings which will combined with "_" to create a filename appended with *.csv*
  * The *set_writer* method will also append device info and settings from *SensorDevice()* when creating the filename
```
>>> from esensorlib import sensor_device
>>> dev = sensor_device.SensorDevice('com7')
Detected: G366PDG0
>>> dev.set_config()
Configured basic
Delta angle / velocity disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> from esensorlib.example import helper
>>> log = helper.LoggerHelper(sensor=dev)
>>> log.set_writer(to=['my_csv'])
```

  * If output is currently directed to a csv file, to close the file and redirect back to the console, call the *LoggerHelper()* *set_writer()* method without a parameter
```
>>> log.set_writer()
CSV closed
```

## Writing Header
  * To write header rows containing device & configuration information to the csv file or console call the *write_header()* method
  * **NOTE:** The *SensorDevice()* should be properly configured by *set_config()* method before calling the *write_header()* method
```
>>> from esensorlib import sensor_device
>>> dev = sensor_device.SensorDevice('com7')
Detected: G366PDG0
>>> dev.set_config()
Configured basic
Delta angle / velocity disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> from esensorlib.example import helper
>>> log = helper.LoggerHelper(sensor=dev)
>>> log.write_header()
Start Log: 2023-02-23 17:06:39.331964
#Log created in Python,,,Sample Rate,200,Filter Cfg,MV_AVG16,,,
#Creation Date:,2023-02-23 17:06:39.331964,PROD_ID=G366PDG0,VERSION=373,SERIAL_NUM=T1000062,,,,,,
#Scaled Data,SF_GYRO=+0.01515152 / 2^16 (deg/s)/bit,SF_ACCL=+0.25000000 / 2^16 mg/bit,SF_TEMPC=+0.00390625 / 2^16 degC/bit
Sample No.,Flags[hex],Ts[deg.C],Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG],Counter[dec]
>>>
```

## Writing Sample Data
  * To write a burst of sensor samples to the console or csv file call the *write()* method using the return values from the *SensorDevice()* *read_sample()* method
  * **NOTE:** The device must be in SAMPLING mode before calling the *read_sample()* method
  * **NOTE:** The *SensorDevice()* should be be properly configured by *set_config()* method before calling the *read_sample()* method
```
>>> from esensorlib import sensor_device
>>> dev = sensor_device.SensorDevice('com7')
Detected: G366PDG0
>>> dev.set_config()
Configured basic
Delta angle / velocity disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> dev.goto('sampling')
>>> from esensorlib.example import helper
>>> log = helper.LoggerHelper(sensor=dev)
>>> log.write(dev.read_sample())
>>>
```

  * To write 1000 bursts of sensor samples to the csv file call the *write()* method with the return values from the *SensorDevice()* *read_sample()* method
```
>>> from esensorlib import sensor_device
>>> dev = sensor_device.SensorDevice('com7')
Detected: G366PDG0
>>> dev.set_config()
Configured basic
Delta angle / velocity disabled. Bypassing.
Attitude or quaternion disabled. Bypassing.
>>> dev.goto('sampling')
>>> from esensorlib.example import helper
>>> log = helper.LoggerHelper(sensor=dev)
>>> for i in range(1000):
...   log.write(dev.read_sample())
>>>
```

## Writing Footer
  * To write footer (device and configuration status) rows to the csv file or console call the *write_footer()* method
  * **NOTE:** The *SensorDevice()* should be be properly configured by *set_config()* method before calling the *write_footer()* method
```
>>> log.write_footer()
#Log End,2023-02-23 17:09:06.114034,,,,,,,,
#Sample Count,000000000,,,,,,,,
#Output Rate,200,sps,,Filter Setting,MV_AVG16,,,,
```

## Printing Device Status
  * To print to console current date/time and device, and configuration info call the *get_dev_info()* method
  * **NOTE:** The *SensorDevice()* should be be properly configured by *set_config()* method before calling the *get_dev_info()* method
```
>>>log.get_dev_info()
-----------------  -----------------  ----------------  ------------
Date: 2023-02-23   Time: 21:04:07
-----------------  -----------------  ----------------  ------------
PROD_ID: G370PDS0  VERSION: 29FD      SERIAL: W0000015
DOUT_RATE: 200.0   FILTER: K128_FC25
NDFLAG: True       TEMPC: True        COUNTER: Sample   CHKSUM: True
DLT: False         ATTI: False        QTN: False        BIT32: True
-----------------  -----------------  ----------------  ------------
```

## Helper Public Methods and Properties

### Helper Public Properties
  * These properties are mirrors of the *SensorDevice()* properties propagated to the *LoggerHelper()* class

Attribute       | Type         | Description / Comment
----------------|--------------|-----------------------
dev_info        | mappingproxy | Device info such as prod_id, version_id, serial_id, comport, model
dev_status      | mappingproxy | Device configuration status *SensorDevice()* *status*
dev_burst_out   | mappingproxy | Burst output status of *SensorDevice()* *burst_out* properties
dev_burst_fields| tuple        | Ordered list of burst field names for a burst read *SensorDevice()* *read_sample()*
dev_mdef        | object       | Object that stores the current model's specific definitions and constants of *SensorDevice()* *mdef*

### Helper Public Method

Method                                | Description / Comment
--------------------------------------|-------------------------------
set_writer(to)                        | Set the writer to csv file with filename derived from list of strings (parameter) or to the console (no parameter)
write(sample_data)                    | Send specified tuple of sample_data to csv file or console
write_header(scale_mode, start_date)  | Write header information to csv file or console
write_footer(end_date)                | Write footer information to csv file or console
get_dev_status()                      | Send current info about device and configuration to console
clear_count()                         | Clear the internal sample counter which increments on every call to *write()*
