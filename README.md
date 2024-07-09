
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
  * *SensorDevice* main class is composed of 5 subclasses *UartPort*, *RegInterface*, and one of the following *AcclFn*, *ImuFn*, or *VibFn* depending on the type of device
    * Primary purpose is to communicate and control the sensing device
    * Provide low-level functions to read/write registers
    * Provide functions to perform self-tests, software reset, flash-related functions
    * Provide functions to configure the device, and enter CONFIG/SAMPLING mode
    * Provide functions to read a burst sample when in  SAMPLING mode
    * Expose properties to read various statuses and device model information
    * For more detailed information on using the *SensorDevice* class refer to the README.md in the `src/esensorlib/` folder
  * A example logger comes in 3 variants based on the sensing device types: *accl_logger.py*, *imu_logger.py*, *vibe_logger.py*
    * It is intended as evaluation software and as a reference on how to use the *SensorDevice* class to control and read sensor data
    * It uses the *LoggerHelper* class for parsing and formatting sensor device status and sensor data
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


# Logger Usage
--------------
  * There is a logger programs for each of the 3 device types
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

**NOTE:** Add the `--csv` switch to send the sensor data to a CSV files instead of the output console
```
python3 -m esensorlib.example.imu_logger -s com7 --drate 200 --filter k32_fc50 --samples 100
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Dlt disabled. Bypassing.
Attitude or Quaternion disabled. Bypassing.
Start Log: 2024-06-11 12:02:29.830146
#Log created,,,Output Rate,200.0,Filter Setting,K32_FC50,,,
#Creation Date:,2024-06-11 12:02:29.830146,PROD_ID=G366PDG0,VERSION=373,SERIAL_NUM=T1000062,,,,,
#Scaled Data,SF_GYRO=+0.01515152/2^16 (deg/s)/bit,SF_ACCL=+0.25000000/2^16 mg/bit
Sample No.,Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG]
0,0.17765299,-0.0460145,0.00214247,2.1502533,6.28370667,91.74726868
1,0.05104851,-0.00950923,-0.00730711,8.3056488,8.00406647,796.34479523
2,-0.01316464,0.00648961,-0.01723919,10.33483887,8.135849,1000.58912659
3,-0.01592347,0.01274941,0.00672866,9.9491806,7.927948,1001.35240173
4,-0.00865474,0.01621593,0.00561547,9.56713867,8.39748383,1001.05265808
5,-0.0213237,-0.00051695,-0.02514094,9.17617798,8.38954926,1001.07421875
6,-0.01478554,-0.00031396,-0.01239037,9.84323883,8.48654938,1000.64748383
7,-0.00332665,-0.0076939,-0.0365159,10.94252014,8.54973602,1000.58926392
8,0.00025639,-0.00816345,-0.02707788,10.50254822,8.3022995,1001.23961639
9,-0.00409814,-0.00109123,-0.00167222,10.41840363,7.87080383,1001.17864227
.
.
.
90,0.0186185,0.00201439,-0.02630638,10.76303101,8.44337463,1001.57707977
91,-0.00515816,0.01418304,-0.0330258,10.25996399,8.56550598,1001.5146637
92,-0.00131387,0.00271098,-0.01800907,10.24481964,8.37974548,1000.80552673
93,-0.00034841,0.02794601,0.00507285,10.57369995,8.16768646,1000.81603241
94,-0.01513811,0.00263052,0.01499916,11.16758728,7.78646851,1000.9238739
95,-0.01777395,0.01857087,0.02422287,10.74871063,7.78466034,1000.78942871
96,0.00474988,0.0159459,-0.01597387,10.21640015,8.24372864,1000.51219177
97,0.00461879,0.03245406,-0.0459063,10.05867767,8.3821106,1000.13761139
98,-0.01261948,0.00414207,-0.03243371,10.06912994,8.37178802,1000.39889526
99,-0.01599029,0.01341109,0.00982805,9.87325287,8.19876862,1001.62425995
#Log End,2024-06-11 12:02:30.342238,,,,,,,,
#Sample Count,000000100,,,,,,,,
#Output Rate,200.0,,Filter Setting,K32_FC50,,,,,
-----------------  ----------------  ----------------  ------------
Date: 2024-06-11   Time: 12:02:30
-----------------  ----------------  ----------------  ------------
PROD_ID: G366PDG0  VERSION: 373      SERIAL: T1000062
DOUT_RATE: 200.0   FILTER: K32_FC50
NDFLAG: False      TEMPC: False      COUNTER: False    CHKSM: False
DLT: False         ATTI: False       QTN: False
-----------------  ----------------  ----------------  ------------
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

**NOTE:** Add the `--csv` switch to send the sensor data to a CSV files instead of the output console
```
python3 -m esensorlib.example.accl_logger -s com14 --drate 200 --filter k128_fc36 --samples 100
Model not specified, attempting to auto-detect
Open:  com14 ,  460800
Detected: A352AD10
Start Log: 2024-06-11 13:29:32.134457
#Log created,,,Output Rate,200.0,Filter Setting,K128_FC36,,,
#Creation Date:,2024-06-11 13:29:32.134457,PROD_ID=A352AD10,VERSION=0D,SERIAL_NUM=W0000501,,,,,
#Scaled Data,SF_ACCL=+0.00006000 mg/bit
Sample No.,Ax[mG],Ay[mG],Az[mG]
0,-12.66552,36.13458,1003.85238
1,-12.78234,36.18906,1004.29872
2,-12.72396,36.39714,1004.44692
3,-12.6696,36.51066,1004.83998
4,-12.73236,36.42846,1005.5496
5,-12.75996,36.30018,1005.85848
6,-12.77688,36.2496,1005.64938
7,-12.8286,36.3018,1005.21456
8,-12.68418,36.4113,1004.52528
9,-12.41376,36.46464,1003.75128
.
.
.
90,-13.08882,36.49302,1005.89754
91,-12.70896,36.58008,1006.65426
92,-12.39642,36.66714,1007.06292
93,-12.53196,36.79848,1006.84212
94,-12.77112,36.77724,1005.9765
95,-12.87816,36.4758,1004.8215
96,-12.97302,36.10464,1003.79754
97,-12.90564,35.95476,1003.08084
98,-12.53148,36.06276,1002.726
99,-12.23376,36.28764,1002.79512
#Log End,2024-06-11 13:29:32.672292,,,,,,,,
#Sample Count,000000100,,,,,,,,
#Output Rate,200.0,,Filter Setting,K128_FC36,,,,,
-----------------  -----------------  ----------------  ------------
Date: 2024-06-11   Time: 13:29:32
-----------------  -----------------  ----------------  ------------
PROD_ID: A352AD10  VERSION: 0D        SERIAL: W0000501
DOUT_RATE: 200.0   FILTER: K128_FC36
NDFLAG: False      TEMPC: False       COUNTER: False    CHKSM: False

