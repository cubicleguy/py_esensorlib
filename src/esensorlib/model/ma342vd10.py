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

"""Constant and definition for IMU M-A342VD10"""

from enum import Enum

# Low-level UART
BURST_MARKER = 0x80
DELIMITER = 0x0D


class Reg(Enum):
    """WIN_ID and Register Address"""

    BURST = (0, 0x00, 0x01)
    MODE_CTRL = (0, 0x02, 0x03)
    DIAG_STAT1 = (0, 0x04, 0x05)
    FLAG = (0, 0x06, 0x07)
    COUNT = (0, 0x0A, 0x0B)
    DIAG_STAT2 = (0, 0x0C, 0x0D)
    TEMP1 = (0, 0x10, 0x11)
    ACC_SELFTEST_DATA1 = (0, 0x2A, 0x2B)
    ACC_SELFTEST_DATA2 = (0, 0x2C, 0x2D)
    TEMP2 = (0, 0x2E, 0x2F)
    XVELC_HIGH = (0, 0x30, 0x31)
    XDISP_HIGH = (0, 0x30, 0x31)
    XVELC_LOW = (0, 0x32, 0x33)
    XDISP_LOW = (0, 0x32, 0x33)
    YVELC_HIGH = (0, 0x34, 0x35)
    YDISP_HIGH = (0, 0x34, 0x35)
    YVELC_LOW = (0, 0x36, 0x37)
    YDISP_LOW = (0, 0x36, 0x37)
    ZVELC_HIGH = (0, 0x38, 0x39)
    ZDISP_HIGH = (0, 0x38, 0x39)
    ZVELC_LOW = (0, 0x3A, 0x3B)
    ZDISP_LOW = (0, 0x3A, 0x3B)
    ID = (0, 0x4C, 0x4D)
    SIG_CTRL = (1, 0x00, 0x01)
    MSC_CTRL = (1, 0x02, 0x03)
    SMPL_CTRL = (1, 0x04, 0x05)
    UART_CTRL = (1, 0x08, 0x09)
    GLOB_CMD = (1, 0x0A, 0x0B)
    BURST_CTRL = (1, 0x0C, 0x0D)
    ALIGNMENT_COEF_CMD = (1, 0x38, 0x39)
    ALIGNMENT_COEF_DATA = (1, 0x3A, 0x3B)
    ALIGNMENT_COEF_ADDR = (1, 0x3C, 0x3D)
    XALARM = (1, 0x46, 0x47)
    YALARM = (1, 0x48, 0x49)
    ZALARM = (1, 0x4A, 0x4B)
    PROD_ID1 = (1, 0x6A, 0x6B)
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

OUTPUT_SEL = {
    "VELOCITY_RAW": 0x00,
    "VELOCITY_RMS": 0x01,
    "VELOCITY_PP": 0x02,
    "DISP_RAW": 0x04,
    "DISP_RMS": 0x05,
    "DISP_PP": 0x06,
}

BAUD_RATE = {
    921600: 0x00,
    460800: 0x01,
    230400: 0x02,
    115200: 0x03,
}

# scale factor and conversion constants
SF_VEL = 2.38e-4  # mm/s/bit
SF_DISP = 2.38e-4  # mm/bit
SF_TEMPC = -0.0037918  # degC/bit

# delays and other timing constants
POWERON_DELAY_S = 0.900
RESET_DELAY_S = 0.970
FLASH_BACKUP_DELAY_S = 0.310
FLASH_RESET_DELAY_S = 2.300
SELFTEST_DELAY_S = 0.300  # ACC, TEMP, VDD
SELFTEST_RESONANCE_DELAY_S = 0.820
SELFTEST_FLASH_DELAY_S = 0.005
OUTPUT_MODE_SETTING_DELAY_S = 0.118
SAMPLING_START_DELAY_S = 0.005
SAMPLING_STOP_DELAY_S = 0.001
SLEEP_WAKE_DELAY_S = 0.016
