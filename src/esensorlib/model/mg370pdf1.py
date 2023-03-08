# MIT License

# Copyright (c) 2023, Seiko Epson Corporation

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Constant and definition for IMU M-G370PDF1"""

from collections import namedtuple

# Low-level UART
BURST_MARKER = 0x80
DELIMITER = 0x0D
WINID = 0x07E

# Low-level UART Timing Delays max in seconds
TSTALL = 70e-6
TWRITERATE = 350e-6
TREADRATE = 350e-6

# register map by namedtuple
reg = namedtuple("reg", "winid addr addrh", defaults=[None, None, None])

BURST = reg(0, 0x00)
MODE_CTRL = reg(0, 0x02, 0x03)
DIAG_STAT = reg(0, 0x04)
FLAG = reg(0, 0x06)
GPIO = reg(0, 0x08, 0x09)
COUNT = reg(0, 0x0A)
RANGE_OVER = reg(0, 0x0C)
TEMP_HIGH = reg(0, 0x0E)
TEMP_LOW = reg(0, 0x10)
XGYRO_HIGH = reg(0, 0x12)
XGYRO_LOW = reg(0, 0x14)
YGYRO_HIGH = reg(0, 0x16)
YGYRO_LOW = reg(0, 0x18)
ZGYRO_HIGH = reg(0, 0x1A)
ZGYRO_LOW = reg(0, 0x1C)
XACCL_HIGH = reg(0, 0x1E)
XACCL_LOW = reg(0, 0x20)
YACCL_HIGH = reg(0, 0x22)
YACCL_LOW = reg(0, 0x24)
ZACCL_HIGH = reg(0, 0x26)
ZACCL_LOW = reg(0, 0x28)
RT_DIAG = reg(0, 0x2A)
ID = reg(0, 0x4C)
XDLTA_HIGH = reg(0, 0x64)
XDLTA_LOW = reg(0, 0x66)
YDLTA_HIGH = reg(0, 0x68)
YDLTA_LOW = reg(0, 0x6A)
ZDLTA_HIGH = reg(0, 0x6C)
ZDLTA_LOW = reg(0, 0x6E)
XDLTV_HIGH = reg(0, 0x70)
XDLTV_LOW = reg(0, 0x72)
YDLTV_HIGH = reg(0, 0x74)
YDLTV_LOW = reg(0, 0x76)
ZDLTV_HIGH = reg(0, 0x78)
ZDLTV_LOW = reg(0, 0x7A)
SIG_CTRL = reg(1, 0x00, 0x01)
MSC_CTRL = reg(1, 0x02, 0x03)
SMPL_CTRL = reg(1, 0x04, 0x05)
FILTER_CTRL = reg(1, 0x06, 0x07)
UART_CTRL = reg(1, 0x08, 0x09)
GLOB_CMD = reg(1, 0x0A, 0x0B)
BURST_CTRL1 = reg(1, 0x0C, 0x0D)
BURST_CTRL2 = reg(1, 0x0E, 0x0F)
POL_CTRL = reg(1, 0x10, 0x11)
DLT_CTRL = reg(1, 0x12, 0x13)
ATTI_CTRL = reg(1, 0x14, 0x15)
GLOB_CMD2 = reg(1, 0x16, 0x17)
R_MATRIX_G_M11 = reg(1, 0x38, 0x39)
R_MATRIX_G_M12 = reg(1, 0x3A, 0x3B)
R_MATRIX_G_M13 = reg(1, 0x3C, 0x3D)
R_MATRIX_G_M21 = reg(1, 0x3E, 0x3F)
R_MATRIX_G_M22 = reg(1, 0x40, 0x41)
R_MATRIX_G_M23 = reg(1, 0x42, 0x43)
R_MATRIX_G_M31 = reg(1, 0x44, 0x45)
R_MATRIX_G_M32 = reg(1, 0x46, 0x47)
R_MATRIX_G_M33 = reg(1, 0x48, 0x49)
R_MATRIX_A_M11 = reg(1, 0x4A, 0x4B)
R_MATRIX_A_M12 = reg(1, 0x4C, 0x4D)
R_MATRIX_A_M13 = reg(1, 0x4E, 0x4F)
R_MATRIX_A_M21 = reg(1, 0x50, 0x51)
R_MATRIX_A_M22 = reg(1, 0x52, 0x53)
R_MATRIX_A_M23 = reg(1, 0x54, 0x55)
R_MATRIX_A_M31 = reg(1, 0x56, 0x57)
R_MATRIX_A_M32 = reg(1, 0x58, 0x59)
R_MATRIX_A_M33 = reg(1, 0x5A, 0x5B)
PROD_ID1 = reg(1, 0x6A)
PROD_ID2 = reg(1, 0x6C)
PROD_ID3 = reg(1, 0x6E)
PROD_ID4 = reg(1, 0x70)
VERSION = reg(1, 0x72)
SERIAL_NUM1 = reg(1, 0x74)
SERIAL_NUM2 = reg(1, 0x76)
SERIAL_NUM3 = reg(1, 0x78)
SERIAL_NUM4 = reg(1, 0x7A)
WIN_CTRL = reg(0, 0x7E, 0x7F)

# List of registers

REGMAP = (
    MODE_CTRL,
    DIAG_STAT,
    FLAG,
    GPIO,
    COUNT,
    RANGE_OVER,
    TEMP_HIGH,
    TEMP_LOW,
    XGYRO_HIGH,
    XGYRO_LOW,
    YGYRO_HIGH,
    YGYRO_LOW,
    ZGYRO_HIGH,
    ZGYRO_LOW,
    XACCL_HIGH,
    XACCL_LOW,
    YACCL_HIGH,
    YACCL_LOW,
    ZACCL_HIGH,
    ZACCL_LOW,
    RT_DIAG,
    ID,
    XDLTA_HIGH,
    XDLTA_LOW,
    YDLTA_HIGH,
    YDLTA_LOW,
    ZDLTA_HIGH,
    ZDLTA_LOW,
    XDLTV_HIGH,
    XDLTV_LOW,
    YDLTV_HIGH,
    YDLTV_LOW,
    ZDLTV_HIGH,
    ZDLTV_LOW,
    SIG_CTRL,
    MSC_CTRL,
    SMPL_CTRL,
    FILTER_CTRL,
    UART_CTRL,
    GLOB_CMD,
    BURST_CTRL1,
    BURST_CTRL2,
    POL_CTRL,
    DLT_CTRL,
    ATTI_CTRL,
    GLOB_CMD2,
    R_MATRIX_G_M11,
    R_MATRIX_G_M12,
    R_MATRIX_G_M13,
    R_MATRIX_G_M21,
    R_MATRIX_G_M22,
    R_MATRIX_G_M23,
    R_MATRIX_G_M31,
    R_MATRIX_G_M32,
    R_MATRIX_G_M33,
    R_MATRIX_A_M11,
    R_MATRIX_A_M12,
    R_MATRIX_A_M13,
    R_MATRIX_A_M21,
    R_MATRIX_A_M22,
    R_MATRIX_A_M23,
    R_MATRIX_A_M31,
    R_MATRIX_A_M32,
    R_MATRIX_A_M33,
    PROD_ID1,
    PROD_ID2,
    PROD_ID3,
    PROD_ID4,
    VERSION,
    SERIAL_NUM1,
    SERIAL_NUM2,
    SERIAL_NUM3,
    SERIAL_NUM4,
    WIN_CTRL,
)

# register value definitions

MODE_CMD = {
    "SAMPLING": 0x01,
    "CONFIG": 0x02,
}

EXT_SEL = {
    "GPIO": 0x00,
    "RESET": 0x01,
    "TYPEA": 0x02,
    "TYPEB": 0x03,
}

DOUT_RATE = {
    2000: 0x00,
    1000: 0x01,
    500: 0x02,
    250: 0x03,
    125: 0x04,
    62.5: 0x05,
    31.25: 0x06,
    15.625: 0x07,
    400: 0x08,
    200: 0x09,
    100: 0x0A,
    80: 0x0B,
    50: 0x0C,
    40: 0x0D,
    25: 0x0E,
    20: 0x0F,
}

FILTER_SEL_2K_400_80 = {
    "MV_AVG0": 0x00,
    "MV_AVG2": 0x01,
    "MV_AVG4": 0x02,
    "MV_AVG8": 0x03,
    "MV_AVG16": 0x04,
    "MV_AVG32": 0x05,
    "MV_AVG64": 0x06,
    "MV_AVG128": 0x07,
    "K32_FC50": 0x08,
    "K32_FC100": 0x09,
    "K32_FC200": 0x0A,
    "K32_FC400": 0x0B,
    "K64_FC50": 0x0C,
    "K64_FC100": 0x0D,
    "K64_FC200": 0x0E,
    "K64_FC400": 0x0F,
    "K128_FC50": 0x10,
    "K128_FC100": 0x11,
    "K128_FC200": 0x12,
    "K128_FC400": 0x13,
}

FILTER_SEL = {
    "MV_AVG0": 0x00,
    "MV_AVG2": 0x01,
    "MV_AVG4": 0x02,
    "MV_AVG8": 0x03,
    "MV_AVG16": 0x04,
    "MV_AVG32": 0x05,
    "MV_AVG64": 0x06,
    "MV_AVG128": 0x07,
    "K32_FC25": 0x08,
    "K32_FC50": 0x09,
    "K32_FC100": 0x0A,
    "K32_FC200": 0x0B,
    "K64_FC25": 0x0C,
    "K64_FC50": 0x0D,
    "K64_FC100": 0x0E,
    "K64_FC200": 0x0F,
    "K128_FC25": 0x10,
    "K128_FC50": 0x11,
    "K128_FC100": 0x12,
    "K128_FC200": 0x13,
}

BAUD_RATE = {
    460800: 0,
    230400: 1,
    921600: 2,
}

ATTI_ON = {
    "DISABLE": 0,
    "DELTA": 1,
}


# scale factor and conversion constants
SF_GYRO = 1 / 66  # (deg/s)/bit
SF_ACCL = 1 / 2.5  # mG/bit
SF_TEMPC = -0.0037918  # degC/bit
TEMPC_25C = 2634  # offset @ 25degC
SF_DLTA = SF_GYRO * 1 / 1000  # deg/LSB
SF_DLTV = SF_ACCL * 1 / 1000 * 1 / 1000 * 9.80665  # (m/s)/LSB

# delays and other timing constants
POWERON_DELAY_S = 0.800
RESET_DELAY_S = 0.800
FLASH_TEST_DELAY_S = 0.005
FLASH_BACKUP_DELAY_S = 0.200
SELFTEST_DELAY_S = 0.150
FILTER_SETTING_DELAY_S = 0.001