-----------------  -----------------  ----------------  ------------
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

**NOTE:** Add the `--csv` switch to send the sensor data to a CSV files instead of the output console
```
python3 -m esensorlib.example.vibe_logger -s com10 --output_sel velocity_rms --drate 10 --urate 99 --samples 100
Model not specified, attempting to auto-detect
Open:  com10 ,  460800
Detected: A342VD10
Start Log: 2024-06-11 14:27:02.661445
#Log created,,,Output Rate,1,Filter Setting,NA,Output Sel,VELOCITY_RMS,
#Creation Date:,2024-06-11 14:27:02.661445,PROD_ID=A342VD10,VERSION=280,SERIAL_NUM=00000094,,,,,
#Scaled Data,SF_VEL=+0.00023800 (mm/s)/bit
Sample No.,Vx[mm/s],Vy[mm/s],Vz[mm/s]
0,0.009044,0.010948,0.200634
1,0.011186,0.008806,0.06307
2,0.009044,0.006902,0.067592
3,0.017612,0.004522,0.126378
4,0.0119,0.010472,0.068782
5,0.033796,0.013566,0.105672
6,0.021896,0.010472,0.017612
7,0.018802,0.014756,0.071162
8,0.006426,0.006426,0.066164
9,0.007854,0.00833,0.039508
.
.
.
90,0.009044,0.010948,0.04879
91,0.005712,0.004284,0.11424
92,0.008092,0.015232,0.115668
93,0.012614,0.008806,0.037128
94,0.004522,0.007854,0.020468
95,0.009996,0.008806,0.02737
96,0.00357,0.00952,0.119476
97,0.006664,0.006664,0.16779
98,0.007616,0.00952,0.090678
99,0.004522,0.006188,0.009996
#Log End,2024-06-11 14:27:12.839649,,,,,,,,
#Sample Count,000000100,,,,,,,,
#Output Rate,1,,Filter Setting,NA,,Output Sel,VELOCITY_RMS,,
-------------------  --------------  ----------------  ------------
Date: 2024-06-11     Time: 14:27:12
-------------------  --------------  ----------------  ------------
PROD_ID: A342VD10    VERSION: 280    SERIAL: 00000094
DOUT_RATE_RMSPPP: 1  UPDATE_RATE: 0
NDFLAG: False        TEMPC: False    COUNTER: False    CHKSM: False

-------------------  --------------  ----------------  ------------
```

