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

"""Uart Port class for interfacing to accelerometer, vibration sensor, or IMU
Contains:
- UartPort() class
- Descriptive Exceptions specific to this package
"""

import struct
import sys
import time
from collections import namedtuple
from types import MappingProxyType

from loguru import logger

import serial
import serial.tools.list_ports


# Custom Exceptions
class InvalidResponseFormatError(Exception):
    """Exception class for invalid response format"""


ReadResponse = namedtuple("ReadResponse", "ADDR DATA DELIMITER")


class UartPort:
    """
    UART Port Interface
    ...

    Attributes
    ----------
    info : MappingProxyType
        serial port settings

    Methods
    -------
    list_ports()
    open(port, baudrate, verbose)
    close(verbose)
    write_bytes(wr_data)
    read_bytes(size)
    in_waiting()
    reset_input_buffer()
    get_raw16(regaddr, verbose)
    set_raw8(regaddr, regbyte, verbose)
    response_ok(retries, verbose)
    find_delimiter(ntries, retry_delay, verbose)
    """

    # UART Port Timeout, adjust as necessary
    UART_RD_TIMEOUT_SEC = 3
    UART_WR_TIMEOUT_SEC = 3
    # Windows buffer may be ignored by the device driver
    WIN_BUFFER_SZ = 4096 * 4

    BURST_MARKER = 0x80
    DELIMITER = 0x0D

    WIN_ID_ADDR = 0x7E
    MODE_CTRL_ADDRH = 0x03
    ID_ADDR = 0x4C

    # Expected fixed return value when reading ID register
    ID_RETVAL = 0x5345

    # UART Timing Delays max in seconds
    TSTALL = 70e-6
    TWRITERATE = 350e-6
    TREADRATE = 350e-6

    def __init__(self, port, speed=460800, verbose=False, no_init=False):
        """
        Parameters
        ----------
        port : str
            The name of uart port
        speed : int
            Baudrate of sensor device connected to uart port
        verbose : bool
            If True outputs additional debug info
        no_init : bool
            If True does not call response_ok() during initialization
        """

        # If no serial port is specified, list available ports on PC
        if port is None:
            print("\nNo serial port specified. Available COM ports:")
            print(self.list_ports())
            raise IOError("No serial port specified")

        self._port = port
        self._speed = speed
        self._verbose = verbose
        self._no_init = no_init

        # Create serial port object to device
        self.uart_epson = serial.Serial()

        # Initialize serial port settings
        self.open(port=port, speed=speed)

        if no_init is False:
            # Check for device
            if not self.response_ok(verbose=verbose):
                raise IOError(
                    "Cannot send/receive commands with device:" f"{port} @ {speed} baud"
                )

    def __repr__(self):
        cls = self.__class__.__name__
        string_val = "".join(
            [
                f"{cls}(port='{self._port}', ",
                f"speed={self._speed}, ",
                f"verbose={self._verbose}, ",
                f"no_init={self._no_init})",
            ]
        )
        return string_val

    def __str__(self):
        string_val = "".join(
            [
                "\nUART Port",
                f"\n  Port: {self._port}",
                f"\n  Speed (baud): {self._speed}",
                f"\n  Verbose: {self._verbose}",
                f"\n  No_Init: {self._no_init}",
            ]
        )
        return string_val

    def __del__(self):
        self.close()

    @property
    def info(self):
        """property for underlying serial interface as MappingProxyType"""
        return MappingProxyType(self.uart_epson.get_settings())

    @staticmethod
    def list_ports():
        """List serial ports"""

        return [
            comport.device.upper() for comport in serial.tools.list_ports.comports()
        ]

    def open(self, port, speed, verbose=True):
        """Opens and initializes serial port of device
        If WIN system try to set buffer on Rx and Tx
        If Linux/Mac try to enable low_latency mode
        """

        try:
            self.uart_epson.port = port
            self.uart_epson.baudrate = speed
            self.uart_epson.timeout = self.UART_RD_TIMEOUT_SEC
            self.uart_epson.writeTimeout = self.UART_WR_TIMEOUT_SEC
            self.uart_epson.parity = serial.PARITY_NONE
            self.uart_epson.stopbits = serial.STOPBITS_ONE
            self.uart_epson.bytesize = serial.EIGHTBITS
            self.uart_epson.open()
            # For WIN try to increase the buffer size
            if sys.platform.startswith("win"):
                self.uart_epson.set_buffer_size(
                    rx_size=self.WIN_BUFFER_SZ,
                    tx_size=self.WIN_BUFFER_SZ,
                )
            # For Linux try to enable LOW_LATENCY mode for USB Serial Ports
            elif (
                sys.platform.startswith("linux")
                or sys.platform.startswith("cygwin")
                or sys.platform.startswith("darwin")
            ):
                try:
                    self.uart_epson.set_low_latency_mode(True)
                except ValueError as err:
                    logger.error(
                        f"** Could not enable low_latency mode (permissions?): {err}"
                    )

            if verbose:
                print(
                    " ".join(
                        [
                            "Open: ",
                            self.uart_epson.portstr,
                            ", ",
                            str(self.uart_epson.baudrate),
                        ]
                    )
                )
        except (OSError, serial.SerialException) as err:
            logger.error(
                f"** Could not open: {self.uart_epson.port} @ {self.uart_epson.baudrate} baud"
            )
            print("\nAvailable COM ports:")
            print(self.list_ports())
            raise IOError from err

    def close(self, verbose=True):
        """Closes the serial port"""

        try:
            if self.uart_epson.is_open:
                self.uart_epson.close()
                if verbose:
                    print(
                        " ".join(
                            [
                                "Close: ",
                                self.uart_epson.portstr,
                                ", ",
                                str(self.uart_epson.baudrate),
                                "baud",
                            ]
                        )
                    )
        except AttributeError:
            pass
        except (OSError, serial.SerialException) as err:
            logger.error(
                f"** Could not close: {self.uart_epson.portstr} @ {self.uart_epson.baudrate} baud"
            )
            raise IOError from err

    def write_bytes(self, wr_data):
        """Redirect to pyserial"""

        self.uart_epson.write(wr_data)

    def read_bytes(self, size=1):
        """Redirect to pyserial"""

        return self.uart_epson.read(size)

    def in_waiting(self):
        """Redirect to pyserial"""

        return self.uart_epson.in_waiting

    def reset_input_buffer(self):
        """Redirect to pyserial"""

        self.uart_epson.reset_input_buffer()

    def get_raw16(self, regaddr, verbose=False):
        """Returns the 16-bit read command from regaddr (must be even)"""

        read_cmd = bytearray((regaddr & 0xFE, 0x00, self.DELIMITER))
        self.write_bytes(read_cmd)
        time.sleep(self.TSTALL)

        # Read the bytes returned from the serial
        # format must conform to the expected data
        data_struct = struct.Struct(">BHB")
        data_str = self.read_bytes(data_struct.size)
        time.sleep(self.TWRITERATE - self.TSTALL)

        # Unpack bytes
        rdata = ReadResponse._make(data_struct.unpack(data_str))

        # Validation check on Header Byte, and Delimiter Byte
        if (rdata.ADDR != regaddr) or (rdata.DELIMITER != self.DELIMITER):
            raise InvalidResponseFormatError(
                f"Error: Unexpected response ({rdata.ADDR:02X},"
                f"{rdata.DATA:04X}, {rdata.DELIMITER:02X})"
            )

        if verbose:
            logger.debug(f"REG[0x{regaddr & 0xFE:02X}] -> 0x{rdata.DATA:04X}")

        return rdata.DATA

    def set_raw8(self, regaddr, regbyte, verbose=False):
        """Writes 1 byte to specified regaddr (odd or even)"""

        write_cmd = bytearray((regaddr | 0x80, regbyte, self.DELIMITER))
        self.write_bytes(write_cmd)
        time.sleep(self.TWRITERATE)

        if verbose:
            logger.debug(f"REG[0x{regaddr & 0xFF:02X}] <- 0x{regbyte:02X}")

    def response_ok(self, retries=5, verbose=False):
        """
        Assumes behaviour of Epson sensor device
        1)Place device in CONFIG mode.
        2)Clears the serial RX buffer, and checks RX buffer is zero
        3)If nonzero, send DELIMITER byte and repeat step 1, 2 for n retries
        4)If zero, then returns True if ID register returns expected value
        Returns False if retries exceeded
        """
        try:
            _count = 0
            while _count < retries:
                # Send goto CONFIG command
                self.set_raw8(self.WIN_ID_ADDR, 0x00, verbose)
                self.set_raw8(self.MODE_CTRL_ADDRH, 0x02, verbose)

                # If RX buffer clears, and ID register is ok, then exit True
                if self._clear_rx_buffer(verbose=verbose) is True:
                    self.set_raw8(self.WIN_ID_ADDR, 0x00, verbose)
                    result = self.get_raw16(self.ID_ADDR, verbose)
                    if result == self.ID_RETVAL:
                        return True
                # If RX buffer does not clear or ID check fails, try to
                # send a DELIMITER byte and go thru loop again
                if verbose:
                    logger.debug("Send DELIMITER byte")
                self.write_bytes(struct.pack("B", self.DELIMITER))
                _count = _count + 1
            return False
        except KeyboardInterrupt:
            return False

    def find_delimiter(self, ntries=100, verbose=False):
        """
        Read UART RX buffer one byte at a time until DELIMITER byte detected
        Returns False if ntries exceeded
        """

        if verbose:
            logger.debug("Searching for DELIMITER...")
        _try = 0
        while _try < ntries:
            if self.in_waiting() > 0:
                # Read 1 byte and search for DELIMITER
                data = self.read_bytes(1)
                if self.DELIMITER in data:
                    if verbose:
                        logger.debug("Found DELIMITER...")
                    return True
            _try = _try + 1
        return False

    def _clear_rx_buffer(self, retries=5, retry_delay=0.10, verbose=False):
        """
        Flushes the UART RX buffer.
        Returns False if RX buffer not empty after retries exceeded.
        """

        try:
            _rxcount = 0
            while _rxcount < retries:
                if self.in_waiting() != 0:
                    self.reset_input_buffer()
                    # Longer than slowest sample_rate is 15.625Hz
                    time.sleep(retry_delay)
                    if verbose:
                        logger.debug(f"RX {_rxcount}: {self.in_waiting()} bytes")
                _rxcount = _rxcount + 1
            if self.in_waiting() == 0:
                return True
            logger.warning(
                "** Rx Buffer contains data after reset_input_buffer() "
                "Is device in SAMPLING mode?"
            )
            return False
        except KeyboardInterrupt:
            return False
