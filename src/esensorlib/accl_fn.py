#!/usr/bin/env python

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

"""Accelerometer class for accelerometer functions
Contains:
- AcclFn() class
- Descriptive Exceptions specific to this package
"""

import struct
import time
from types import MappingProxyType


# Custom Exceptions
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


class AcclFn:
    """
    ACCL functions

    ...

    Attributes
    ----------
    info : MappingProxyType
        dict of device ID information
    status : MappingProxyType
        dict of device status
    burst_out : MappingProxyType
        dict of burst output status
    burst_fields : tuple
        tuple of fields for sensor burst read
    mdef : object
        model specific definitions - addresses, values, constants, etc
    reg : enum
        model specific register addresses from mdef

    Methods
    -------
    get_reg(winnum, regaddr, verbose=False)
        16-bit read from specified register address

    set_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write to specified register address

    set_config(**cfg)
        Configure device from key, value parameters

    set_baudrate(baud, verbose=False)
        Configure device baudrate setting NOTE: This takes immediate effect.

    init_check(verbose=False)
        Check if HARD_ERR (hardware error) is reported
        Usually performed once after startup

    do_selftest(verbose=False)
        Perform self-test and check if ST_ERR (self-test error) is reported

    do_softreset(verbose=False)
        Perform software reset

    do_flashtest(verbose=False)
        Perform self-test on flash and return result

    backup_flash(verbose=False)
        Perform flash backup of registers and return result

    init_backup(verbose=False)
        Restore flash to factory default and return result

    goto(mode, post_delay, verbose=False)
        Set device to CONFIG or SAMPLING mode

    get_mode(verbose=False)
        Return device mode status as either CONFIG or SAMPLING

    read_sample()
        Return scaled burst sample of sensor data

    read_sample_unscaled()
        Return unscaled burst sample of sensor data
    """

    def __init__(self, obj_regif, obj_mdef, device_info=None, verbose=False):
        """
        Parameters
        ----------
        obj_regif : RegInterface() instance
            Register interface object passed from SensorDevice() instance
        obj_mdef : module
            Model definitions passed from SensorDevice() instance
        device_info : dict
            prod_id, version_id, serial_id as key, value pairs
        verbose : bool
            If True outputs additional debug info
        """

        self.regif = obj_regif
        self.model_def = obj_mdef

        self._device_info = device_info or {
            "prod_id": None,
            "version_id": None,
            "serial_id": None,
        }

        self._verbose = verbose

        # Stores device config status with defaults
        self._status = {
            "dout_rate": 200,
            "filter_sel": None,
            "ndflags": False,
            "tempc": False,
            "counter": False,
            "chksm": False,
            "auto_start": False,
            "ext_trigger": False,
            "uart_auto": False,
            "drdy_pol": True,
            "tilt": 0,
            "is_config": True,
        }
        # Stores current burst output status with defaults
        self._burst_out = {
            "ndflags": False,
            "tempc": False,
            "acclx": True,
            "accly": True,
            "acclz": True,
            "counter": False,
            "chksm": False,
        }
        # Stores burst output fields
        self._burst_fields = ()

        # Store burst structure format for unpacking bytes
        self._b_struct = ""

    def __repr__(self):
        cls = self.__class__.__name__
        string_val = "".join(
            [
                f"{cls}(obj_regif={repr(self.regif)}, ",
                f"obj_mdef={repr(self.model_def)}, ",
                f"device_info={self._device_info}, ",
                f"verbose={self._verbose})",
            ]
        )
        return string_val

    def __str__(self):
        string_val = "".join(
            [
                "\nAccelerometer Functions",
                f"\n  Register Interface: {repr(self.regif)}",
                f"\n  Model Definitions: {self.model_def}",
                f"\n  Device Info: {self._device_info}",
                f"\n  Verbose: {self._verbose}",
            ]
        )
        return string_val

    @property
    def info(self):
        """property for device info as MappingProxyType"""
        return MappingProxyType(self._device_info)

    @property
    def status(self):
        """property for device status as MappingProxyType"""
        return MappingProxyType(self._status)

    @property
    def burst_out(self):
        """property for burst_output as MappingProxyType"""
        return MappingProxyType(self._burst_out)

    @property
    def burst_fields(self):
        """property for burst_fields"""
        return self._burst_fields

    @property
    def mdef(self):
        """property from SensorDevice() instance model definitions"""
        return self.model_def

    @property
    def reg(self):
        """property from SensorDevice() instance registers"""
        return self.model_def.Reg

    def get_reg(self, winnum, regaddr, verbose=False):
        """redirect to RegInterface() instance"""
        return self.regif.get_reg(winnum, regaddr, verbose)

    def set_reg(self, winnum, regaddr, write_byte, verbose=False):
        """redirect to RegInterface() instance"""
        self.regif.set_reg(winnum, regaddr, write_byte, verbose)

    def set_config(self, **cfg):
        """Configure device based on key, value parameters.
        Configure with supplied key, values,
        Then read burst configuration from BURST_CTRL
        and update status dict

        Parameters
        ----------
        "dout_rate": int,
        "filter_sel": str,
        "ndflags": bool,
        "tempc": bool,
        "counter": bool,
        "chksm": bool,
        "auto_start": bool,
        "ext_trigger": bool,
        "uart_auto": bool,
        "burst_fields": [],
        "is_config": bool,
        "verbose" : bool, If True outputs additional debug info
        """

        is_dict = isinstance(cfg, dict)
        is_none = cfg is None
        if not (is_dict or is_none):
            raise TypeError(f"** cfg parameters must be **kwargs or None: {cfg}")

        verbose = cfg.get("verbose", False)
        self.goto("config", verbose=verbose)
        self._config_basic(**cfg)
        self._get_burst_config(verbose=verbose)
        if verbose:
            print(f"Status: {self._status}")

    def set_baudrate(self, baud, verbose=False):
        """Configure Baud Rate
        NOTE: This change occurs immediately on the device
        and will break existing UART communication. The serial
        port to device should be re-opened with the new baudrate
        to re-establish communication

        Parameters
        ----------
        baud : int
            new baudrate setting
        verbose : bool
            If True outputs additional debug info
        """

        try:
            writebyte = self.mdef.BAUD_RATE[baud]
            self.set_reg(
                self.reg.UART_CTRL.WINID,
                self.reg.UART_CTRL.ADDRH,
                writebyte,
                verbose,
            )
            if verbose:
                print(f"Set Baud Rate = {baud}")
        except KeyError as err:
            print(f"** Invalid BAUD_RATE, Set Baud Rate = {baud}")
            raise InvalidCommandError from err

    def init_check(self, verbose=False):
        """Check for HARD_ERR (hardware error)

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        HardwareError
            non-zero results indicates HARD_ERR
        """

        result = 0x0400
        while (result & 0x0400) != 0:
            # Wait for NOT_READY
            result = self.get_reg(
                self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR, verbose
            )
            if verbose:
                print(".", end="")
        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
        )
        if verbose:
            print("IMU Startup Check")
        result = result & 0x0060
        if result:
            raise HardwareError("** Hardware Failure. HARD_ERR bits")

    def do_selftest(self, verbose=False):
        """Initiate Self Test
           Z_SENS, Y_SENS, X_SENS, ACC_TEST, TEMP_TEST
           VDD_TEST

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        SelfTestError
            non-zero results indicates DIAG_STAT error
        """

        print("ACC_TEST, TEMP_TEST, VDD_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x07, verbose)
        time.sleep(self.mdef.SELFTEST_DELAY_S)
        result = 0x0700
        while (result & 0x0700) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        print("XSENS_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x10, verbose)
        time.sleep(self.mdef.SELFTEST_SENSAXIS_DELAY_S)
        result = 0x0100
        while (result & 0x0100) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        print("YSENS_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x20, verbose)
        time.sleep(self.mdef.SELFTEST_SENSAXIS_DELAY_S)
        result = 0x0200
        while (result & 0x0200) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        print("ZSENS_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x40, verbose)
        time.sleep(self.mdef.SELFTEST_SENSAXIS_DELAY_S)
        result = 0x0400
        while (result & 0x0400) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
        )
        if result:
            raise SelfTestError(f"** Self Test Failure. DIAG_STAT={result: 04X}")
        print("Self Test completed with no errors")

    def do_softreset(self, verbose=False):
        """Initiate Software Reset

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info
        """

        self.set_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR, 0x80, verbose)
        time.sleep(self.mdef.RESET_DELAY_S)
        print("Software Reset Completed")

    def do_flashtest(self, verbose=False):
        """Initiate Flash Test

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        FlashTestError
            non-zero results indicates FLASH_ERR
        """

        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x08, verbose)
        time.sleep(self.mdef.SELFTEST_FLASH_DELAY_S)
        result = 0x0800
        while (result & 0x0800) != 0:
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
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
            If True outputs additional debug info

        Raises
        -------
        FlashBackupError
            non-zero results indicates FLASH_BU_ERR
        """

        self.set_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR, 0x08, verbose)
        time.sleep(self.mdef.FLASH_BACKUP_DELAY_S)
        result = 0x0008
        while (result & 0x0008) != 0:
            result = self.get_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
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
            If True outputs additional debug info

        Raises
        -------
        FlashBackupError
            non-zero results indicates FLASH_BU_ERR
        """

        self.set_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR, 0x04, verbose)
        time.sleep(self.mdef.FLASH_BACKUP_DELAY_S)
        result = 0x0010
        while (result & 0x0010) != 0:
            result = self.get_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
        )
        result = result & 0x0001
        if result:
            raise FlashBackupError("** Flash Backup Failure. FLASH_BU_ERR bit")
        print("Initial Backup Completed")

    def goto(self, mode, post_delay=0.2, verbose=False):
        """Set MODE_CMD to either CONFIG or SAMPLING or SLEEP mode.

        NOTE: SLEEP mode cannot be exited from without EXT signal or HW reset

        If entering SAMPLING, store the state of burst configuration
        NOTE: Device must be in SAMPLING mode to call read_sample()
        NOTE: Device must be in CONFIG mode for most register write functions

        Parameters
        ----------
        mode : str
            Can be "config" or "sampling" or "sleep"
        post_delay : float
            Delay time in seconds after sending command before returning
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        InvalidCommandError
            Raises to caller when mode is not valid string
        """
        if not isinstance(mode, str):
            raise TypeError(
                f"** Mode parameter must be 'config' or 'sampling' or 'sleep': {mode}"
            )

        mode = mode.upper()
        try:
            # When entering SAMPLING mode, update the
            # self._burst_out & self._status from
            # _get_burst_config()
            if mode == "SAMPLING":
                self._get_burst_config(verbose=verbose)

            self.set_reg(
                self.reg.MODE_CTRL.WINID,
                self.reg.MODE_CTRL.ADDRH,
                self.mdef.MODE_CMD[mode],
                verbose=verbose,
            )
            time.sleep(post_delay)
            # When entering CONFIG mode
            # flush any pending incoming burst data
            if mode == "CONFIG":
                self.regif.port_io.reset_input_buffer()
            if verbose:
                print(f"MODE_CMD = {mode}")
            self._status["is_config"] = mode == "CONFIG"
        except KeyError as err:
            print("** Invalid MODE_CMD")
            raise InvalidCommandError from err

    def get_mode(self, verbose=False):
        """Return MODE_STAT bit

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Returns
        -------
        int
            0 = Sampling, 1 = Config, 2 = Sleep
        """

        result = 0x0300
        while (result & 0x0300) != 0:
            result = self.get_reg(
                self.reg.MODE_CTRL.WINID, self.reg.MODE_CTRL.ADDR, verbose=verbose
            )
        result = (
            self.get_reg(
                self.reg.MODE_CTRL.WINID, self.reg.MODE_CTRL.ADDR, verbose=verbose
            )
            & 0x0C00
        ) >> 10
        self._status["is_config"] = result == 0x01
        if verbose:
            print(f"MODE_CMD = {result}")
        return result

    def read_sample(self, verbose=False):
        """Read one burst of sensor data, post processes,
        and returns scaled sensor data.
        If burst read contains corrupted data, returns ()
        NOTE: Device must be in SAMPLING mode before calling

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Returns
        -------
        tuple
            tuple containing single set of sensor burst data with or
            without scale factor applied
            () if burst data is malformed or device not in SAMPLING

        Raises
        -------
        KeyboardInterrupt
            Raises to caller CTRL-C
        IOError
            Raises to caller any type of serial port error
        """

        try:
            raw_burst = self._get_sample(verbose=verbose)
            return self._proc_sample(raw_burst)
        except InvalidCommandError:
            return ()
        except InvalidBurstReadError:
            return ()
        except KeyboardInterrupt:
            print("Stop reading sensor")
            raise
        except IOError:
            print("** Failure reading sensor sample")
            raise

    def read_sample_unscaled(self, verbose=False):
        """Read one burst of sensor data, post processes,
        and returns unscaled sensor data.
        If burst read contains corrupted data, returns ()
        NOTE: Device must be in SAMPLING mode before calling

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Returns
        -------
        tuple
            tuple containing single set of sensor burst data with or
            without scale factor applied
            () if burst data is malformed or device not in SAMPLING

        Raises
        -------
        KeyboardInterrupt
            Raises to caller CTRL-C
        IOError
            Raises to caller any type of serial port error
        """

        try:
            raw_burst = self._get_sample(verbose=verbose)
            return raw_burst
        except InvalidCommandError:
            return ()
        except InvalidBurstReadError:
            return ()
        except KeyboardInterrupt:
            print("Stop reading sensor")
            raise
        except IOError:
            print("** Failure reading sensor sample")
            raise

    def _get_burst_config(self, verbose=False):
        """Read BURST_CTRL to update
        _b_struct, _burst_out, _burst_fields

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info
        """

        tmp1 = self.get_reg(
            self.reg.BURST_CTRL.WINID, self.reg.BURST_CTRL.ADDR, verbose
        )

        self._burst_out["ndflags"] = bool(tmp1 & 0x8000)
        self._burst_out["tempc"] = bool(tmp1 & 0x4000)
        self._burst_out["acclx"] = bool(tmp1 & 0x0400)
        self._burst_out["accly"] = bool(tmp1 & 0x0200)
        self._burst_out["acclz"] = bool(tmp1 & 0x0100)
        self._burst_out["counter"] = bool(tmp1 & 0x0002)
        self._burst_out["chksm"] = bool(tmp1 & 0x0001)

        self._b_struct = self._get_burst_struct_fmt()
        self._burst_fields = self._get_burst_fields()

        if verbose:
            print(f"_get_burst_struct_fmt(): {self._b_struct}")
            print(f"_get_burst_fields(): {self._burst_fields}")
            print(f"_get_burst_config(): {self._burst_out}")

    def _get_burst_struct_fmt(self):
        """Returns the struct format for burst packet
        based on _burst_out (from BURST_CTRL)

        Returns
        -------
        list
            containing struct format describing burst data
        """

        # Build struct format based on decoded flags
        # of bytes from BURST_CTRL & SIG_CTRL
        # > = Big endian, B = unsigned char
        # i = int (4 byte), I = unsigned int (4 byte)
        # h = short (2byte), H = unsigned short (2 byte)

        _map_struct = {
            "ndflags": "H",
            "tempc": "i",
            "acclx": "i",
            "accly": "i",
            "acclz": "i",
            "counter": "H",
            "chksm": "H",
        }
        # Header Byte
        struct_list = [">B"]
        for key in self._burst_out:
            if self._burst_out.get(key):
                struct_list.append(_map_struct.get(key))
        # Delimiter Byte
        struct_list.append("B")
        return "".join(struct_list)

    def _get_burst_fields(self):
        """Returns tuple containing enabled burst_fields based on _burst_out

        Returns
        -------
        tuple
            containing strings of burst fields
        """

        burst_fields = [key for key, value in self._burst_out.items() if value is True]
        # Modify if TILT function enabled
        if self._status.get("tilt") & 0b100:
            burst_fields = [field.replace("acclx", "tiltx") for field in burst_fields]
        if self._status.get("tilt") & 0b010:
            burst_fields = [field.replace("accly", "tilty") for field in burst_fields]
        if self._status.get("tilt") & 0b001:
            burst_fields = [field.replace("acclz", "tiltz") for field in burst_fields]

        return tuple(burst_fields)

    def _set_ndflags(self, burst_cfg, verbose=False):
        """Configure SIG_CTRL based on burst_cfg dict
        NOTE: Not used when UART_AUTO is enabled

        Parameters
        ----------
        burst_cfg : dict
            parses burst flags from dict to enable in SIG_CTRL
        verbose : bool
            If True outputs additional debug info
        """
        # If UART_AUTO then ignore setting SIG_CTRL
        if self._status["uart_auto"]:
            return

        try:
            # SIG_CTRL
            _wval = (
                int(burst_cfg["tempc"]) << 7
                | int(burst_cfg["acclx"]) << 3
                | int(burst_cfg["accly"]) << 2
                | int(burst_cfg["acclz"]) << 1
            )
            self.set_reg(
                self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDRH, _wval, verbose
            )

        except KeyError as err:
            print("** Invalid SIG_CTRL setting")
            raise InvalidCommandError from err

    def _set_output_rate(self, rate, verbose=False):
        """Configure Output Data Rate DOUT_RATE

        Parameters
        ----------
        rate : int
            Supported DOUT_RATE in Hz to apply
        verbose : bool
            If True outputs additional debug info
        Raises
        -------
        InvalidCommandError
            When unsupported rate is specified
        """

        try:
            writebyte = self.mdef.DOUT_RATE[rate]
            self.set_reg(
                self.reg.SMPL_CTRL.WINID,
                self.reg.SMPL_CTRL.ADDRH,
                writebyte,
                verbose,
            )
            self._status["dout_rate"] = rate
            if verbose:
                print(f"Set Output Rate = {rate}")
        except KeyError as err:
            print(f"** Invalid DOUT_RATE, Set Output Rate = {rate}")
            raise InvalidCommandError from err

    def _set_filter(self, filter_type=None, verbose=False):
        """Configure Filter Type FILTER_SEL

        Parameters
        ----------
        filter_type : str
            Supported filter setting to apply.
            If None, then auto select based on DOUT_RATE
        verbose : bool
            If True outputs additional debug info
        Raises
        -------
        InvalidCommandError
            When unsupported filter_type is specified
        """

        if self._status["dout_rate"] is None:
            print("Set Output Rate before setting the filter", "filter setting ignored")
            return

        map_filter = {
            1000: "K512_FC460",
            500: "K512_FC210",
            200: "K512_FC60",
            100: "K512_FC16",
            50: "K512_FC9",
        }

        # If no filter_type set to "safe" filter based on DOUT_RATE
        if filter_type is None:
            filter_type = map_filter.get(self._status["dout_rate"])

        _filter_sel = self.mdef.FILTER_SEL

        filter_type = filter_type.upper()
        try:
            writebyte = _filter_sel[filter_type]
            self.set_reg(
                self.reg.FILTER_CTRL.WINID,
                self.reg.FILTER_CTRL.ADDR,
                writebyte,
                verbose,
            )
            time.sleep(self.mdef.FILTER_SETTING_DELAY_S)
            result = 0x0020
            while (result & 0x0020) != 0:
                result = self.get_reg(
                    self.reg.FILTER_CTRL.WINID, self.reg.FILTER_CTRL.ADDR
                )
                if verbose:
                    print(".", end="")
            self._status["filter_sel"] = filter_type
            if verbose:
                print(f"Filter Type = {filter_type}")
        except KeyError as err:
            print(f"** Invalid FILTER_SEL, Filter Type = {filter_type}")
            raise InvalidCommandError from err

    def _set_uart_mode(self, mode, verbose=False):
        """Configure AUTO_START and UART_AUTO bits in UART_CTRL register

        Parameters
        ----------
        mode : int
            Integer value to apply to UART_CTRL
        verbose : bool
            If True outputs additional debug info
        """

        self.set_reg(
            self.reg.UART_CTRL.WINID, self.reg.UART_CTRL.ADDR, mode & 0x03, verbose
        )
        self._status["auto_start"] = (mode & 0x02) == 2
        self._status["uart_auto"] = (mode & 0x01) == 1
        if verbose:
            print(f"IMU UART Mode = {mode}")

    def _set_ext_sel(self, enabled=False, verbose=False):
        """Configure EXT pin function

        Parameters
        ----------
        enabled : bool
            Enable External Trigger or not
        verbose : bool
            If True outputs additional debug info
        """

        try:
            _tmp = self.get_reg(
                self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR, verbose
            )
            self.set_reg(
                self.reg.MSC_CTRL.WINID,
                self.reg.MSC_CTRL.ADDR,
                (_tmp & 0x06) | enabled << 6,
                verbose,
            )
            self._status["ext_trigger"] = enabled
            if verbose:
                print(f"EXT_SEL = {enabled}")
        except KeyError as err:
            print("** Invalid EXT_SEL")
            raise InvalidCommandError from err

    def _set_drdy_polarity(self, act_high=True, verbose=False):
        """Configure DRDY polarity to active HIGH

        Parameters
        ----------
        act_high : bool
            True = active HIGH or False = active LOW
        verbose : bool
            If True outputs additional debug info
        """

        _tmp = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.MSC_CTRL.WINID,
            self.reg.MSC_CTRL.ADDR,
            (_tmp & 0xFD) | int(act_high) << 1,
            verbose,
        )
        self._status["drdy_pol"] = act_high
        if verbose:
            print(f"DRDY_POL = {act_high}")

    def _set_tilt(self, mask=0b000, verbose=False):
        """Configure TILT enable bits in SIG_CTRL

        Parameters
        ----------
        mask : int
            3-bit mask to enable TILT in bit order X, Y, Z
        verbose : bool
            If True outputs additional debug info
        """

        _tmp = self.get_reg(self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.SIG_CTRL.WINID,
            self.reg.SIG_CTRL.ADDR,
            (_tmp & 0x1F) | mask << 5,
            verbose,
        )
        self._status["tilt"] = mask
        if verbose:
            print(f"TILT = {mask}")

    def _config_basic(
        self,
        dout_rate=200,
        filter_sel=None,
        ndflags=False,
        tempc=False,
        counter=False,
        chksm=False,
        auto_start=False,
        ext_trigger=False,
        uart_auto=False,
        drdy_pol=True,
        tilt=0,
        verbose=False,
        **cfg,
    ):
        """Configure basic settings based on key, value parameters

        Parameters
        ----------
        "dout_rate": 200,
        "filter_sel": None,
        "ndflags": False,
        "tempc": False,
        "counter": False,
        "chksm": False,
        "auto_start": False,
        "ext_trigger": False,
        "uart_auto": False,
        "drdy_pol": True,
        "tilt": 0,
        "verbose" : bool, If True outputs additional debug info

        Raises
        ----------
        DeviceConfigurationError
            When unsupported configuration provided
        """

        try:
            self._set_ext_sel(ext_trigger, verbose=verbose)
            self._set_drdy_polarity(drdy_pol, verbose=verbose)
            self._set_tilt(tilt, verbose=verbose)
            self._set_output_rate(dout_rate, verbose=verbose)
            self._set_filter(filter_sel, verbose=verbose)

            _wval = int(auto_start) << 1 | int(uart_auto)
            self._set_uart_mode(_wval, verbose=verbose)

            # BURST_CTRL HIGH for cfg
            _wval = (
                int(ndflags) << 7
                | int(tempc) << 6
                | 0 << 5  # reserved
                | 0 << 4  # reserved
                | 0 << 3  # reserved
                | 1 << 2  # acclx always enabled
                | 1 << 1  # accly always enabled
                | 1 << 0  # acclz always enabled
            )
            self.set_reg(
                self.reg.BURST_CTRL.WINID,
                self.reg.BURST_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["ndflags"] = ndflags
            self._status["tempc"] = tempc

            # BURST_CTRL LOW for cfg
            _wval = int(counter) << 1 | int(chksm)
            self.set_reg(
                self.reg.BURST_CTRL.WINID,
                self.reg.BURST_CTRL.ADDR,
                _wval,
                verbose=verbose,
            )
            self._status["counter"] = counter
            self._status["chksm"] = chksm

            print("Configured")
            # If UART_AUTO then ignore setting SIG_CTRL
            if self._status.get("uart_auto") is True:
                return

            # SIG_CTRL for cfg - tempc, Accl
            _wval = int(tempc) << 7 | 7 << 1  # AcclXYZ
            self.set_reg(
                self.reg.SIG_CTRL.WINID,
                self.reg.SIG_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )
        except KeyError as err:
            print("** Failure writing basic configuration to device")
            raise DeviceConfigurationError from err

    def _get_sample(self, inter_delay=0.000001, verbose=False):
        """Return single burst from device
        if malformed find next header and raise InvalidBurstReadError

        Parameters
        ----------
        inter_delay : float
            delay time between checking a complete burst is in the buffer
        verbose : bool
            If True outputs additional debug info

        Returns
        -------
        list of integers of a single burst of data

        Raises
        -------
        InvalidCommandError
            When device is not configured by set_config() or
            When device is not in SAMPLING mode
        InvalidBurstReadError
            When header byte and delimiter byte is missing, find next header byte,
            and re-raise InvalidBurstReadError
        KeyboardInterrupt
            When CTRL-C occurs, re-raise
        """

        # Return if struct is empty, then device is not configured
        if self._b_struct == "":
            print("** Device not configured. Have you run set_config()?")
            raise InvalidCommandError
        # Return if still in CONFIG mode
        if self._status.get("is_config"):
            print("** Device not in SAMPLING mode. Run goto('sampling') first.")
            raise InvalidCommandError
        # Get data structure of the burst
        data_struct = struct.Struct(self._b_struct)
        # If UART_AUTO disabled, send BURST command
        if self._status["uart_auto"] is False:
            self.regif.port_io.set_raw8(self.mdef.BURST_MARKER, 0x00, verbose)

        try:
            while self.regif.port_io.in_waiting() < data_struct.size:
                time.sleep(inter_delay)
            data_str = self.regif.port_io.read_bytes(data_struct.size)

            data_unpacked = data_struct.unpack(data_str)

            if (data_unpacked[0] != self.mdef.BURST_MARKER) or (
                data_unpacked[-1] != self.mdef.DELIMITER
            ):
                print("** Missing Header or Delimiter")
                raise InvalidBurstReadError

            # Strip out the header and delimiter byte
            return data_unpacked[1:-1]
        except InvalidBurstReadError:
            self.regif.port_io.find_delimiter(verbose=verbose)
            raise
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise

    def _proc_sample(self, raw_burst=()):
        """Process parameter as single burst read of device data
        Returns processed data in a tuple or None if empty burst

        Parameters
        ----------
        raw_burst : list
            list of integers of single burst of data
            Typically the output from _get_sample()

        Returns
        -------
        tuple of scale-converted single burst of data

        Raises
        -------
        InvalidBurstReadError
            If raw_burst is Falsey
        KeyboardInterrupt
            When CTRL-C occurs re-raise
        """

        try:
            if not raw_burst:
                raise InvalidBurstReadError

            # Locally held scale factor
            sf_tempc = self.mdef.SF_TEMPC
            sf_accl = self.mdef.SF_ACCL
            sf_tilt = self.mdef.SF_TILT

            # Map conversions for scaled
            map_scl = {
                "ndflags": lambda x: x,
                "tempc": lambda x: round((x * sf_tempc) + 34.987, 4),
                "acclx": lambda x: round(x * sf_accl, 6),
                "accly": lambda x: round(x * sf_accl, 6),
                "acclz": lambda x: round(x * sf_accl, 6),
                "tiltx": lambda x: round(x * sf_tilt, 6),
                "tilty": lambda x: round(x * sf_tilt, 6),
                "tiltz": lambda x: round(x * sf_tilt, 6),
                "counter": lambda x: x,
                "chksm": lambda x: x,
            }

            return tuple(
                map_scl[key.split("_")[0]](bdata)
                for key, bdata in zip(self._burst_fields, raw_burst)
            )
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise
