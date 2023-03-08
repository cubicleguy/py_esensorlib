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

"""Constant and definition for Basic Device"""

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

MODE_CTRL = reg(0, 0x02, 0x03)
ID = reg(0, 0x4C)
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
    ID,
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

# delays and other timing constants
POWERON_DELAY_S = 0.800
RESET_DELAY_S = 0.800
