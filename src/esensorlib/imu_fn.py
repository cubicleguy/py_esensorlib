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

"""IMU class for IMU functions
Contains:
- ImuFn() class
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


class ImuFn:
    """
    IMU level functions

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
        16-bit read from specified WIN_ID and register address

    set_reg(winnum, regaddr, write_byte, verbose=False)
        8-bit write to specified WIN_ID and register address

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
            prod_id, version_id, serial_id as key, values pairs
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

        # Default device config status
        self._status = {
            "dout_rate": 200,
            "filter_sel": None,
            "ndflags": False,
            "tempc": False,
            "counter": "",
            "chksm": False,
            "auto_start": False,
            "is_32bit": True,
            "a_range": False,
            "ext_trigger": False,
            "uart_auto": False,
            "is_config": True,
            # delta angle/velocity cfg status
            "dlta": False,
            "dltv": False,
            "dlta_sf_range": 12,
            "dltv_sf_range": 12,
            # attitude cfg status
            "atti": False,
            "atti_mode": "euler",
            "atti_conv": 0,
            "atti_profile": "modea",
            "qtn": False,
        }
        # Stores current burst output status
        self._burst_out = {
            "ndflags": False,
            "tempc": False,
            "gyro": True,
            "accl": True,
            "dlta": False,
            "dltv": False,
            "qtn": False,
            "atti": False,
            "gpio": False,
            "counter": False,
            "chksm": False,
            "tempc32": True,
            "gyro32": True,
            "accl32": True,
            "dlta32": False,
            "dltv32": False,
            "qtn32": False,
            "atti32": False,
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
                "\nIMU Functions",
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
        Configure with supplied key, values,
        Then read burst configuration from BURST_CTRL1, BURST_CTRL2
        and update status dict

        Parameters
        ----------
        "dout_rate": int,
        "filter_sel": str,
        "ndflags": bool,
        "tempc": bool,
        "counter": str,
        "chksm": bool,
        "auto_start": bool,
        "is_32bit": bool,
        "a_range": bool,
        "ext_trigger": bool,
        "uart_auto": bool

        "dlta": bool,
        "dltv": bool,
        "dlta_sf_range": int,
        "dltv_sf_range": int,

        "atti": bool,
        "mode": str, "euler" or "incl"
        "conv": int, 0 to 23
        "profile": "modea", "modeb", "modec"
        "qtn": bool,
        "verbose" : bool, If True outputs additional debug info

        """

        is_dict = isinstance(cfg, dict)
        is_none = cfg is None
        if not (is_dict or is_none):
            raise TypeError(f"** cfg parameters must be **kwargs or None: {cfg}")

        verbose = cfg.get("verbose", False)
        self.goto("config", verbose=verbose)
        self._config_basic(**cfg)
        self._config_dlt(**cfg)
        self._config_atti(**cfg)

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
            print(f"** Invalid BAUD_RATE: {baud}")
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

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info

        Raises
        -------
        SelfTestError
            non-zero results indicates ST_ERR
        """

        self.set_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDRH, 0x04, verbose)
        time.sleep(self.mdef.SELFTEST_DELAY_S)
        result = 0x0400
        while (result & 0x0400) != 0:
            # Wait for SELF_TEST = 0
            result = self.get_reg(self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR)
            if verbose:
                print(".", end="")
        result = self.get_reg(
            self.reg.DIAG_STAT.WINID, self.reg.DIAG_STAT.ADDR, verbose
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
        time.sleep(self.mdef.FLASH_TEST_DELAY_S)
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
        """

        self.set_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR, 0x10, verbose)
        time.sleep(self.mdef.FLASH_BACKUP_DELAY_S)
        result = 0x0010
        while (result & 0x0010) != 0:
            result = self.get_reg(self.reg.GLOB_CMD.WINID, self.reg.GLOB_CMD.ADDR)
            if verbose:
                print(".", end="")
        print("Initial Backup Completed")

    def goto(self, mode, post_delay=0.5, verbose=False):
        """Set MODE_CMD to either CONFIG or SAMPLING mode.
        If entering SAMPLING, store the state of burst configuration
        NOTE: Device must be in SAMPLING mode to call read_sample()
        NOTE: Device must be in CONFIG mode for most functions

        Parameters
        ----------
        mode : str
            "config" or "sampling"
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
            raise TypeError(f"** Mode parameter must be 'config' or 'sampling': {mode}")

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
            # After entering CONFIG mode
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
            0 = Sampling, 1 = Config
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
            & 0x0400
        ) >> 10
        self._status["is_config"] = bool(result)
        if verbose:
            print(f"MODE_CMD = {result}")
        return result

    def read_sample(self, verbose=False):
        """Read one burst of sensor data, post processes,
        and returns scaled sensor data scaled.
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
        """Read BURST_CTRL1 & BURST_CTRL2 to update in
        _b_struct, _burst_out, _burst_fields

        Parameters
        ----------
        verbose : bool
            If True outputs additional debug info
        """

        tmp1 = self.get_reg(
            self.reg.BURST_CTRL1.WINID, self.reg.BURST_CTRL1.ADDR, verbose
        )
        tmp2 = self.get_reg(
            self.reg.BURST_CTRL2.WINID, self.reg.BURST_CTRL2.ADDR, verbose
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
        self._burst_fields = self._get_burst_fields()

        if verbose:
            print(f"_get_burst_struct_fmt(): {self._b_struct}")
            print(f"_get_burst_fields(): {self._burst_fields}")
            print(f"_get_burst_config(): {self._burst_out}")

    def _get_burst_struct_fmt(self):
        """Returns the struct format for burst packet
        based on _burst_out (from BURST_CTRL1 & BURST_CTRL2)

        Returns
        -------
        list
            containing struct format describing burst data
        """

        # Build struct format based on decoded flags
        # of bytes from BURST_CTRL & SIG_CTRL
        # > = Big endian
        # B = unsigned char
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
        # Start with header byte
        struct_list = [">B"]
        for key in self._burst_out:
            # Loop thru _burst_out until it reaches tempc32
            # After temp32 the flags repeat for 32-bit
            if key == "tempc32":
                break
            # If burst field is True, then also check if 32-bit else 16-bit
            if self._burst_out.get(key) is True:
                if self._burst_out.get(f"{key}32"):
                    struct_list.append(_map_struct.get(f"{key}32"))
                else:
                    struct_list.append(_map_struct.get(key))
        # Append delimiter byte
        struct_list.append("B")
        return "".join(struct_list)

    def _get_burst_fields(self):
        """Returns tuple containing enabled burst_fields based on _burst_out

        Returns
        -------
        tuple
            containing strings of burst fields
        """
        burst_fields = []
        for key, value in self._burst_out.items():
            if key == "tempc32":
                break
            if value is True:
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
        """Configure SIG_CTRL based on burst config dict
        NOTE: Not used when UART_AUTO is enabled

        Parameters
        ----------
        burst_cfg : dict
            parses burst flags from dict to enabled in SIG_CTRL
        verbose : bool
            If True outputs additional debug info
        """
        # If UART_AUTO then ignore setting SIG_CTRL and return
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
                self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDRH, _wval, verbose
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
                self.reg.SIG_CTRL.WINID, self.reg.SIG_CTRL.ADDR, _wval, verbose
            )
        except KeyError as err:
            print("** Invalid SIG_CTRL setting")
            raise InvalidCommandError from err

    def _set_output_rate(self, rate, verbose=False):
        """Configure Output Data Rate DOUT_RATE

        Parameters
        ----------
        rate : int
            Supported DOUT_RATE to apply
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
            print("** Invalid DOUT_RATE")
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

        _filter_sel = self.mdef.FILTER_SEL
        # For G370PDF1 & G370PDS0, filter setting is non-standard
        # when DOUT_RATE 2000, 400, or 80sps
        if self.info.get("prod_id").lower() in [
            "g370pdf1",
            "g370pds0",
        ] and self._status["dout_rate"] in [2000, 400, 80]:
            _filter_sel = self.mdef.FILTER_SEL_2K_400_80

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
            print("** Invalid FILTER_SEL")
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

    def _set_ext_sel(self, mode="GPIO", verbose=False):
        """Configure EXT pin function

        Parameters
        ----------
        mode : str
            Set EXT pin to GPIO, or External Trigger TYPEB, or Counter Reset
        verbose : bool
            If True outputs additional debug info
        """

        if self.info.get("prod_id").lower() in ["g570pr20"]:
            print("EXT pin function not supported")
            return

        try:
            mode = mode.upper()
            writebyte = self.mdef.EXT_SEL[mode]
            _tmp = self.get_reg(
                self.reg.MSC_CTRL.WINID, self.reg.MSC_CTRL.ADDR, verbose
            )
            self.set_reg(
                self.reg.MSC_CTRL.WINID,
                self.reg.MSC_CTRL.ADDR,
                (_tmp & 0x06) | writebyte << 6,
                verbose,
            )

            self._status["ext_trigger"] = mode == "TYPEB"

            if verbose:
                print(f"EXT_SEL = {mode}")
        except KeyError as err:
            print(f"** Invalid EXT_SEL, EXT_SEL = {mode}")
            raise InvalidCommandError from err

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
            print(f"DRDY_POL = {act_high}")

    def _set_accl_range(self, a_range=False, verbose=False):
        """Configure A_RANGE settings for models that support it

        Parameters
        ----------
        a_range : bool
            True = accel range 16G or False = accel range 8G
        verbose : bool
            If True outputs additional debug info
        """

        try:
            # Accelerometer A_RANGE_CTRL support only for certain models
            if self.info.get("prod_id").lower() not in [
                "g330pdg0",
                "g330pde0",
                "g366pdg0",
                "g366pde0",
                "g370pdg0",
                "g370pdt0",
            ]:
                print("Setting A_RANGE not support in this device")
                return

            self.set_reg(
                self.reg.DLT_CTRL.WINID,
                self.reg.DLT_CTRL.ADDRH,
                a_range,
                verbose=verbose,
            )
            self._status["a_range"] = a_range
        except KeyError as err:
            print("** Failure writing A_RANGE to device")
            raise DeviceConfigurationError from err

    def _config_basic(
        self,
        dout_rate=200,
        filter_sel=None,
        ndflags=False,
        tempc=False,
        counter="",
        chksm=False,
        auto_start=False,
        is_32bit=True,
        a_range=False,
        ext_trigger=False,
        uart_auto=True,
        verbose=False,
        **cfg,
    ):
        """Configure basic settings based on key, value parameters

        Parameters
        ----------
        "dout_rate": int,
        "filter_sel": str,
        "ndflags": bool,
        "tempc": bool,
        "counter": str,
        "chksm": bool,
        "auto_start": bool,
        "is_32bit": bool,
        "a_range": bool,
        "ext_trigger": bool,
        "uart_auto": bool,
        "verbose": bool,

        Raises
        ----------
        DeviceConfigurationError
            When unsupported configuration provided
        """

        try:
            if ext_trigger is True:
                self._set_ext_sel("typeb", verbose=verbose)
            elif counter == "reset":
                self._set_ext_sel("reset", verbose=verbose)
            elif counter == "sample":
                self._set_ext_sel("gpio", verbose=verbose)
            else:
                self._set_ext_sel("gpio", verbose=verbose)
            self._set_drdy_polarity(True, verbose=verbose)
            self._set_output_rate(dout_rate, verbose=verbose)
            self._set_filter(filter_sel, verbose=verbose)

            _wval = int(auto_start) << 1 | int(uart_auto)
            self._set_uart_mode(_wval, verbose=verbose)

            self._set_accl_range(a_range, verbose=verbose)

            # BURST_CTRL1 HIGH for cfg
            _wval = (
                int(ndflags) << 7
                | int(tempc) << 6
                | 1 << 5  # Gyro always enabled
                | 1 << 4  # Accel always enabled
                | 0 << 3  # DLTA
                | 0 << 2  # DLTV
                | 0 << 1  # QTN
                | 0  # ATTI
            )
            self.set_reg(
                self.reg.BURST_CTRL1.WINID,
                self.reg.BURST_CTRL1.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["ndflags"] = ndflags
            self._status["tempc"] = tempc

            # BURST_CTRL1 LOW for cfg
            _wval = int(bool(counter)) << 1 | int(chksm)
            self.set_reg(
                self.reg.BURST_CTRL1.WINID,
                self.reg.BURST_CTRL1.ADDR,
                _wval,
                verbose=verbose,
            )
            self._status["counter"] = counter
            self._status["chksm"] = chksm

            # BURST_CTRL2 for cfg
            _wval = 0x7F if is_32bit else 0x00
            self.set_reg(
                self.reg.BURST_CTRL2.WINID,
                self.reg.BURST_CTRL2.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["is_32bit"] = is_32bit

            # Disable ATTI mode as default action
            # It will be re-enabled if needed by _config_dlt() or _config_atti()
            try:
                disable = 0x00
                self.set_reg(
                    self.reg.ATTI_CTRL.WINID,
                    self.reg.ATTI_CTRL.ADDRH,
                    disable,
                    verbose=verbose,
                )
            except AttributeError:
                # If ATTI_CTRL does not exist for G320, G354, G364 so bypass
                pass
            print("Configured basic")
            # If UART_AUTO then ignore setting SIG_CTRL
            if uart_auto is True:
                return

            # SIG_CTRL for cfg - tempc, gyro, accl
            _wval = int(tempc) << 7 | 7 << 4 | 7 << 1  # GyroXYZ  # AcclXYZ
            self.set_reg(
                self.reg.SIG_CTRL.WINID,
                self.reg.SIG_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )
        except KeyError as err:
            print("** Failure writing basic configuration to device")
            raise DeviceConfigurationError from err

    def _config_dlt(
        self,
        dlta=False,
        dltv=False,
        dlta_sf_range=12,
        dltv_sf_range=12,
        verbose=False,
        **cfg,
    ):
        """Configure delta angle/velocity settings based on key, value parameters

        Parameters
        ----------
        "dlta": bool,
        "dltv": bool,
        "dlta_sf_range": int,
        "dltv_sf_range": int,
        "verbose" : bool, If True outputs additional debug info

        Raises
        ----------
        DeviceConfigurationError
            When unsupported configuration provided
        """

        if self.info.get("prod_id").lower() in ["g570pr20"]:
            print("Delta angle / velocity function not supported. Bypassing.")
            return

        # Exit if both DLTA and DLTV are disabled
        if dlta is False and dltv is False:
            print("Delta angle / velocity function disabled. Bypassing.")
            return

        try:
            # DLT_CTRL for cfg
            _wval = (dlta_sf_range & 0xF) << 4 | (dltv_sf_range & 0xF)
            self.set_reg(
                self.reg.DLT_CTRL.WINID,
                self.reg.DLT_CTRL.ADDR,
                _wval,
                verbose=verbose,
            )
            self._status["dlta_sf_range"] = dlta_sf_range
            self._status["dltv_sf_range"] = dltv_sf_range

            # BURST_CTRL1 HIGH for cfg
            _tmp = self.get_reg(
                self.reg.BURST_CTRL1.WINID,
                self.reg.BURST_CTRL1.ADDR,
                verbose=verbose,
            )
            _wval = (_tmp >> 8) & 0xF3 | (dlta << 3) | (dltv << 2)
            self.set_reg(
                self.reg.BURST_CTRL1.WINID,
                self.reg.BURST_CTRL1.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["dlta"] = dlta
            self._status["dltv"] = dltv

            # ATTI_CTRL does not exist for these models
            has_atti_ctrl = self.info.get("prod_id").lower() not in [
                "g320pdg0",
                "g320pdgn",
                "g354pdh0",
                "g364pdc0",
                "g364pdca",
            ]
            if has_atti_ctrl is True:
                # ATTI_CTRL for cfg
                _tmp = self.get_reg(
                    self.reg.ATTI_CTRL.WINID, self.reg.ATTI_CTRL.ADDR, verbose=verbose
                )
                _atti_on = 0b01 if any((dlta, dltv)) else 0b00
                _wval = (_tmp >> 8) & 0xF9 | (
                    _atti_on << 1
                )  # ATTI_ON, 0b01 = Delta Angle/Velocity
                self.set_reg(
                    self.reg.ATTI_CTRL.WINID,
                    self.reg.ATTI_CTRL.ADDRH,
                    _wval,
                    verbose=verbose,
                )
            print("Configured delta angle / velocity")
            # If UART_AUTO then ignore setting SIG_CTRL
            if self._status.get("uart_auto") is True:
                return

            # SIG_CTRL for cfg - dlta, dltv
            _wval = 7 << 5 | 7 << 2  # dltaXYZ , dltvXYZ
            self.set_reg(
                self.reg.SIG_CTRL.WINID,
                self.reg.SIG_CTRL.ADDR,
                _wval,
                verbose=verbose,
            )
        except KeyError as err:
            print("** Failure writing delta angle/velocity configuration to device")
            raise DeviceConfigurationError from err

    def _config_atti(
        self,
        atti=False,
        atti_mode="euler",
        atti_conv=0,
        atti_profile="modea",
        qtn=False,
        verbose=False,
        **cfg,
    ):
        """Configure attitude or quaternion settings based on key, value parameters

        Parameters
        ----------
        "atti": bool,
        "atti_mode": str,
        "atti_conv": int,
        "atti_profile": str,
        "qtn": bool,
        "verbose" : bool, If True outputs additional debug info

        Raises
        ----------
        DeviceConfigurationError
            When unsupported configuration provided
        """

        # Exit if model does not support the attitude function
        has_attitude_function = self.info.get("prod_id").lower() in [
            "g330pde0",
            "g330pdg0",
            "g366pde0",
            "g366pdg0",
            "g365pdf1",
            "g365pdc1",
        ]
        if has_attitude_function is False:
            print("Attitude or quaternion not supported. Bypassing.")
            return

        # Exit if both ATTI and QTN are disabled
        if atti is False and qtn is False:
            print("Attitude or quaternion disabled. Bypassing.")
            return

        # Exit if DLT is enabled
        if cfg.get("dlta") or cfg.get("dltv"):
            print("Delta angle / velocity is enabled. Bypassing attitude / quaternion.")
            return

        # Exit if ATTI_CONV not between 0 or 23
        if atti_conv < 0 or atti_conv > 23:
            print("ATTI_CONV must be between 0 and 23. Bypassing.")
            return

        try:
            # BURST_CTRL1 HIGH for cfg
            _tmp = self.get_reg(
                self.reg.BURST_CTRL1.WINID,
                self.reg.BURST_CTRL1.ADDR,
                verbose=verbose,
            )
            _wval = (_tmp >> 8) & 0xFC | qtn << 1 | atti  # QTN_OUT  # ATTI_OUT
            self.set_reg(
                self.reg.BURST_CTRL1.WINID,
                self.reg.BURST_CTRL1.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["qtn"] = qtn
            self._status["atti"] = atti

            # ATTI_CTRL HIGH for cfg
            _tmp = self.get_reg(
                self.reg.ATTI_CTRL.WINID,
                self.reg.ATTI_CTRL.ADDR,
                verbose=verbose,
            )
            _atti_on = 0b10 if any((atti, qtn)) else 0b00
            _wval = (
                (_tmp >> 8) & 0xF1
                | (int(atti_mode == "euler") << 3)  # ATTI_MODE = Euler or Inclination
                | (
                    _atti_on << 1
                )  # ATTI_ON, 0b10 = Attitude or Quaternion, 0b00 = Disabled
            )
            self.set_reg(
                self.reg.ATTI_CTRL.WINID,
                self.reg.ATTI_CTRL.ADDRH,
                _wval,
                verbose=verbose,
            )
            self._status["atti_mode"] = atti_mode

            # ATTI_CTRL LOW
            self.set_reg(
                self.reg.ATTI_CTRL.WINID,
                self.reg.ATTI_CTRL.ADDR,
                atti_conv,
                verbose=verbose,
            )
            self._status["atti_conv"] = atti_conv

            # GLOB_CMD2 for cfg
            _wval = self.mdef.ATTI_MOTION_PROFILE[atti_profile.upper()] << 4

            # ATTITUDE_MOTION_PROFILE
            self.set_reg(
                self.reg.GLOB_CMD2.WINID,
                self.reg.GLOB_CMD2.ADDR,
                _wval,
                verbose=verbose,
            )
            time.sleep(self.mdef.ATTI_MOTION_SETTING_DELAY_S)
            self._status["atti_profile"] = atti_profile
            print("Configured attitude / quaternion")
        except KeyError as err:
            print("** Failure writing attitude or quaternion configuration to device")
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
            return data_unpacked[1:-1]
        except InvalidBurstReadError:
            self.regif.port_io.find_delimiter(verbose=verbose)
            raise
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise

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
            If raw_burst is ()
        KeyboardInterrupt
            When CTRL-C occurs and re-raise
        """

        try:
            if not raw_burst:
                raise InvalidBurstReadError

            # Locally held scale factor
            sf_tempc = self.mdef.SF_TEMPC
            tempc_25c = self.mdef.TEMPC_25C
            sf_gyro = self.mdef.SF_GYRO
            sf_accl = (
                self.mdef.SF_ACCL
                if not self._status.get("a_range")
                else self.mdef.SF_ACCL * 2
            )

            sf_dlta = 0
            sf_dltv = 0
            dlt_supported = self.info.get("prod_id").lower() not in ["g570pr20"]
            if dlt_supported:
                if self._status.get("dlta_sf_range") is not None:
                    sf_dlta = self.mdef.SF_DLTA * 2 ** self._status.get("dlta_sf_range")
                _sf_dltv = (
                    self.mdef.SF_DLTV
                    if not self._status.get("a_range")
                    else self.mdef.SF_DLTV * 2
                )
                if self._status.get("dltv_sf_range") is not None:
                    sf_dltv = _sf_dltv * 2 ** self._status.get("dltv_sf_range")

            sf_qtn = 1 / 2**14

            # Set ATTI_SF to 0 for unsupported models
            atti_supported = self.info["prod_id"].lower() in [
                "g330pdg0",
                "g366pdg0",
                "g365pdf1",
                "g365pdc1",
            ]
            sf_atti = 0
            if atti_supported:
                sf_atti = self.mdef.SF_ATTI

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
                # Pass field_data into lambda function in map_scl dict
                map_scl[field_name.split("_")[0]](field_data)
                for field_name, field_data in zip(self._burst_fields, raw_burst)
            )
        except KeyboardInterrupt:
            print("CTRL-C: Exiting")
            raise