## Reading Out Current Registers

### IMU Register Data

Open a command prompt and run `imu_logger.py` with the appropriate command line switches:
1. Select COM port with `-s` switch (i.e., `-s COM7`)
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
1. Select COM port with `-s` switch (i.e., `-s COM10`)
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

Configuring a device for AUTO_START is a two stage process.
Run the `xxxx_logger.py` that matches your connected device to first configure the desired device settings and with `--auto_start`.
Then, run the `xxxx_logger.py` again with the `--flash_update` switch to store the settings to non-volatile memory of the device.

### AUTO_START Mode

*AUTO_START* mode is intended for the UART interface only so that the device will automatically retrieve user-programmed settings from device flash after power-on or reset
and automatically enter SAMPLING mode to start sending sensor data.

**NOTE:** Be sure to run the `xxxx_logger.py` that matches the connected device type.

For example, below is an example for an IMU using `imu_logger.py`:

1. Select COM port with `-s` switch (i.e., `-s com7`)
2. Select the correct model with `--model` switch or do not specify the switch to let the software auto-detect
3. Select the desired output rate with the `--drate` switch (i.e., `--drate 100` for 100Hz)
4. Select the desired filter setting `--filter` switch (i.e., `--filter K128_FC25`)
5. Select `--autostart` switch
6. Select other output field options as desired such as `--ndflags` `--tempc` `--counter sample` `--chksm`
7. Press CTRL-C to exit early or let the logger complete and finish its operation
```
python -m esensorlib.example.imu_logger -s com7 --drate 100 --filter mv_avg128 --autostart --ndflags --tempc --counter sample --chksm
Model not specified, attempting to auto-detect
Open:  com7 ,  460800
Detected: G366PDG0
Dlt disabled. Bypassing.
Attitude or Quaternion disabled. Bypassing.
Start Log: 2024-06-11 14:56:54.349805
#Log created,,,Output Rate,100.0,Filter Setting,MV_AVG128,,,
#Creation Date:,2024-06-11 14:56:54.349805,PROD_ID=G366PDG0,VERSION=373,SERIAL_NUM=T1000062,,,,,
#Scaled Data,SF_ACCL=+0.25000000/2^16 mg/bit,SF_TEMPC=+0.00390625/2^16 degC/bit,SF_GYRO=+0.01515152/2^16 (deg/s)/bit
Sample No.,Flags[dec],Ts[degC],Gx[dps],Gy[dps],Gz[dps],Ax[mG],Ay[mG],Az[mG],Counter[dec],Chksm16[dec]
0,65276,24.8438,0.16393789,-0.04179452,0.003433,-31.20108795,86.61482239,118.74742126,20,61545
1,65276,24.6918,0.13401031,-0.0311062,0.00260232,-63.57322693,167.09786224,250.58969879,40,34840
2,65276,24.5371,0.10590663,-0.02248984,-0.00158137,-96.02385712,247.59860229,382.58917236,60,38310
3,65276,24.3802,0.07154338,-0.01399323,-0.00473508,-128.45758057,328.11968231,514.50144196,80,34220
4,65276,24.2273,0.03967308,-0.00520163,-0.00651204,-160.96394348,408.53707123,646.38239288,100,59244
5,65276,24.0752,0.00540693,-0.00076109,-0.00776302,-193.33174133,488.97183228,778.35786438,120,6280
6,65276,24.0156,-0.00989579,-0.00158738,-0.00926116,-206.21827698,521.18305206,831.11870575,140,1901
7,65276,24.0145,-0.0056113,-0.00104037,-0.0163558,-206.24491882,521.17608643,831.26002502,160,1935
8,65276,24.0153,-0.00459613,-0.0050895,-0.01800075,-206.18806458,521.13359833,831.21425629,180,51308
9,65276,24.0191,-0.00376545,-0.00867832,-0.02001953,-206.27063751,521.1313324,831.09406281,200,41942
10,65276,24.0202,-0.0030254,-0.0100604,-0.02253515,-206.15485382,521.06364441,831.0521698,220,48364
11,65276,24.0169,-0.00377771,-0.01173794,-0.02382799,-206.0394516,521.12828827,831.1150589,240,40669
CTRL-C: Exiting
Stop reading sensor
#Log End,2024-06-11 14:56:57.907024,,,,,,,,
#Sample Count,000000354,,,,,,,,
#Output Rate,100.0,,Filter Setting,MV_AVG128,,,,,
-----------------  -----------------  ----------------  -----------
Date: 2024-06-11   Time: 14:56:57
-----------------  -----------------  ----------------  -----------
PROD_ID: G366PDG0  VERSION: 373       SERIAL: T1000062
DOUT_RATE: 100.0   FILTER: MV_AVG128
NDFLAG: True       TEMPC: True        COUNTER: True     CHKSM: True
DLT: False         ATTI: False        QTN: False
-----------------  -----------------  ----------------  -----------
```

