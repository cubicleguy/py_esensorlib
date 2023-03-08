# Disclaimer:
--------------
MIT License

Copyright (c) 2023, Seiko Epson Corporation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# Table of Contents
-------------
1. [Python Library for Epson Sensing System Devices](#Python-Library-for-Epson-Sensing-System-Devices)
2. [Test machine](#Test-machine)
3. [Requirements](#Requirements)
4. [Precautionary Notes](#Precautionary-Notes)
5. [Installation](#Installation)
6. [Logger Usage](#Logger-Usage)
7. [SensorDevice Class Library Usage](#SensorDevice-Class-Library-Usage)
8. [LoggerHelper Class Library Usage](#LoggerHelper-Class-Library-Usage)
9. [File Listing](#File-Listing)
10. [Change Record](#Change-Record)


# Python Library for Epson Sensing System Devices
-------------
This a general python library for developing and evaluating the Epson Sensing System
Devices in a Python 3.x environment using the UART interface

This package consists of two parts:
 * *SensorDevice* library class which allows the user to communicate and control the sensing device
   * Provides low-level functions to read/write registers
   * Provides functions to perform selftests, software reset,
   * Provides flash-related functions
   * Provides functions to configure the device, and enter CONFIG/SAMPLING modes
   * Provides function to read a burst sample when in SAMPLING mode
   * Exposes read-only property attributes to read various statuses and model information
 * Logger script *logger.py* which is built around the *LoggerHelper* library class and intended as reference on how to use the *SensorDevice* class
   * Command Line driven application with full set of arguments for configuring the device and logger output
   * serial port setting, i.e. port, baudrate
   * logging duration
   * device configuration, i.e. output rate, filter setting, model, etc
   * flash operations
   * output to stdout or CSV file


# Test machine
-------------
 * Windows 10 Pro 64-bit
 * Intel Core i5-6500 @ 3.2GHz, 16GB RAM


# Requirements
-------------
 * Python 3.7+
 * Python packages (can be installed using [pypi](https://pypi.org):
	* [serial](https://pypi.org/project/pyserial)
	* [tqdm](https://pypi.org/project/tqdm)
	* [tabulate](https://pypi.org/project/tabulate)
 * Epson sensing device connected to the host UART interface i.e. WIN/PC, Linux/PC or any embedded system with serial port
  * M-G320PDG0, M-G354PDH0, M-G364PDC0, M-G364PDCA
	* M-G365PDC1, M-G365PDF1, M-G370PDF1
	* M-G330PDG0, M-G366PDG0, preliminary (M-G370PDG0, M-G370PDT0)
 * Epson USB evaluation board [M-G32EV041](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev041_e_rev201910.pdf)


# Precautionary Notes
------------
For WIN/PC:

 * Before running the program, please ensure the Epson IMU USB evaluation port is plugged into the USB port
and the BM Options -> Latency Timer to 1msec
 * This is especially necessary to support sampling rates > 125sps
 * By default, the Latency Timer is set to 16ms unless changed
 * A 16msec Latency Timer may cause the serial link to drop some bytes during transmission
 * Change the serial port Latency Timer to 1msec in Windows 10, go to:
   * Control Panel -> Hardware and Sound -> Device Manager -> Ports (COM & LPT) -> USB Serial Port (COMx) -> Properties ->  Port Settings -> Advanced -> BM Options -> Latency Timer (msec) -> set to 1

For all systems:

 * Connect IMU to the USB Evalboard
 * Connect the USB Evalboard to the PC via USB cable

# Installation
--------------
 * The conventional method to install this package is to use [pip](https://pip.pypa.io/en/stable/)
 * Read more about [installing python packages](https://packaging.python.org/en/latest/tutorials/installing-packages/)
 * As an example, this package is installed from [PyPi](https://pypi.org/) using the following command:
```
python3 -m pip install esensorlib
```
 * Alternatively, if you downloaded the package locally to install, use the following commad:

 For tar.gz file:
 ```
 python3 -m pip install <path to file>/esensorlib-x.x.x.tar.gz
 ```
 For whl file:
 ```
 python3 -m pip install <path to file>/esensorlib-x.x.x-py3-none-any.whl
 ```


# Logger Usage
--------------
NOTE: Use the -h switch for the help menu

## Sending Sensor Data:

Open a command prompt and run the logger.py python script with the appropriate command line switches:
1. Select COM port with -s switch (i.e., "-s com6")
2. Select IMU model --model switch (i.e., "--model G370PDF1") or let the software auto-detect by not specifying this switch
3. Select the desired output rate with the --drate switch (i.e., "--drate 200" for 200Hz)
4. Select the desired filter setting with the --filter switch (i.e., "--filter K128_FC50") or let the software choose a valid moving average filter by not specifying this switch
5. Select the desired time duration in seconds with the --secs switch (i.e., "--secs 60") or number of samples with the --samples switch (i.e., "--samples 5000")
6. Select if the sensor data to be written to a CSV file with the --csv switch

### To output to console:
```
python3 logger.py -s com6 --drate 200 --filter K128_FC25 --secs 100
Model not specified, attempting to auto-detect
Detected: G370PDS0
Attitude or Quaternion not supported.
Start Log: 2023-02-23 20:58:50.056749
#Log created in Python,,,Sample Rate,200.0,Filter Cfg,k128_fc25,,,
#Creation Date:,2023-02-23 20:58:50.056749,PROD_ID=G370PDS0,VERSION=29FD,SERIAL_NUM=W0000015,,,,,,
#Scaled Data,SF_GYRO=+0.00666667 / 2^16 (deg/s)/bit,SF_ACCL=+0.40000000 / 2^16 mg/bit
Sample No.,Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG]
0,0.05045105,0.61051066,-0.05250793,12.31838989,10.00319214,6.27946777
1,0.05047262,0.61033732,-0.05248606,12.30870361,9.88743286,5.97288818
2,0.05077443,0.60953054,-0.05238241,12.26567383,9.36682739,4.59973145
3,0.05161662,0.60802389,-0.05219604,12.18662109,8.40490723,2.07177734
.
.
.
74,0.12697825,0.04116516,0.00080088,-17.93453979,-346.55579834,-940.4909668
75,0.20138194,0.05390228,0.00061808,-17.59989014,-347.20582886,-940.01728516
76,0.25439443,0.06177979,0.00140025,-17.30096436,-348.21726074,-939.44940796
77,0.28146159,0.0647109,0.00308879,-17.08118286,-349.47402954,-938.86427002
CTRL-C: Exiting
Stop reading sensor
#Log End,2023-02-21 21:31:11.226411,,,,,,,,
#Sample Count,000000078,,,,,,,,
#Data Rate,200.0,sps,,Filter Cfg,k128_fc25,,,,
-----------------  -----------------  ----------------  -------------
Date: 2023-02-23   Time: 20:58:50
-----------------  -----------------  ----------------  -------------
PROD_ID: G370PDS0  VERSION: 29FD      SERIAL: W0000015
DOUT_RATE: 200.0   FILTER: K128_FC25
NDFLAG: False      TEMPC: False       COUNTER: None     CHKSUM: False
DLT: False         ATTI: False        QTN: False        BIT32: True
-----------------  -----------------  ----------------  -------------
Close:  com6 ,  460800 baud
```

### To output to csv file:
```
python3 logger.py -s com6 --drate 200 --filter K128_FC25 --secs 10 --csv
Model not specified, attempting to auto-detect
Detected: G370PDS0
Attitude or Quaternion not supported.
Start Log: 2023-02-23 21:00:49.560112
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2000/2000 [00:09<00:00, 202.90it/s]
-----------------  -----------------  ----------------  -------------
Date: 2023-02-23   Time: 21:00:59
-----------------  -----------------  ----------------  -------------
PROD_ID: G370PDS0  VERSION: 29FD      SERIAL: W0000015
DOUT_RATE: 200.0   FILTER: K128_FC25
NDFLAG: False      TEMPC: False       COUNTER: None     CHKSUM: False
DLT: False         ATTI: False        QTN: False        BIT32: True
-----------------  -----------------  ----------------  -------------
Close:  com6 ,  460800 baud
CSV closed
```

## Reading Out All the Current IMU Registers

Open a command prompt and run the *logger.py* python script with the appropriate command line switches:
1. Select COM port with -s switch (i.e., "-s COM6")
2. Select IMU model --model switch (i.e., "--model G370PDF1") or do not specify the switch to let the software auto-detect
3. Select --dump_reg switch (i.e., "--dump_reg")

```
python3 logger.py -s com6 --dump_reg
D:\projects\py_esensorlib\src\logger>logger.py -s com6 --dump_reg
Model not specified, attempting to auto-detect
Detected: G370PDS0
Reading registers:
REG[0x02, (W0)] => 0x0400       REG[0x04, (W0)] => 0x0000       REG[0x06, (W0)] => 0x0100
REG[0x08, (W0)] => 0x0000       REG[0x0A, (W0)] => 0x2729       REG[0x0C, (W0)] => 0x3001
REG[0x0E, (W0)] => 0x0C4F       REG[0x10, (W0)] => 0xBD09       REG[0x12, (W0)] => 0xFFDC
REG[0x14, (W0)] => 0x73E4       REG[0x16, (W0)] => 0xFFFB       REG[0x18, (W0)] => 0x4A63
REG[0x1A, (W0)] => 0x0000       REG[0x1C, (W0)] => 0x5874       REG[0x1E, (W0)] => 0xFFD1
REG[0x20, (W0)] => 0xFD58       REG[0x22, (W0)] => 0xFCA4       REG[0x24, (W0)] => 0x9056
REG[0x26, (W0)] => 0xF6CD       REG[0x28, (W0)] => 0x588D       REG[0x2A, (W0)] => 0x0000
.
.
.
REG[0x48, (W1)] => 0x4000       REG[0x4A, (W1)] => 0x4000       REG[0x4C, (W1)] => 0x0000
REG[0x4E, (W1)] => 0x0000       REG[0x50, (W1)] => 0x0000       REG[0x52, (W1)] => 0x4000
REG[0x54, (W1)] => 0x0000       REG[0x56, (W1)] => 0x0000       REG[0x58, (W1)] => 0x0000
REG[0x5A, (W1)] => 0x4000       REG[0x6A, (W1)] => 0x3347       REG[0x6C, (W1)] => 0x3037
REG[0x6E, (W1)] => 0x4450       REG[0x70, (W1)] => 0x3053       REG[0x72, (W1)] => 0x29FD
REG[0x74, (W1)] => 0x3057       REG[0x76, (W1)] => 0x3030       REG[0x78, (W1)] => 0x3030
REG[0x7A, (W1)] => 0x3531       REG[0x7E, (W0)] => 0x0000       Close:  com6 ,  460800 baud
```

## Configuring the Device for AUTOSTART Mode

AUTOSTART mode means that the device will automatically retrieve user-programmed device settings from Flash after power-on or reset
and enter SAMPLING mode to start sending sensor data

This is a two stage process. The *logger.py* script is first run to configure the desired settings with AUTOSTART enabled.
Then, the *logger.py* script is run again with the --flash_update switch.

Open a command prompt and run the *logger.py* python script with the desired command line switches:

1. Select COM port with -s switch (i.e., "-s com6")
2. Select IMU model --model switch (i.e., "--model G370PDF1") or do not specify the switch to let the software auto-detect
3. Select the desired output rate with the --drate switch (i.e., "--drate 200" for 200Hz)
4. Select the desired filter setting --filter switch (i.e., "--filter K128_FC25")
5. Select --autostart switch
6. Select other output field options as desired such as --ndflags --tempc --counter sample --chksm

```
python3 logger.py -s com6 --drate 200 --filter K128_FC25 --autostart --ndflags --tempc --counter sample --chksm
Model not specified, attempting to auto-detect
Detected: G370PDS0
Attitude or Quaternion not supported.
Start Log: 2023-02-23 21:04:06.935868
#Log created in Python,,,Sample Rate,200.0,Filter Cfg,k128_fc25,,,
#Creation Date:,2023-02-23 21:04:06.935868,PROD_ID=G370PDS0,VERSION=29FD,SERIAL_NUM=W0000015,,,,,,
#Scaled Data,SF_GYRO=+0.00666667 / 2^16 (deg/s)/bit,SF_ACCL=+0.40000000 / 2^16 mg/bit,SF_TEMPC=-0.00379180 / 2^16 degC/bit
Sample No.,Flags[hex],Ts[deg.C],Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG],Counter[dec],Chksm16[dec]
0,65276,34.9878,0.05045481,0.61051107,-0.05250783,12.32171631,9.99328003,6.27833252,5,46256
1,65276,34.9834,0.05044586,0.61031555,-0.0524821,12.22573242,10.13508911,6.00200195,10,17504
2,65276,34.9636,0.0504128,0.60951121,-0.05234721,11.79653931,10.77099609,4.76342163,15,52116
3,65276,34.9272,0.0503476,0.60810201,-0.05207926,11.00755005,11.94151611,2.48411255,20,30445
.
.
.
78,65276,21.4056,0.01772471,-0.00318665,-0.00625661,-282.01542358,447.45990601,-846.54857788,395,29988
79,65276,21.4057,0.01102142,-0.00939178,-0.02012268,-282.372229,447.215625,-846.31990356,400,31254
80,65276,21.4058,-0.00463511,-0.0199587,-0.02862864,-283.0545105,446.97546387,-846.23619385,405,9847
81,65276,21.4057,-0.02773682,-0.03746836,-0.0320049,-284.0480835,446.84927979,-846.26987915,410,44621
82,65276,21.4056,-0.05128143,-0.05793732,-0.03223145,-285.33282471,446.89196167,-846.31789551,415,56327
CTRL-C: Exiting
Stop reading sensor
#Log End,2023-02-23 21:04:07.232625,,,,,,,,
#Sample Count,000000083,,,,,,,,
#Data Rate,200.0,sps,,Filter Cfg,k128_fc25,,,,
-----------------  -----------------  ----------------  ------------
Date: 2023-02-23   Time: 21:04:07
-----------------  -----------------  ----------------  ------------
PROD_ID: G370PDS0  VERSION: 29FD      SERIAL: W0000015
DOUT_RATE: 200.0   FILTER: K128_FC25
NDFLAG: True       TEMPC: True        COUNTER: Sample   CHKSUM: True
DLT: False         ATTI: False        QTN: False        BIT32: True
-----------------  -----------------  ----------------  ------------
Close:  com6 ,  460800 baud
```

Then run the *logger.py* python script again:
1. Select COM port with -s switch (i.e., "-s com6")
2. Select --flash_update to store settings in the device

```
python3 logger.py -s com6 --flash_update
Model not specified, attempting to auto-detect
Detected: G370PDS0
Flash Backup Completed
Close:  com6 ,  460800 baud
```

## Configuring the Device Back to Factory Default Registers Settings

Open a command prompt and run the *logger.py* python script with the appropriate command line switches:

1. Select COM port with with -s switch (i.e., "-s com6")
2. Select --init_default

```
python3 logger.py -s com6 --initdefault
Model not specified, attempting to auto-detect
Detected: G370PDS0
Initial Backup Completed
Close:  com6 ,  460800 baud
```

## Help Screen Options:

```
usage: logger.py [-h] [-s SERIAL_PORT] [-b {921600,460800,230400}] [--secs SECS | --samples SAMPLES]
                   [--drate {2000,1000,500,250,125,62.5,31.25,15.625,400,200,100,80,50,40,25,20}]
                   [--filter {mv_avg0,mv_avg2,mv_avg4,mv_avg8,mv_avg16,mv_avg32,mv_avg64,mv_avg128,k32_fc25,k32_fc50,k32_fc100,k32_fc200,k32_fc400,k64_fc25,k64_fc50,k64_fc100,k64_fc200,k64_fc400,k128_fc25,k128_fc50,k128_fc100,k128_fc200,k128_fc400}]
                   [--model {g320,g354,g364pdc0,g364pdca,g365pdc1,g365pdf1,g370pdf1,g370pds0,g330pdg0,g366pdg0,g370pdg0}] [--a_range] [--bit16] [--csv] [--noscale]
                   [--ndflags] [--tempc] [--chksm] [--counter {reset,sample} | --ext_trigger]
                   [--dlt {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15} {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}] [--atti {euler,incl}] [--qtn]
                   [--atti_profile {modea,modeb,modec}] [--atti_conv {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}] [--autostart] [--init_default]
                   [--flash_update] [--dump_reg] [--verbose]

This program is intended as sample code for evaluation testing the Epson device with the UART I/F. This program will initialize the device with user specified arguments
and retrieve sensor data and format the output to console or CSV file. Other misc. utility functions are described in the help

optional arguments:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx
  -b {921600,460800,230400}, --baud_rate {921600,460800,230400}
                        specifies baudrate of the serial port, default is 460800
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C to abort and exit early
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit early
  --drate {2000,1000,500,250,125,62.5,31.25,15.625,400,200,100,80,50,40,25,20}
                        specifies IMU output data rate in sps, default is 200sps
  --filter {mv_avg0,mv_avg2,mv_avg4,mv_avg8,mv_avg16,mv_avg32,mv_avg64,mv_avg128,k32_fc25,k32_fc50,k32_fc100,k32_fc200,k32_fc400,k64_fc25,k64_fc50,k64_fc100,k64_fc200,k64_fc400,k128_fc25,k128_fc50,k128_fc100,k128_fc200,k128_fc400}
                        specifies the filter selection. If not specified, moving average based on selected output data rate will automatically be selected. NOTE: Refer
                        to datasheet for valid settings.
  --model {g320,g354,g364pdc0,g364pdca,g365pdc1,g365pdf1,g370pdf1,g370pds0,g330pdg0,g366pdg0,g370pdg0}
                        specifies the IMU model type, if not specified will auto-detect
  --a_range             specifies to use 16G accelerometer output range instead of 8G. NOTE: Not all devices support this mode.
  --bit16               specifies to output 16-bit resolution, otherwise use 32-bit
  --csv                 specifies to read sensor data to file otherwise sends to console. An optional string parameter if specified will be appended to filename
  --noscale             specifies to keep sensor data as digital counts (without applying scale factors)
  --counter {reset,sample}
                        specifies to enable reset counter(GPIO2) or sample counter in the sensor data
  --ext_trigger         specifies to enable external trigger mode on GPIO2

output field options:
  --ndflags             specifies to enable ND/EA flags in sensor data
  --tempc               specifies to enable temperature data in sensor data
  --chksm               specifies to enable 16-bit checksum in sensor data

attitude options:
  --atti {euler,incl}   specifies to enable attitude output in sensor data in euler mode or inclination mode NOTE: Not all devices support this mode.
  --qtn                 specifies to enable attitude quaternion data in sensor data. NOTE: Not all devices support this mode.
  --atti_profile {modea,modeb,modec}
                        specifies the attitude motion profile when attitude euler or quaternion output is enabled. NOTE: Not all devices support this feature.
  --atti_conv {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}
                        specifies the attitude axis conversion when attitude euler output is enabled. Must be between 0 to 23 (inclusive). This must be set to 0 for
                        when quaternion output is enabled NOTE: Not all devices support this feature.

delta angle/velocity options:
  --dlt {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15} {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}
                        specifies to enable delta angle & delta velocity in sensor data with specified delta angle, delta velocity scale factors. NOTE: Not all devices
                        support this mode.

flash-related options:
  --autostart           Enables AUTO_START fucntion. Should run afterwards with --flashupdate to store the settings to flash
  --init_default        This sets the IMU flash setting with default register settings per datasheet.
  --flash_update        specifies to store current IMU register settings to flash. This is normally used with --autostart or --initdefault

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device
  --verbose             specifies to enable low-level register messages for debugging
```

# SensorDevice Class Library Usage
-----------------------------------
 * *SensorDevice* is the main library class in the *esesnorlib* package for communicating and controlling the Epson sensor device
 * Provides low-level functions to read/write registers
 * Provides functions to perform selftests, software reset,
 * Provides flash-related functions
 * Provides functions to configure the device, and enter CONFIG/SAMPLING modes
 * Provides function to read a burst sample when in SAMPLING mode
 * Exposes read-only property attributes to read device statuses and model information


## Importing
 * Assuming the *esensorlib* package has been properly installed (see [Installation](#Installation)), the package must first be imported into the current python environment
 * *SensorDevice()* class is located in the *sensor_core.py* file in directory *src/esensorlib*

```
import esensorlib.sensor_core as sensor
```

## Instantiating
 * After importing the package, instantiate the class by passing the name of the serial port where the sensor device is attached
 * Optionally specify the baudrate (defaults to 460800 baud if not specified) and device model (auto-detects if not specified)
```
>>> imu = sensor.SensorDevice('com6')
Detected: G370PDS0
```

## Configuring
 * The device should be configured by passing the "basic" configuration dict, *basic_cfg*, when calling the *config()* method
 * Two optional configuration dicts can also be passed:
   * "delta angle / velocity" configuration (*dlt_cfg*)
   * "attitude / quaternion" configuration (*atti_cfg*)

### Default Configuration
 * If no configuration dicts are passed when calling the *config()* method, the defaults in [Default Basic](#Default-Basic) are used

```
>>> imu.config()
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
```

#### Default Basic (*basic_cfg*)

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
dout_rate       | 200          | 200 Hz
filter          | None         | Will auto-set to Moving Average TAP=16
ndflags         | True         | Include NDFLAGS field
tempc           | True         | Include temperature field
counter         | sample       | Include counter field containing sample count
chksm           | False        | Do not include 16-bit checksum field
auto_start      | False        | Disable AUTO_START function
is_32bit        | True         | Sensor data is 32-bit resolution i.e. Gyro, Accl, Temperature, etc
a_range         | False        | Set M-G330PDG0, M-G366PDG0, M-G370PDG0, M-G370PDT0 accelerometer output range to 8G (ignored for other models)
ext_trigger     | False        | Disable external trigger
uart_auto       | False        | UART_AUTO mode is disabled

#### Default Delta Angle / Velocity  (*dlt_cfg*)

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
dlta            | False        | Delta Angle output disabled
dltv            | False        | Delta Velcoity output disabled
dlta_sf_range   | 12           | If None, Delta Angle Scale Factor setting is 12
dltv_sf_range   | 12           | If None, Delta Velocity Scale Factor setting is 12

#### Default Attitude / Quaternion  (*atti_cfg*)

Key             | Value        | Description / Comment
----------------|--------------|-----------------------
atti            | False        | Attitude output disabled
mode            | "euler"      | Attitude mode is Euler mode
conv            | 0            | Attitude conversion mode is 0
profile         | "modea"      | Attitude Motion Profile is ModeA
qtn             | False        | Quaternion output is disabled


### Basic Configuration
 * Create a dict with desired basic settings and pass it in to the *basic_cfg* parameter when calling the *config()* method
 * *dlt_cfg* and *atti_cfg* parameters are optional and may be ommitted
 * NOTE: If *dlt_cfg* and *atti_cfg* are not specified it will use [defaults](#Default-Delta-Angle-/-Velocity)

```
my_basic = {
    "dout_rate": 250,
    "filter": "mv_avg16",
    "ndflags": True,
    "tempc": True,
    "counter": "sample",
    "chksm": False,
    "uart_auto": True,
    "auto_start": False,
    "is_32bit": True,
    "a_range": 0,
    "ext_trigger": False,
}
imu.config(basic_cfg=my_basic)
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
```

 * NOTE: Not all key, value pairs need to be included in the *basic_cfg* dict, only "dout_rate" is mandatory.

```
my_basic = {
    "dout_rate": 200,
    "ndflags": True,
    "tempc": True,
    "counter": "sample",
    "is_32bit": True,
}
imu.config(basic_cfg=my_basic)
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
```

### Delta Angle / Velocity Configuration
 * Create a dict with delta angle/velocity settings and pass it to the *dlt_cfg* parameter when calling the *config()* method
 * NOTE: If *basic_cfg* or *atti_cfg* are not specified it will use [defaults](#Default-Basic)

```
my_dlt = {
    "dlta": True,
    "dltv": True,
    "dlta_sf_range": 4,
    "dltv_sf_range": 4,
}
imu.config(dlt_cfg=my_dlt)
No atti_cfg specified. Bypassing.
```

### Attitude / Quaternion Configuration
 * Create a dict with attitude / quaternion settings and pass it to the *atti_cfg* parameter when calling the *config()* method
 * NOTE: Not all models support attitude or quaternion output
 * NOTE: If *basic_cfg* or *dlt_cfg* are not specified it will use [defaults](#Default-Basic)

```
my_atti = {
    "atti": True,
    "mode": "euler",
    "conv": 0,
    "profile": "modea",
    "qtn": True,
}
imu.config(atti_cfg=my_atti)
No dlt_cfg specified. Bypassing.
```

## Entering Sampling Mode or Config Mode
 * By default, the device will starts in CONFIG mode for general configuration by reading and writing registers
 * After the device has been configured (by calling *config()*), it must be put into SAMPLING mode to be able to read back sensor data

```
imu.goto('sampling')
```
 * NOTE: In SAMPLING mode, other than reading sensor data, the device can only go back to CONFIG mode (or calling a software reset)

```
imu.goto('config')
```

## Reading Sensor Data
 * When the device is in SAMPLING mode, calling *read_sample()* will return a tuple containing scaled sensor values
 * To return unscaled sensor data pass the parameter *scale_mode*=False when calling *read_sample()*
 * The type of fields in the returned sample data depends on the configuration of the device (after *config()* was called)
 * To check the type of burst field content and ordering for the *read_sample()* read the *burst_fields* property

```
>>> import esensorlib.sensor_core as sensor
>>> imu = sensor.SensorDevice('com7')
Detected: G366PDG0
>>> imu.config()
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
>>> imu.goto('sampling')
>>> imu.read_sample()
(65277, 24.4844, -0.09913381, -0.04506152, -0.02306736, -7.28860474, -0.18999481, -1005.48262787, 30950)
>>> imu.read_sample(False)
(65277, -8912896, -224449, -122431, -45655, -2016294, 199122, -263534044, 14054)
>>> imu.burst_fields
('ndflags', 'tempc32', 'gyro32_X', 'gyro32_Y', 'gyro32_Z', 'accl32_X', 'accl32_Y', 'accl32_Z', 'counter')
```

## Public Methods and Attributes

### Public Attributes

Attribute       | Type         | Description / Comment
----------------|--------------|-----------------------
info            | dict         | Device info such as prod_id, version_id, serial_id, comport, model
status          | dict         | Configuration status such as dout_rate, filter, ndflags, tempc, counter, chksm, auto_start, is_32bit, a_range, ext_trigger, uart_auto, is_config
dlt_status      | dict         | Delta angle / velocity status such as dlta, dltv, dlta_sf_range, dltv_sf_range
atti_status     | dict         | Atittiude/Quaternion status such as atti, mode, conv, profile, qtn
burst_out       | dict         | Burst output status such as ndflags, tempc, gyro, accl, dlta, dltv, qtn, atti, gpio, counter, chksm, tempc32, gyro32, accl32, dlta32, dltv32, qtn32, atti32
burst_fields    | tuple        | Types of fields contained in a burst read
mdef            | object       | Object that stores the current model's specific definitions and constants


### Public Method

Method                                | Description / Comment
--------------------------------------|-------------------------------
get_reg(winnum, regaddr)              | Perform 16-bit read from specified register address
set_reg(winnum, regaddr, write_byte)  | Perform 8-bit write to register address with specified byte
init_check()                          | Read status for hardware error (HARD_ERR)
do_selftest()                         | Perform selftest and check for errors (ST_ERR)
do_softreset()                        | Perform software reset
test_flash()                          | Perform flash test and check for errors (FLASH_ERR)
backup_flash()                        | Backup current register settings to flash and check for errors (FLASH_BU_ERR)
init_backup()                         | Clear backup setting in flash back to factory defaults
dump_reg(columns)                     | Print out all registers (specify number of columns to format to)
config(basic_cfg, dlt_cfg, atti_cfg)  | Configure device settings for basic, delta angle/velocity, attitude/quaternion
goto(mode, post_delay)                | Put device in CONFIG or SAMPLING mode and delay for specified time(post_delay) in seconds
get_mode()                            | Read the device for current mode (CONFIG or SAMPLING)
read_sample(scale_mode)               | Burst read a sample set from device specifying scaled values or not (scale_mode)


# LoggerHelper Class Library Usage
-----------------------------------
 * This *LoggerHelper* class is used by the *logger.py* to handle formatting of the sensor data output to console or csv file
 * NOTE: *LoggerHelper* requires a properly instantiated and configured *SensorDevice* object

## Importing
 * NOTE: Before using *LoggerHelper* class library, a *SensorDevice* should be instantiated from the *esensorlib* package
 * *LoggerHelper()* class is located in the *helper.py* file in the logger subdirectory where the *esensorlib* package is installed in your system (i.e. <python>\Lib\site-packages\esensorlib\logger)

```
import helper
```

## Instantiating
 * After importing the *helper.py*, instantiate a LoggerHelper class while passing the *SensorDevice* instance to the sensor parameter
```
>>> import esensorlib.sensor_core as sensor
>>> imu = sensor.SensorDevice('com7')
Detected: G366PDG0
>>> import esensorlib.logger.helper as helper
>>> log = helper.LoggerHelper(sensor=imu)
```

## Setting Output to CSV File
 * By default, *LoggerHelper* class methods *write()*, *write_header()*, *write_trailer()* will send output to the console
 * To send to a CSV file instead of the console, call the *LoggerHelper* *set_writer()* method specifying the *to* parameter
 * In the *to* parameter pass a list of strings which will combined with "_" to create a filename
 * The *set_writer* method will also insert the *SensorDevice* *prod_id*, *dout_rate*, *filter* values when creating teh filename
```
>>> import esensorlib.sensor_core as sensor
>>> imu = sensor.SensorDevice('com7')
Detected: G366PDG0
>>> import esensorlib.logger.helper as helper
>>> log = helper.LoggerHelper(sensor=imu)
>>> log.set_writer(to=['my_csv'])
```

 * If output is currently directed to a csv file, to close the file and redirect back to the console, call the *LoggerHelper* *set_writer()* method without a parameter
```
>>> log.set_writer()
CSV closed
```

## Writing Header
 * To write header rows containing device & configuration information to the csv file or console call the *write_header()* method
 * NOTE: The *SensorDevice* should be properly configured (by *config()* method) before calling the *write_header* method
```
>>> import esensorlib.sensor_core as sensor
>>> imu = sensor.SensorDevice('com7')
Detected: G366PDG0
>>> imu.config()
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
>>> import esensorlib.logger.helper as helper
>>> log = helper.LoggerHelper(sensor=imu)
>>> log.write_header()
Start Log: 2023-02-23 17:06:39.331964
#Log created in Python,,,Sample Rate,200,Filter Cfg,MV_AVG16,,,
#Creation Date:,2023-02-23 17:06:39.331964,PROD_ID=G366PDG0,VERSION=373,SERIAL_NUM=T1000062,,,,,,
#Scaled Data,SF_GYRO=+0.01515152 / 2^16 (deg/s)/bit,SF_ACCL=+0.25000000 / 2^16 mg/bit,SF_TEMPC=+0.00390625 / 2^16 degC/bit
Sample No.,Flags[hex],Ts[deg.C],Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG],Counter[dec]
>>>
```

## Writing Sample Data
 * To write a burst sensor sample to the console or csv file call the *write()* method with the output fron the *SensorDevice* *read_sample()* method
 * NOTE: The *SensorDevice* should be be properly configured (by *config()* method) before calling the *read_sample()* method
```
>>> import esensorlib.sensor_core as sensor
>>> imu = sensor.SensorDevice('com7')
Detected: G366PDG0
>>> imu.config()
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
>>> imu.goto('sampling')
>>> import esensorlib.logger.helper as helper
>>> log = helper.LoggerHelper(sensor=imu)
>>> log.write(imu.read_sample())
>>>
```

 * To write 1000 burst sensor samples to the csv file call the *write()* method with the output fron the *SensorDevice* *read_sample()* method
```
>>> import esensorlib.sensor_core as sensor
>>> imu = sensor.SensorDevice('com7')
Detected: G366PDG0
>>> imu.config()
No dlt_cfg specified. Bypassing.
No atti_cfg specified. Bypassing.
>>> imu.goto('sampling')
>>> import esensorlib.logger.helper as helper
>>> log = helper.LoggerHelper(sensor=imu)
>>> for i in range(1000):
... 	log.write(imu.read_sample())
>>>
```

## Writing Trailer
 * To write trailer rows data to the csv file or console call the *write_trailer()* method
 * NOTE: The *SensorDevice* should be be properly configured (by *config()* method) before calling the *read_sample()* method
```
>>> log.write_trailer()
#Log End,2023-02-23 17:09:06.114034,,,,,,,,
#Sample Count,000000000,,,,,,,,
#Data Rate,200,sps,,Filter Cfg,MV_AVG16,,,,
```

## Printing Device Status
 * To print to console current date/time and device, and configuration info call the *get_dev_info()* method
 * NOTE: The *SensorDevice* should be be properly configured (by *config()* method) before calling the *get_dev_info()* method
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
## Public Methods and Attributes

### Public Attributes
 * These are mirrors of the *SensorDevice* attributes propogated to the *LoggerHelper* class

Attribute       | Type         | Description / Comment
----------------|--------------|-----------------------
dev_info        | dict         | Device info such as prod_id, version_id, serial_id, comport, model
dev_status      | dict         | Configuration status such as dout_rate, filter, ndflags, tempc, counter, chksm, auto_start, is_32bit, a_range, ext_trigger, uart_auto, is_config
dev_dlt_status  | dict         | Delta angle / velocity status such as dlta, dltv, dlta_sf_range, dltv_sf_range
dev_atti_status | dict         | Atittiude/Quaternion status such as atti, mode, conv, profile, qtn
dev_burst_out   | dict         | Burst output status such as ndflags, tempc, gyro, accl, dlta, dltv, qtn, atti, gpio, counter, chksm, tempc32, gyro32, accl32, dlta32, dltv32, qtn32, atti32
dev_mdef        | object       | Object that stores the current model's specific definitions and constants


### Public Method

Method                                | Description / Comment
--------------------------------------|-------------------------------
set_writer(to)                        | Set the writer to csv file with filename derived from list of strings (parameter) or to the console (no parameter)
write(sample_data)                    | Send specified sample_data (tuple) to csv file or console
write_header(scale_mode, start_date)  | Write header information to csv file or console
write_trailer(end_date)               | Write trailer information to csv file or console
get_dev_status()                      | Send current info about device and configuration to console
clear_count()                         | Clear the internal sample counter which increments on every call to *write()*


# File Listing
--------------

File                              | Description / Comment
----------------------------------|----------------------
src\                              | Python source files
src\esensorlib\sensor_core.py     | SensorDevice library class
src\esensorlib\model\mcore.py     | Core model definition/constants (temporarily used for auto-detect)
src\esensorlib\model\mg320.py     | M-G320PDG0 model definition/constants
src\esensorlib\model\mg354.py     | M-G354PDH0 model definition/constants
src\esensorlib\model\mg364pdc0.py | M-G364PDC0 model definition/constants
src\esensorlib\model\mg364pdca.py | M-G364PDCA model definition/constants
src\esensorlib\model\mg365pdc1.py | M-G365PDC1 model definition/constants
src\esensorlib\model\mg365pdf1.py | M-G365PDF1 model definition/constants
src\esensorlib\model\mg366pdg0.py | M-G366PDG0 model definition/constants
src\esensorlib\model\mg370pdf1.py | M-G370PDF1 model definition/constants
src\esensorlib\model\mg370pds0.py | M-G370PDS0 model definition/constants
src\esensorlib\model\mg370pdt0.py | M-G370PDT0 model definition/constants
src\esensorlib\logger\logger.py   | Logger script
src\esensorlib\logger\helper.py   | Logger helper class (for formatting and file I/O)
tests\                            | Test files (currently empty)
LICENSE                           | License description
pyproject.toml                    | Contains build system requirements and information, which are used by pip to build the package
README.md                         | This readme file


# Change Record
--------------

Date        | Version   | Description / Comment
------------|-----------|----------------------
2023-02-24  | v1.0.0    | Initial release
