# MIT License

# Copyright (c) 2024 Seiko Epson Corporation

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

"""Constant and definition for IMU M-A352AD10"""

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
    COUNT = (0, 0x0A, 0x0B)
    TEMP_HIGH = (0, 0x0E, 0x0F)
    TEMP_LOW = (0, 0x10, 0x11)
    XACCL_HIGH = (0, 0x30, 0x31)
    XACCL_LOW = (0, 0x32, 0x33)
    YACCL_HIGH = (0, 0x34, 0x35)
    YACCL_LOW = (0, 0x36, 0x37)
    ZACCL_HIGH = (0, 0x38, 0x39)
    ZACCL_LOW = (0, 0x3A, 0x3B)
    XTILT_HIGH = (0, 0x3C, 0x3D)
    XTILT_LOW = (0, 0x3E, 0x3F)
    YTILT_HIGH = (0, 0x40, 0x41)
    YTILT_LOW = (0, 0x42, 0x43)
    ZTILT_HIGH = (0, 0x44, 0x45)
    ZTILT_LOW = (0, 0x46, 0x47)
    ID = (0, 0x4C, 0x4D)
    SIG_CTRL = (1, 0x00, 0x01)
    MSC_CTRL = (1, 0x02, 0x03)
    SMPL_CTRL = (1, 0x04, 0x05)
    FILTER_CTRL = (1, 0x06, 0x07)
    UART_CTRL = (1, 0x08, 0x09)
    GLOB_CMD = (1, 0x0A, 0x0B)
    BURST_CTRL = (1, 0x0C, 0x0D)
    FIR_UCMD = (1, 0x16, 0x17)
    FIR_UDATA = (1, 0x18, 0x19)
    FIR_UADDR = (1, 0x1A, 0x1B)
    LONGFILT_CTRL = (1, 0x1C, 0x1D)
    LONGFILT_TAP = (1, 0x1E, 0x1F)
    OFFSET_XA_HIGH = (1, 0x2C, 0x2D)
    OFFSET_XA_LOW = (1, 0x2E, 0x2F)
    OFFSET_YA_HIGH = (1, 0x30, 0x31)
    OFFSET_YA_LOW = (1, 0x32, 0x33)
    OFFSET_ZA_HIGH = (1, 0x34, 0x35)
    OFFSET_ZA_LOW = (1, 0x36, 0x37)
    XALARM = (1, 0x46, 0x47)
    YALARM = (1, 0x48, 0x49)
    ZALARM = (1, 0x4A, 0x4B)
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
    "SLEEP": 0x03,
}

EXT_SEL = {
    "DISABLED": 0x00,
    "TRIG_POS_EDGE": 0x10,
    "TRIG_NEG_EDGE": 0x11,
}

DOUT_RATE = {
    1000: 0x02,
    500: 0x03,
    200: 0x04,
    100: 0x05,
    50: 0x06,
}

FILTER_SEL = {
    "K64_FC83": 0x01,
    "K64_FC220": 0x02,
    "K128_FC36": 0x03,
    "K128_FC110": 0x04,
    "K128_FC350": 0x05,
    "K512_FC9": 0x06,
    "K512_FC16": 0x07,
    "K512_FC60": 0x08,
    "K512_FC210": 0x09,
    "K512_FC460": 0x0A,
    "UDF4": 0x0B,
    "UDF64": 0x0C,
    "UDF128": 0x0D,
    "UDF512": 0x0E,
}

BAUD_RATE = {
    460800: 0x01,
    230400: 0x02,
    115200: 0x03,
}


# scale factor and conversion constants
SF_ACCL = 0.06e-3  # mg/bit
SF_TEMPC = -0.0037918  # degC/bit
SF_TILT = 0.002e-6  # rad/bit

# delays and other timing constants
POWERON_DELAY_S = 0.900
RESET_DELAY_S = 0.970
FLASH_BACKUP_DELAY_S = 0.310
FLASH_RESET_DELAY_S = 1.900
SELFTEST_DELAY_S = 0.200  # ACC, TEMP, VDD
SELFTEST_SENSAXIS_DELAY_S = 40  # Sensitivity/axis
SELFTEST_FLASH_DELAY_S = 0.005
FILTER_SETTING_DELAY_S = 0.100  # UDF max
SLEEP_WAKE_DELAY_S = 0.016
