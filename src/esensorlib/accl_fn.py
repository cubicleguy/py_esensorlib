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

"""Accelerometer class for accelerometer functions
Contains:
- AcclFn() class
- Descriptive Exceptions specific to this package
"""

import struct
import time
from types import MappingProxyType

from loguru import logger


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
    get_reg(winnum, regaddr, verbose)
        16-bit read from specified WIN_ID and register address

    set_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write to specified WIN_ID and register address

    set_config(**cfg)
        Configure device from key, value parameters

    set_baudrate(baud, verbose)
        Configure device baudrate setting NOTE: This takes immediate effect.

    init_check(verbose)
        Check if HARD_ERR (hardware error) is reported
        Usually performed once after startup

    do_selftest(verbose)
        Perform self-test and check if ST_ERR (self-test error) is reported

    do_softreset(verbose)
        Perform software reset

    do_flashtest(verbose)
        Perform self-test on flash and return result

    backup_flash(verbose)
        Perform flash backup of registers and return result

    init_backup(verbose)
        Restore flash to factory default and return result

    goto(mode, post_delay, verbose)
        Set device to CONFIG or SAMPLING mode

    get_mode(verbose)
        Return device mode status as either CONFIG or SAMPLING

    read_sample(verbose)
        Return scaled burst sample of sensor data

    read_sample_unscaled(verbose)
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

        # _cfg is updated when set_config(**cfg) called
        self._cfg = {}

        # Default device config status
        self._status = {
            "dout_rate": 200,
            "filter_sel": None,
            "ndflags": False,
            "tempc": False,
            "counter": False,
            "chksm": False,
            "auto_start": False,
            "ext_trigger": "DISABLED",
            "uart_auto": False,
            "drdy_pol": True,
            "tilt": 0,
            "reduced_noise": False,
            "temp_stabil": True,
            "is_config": True,
        }
        # Stores current burst output status
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
        cfg : dict of keyword arguments
            Optional keyword arguments
        """

        if not cfg:
            logger.warning("** No cfg parameters provided using defaults")

        self._cfg = cfg

        verbose = self._cfg.get("verbose", False)
        if verbose:
            logger.debug(f"set_config({cfg})")

        # Place device in CONFIG mode, if not already
        self.goto("config", verbose=verbose)
        self._config_basic(verbose)
        self._get_burst_config(verbose)
        if verbose:
            logger.debug(f"accl_fn.status: {self.status}")

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

        if verbose:
            logger.debug(f"Set Baud Rate = {baud}")

        try:
            writebyte = self.mdef.BAUD_RATE[baud]
            self.set_reg(
                self.reg.UART_CTRL.WINID,
                self.reg.UART_CTRL.ADDRH,
                writebyte,
                verbose,
            )
        except KeyError as err:
            logger.error(f"** Invalid BAUD_RATE: {baud}")
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
        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
        )
        if verbose:
            logger.debug("ACCL Startup Check")
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

        print("XSENS_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x10, verbose)
        time.sleep(self.mdef.SELFTEST_SENSAXIS_DELAY_S)
        result = 0x0100
        while (result & 0x0100) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)

        print("YSENS_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x20, verbose)
        time.sleep(self.mdef.SELFTEST_SENSAXIS_DELAY_S)
        result = 0x0200
        while (result & 0x0200) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)

        print("ZSENS_TEST")
        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x40, verbose)
        time.sleep(self.mdef.SELFTEST_SENSAXIS_DELAY_S)
        result = 0x0400
        while (result & 0x0400) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)

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
        if not self.mdef.HAS_FEATURE.get("INITIAL_BACKUP"):
            logger.warning("Initial backup function not supported. Bypassing...")
            return

        self.set_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR, 0x04, verbose)
        time.sleep(self.mdef.FLASH_BACKUP_DELAY_S)
        result = 0x0010
        while (result & 0x0010) != 0:
            result = self.get_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR)

        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
        )
        result = result & 0x0001
        if result:
            raise FlashBackupError("** Initial Backup Failure. FLASH_BU_ERR bit")
        print("Initial Backup Completed")

    def goto(self, mode="config", post_delay=0.2, verbose=False):
        """Set MODE_CMD to either CONFIG or SAMPLING or SLEEP mode.

        NOTE: SLEEP mode cannot be exited without EXT signal or HW reset
        If entering SAMPLING, store the state of burst configuration
        update _status
        if no_init, avoid register accesses
        NOTE: Device must be in SAMPLING mode to call read_sample()
        NOTE: Device must be in CONFIG mode for most configuration functions

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
        self._status["is_config"] = mode == "CONFIG"

        if verbose:
            logger.debug(f"MODE_CMD = {mode}")

        if self._cfg.get("no_init", False):
            logger.warning(
                "--no_init option specified, bypass setting in MODE_CTRL register"
            )
            return

        try:
            # When entering SAMPLING mode, get burst read configuration
            if mode == "SAMPLING":
                self._get_burst_config(verbose)

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

        except KeyError as err:
            logger.error("** Invalid MODE_CMD")
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
            logger.debug(f"MODE_CMD = {result}")
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
            tuple containing single set of sensor burst data with
            scale factor applied or () if burst data is malformed
            or device not in SAMPLING

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
            logger.error("** Failure reading sensor sample")
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
            tuple containing single set of sensor burst data
            without scale factor applied or () if burst data
            is malformed or device not in SAMPLING

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
            logger.error("** Failure reading sensor sample")
            raise

    def _get_burst_config(self, verbose=False):
        """Typically read from BURST_CTRL.
        For no_init, read from self._cfg to update
        _burst_out, _b_struct, _burst_fields

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info
        """

        no_init = self._cfg.get("no_init", False)

        if not no_init:
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
        else:
            logger.warning(
                "--no_init option assumes device is already configured "
                "with user-specified settings and AUTO_START "
                "enabled."
            )
            self._burst_out["ndflags"] = self._cfg.get("ndflags", False)
            self._burst_out["tempc"] = self._cfg.get("tempc", False)
            self._burst_out["acclx"] = True
            self._burst_out["accly"] = True
            self._burst_out["acclz"] = True
            self._burst_out["counter"] = bool(self._cfg.get("counter", ""))
            self._burst_out["chksm"] = self._cfg.get("chksm", False)

        self._b_struct = self._get_burst_struct_fmt()
        self._burst_fields = self._get_burst_fields()

        if verbose:
            logger.debug(f"burst_out: {self._burst_out}")
            logger.debug(f"burst_struct_fmt: {self._b_struct}")
            logger.debug(f"burst_fields: {self._burst_fields}")

    def _get_burst_struct_fmt(self):
        """Returns the struct format for burst packet
        based on _burst_out

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

    def _set_output_rate(self, output_rate=200, verbose=False):
        """Configure DOUT_RATE and update _status, and
        if no_init then do not write to registers

        Parameters
        ----------
        output_rate : int
            Specify DOUT_RATE setting in sps
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        InvalidCommandError
            When unsupported output_rate is specified
        """

        self._status["dout_rate"] = output_rate

        if verbose:
            logger.debug(f"Set Output Rate = {output_rate}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting DOUT_RATE register")
            return

        try:
            writebyte = self.mdef.DOUT_RATE[output_rate]
            self.set_reg(
                self.reg.SMPL_CTRL.WINID,
                self.reg.SMPL_CTRL.ADDRH,
                writebyte,
                verbose,
            )
        except KeyError as err:
            logger.error(f"** Invalid DOUT_RATE, Set Output Rate = {output_rate}")
            raise InvalidCommandError from err

    def _set_filter(self, filter_type=None, verbose=False):
        """Configure FILTER_SEL and update _status, and
        if no_init then do not write to registers

        Parameters
        ----------
        filter_type : str
            Specify FILTER_SEL type setting
            If None, then auto select based on DOUT_RATE
        verbose : bool
            If True outputs additional debug info
        Raises
        -------
        InvalidCommandError
            When unsupported filter_type is specified
        """

        if self._status.get("dout_rate") is None:
            logger.warning(
                "Set Output Rate before setting the filter. " "Filter setting ignored"
            )
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
            print(f"Filter not specified, setting to {filter_type}")

        _filter_sel = self.mdef.FILTER_SEL

        filter_type = filter_type.upper()

        self._status["filter_sel"] = filter_type

        if verbose:
            logger.debug(f"Filter Type = {filter_type}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting FILTER_SEL register")
            return

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
        except KeyError as err:
            logger.error(f"** Invalid FILTER_SEL, Filter Type = {filter_type}")
            raise InvalidCommandError from err

    def _set_uart_mode(self, mode=0x02, verbose=False):
        """Configure AUTO_START and UART_AUTO bits in UART_CTRL register,
           update _status, and if no_init do not write to registers

        Parameters
        ----------
        mode : int
            Integer value to apply to UART_CTRL
        verbose : bool
            If True outputs additional debug info
        """

        self._status["auto_start"] = (mode & 0x02) == 2
        self._status["uart_auto"] = (mode & 0x01) == 1

        if verbose:
            logger.debug(f"_set_uart_mode({mode})")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting UART_CTRL register")
            return

        self.set_reg(
            self.reg.UART_CTRL.WINID, self.reg.UART_CTRL.ADDR, mode & 0x03, verbose
        )

    def _set_ext_sel(self, mode="DISABLED", verbose=False):
        """Configure EXT pin function

        Parameters
        ----------
        mode : str
            "DISABLED", "EXT_TRIG", "TRIG_POS_EDGE", "TRIG_NEG_EDGE",
            "1PPS_POS" or "1PPS_POS"
        verbose : bool
            If True outputs additional debug info
        """

        if not self.mdef.HAS_FEATURE.get("EXT_PIN"):
            if verbose:
                logger.warning("EXT pin function not supported...")
            return
        mode = mode.upper()
        self._status["ext_trigger"] = mode

        if verbose:
            logger.debug(f"EXT_SEL/EXT_POL = {mode}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting EXT function in MSC_CTRL register")
            return

        _ext_sel = self.mdef.EXT_SEL
        try:
            mode_val = _ext_sel[mode]
            _tmp = self.get_reg(
                self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR, verbose
            )
            self.set_reg(
                self.reg.MSC_CTRL.WINID,
                self.reg.MSC_CTRL.ADDR,
                (_tmp & 0x06) | mode_val << 5,
                verbose,
            )
        except KeyError as err:
            logger.error(f"** Invalid EXT_SEL/EXT_POL = {mode}")
            raise InvalidCommandError from err

    def _set_drdy_polarity(self, act_high=True, verbose=False):
        """Configure DRDY to active HIGH in MSC_CTRL
           update _status, and if no_init do not write to registers

        Parameters
        ----------
        act_high : bool
            True = active HIGH or False = active LOW
        verbose : bool
            If True outputs additional debug info
        """

        self._status["drdy_pol"] = act_high

        if verbose:
            logger.debug(f"DRDY_POL = {act_high}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting DRDY_POL in MSC_CTRL register")
            return

        _tmp = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.MSC_CTRL.WINID,
            self.reg.MSC_CTRL.ADDR,
            (_tmp & 0xFD) | int(act_high) << 1,
            verbose,
        )

    def _set_tilt(self, mask=0b000, verbose=False):
        """Configure TILT enable bits in SIG_CTRL

        Parameters
        ----------
        mask : int
            3-bit mask to enable TILT in bit order X, Y, Z
        verbose : bool
            If True outputs additional debug info
        """
        self._status["tilt"] = mask

        if verbose:
            logger.debug(f"TILT = {mask}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting OUTPUT_SEL_x in SIG_CTRL register")
            return

        _tmp = self.get_reg(self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.SIG_CTRL.WINID,
            self.reg.SIG_CTRL.ADDR,
            (_tmp & 0x1F) | mask << 5,
            verbose,
        )

    def _set_mesmod(self, mode=False, verbose=False):
        """Configure MESMOD_SEL bit in SIG_CTRL

        Parameters
        ----------
        enable : bool
            If True enables reduced noise floor condition
        verbose : bool
            If True outputs additional debug info
        """

        if not self.mdef.HAS_FEATURE.get("REDUCED_NOISE"):
            if verbose:
                logger.warning(
                    "Reduced noise floor function not supported. Bypassing..."
                )
            return

        self._status["reduced_noise"] = mode

        if verbose:
            logger.debug(f"MESMOD_SEL = {mode}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting MESMOD_SEL in SIG_CTRL register")
            return

        _tmp = self.get_reg(self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.SIG_CTRL.WINID,
            self.reg.SIG_CTRL.ADDR,
            (_tmp & 0xEF) | int(mode) << 4,
            verbose,
        )

    def _set_temp_stabil(self, mode=True, verbose=False):
        """Configure TEMP_STABIL bit in SIG_CTRL

        Parameters
        ----------
        enable : bool
            If True enables bias shock stabilization against temperature
        verbose : bool
            If True outputs additional debug info
        """

        if not self.mdef.HAS_FEATURE.get("TEMP_STABIL"):
            if verbose:
                logger.warning(
                    "Bias stabilization against thermal shock function "
                    "not supported. Bypassing..."
                )
            return

        self._status["temp_stabil"] = mode

        if verbose:
            logger.debug(f"TEMP_STABIL = {mode}")

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting TEMP_STABIL in SIG_CTRL register")
            return

        _tmp = self.get_reg(self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, verbose)
        self.set_reg(
            self.reg.SIG_CTRL.WINID,
            self.reg.SIG_CTRL.ADDR,
            (_tmp & 0xFB) | int(mode) << 2,
            verbose,
        )

    def _config_basic(self, verbose=False):
        """Configure basic device settings based on self._cfg dict

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Raises
        ----------
        DeviceConfigurationError
            When unsupported configuration provided
        """

        if verbose:
            logger.debug(f"_config_basic:\nself._cfg:({self._cfg})")

        try:
            # MSC_CTRL - EXT_SEL & DRDY
            ext_trigger = self._cfg.get("ext_trigger", "DISABLED")
            self._set_ext_sel(ext_trigger, verbose)
            drdy_pol = self._cfg.get("drdy_pol", True)
            self._set_drdy_polarity(drdy_pol, verbose)
            # SIG_CTRL - TILT, MESMOD_SEL & TEMP_STABIL
            tilt = self._cfg.get("tilt", 0)
            self._set_tilt(tilt, verbose)

            mesmod_sel = self._cfg.get("reduced_noise", False)
            self._set_mesmod(mesmod_sel, verbose)

            temp_stabil = self._cfg.get("temp_stabil", True)
            self._set_temp_stabil(temp_stabil, verbose)
            # DOUT_RATE
            dout_rate = self._cfg.get("dout_rate", 200)
            self._set_output_rate(dout_rate, verbose)
            # FILTER_SEL
            filter_sel = self._cfg.get("filter_sel", None)
            self._set_filter(filter_sel, verbose)
            # UART_CTRL
            auto_start = self._cfg.get("auto_start", False)
            uart_auto = self._cfg.get("uart_auto", False)
            mode = int(auto_start) << 1 | int(uart_auto)
            self._set_uart_mode(mode, verbose)

            # BURST_CTRL
            self._config_burst_ctrl(verbose)

            print("Configured")

            # If UART_AUTO then ignore setting SIG_CTRL
            if uart_auto is True:
                return

            # SIG_CTRL - tempc, accl
            _wval = int(self._cfg.get("tempc", False)) << 7 | 7 << 1  # AcclXYZ
            self.set_reg(
                self.reg.SIG_CTRL.WINID,
                self.reg.SIG_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )
        except KeyError as err:
            logger.error("** Failure writing basic configuration to device")
            raise DeviceConfigurationError from err

    def _get_sample(self, inter_delay=0.000001, verbose=False):
        """Return single burst from device if burst is malformed
        then find next header byte and raise InvalidBurstReadError

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
            logger.error("** Device not configured. Have you run set_config()?")
            raise InvalidCommandError
        # Return if still in CONFIG mode
        if self._status.get("is_config"):
            logger.error("** Device not in SAMPLING mode. Run goto('sampling') first.")
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
                logger.warning("** Missing Header or Delimiter")
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
        """Process as single burst read of device data
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
            If raw_burst is False
        KeyboardInterrupt
            When CTRL-C occurs re-raise
        """

        try:
            if not raw_burst:
                raise InvalidBurstReadError

            # Locally held scale factor
            sf_tempc = self.mdef.SF_TEMPC
            tempc_offset = self.mdef.TEMPC_OFFSET
            sf_accl = self.mdef.SF_ACCL
            sf_tilt = self.mdef.SF_TILT

            # Map conversions for scaled
            map_scl = {
                "ndflags": lambda x: x,
                "tempc": lambda x: round((x * sf_tempc) + tempc_offset, 4),
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

    def _config_burst_ctrl(self, verbose=False):
        """Configure BURST_CTRL

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info
        """

        ndflags = self._cfg.get("ndflags", False)
        tempc = self._cfg.get("tempc", False)
        counter = self._cfg.get("counter", "")
        chksm = self._cfg.get("chksm", False)
        verbose = self._cfg.get("verbose", False)

        self._status["ndflags"] = ndflags
        self._status["tempc"] = tempc
        self._status["counter"] = counter
        self._status["chksm"] = chksm

        if self._cfg.get("no_init", False):
            logger.warning("--no_init bypass setting BURST_CTRL register")
            return

        # BURST_CTRL HIGH
        _wval = (
            int(ndflags) << 7
            | int(tempc) << 6
            | 0 << 5  # reserved
            | 0 << 4  # reserved
            | 0 << 3  # reserved
            | 1 << 2  # ACCX
            | 1 << 1  # ACCY
            | 1  # ACCZ
        )
        self.set_reg(
            self.reg.BURST_CTRL.WINID,
            self.reg.BURST_CTRL.ADDRH,
            _wval,
            verbose=verbose,
        )
        # BURST_CTRL LOW
        _wval = int(bool(counter)) << 1 | int(chksm)
        self.set_reg(
            self.reg.BURST_CTRL.WINID,
            self.reg.BURST_CTRL.ADDR,
            _wval,
            verbose=verbose,
        )