### Flashing Settings

To store the current device settings to flash, run the `xxxx_logger.py` python script with `--flash_update` option:
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

## Flashing Device Back to Factory Default Registers Settings

Open a command prompt and run the `xxxx_logger.py` that matches the type of connected device:

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
usage: imu_logger.py [-h] [-s SERIAL_PORT] [-b {921600,460800,230400,1000000,1500000,2000000}] [--secs SECS | --samples SAMPLES]
                     [--drate {2000,1000,500,250,125,62.5,31.25,15.625,400,200,100,80,50,40,25,20}]
                     [--filter {mv_avg0,mv_avg2,mv_avg4,mv_avg8,mv_avg16,mv_avg32,mv_avg64,mv_avg128,k32_fc25,k32_fc50,k32_fc100,k32_fc200,k32_fc400,k64_fc25,k64_fc50,k64_fc100,k64_fc200,k64_fc400,k128_fc25,k128_fc50,k128_fc100,k128_fc200,k128_fc400}]
                     [--model {g320,g354,g364pdc0,g364pdca,g365pdc1,g365pdf1,g370pdf1,g370pds0,g330pdg0,g366pdg0,g370pdg0,g370pdt0,g570pr20}] [--a_range] [--bit16]
                     [--csv] [--noscale] [--ndflags] [--tempc] [--chksm] [--counter {reset,sample} | --ext_trigger]
                     [--dlt {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15} {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}] [--atti {euler,incl}] [--qtn]
                     [--atti_profile {modea,modeb,modec}] [--atti_conv {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23}] [--autostart] [--init_default]
                     [--flash_update] [--dump_reg] [--verbose] [--tag TAG] [--max_rows MAX_ROWS]

