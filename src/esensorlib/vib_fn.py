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

"""Vibration sensor class for vibration sensor functions
Contains:
- VibFn() class
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


class VibFn:
    """
    VIB functions

    ...

    Attributes
    ----------
    info : MappingProxyType
        dict of device ID and port information
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
        16-bit read from specified WIN_ID and register address

    set_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write to specified WIN_ID and register address

    set_config(**cfg)
        Configure device from key, value parameters

    init_check(verbose=False)
        Check if HARD_ERR (hardware error) is reported
        Usually performed once after startup

    do_selftest(verbose=False)
        Perform self-test and check if ST_ERR (self-test error) is reported

    do_softreset(verbose=False)
        Perform software reset

    test_flash(verbose=False)
        Perform self-test on flash and return result

    backup_flash(verbose=False)
        Perform flash backup of registers and return result

    init_backup(verbose=False)
        Restore flash to factory default and return result

    dump_reg(columns, verbose=False)
        Read all registers and return the values formatted in N columns

    set_baudrate(baud, verbose=False)
        Configure device baudrate setting NOTE: This takes immediate effect.

    goto(mode, post_delay, verbose=False)
        Set device to CONFIG or SAMPLING mode

    get_mode(verbose=False)
        Return device mode status either CONFIG or SAMPLING

    read_sample()
        Return scaled burst sample of sensor data

    read_sample_unscaled()
        Return unscaled burst sample of sensor data
    """

    def __init__(self, obj_regif, obj_mdef, device_info=None, verbose=False):
        """
        Parameters
        ----------
        obj_regif : RegInterface() instance passed from SensorDevice() instance
            Register interface object
        obj_mdef : module
            Model definitions passed from SensorDevice() instance
        device_info : dict
            prod_id, version_id, serial_id values
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

        # Stores device config status
        self._status = {
            "output_sel": "VELOCITY_RMS",
            "dout_rate_rmspp": 1,
            "update_rate_rmspp": 4,
            "ndflags": False,
            "tempc": False,
            "sensx": True,
            "sensy": True,
            "sensz": True,
            "counter": False,
            "chksm": False,
            "is_tempc16": True,
            "auto_start": False,
            "uart_auto": False,
            "ext_pol": False,
            "is_config": True,
        }
        # Stores current burst output status
        self._burst_out = {
            "ndflags": False,
            "tempc": False,
            "sensx": True,
            "sensy": True,
            "sensz": True,
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
                f"device_info=({self._device_info}), ",
                f"verbose={self._verbose})",
            ]
        )
        return string_val

    def __str__(self):
        string_val = "".join(
            [
                "\nVibration Sensor Functions",
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
        """property from SensorDevice() instance Reg"""
        return self.model_def.Reg

    def get_reg(self, winnum, regaddr, verbose=False):
        """redirect to RegInterface() instance"""
        return self.regif.get_reg(winnum, regaddr, verbose)

    def set_reg(self, winnum, regaddr, write_byte, verbose=False):
        """redirect to RegInterface() instance"""
        self.regif.set_reg(winnum, regaddr, write_byte, verbose)

    def set_config(self, **cfg):
        """Configure device based on keyword, value parameters.
        Configure with supplied key, values
        Then read burst configuration from BURST_CTRL
        and update status dict

        Parameters
        ----------
        "output_sel": str,
        "dout_rate_rmspp": int,
        "update_rate_rmspp": int,
        "ndflags": bool,
        "tempc": bool,
        "sensx": bool,
        "sensy": bool,
        "sensz": bool,
        "counter": bool,
        "chksm": bool,
        "is_tempc16": bool,
        "auto_start": bool,
        "uart_auto": bool,
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
            self.reg.DIAG_STAT1.WINID, self.reg.DIAG_STAT1.ADDR, verbose
        )
        if verbose:
            print("VIB Startup Check")
        result = result & 0x00E0
        if result:
            raise HardwareError("** Hardware Failure. HARD_ERR bits")

    def do_selftest(self, verbose=False):
        """Initiate Self Test
           EXI_TEST, FLASH_TEST, ACC_TEST, TEMP_TEST, VDD_TEST

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        SelfTestError
            non-zero results indicates DIAG_STAT error
        """

        print("EXI_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x80, verbose)
        time.sleep(self.mdef.SELFTEST_RESONANCE_DELAY_S)
        result = 0x8000
        while (result & 0x8000) != 0:
            # Wait for EXI_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        print("FLASH_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x08, verbose)
        time.sleep(self.mdef.SELFTEST_FLASH_DELAY_S)
        result = 0x0800
        while (result & 0x0800) != 0:
            # Wait for FLASH_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        print("ACC_TEST, TEMP_TEST, VDD_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x07, verbose)
        time.sleep(self.mdef.SELFTEST_DELAY_S)
        result = 0x0700
        while (result & 0x0700) != 0:
            # Wait for ACC_TEST, TEMP_TEST, VDD_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        result_diag1 = self.get_reg(
            self.reg.DIAG_STAT1.WINID, self.reg.DIAG_STAT1.ADDR, verbose
        )
        result_diag2 = self.get_reg(
            self.reg.DIAG_STAT2.WINID, self.reg.DIAG_STAT2.ADDR, verbose
        )

        if result_diag1 or result_diag2:
            raise SelfTestError(
                f"** Self Test Failure. DIAG_STAT1={result_diag1: 04X}, DIAG_STAT2={result_diag2: 04X}"
            )
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

        print("FLASH_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x08, verbose)
        time.sleep(self.mdef.SELFTEST_FLASH_DELAY_S)
        result = 0x0800
        while (result & 0x0800) != 0:
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")

        result = self.get_reg(
            self.reg.DIAG_STAT1.WINID, self.reg.DIAG_STAT1.ADDR, verbose
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
            self.reg.DIAG_STAT1.WINID, self.reg.DIAG_STAT1.ADDR, verbose
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
            self.reg.DIAG_STAT1.WINID, self.reg.DIAG_STAT1.ADDR, verbose
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
        NOTE: Device must be in CONFIG mode for most functions

        Parameters
        ----------
        mode : str
            "config" or "sampling" or "sleep"
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
            # BURST_CTRL1 & BURST_CTRL2 register settings
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
        """Return MODE_STAT bits

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
            # Intermediary conversion step for sensXYZ data (byte + short) --> signed int
            raw_burst = self._convert_sens(self._get_sample(verbose=verbose))

            # If 8-bit temperature, conversion step
            tempc_enabled = self._burst_out.get("tempc")
            tempc_16bit = self._status.get("is_tempc16")
            if tempc_enabled and not tempc_16bit:
                raw_burst = self._convert_temp8(raw_burst)

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
        tuple or ()
            tuple containing single set of sensor burst data with or
            without scale factor applied
            None if burst data is malformed or device not in SAMPLING

        Raises
        -------
        KeyboardInterrupt
            Raises to caller CTRL-C
        IOError
            Raises to caller any type of serial port error
        """

        try:
            # Intermediary conversion step for sensXYZ data (byte + short) --> signed int
            raw_burst = self._convert_sens(self._get_sample(verbose=verbose))

            # If 8-bit temperature, conversion step
            tempc_enabled = self._burst_out.get("tempc")
            tempc_16bit = self._status.get("is_tempc16")
            if tempc_enabled and not tempc_16bit:
                raw_burst = self._convert_temp8(raw_burst)

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
        self._burst_out["sensx"] = bool(tmp1 & 0x0400)
        self._burst_out["sensy"] = bool(tmp1 & 0x0200)
        self._burst_out["sensz"] = bool(tmp1 & 0x0100)
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
        # > = Big endian, B = unsigned char, b = signed char
        # i = int (4 byte), I = unsigned int (4 byte)
        # h = short (2byte), H = unsigned short (2 byte)

        _map_struct = {
            "ndflags": "H",
            "tempc": "H",
            "sensx": "BH",
            "sensy": "BH",
            "sensz": "BH",
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
        """Returns enabled burst_fields based on _burst_out

        Returns
        -------
        tuple
            containing strings of burst fields
        """

        burst_fields = [key for key, value in self._burst_out.items() if value is True]

        # Modify for DISP, VELOCITY
        if self._status.get("output_sel").startswith("VELOCITY"):
            burst_fields = [x.replace("sens", "vel") for x in burst_fields]
        else:
            burst_fields = [x.replace("sens", "disp") for x in burst_fields]

        # If 8-bit temperature, conversion step to split "tempc" -> "tempc8" + "exi-alrm-cnt"
        tempc_enabled = self._burst_out.get("tempc")
        tempc_16bit = self._status.get("is_tempc16")
        if tempc_enabled and not tempc_16bit:
            burst_fields = [x.replace("tempc", "tempc8") for x in burst_fields]
            tempc8_index = burst_fields.index("tempc8")
            burst_fields.insert(tempc8_index + 1, "exi-alrm-cnt")

        return tuple(burst_fields)

    def _set_ndflags(self, burst_cfg, verbose=False):
        """Configure SIG_CTRL
        NOTE: Not used when UART_AUTO is enabled

        Parameters
        ----------
        burst_cfg : dict
            parses burst flags from dict to enabled in SIG_CTRL
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
                | int(burst_cfg["sensx"]) << 3
                | int(burst_cfg["sensy"]) << 2
                | int(burst_cfg["sensz"]) << 1
            )
            self.set_reg(
                self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDRH, _wval, verbose
            )

        except KeyError as err:
            print("** Invalid SIG_CTRL setting")
            raise InvalidCommandError from err

    def _set_output_sel(self, mode=None, verbose=False):
        """Configure Output Selection function in SIG_CTRL LOW

        Parameters
        ----------
        mode : str
            VELOCITY_RAW, VELOCITY_RMS, VELOCITY_PP,
            DISP_RAW, DISP_RMS, DISP_PP,
        verbose : bool
            If True outputs additional debug info
        Raises
        -------
        InvalidCommandError
            When unsupported rate is specified
        """

        try:
            mode = mode.upper()
            _output_sel = self.mdef.OUTPUT_SEL.get(mode, "DISP_RMS")
            _tmp = self.get_reg(
                self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, verbose
            )
            self.set_reg(
                self.reg.SIG_CTRL.WINID,
                self.reg.SIG_CTRL.ADDR,
                (_tmp & 0x0F) | _output_sel << 4,
                verbose,
            )
            time.sleep(self.mdef.OUTPUT_MODE_SETTING_DELAY_S)
            result = 0x0001
            while (result & 0x0001) != 0:
                result = self.get_reg(self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR)
            result = self.get_reg(
                self.reg.DIAG_STAT1.WINID, self.reg.DIAG_STAT1.ADDR, verbose
            )
            result = result & 0x00E0
            if result:
                raise HardwareError("** Output Select Failure. HARD_ERR bits")
            self._status["output_sel"] = mode
            if verbose:
                print(f"OUTPUT_SEL = {mode}")
        except KeyError as err:
            print(f"** Invalid OUTPUT_SEL, Output sel = {mode}")
            raise InvalidCommandError from err

    def _set_output_rate(self, dout_rate, verbose=False):
        """Configure Output Data Rate for DOUT_RATE_RMSPP
        Only valid for RMS or Peak-to-Peak
        If RAW mode, this is ignored

        Parameters
        ----------
        dout_rate : int
            DOUT_RATE_RMSPP setting
        verbose : bool
            If True outputs additional debug info
        """

        if self._status.get("output_sel") in ("VELOCITY_RAW", "DISP_RAW"):
            print("RAW mode output detected. Bypass setting DOUT_RATE_RMSPP")
            return

        if dout_rate < 1 or dout_rate > 255:
            print(
                "DOUT_RATE_RMSPP must be 1 ~ 255 (inclusive). Bypass setting DOUT_RATE_RMSPP"
            )
            return

        self.set_reg(
            self.reg.SMPL_CTRL.WINID,
            self.reg.SMPL_CTRL.ADDRH,
            dout_rate,
            verbose,
        )
        self._status["dout_rate_rmspp"] = dout_rate
        if verbose:
            print(f"Set Output Rate = {dout_rate}")

    def _set_update_rate(self, update_rate, verbose=False):
        """Configure Update Rate for UPDATE_RATE_RMSPP
        Only valid for RMS or Peak-to-Peak
        If RAW mode, this is ignored

        Parameters
        ----------
        update_rate : int
            UPDATE_RATE_RMSPP setting
        verbose : bool
            If True outputs additional debug info
        """

        if self._status.get("output_sel") in ("VELOCITY_RAW", "DISP_RAW"):
            print("RAW mode output detected. Bypass setting UPDATE_RATE_RMSPP")
            return

        if update_rate < 0 or update_rate > 15:
            print(
                "UPDATE_RATE_RMSPP must be 0 ~ 15 (inclusive). Bypass setting UPDATE_RATE_RMSPP"
            )
            return

        self.set_reg(
            self.reg.SMPL_CTRL.WINID,
            self.reg.SMPL_CTRL.ADDR,
            update_rate,
            verbose,
        )
        self._status["update_rate_rmspp"] = update_rate
        if verbose:
            print(f"Set Update Rate = {update_rate}")

    def _set_uart_mode(self, mode, verbose=False):
        """Configure AUTO_START and UART_AUTO bits in UART_CTRL

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

    def _set_ext_pol(self, act_low=False, verbose=False):
        """Configure EXT pin active low

        Parameters
        ----------
        act_low : bool
            Set EXT pin polarity active LOW (True), or active HIGH (False)
        verbose : bool
            If True outputs additional debug info
        """

        _tmp = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.MSC_CTRL.WINID,
            self.reg.MSC_CTRL.ADDR,
            (_tmp & 0xDF) | int(act_low) << 5,
            verbose,
        )
        self._status["ext_pol"] = act_low
        if verbose:
            print(f"EXT_POL Active LOW = {act_low}")

    def _set_drdy_polarity(self, act_high=True, verbose=False):
        """Configure DRDY to active HIGH

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
            print(f"DRDY_POL Active HIGH = {act_high}")

    def _set_tempc_format(self, bit16=True, verbose=False):
        """Configure temperature 16bit or 8bit

        Parameters
        ----------
        bit16 : bool
            True = tempc is 16-bit, False = tempc is 8-bit, lower 8-bit is 2-bit counter
        verbose : bool
            If True outputs additional debug info
        """

        _tmp = self.get_reg(self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.SIG_CTRL.WINID,
            self.reg.SIG_CTRL.ADDR,
            (_tmp & 0xFD) | int(bit16) << 1,
            verbose,
        )
        self._status["is_tempc16"] = bit16
        if verbose:
            print(f"TEMP_SEL 16bit = {bit16}")

    def _config_basic(
        self,
        output_sel="velocity_rms",
        dout_rate_rmspp=1,
        update_rate_rmspp=4,
        ndflags=False,
        tempc=False,
        sensx=True,
        sensy=True,
        sensz=True,
        counter=False,
        chksm=False,
        is_tempc16=True,
        auto_start=False,
        uart_auto=True,
        ext_pol=False,
        verbose=False,
        **cfg,
    ):
        """Configure basic settings based on key, value parameters

        Parameters
        ----------
        "output_sel": str,
        "dout_rate_rmspp": int,
        "update_rate_rmspp": int,
        "ndflags": bool,
        "tempc": bool,
        "sensx": bool,
        "sensy": bool,
        "sensz": bool,
        "counter": bool,
        "chksm": bool,
        "is_tempc16": bool,
        "auto_start": bool,
        "uart_auto": bool,
        "ext_pol": bool,
        "verbose" : bool, If True outputs additional debug info

        Raises
        ----------
        DeviceConfigurationError
            When unsupported configuration provided
        """

        try:
            self._set_ext_pol(ext_pol, verbose=verbose)
            self._set_drdy_polarity(True, verbose=verbose)
            if tempc:
                self._set_tempc_format(is_tempc16, verbose=verbose)
            self._set_output_sel(output_sel, verbose=verbose)
            self._set_output_rate(dout_rate_rmspp, verbose=verbose)
            self._set_update_rate(update_rate_rmspp, verbose=verbose)

            _wval = int(auto_start) << 1 | int(uart_auto)
            self._set_uart_mode(_wval, verbose=verbose)

            # BURST_CTRL for cfg
            _wval = (
                int(ndflags) << 7
                | int(tempc) << 6
                | 0 << 5  # reserved
                | 0 << 4  # reserved
                | 0 << 3  # reserved
                | int(sensx) << 2
                | int(sensy) << 1
                | int(sensz) << 0
            )
            self.set_reg(
                self.reg.BURST_CTRL.WINID,
                self.reg.BURST_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["ndflags"] = ndflags
            self._status["tempc"] = tempc
            self._status["sensx"] = sensx
            self._status["sensy"] = sensy
            self._status["sensz"] = sensz

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
            if self._status.get("uart_auto", False):
                return

            # SIG_CTRL for cfg - tempc, Accl
            _wval = (
                int(tempc) << 7 | int(sensx) << 3 | int(sensy) << 2 | int(sensz) << 1
            )
            self.set_reg(
                self.reg.SIG_CTRL.WINID,
                self.reg.SIG_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )

        except (KeyError, HardwareError) as err:
            print("** Failure writing basic configuration to device")
            raise DeviceConfigurationError from err

    def _get_sample(self, inter_delay=0.000001, verbose=False):
        """Return single burst from device data
        if malformed find next header byte and raise InvalidBurstReadError

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
            When CTRL-C occurs and re-raise
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
        if not self._status["uart_auto"]:
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
            # data_unpacked = data_unpacked[1:-1]
            return data_unpacked[1:-1]
        except InvalidBurstReadError:
            self.regif.port_io.find_delimiter(verbose=verbose)
            raise
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise

    def _convert_sens(self, burst_in=()):
        """Return modified burst data for sensXYZ data
        to convert upper 1-byte + lower 2-byte to 32-bit signed int
        or () if empty burst

        Parameters
        ----------
        burst_in : iterable
            sensor burst data with sensXYZ fields in separated 8bit and 16bit

        Returns
        -------
        Tuple of integers of a single burst of data with sensXYZ field merged into 32-bit integer
        """

        # Return if burst_in is empty
        if not burst_in:
            return ()

        # Create internal burst fields list from self._burst_out
        # burst_in has 8-bit + 16bit for each sens measurement which is not consistent
        # with current self._burst_fields
        burst_fields = [key for key, value in self._burst_out.items() if value is True]

        # Create new burst list for sensXYZ data byte+short -> int
        i = 0
        converted_burst = []
        for field in burst_fields:
            if field.startswith("sens"):
                # thunk data into unsigned int
                data = (burst_in[i] << 24) | (burst_in[i + 1] << 8)
                packed = struct.pack(">I", data)
                # convert to signed int and right shift back
                unpacked = struct.unpack(">i", packed)[0] >> 8
                converted_burst.append(unpacked)
                i = i + 2
            else:
                converted_burst.append(burst_in[i])
                i = i + 1
        return tuple(converted_burst)

    def _convert_temp8(self, burst_in=()):
        """Return modified burst data to split 16-bit temperature data
        to 1-byte temperature + 1-byte EXI, ALRM, 2BIT_COUNT
        or () if empty burst

        Parameters
        ----------
        burst_in : iterable
            sensor burst data with tempc as 16-bit fields

        Returns
        -------
        Tuple of integers of a single burst of data with tempc split to tempc8 and EXI-ALRM-CNT
        """

        # Return if burst is empty
        if not burst_in:
            return ()

        # Create internal burst fields list from self._burst_out
        # burst_in has 8-bit + 16bit for each sens measurement which is not consistent
        # with current self._burst_fields
        burst_fields = [key for key, value in self._burst_out.items() if value is True]

        # When temperature output enabled in 8-bit mode, split to 2 bytes
        converted_burst = []
        for field, burst_data in zip(burst_fields, burst_in):
            if field.startswith("tempc"):
                # upper byte 8-bit temperature
                # lower byte 8-bit EXI, ALRM, 2BIT_COUNTER
                tempc8, exi_alrm_cnt = struct.unpack(
                    ">bB", burst_data.to_bytes(2, "big")
                )
                converted_burst.append(tempc8)
                converted_burst.append(exi_alrm_cnt)
            else:
                converted_burst.append(burst_data)
        return tuple(converted_burst)

    def _proc_sample(self, raw_burst=()):
        """Process parameter as single burst read of device data
        Returns processed data in a tuple or () if empty burst

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
            If raw_burst is None
        KeyboardInterrupt
            When CTRL-C occurs and re-raise
        """

        try:
            if not raw_burst:
                raise InvalidBurstReadError

            # Get current burst fields setting
            burst_fields = self._burst_fields

            # Locally held scale factor
            sf_tempc = self.mdef.SF_TEMPC
            sf_vel = self.mdef.SF_VEL
            sf_disp = self.mdef.SF_DISP

            # Map conversions for scaled
            map_scl = {
                "ndflags": lambda x: x,
                "tempc": lambda x: round((x * sf_tempc) + 34.987, 4),
                "tempc8": lambda x: round((x * sf_tempc * 256) + 34.987, 4),
                "velx": lambda x: round(x * sf_vel, 8),
                "vely": lambda x: round(x * sf_vel, 8),
                "velz": lambda x: round(x * sf_vel, 8),
                "dispx": lambda x: round(x * sf_disp, 8),
                "dispy": lambda x: round(x * sf_disp, 8),
                "dispz": lambda x: round(x * sf_disp, 8),
                "counter": lambda x: x,
                "chksm": lambda x: x,
                "exi-alrm-cnt": lambda x: x,
            }

            return tuple(
                map_scl[key.split("_")[0]](bdata)
                for key, bdata in zip(burst_fields, raw_burst)
            )
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise
