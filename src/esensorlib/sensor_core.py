#!/usr/bin/env python

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

"""Low level driver class to communicate to Epson Sensing System Device
   using the UART interface.
   Contains:
   - SensorDevice() class
   - Descriptive Exceptions related to the SensorDevice()
   """

import struct
import time
import sys
import glob
import importlib
from collections import namedtuple
import serial


# Custom Exceptions
class InvalidReturnFormatError(Exception):
    """Exception class for invalid response format"""


class HardwareError(Exception):
    """Exception class for HARD_ERR from device"""


class SelfTestError(Exception):
    """Exception class for ST_ERR from device"""


class FlashTestError(Exception):
    """Exception class for FLASH_ERR from device"""


class FlashBackupError(Exception):
    """Exception class for FLASH_BU_ERR from device"""


class DeviceConfigurationError(Exception):
    """Exception class for FLASH_BU_ERR from device"""


class InvalidCommandError(Exception):
    """Exception class for invalid register access for device"""


class InvalidBurstReadError(Exception):
    """Exception class for malformed burst read access for device"""


class UartRxClearBufferError(Exception):
    """Exception class for failure syncing UART Rx for device"""


class UartTxSyncError(Exception):
    """Exception class for failure syncing UART Txfor device"""


class SyncRetriesError(Exception):
    """Exception class for failure syncing UART for device"""


ReadResponse = namedtuple("ReadResponse", "addr data delimiter")


class SensorDevice:
    """
    A class of Epson sensor device

    ...

    Attributes
    ----------
    info : dict
        dict of device ID and port information
    status : dict
        dict of device basic status
    dlt_status : dict
        dict of delta angle/velocity status
    atti_status : dict
        dict of attitude or quaternion status
    burst_out : dict
        dict of burst output status
    burst_fields : tuple
        tuple of fields for a single sensor burst read
    mdef : object
        device model definitions and constants

    Methods
    -------
    get_reg(winnum, regaddr, verbose=False)
        16-bit read from specified register address

    set_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    init_check(verbose=False)
        Check if HARD_ERR (hardware error) is reported
        Usually performed once after startup

    do_selftest(verbose=False)
        Perform do_selftest and check if ST_ERR (do_selftest error) is reported

    do_softreset(verbose=False)
        8-bit write with byte data to specified register address

    test_flash(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    backup_flash(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    init_backup(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    dump_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    config(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    goto(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    get_mode(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address

    read_sample(winnum, regaddr, write_byte, verbose=False)
        8-bit write with byte data to specified register address
    """

    def __init__(self, comport, baudrate=460800, model="auto", verbose=False):
        """
        Parameters
        ----------
        comport : str
            The name of serial port
        baudrate : int
            Baudrate of sensor device connected to serial port
        model : str
            Model of sensor device. Set to auto for auto-detect
                g320, g354, g364pdc0, g364pdca, g365pdc1,
                g365pdf1, g370pdf1, g370pds0, g330pdg0,
                g366pdg0, g370pdg0
        verbose : bool
            If True outputs additonal debug info
        """

        # If no serial port is specified, list available ports on PC
        if not comport:
            print("\nNo serial port specified. Available COM ports:")
            print(list(self._serial_ports()))
            raise IOError("No serial port specified")

        # Stores device id and port info
        self._info = {
            "prod_id": None,
            "version_id": None,
            "serial_id": None,
            "comport": comport,
            "baudrate": baudrate,
            "model": model,
        }
        # Stores basic cfg status
        self._status = {
            "dout_rate": 200,
            "filter": None,
            "ndflags": True,
            "tempc": True,
            "counter": "sample",
            "chksm": False,
            "auto_start": False,
            "is_32bit": True,
            "a_range": False,
            "ext_trigger": False,
            "uart_auto": False,
            "burst_fields": [],
            "is_config": True,
        }
        # Stores delta angle/velocity cfg status
        self._dlt_status = {
            "dlta": False,
            "dltv": False,
            "dlta_sf_range": 12,
            "dltv_sf_range": 12,
        }
        # Stores current attitude cfg status
        self._atti_status = {
            "atti": False,
            "mode": "euler",
            "conv": 0,
            "profile": "modea",
            "qtn": False,
        }
        # Stores current burst output status
        self._burst_out = {
            "ndflags": True,
            "tempc": True,
            "gyro": True,
            "accl": True,
            "dlta": False,
            "dltv": False,
            "qtn": False,
            "atti": False,
            "gpio": False,
            "counter": True,
            "chksm": False,
            "tempc32": True,
            "gyro32": True,
            "accl32": True,
            "dlta32": False,
            "dltv32": False,
            "qtn32": False,
            "atti32": False,
        }
        # Store burst structure format for unpacking
        self._b_struct = ""

        # Create serial port object to device
        self._serial_epson = serial.Serial()

        # Initialize serial port settings
        self._init_serial(verbose=verbose)

        # Load core device definitions for basic communication
        # and attempt communication check
        self._mdef = importlib.import_module("esensorlib.model.mcore")
        if not self._sync_device(verbose=verbose):
            raise IOError(
                "Cannot send/receive commands with device:"
                f"{self._info['comport']} @ {self._info['baudrate']} baud"
            )

        # Load user-specified model contants and variables or Auto-Detect
        if model == "auto":
            detected_model = "".join(chr(i) for i in self._get_prod_id())
            print(f"Detected: {detected_model}")
            model = detected_model.lower()
        # If G330, G366 use the same model definitions
        if model in ["g330pdg0", "g330pde0", "g366pde0"]:
            model = "g366pdg0"
        # If G320 or G354 just keep the first 4 letters
        elif model.startswith("g320") or model.startswith("g354"):
            model = model[:4]
        # Import the model definitions
        try:
            self._mdef = importlib.import_module(f"esensorlib.model.m{model}")
        except ModuleNotFoundError as err:
            print("** Unknown device model detected")
            raise IOError from err

        # Retrieve device info but overide if user specifies the model
        self._get_device_info(verbose=verbose)
        if model.upper() != self._info["prod_id"]:
            print(
                f"Overriding detected {self._info['prod_id']} with specified {model.upper()}"
            )
            self._info["prod_id"] = model.upper()

    def __repr__(self):
        cls = self.__class__.__name__
        string_val = ",".join(
            [
                f"{cls}(comport={self._info['comport']}",
                f"baudrate={self._info['baudrate']}",
                f"model={self._info['model']})",
            ]
        )
        return string_val

    def __str__(self):
        cls = self.__class__.__name__
        string_val = ",".join(
            [
                f"{cls}(prod_id={self._info['prod_id']}",
                f"version={self._info['version_id']}",
                f"serial_id={self._info['serial_id']}",
                f"comport={self._info['comport']}",
                f"baudrate={self._info['baudrate']})",
            ]
        )
        return string_val

    def __del__(self):
        self._close()

    @property
    def info(self):
        """property for device info dict"""
        return self._info

    @property
    def status(self):
        """property for basic status dict"""
        return self._status

    @property
    def atti_status(self):
        """property for attitude or quaternion status dict"""
        return self._atti_status

    @property
    def dlt_status(self):
        """property for delta angle/velocity status dict"""
        return self._dlt_status

    @property
    def burst_out(self):
        """property for burst_output dict"""
        return self._burst_out

    @property
    def burst_fields(self):
        """property for burst_fields list"""
        return self._status["burst_fields"]

    @property
    def mdef(self):
        """property for model definitions dict"""
        return self._mdef

    def get_reg(self, winnum, regaddr, verbose=False):
        """Returns the 16-bit register data from regaddr (must be even)
        always sends WIN_ID prior to sending register read command.

        Parameters
        ----------
        winnum : int
            WIN_ID for device register map. Usually 0 or 1
        regaddr : int
            7-bit register address (must be even, lsb ignored)
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        int
            16-bit data read from register
        """

        self._set_raw(self._mdef.WINID, winnum, verbose=False)
        read_data = self._get_raw(regaddr, verbose=False)

        if verbose:
            print(f"REG[0x{regaddr & 0xFE:02X}, W({winnum:X})] -> 0x{read_data:04X}")

        return read_data

    def set_reg(self, winnum, regaddr, write_byte, verbose=False):
        """Writes 1 byte to specified regaddr (odd or even)
        always sends WIN_ID prior to sending register write command.

        Parameters
        ----------
        winnum : int
            WIN_ID for device register map. Usually 0 or 1
        regaddr : int
            7-bit register address
        write_byte : int
            8-bit write data
        verbose : bool
            If True outputs additonal debug info
        """

        self._set_raw(self._mdef.WINID, winnum, verbose=False)
        self._set_raw(regaddr, write_byte, verbose=False)

        if verbose:
            print(f"REG[0x{regaddr & 0xFF:02X}, W({winnum:X})] <- 0x{write_byte:02X}")

    def init_check(self, verbose=False):
        """Check for HARD_ERR (hardware error)

        Parameters
        ----------
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        int
            non-zero results indicates HARD_ERR
        """

        result = 0x0400
        while (result & 0x0400) != 0:
            # Wait for NOT_READY
            result = self.get_reg(
                self._mdef.GLOB_CMD.winid, self._mdef.GLOB_CMD.addr, verbose
            )
            if verbose:
                print(".", end="")
        result = self.get_reg(
            self._mdef.DIAG_STAT.winid, self._mdef.DIAG_STAT.addr, verbose
        )
        if verbose:
            print("IMU Startup Check")
        result = result & 0x0060
        if result:
            raise HardwareError("** Hardware Failure. HARD_ERR bits")

    def do_selftest(self, verbose=False):
        """Initiate Self Test

        Parameters
        ----------
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        int
            non-zero results indicates ST_ERR
        """

        self.set_reg(
            self._mdef.MSC_CTRL.winid, self._mdef.MSC_CTRL.addrh, 0x04, verbose
        )
        time.sleep(self._mdef.SELFTEST_DELAY_S)
        result = 0x0400
        while (result & 0x0400) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self._mdef.MSC_CTRL.winid, self._mdef.MSC_CTRL.addr)
            if verbose:
                print(".", end="")
        result = self.get_reg(
            self._mdef.DIAG_STAT.winid, self._mdef.DIAG_STAT.addr, verbose
        )
        result = result & 0x7800
        if result:
            raise SelfTestError("** Self Test Failure. ST_ERR bits")
        print("Self Test completed with no errors")

    def do_softreset(self, verbose=False):
        """Initiate Software Reset

        Parameters
        ----------
        verbose : bool
            If True outputs additonal debug info
        """

        self.set_reg(self._mdef.GLOB_CMD.winid, self._mdef.GLOB_CMD.addr, 0x80, verbose)
        time.sleep(self._mdef.RESET_DELAY_S)
        print("Software Reset Completed")

    def test_flash(self, verbose=False):
        """Initiate Flash Test

        Parameters
        ----------
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        int
            non-zero results indicates FLASH_ERR
        """

        self.set_reg(
            self._mdef.MSC_CTRL.winid, self._mdef.MSC_CTRL.addrh, 0x08, verbose
        )
        time.sleep(self._mdef.FLASH_TEST_DELAY_S)
        result = 0x0800
        while (result & 0x0800) != 0:
            result = self.get_reg(self._mdef.MSC_CTRL.winid, self._mdef.MSC_CTRL.addr)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self._mdef.DIAG_STAT.winid, self._mdef.DIAG_STAT.addr, verbose
        )
        result = result & 0x0004
        if result:
            raise FlashTestError("** Flash Test Failure. FLASH_ERR bits")
        print("Flash Test Completed")

    def backup_flash(self, verbose=False):
        """Initiate Flash Backup

        Parameters
        ----------
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        int
            non-zero results indicates FLASH_BU_ERR
        """

        self.set_reg(self._mdef.GLOB_CMD.winid, self._mdef.GLOB_CMD.addr, 0x08, verbose)
        time.sleep(self._mdef.FLASH_BACKUP_DELAY_S)
        result = 0x0008
        while (result & 0x0008) != 0:
            result = self.get_reg(self._mdef.GLOB_CMD.winid, self._mdef.GLOB_CMD.addr)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self._mdef.DIAG_STAT.winid, self._mdef.DIAG_STAT.addr, verbose
        )
        result = result & 0x0001
        if result:
            raise FlashBackupError("** Flash Backup Failure. FLASH_BU_ERR bit")
        print("Flash Backup Completed")

    def init_backup(self, verbose=False):
        """Initialize flash backup registers to factory defaults

        Parameters
        ----------
        verbose : bool
            If True outputs additonal debug info
        """

        self.set_reg(self._mdef.GLOB_CMD.winid, self._mdef.GLOB_CMD.addr, 0x10, verbose)
        time.sleep(self._mdef.FLASH_BACKUP_DELAY_S)
        result = 0x0010
        while (result & 0x0010) != 0:
            result = self.get_reg(self._mdef.GLOB_CMD.winid, self._mdef.GLOB_CMD.addr)
            if verbose:
                print(".", end="")
        print("Initial Backup Completed")

    def dump_reg(self, columns=3, verbose=False):
        """Initiate register dump and format into table

        Parameters
        ----------
        columns : int
            Number of columns to layout register read values
        verbose : bool
            If True outputs additonal debug info
        """

        print("Reading registers:")
        reg_dmp = [
            (
                regs.addr,
                regs.winid,
                self.get_reg(regs.winid, regs.addr, verbose=verbose),
            )
            for regs in self._mdef.REGMAP
        ]
        for i, each in enumerate(reg_dmp):
            print(f"REG[0x{each[0]:02X}, (W{each[1]})] => 0x{each[2]:04X}\t", end="")
            if i % columns == columns - 1:
                print()

    def config(self, basic_cfg=None, dlt_cfg=None, atti_cfg=None, verbose=False):
        """Configure device based on parameters.
        Configuration sequentially into 3 functions:
        1) basic
        2) delta angle/velocity
        3) attitude or quaternion
        Then read burst configuration from BURST_CTRL1, BURST_CTRL2
        and store in _status dict

        Parameters
        ----------
        basic_cfg : dict
            Dict containing key, value pairs for basic configuration
            If None, then use default settings in _config_basic()
                "dout_rate": int,
                "filter": str,
                "ndflags": bool,
                "tempc": bool,
                "counter": str,
                "chksm": bool,
                "auto_start": bool,
                "is_32bit": bool,
                "a_range": bool,
                "ext_trigger": bool,
                "uart_auto": bool
        dlt_cfg : dict
            Dict containing key, value pairs for delta angle/velocity configuration
            If None, then exit from _config_dlt() early
                "dlta": bool,
                "dltv": bool,
                "dlta_sf_range": int,
                "dltv_sf_range": int,
        atti_cfg : dict
            Dict containing key, value pairs for attitude/quaternion configuration
            If None, then exit from _config_atti() early
                "atti": bool,
                "mode": str, "euler" or "incl"
                "conv": int, 0 to 23
                "profile": "modea", "modeb", "modec"
                "qtn": bool,
        verbose : bool
            If True outputs additonal debug info
        """

        self._config_basic(basic_cfg, verbose=verbose)
        self._config_dlt(dlt_cfg, verbose=verbose)
        self._config_atti(atti_cfg, verbose=verbose)
        self._get_burst_config(verbose=verbose)

    def goto(self, mode, post_delay=0.1, verbose=False):
        """Set MODE_CMD to either CONFIG or SAMPLING mode.
        If entering SAMPLING, store the state of burst configuration
        and reset the current sample count.
        NOTE: Device must be in SAMPLING mode to call read_sample()
        NOTE: Device must be in CONFIG mode for most functions

        Parameters
        ----------
        mode : str
            Can be "config" or "sampling"
        post_delay : float
            Delay time in seconds after sending command before returning
        verbose : bool
            If True outputs additonal debug info

        Raises
        -------
        KeyError
            Raises to caller when mode is not valid string
        """

        mode = mode.upper()
        try:
            # When entering SAMPLING mode, update the
            # self._burst_out & self._status from
            # BURST_CTRL1 & BURST_CTRL2 register settings
            # reset sample counter
            if mode == "SAMPLING":
                self._get_burst_config(verbose=verbose)

            self.set_reg(
                self._mdef.MODE_CTRL.winid,
                self._mdef.MODE_CTRL.addrh,
                self._mdef.MODE_CMD[mode],
                verbose=verbose,
            )
            self._status["is_config"] = mode == "CONFIG"
            time.sleep(post_delay)
            # When entering CONFIG mode
            # flush any pending incoming burst data
            if mode == "CONFIG":
                self._clear_rx_buffer()
            if verbose:
                print(f"MODE_CMD = {mode}")
        except KeyError as err:
            print("** Invalid MODE_CMD")
            raise InvalidCommandError from err

    def get_mode(self, verbose=False):
        """Return MODE_STAT bit

        Parameters
        ----------
        mode : str
            Can be "config" or "sampling"
        post_delay : float
            Delay time in seconds after sending command before returning
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        int
            0 = Sampling, 1 = Config
        """

        result = 0x0300
        while (result & 0x0300) != 0:
            result = self.get_reg(
                self._mdef.MODE_CTRL.winid, self._mdef.MODE_CTRL.addr, verbose=verbose
            )
        result = (
            self.get_reg(
                self._mdef.MODE_CTRL.winid, self._mdef.MODE_CTRL.addr, verbose=verbose
            )
            & 0x0400
        ) >> 10
        self._status["is_config"] = bool(result)
        if verbose:
            print(f"MODE_CMD = {result}")
        return result

    def read_sample(self, scale_mode=True):
        """Calls to read 1 burst of sensor data, post processes
        depending on scale_mode parameter, and returns sensor data.
        If burst read contains corrupted data, returns None
        NOTE: Device must be in SAMPLING mode before calling

        Parameters
        ----------
        scale_mode : bool
            apply scale factor or not (raw decimal)
        verbose : bool
            If True outputs additonal debug info

        Returns
        -------
        tuple or None
            tuple containing single set of sensor burst data with or
            without scale factor applied
            None if burst data is malformed

        Raises
        -------
        KeyboardInterrupt
            Raises to caller CTRL-C
        IOError
            Raises to caller any type of serial port error
        """

        try:
            raw_burst = self._get_sample()
        except InvalidBurstReadError:
            print("** Missing Header & Delimiter")
            return None
        except KeyboardInterrupt:
            print("Stop reading sensor")
            raise
        except IOError:
            print("** Failure reading sensor sample")
            raise
        else:
            if scale_mode:
                return self._proc_sample(raw_burst)
            return raw_burst

    @staticmethod
    def _serial_ports():
        """List serial ports"""

        if sys.platform.startswith("win"):
            ports = ["COM" + str(i + 1) for i in range(256)]

        elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
            # this is to exclude your current terminal "/dev/tty"
            ports = glob.glob("/dev/tty[A-Za-z]*")

        elif sys.platform.startswith("darwin"):
            ports = glob.glob("/dev/tty.*")

        else:
            raise EnvironmentError("Unsupported platform")

        result = []
        for port in ports:
            try:
                s_ports = serial.Serial(port)
                s_ports.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def _init_serial(self, verbose=True):
        """Opens and initializes serial port of device
        If WIN system try to enable 16kB buffer on Rx and Tx
        If Linux/Mac try to enable low_latency mode
        """

        win_buffer_size = 4096 * 4  # May be ignored by device driver
        try:
            self._serial_epson.port = self._info[
                "comport"
            ]  # usually /dev/ttyUSBx for linux, COMxx for WIN
            self._serial_epson.baudrate = self._info["baudrate"]
            self._serial_epson.timeout = (
                3  # read timeout, arbitrary, can be increased depending on host latency
            )
            self._serial_epson.writeTimeout = (
                3  # arbitrary, can be increased depending on host latency
            )
            self._serial_epson.parity = serial.PARITY_NONE
            self._serial_epson.stopbits = serial.STOPBITS_ONE
            self._serial_epson.bytesize = serial.EIGHTBITS
            self._serial_epson.open()
            # For WIN try to increase the buffer size
            if sys.platform.startswith("win"):
                self._serial_epson.set_buffer_size(
                    rx_size=win_buffer_size, tx_size=win_buffer_size
                )
            # For Linux try to enable LOW_LATENCY mode for USB Serial Ports
            elif (
                sys.platform.startswith("linux")
                or sys.platform.startswith("cygwin")
                or sys.platform.startswith("darwin")
            ):
                self._serial_epson.set_low_latency_mode(True)
            if verbose:
                print(
                    " ".join(
                        [
                            "Open: ",
                            self._serial_epson.portstr,
                            ", ",
                            str(self._serial_epson.baudrate),
                        ]
                    )
                )
        except (OSError, serial.SerialException) as err:
            print(
                f"** Could not open: {self._info['comport']} @ {self._info['baudrate']} baud"
            )
            print("\nAvailable COM ports:")
            print(list(self._serial_ports()))
            raise IOError from err

    def _close(self, verbose=True):
        """Closes the serial port"""

        try:
            if self._serial_epson.is_open:
                self._serial_epson.close()
                if verbose:
                    print(
                        " ".join(
                            [
                                "Close: ",
                                self._serial_epson.portstr,
                                ", ",
                                str(self._serial_epson.baudrate),
                                "baud",
                            ]
                        )
                    )
        except AttributeError:
            pass
        except (OSError, serial.SerialException) as err:
            print(
                f"** Could not close: {self._info['comport']} @ {self._info['baudrate']} baud"
            )
            raise IOError from err

    def _get_raw(self, regaddr, verbose=False):
        """Returns the 16-bit register data from regaddr (must be even)
        assuming current WIN_ID is already set.
        """

        write_bytes = bytearray((regaddr & 0xFE, 0x00, self._mdef.DELIMITER))
        self._serial_epson.write(write_bytes)
        time.sleep(self._mdef.TSTALL)

        # Read the bytes returned from the serial
        # format must conform to the expected data
        data_struct = struct.Struct(">BHB")
        data_str = self._serial_epson.read(data_struct.size)
        time.sleep(self._mdef.TWRITERATE - self._mdef.TSTALL)

        # The data must be unpacked to be read correctly
        rdata = ReadResponse._make(data_struct.unpack(data_str))

        # Validation check on Header Byte, and Delimiter Byte
        if (rdata.addr != regaddr) or (rdata.delimiter != self._mdef.DELIMITER):
            raise InvalidReturnFormatError(
                f"Error: Unexpected response ({rdata.addr:02X},"
                f"{rdata.data:04X}, {rdata.delimiter:02X})"
            )

        if verbose:
            print(f"REG[0x{regaddr & 0xFE:02X}] -> 0x{rdata.data:04X}")

        return rdata.data

    def _set_raw(self, regaddr, regbyte, verbose=False):
        """Writes 1 byte to specified REGADDR (odd or even)
        assuming current WIN_ID is already set.
        """

        write_bytes = bytearray((regaddr | 0x80, regbyte, self._mdef.DELIMITER))
        self._serial_epson.write(write_bytes)
        time.sleep(self._mdef.TWRITERATE)

        if verbose:
            print(f"REG[0x{regaddr & 0xFF:02X}] <- 0x{regbyte:02X}")

    def _get_device_info(self, verbose=False):
        """Read and store PRODID, VERSION_ID, SERIAL_ID"""

        # Read Model Info from device
        prod_id = self._get_prod_id(verbose)
        version = self._get_firm_ver(verbose)
        serial_num = self._get_unit_id(verbose)

        self._info["prod_id"] = "".join(chr(i) for i in prod_id)
        self._info["version_id"] = f"{version[1]:X}{version[0]:X}"
        self._info["serial_id"] = "".join(chr(i) for i in serial_num)

    def _get_prod_id(self, verbose=False):
        """Read Product ID, serial number as ASCII"""

        result = []
        result.append(self.get_reg(self._mdef.PROD_ID1.winid, self._mdef.PROD_ID1.addr))
        result.append(self.get_reg(self._mdef.PROD_ID2.winid, self._mdef.PROD_ID2.addr))
        result.append(self.get_reg(self._mdef.PROD_ID3.winid, self._mdef.PROD_ID3.addr))
        result.append(self.get_reg(self._mdef.PROD_ID4.winid, self._mdef.PROD_ID4.addr))

        prodcode = []
        for item in result:
            prodcode.append(item & 0xFF)
            prodcode.append(item >> 8)

        if verbose:
            print("\nPRODUCT ID raw byte code returned:")
            print(prodcode)
            print(
                "\nIMU PRODUCT ID ASCII conversion:\t"
                + "".join(chr(i) for i in prodcode)
            )
        return prodcode

    def _get_firm_ver(self, verbose=False):
        """Read Firmware Version as ASCII"""

        result = self.get_reg(self._mdef.VERSION.winid, self._mdef.VERSION.addr)

        fwcode = []
        fwcode.append(result & 0xFF)
        fwcode.append(result >> 8)

        if verbose:
            print("\nFirmware Version raw byte code returned:")
            print(fwcode)
        return fwcode

    def _get_unit_id(self, verbose=False):
        """Read UNIT_ID, serial number as ASCII"""

        result = []
        result.append(
            self.get_reg(self._mdef.SERIAL_NUM1.winid, self._mdef.SERIAL_NUM1.addr)
        )
        result.append(
            self.get_reg(self._mdef.SERIAL_NUM2.winid, self._mdef.SERIAL_NUM2.addr)
        )
        result.append(
            self.get_reg(self._mdef.SERIAL_NUM3.winid, self._mdef.SERIAL_NUM3.addr)
        )
        result.append(
            self.get_reg(self._mdef.SERIAL_NUM4.winid, self._mdef.SERIAL_NUM4.addr)
        )

        idcode = []
        for item in result:
            idcode.append(item & 0xFF)
            idcode.append(item >> 8)

        if verbose:
            print("\nIMU ID raw byte code returned:")
            print(idcode)
            print("\nIMU ID ASCII conversion:\t" + "".join(chr(i) for i in idcode))
        return idcode

    def _get_burst_config(self, verbose=False):
        """Read BURST_CTRL1 & BURST_CTRL2 to set in
        _status & _burst_out
        """

        tmp1 = self.get_reg(
            self._mdef.BURST_CTRL1.winid, self._mdef.BURST_CTRL1.addr, verbose
        )
        tmp2 = self.get_reg(
            self._mdef.BURST_CTRL2.winid, self._mdef.BURST_CTRL2.addr, verbose
        )

        self._burst_out["ndflags"] = bool(tmp1 & 0x8000)
        self._burst_out["tempc"] = bool(tmp1 & 0x4000)
        self._burst_out["gyro"] = bool(tmp1 & 0x2000)
        self._burst_out["accl"] = bool(tmp1 & 0x1000)
        self._burst_out["dlta"] = bool(tmp1 & 0x0800)
        self._burst_out["dltv"] = bool(tmp1 & 0x0400)
        self._burst_out["qtn"] = bool(tmp1 & 0x0200)
        self._burst_out["atti"] = bool(tmp1 & 0x0100)
        self._burst_out["gpio"] = bool(tmp1 & 0x0004)
        self._burst_out["counter"] = bool(tmp1 & 0x0002)
        self._burst_out["chksm"] = bool(tmp1 & 0x0001)

        self._burst_out["tempc32"] = bool(tmp2 & 0x4000)
        self._burst_out["gyro32"] = bool(tmp2 & 0x2000)
        self._burst_out["accl32"] = bool(tmp2 & 0x1000)
        self._burst_out["dlta32"] = bool(tmp2 & 0x0800)
        self._burst_out["dltv32"] = bool(tmp2 & 0x0400)
        self._burst_out["qtn32"] = bool(tmp2 & 0x0200)
        self._burst_out["atti32"] = bool(tmp2 & 0x0100)

        self._b_struct = self._get_burst_struct_fmt()
        self._status["burst_fields"] = self._get_burst_fields()

        if verbose:
            print(self._burst_out)

    def _get_burst_struct_fmt(self):
        """Determines the structure format for burst packet
        based on _burst_out (from BURST_CTRL1 & BURST_CTRL2)
        """

        # Build struct format based on decoded flags
        # of bytes from BURST_CTRL & SIG_CTRL
        # > = Big endian, B = unsigned char
        # i = int (4 byte), I = unsigned int (4 byte)
        # h = short (2byte), H = unsigned short (2 byte)

        _map_struct = {
            "ndflags": "H",
            "tempc": "h",
            "gyro": "hhh",
            "accl": "hhh",
            "dlta": "hhh",
            "dltv": "hhh",
            "qtn": "hhhh",
            "atti": "hhh",
            "gpio": "H",
            "counter": "H",
            "chksm": "H",
            "tempc32": "i",
            "gyro32": "iii",
            "accl32": "iii",
            "dlta32": "iii",
            "dltv32": "iii",
            "qtn32": "iiii",
            "atti32": "iii",
        }
        # Header Byte
        struct_list = [">B"]
        for key in self._burst_out:
            if key == "tempc32":
                break
            # If status is True, then also check 32-bit status else use 16-bit
            if self._burst_out.get(key):
                if self._burst_out.get(f"{key}32"):
                    struct_list.append(_map_struct.get(f"{key}32"))
                else:
                    struct_list.append(_map_struct.get(key))
        # Delimiter Byte
        struct_list.append("B")
        return "".join(struct_list)

    def _get_burst_fields(self):
        """Returns enabled burst_fields based on _burst_out"""

        burst_fields = []
        for key, value in self._burst_out.items():
            if key == "tempc32":
                break
            if value:
                if key in ["gyro", "accl", "dlta", "dltv", "atti"]:
                    if self._burst_out.get(f"{key}32"):
                        key = key + "32"
                    burst_fields.append(f"{key}_X")
                    burst_fields.append(f"{key}_Y")
                    burst_fields.append(f"{key}_Z")
                elif key in ["qtn"]:
                    if self._burst_out.get(f"{key}32"):
                        key = key + "32"
                    burst_fields.append(f"{key}_0")
                    burst_fields.append(f"{key}_1")
                    burst_fields.append(f"{key}_2")
                    burst_fields.append(f"{key}_3")
                elif key in ["tempc"]:
                    if self._burst_out.get(f"{key}32"):
                        key = key + "32"
                    burst_fields.append(key)
                else:
                    burst_fields.append(key)
        return tuple(burst_fields)

    def _set_ndflags(self, burst_cfg, verbose=False):
        """Configure SIG_CTRL
        NOTE: Not used when UART_AUTO is enabled
        """
        # If UART_AUTO then ignore setting SIG_CTRL
        if self._status["uart_auto"]:
            return

        try:
            # SIG_CTRL
            _wval = (
                int(burst_cfg["tempc"]) << 7
                | int(burst_cfg["gyro"]) << 6
                | int(burst_cfg["gyro"]) << 5
                | int(burst_cfg["gyro"]) << 4
                | int(burst_cfg["accl"]) << 3
                | int(burst_cfg["accl"]) << 2
                | int(burst_cfg["accl"]) << 1
            )
            self.set_reg(
                self._mdef.SIG_CTRL.winid, self._mdef.SIG_CTRL.addrh, _wval, verbose
            )
            _wval = (
                int(burst_cfg["dlta"]) << 7
                | int(burst_cfg["dlta"]) << 6
                | int(burst_cfg["dlta"]) << 5
                | int(burst_cfg["dltv"]) << 4
                | int(burst_cfg["dltv"]) << 3
                | int(burst_cfg["dltv"]) << 2
            )
            self.set_reg(
                self._mdef.SIG_CTRL.winid, self._mdef.SIG_CTRL.addr, _wval, verbose
            )
        except KeyError as err:
            print("** Invalid SIG_CTRL setting")
            raise InvalidCommandError from err

    def _set_baudrate(self, baud, verbose=False):
        """Configure Baud Rate
        NOTE: This change occurs immediately on the device
        and will break existing UART communication. The serial
        port to device should be re-opened with the new baudrate
        to re-establish communication
        """

        try:
            writebyte = self._mdef.BAUD_RATE[baud]
            self.set_reg(
                self._mdef.UART_CTRL.winid,
                self._mdef.UART_CTRL.addrh,
                writebyte,
                verbose,
            )
            if verbose:
                print(f"Set Baud Rate = {baud}")
        except KeyError as err:
            print("** Invalid BAUD_RATE")
            raise InvalidCommandError from err

    def _set_output_rate(self, rate, verbose=False):
        """Configure Output Data Rate DOUT_RATE"""

        try:
            writebyte = self._mdef.DOUT_RATE[rate]
            self.set_reg(
                self._mdef.SMPL_CTRL.winid,
                self._mdef.SMPL_CTRL.addrh,
                writebyte,
                verbose,
            )
            self._status["dout_rate"] = rate
            if verbose:
                print(f"Set Output Rate = {rate}")
        except KeyError as err:
            print("** Invalid DOUT_RATE")
            raise InvalidCommandError from err

    def _set_filter(self, filter_type=None, verbose=False):
        """Configure Filter Type FILTER_SEL"""

        if self._status["dout_rate"] is None:
            print("Set Output Rate before setting the filter", "filter setting ignored")
            return

        map_filter = {
            2000: "MV_AVG0",
            1000: "MV_AVG2",
            500: "MV_AVG4",
            400: "MV_AVG8",
            250: "MV_AVG8",
            200: "MV_AVG16",
            125: "MV_AVG16",
            100: "MV_AVG32",
            80: "MV_AVG32",
            62.5: "MV_AVG32",
            50: "MV_AVG64",
            40: "MV_AVG64",
            31.25: "MV_AVG64",
            25: "MV_AVG128",
            20: "MV_AVG128",
            15.625: "MV_AVG128",
        }

        # If no filter_type set to "safe" moving average filter based on DOUT_RATE
        if filter_type is None:
            filter_type = map_filter.get(self._status["dout_rate"])

        _filter_sel = self._mdef.FILTER_SEL
        # For G370PDF1 & G370PDS0, filter setting is non-standard
        # when DOUT_RATE 2000, 400, or 80sps
        if self._info["prod_id"].lower() in [
            "g370pdf1",
            "g370pds0",
        ] and self._status[
            "dout_rate"
        ] in [2000, 400, 80]:
            _filter_sel = self._mdef.FILTER_SEL_2K_400_80

        filter_type = filter_type.upper()
        try:
            writebyte = _filter_sel[filter_type]
            self.set_reg(
                self._mdef.FILTER_CTRL.winid,
                self._mdef.FILTER_CTRL.addr,
                writebyte,
                verbose,
            )
            time.sleep(self._mdef.FILTER_SETTING_DELAY_S)
            result = 0x0020
            while (result & 0x0020) != 0:
                result = self.get_reg(
                    self._mdef.FILTER_CTRL.winid, self._mdef.FILTER_CTRL.addr
                )
                if verbose:
                    print(".", end="")
            self._status["filter"] = filter_type
            if verbose:
                print(f"Filter Type = {filter_type}")
        except KeyError as err:
            print("** Invalid FILTER_SEL")
            raise InvalidCommandError from err

    def _set_uart_mode(self, mode, verbose=False):
        """Configure UART Mode"""

        self.set_reg(
            self._mdef.UART_CTRL.winid, self._mdef.UART_CTRL.addr, mode & 0x03, verbose
        )
        self._status["auto_start"] = mode & 0x02 == 2
        self._status["uart_auto"] = mode & 0x01 == 1
        if verbose:
            print(f"IMU UART Mode = {mode}")

    def _set_ext_sel(self, mode, verbose=False):
        """Configure EXT pin function"""

        mode = mode.upper()
        try:
            writebyte = self._mdef.EXT_SEL[mode]
            _tmp = self.get_reg(self._mdef.MSC_CTRL.winid, self._mdef.MSC_CTRL.addr)
            self.set_reg(
                self._mdef.MSC_CTRL.winid,
                self._mdef.MSC_CTRL.addr,
                (_tmp & 0x06) | writebyte << 6,
                verbose,
            )
            if verbose:
                print(f"EXT_SEL = {mode}")
        except KeyError as err:
            print("** Invalid EXT_SEL")
            raise InvalidCommandError from err

    def _set_drdy_polarity(self, act_high=True, verbose=False):
        """Configure DRDY input active polarity"""

        _tmp = self.get_reg(self._mdef.MSC_CTRL.winid, self._mdef.MSC_CTRL.addr)
        if act_high:
            self.set_reg(
                self._mdef.MSC_CTRL.winid,
                self._mdef.MSC_CTRL.addr,
                _tmp | 0x02,
                verbose,
            )
        else:
            self.set_reg(
                self._mdef.MSC_CTRL.winid,
                self._mdef.MSC_CTRL.addr,
                _tmp & 0xC4,
                verbose,
            )
        self._status["drdy_pol"] = act_high
        if verbose:
            print(f"DRDY_POL = {act_high}")

    def _set_accl_range(self, a_range=False, verbose=False):
        """Configure A_RANGE settings"""

        try:
            # Accelerometer A_RANGE_CTRL support only for certain models
            if self._info["prod_id"].lower() not in [
                "g330pdg0",
                "g330pde0",
                "g366pdg0",
                "g366pde0",
                "g370pdg0",
                "g370pdt0",
            ]:
                return

            self.set_reg(
                self._mdef.DLT_CTRL.winid,
                self._mdef.DLT_CTRL.addrh,
                a_range,
                verbose=verbose,
            )
            if a_range:
                self._mdef.SF_ACCL = self._mdef.SF_ACCL * 2
                self._mdef.SF_DLTV = self._mdef.SF_DLTV * 2
            self._status["a_range"] = a_range
        except KeyError as err:
            print("** Failure writing A_RANGE to device")
            raise DeviceConfigurationError from err

    def _config_basic(self, basic_cfg=None, verbose=False):
        """Configure basic core settings based on parameters"""

        if basic_cfg is None:
            basic_cfg = {
                "dout_rate": 200,
                "filter": None,
                "ndflags": True,
                "tempc": True,
                "counter": "sample",
                "is_32bit": True,
            }

        try:
            if basic_cfg.get("ext_trigger"):
                self._set_ext_sel("TypeB", verbose=verbose)
                self._status["ext_trigger"] = True
            if basic_cfg.get("counter"):
                _ext_sel = "gpio" if basic_cfg.get("counter") == "sample" else "reset"
                self._set_ext_sel(_ext_sel, verbose=verbose)
            if basic_cfg.get("drdy_pol"):
                self._set_drdy_polarity(basic_cfg["drdy_pol"], verbose=verbose)
            self._set_output_rate(
                basic_cfg.get("dout_rate", self._mdef.DOUT_RATE[200]), verbose=verbose
            )
            self._set_filter(basic_cfg.get("filter"), verbose=verbose)
            # Already stored in _status dict by _set_filter()
            # so delete it to prevent overwriting dict
            if basic_cfg.get("filter") is None:
                del basic_cfg["filter"]

            _wval = int(bool(basic_cfg.get("auto_start"))) << 1 | int(
                bool(basic_cfg.get("uart_auto"))
            )
            self._set_uart_mode(_wval, verbose=verbose)
            self._set_accl_range(basic_cfg.get("a_range", False), verbose=verbose)

            # BURST_CTRL1 HIGH for basic_cfg
            _wval = (
                int(bool(basic_cfg.get("ndflags"))) << 7
                | int(bool(basic_cfg.get("tempc"))) << 6
                | 1 << 5  # Gyro always enabled
                | 1 << 4  # Accel always enabled
                | 0 << 3  # DLTA
                | 0 << 2  # DLTV
                | 0 << 1  # QTN
                | 0  # ATTI
            )
            self.set_reg(
                self._mdef.BURST_CTRL1.winid,
                self._mdef.BURST_CTRL1.addrh,
                _wval,
                verbose=verbose,
            )
            # BURST_CTRL1 LOW for basic_cfg
            _wval = (
                0 << 2  # GPIO
                | int(bool(basic_cfg.get("counter"))) << 1
                | int(bool(basic_cfg.get("chksm")))
            )
            self.set_reg(
                self._mdef.BURST_CTRL1.winid,
                self._mdef.BURST_CTRL1.addr,
                _wval,
                verbose=verbose,
            )
            # BURST_CTRL2 for basic cfg
            _wval = 0x7F if basic_cfg.get("is_32bit") else 0x00
            self.set_reg(
                self._mdef.MSC_CTRL.winid,
                self._mdef.BURST_CTRL2.addrh,
                _wval,
                verbose=verbose,
            )
            # Update _status dict
            self._status.update(basic_cfg)

            # If UART_AUTO then ignore setting SIG_CTRL
            if self._status.get("uart_auto"):
                return

            # SIG_CTRL for basic_cfg
            _wval = (
                int(bool(basic_cfg.get("tempc"))) << 7
                | 7 << 4  # GyroXYZ
                | 7 << 1  # AcclXYZ
            )
            self.set_reg(
                self._mdef.SIG_CTRL.winid,
                self._mdef.SIG_CTRL.addrh,
                _wval,
                verbose=verbose,
            )
        except KeyError as err:
            print("** Failure writing basic configuration to device")
            raise DeviceConfigurationError from err

    def _config_dlt(self, dlt_cfg=None, verbose=False):
        """Configure delta angle/velocity settings based on parameters"""

        if dlt_cfg is None:
            print("No dlt_cfg specified. Bypassing.")
            return

        if dlt_cfg.get("dlta_sf_range") is None:
            dlt_cfg["dlta_sf_range"] = 12
        if dlt_cfg.get("dltv_sf_range") is None:
            dlt_cfg["dltv_sf_range"] = 12

        try:
            # DLT_CTRL for dlt_cfg
            _wval = (dlt_cfg.get("dlta_sf_range") & 0xF) << 4 | (
                dlt_cfg.get("dltv_sf_range") & 0xF
            )
            self.set_reg(
                self._mdef.DLT_CTRL.winid,
                self._mdef.DLT_CTRL.addr,
                _wval,
                verbose=verbose,
            )
            # BURST_CTRL1 HIGH for dlt_cfg
            _tmp = self.get_reg(
                self._mdef.BURST_CTRL1.winid,
                self._mdef.BURST_CTRL1.addr,
                verbose=verbose,
            )
            _wval = (
                (_tmp >> 8) & 0xF3
                | (dlt_cfg.get("dlta", False) << 3)  # DLTA_OUT
                | (dlt_cfg.get("dltv", False) << 2)  # DLTV_OUT
            )
            self.set_reg(
                self._mdef.BURST_CTRL1.winid,
                self._mdef.BURST_CTRL1.addrh,
                _wval,
                verbose=verbose,
            )
            # ATTI_CTRL for dlt_cfg
            _tmp = self.get_reg(
                self._mdef.ATTI_CTRL.winid, self._mdef.ATTI_CTRL.addr, verbose=verbose
            )
            _atti_on = 0b01 if any((dlt_cfg.get("dlta"), dlt_cfg.get("dltv"))) else 0b00
            _wval = (_tmp >> 8) & 0xF9 | (
                _atti_on << 1
            )  # ATTI_ON, 0b01 = Delta Angle/Velocity
            self.set_reg(
                self._mdef.ATTI_CTRL.winid,
                self._mdef.ATTI_CTRL.addrh,
                _wval,
                verbose=verbose,
            )
            # Update _dlt_status dict
            self._dlt_status.update(dlt_cfg)

            # If UART_AUTO then ignore setting SIG_CTRL
            if self._status.get("uart_auto"):
                return
            # SIG_CTRL for dlt_cfg
            _wval = 7 << 5 | 7 << 2  # DltaXYZ  # DltvXYZ
            self.set_reg(
                self._mdef.SIG_CTRL.winid,
                self._mdef.SIG_CTRL.addr,
                _wval,
                verbose=verbose,
            )
        except KeyError as err:
            print("** Failure writing delta angle/velocity configuration to device")
            raise DeviceConfigurationError from err

    def _config_atti(self, atti_cfg=None, verbose=False):
        """Configure attitude or quaternion settings based on parameters"""

        if atti_cfg is None:
            print("No atti_cfg specified. Bypassing.")
            return

        # Exit if model does not support the attitude function
        if self._info.get("prod_id").lower() not in [
            "g330pde0",
            "g330pdg0",
            "g366pde0",
            "g366pdg0",
            "g365pdf1",
            "g365pdc1",
        ]:
            print("Attitude or Quaternion not supported.")
            return
        # Exit if ATTI_CONV not between 0 or 23
        if atti_cfg.get("conv") < 0 or atti_cfg.get("conv") > 23:
            print("ATTI_CONV must be between 0 and 23.")
            return
        try:
            # Auto-disable attitude output when delta angle/velocity enabled
            if any((self._dlt_status.get("dlta"), self._dlt_status.get("dltv"))):
                print(
                    "Delta angle/velocity enabled. "
                    "Attitude or Quaternion automatically disabled"
                )
                atti_cfg["atti"], atti_cfg["qtn"] = False, False

            # BURST_CTRL1 HIGH for atti_cfg
            _tmp = self.get_reg(
                self._mdef.BURST_CTRL1.winid,
                self._mdef.BURST_CTRL1.addr,
                verbose=verbose,
            )
            _wval = (
                (_tmp >> 8) & 0xFC
                | atti_cfg.get("qtn", False) << 1  # QTN_OUT
                | atti_cfg.get("atti", False)  # ATTI_OUT
            )
            self.set_reg(
                self._mdef.BURST_CTRL1.winid,
                self._mdef.BURST_CTRL1.addrh,
                _wval,
                verbose=verbose,
            )
            # ATTI_CTRL HIGH for atti_cfg, only set if delta angle/velocity is disabled
            if not any((self._dlt_status.get("dlta"), self._dlt_status.get("dltv"))):
                _tmp = self.get_reg(
                    self._mdef.ATTI_CTRL.winid,
                    self._mdef.ATTI_CTRL.addr,
                    verbose=verbose,
                )
                _atti_on = (
                    0b10 if any((atti_cfg.get("atti"), atti_cfg.get("qtn"))) else 0b00
                )
                _wval = (
                    (_tmp >> 8) & 0xF1
                    | (
                        int(atti_cfg.get("mode") == "euler") << 3
                    )  # ATTI_MODE = Euler or Inclination
                    | (
                        _atti_on << 1
                    )  # ATTI_ON, 0b10 = Attitude or Quaternion, 0b00 = Disabled
                )
                self.set_reg(
                    self._mdef.ATTI_CTRL.winid,
                    self._mdef.ATTI_CTRL.addrh,
                    _wval,
                    verbose=verbose,
                )
            # ATTI_CTRL LOW
            self.set_reg(
                self._mdef.ATTI_CTRL.winid,
                self._mdef.ATTI_CTRL.addr,
                atti_cfg.get("conv", 0),
                verbose=verbose,
            )
            # GLOB_CMD2 for atti_cfg
            _wval = (
                self._mdef.ATTI_MOTION_PROFILE[atti_cfg.get("profile", "modea").upper()]
                << 4
            )
            # ATTITUDE_MOTION_PROFILE
            self.set_reg(
                self._mdef.GLOB_CMD2.winid,
                self._mdef.GLOB_CMD2.addr,
                _wval,
                verbose=verbose,
            )
            time.sleep(self._mdef.ATTI_MOTION_SETTING_DELAY_S)
            # Update _atti_status dict
            self._atti_status.update(atti_cfg)
        except KeyError as err:
            print("** Failure writing attitude or quaternion configuration to device")
            raise DeviceConfigurationError from err

    def _get_sample(self, inter_delay=0.000001):
        """Return single burst from device data
        if malformed find next header and raise InvalidBurstReadError
        """

        # Return if struct is empty, then device is not configured
        if not self._b_struct:
            print("** Device not configured. Have you run config()?")
            return None
        # Return if still in CONFIG mode
        if self._status.get("is_config"):
            print("** Device not in SAMPLING mode. Run goto('sampling') first.")
            return None
        # get data structure of the burst
        data_struct = struct.Struct(self._b_struct)
        if not self._status["uart_auto"]:
            self._set_raw(self._mdef.BURST_MARKER, 0x00)

        try:
            while self._serial_epson.in_waiting < data_struct.size:
                time.sleep(inter_delay)
            data_str = self._serial_epson.read(data_struct.size)

            data_unpacked = data_struct.unpack(data_str)

            if (data_unpacked[0] != self._mdef.BURST_MARKER) or (
                data_unpacked[-1] != self._mdef.DELIMITER
            ):
                raise InvalidBurstReadError

            # Strip out the header and delimter byte
            return data_unpacked[1:-1]
        except InvalidBurstReadError:
            self._find_sync()
            raise
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise

    def _proc_sample(self, raw_burst=None):
        """Process single burst read of device data
        Returns processed data in a tuple
        """

        if raw_burst is None:
            return None

        # Create list of fields to loop over
        burst_fields = self._status.get("burst_fields")

        # locally held scale factor
        sf_tempc = self._mdef.SF_TEMPC
        tempc_25c = self._mdef.TEMPC_25C
        sf_gyro = self._mdef.SF_GYRO
        sf_accl = self._mdef.SF_ACCL
        sf_dlta = self._mdef.SF_DLTA * 2 ** self._dlt_status.get("dlta_sf_range", 12)
        sf_dltv = self._mdef.SF_DLTV * 2 ** self._dlt_status.get("dltv_sf_range", 12)
        sf_qtn = 1 / 2**14

        # Set ATTI_SF to 0 for unsupported models
        atti_supported = self._info["prod_id"].lower() in [
            "g330pde0",
            "g330pdg0",
            "g366pde0",
            "g366pdg0",
            "g365pdf1",
            "g365pdc1",
        ]
        sf_atti = self._mdef.SF_ATTI if atti_supported else 0

        # Map conversions for scaled
        map_scl = {
            "ndflags": lambda x: x,
            "tempc": lambda x: round(((x - tempc_25c) * sf_tempc) + 25, 4),
            "gyro": lambda x: round(x * sf_gyro, 6),
            "accl": lambda x: round(x * sf_accl, 6),
            "dlta": lambda x: round(x * sf_dlta, 6),
            "dltv": lambda x: round(x * sf_dltv, 6),
            "qtn": lambda x: round(x * sf_qtn, 6),
            "atti": lambda x: round(x * sf_atti, 6),
            "tempc32": lambda x: round(
                ((x - (tempc_25c * 65536)) * sf_tempc / 65536) + 25, 4
            ),
            "gyro32": lambda x: round(x * sf_gyro / 65536, 8),
            "accl32": lambda x: round(x * sf_accl / 65536, 8),
            "dlta32": lambda x: round(x * sf_dlta / 65536, 8),
            "dltv32": lambda x: round(x * sf_dltv / 65536, 8),
            "qtn32": lambda x: round(x * sf_qtn / 65536, 8),
            "atti32": lambda x: round(x * sf_atti / 65536, 8),
            "gpio": lambda x: x,
            "counter": lambda x: x,
            "chksm": lambda x: x,
        }

        return tuple(
            map_scl[key.split("_")[0]](bdata)
            for key, bdata in zip(burst_fields, raw_burst)
        )

    def _find_sync(self, verbose=False):
        """Find the next DELIMITER byte in serial input buffer"""

        while True:
            if self._serial_epson.in_waiting > 0:
                # Read 1 byte and search for self._mdef.DELIMITER
                data = self._serial_epson.read(1)
                if verbose:
                    sys.stdout.write(".")
                if self._mdef.DELIMITER in data:
                    if verbose:
                        sys.stdout.write("!\n")
                    break

    def _clear_rx_buffer(self, retries=10, retry_delay=0.10, verbose=False):
        """Flushes the UART RX buffer until empty.
        Returns False if retries exceeded.
        """

        try:
            _count = 0
            while self._serial_epson.in_waiting != 0:
                self._serial_epson.reset_input_buffer()
                time.sleep(retry_delay)  # Longer than slowest sample_rate is 15.625Hz
                _count = _count + 1
                if verbose:
                    print(f"RX {_count}: {self._serial_epson.in_waiting}")
                if _count > retries:
                    raise UartRxClearBufferError(
                        "** Rx Buffer contains data after reset_input_buffer() "
                        "Is device in SAMPLING mode?"
                    )
            return True
        except KeyboardInterrupt:
            return False

    def _sync_tx_buffer(self, retries=10, retry_delay=0.10, verbose=False):
        """Sends self._mdef.DELIMITER byte until an expected register read response is returned
        to synchronize device's command interface. Returns False if retries exceeded
        """

        try:
            # Send self._mdef.DELIMITER until Rx buffer receives RESPONSE (4 bytes)
            _count = 0
            while self._serial_epson.in_waiting < 4:
                self._serial_epson.write(struct.pack("B", self._mdef.DELIMITER))
                time.sleep(retry_delay)  # Longer than slowest sample_rate is 15.625Hz
                _count = _count + 1
                if verbose:
                    print(f"TX {_count}: {self._serial_epson.in_waiting}")
                if _count > retries:
                    raise UartTxSyncError("** Device not sending RESPONSE")

            # Check returned bytes for header & delimiter
            resp_struct = struct.Struct(">BHB")
            resp_raw = self._serial_epson.read(resp_struct.size)

            # The data must be unpacked to be read correctly
            rdata = ReadResponse._make(resp_struct.unpack(resp_raw))

            # Validation check on Header Byte, and Delimiter Byte
            if (rdata.addr != self._mdef.DELIMITER) or (
                rdata.delimiter != self._mdef.DELIMITER
            ):
                raise UartTxSyncError(
                    f"** Unexpected response ({rdata.addr:02X}, "
                    f"{rdata.data:04X}, {rdata.delimiter:02X})"
                )
            return True
        except KeyboardInterrupt:
            return False

    def _sync_device(self, retries=10, verbose=False):
        """
        Places device into CONFIG mode.
        Clears the serial RX buffer, then
        try to sync the serial Tx.
        Returns False if retries exceeded
        """
        try:
            _count = 0
            while _count < retries:
                # Put device in CONFIG mode
                self.set_reg(
                    self._mdef.MODE_CTRL.winid,
                    self._mdef.MODE_CTRL.addrh,
                    self._mdef.MODE_CMD.get("CONFIG"),
                    verbose=verbose,
                )
                if self._clear_rx_buffer(verbose=verbose):
                    if self._sync_tx_buffer(verbose=verbose):
                        self._status["is_config"] = True
                        return True
                _count = _count + 1
            raise SyncRetriesError("** Failure trying to sync with device")
        except KeyboardInterrupt:
            return False