This program is intended as sample code for evaluation testing the Epson device. This program will initialize the device with user specified arguments and retrieve sensor
data and format the output to console or CSV file. Other misc. utility functions are described in the help

optional arguments:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx
  -b {921600,460800,230400,1000000,1500000,2000000}, --baud_rate {921600,460800,230400,1000000,1500000,2000000}
                        specifies baudrate of the serial port, default is 460800. Not all devices support range of baudrates
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C to abort and exit early
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit early
  --drate {2000,1000,500,250,125,62.5,31.25,15.625,400,200,100,80,50,40,25,20}
                        specifies IMU output data rate in sps, default is 200sps
  --filter {mv_avg0,mv_avg2,mv_avg4,mv_avg8,mv_avg16,mv_avg32,mv_avg64,mv_avg128,k32_fc25,k32_fc50,k32_fc100,k32_fc200,k32_fc400,k64_fc25,k64_fc50,k64_fc100,k64_fc200,k64_fc400,k128_fc25,k128_fc50,k128_fc100,k128_fc200,k128_fc400}
                        specifies the filter selection. If not specified, moving average filter based on selected output data rate will automatically be selected. NOTE:
                        Refer to datasheet for valid settings.
  --model {g320,g354,g364pdc0,g364pdca,g365pdc1,g365pdf1,g370pdf1,g370pds0,g330pdg0,g366pdg0,g370pdg0,g370pdt0,g570pr20}
                        specifies the IMU model type, if not specified will auto-detect
  --a_range             specifies to use 16G accelerometer output range instead of 8G. NOTE: Not all models support this feature.
  --bit16               specifies to output sensor data in 16-bit resolution, otherwise use 32-bit.
  --csv                 specifies to read sensor data to CSV file otherwise sends to console.
  --noscale             specifies to keep sensor data as digital counts (without applying scale factor conversion)
  --counter {reset,sample}
                        specifies to enable reset counter (EXT/GPIO2 pin) or sample counter in the sensor data
  --ext_trigger         specifies to enable external trigger mode on EXT/GPIO2 pin
  --tag TAG             specifies extra string to append to end of the filename if CSV is enabled
  --max_rows MAX_ROWS   specifies to split CSV files when # of samples exceeds max_rows

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
                        specifies the attitude axis conversion when attitude euler output is enabled. Must be between 0 to 23 (inclusive). This must be set to 0 for when
                        quaternion output is enabled NOTE: Not all devices support this feature.

delta angle/velocity options:
  --dlt {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15} {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}
                        specifies to enable delta angle & delta velocity in sensor data with specified delta angle, delta velocity scale factors. NOTE: Not all devices
                        support this mode.

flash-related options:
  --autostart           Enables AUTO_START function. Run logger again afterwards with --flash_update to store the register settings to device flash
  --init_default        This sets the flash setting back to default register settings per datasheet.
  --flash_update        specifies to store current register settings to device flash.

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device
  --verbose             specifies to enable low-level register messages for debugging
```

### ACCL Help Screen

```
usage: accl_logger.py [-h] [-s SERIAL_PORT] [-b {460800,230400,115200}] [--secs SECS | --samples SAMPLES] [--drate {1000,500,200,100,50}]
                      [--filter {k64_fc83,k64_fc220,k128_fc36,k128_fc110,k128_fc350,k512_fc9,k512_fc16,k512_fc60,k512_fc210,k512_fc460}] [--model {a352ad10}] [--csv]
                      [--tilt {0,1,2,3,4,5,6,7}] [--noscale] [--ndflags] [--tempc] [--chksm] [--counter] [--ext_trigger] [--autostart] [--init_default] [--flash_update]
                      [--dump_reg] [--verbose] [--tag TAG] [--max_rows MAX_ROWS]

