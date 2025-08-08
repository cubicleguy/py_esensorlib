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

"""Sensor Device class is composed of classes for accelerometer, vibration sensor,
   IMU, UartPort
Contains:
- SensorDevice() class
"""

import importlib
from types import MappingProxyType

from loguru import logger

from esensorlib import uart_port, spi_port, reg_interface, accl_fn, imu_fn, vib_fn


class SensorDevice:
    """
    SensorDevice is the main class composed of UartPort(), RegInterface(),
    and one of AcclFn(), ImuFn(), or VibFn().

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

    Methods
    -------
    get_model_definitions(prod_id)
        Return object containing module imported for device model definitions

    get_sensor_fn(verbose)
        Return AcclFn(), ImuFn(), VibFn() object based on model type

    get_regdump(columns, verbose)
        Read all registers and return the values formatted in N columns

    get_reg(winnum, regaddr, verbose)
        16-bit read from specified register address

    set_reg(winnum, regaddr, write_byte, verbose)
        8-bit write to specified register address

    set_config(**cfg)
        Configure device from key, value parameters

    init_check(verbose)
        Check if HARD_ERR (hardware error) is reported
        Usually performed once after startup

    do_selftest(verbose)
        Perform self-test and check if ST_ERR (self-test error) is reported

    do_softreset(verbose)
        Perform software reset

    test_flash(verbose)
        Perform self-test on flash and return result

    backup_flash(verbose)
        Perform flash backup of registers and return result

    init_backup(verbose)
        Restore flash to factory default and return result

    goto(mode, post_delay, verbose)
        Set device to CONFIG or SAMPLING mode

    get_mode(verbose)
        Return device mode status either CONFIG or SAMPLING

    read_sample(verbose)
        Return scaled burst sample of sensor data

    read_sample_unscaled(verbose)
        Return unscaled burst sample of sensor data
    """

    def __init__(
        self,
        port,
        speed=460800,
        if_type="uart",
        model="auto",
        verbose=False,
        no_init=False,
    ):
        """
        Parameters
        ----------
        port : UartPort() instance
            The name of interface port
        speed : int
            speed of sensor device connected to port
        if_type : str
            Currently only "uart" is supported
        model : str
            Model of sensor device. Set to auto for auto-detect
        verbose : bool
            If True outputs additional debug info
        no_init : bool
            If True object is created without device register access.
            This is intended for devices that are already configured
            and flashed with AUTO_START, and set_config() must be
            specified with all device configuration to read & process
            sensor burst data
        """

        self._port = port
        self._speed = speed
        self._if_type = if_type.lower()
        self._model = model.upper()
        self._verbose = verbose
        self._no_init = no_init
        self._cfg = {}  # place holder - updated in set_config()

        # UartPort() or SpiPort() instance depends on if_type
        # SpiPort is just a stub and not implemented yet
        # when no_init is enabled, detecting device routine is
        # not performed when port to device is opened
        if self._if_type == "uart":
            self.port_io = uart_port.UartPort(
                self._port, self._speed, self._verbose, self._no_init
            )
        elif self._if_type == "spi":
            self.port_io = spi_port.SpiPort(
                self._port, self._speed, self._verbose, self._no_init
            )
        else:
            raise IOError(f"** Unsupported if_type specified {self._if_type}")

        # RegInterface() instance
        self.regif = reg_interface.RegInterface(self.port_io, self._verbose)

        # Create _info dict of UartPort() or SpiPort() instance,
        # if_type, model
        self._info = {
            "port_io": self.port_io,
            "if_type": self._if_type,
            "model": self._model,
            # from UartPort() or SpiPort() info
            "port_io_info": self.port_io.info,
        }
        # For no_init, do not read device registers instead
        # return empty values
        if self._no_init:
            self._device_info = {
                "prod_id": None,
                "version_id": None,
                "serial_id": None,
            }
        else:
            # Read registers to identify Device PROD_ID, VERSION, SER_NUM
            self._device_info = self.regif.get_device_info(self._verbose)

        # Update _info with prod_id, version_id, serial_id from UartPort()
        self._info.update(self._device_info)

        # Import model definitions and constants, autodetect if model="auto"
        # UartPort().info or SpiPort().info must be defined before calling
        # get_model_definitions()
        self._mdef = self.get_model_definitions(self._model)

        # Return sensor object based on prod_id
        # from AcclFn(), ImuFn(), or VibFn() instance
        # UartPort().info or SpiPort().info must be defined before calling
        # get_sensor_fn()
        self.sensor_fn = self.get_sensor_fn(self._verbose)

    def __repr__(self):
        cls = self.__class__.__name__
        string_val = "".join(
            [
                f"{cls}(port='{self._port}', ",
                f"speed={self._speed}, ",
                f"if_type='{self._if_type}', ",
                f"model='{self._model}', ",
                f"verbose={self._verbose}, ",
                f"no_init={self._no_init})",
            ]
        )
        return string_val

    def __str__(self):
        string_val = "".join(
            [
                "\nSensor Device",
                f"\n  Port: {self._port}",
                f"\n  Speed (baud or Hz): {self._speed}",
                f"\n  Interface Type: {self._if_type}",
                f"\n  Model: {self._model}",
                f"\n  Verbose: {self._verbose}",
                f"\n  No_Init: {self._no_init}",
            ]
        )
        return string_val

    @property
    def info(self):
        """property for device info"""
        return MappingProxyType(self._info)

    @property
    def status(self):
        """property for AcclFn(), ImuFn(), or VibFn() status"""
        return self.sensor_fn.status

    @property
    def burst_out(self):
        """property for burst_output of AcclFn(), ImuFn(), or VibFn()"""
        return self.sensor_fn.burst_out

    @property
    def burst_fields(self):
        """property for burst_fields tuple of AcclFn(), ImuFn(), or VibFn()"""
        return self.sensor_fn.burst_fields

    @property
    def mdef(self):
        """property for model definitions"""
        return self._mdef

    def get_model_definitions(self, prod_id):
        """Load user-specified model or load auto-detect model definitions"""
        prod_id = prod_id.upper()
        # If no_init then set product ID for _info and _device_info based on
        # user supplied parameter
        if self._no_init is True:
            self._info["prod_id"] = prod_id
            self._device_info["prod_id"] = prod_id
        elif prod_id == "AUTO":
            detected = self._info.get("prod_id") or "UNKNOWN"
            print(f"Detected: {detected}")
            prod_id = detected
        else:
            if prod_id != self._info.get("prod_id"):
                print(
                    f"Overriding detected {self._info['prod_id']} with user-specified {prod_id}"
                )
            # Override detected product id
            self._info["prod_id"] = prod_id
            self._device_info["prod_id"] = prod_id

        # If G330, or G366 use the same G366 model definitions
        if prod_id.startswith("G330") or prod_id.startswith("G366"):
            prod_id = "G366PDG0"
        # If G320 or G354 just keep the first 4 letters
        elif prod_id.startswith("G320") or prod_id.startswith("G354"):
            prod_id = prod_id[:4]
        # Import the model definitions
        try:
            model_def = importlib.import_module(
                f".model.m{prod_id.lower()}", package="esensorlib"
            )
            return model_def
        except ModuleNotFoundError as exc:
            logger.error(
                f"** Cannot load model definitions. Unknown device model detected: {prod_id}"
            )
            raise IOError from exc

    def get_sensor_fn(self, verbose=False):
        """Return instantiated ImuFn(), AcclFn(), VibFn() based on product_id"""

        _prod_id = self._info.get("prod_id")
        is_imu = _prod_id.startswith("G")
        is_accl = (
            _prod_id.startswith("A352")
            or _prod_id.startswith("A552AR")
            or _prod_id.startswith("A370")
        )
        is_vib = _prod_id.startswith("A342") or _prod_id.startswith("A542VR")

        if is_imu:
            return imu_fn.ImuFn(self.regif, self._mdef, self._device_info, verbose)
        if is_accl:
            return accl_fn.AcclFn(self.regif, self._mdef, self._device_info, verbose)
        if is_vib:
            return vib_fn.VibFn(self.regif, self._mdef, self._device_info, verbose)

        raise IOError(f"Unknown Device {self._info.get('prod_id')}")

    def get_regdump(self, columns=3, verbose=False):
        """Initiate register dump and format into table

        Parameters
        ----------
        columns : int
            Number of columns to layout register read values
        verbose : bool
            If True outputs additional debug info
        """

        print("Reading registers:")
        reg_dmp = [
            (
                reg.ADDR,
                reg.WINID,
                self.get_reg(reg.WINID, reg.ADDR, verbose=verbose),
            )
            for reg in self._mdef.Reg
        ]
        for i, each in enumerate(reg_dmp):
            print(f"REG[0x{each[0]:02X}, (W{each[1]})] => 0x{each[2]:04X}\t", end="")
            if i % columns == columns - 1:
                print()

    def get_reg(self, winnum, regaddr, verbose=False):
        """redirect to RegInterface() instance
        Read 16-bit register from WIN_ID and register address (even only)"""
        return self.regif.get_reg(winnum, regaddr, verbose)

    def set_reg(self, winnum, regaddr, write_byte, verbose=False):
        """redirect to RegInterface() instance
        Write byte to register WIN_ID and register address (odd or even)"""
        self.regif.set_reg(winnum, regaddr, write_byte, verbose)

    def set_config(self, **cfg):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Configure device based on parameters."""
        self._cfg = cfg
        self.sensor_fn.set_config(**self._cfg)

    def init_check(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Check for HARD_ERR (hardware error)"""
        self.sensor_fn.init_check(verbose)

    def do_selftest(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Initiate Self Test"""
        self.sensor_fn.do_selftest(verbose)

    def do_softreset(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Initiate Software Reset"""
        self.sensor_fn.do_softreset(verbose)

    def do_flashtest(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Initiate Flash Test"""
        self.sensor_fn.do_flashtest(verbose)

    def backup_flash(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Initiate Flash Backup"""
        self.sensor_fn.backup_flash(verbose)

    def init_backup(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Initialize flash backup registers to factory defaults"""
        self.sensor_fn.init_backup(verbose)

    def goto(self, mode, post_delay=0.2, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Set MODE_CMD to either CONFIG or SAMPLING mode."""
        self.sensor_fn.goto(mode, post_delay, verbose)

    def get_mode(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Return MODE_STAT bit"""
        return self.sensor_fn.get_mode(verbose)

    def read_sample(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Read one burst of scaled sensor data"""
        return self.sensor_fn.read_sample(verbose)

    def read_sample_unscaled(self, verbose=False):
        """redirect to ImuFn(), AcclFn(), VibFn() instance.
        Read one burst of unscaled sensor data"""
        return self.sensor_fn.read_sample_unscaled(verbose)
