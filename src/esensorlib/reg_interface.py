#!/usr/bin/env python

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

"""Register Interface class for accelerometer, vibration sensor, or IMU
Contains:
- RegInterface() class
"""

import importlib

from loguru import logger


class RegInterface:
    """
    Basic port register communication and
    device identification

    ...

    Attributes
    ----------
    None

    Methods
    -------
    get_reg(winnum, regaddr, verbose=False)
        16-bit read from specified register address

    set_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write to specified register address

    get_device_info(verbose=False)
        Return dict of device read prod_id, version_id, serial_id
    """

    WIN_ID_ADDR = 0x7E

    def __init__(self, obj_port, verbose=False):
        """
        Parameters
        ----------
        obj_port : Port object
            Instance of UartPort() or SpiPort()
        verbose : bool
            If True outputs additional debug info
        """

        self.port_io = obj_port
        self._verbose = verbose

        # Load core device definitions for basic communication
        self._mdef = importlib.import_module(".model.mcore", package="esensorlib")
        self.reg = self._mdef.Reg

    def __repr__(self):
        cls = self.__class__.__name__
        string_val = "".join(
            [f"{cls}(obj_port={repr(self.port_io)}, " f"verbose={self._verbose})"]
        )
        return string_val

    def __str__(self):
        string_val = "".join(
            [
                "\nRegister Interface",
                f"\n  Port Object: {repr(self.port_io)}",
                f"\n  Verbose: {self._verbose}",
            ]
        )
        return string_val

    def get_reg(self, winnum, regaddr, verbose=False):
        """Returns the 16-bit register data from specified WINI_ID
        and regaddr (must be even).

        Parameters
        ----------
        winnum : int
            WIN_ID for device register map. Usually 0 or 1
        regaddr : int
            7-bit register address (must be even, lsb ignored)
        verbose : bool
            If True outputs additional debug info

        Returns
        -------
        int
            16-bit data read from register
        """

        self.port_io.set_raw8(self.WIN_ID_ADDR, winnum, verbose=False)
        read_data = self.port_io.get_raw16(regaddr, verbose=False)

        if verbose:
            logger.debug(
                f"REG[0x{regaddr & 0xFE:02X}, W({winnum:X})] -> 0x{read_data:04X}"
            )

        return read_data

    def set_reg(self, winnum, regaddr, write_byte, verbose=False):
        """Writes 1 byte to specified WIN_ID and regaddr (odd or even).

        Parameters
        ----------
        winnum : int
            WIN_ID for device register map. Usually 0 or 1
        regaddr : int
            7-bit register address
        write_byte : int
            8-bit write data
        verbose : bool
            If True outputs additional debug info
        """

        self.port_io.set_raw8(self.WIN_ID_ADDR, winnum, verbose=False)
        self.port_io.set_raw8(regaddr, write_byte, verbose=False)

        if verbose:
            logger.debug(
                f"REG[0x{regaddr & 0xFF:02X}, W({winnum:X})] <- 0x{write_byte:02X}"
            )

    def get_device_info(self, verbose=False):
        """Returns PRODID, VERSION_ID, SERIAL_ID as dict.

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Returns
        -------
        dict
            "prod_id", "version_id", "serial_id" as key, values
        """

        # Read Model Info from device
        prod_id = self._get_prod_id(verbose)
        version = self._get_firm_ver(verbose)
        serial_num = self._get_unit_id(verbose)

        return {
            "prod_id": "".join(chr(i) for i in prod_id),
            "version_id": f"{version[1]:X}{version[0]:X}",
            "serial_id": "".join(chr(i) for i in serial_num),
        }

    def _get_prod_id(self, verbose=False):
        """Return Product ID as ASCII"""

        result = []
        result.append(self.get_reg(self.reg.PROD_ID1.WINID, self.reg.PROD_ID1.ADDR))
        result.append(self.get_reg(self.reg.PROD_ID2.WINID, self.reg.PROD_ID2.ADDR))
        result.append(self.get_reg(self.reg.PROD_ID3.WINID, self.reg.PROD_ID3.ADDR))
        result.append(self.get_reg(self.reg.PROD_ID4.WINID, self.reg.PROD_ID4.ADDR))

        prodcode = []
        for item in result:
            prodcode.append(item & 0xFF)
            prodcode.append(item >> 8)

        if verbose:
            logger.debug(f"PRODUCT ID raw byte code returned: {prodcode}")
            logger.debug(
                f"IMU PRODUCT ID ASCII conversion:\t {''.join(chr(i) for i in prodcode)}"
            )
        return prodcode

    def _get_firm_ver(self, verbose=False):
        """Return Firmware Version"""

        result = self.get_reg(self.reg.VERSION.WINID, self.reg.VERSION.ADDR)

        fwcode = []
        fwcode.append(result & 0xFF)
        fwcode.append(result >> 8)

        if verbose:
            logger.debug(f"Firmware Version raw byte code returned: {fwcode}")
        return fwcode

    def _get_unit_id(self, verbose=False):
        """Read UNIT_ID (serial number) as ASCII"""

        result = []
        result.append(
            self.get_reg(self.reg.SERIAL_NUM1.WINID, self.reg.SERIAL_NUM1.ADDR)
        )
        result.append(
            self.get_reg(self.reg.SERIAL_NUM2.WINID, self.reg.SERIAL_NUM2.ADDR)
        )
        result.append(
            self.get_reg(self.reg.SERIAL_NUM3.WINID, self.reg.SERIAL_NUM3.ADDR)
        )
        result.append(
            self.get_reg(self.reg.SERIAL_NUM4.WINID, self.reg.SERIAL_NUM4.ADDR)
        )

        idcode = []
        for item in result:
            idcode.append(item & 0xFF)
            idcode.append(item >> 8)

        if verbose:
            logger.debug(f"IMU ID raw byte code returned: {idcode}")
            logger.debug(
                f"IMU ID ASCII conversion:\t {''.join(chr(i) for i in idcode)}"
            )
        return idcode
