
# Table of Contents
-------------
<!---toc start-->

* [Table of Contents](#table-of-contents)
* [Python Library for Epson Sensing System Devices](#python-library-for-epson-sensing-system-devices)
  * [Test Machines](#test-machines)
  * [Requirements](#requirements)
  * [Precautionary Notes](#precautionary-notes)
* [Installation](#installation)
* [Logger Usage](#logger-usage)
  * [Reading Sensor Data](#reading-sensor-data)
    * [IMU Sensor Data](#imu-sensor-data)
    * [ACCL Sensor Data](#accl-sensor-data)
    * [VIBE Sensor Data](#vibe-sensor-data)
  * [Reading Out Current Registers](#reading-out-current-registers)
    * [IMU Register Data](#imu-register-data)
    * [ACCL Register Data](#accl-register-data)
    * [VIBE Register Data](#vibe-register-data)
  * [Configuring Device for AUTO_START and Flash Update](#configuring-device-for-auto_start-and-flash-update)
    * [AUTO_START Mode](#auto_start-mode)
    * [Flashing Settings](#flashing-settings)
    * [NO_INIT Mode Operation](#no_init-mode-operation)
  * [Flashing Device Back to Factory Default Registers Settings](#flashing-device-back-to-factory-default-registers-settings)
  * [Help Screen Options](#help-screen-options)
    * [IMU Help Screen](#imu-help-screen)
    * [ACCL Help Screen](#accl-help-screen)
    * [VIBE Help Screen](#vibe-help-screen)
* [File Listing](#file-listing)
* [Change Record](#change-record)

<!---toc end-->

# Python Library for Epson Sensing System Devices
-------------
This a general python library for evaluating the Epson Sensing System
devices and building evaluation software in a Python 3.x environment using the UART interface.

This package consists of two main parts:
  * *SensorDevice* main class is a composition subclasses *UartPort*, *RegInterface*, and one of the following *AcclFn*, *ImuFn*, or *VibFn* depending on the type of device
    * Primary purpose is to communicate and control the sensing device
    * Provide low-level functions to read/write registers
    * Provide functions to perform self-tests, software reset, flash-related functions
    * Provide functions to configure the device, and enter CONFIG/SAMPLING mode
    * Provide functions to read a burst sample when in SAMPLING mode
    * Expose properties to read various statuses and device model information
    * For more detailed information on using the *SensorDevice* class refer to the README.md in the `src/esensorlib/` folder
  * A example logger comes in 3 variants based on the sensing device types: *accl_logger.py*, *imu_logger.py*, *vibe_logger.py*
    * This is intended as evaluation software and as a reference on how to use the *SensorDevice* class to control and read sensor data
    * The *LoggerHelper* class is for parsing and formatting sensor device status and sensor data
    * This is a command line driven application for configuring the device and/or logging the sensor output using arguments:
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
  * Python 3.8+
  * Python packages can be installed using [pypi](https://pypi.org):
    * [serial](https://pypi.org/project/pyserial)
    * [tqdm](https://pypi.org/project/tqdm)
    * [tabulate](https://pypi.org/project/tabulate)
    * [loguru](https://pypi.org/project/loguru)
  * Epson sensing device connected to the host UART interface i.e. WIN/PC, Linux/PC or any embedded Linux system with serial port
    * M-G320PDG0, M-G354PDH0, M-G364PDC0, M-G364PDCA
    * M-G365PDC1, M-G365PDF1, M-G370PDF1, M-G370PDS0
    * M-G330PDG0, M-G366PDG0, M-G370PDG0, M-G370PDT0
    * M-G570PR20, M-G355QDG0
    * M-A352AD10, M-A370AD10, M-A342VD10
  * Epson evaluation board
    * Epson USB evaluation board [M-G32EV041](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev041_e_rev201910.pdf)
  * Alternatively, a direct connection to host digital UART port (**NOTE:** 3.3V CMOS I/O signaling) using an adapter such as:
    * Epson PCB Breakout board [M-G32EV031](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev031_e_rev201910.pdf), or
    * Epson Relay board [M-G32EV051](https://global.epson.com/products_and_drivers/sensing_system/assets/pdf/m-g32ev051_e_rev201910.pdf)


## Precautionary Notes
For WIN/PC Only:

  * Before running the logger using the Epson IMU USB evaluation board (or equivalent FTDI USB-UART bridge IC) on a WIN/PC host, please set the Window's BM Options -> Latency Timer to 1msec
  * This is especially necessary for sampling rates faster than 125sps
  * By default the *BM latency timer* is set to 16ms, which may cause the serial handling on the PC to be sluggish and drop bytes during transmission
  * Change the serial port *BM latency timer* to 1msec in Windows 10, go to:
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


# Logger Usage
--------------
  * There is a logger program for each of the 3 device types
    * `imu_logger.py` for IMU devices
    * `accl_logger.py` for ACCL devices
    * `vibe_logger.py` for VIBE devices
  * Each logger script have different features and configuration options specific to the device type
  * When the `esensorlib` is installed using pip, the logger can be launched from python using the `-m` command from the console
    * `python3 -m esensorlib.example.imu_logger`
    * `python3 -m esensorlib.example.accl_logger`
    * `python3 -m esensorlib.example.vibe_logger`

**NOTE:** Use the -h switch for the help menu to see a description of logger settings

## Reading Sensor Data

### IMU Sensor Data

Open a command prompt and run `imu_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s com6`)
2. Select IMU model `--model` switch (i.e., `--model g366pdg0`) or let the software auto-detect by not specifying this switch
3. Select the desired output rate with the `--drate` switch (i.e., `--drate 200` for 200Hz)
4. Select the desired filter setting with the `--filter` switch (i.e., `--filter k32_fc50`) or let the software choose a valid moving average filter by not specifying this switch
5. Select the desired time duration in seconds with the `--secs` switch (i.e., `--secs 60`) or number of samples with the `--samples` switch (i.e., `--samples 100`)
6. Select if the sensor data is written to a CSV file with the `--csv` switch or to the console by not specifying this switch
7. Append other switches to include more fields in the sensor data as desired. Use the `-h` for help description of switches

```
python3 -m esensorlib.example.imu_logger -s com7 --drate 200 --filter k32_fc50 --samples 100
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Configured basic
#Log esensorlib,,,Output Rate,200.0,Filter Setting,K32_FC50,,,
#Creation Date:,2025-07-29 16:55:36.082827,PROD_ID=G366PDG0,VERSION=373,SERIAL_NUM=T1000062,,,,,
#Scaled Data,SF_ACCL=+0.25000000/2^16 mg/bit,SF_GYRO=+0.01515152/2^16 (deg/s)/bit
Sample No.,Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG]
0,0.17656107,-0.04621055,0.00403687,1.73661041,6.02949524,-115.25700378
1,0.05184636,-0.0207753,-0.02566621,4.836586,5.75184631,-802.11402893
2,-0.01542733,-0.00574517,-0.0055253,5.83975983,5.56912994,-1003.18618011
3,-0.01252932,0.0083461,-0.00669213,5.73040771,5.17081451,-1005.02420044
4,-0.01120064,-0.02008057,-0.00241043,5.45614624,5.24601746,-1004.30560303
5,-0.00521804,-0.01649914,-0.03712995,5.64749908,4.91703796,-1005.43212891
.
.
.
95,-0.03275299,-0.01664688,-0.01719434,5.95344543,5.80189514,-1001.99334717
96,-0.02927954,-0.0521839,-0.03959933,5.25948334,5.67977142,-1003.1716156
97,-0.02407236,-0.0366671,-0.02832332,5.47563171,5.80312347,-1006.95452881
98,0.02495482,-0.02459462,-0.00762801,6.25119781,5.55180359,-1009.36605072
99,0.01979828,-0.00823212,-0.03410016,6.63855743,5.3670578,-1008.39677429
#Log End,2025-07-29 16:55:36.603141,,,,,,,,
#Sample Count,000000100,,,,,,,,
#Output Rate,200.0,,Filter Setting,K32_FC50,,,,,
-----------------  ----------------  ----------------  ------------
Date: 2025-07-29   Time: 16:55:36
-----------------  ----------------  ----------------  ------------
PROD_ID: G366PDG0  VERSION: 373      SERIAL: T1000062
DOUT_RATE: 200.0   FILTER: K32_FC50
NDFLAG: False      TEMPC: False      COUNTER: False    CHKSM: False
DLT: False         ATTI: False       QTN: False
-----------------  ----------------  ----------------  ------------
Close:  com7 ,  460800 baud
```

### ACCL Sensor Data

Open a command prompt and run `accl_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s com14`)
2. Select IMU model `--model` switch (i.e., `--model a352ad10`) or let the software auto-detect by not specifying this switch
3. Select the desired output rate with the `--drate` switch (i.e., `--drate 200` for 200Hz)
4. Select the desired filter setting with the `--filter` switch (i.e., `--filter k128_fc36`) or let the software choose a valid moving average filter by not specifying this switch
5. Select the desired time duration in seconds with the `--secs` switch (i.e., `--secs 60`) or number of samples with the `--samples` switch (i.e., `--samples 100`)
6. Select if the sensor data is written to a CSV file with the `--csv` switch or to the console by not specifying this switch
7. Append other switches to include more fields in the sensor data as desired. Use the `-h` for help description of switches

```
python3 -m esensorlib.example.accl_logger -s com14 --drate 200 --filter k128_fc36 --samples 100
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: A352AD10
Configured
#Log esensorlib,,,Output Rate,200.0,Filter Setting,K128_FC36,,,
#Creation Date:,2025-07-29 16:57:28.931331,PROD_ID=A352AD10,VERSION=0D,SERIAL_NUM=W0000501,,,,,
#Scaled Data,SF_ACCL=+0.00005960 mg/bit
Sample No.,Ax[mG],Ay[mG],Az[mG]
0,42.548001,20.377815,-1006.109953
1,42.4546,20.451248,-1005.945265
2,42.480588,20.431519,-1005.155563
3,42.445242,20.374835,-1004.418314
4,42.468965,20.343781,-1004.119575
5,42.60844,20.325482,-1004.014909
.
.
.
95,42.630911,20.183325,-1006.026089
96,42.575061,20.093501,-1005.919635
97,42.537212,20.054996,-1005.899608
98,42.514145,20.072699,-1005.821347
99,42.565048,20.109892,-1005.606353
#Log End,2025-07-29 16:57:29.476955,,,,,,,,
#Sample Count,000000100,,,,,,,,
#Output Rate,200.0,,Filter Setting,K128_FC36,,,,,
-----------------  -----------------  ----------------  ------------
Date: 2025-07-29   Time: 16:57:29
-----------------  -----------------  ----------------  ------------
PROD_ID: A352AD10  VERSION: 0D        SERIAL: W0000501
DOUT_RATE: 200.0   FILTER: K128_FC36
NDFLAG: False      TEMPC: False       COUNTER: False    CHKSM: False

-----------------  -----------------  ----------------  ------------
Close:  com7 ,  460800 baud
```

### VIBE Sensor Data

Open a command prompt and run `vibe_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s com10`)
2. Select IMU model `--model` switch (i.e., `--model a342vd10`) or let the software auto-detect by not specifying this switch
3. Select the desired output_sel mode `--output_sel` switch (i.e., `--output_sel velocity_rms`)
3. Select the desired output rate with the `--drate` switch (i.e., `--drate 10` for 10Hz)
4. Select the desired update rate with the `--urate` switch (i.e., `--urate 99`)
5. Select the desired time duration in seconds with the `--secs` switch (i.e., `--secs 60`) or number of samples with the `--samples` switch (i.e., `--samples 100`)
6. Select if the sensor data is written to a CSV file with the `--csv` switch or to the console by not specifying this switch
7. Append other switches to include more fields in the sensor data as desired. Use the `-h` for help description of switches

```
python3 -m esensorlib.example.vibe_logger -s com10 --output_sel velocity_rms --drate 10 --urate 99 --samples 100
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: A342VD10
Configured
#Log esensorlib,,,DOUT_RATE_RMSPP,1,UPDATE_RATE_RMSPP,0,Output Sel,VELOCITY_RMS,
#Creation Date:,2025-07-29 16:58:53.119076,PROD_ID=A342VD10,VERSION=280,SERIAL_NUM=00000094,,,,,
#Scaled Data,SF_VEL=+0.00023842 (mm/s)/bit
Sample No.,Vx[mm/s],Vy[mm/s],Vz[mm/s]
0,0.00762939,0.01001358,0.19955635
1,0.02384186,0.02241135,0.13256073
2,0.00452995,0.0128746,0.04839897
3,0.0243187,0.00977516,0.12898445
4,0.00548363,0.01192093,0.10681152
5,0.00762939,0.00882149,0.16880035
.
.
.
95,0.00786781,0.01597404,0.01478195
96,0.00476837,0.00619888,0.09036064
97,0.01335144,0.00524521,0.04768372
98,0.00882149,0.00810623,0.08368492
99,0.01335144,0.0064373,0.14591217
#Log End,2025-07-29 16:59:03.288143,,,,,,,,
#Sample Count,000000100,,,,,,,,
#Output Rate,1,,Filter Setting,NA,,Output Sel,VELOCITY_RMS,,
-------------------  --------------  ----------------  ------------
Date: 2025-07-29     Time: 16:59:03
-------------------  --------------  ----------------  ------------
PROD_ID: A342VD10    VERSION: 280    SERIAL: 00000094
DOUT_RATE_RMSPPP: 1  UPDATE_RATE: 0
NDFLAG: False        TEMPC: False    COUNTER: False    CHKSM: False

-------------------  --------------  ----------------  ------------
Close:  com7 ,  460800 baud
```

## Reading Out Current Registers

### IMU Register Data

Open a command prompt and run `imu_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s com7`)
2. Select IMU model `--model` switch (i.e., `--model g370pdf1`) or do not specify the switch to let the software auto-detect
3. Select `--dump_reg` switch

```
python3 -m esensorlib.example.imu_logger -s com7 --dump_reg
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Reading registers:
REG[0x00, (W0)] => 0xFFFF       REG[0x02, (W0)] => 0x0400       REG[0x04, (W0)] => 0x0400
REG[0x06, (W0)] => 0x0100       REG[0x08, (W0)] => 0x0000       REG[0x0A, (W0)] => 0x03E8
REG[0x0C, (W0)] => 0x2001       REG[0x0E, (W0)] => 0xFEA1       REG[0x10, (W0)] => 0xC8EC
REG[0x12, (W0)] => 0xFFFE       REG[0x14, (W0)] => 0xF1D4       REG[0x16, (W0)] => 0x0000
REG[0x18, (W0)] => 0xE298       REG[0x1A, (W0)] => 0x0000       REG[0x1C, (W0)] => 0xA60E
REG[0x1E, (W0)] => 0x0027       REG[0x20, (W0)] => 0x7E36       REG[0x22, (W0)] => 0x0020
REG[0x24, (W0)] => 0xCB8A       REG[0x26, (W0)] => 0x0FA6       REG[0x28, (W0)] => 0x7F3E
REG[0x4C, (W0)] => 0x5345       REG[0x50, (W0)] => 0x3FFF       REG[0x52, (W0)] => 0xA5A9
REG[0x54, (W0)] => 0x0042       REG[0x56, (W0)] => 0xC272       REG[0x58, (W0)] => 0xFFAB
REG[0x5A, (W0)] => 0xB358       REG[0x5C, (W0)] => 0x0000       REG[0x5E, (W0)] => 0x61E1
REG[0x64, (W0)] => 0x0042       REG[0x66, (W0)] => 0xC1D5       REG[0x68, (W0)] => 0xFFAB
REG[0x6A, (W0)] => 0xB247       REG[0x6C, (W0)] => 0x0000       REG[0x6E, (W0)] => 0xB9E2
REG[0x70, (W0)] => 0x7EF0       REG[0x72, (W0)] => 0x7EF0       REG[0x74, (W0)] => 0x7EF0
REG[0x76, (W0)] => 0x7EF0       REG[0x78, (W0)] => 0x7EF0       REG[0x7A, (W0)] => 0x7EF0
REG[0x00, (W1)] => 0xFE00       REG[0x02, (W1)] => 0x0006       REG[0x04, (W1)] => 0x0903
REG[0x06, (W1)] => 0x0008       REG[0x08, (W1)] => 0x0001       REG[0x0A, (W1)] => 0x0000
REG[0x0C, (W1)] => 0x3000       REG[0x0E, (W1)] => 0x7F00       REG[0x10, (W1)] => 0x0000
REG[0x12, (W1)] => 0x00CC       REG[0x14, (W1)] => 0x0C00       REG[0x16, (W1)] => 0x0000
REG[0x38, (W1)] => 0x4000       REG[0x3A, (W1)] => 0x0000       REG[0x3C, (W1)] => 0x0000
REG[0x3E, (W1)] => 0x0000       REG[0x40, (W1)] => 0x4000       REG[0x42, (W1)] => 0x0000
REG[0x44, (W1)] => 0x0000       REG[0x46, (W1)] => 0x0000       REG[0x48, (W1)] => 0x4000
REG[0x6A, (W1)] => 0x3347       REG[0x6C, (W1)] => 0x3636       REG[0x6E, (W1)] => 0x4450
REG[0x70, (W1)] => 0x3047       REG[0x72, (W1)] => 0x3703       REG[0x74, (W1)] => 0x3154
REG[0x76, (W1)] => 0x3030       REG[0x78, (W1)] => 0x3030       REG[0x7A, (W1)] => 0x3236
REG[0x7E, (W0)] => 0x0000
```

### ACCL Register Data

Open a command prompt and run `accl_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s COM7`)
2. Select IMU model `--model` switch (i.e., `--model a352ad10`) or do not specify the switch to let the software auto-detect
3. Select `--dump_reg` switch

```
python3 -m esensorlib.example.accl_logger -s com14 --dump_reg
Model not specified, attempting to auto-detect
Open:  com14 ,  460800
Detected: A352AD10
Reading registers:
REG[0x00, (W0)] => 0xFFFF       REG[0x02, (W0)] => 0x0400       REG[0x04, (W0)] => 0x0000
REG[0x06, (W0)] => 0x0000       REG[0x0A, (W0)] => 0x07D0       REG[0x0E, (W0)] => 0x0000
REG[0x10, (W0)] => 0x09A2       REG[0x30, (W0)] => 0xFFFC       REG[0x32, (W0)] => 0xE388
REG[0x34, (W0)] => 0x0009       REG[0x36, (W0)] => 0x3A7A       REG[0x38, (W0)] => 0x00FF
REG[0x3A, (W0)] => 0x0624       REG[0x3C, (W0)] => 0xFFA2       REG[0x3E, (W0)] => 0xE7FD
REG[0x40, (W0)] => 0x0148       REG[0x42, (W0)] => 0x27D7       REG[0x44, (W0)] => 0xFFFF
REG[0x46, (W0)] => 0xFFFF       REG[0x4C, (W0)] => 0x5345       REG[0x00, (W1)] => 0x8E04
REG[0x02, (W1)] => 0x0006       REG[0x04, (W1)] => 0x0400       REG[0x06, (W1)] => 0x0003
REG[0x08, (W1)] => 0x0101       REG[0x0A, (W1)] => 0x0000       REG[0x0C, (W1)] => 0x0700
REG[0x16, (W1)] => 0x0000       REG[0x18, (W1)] => 0x0000       REG[0x1A, (W1)] => 0x0800
REG[0x1C, (W1)] => 0x0000       REG[0x1E, (W1)] => 0x000A       REG[0x2C, (W1)] => 0x0000
REG[0x2E, (W1)] => 0x0000       REG[0x30, (W1)] => 0x0000       REG[0x32, (W1)] => 0x0000
REG[0x34, (W1)] => 0x0000       REG[0x36, (W1)] => 0x0000       REG[0x46, (W1)] => 0x0FF1
REG[0x48, (W1)] => 0x0FF1       REG[0x4A, (W1)] => 0x0FF1       REG[0x6A, (W1)] => 0x3341
REG[0x6C, (W1)] => 0x3235       REG[0x6E, (W1)] => 0x4441       REG[0x70, (W1)] => 0x3031
REG[0x72, (W1)] => 0x000D       REG[0x74, (W1)] => 0x3057       REG[0x76, (W1)] => 0x3030
REG[0x78, (W1)] => 0x3530       REG[0x7A, (W1)] => 0x3130       REG[0x7E, (W0)] => 0x0000
```

### VIBE Register Data

Open a command prompt and run `vibe_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s com10`)
2. Select IMU model `--model` switch (i.e., `--model a342vd10`) or do not specify the switch to let the software auto-detect
3. Select `--dump_reg` switch

```
python3 -m esensorlib.example.vibe_logger -s com10 --dump_reg
Model not specified, attempting to auto-detect
Open:  com10 ,  460800
Detected: A342VD10
Reading registers:
REG[0x00, (W0)] => 0xFFFF       REG[0x02, (W0)] => 0x0400       REG[0x04, (W0)] => 0x0000
REG[0x06, (W0)] => 0x0000       REG[0x0A, (W0)] => 0x2582       REG[0x0C, (W0)] => 0x0000
REG[0x10, (W0)] => 0x09D2       REG[0x2A, (W0)] => 0xFFFF       REG[0x2C, (W0)] => 0xFFFF
REG[0x2E, (W0)] => 0x0900       REG[0x30, (W0)] => 0x0000       REG[0x32, (W0)] => 0x0025
REG[0x34, (W0)] => 0x0000       REG[0x36, (W0)] => 0x001D       REG[0x38, (W0)] => 0x0000
REG[0x3A, (W0)] => 0x00B4       REG[0x4C, (W0)] => 0x5345       REG[0x00, (W1)] => 0x8E10
REG[0x02, (W1)] => 0x0006       REG[0x04, (W1)] => 0x0100       REG[0x08, (W1)] => 0x0101
REG[0x0A, (W1)] => 0x0000       REG[0x0C, (W1)] => 0x0700       REG[0x38, (W1)] => 0x0000
REG[0x3A, (W1)] => 0x0000       REG[0x3C, (W1)] => 0x0000       REG[0x46, (W1)] => 0x0666
REG[0x48, (W1)] => 0x0666       REG[0x4A, (W1)] => 0x0666       REG[0x6A, (W1)] => 0x3341
REG[0x6C, (W1)] => 0x3234       REG[0x6E, (W1)] => 0x4456       REG[0x70, (W1)] => 0x3031
REG[0x72, (W1)] => 0x0280       REG[0x74, (W1)] => 0x3030       REG[0x76, (W1)] => 0x3030
REG[0x78, (W1)] => 0x3030       REG[0x7A, (W1)] => 0x3439       REG[0x7E, (W0)] => 0x0000
```

## Configuring Device for AUTO_START and Flash Update

* Configuring a device for AUTO_START is a two stage process.
* First run the appropriate `xxxx_logger.py` that matches your connected device to configure the desired device settings and with `--auto_start`.
* Then, run the `xxxx_logger.py` again with the `--flash_update` switch to store the settings to non-volatile memory of the device.

### AUTO_START Mode

*AUTO_START* mode is intended for the UART interface only for the device to automatically retrieve user-programmed settings from device internal flash after power-on or reset
and automatically enter SAMPLING mode to start sending sensor data.

**NOTE:** When the device is programmed with *AUTO_START*, the appropriate `xxxx_logger.py` must be run with desired parameters for the connected device.

For example, below is an example for an IMU using `imu_logger.py`:

1. Select COM port with `-s` switch (i.e., `-s com7`)
2. Select the correct model with `--model` parameter or do not specify the switch to let the software auto-detect
3. Select the desired output rate with the `--drate` parameter (i.e., `--drate 100` for 100Hz)
4. Select the desired filter setting `--filter` parameter (i.e., `--filter K128_FC25`)
5. Select other options as desired such as `--ndflags` `--tempc` `--counter sample` `--chksm`
6. Select `--autostart` switch
7. Press CTRL-C to exit early or let the logger complete and finish its operation
```
python3 -m esensorlib.example.imu_logger -s com7 --drate 100 --filter mv_avg128 --ndflags --tempc --counter sample --chksm --autostart
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Configured basic
#Log esensorlib,,,Output Rate,100.0,Filter Setting,MV_AVG128,,,
#Creation Date:,2025-07-29 16:42:57.920768,PROD_ID=G366PDG0,VERSION=373,SERIAL_NUM=T1000062,,,,,
#Scaled Data,SF_ACCL=+0.25000000/2^16 mg/bit,SF_GYRO=+0.01515152/2^16 (deg/s)/bit,SF_TEMPC=+0.00390625/2^16 degC/bit
Sample No.,Flags[dec],Ts[degC],Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG],Counter[dec],Chksm16[dec]
0,65276,24.9648,0.17064158,-0.04597103,-0.00179337,2.07702637,5.84046936,-167.99195862,20,50797
1,65276,24.9298,0.13737326,-0.04109862,-0.00705973,2.82232666,5.82949829,-322.89312744,40,60533
2,65276,24.8932,0.11094735,-0.03477177,-0.01309643,3.50617218,5.71233368,-477.98628235,60,46432
3,65276,24.855,0.08192005,-0.02985197,-0.02164852,4.18172455,5.46247864,-632.98291779,80,32904
4,65276,24.8141,0.05373151,-0.02111192,-0.02808981,4.96351624,5.31898499,-787.96170807,100,62478
5,65276,24.7744,0.02362639,-0.01416409,-0.03161529,5.73574829,5.18725586,-942.70998383,120,36988
6,65276,24.7566,0.01069433,-0.01089223,-0.0316035,5.96842194,5.2179718,-1004.40931702,140,42023
7,65276,24.7539,0.01111348,-0.00580273,-0.03045261,5.94342804,5.13697815,-1004.28749847,160,29430
8,65276,24.7531,0.00868202,-0.00819166,-0.03066832,6.1237793,4.99550629,-1004.03150177,180,5095
9,65276,24.7555,0.00474363,-0.00820414,-0.03200254,6.21252441,5.17482758,-1004.29095459,200,25474
CTRL-C: Exiting
Stop reading sensor
#Sample Count,000000010,,,,,,,,
#Output Rate,100.0,,Filter Setting,MV_AVG128,,,,,
-----------------  -----------------  ----------------  -----------
Date: 2025-07-29   Time: 16:42:58
-----------------  -----------------  ----------------  -----------
PROD_ID: G366PDG0  VERSION: 373       SERIAL: T1000062
DOUT_RATE: 100.0   FILTER: MV_AVG128
NDFLAG: True       TEMPC: True        COUNTER: True     CHKSM: True
DLT: False         ATTI: False        QTN: False
-----------------  -----------------  ----------------  -----------
Close:  com7 ,  460800 baud
```

### Flashing Settings

To store the current device settings to flash, run the same `xxxx_logger.py` python script with `--flash_update` option:
1. Select COM port with `-s` switch (i.e., `-s com7`)
2. Select `--flash_update` to store settings in the device
3. The settings are now stored on the device and re-loads on power-on or reset

```
python3 -m esensorlib.example.imu_logger -s com7 --flash_update
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Flash Backup Completed
```

### NO_INIT Mode Operation

When a device has been configured and flashed for *AUTO_START*, the device loads the device settings, enters *SAMPLING* mode
and sends sensor sampling data automatically.

By default the `xxxx_logger.py` programs are designed to initialize a sensor device based on user supplied parameters.
However, when a device is configured for *AUTO_START*, the device will already be configured and sending sensor sampling data. In this case, the user may wish to bypass initializing the device and simply read out
or log the sensor data to CSV without writing to the sensor device registers.

NO_INIT mode operation is designed to read out the sensor device when it is already in *SAMPLING* mode by *AUTO_START* mode.

NOTE: The user must provide the device model & proper settings that were flashed to the device when using `--no_init` option.

1. Select COM port with `-s` switch (i.e., `-s com7`)
2. Specify the model `--model` switch (i.e., `--model g366pdg0`)
3. Specify `--no_init` so that device initialization will be bypassed and registers will not be written to the device
4. Specify the device settings that were used to to flash the device, so that the program can properly parse and decode the sensor data

```
python3 -m esensorlib.example.imu_logger -s com7 --model g366pdg0 --no_init --drate 100 --filter mv_avg128 --ndflags --tempc --counter sample --chksm --samples 10
Open:  com7 ,  460800
2025-07-29 16:39:03.848 | WARNING  | esensorlib.imu_fn:goto:524 - --no_init option specified, bypass setting in MODE_CTRL register
2025-07-29 16:39:03.848 | WARNING  | esensorlib.imu_fn:_set_ext_sel:979 - --no_init bypass setting EXT_POL in MSC_CTRL register
2025-07-29 16:39:03.848 | WARNING  | esensorlib.imu_fn:_set_output_rate:845 - --no_init bypass setting DOUT_RATE register
2025-07-29 16:39:03.848 | WARNING  | esensorlib.imu_fn:_set_filter:909 - --no_init bypass setting FILTER_SEL register
2025-07-29 16:39:03.848 | WARNING  | esensorlib.imu_fn:_set_uart_mode:949 - --no_init bypass setting UART_CTRL register
2025-07-29 16:39:03.855 | WARNING  | esensorlib.imu_fn:_set_accl_range:1052 - --no_init bypass setting A_RANGE in SIG_CTRL register
2025-07-29 16:39:03.855 | WARNING  | esensorlib.imu_fn:_config_burst_ctrl1:1563 - --no_init bypass setting BURST_CTRL1 register
2025-07-29 16:39:03.856 | WARNING  | esensorlib.imu_fn:_config_burst_ctrl2:1606 - --no_init bypass setting BURST_CTRL2 register
Configured basic
2025-07-29 16:39:03.857 | WARNING  | esensorlib.imu_fn:_config_dlt:1161 - Delta angle / velocity function disabled. Bypassing.
2025-07-29 16:39:03.857 | WARNING  | esensorlib.imu_fn:_config_atti:1266 - Attitude or quaternion disabled. Bypassing.
2025-07-29 16:39:03.857 | WARNING  | esensorlib.imu_fn:_get_burst_config:701 - --no_init option assumes device is already configured with user-specified settings and AUTO_START enabled.
2025-07-29 16:39:03.857 | WARNING  | esensorlib.imu_fn:goto:524 - --no_init option specified, bypass setting in MODE_CTRL register
#Log esensorlib,,,Output Rate,100.0,Filter Setting,MV_AVG128,,,
#Creation Date:,2025-07-29 16:39:03.857930,PROD_ID=G366PDG0,VERSION=None,SERIAL_NUM=None,,,,,
#Scaled Data,SF_ACCL=+0.25000000/2^16 mg/bit,SF_GYRO=+0.01515152/2^16 (deg/s)/bit,SF_TEMPC=+0.00390625/2^16 degC/bit
Sample No.,Flags[dec],Ts[degC],Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG],Counter[dec],Chksm16[dec]
0,65276,23.3408,0.00629864,-0.00021987,-0.02803987,6.3888855,5.1231308,-1004.74882507,63080,47782
1,65276,23.342,0.00553617,0.00411432,-0.02675814,6.3465271,5.09443665,-1004.88045502,63100,36143
2,65276,23.3383,0.01047493,0.00407433,-0.02186954,6.41944122,5.06581116,-1004.97850037,63120,2964
3,65276,23.3313,0.01072531,0.00835627,-0.01745698,6.25437164,5.03913879,-1005.20718384,63140,10307
4,65276,23.3292,0.01091373,0.00581637,-0.01009739,6.39601898,5.05594635,-1005.03746033,63160,16644
5,65276,23.3292,0.01529532,0.00502662,-0.00572667,6.40953064,5.08692169,-1004.69545746,63180,21352
6,65276,23.3303,0.01466416,-0.00469416,-0.01180892,6.57705688,5.06537628,-1004.29202271,63200,47210
7,65276,23.3309,0.01638123,-0.00522521,-0.01359489,6.53486633,5.05635071,-1004.12186432,63220,21545
8,65276,23.3285,0.01171043,-0.00811444,-0.01724867,6.39255524,5.12077332,-1003.98863983,63240,12141
9,65276,23.3317,0.0097936,-0.01029344,-0.01863653,6.4208374,5.13485718,-1004.22690582,63260,55871
2025-07-29 16:39:03.942 | DEBUG    | esensorlib.imu_fn:goto:524 - --no_init option specified, bypass setting in MODE_CTRL register
#Log End,2025-07-29 16:39:03.942461,,,,,,,,
#Sample Count,000000010,,,,,,,,
#Output Rate,100.0,,Filter Setting,MV_AVG128,,,,,
-----------------  -----------------  -------------  -----------
Date: 2025-07-29   Time: 16:39:03
-----------------  -----------------  -------------  -----------
PROD_ID: G366PDG0  VERSION: None      SERIAL: None
DOUT_RATE: 100.0   FILTER: MV_AVG128
NDFLAG: True       TEMPC: True        COUNTER: True  CHKSM: True
DLT: False         ATTI: False        QTN: False
-----------------  -----------------  -------------  -----------
Close:  com7 ,  460800 baud
```


## Flashing Device Back to Factory Default Registers Settings

Open a command prompt and run the appropriate `xxxx_logger.py` that matches the type of connected device:

1. Select COM port with `-s` switch (i.e., `-s com7`)
2. Use `--init_default` switch
3. The flash settings are now restored to factory defaults after power-on or reset

```
python3 -m esensorlib.example.imu_logger -s com7 --init_default
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Initial Backup Completed
```

## Help Screen Options

Run the `xxxx_logger.py` with the `-h` switch to list the switches and parameters for the logger software

### IMU Help Screen

```
usage: imu_logger.py [-h] [-s SERIAL_PORT] [-b {921600,460800,230400,1000000,1500000,2000000}]
                     [--secs SECS | --samples SAMPLES]
                     [--drate {2000,1000,500,250,125,62.5,31.25,15.625,400,200,100,80,50,40,25,20}]
                     [--filter {mv_avg0,mv_avg2,mv_avg4,mv_avg8,mv_avg16,mv_avg32,mv_avg64,mv_avg128,k32_fc25,k32_fc50,k32_fc100,k32_fc200,k32_fc400,k64_fc25,k64_fc50,k64_fc100,k64_fc200,k64_fc400,k128_fc25,k128_fc50,k128_fc100,k128_fc200,k128_fc400}]
                     [--model {g320pdg0,g320pdgn,g354pdh0,g364pdc0,g364pdca,g365pdc1,g365pdf1,g370pdf1,g370pds0,g330pdg0,g355qdg0,g366pdg0,g370pdg0,g370pdt0,g570pr20}]
                     [--a_range] [--bit16] [--csv] [--noscale] [--ndflags] [--tempc] [--chksm]
                     [--counter {reset,sample} | --ext_trigger]
                     [--dlt {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15} {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}]
                     [--atti {euler,incl}] [--qtn] [--atti_profile {modea,modeb,modec}]
                     [--atti_conv {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}] [--autostart]
                     [--init_default] [--flash_update] [--dump_reg] [--verbose] [--no_init] [--tag TAG]
                     [--max_rows MAX_ROWS]

This program is intended as sample code for evaluation testing the Epson device. This program will initialize the
device with user specified arguments and retrieve sensor data and format the output to console or CSV file. Other
misc. utility functions are described in the help.

options:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx.
  -b {921600,460800,230400,1000000,1500000,2000000}, --baud_rate {921600,460800,230400,1000000,1500000,2000000}
                        specifies baudrate of the serial port, default is 460800. Not all devices support range of
                        baudrates. This assumes the device serial port baudrate is already configured. Refer to
                        device datasheet.
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C
                        to abort and exit early.
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit
                        early.
  --drate {2000,1000,500,250,125,62.5,31.25,15.625,400,200,100,80,50,40,25,20}
                        specifies IMU output data rate in sps, default is 200sps.
  --filter {mv_avg0,mv_avg2,mv_avg4,mv_avg8,mv_avg16,mv_avg32,mv_avg64,mv_avg128,k32_fc25,k32_fc50,k32_fc100,k32_fc200,k32_fc400,k64_fc25,k64_fc50,k64_fc100,k64_fc200,k64_fc400,k128_fc25,k128_fc50,k128_fc100,k128_fc200,k128_fc400}
                        specifies the filter selection. If not specified, moving average filter based on selected
                        output data rate will automatically be selected. NOTE: Refer to datasheet for valid
                        settings.
  --model {g320pdg0,g320pdgn,g354pdh0,g364pdc0,g364pdca,g365pdc1,g365pdf1,g370pdf1,g370pds0,g330pdg0,g355qdg0,g366pdg0,g370pdg0,g370pdt0,g570pr20}
                        specifies the IMU model type, if not specified will auto-detect.
  --a_range             specifies to use 16G accelerometer output range instead of 8G. NOTE: Not all models support
                        this feature.
  --bit16               specifies to output sensor data in 16-bit resolution, otherwise uses 32-bit.
  --noscale             specifies to keep sensor data as digital counts (without applying scale factor conversion).
  --counter {reset,sample}
                        specifies to enable reset counter (EXT/GPIO2 pin) or sample counter in the sensor data.
  --ext_trigger         specifies to enable external trigger mode on EXT/GPIO2 pin.

output field options:
  --ndflags             specifies to enable ND/EA flags in sensor data.
  --tempc               specifies to enable temperature data in sensor data.
  --chksm               specifies to enable 16-bit checksum in sensor data.

attitude options:
  --atti {euler,incl}   specifies to enable attitude output in sensor data in euler mode or inclination mode. NOTE:
                        Not all devices support this mode. Refer to device datasheet.
  --qtn                 specifies to enable attitude quaternion data in sensor data. --atti_conv must be 0 for
                        quaternion output. NOTE: Not all devices support this mode. Refer to device datasheet.
  --atti_profile {modea,modeb,modec}
                        specifies the attitude motion profile when attitude euler or quaternion output is enabled.
                        NOTE: Not all devices support this feature. Refer to device datasheet.
  --atti_conv {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}
                        specifies the attitude axis conversion when attitude output is enabled. Must be between 0
                        to 23 (inclusive). Must be set to 0 for when quaternion output is enabled. NOTE: Not all
                        devices support this feature. Refer to device datasheet.

delta angle/velocity options:
  --dlt {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15} {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}
                        specifies to enable delta angle & delta velocity in sensor data with specified delta angle,
                        delta velocity scale factors. NOTE: Not all devices support this mode. Refer to device
                        datasheet.

flash-related options:
  --autostart           Enables AUTO_START function. Run logger again afterwards with --flash_update to store
                        current register settings to device flash.
  --init_default        This sets the device flash setting back to default register settings per datasheet.
  --flash_update        specifies to store the current device register settings to device flash without configuring
                        the device. Run the logger program with desired settings first, before re-running with the
                        --flash_update option.

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device.
  --verbose             specifies to enable low-level register messages for debugging purpose.
  --no_init             specifies to NOT initialize the device and assumes device is pre-configured for with
                        --autostart and already in SAMPLING mode. NOTE: User-specified options must match device
                        programmed --autostart settings.

csv options:
  --csv                 specifies to read sensor data to CSV file otherwise sends to console.
  --tag TAG             specifies an extra string to append to end of the filename if CSV is enabled.
  --max_rows MAX_ROWS   specifies to split CSV files when the number of samples exceeds specified max_rows.
```

### ACCL Help Screen

```
usage: accl_logger.py [-h] [-s SERIAL_PORT] [-b {460800,230400,115200}] [--secs SECS | --samples SAMPLES]
                      [--drate {1000,500,200,100,50}]
                      [--filter {k64_fc83,k64_fc220,k128_fc36,k128_fc110,k128_fc350,k512_fc9,k512_fc16,k512_fc60,k512_fc210,k512_fc460}]
                      [--model {a352ad10,a370ad10}] [--csv] [--tilt {0,1,2,3,4,5,6,7}] [--noscale]
                      [--reduced_noise] [--dis_temp_stabil] [--ndflags] [--tempc] [--chksm] [--counter]
                      [--ext_trigger {disabled,ext_trig_pos,ext_trig_neg,1pps_pos,1pps_neg}] [--autostart]
                      [--init_default] [--flash_update] [--dump_reg] [--no_init] [--verbose] [--tag TAG]
                      [--max_rows MAX_ROWS]

This program is intended as sample code for evaluation testing the Epson device. This program will initialize the
device with user specified arguments and retrieve sensor data and format the output to console or CSV file. Other
misc. utility functions are described in the help.

options:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx.
  -b {460800,230400,115200}, --baud_rate {460800,230400,115200}
                        specifies baudrate of the serial port, default is 460800. Not all devices support range of
                        baudrates. This assumes the device serial port baudrate is already configured. Refer to
                        device datasheet.
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C
                        to abort and exit early.
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit
                        early.
  --drate {1000,500,200,100,50}
                        specifies ACCL output data rate in sps, default is 200sps.
  --filter {k64_fc83,k64_fc220,k128_fc36,k128_fc110,k128_fc350,k512_fc9,k512_fc16,k512_fc60,k512_fc210,k512_fc460}
                        specifies the filter selection. If not specified, filter based on selected output data rate
                        will automatically be selected. NOTE: Refer to datasheet for valid settings.
  --model {a352ad10,a370ad10}
                        specifies the ACCL model type, if not specified will auto-detect.
  --tilt {0,1,2,3,4,5,6,7}
                        specifies tilt output for each X-Y-Z axes as a 3-bit enable mask (a 1 in bit position
                        enables tilt output on that axis).
  --noscale             specifies to keep sensor data as digital counts (without applying scale factor conversion).
  --reduced_noise       specifies to enabled reduced noise floor condition.Otherwise, standard noise floor
                        condition selected.
  --dis_temp_stabil     specifies to disable bias stabilization against thermal shock. Otherwise, enabled.
  --counter             specifies to enable sample counter in the sensor data.
  --ext_trigger {disabled,ext_trig_pos,ext_trig_neg,1pps_pos,1pps_neg}
                        specifies the external trigger mode on EXT pin. NOTE: Refer to datasheet for valid settings
                        for the model.

output field options:
  --ndflags             specifies to enable ND/EA flags in sensor data.
  --tempc               specifies to enable temperature data in sensor data.
  --chksm               specifies to enable 16-bit checksum in sensor data.

flash-related options:
  --autostart           Enables AUTO_START function. Run logger again afterwards with --flash_update to store
                        current register settings to device flash.
  --init_default        This sets the device flash setting back to default register settings per datasheet.
  --flash_update        specifies to store the current device register settings to device flash without configuring
                        the device. Run the logger program with desired settings first, before re-running with the
                        --flash_update option.

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device.
  --no_init             specifies to NOT initialize the device and assumes device is pre-configured for with
                        --autostart and already in SAMPLING mode. NOTE: User-specified options must match device
                        programmed --autostart settings.
  --verbose             specifies to enable low-level register messages for debugging.

csv options:
  --csv                 specifies to read sensor data to CSV file otherwise sends to console.
  --tag TAG             specifies an extra string to append to end of the filename if CSV is enabled.
  --max_rows MAX_ROWS   specifies to split CSV files when the number of samples exceeds specified max_rows.
```

### VIBE Help Screen

```
usage: vibe_logger.py [-h] [-s SERIAL_PORT] [-b {921600,460800,230400,115200}] [--secs SECS | --samples SAMPLES]
                      [--output_sel {velocity_raw,velocity_rms,velocity_pp,disp_raw,disp_rms,disp_pp}]
                      [--drate DRATE] [--urate URATE] [--model {a342vd10}] [--csv] [--noscale] [--ndflags]
                      [--counter] [--chksm] [--ext_pol_neg] [--tempc | --tempc8] [--autostart] [--init_default]
                      [--flash_update] [--dump_reg] [--no_init] [--verbose] [--tag TAG] [--max_rows MAX_ROWS]

This program is intended as sample code for evaluation testing the Epson device. This program will initialize the
device with user specified arguments and retrieve sensor data and format the output to console or CSV file. Other
misc. utility functions are described in the help.

options:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx.
  -b {921600,460800,230400,115200}, --baud_rate {921600,460800,230400,115200}
                        specifies baudrate of the serial port, default is 460800. Not all devices support range of
                        baudrates. This assumes the device serial port baudrate is already configured. Refer to
                        device datasheet.
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C
                        to abort and exit early.
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit
                        early.
  --output_sel {velocity_raw,velocity_rms,velocity_pp,disp_raw,disp_rms,disp_pp}
                        specifies VIB output type for velocity or displacement, default is velocity_rms. When
                        output_sel is velocity_raw or disp_raw, the --drate, --urate options are ignored and not
                        used.
  --drate DRATE         specifies VIB output rate in Hz. The supported output rate depends on output_sel mode.
                        Velocity = 0.039 ~ 10 Hz. Displacement = 0.0039 ~ 1 Hz. For output_sel mode velocity_raw or
                        disp_raw, this switch is ignored. The specified output rate in Hz is converted to a value
                        for DOUT_RATE_RMSPP.
  --urate URATE         specifies VIB update rate in Hz. The update rate depends on output_sel mode and specifies
                        the time period for calculating the RMS or peak-peak values from the internal raw
                        velocity/displacement data. Velocity = 0.0057 ~ 187.5 Hz. Displacement = 0.00057 ~ 18.75
                        Hz. For output_sel mode velocity_raw or disp_raw, this switch is ignored. The update rate
                        in HZ is converted to a value for UPDATE_RATE_RMSPP.
  --model {a342vd10}    specifies the VIB model type, if not specified will auto-detect.
  --noscale             specifies to keep sensor data as digital counts (without applying scale factor conversion).
  --ext_pol_neg         specifies to set external terminal to active low on EXT pin.
  --tempc               specifies to enable 16-bit temperature data in sensor data.
  --tempc8              specifies to enable 8-bit temperature data in sensor data the other 8-bits represents
                        EXI_ERR, and 2BIT_COUNT.

output field options:
  --ndflags             specifies to enable ND/EA flags in sensor data.
  --counter             specifies to enable sample counter in the sensor data.
  --chksm               specifies to enable 16-bit checksum in sensor data.

flash-related options:
  --autostart           Enables AUTO_START function. Run logger again afterwards with --flash_update to store
                        current register settings to device flash.
  --init_default        This sets the device flash setting back to default register settings per datasheet.
  --flash_update        specifies to store the current device register settings to device flash without configuring
                        the device. Run the logger program with desired settings first, before re-running with the
                        --flash_update option.

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device.
  --no_init             specifies to NOT initialize the device and assumes device is pre-configured for with
                        --autostart and already in SAMPLING mode. NOTE: User-specified options must match device
                        programmed --autostart settings.
  --verbose             specifies to enable low-level register messages for debugging.

csv options:
  --csv                 specifies to read sensor data to CSV file otherwise sends to console.
  --tag TAG             specifies an extra string to append to end of the filename if CSV is enabled.
  --max_rows MAX_ROWS   specifies to split CSV files when the number of samples exceeds specified max_rows.
```

# File Listing
--------------

File                                           | Description / Comment
-----------------------------------------------|----------------------
src\                                           | Python source directory
src\esensorlib\accl_fn.py                      | AcclFn class for accelerometer functions used by SensorDevice class
src\esensorlib\imu_fn.py                       | ImuFn class for IMU functions used by SensorDevice class
src\esensorlib\reg_interface.py                | RegInterface class for register I/O used by SensorDevice class
src\esensorlib\sensor_device.py                | SensorDevice class is top-level class to be instantiated by user
src\esensorlib\spi_port.py                     | ** This is not implemented yet ** SPI port class for low-level I/O to the device
src\esensorlib\uart_port.py                    | UART port class for low-level I/O to the device
src\esensorlib\vib_fn.py                       | VibFn class for vibration sensor functions used by SensorDevice class
src\esensorlib\README.md                       | Readme describing SensorDevice class usage
src\esensorlib\example\accl_logger.py          | Logger example for ACCL (accelerometer) devices
src\esensorlib\example\helper.py               | Logger helper class (for formatting and file I/O)
src\esensorlib\example\imu_logger.py           | Logger example for IMU (inertial measurement unit) devices
src\esensorlib\example\vibe_logger.py          | Logger example for VIBE (vibration sensor) devices
src\esensorlib\model\mcore.py                  | Core model definition/constants (temporarily used for auto-detect)
src\esensorlib\model\mg320.py                  | M-G320PDG0 model definition/constants
src\esensorlib\model\mg354.py                  | M-G354PDH0 model definition/constants
src\esensorlib\model\mg355qdg0.py              | M-G355QDG0 model definition/constants
src\esensorlib\model\mg364pdc0.py              | M-G364PDC0 model definition/constants
src\esensorlib\model\mg364pdca.py              | M-G364PDCA model definition/constants
src\esensorlib\model\mg365pdc1.py              | M-G365PDC1 model definition/constants
src\esensorlib\model\mg365pdf1.py              | M-G365PDF1 model definition/constants
src\esensorlib\model\mg366pdg0.py              | M-G366PDG0/M-G330PDG0 model definition/constants
src\esensorlib\model\mg370pdf1.py              | M-G370PDF1 model definition/constants
src\esensorlib\model\mg370pdg0.py              | M-G370PDG0 model definition/constants
src\esensorlib\model\mg370pds0.py              | M-G370PDS0 model definition/constants
src\esensorlib\model\mg370pdt0.py              | M-G370PDT0 model definition/constants
src\esensorlib\model\mg570pr20.py              | M-G570PR20 model definition/constants
src\esensorlib\model\ma342vd10.py              | M-A342VD10 model definition/constants
src\esensorlib\model\ma352ad10.py              | M-A352AD10 model definition/constants
src\esensorlib\model\ma370ad10.py              | M-A370AD10 model definition/constants
LICENSE                                        | License file
pyproject.toml                                 | Contains build system requirements and information, which are used by pip to build the package
README.md                                      | This general readme file


# Change Record
--------------

Date        | Version   | Description / Comment
------------|-----------|----------------------
2023-02-24  | v1.0.0    | Initial release
2024-06-21  | v2.0.0    | Major redesign of code base, added support for IMU G570PR20, Accl A352AD10, Vibe A342VD10
2025-07-29  | v2.1.0    | Added no_init option, added support for IMU G355QDG0, Accl A370AD10