This program is intended as sample code for evaluation testing the Epson device. This program will initialize the device with user specified arguments and retrieve sensor
data and format the output to console or CSV file. Other misc. utility functions are described in the help

optional arguments:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx
  -b {460800,230400,115200}, --baud_rate {460800,230400,115200}
                        specifies baudrate of the serial port, default is 460800. Not all devices support range of baudrates
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C to abort and exit early
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit early
  --drate {1000,500,200,100,50}
                        specifies ACCL output data rate in sps, default is 200sps
  --filter {k64_fc83,k64_fc220,k128_fc36,k128_fc110,k128_fc350,k512_fc9,k512_fc16,k512_fc60,k512_fc210,k512_fc460}
                        specifies the filter selection. If not specified, filter based on selected output data rate will automatically be selected. NOTE: Refer to
                        datasheet for valid settings.
  --model {a352ad10}    specifies the ACCL model type, if not specified will auto-detect
  --csv                 specifies to read sensor data to CSV file otherwise sends to console.
  --tilt {0,1,2,3,4,5,6,7}
                        specifies tilt output for each X-Y-Z axes as a 3-bit enable mask (a 1 in bit position enables tilt output on that axis)
  --noscale             specifies to keep sensor data as digital counts (without applying scale factor conversion)
  --counter             specifies to enable sample counter in the sensor data
  --ext_trigger         specifies to enable external trigger on EXT pin
  --tag TAG             specifies extra string to append to end of the filename if CSV is enabled
  --max_rows MAX_ROWS   specifies to split CSV files when # of samples exceeds max_rows

output field options:
  --ndflags             specifies to enable ND/EA flags in sensor data
  --tempc               specifies to enable temperature data in sensor data
  --chksm               specifies to enable 16-bit checksum in sensor data

flash-related options:
  --autostart           Enables AUTO_START function. Run logger again afterwards with --flash_update to store the register settings to device flash
  --init_default        This sets the flash setting back to default register settings per datasheet.
  --flash_update        specifies to store current register settings to device flash.

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device
  --verbose             specifies to enable low-level register messages for debugging
```

### VIBE Help Screen

```
usage: vibe_logger.py [-h] [-s SERIAL_PORT] [-b {921600,460800,230400,115200}] [--secs SECS | --samples SAMPLES]
                      [--output_sel {velocity_raw,velocity_rms,velocity_pp,disp_raw,disp_rms,disp_pp}] [--drate DRATE] [--urate URATE] [--model {a342vd10}] [--csv]
                      [--noscale] [--ndflags] [--counter] [--chksm] [--ext_pol_neg] [--tempc | --tempc8] [--autostart] [--init_default] [--flash_update] [--dump_reg]
                      [--verbose] [--tag TAG] [--max_rows MAX_ROWS]

This program is intended as sample code for evaluation testing the Epson device. This program will initialize the device with user specified arguments and retrieve sensor
data and format the output to console or CSV file. Other misc. utility functions are described in the help

