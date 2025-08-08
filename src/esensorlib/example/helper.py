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

"""Utility helper class to format and send sensor data
to either stdout or CSV file
Contains:
- LoggerHelper() class
"""

import csv
import datetime
import sys
import time

from tabulate import SEPARATING_LINE, tabulate


class LoggerHelper:
    """
    A class for formatting and outputting sensor data
    This should be instantiated passing in a "configured" SensorDevice() object

    ...

    Attributes
    ----------
    dev_info : dict
        SensorDevice() info
    dev_status : dict
        SensorDevice() status
    dev_mdef : dict
        SensorDevice() mdef (model definitions)
    dev_burst_out : dict
        SensorDevice() burst_out
    dev_burst_fields : tuple
        SensorDevice() burst_fields

    Methods
    -------
    set_writer(to=None)
        If to=None, write() method sends to stdout.
        If to=list of strings, write() method sends to CSV file with
        filename generated joining list of strings

    write(sample_data)
        Write list or tuple of numbers (representing sensor data) to writer

    write_header(scale_mode=True, start_date=None)
        Write rows of header info to writer and
        increment internal sample counter

    write_footer(end_date=None)
        Write rows of footer info to writer

    get_dev_status()
        Write device status in table format

    clear_count()
        Clear the internal sample counter to zero
    """

    def __init__(self, sensor):
        """Class initializer

        Parameters
        ----------
        sensor : class
            SensorDevice() object
        """

        # File handle for log data
        self._csv_file = None
        # Writer object defaults to stdout
        self._csv_writer = csv.writer(sys.stdout)
        # Sensor object
        self._sensor = sensor
        # SensorDevice() properties
        self.dev_info = sensor.info
        self.dev_status = sensor.status
        self.dev_mdef = sensor.mdef
        self.dev_burst_out = sensor.burst_out
        self.dev_burst_fields = sensor.burst_fields
        # Store sample count when logging
        self._sample_count = 0

    def __repr__(self):
        cls = self.__class__.__name__
        return f"{cls}(sensor={repr(self._sensor)})"

    def __str__(self):
        return "".join(["\nLogger Helper", f"\n  Sensor: {repr(self._sensor)}"])

    def __del__(self):
        self._close()

    def set_writer(self, to=None):
        """Sets the writer to stdout if to=None or
           csv_writer object if to=list of strings

        Parameters
        ----------
        to : list
            list of strings to concatenate to a filename

        Returns
        -------
        None
        """
        try:
            if to is not None:
                self._close()
                to.insert(1, self.dev_info.get("prod_id"))
                to.insert(
                    2,
                    str(
                        self.dev_status.get("dout_rate")
                        or str(self.dev_status.get("dout_rate_rmspp"))
                    ),
                )
                if self.dev_status.get("filter_sel"):
                    to.insert(3, str(self.dev_status.get("filter_sel", "NA")))
                fname = "_".join(to)
                fname = fname + ".csv"
                self._csv_file = open(fname, "a", newline="", encoding="utf-8")
                self._csv_writer = csv.writer(self._csv_file, dialect="excel")
            else:
                self._close()
                self._csv_file = None
                self._csv_writer = csv.writer(sys.stdout)  # Defaults to stdout
        except KeyboardInterrupt:
            pass

    def write(self, sample_data=None):
        """Appends sample count to sample_data, formats,
        sends to writer object. If sample_data is None
        burst data is corrupted, and write error msg instead

        Parameters
        ----------
        sample_data : list or tuple
            iterable of numbers (expected to be return values from read_sample() method)

        Returns
        -------
        None
        """

        try:
            row_data = [self._sample_count]
            if sample_data:
                row_data.extend(sample_data)
                # Send burst data to writer handle
                self._csv_writer.writerow(row_data)
            else:
                self._csv_writer.writerow(
                    [
                        "### Corrupted burst read detected. Attempting to find next header. ###"
                    ]
                )
            self._sample_count = self._sample_count + 1
        except KeyboardInterrupt:
            pass

    def write_header(self, scale_mode=True, start_date=None):
        """Writes the header rows to the writer object

        Parameters
        ----------
        scale_mode : bool
            Some minor differences in header between scale_mode is True or False
        start_date : datetime object
            datetime of current time, if None then grab current datetime
        Returns
        -------
        None
        """

        if not start_date:
            start_date = datetime.datetime.now()
        try:
            if self.dev_status.get("output_sel") is None:
                _output_sel_name = ""
                _output_sel_val = ""
            else:
                _output_sel_name = "Output Sel"
                _output_sel_val = self.dev_status.get("output_sel")

            # Create Header Rows (max rows is 17 columns)
            header1 = [
                "#Log esensorlib",
                "",
                "",
            ]
            # Output Rate Status
            if self.dev_status.get("dout_rate"):
                header1.extend(["Output Rate", f"{self.dev_status.get('dout_rate')}"])
            elif self.dev_status.get("dout_rate_rmspp"):
                header1.extend(
                    ["DOUT_RATE_RMSPP", f"{self.dev_status.get('dout_rate_rmspp')}"]
                )
            # Filter or Update Rate Status
            if self.dev_status.get("filter_sel"):
                header1.extend(
                    ["Filter Setting", f"{self.dev_status.get('filter_sel')}"]
                )
            elif self.dev_status.get("update_rate_rmspp") is not None:
                header1.extend(
                    ["UPDATE_RATE_RMSPP", f"{self.dev_status.get('update_rate_rmspp')}"]
                )
            header1.extend([_output_sel_name, _output_sel_val, ""])

            header2 = [
                "#Creation Date:",
                str(start_date),
                f"PROD_ID={self.dev_info.get('prod_id')}",
                f"VERSION={self.dev_info.get('version_id')}",
                f"SERIAL_NUM={self.dev_info.get('serial_id')}",
                "",
                "",
                "",
                "",
                "",
            ]
            # Generate map of burst field type to metric units
            map_sf_units = {
                "gyro": "(deg/s)/bit",
                "accl": "mg/bit",
                "tempc": "degC/bit",
                "qtn": "/bit",
                "atti": "deg/bit",
                "dlta": "deg/bit",
                "dltv": "(m/s)/bit",
                "tilt": "rad/bit",
                "vel": "(mm/s)/bit",
                "disp": "(mm)/bit",
            }
            header3 = ["#Scaled Data"] if scale_mode else ["#Raw Data"]
            _row_data = []
            for field in self.dev_burst_fields:
                if "tempc" in field:
                    if "tempc32" in field:
                        _ = f"SF_TEMPC={self.dev_mdef.SF_TEMPC:+01.8f}/2^16"
                    elif "tempc8" in field:
                        _ = f"SF_TEMPC={self.dev_mdef.SF_TEMPC:+01.8f}*2^8"
                    else:  # 16-bit
                        _ = f"SF_TEMPC={self.dev_mdef.SF_TEMPC:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("tempc"))))
                if "gyro" in field:
                    if "gyro32" in field:
                        _ = f"SF_GYRO={self.dev_mdef.SF_GYRO:+01.8f}/2^16"
                    else:
                        _ = f"SF_GYRO={self.dev_mdef.SF_GYRO:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("gyro"))))
                if "accl" in field:
                    _sf_accl = (
                        self.dev_mdef.SF_ACCL
                        if not self.dev_status.get("a_range")
                        else self.dev_mdef.SF_ACCL * 2
                    )
                    if "accl32" in field:
                        _ = f"SF_ACCL={_sf_accl:+01.8f}/2^16"
                    else:  # 16-bit
                        _ = f"SF_ACCL={_sf_accl:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("accl"))))
                if "dlta" in field:
                    if "dlta32" in field:
                        _ = f"SF_DLTA={self.dev_mdef.SF_DLTA * 2**self.dev_status.get('dlta_sf_range'):+01.8f}/2^16"
                    else:  # 16-bit
                        _ = f"SF_DLTA={self.dev_mdef.SF_DLTA * 2**self.dev_status.get('dlta_sf_range'):+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("dlta"))))
                if "dltv" in field:
                    _sf_dltv = (
                        self.dev_mdef.SF_DLTV
                        if not self.dev_status.get("a_range")
                        else self.dev_mdef.SF_DLTV * 2
                    )
                    if "dltv32" in field:
                        _ = f"SF_DLTV={_sf_dltv * 2**self.dev_status.get('dltv_sf_range'):+01.8f}/2^16"
                    else:  # 16-bit
                        _ = f"SF_DLTV={_sf_dltv * 2**self.dev_status.get('dltv_sf_range'):+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("dltv"))))
                if "atti" in field:
                    if "atti32" in field:
                        _ = f"SF_ATTI={self.dev_mdef.SF_ATTI:+01.8f}/2^16"
                    else:  # 16-bit
                        _ = f"SF_ATTI={self.dev_mdef.SF_ATTI:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("atti"))))
                if "qtn" in field:
                    if "qtn32" in field:
                        _ = f"SF_QTN={self.dev_mdef.SF_QTN:+01.8f}/2^16"
                    else:  # 16-bit
                        _ = f"SF_QTN={self.dev_mdef.SF_QTN:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("qtn"))))
                if "tilt" in field:
                    _ = f"SF_TILT={self.dev_mdef.SF_TILT}"
                    _row_data.append(" ".join((_, map_sf_units.get("tilt"))))
                if "vel" in field:
                    _ = f"SF_VEL={self.dev_mdef.SF_VEL:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("vel"))))
                if "disp" in field:
                    _ = f"SF_DISP={self.dev_mdef.SF_DISP:+01.8f}"
                    _row_data.append(" ".join((_, map_sf_units.get("disp"))))
            header3.extend(sorted(set(_row_data)))

            # Generate map of burst field to column value for scaled units
            map_cols_scaled = {
                "ndflags": "Flags[dec]",
                "exi-alrm-cnt": "E-A-C[dec]",
                "gpio": "GPIO[dec]",
                "counter": "Counter[dec]",
                "chksm": "Chksm16[dec]",
            }
            map_cols_scaled.update(
                dict.fromkeys(["tempc", "tempc8", "tempc32"], "Ts[degC]")
            )
            map_cols_scaled.update(dict.fromkeys(["gyro_X", "gyro32_X"], "Gx[dps]"))
            map_cols_scaled.update(dict.fromkeys(["gyro_Y", "gyro32_Y"], "Gy[dps]"))
            map_cols_scaled.update(dict.fromkeys(["gyro_Z", "gyro32_Z"], "Gz[dps]"))
            map_cols_scaled.update(
                dict.fromkeys(["accl_X", "accl32_X", "acclx"], "Ax[mG]")
            )
            map_cols_scaled.update(
                dict.fromkeys(["accl_Y", "accl32_Y", "accly"], "Ay[mG]")
            )
            map_cols_scaled.update(
                dict.fromkeys(["accl_Z", "accl32_Z", "acclz"], "Az[mG]")
            )
            map_cols_scaled.update(dict.fromkeys(["dlta_X", "dlta32_X"], "DAx[deg]"))
            map_cols_scaled.update(dict.fromkeys(["dlta_Y", "dlta32_Y"], "DAy[deg]"))
            map_cols_scaled.update(dict.fromkeys(["dlta_Z", "dlta32_Z"], "DAz[deg]"))
            map_cols_scaled.update(dict.fromkeys(["dltv_X", "dltv32_X"], "DVx[m/s]"))
            map_cols_scaled.update(dict.fromkeys(["dltv_Y", "dltv32_Y"], "DVy[m/s]"))
            map_cols_scaled.update(dict.fromkeys(["dltv_Z", "dltv32_Z"], "DVz[m/s]"))
            map_cols_scaled.update(dict.fromkeys(["atti_X", "atti32_X"], "ANG1[deg]"))
            map_cols_scaled.update(dict.fromkeys(["atti_Y", "atti32_Y"], "ANG2[deg]"))
            map_cols_scaled.update(dict.fromkeys(["atti_Z", "atti32_Z"], "ANG3[deg]"))
            map_cols_scaled.update(dict.fromkeys(["qtn_0", "qtn32_0"], "q0"))
            map_cols_scaled.update(dict.fromkeys(["qtn_1", "qtn32_1"], "q1"))
            map_cols_scaled.update(dict.fromkeys(["qtn_2", "qtn32_2"], "q2"))
            map_cols_scaled.update(dict.fromkeys(["qtn_3", "qtn32_3"], "q3"))
            map_cols_scaled.update(dict.fromkeys(["tiltx"], "Tx[rad]"))
            map_cols_scaled.update(dict.fromkeys(["tilty"], "Ty[rad]"))
            map_cols_scaled.update(dict.fromkeys(["tiltz"], "Tz[rad]"))
            map_cols_scaled.update(dict.fromkeys(["velx"], "Vx[mm/s]"))
            map_cols_scaled.update(dict.fromkeys(["vely"], "Vy[mm/s]"))
            map_cols_scaled.update(dict.fromkeys(["velz"], "Vz[mm/s]"))
            map_cols_scaled.update(dict.fromkeys(["dispx"], "Dx[mm]"))
            map_cols_scaled.update(dict.fromkeys(["dispy"], "Dy[mm]"))
            map_cols_scaled.update(dict.fromkeys(["dispz"], "Dz[mm]"))

            # Generate map of burst field to column value for unscaled units
            map_cols_unscaled = {
                "ndflags": "Flags[dec]",
                "exi-alrm-cnt": "E-A-C[dec]",
                "gpio": "GPIO[dec]",
                "counter": "Counter[dec]",
                "chksm": "Chksm16[dec]",
            }
            map_cols_unscaled.update(
                dict.fromkeys(["tempc", "tempc8", "tempc32"], "Ts[dec]")
            )
            map_cols_unscaled.update(dict.fromkeys(["gyro_X", "gyro32_X"], "Gx[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["gyro_Y", "gyro32_Y"], "Gy[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["gyro_Z", "gyro32_Z"], "Gz[dec]"))
            map_cols_unscaled.update(
                dict.fromkeys(["accl_X", "accl32_X", "acclx"], "Ax[dec]")
            )
            map_cols_unscaled.update(
                dict.fromkeys(["accl_Y", "accl32_Y", "accly"], "Ay[dec]")
            )
            map_cols_unscaled.update(
                dict.fromkeys(["accl_Z", "accl32_Z", "acclz"], "Az[dec]")
            )
            map_cols_unscaled.update(dict.fromkeys(["dlta_X", "dlta32_X"], "DAx[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dlta_Y", "dlta32_Y"], "DAy[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dlta_Z", "dlta32_Z"], "DAz[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dltv_X", "dltv32_X"], "DVx[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dltv_Y", "dltv32_Y"], "DVy[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dltv_Z", "dltv32_Z"], "DVz[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["atti_X", "atti32_X"], "ANG1[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["atti_Y", "atti32_Y"], "ANG2[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["atti_Z", "atti32_Z"], "ANG3[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["qtn_0", "qtn32_0"], "q0[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["qtn_1", "qtn32_1"], "q1[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["qtn_2", "qtn32_2"], "q2[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["qtn_3", "qtn32_3"], "q3[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["tiltx"], "Tx[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["tilty"], "Ty[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["tiltz"], "Tz[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["velx"], "Vx[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["vely"], "Vy[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["velz"], "Vz[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dispx"], "Dx[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dispy"], "Dy[dec]"))
            map_cols_unscaled.update(dict.fromkeys(["dispz"], "Dz[dec]"))

            header4 = ["Sample No."]
            if scale_mode:
                # Scaled Mode
                for key in self.dev_burst_fields:
                    header4.append(map_cols_scaled.get(key))
            else:
                # Raw Digital Mode
                for key in self.dev_burst_fields:
                    header4.append(map_cols_unscaled.get(key))
            self._csv_writer.writerows([header1, header2, header3, header4])
        except KeyboardInterrupt:
            pass

    def write_footer(self, end_date=None):
        """Writes the footer rows to the writer object

        Parameters
        ----------
        end_date : datetime object
            datetime of current time, if None then grab current datetime
        Returns
        -------
        None
        """

        if not end_date:
            end_date = datetime.datetime.now()
        try:
            footer1 = ["#Log End", str(end_date), "", "", "", "", "", "", "", ""]
            footer2 = [
                "#Sample Count",
                f"{self._sample_count:09d}",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]

            _dout_rate = self.dev_status.get("dout_rate") or self.dev_status.get(
                "dout_rate_rmspp"
            )
            if self.dev_status.get("output_sel") is None:
                _output_sel_name = ""
                _output_sel_val = ""
            else:
                _output_sel_name = "Output Sel"
                _output_sel_val = self.dev_status.get("output_sel")
            footer3 = [
                "#Output Rate",
                f"{_dout_rate}",
                "",
                "Filter Setting",
                f"{self.dev_status.get('filter_sel', 'NA')}",
                "",
                _output_sel_name,
                _output_sel_val,
                "",
                "",
            ]
            self._csv_writer.writerows([footer1, footer2, footer3])
        except KeyboardInterrupt:
            pass

    def get_dev_status(self):
        """Writes table of device status info to the writer object"""

        _date = time.strftime("%Y-%m-%d")
        _time = time.strftime("%H:%M:%S")

        table = []
        table.append([f"Date: {_date}", f"Time: {_time}"])
        table.append(SEPARATING_LINE)

        table.append(
            [
                f'PROD_ID: {self.dev_info.get("prod_id")}',
                f'VERSION: {self.dev_info.get("version_id")}',
                f'SERIAL: {self.dev_info.get("serial_id")}',
            ]
        )

        _row1 = []
        if self.dev_status.get("dout_rate"):
            _row1.append(f'DOUT_RATE: {self.dev_status.get("dout_rate")}')
        if self.dev_status.get("dout_rate_rmspp"):
            _row1.append(f'DOUT_RATE_RMSPPP: {self.dev_status.get("dout_rate_rmspp")}')
        if self.dev_status.get("filter_sel"):
            _row1.append(f'FILTER: {self.dev_status.get("filter_sel").upper()}')
        if self.dev_status.get("update_rate_rmspp") is not None:
            _row1.append(f'UPDATE_RATE: {self.dev_status.get("update_rate_rmspp")}')
        table.append(_row1)

        table.append(
            [
                f'NDFLAG: {self.dev_burst_out.get("ndflags")}',
                f'TEMPC: {self.dev_burst_out.get("tempc")}',
                f'COUNTER: {self.dev_burst_out.get("counter")}',
                f'CHKSM: {self.dev_burst_out.get("chksm")}',
            ]
        )

        _row2 = []
        if (
            self.dev_burst_out.get("dlta") is not None
            or self.dev_burst_out.get("dltv") is not None
        ):
            _row2.append(
                f'DLT: {self.dev_burst_out.get("dlta") or self.dev_burst_out.get("dltv")}'
            )
        if self.dev_burst_out.get("atti") is not None:
            _row2.append(f'ATTI: {self.dev_burst_out.get("atti")}')
        if self.dev_burst_out.get("qtn") is not None:
            _row2.append(f'QTN: {self.dev_burst_out.get("qtn")}')
        table.append(_row2)
        print(tabulate(table))

    def clear_count(self):
        """Clears the sample counter"""

        self._sample_count = 0

    def _close(self):
        """Closes file if open"""

        try:
            if self._csv_file:
                if not self._csv_file.closed:
                    self._csv_file.close()
        except AttributeError:
            pass
