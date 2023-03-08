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

"""Utility helper class to format and send sensor data
   to either stdout or CSV file
   Contains:
   - SensorHelper() class
   """

import time
import datetime
import csv
import sys

from tabulate import tabulate, SEPARATING_LINE


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

    Methods
    -------
    set_writer(to=None)
        if to=None, write() method sends to stdout.
        if to=list of strings, write() method sends to CSV file with
        filename generated from list of strings

    write(sample_data)
        Write list or tuple of numbers to writer

    write_header(scale_mode=True, start_date=None)
        Write a row of header info to writer and
        increment sample counter

    write_trailer(end_date=None)
        Write a row of header info to to writer

    print_dev_status()
        Write device status in table format

    clear_count()
        Clear the internal sample counter to zero
    """

    def __init__(self, sensor):
        """Class initialization

        Parameters
        ----------
        sensor : class
            SensorDevice()
        verbose : bool
            If True outputs debug info
        """

        # File handle for log data
        self._csv_file = None
        # Write object defaults to stdout
        self._csv_writer = csv.writer(sys.stdout)
        # SensorDevice() name
        self.device = str(sensor)
        # SensorDevice() properties
        self.dev_info = sensor.info
        self.dev_status = sensor.status
        self.dev_dlt_status = sensor.dlt_status
        self.dev_atti_status = sensor.atti_status
        self.dev_mdef = sensor.mdef
        self.dev_burst_out = sensor.burst_out
        # Store sample count when logging
        self._sample_count = 0

    def __repr__(self):
        cls = self.__class__.__name__
        return f"{cls}(device={self.device})"

    def __del__(self):
        self._close()

    def set_writer(self, to=None):
        """Sets the writer to stdout if to=None or
           csv_writer object if to= list of strings

        Parameters
        ----------
        to : list
            list of strings to concatenate to filename

        Returns
        -------
        None
        """
        try:
            if to is not None:
                to.insert(1, self.dev_info.get("prod_id", "Unknown"))
                to.insert(2, str(self.dev_status.get("dout_rate", "Unknown")))
                to.insert(3, str(self.dev_status.get("filter", "Unknown")))
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
        except IOError:
            print("** IO error creating writer")
            raise

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
            raise
        except IOError:
            print("** Failure writing sensor sample")
            raise

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
            print(f"Start Log: {str(start_date)}")

            # Create Header Rows
            header1 = [
                "#Log created in Python",
                "",
                "",
                "Sample Rate",
                f"{self.dev_status['dout_rate']}",
                "Filter Cfg",
                f"{self.dev_status['filter']}",
                "",
                "",
                "",
            ]
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
                "",
            ]
            _sf_qtn = 1 / 2**14
            _sf_dlta = self.dev_mdef.SF_DLTA * 2 ** (
                12
                if self.dev_dlt_status.get("dlta_sf_range") is None
                else self.dev_dlt_status.get("dlta_sf_range")
            )
            _sf_dltv = self.dev_mdef.SF_DLTV * 2 ** (
                12
                if self.dev_dlt_status.get("dltv_sf_range") is None
                else self.dev_dlt_status.get("dltv_sf_range")
            )
            # if attitude is not supported set _atti_sf to 0
            _supported = self.dev_info["prod_id"].lower() in [
                "g330pde0",
                "g330pdg0",
                "g366pde0",
                "g366pdg0",
                "g365pdf1",
                "g365pdc1",
            ]
            _sf_atti = self.dev_mdef.SF_ATTI if _supported else 0

            map_units = {
                "gyro": "(deg/s)/bit",
                "accl": "mg/bit",
                "tempc": "degC/bit",
                "qtn": "/bit",
                "atti": "deg/bit",
                "dlta": "deg/bit",
                "dltv": "(m/s)/bit",
            }
            map_sf = {
                "gyro": f"SF_GYRO={self.dev_mdef.SF_GYRO:+01.8f}",
                "accl": f"SF_ACCL={self.dev_mdef.SF_ACCL:+01.8f}",
                "tempc": f"SF_TEMPC={self.dev_mdef.SF_TEMPC:+01.8f}",
                "qtn": f"SF_QTN={_sf_qtn:+01.8f}",
                "atti": f"SF_ATTI={_sf_atti:+01.8f}",
                "dlta": f"SF_DLTA={_sf_dlta:+01.8f}",
                "dltv": f"SF_DLTV={_sf_dltv:+01.8f}",
            }
            header3 = ["#Scaled Data"] if scale_mode else ["#Raw Data"]
            for key in map_sf:
                if self.dev_burst_out.get(key):
                    _row_data = [map_sf.get(key)]
                    if self.dev_burst_out.get(f"{key}32"):
                        _row_data.append("/ 2^16")
                    _row_data.append(map_units.get(key))
                    header3.extend([" ".join(_row_data)])

            map_cols_sf = {
                "ndflags": ["Flags[hex]"],
                "tempc": ["Ts[deg.C]"],
                "gyro": ["Gx[dps]", "Gy[dps]", "Gz[dps]"],
                "accl": ["Ax[mG]", "Ay[mG]", "Az[mG]"],
                "dlta": ["DAx[deg]", "DAy[deg]", "DAz[deg]"],
                "dltv": ["DVx[m/s]", "DVy[m/s]", "DVz[m/s]"],
                "qtn": ["q0", "q1", "q2", "q3"],
                "atti": ["ANG1[deg]", "ANG2[deg]", "ANG3[deg]"],
                "gpio": ["GPIO[dec]"],
                "counter": ["Counter[dec]"],
                "chksm": ["Chksm16[dec]"],
            }
            map_cols = {
                "ndflags": ["Flags[dec]"],
                "tempc": ["Ts[dec]"],
                "gyro": ["Gx[dec]", "Gy[dec]", "Gz[dec]"],
                "accl": ["Ax[dec]", "Ay[dec]", "Az[dec]"],
                "dlta": ["DAx[dec]", "DAy[dec]", "DAz[dec]"],
                "dltv": ["DVx[dec]", "DVy[dec]", "DVz[dec]"],
                "qtn": ["q0[dec]", "q1[dec]", "q2[dec]", "q3[dec]"],
                "atti": ["ANG1[dec]", "ANG2[dec]", "ANG3[dec]"],
                "gpio": ["GPIO[dec]"],
                "counter": ["Counter[dec]"],
                "chksm": ["Chksm16[dec]"],
            }
            header4 = ["Sample No."]
            if scale_mode:
                # Scaled Mode
                for key in map_cols_sf:
                    if self.dev_burst_out.get(key):
                        header4.extend(map_cols_sf.get(key))
            else:
                # Raw Digital Mode
                for key in map_cols:
                    if self.dev_burst_out.get(key):
                        header4.extend(map_cols.get(key))
            self._csv_writer.writerows([header1, header2, header3, header4])
        except KeyboardInterrupt:
            pass
        except IOError:
            print("** Failure writing header")
            raise

    def write_trailer(self, end_date=None):
        """Writes the trailer rows to the writer object

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
            trailer1 = ["#Log End", str(end_date), "", "", "", "", "", "", "", ""]
            trailer2 = [
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
            trailer3 = [
                "#Data Rate",
                str(self.dev_status["dout_rate"]),
                "sps",
                "",
                "Filter Cfg",
                f"{self.dev_status['filter']}",
                "",
                "",
                "",
                "",
            ]
            self._csv_writer.writerows([trailer1, trailer2, trailer3])
        except KeyboardInterrupt:
            pass
        except IOError:
            print("** Failure writing trailer")
            raise

    def get_dev_status(self):
        """Writes table of device status info to the writer object"""

        _date = time.strftime("%Y-%m-%d")
        _time = time.strftime("%H:%M:%S")

        table = [
            [f"Date: {_date}", f"Time: {_time}"],
            SEPARATING_LINE,
            [
                f'PROD_ID: {self.dev_info["prod_id"]}',
                f'VERSION: {self.dev_info["version_id"]}',
                f'SERIAL: {self.dev_info["serial_id"]}',
            ],
            [
                f'DOUT_RATE: {self.dev_status["dout_rate"]}',
                f'FILTER: {self.dev_status["filter"].upper()}',
            ],
            [
                f'NDFLAG: {self.dev_status["ndflags"]}',
                f'TEMPC: {self.dev_status["tempc"]}',
                f'COUNTER: {str(self.dev_status["counter"]).title()}',
                f'CHKSUM: {self.dev_status["chksm"]}',
            ],
            [
                f'DLT: {self.dev_dlt_status["dlta"] or self.dev_dlt_status["dltv"]}',
                f'ATTI: {self.dev_atti_status["atti"]}',
                f'QTN: {self.dev_atti_status["qtn"]}',
                f'BIT32: {self.dev_status["is_32bit"]}',
            ],
        ]
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
                    print("CSV closed")
        except AttributeError:
            pass
