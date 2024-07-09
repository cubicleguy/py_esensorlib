# MIT License

# Copyright (c) 2023, 2024 Seiko Epson Corporation

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

"""Constant and definition for IMU M-G366PDG0"""

from enum import Enum

# Low-level UART
BURST_MARKER = 0x80
DELIMITER = 0x0D


class Reg(Enum):
    """WIN_ID and Register Address"""

    BURST = (0, 0x00, 0x01)
    MODE_CTRL = (0, 0x02, 0x03)
    DIAG_STAT = (0, 0x04, 0x05)
    FLAG = (0, 0x06, 0x07)
    GPIO = (0, 0x08, 0x09)
    COUNT = (0, 0x0A, 0x0B)
    RANGE_OVER = (0, 0x0C, 0x0D)
    TEMP_HIGH = (0, 0x0E, 0x0F)
    TEMP_LOW = (0, 0x10, 0x11)
    XGYRO_HIGH = (0, 0x12, 0x13)
    XGYRO_LOW = (0, 0x14, 0x15)
    YGYRO_HIGH = (0, 0x16, 0x17)
    YGYRO_LOW = (0, 0x18, 0x19)
    ZGYRO_HIGH = (0, 0x1A, 0x1B)
    ZGYRO_LOW = (0, 0x1C, 0x1D)
    XACCL_HIGH = (0, 0x1E, 0x1F)
    XACCL_LOW = (0, 0x20, 0x21)
    YACCL_HIGH = (0, 0x22, 0x23)
    YACCL_LOW = (0, 0x24, 0x25)
    ZACCL_HIGH = (0, 0x26, 0x27)
    ZACCL_LOW = (0, 0x28, 0x29)
    ID = (0, 0x4C, 0x4D)
    QTN0_HIGH = (0, 0x50, 0x51)
    QTN0_LOW = (0, 0x52, 0x53)
    QTN1_HIGH = (0, 0x54, 0x55)
    QTN1_LOW = (0, 0x56, 0x57)
    QTN2_HIGH = (0, 0x58, 0x59)
    QTN2_LOW = (0, 0x5A, 0x5B)
    QTN3_HIGH = (0, 0x5C, 0x5D)
    QTN3_LOW = (0, 0x5E, 0x5F)
    XDLTA_HIGH = (0, 0x64, 0x65)
    XDLTA_LOW = (0, 0x66, 0x67)
    YDLTA_HIGH = (0, 0x68, 0x69)
    YDLTA_LOW = (0, 0x6A, 0x6B)
    ZDLTA_HIGH = (0, 0x6C, 0x6D)
    ZDLTA_LOW = (0, 0x6E, 0x6F)
    XDLTV_HIGH = (0, 0x70, 0x71)
    XDLTV_LOW = (0, 0x72, 0x73)
    YDLTV_HIGH = (0, 0x74, 0x75)
    YDLTV_LOW = (0, 0x76, 0x77)
    ZDLTV_HIGH = (0, 0x78, 0x79)
    ZDLTV_LOW = (0, 0x7A, 0x7B)
    SIG_CTRL = (1, 0x00, 0x01)
    MSC_CTRL = (1, 0x02, 0x03)
    SMPL_CTRL = (1, 0x04, 0x05)
    FILTER_CTRL = (1, 0x06, 0x07)
    UART_CTRL = (1, 0x08, 0x09)
    GLOB_CMD = (1, 0x0A, 0x0B)
    BURST_CTRL1 = (1, 0x0C, 0x0D)
    BURST_CTRL2 = (1, 0x0E, 0x0F)
    POL_CTRL = (1, 0x10, 0x11)
    DLT_CTRL = (1, 0x12, 0x13)
    ATTI_CTRL = (1, 0x14, 0x15)
    GLOB_CMD2 = (1, 0x16, 0x17)
    R_MATRIX_G_M11 = (1, 0x38, 0x39)
    R_MATRIX_G_M12 = (1, 0x3A, 0x3B)
    R_MATRIX_G_M13 = (1, 0x3C, 0x3D)
    R_MATRIX_G_M21 = (1, 0x3E, 0x3F)
    R_MATRIX_G_M22 = (1, 0x40, 0x41)
    R_MATRIX_G_M23 = (1, 0x42, 0x43)
    R_MATRIX_G_M31 = (1, 0x44, 0x45)
    R_MATRIX_G_M32 = (1, 0x46, 0x47)
    R_MATRIX_G_M33 = (1, 0x48, 0x49)
    PROD_ID1 = (1, 0x6A, 0x06B)
    PROD_ID2 = (1, 0x6C, 0x6D)
    PROD_ID3 = (1, 0x6E, 0x6F)
    PROD_ID4 = (1, 0x70, 0x71)
    VERSION = (1, 0x72, 0x73)
    SERIAL_NUM1 = (1, 0x74, 0x75)
    SERIAL_NUM2 = (1, 0x76, 0x77)
    SERIAL_NUM3 = (1, 0x78, 0x79)
    SERIAL_NUM4 = (1, 0x7A, 0x7B)
    WIN_CTRL = (0, 0x7E, 0x7F)

    def __init__(self, winid, addr, addrh):
        self.WINID = winid
        self.ADDR = addr
        self.ADDRH = addrh


# register value definitions

MODE_CMD = {
    "SAMPLING": 0x01,
    "CONFIG": 0x02,
}

EXT_SEL = {
    "GPIO": 0x00,
    "RESET": 0x01,
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

FILTER_SEL = {
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

BAUD_RATE = {
    460800: 0,
    230400: 1,
    921600: 2,
}

ATTI_ON = {
    "DISABLE": 0,
    "DELTA": 1,
    "ATTI": 2,
}

ATTI_MOTION_PROFILE = {
    "MODEA": 0,
    "MODEB": 1,
    "MODEC": 2,
}

# scale factor and conversion constants
SF_GYRO = 1 / 66  # (deg/s)/bit
SF_ACCL = 1 / 4  # mG/bit
SF_TEMPC = 0.00390625  # degC/bit
TEMPC_25C = 0  # offset @ 25degC
SF_DLTA = SF_GYRO * 1 / 2000  # deg/LSB
SF_DLTV = SF_ACCL * 1 / 1000 * 1 / 2000 * 9.80665  # (m/s)/LSB
SF_ATTI = 0.00699411  # deg/LSB
SF_QTN = 1 / 2**14

# delays and other timing constants
POWERON_DELAY_S = 0.800
RESET_DELAY_S = 0.800
FLASH_TEST_DELAY_S = 0.030
FLASH_BACKUP_DELAY_S = 0.200
SELFTEST_DELAY_S = 0.080
FILTER_SETTING_DELAY_S = 0.001
ATTI_MOTION_SETTING_DELAY_S = 0.001