optional arguments:
  -h, --help            show this help message and exit
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        specifies the serial port comxx or /dev/ttyUSBx
  -b {921600,460800,230400,115200}, --baud_rate {921600,460800,230400,115200}
                        specifies baudrate of the serial port, default is 460800. Not all devices support range of baudrates
  --secs SECS           specifies time duration of reading sensor data in seconds, default 5 seconds. Press CTRL-C to abort and exit early
  --samples SAMPLES     specifies the approx number samples to read sensor data. Press CTRL-C to abort and exit early
  --output_sel {velocity_raw,velocity_rms,velocity_pp,disp_raw,disp_rms,disp_pp}
                        specifies VIB output type for velocity or displacement, default is velocity_rms. When output_sel is velocity_raw or disp_raw, the --drate, --urate
                        options are ignored and not used.
  --drate DRATE         specifies VIB output rate in Hz, The supported output rate depends on output_sel mode. Velocity = 0.039 ~ 10 Hz, Displacement = 0.0039 ~ 1 Hz, For
                        output_sel mode velocity_raw or disp_raw, this switch is ignored. The specified output rate in HZ is converted to a value for DOUT_RATE_RMSPP.
  --urate URATE         specifies VIB update rate in Hz, The update rate depends on output_sel mode and specifies the time period for calculating the RMS or peak-peak
                        values from the internal raw velocity/displacement data Velocity = 0.0057 ~ 187.5 Hz, Displacement = 0.00057 ~ 18.75 Hz, For output_sel mode
                        velocity_raw or disp_raw, this switch is ignored. The update rate in HZ is converted to a value for UPDATE_RATE_RMSPP.
  --model {a342vd10}    specifies the VIB model type, if not specified will auto-detect
  --csv                 specifies to read sensor data to file otherwise sends to console. An optional string parameter if specified will be appended to filename
  --noscale             specifies to keep sensor data as digital counts (without applying scale factor conversion)
  --ext_pol_neg         specifies to set external terminal to active low on EXT pin
  --tempc               specifies to enable 16-bit temperature data in sensor data
  --tempc8              specifies to enable 8-bit temperature data in sensor data the other 8-bits represents EXI_ERR, and 2BIT_COUNT.
  --tag TAG             specifies extra string to append to end of the filename if CSV is enabled
  --max_rows MAX_ROWS   specifies to split CSV files when # of samples exceeds max_rows

output field options:
  --ndflags             specifies to enable ND/EA flags in sensor data
  --counter             specifies to enable sample counter in the sensor data
  --chksm               specifies to enable 16-bit checksum in sensor data

flash-related options:
  --autostart           Enables AUTO_START function. Run logger again afterwards with --flash_update to store the register settings to device flash
  --init_default        This sets the flash setting back to default register settings per datasheet.
  --flash_update        specifies to store current register settings to device flash.

debug options:
  --dump_reg            specifies to read out all the registers from the device without configuring device
  --verbose             specifies to enable low-level register messages for debugging
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
src\esensorlib\model\mg364pdc0.py              | M-G364PDC0 model definition/constants
src\esensorlib\model\mg364pdca.py              | M-G364PDCA model definition/constants
src\esensorlib\model\mg365pdc1.py              | M-G365PDC1 model definition/constants
src\esensorlib\model\mg365pdf1.py              | M-G365PDF1 model definition/constants
src\esensorlib\model\mg366pdg0.py              | M-G366PDG0/G-G330PDG0 model definition/constants
src\esensorlib\model\mg370pdf1.py              | M-G370PDF1 model definition/constants
src\esensorlib\model\mg370pdg0.py              | M-G370PDG0 model definition/constants
src\esensorlib\model\mg370pds0.py              | M-G370PDS0 model definition/constants
src\esensorlib\model\mg370pdt0.py              | M-G370PDT0 model definition/constants
src\esensorlib\model\mg570pr20.py              | M-G570PR20 model definition/constants
src\esensorlib\model\ma342vd10.py              | M-A342VD10 model definition/constants
src\esensorlib\model\ma352ad10.py              | M-A352AD10 model definition/constants
LICENSE                                        | License file
pyproject.toml                                 | Contains build system requirements and information, which are used by pip to build the package
README.md                                      | This general readme file


# Change Record
--------------

Date        | Version   | Description / Comment
------------|-----------|----------------------
2023-02-24  | v1.0.0    | Initial release
2024-06-21  | v2.0.0    | Major redesign of code base, added support for IMU G570PR20, Accl A352AD10, Vibe A342VD10
