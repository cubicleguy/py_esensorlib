# MIT License

# Copyright (c) 2023, 2025 Seiko Epson Corporation

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

"""Constant and definition for Basic Device"""

from enum import Enum

# Low-level UART
BURST_MARKER = 0x80
DELIMITER = 0x0D


class Reg(Enum):
    """WIN_ID and Register Address"""

    MODE_CTRL = (0, 0x02, 0x03)
    ID = (0, 0x4C, 0x4D)
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


# Device features
HAS_FEATURE = {
    "GYRO": True,
    "ACCL": True,
    "DLT_OUTPUT": False,
    "ATTI_OUTPUT": False,
    "ATTI_ON_REG": False,
    "ROT_MATRIX": False,
    "INITIAL_BACKUP": False,
    "RANGE_OVER": False,
    "RT_DIAG": False,
    "A_RANGE": False,
}
