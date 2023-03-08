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


"""Generic utility to configure and read sensor data from an Epson
   Sensing System Device using the UART interface and output to stdout
   or CSV file. This also demonstrates using the esensorlib pkg.
"""

import argparse
import time
from tqdm import tqdm

import esensorlib.sensor_core as sensor
from esensorlib.logger import helper

parser = argparse.ArgumentParser(
    description="This program is intended as \
                                 sample code for evaluation testing \
                                 the Epson device with the UART I/F. This \
                                 program will initialize the device with \
                                 user specified arguments and retrieve \
                                 sensor data and format the output to \
                                 console or CSV file. Other misc. utility \
                                 functions are described in the help \
                                 "
)

group_bfields = parser.add_argument_group("output field options")
group_atti = parser.add_argument_group("attitude options")
group_dlt = parser.add_argument_group("delta angle/velocity options")
group_flash = parser.add_argument_group("flash-related options")
group_debug = parser.add_argument_group("debug options")

mutual_smpl_time = parser.add_mutually_exclusive_group()
mutual_ext_cfg = parser.add_mutually_exclusive_group()

parser.add_argument(
    "-s",
    "--serial_port",
    help="specifies the serial port comxx or /dev/ttyUSBx",
    type=str,
)

parser.add_argument(
    "-b",
    "--baud_rate",
    help="specifies baudrate of the serial port, default is 460800",
    type=int,
    choices=[921600, 460800, 230400],
    default=460800,
)

mutual_smpl_time.add_argument(
    "--secs",
    help="specifies time duration of reading sensor data in \
                    seconds, default 5 seconds. \
                    Press CTRL-C to abort and exit early",
    type=float,
    default=5,
)

mutual_smpl_time.add_argument(
    "--samples",
    help="specifies the approx number samples to read sensor \
                    data. \
                    Press CTRL-C to abort and exit early",
    type=int,
)

parser.add_argument(
    "--drate",
    help="specifies IMU output data rate in sps, \
                    default is 200sps",
    type=float,
    choices=[
        2000,
        1000,
        500,
        250,
        125,
        62.5,
        31.25,
        15.625,
        400,
        200,
        100,
        80,
        50,
        40,
        25,
        20,
    ],
    default=200,
)

parser.add_argument(
    "--filter",
    help="specifies the filter selection. If not specified, \
                    moving average based on selected output data rate \
                    will automatically be selected. \
                    NOTE: Refer to datasheet for valid settings. \
         ",
    type=str.lower,
    choices=[
        "mv_avg0",
        "mv_avg2",
        "mv_avg4",
        "mv_avg8",
        "mv_avg16",
        "mv_avg32",
        "mv_avg64",
        "mv_avg128",
        "k32_fc25",
        "k32_fc50",
        "k32_fc100",
        "k32_fc200",
        "k32_fc400",
        "k64_fc25",
        "k64_fc50",
        "k64_fc100",
        "k64_fc200",
        "k64_fc400",
        "k128_fc25",
        "k128_fc50",
        "k128_fc100",
        "k128_fc200",
        "k128_fc400",
    ],
)

parser.add_argument(
    "--model",
    help="specifies the IMU model type, if not specified will auto-detect",
    type=str.lower,
    choices=[
        "g320",
        "g354",
        "g364pdc0",
        "g364pdca",
        "g365pdc1",
        "g365pdf1",
        "g370pdf1",
        "g370pds0",
        "g330pdg0",
        "g366pdg0",
        "g370pdg0",
    ],
)

parser.add_argument(
    "--a_range",
    help="specifies to use 16G accelerometer output range instead of 8G. \
                    NOTE: Not all devices support this mode.",
    action="store_true",
)

parser.add_argument(
    "--bit16",
    help="specifies to output 16-bit resolution, otherwise use 32-bit",
    action="store_true",
)

parser.add_argument(
    "--csv",
    help="specifies to read sensor data to file otherwise sends \
                     to console. An optional string parameter \
                     if specified will be appended to filename \
                     ",
    action="store_true",
)

parser.add_argument(
    "--noscale",
    help="specifies to keep sensor data as digital counts \
                    (without applying scale factors)",
    action="store_true",
)

group_bfields.add_argument(
    "--ndflags",
    help="specifies to enable ND/EA flags in sensor data",
    action="store_true",
)

group_bfields.add_argument(
    "--tempc",
    help="specifies to enable temperature data in sensor data",
    action="store_true",
)

group_bfields.add_argument(
    "--chksm",
    help="specifies to enable 16-bit checksum in sensor data",
    action="store_true",
)

mutual_ext_cfg.add_argument(
    "--counter",
    help="specifies to enable reset counter(GPIO2) or sample\
                     counter in the sensor data",
    type=str.lower,
    choices=[
        "reset",
        "sample",
    ],
)

mutual_ext_cfg.add_argument(
    "--ext_trigger",
    help="specifies to enable external trigger mode on GPIO2",
    action="store_true",
)

group_dlt.add_argument(
    "--dlt",
    help="specifies to enable delta angle & delta velocity \
                    in sensor data with specified delta angle, \
                    delta velocity scale factors. \
                    NOTE: Not all devices support this mode.",
    nargs=2,
    type=int,
    choices=range(0, 16),
)

group_atti.add_argument(
    "--atti",
    help="specifies to enable attitude output in sensor data in \
                    euler mode or inclination mode \
                    NOTE: Not all devices support this mode.",
    type=str.lower,
    choices=[
        "euler",
        "incl",
    ],
)

group_atti.add_argument(
    "--qtn",
    help="specifies to enable attitude quaternion data in sensor data. \
                    NOTE: Not all devices support this mode.",
    action="store_true",
)

group_atti.add_argument(
    "--atti_profile",
    help="specifies the attitude motion profile \
                    when attitude euler or quaternion output is enabled. \
                    NOTE: Not all devices support this feature.",
    type=str.lower,
    choices=[
        "modea",
        "modeb",
        "modec",
    ],
    default="modea",
)

group_atti.add_argument(
    "--atti_conv",
    help="specifies the attitude axis conversion \
                    when attitude euler output is enabled. \
                    Must be between 0 to 23 (inclusive). \
                    This must be set to 0 for when quaternion output \
                    is enabled \
                    NOTE: Not all devices support this feature.",
    type=int,
    choices=range(0, 24),
    default=0,
)

group_flash.add_argument(
    "--autostart",
    help="Enables AUTO_START fucntion. Should run afterwards with --flashupdate \
                    to store the settings to flash",
    action="store_true",
)

group_flash.add_argument(
    "--init_default",
    help="This sets the IMU flash setting with \
                    default register settings per datasheet.",
    action="store_true",
)

group_flash.add_argument(
    "--flash_update",
    help="specifies to store current IMU \
                    register settings to flash. This is normally used with --autostart \
                    or --initdefault",
    action="store_true",
)

group_debug.add_argument(
    "--dump_reg",
    help="specifies to read out all the registers \
                    from the device without configuring device",
    action="store_true",
)

group_debug.add_argument(
    "--verbose",
    help="specifies to enable low-level register messages \
                    for debugging",
    action="store_true",
)

args = parser.parse_args()

if __name__ == "__main__":
    # Output parsed command parameters
    if args.verbose:
        print(args)

    # Set the IMU model parameter
    if not args.model:
        args.model = "auto"
        print("Model not specified, attempting to auto-detect")

    # Generate filename tag based on specified settings
    if args.csv:
        fn_list = [time.strftime("%Y%m%d-%H%M%S")]

        if args.bit16:
            fn_list.append("16B")
        else:
            fn_list.append("32B")
        if args.noscale:
            fn_list.append("NSCL")
        else:
            fn_list.append("SCL")
        if args.ndflags:
            fn_list.append("NDF")
        if args.tempc:
            fn_list.append("TC")
        if args.dlt:
            fn_list.extend(["DLT", str(args.dlt[0]), str(args.dlt[1])])
        if args.qtn:
            fn_list.append("QTN")
        if args.atti:
            fn_list.append("ATTI")
        if args.counter:
            fn_list.append("CNT")
        if args.chksm:
            fn_list.append("CHK")

    # Communicate with device to process runtime switches and parameters
    while True:
        try:
            imu = sensor.SensorDevice(
                comport=args.serial_port,
                baudrate=args.baud_rate,
                model=args.model,
                verbose=args.verbose,
            )
        except IOError:
            print("Port Error: Unable to initialize device")
            break
        if args.dump_reg:
            imu.dump_reg()
            break
        # If flash backup enabled
        if args.init_default:
            imu.init_backup(verbose=args.verbose)
            break
        # If flash backup enabled
        if args.flash_update:
            imu.backup_flash(verbose=args.verbose)
            break
        # Create basic configuration dict arguments
        basic_cfg = {
            "dout_rate": args.drate,
            "filter": args.filter,
            "ndflags": args.ndflags,
            "tempc": args.tempc,
            "counter": args.counter,
            "chksm": args.chksm,
            "uart_auto": True,
            "auto_start": args.autostart,
            "is_32bit": not args.bit16,
            "a_range": args.a_range,
            "ext_trigger": args.ext_trigger,
        }
        dlt_cfg = {
            "dlta": bool(args.dlt),
            "dltv": bool(args.dlt),
            "dlta_sf_range": args.dlt[0] if args.dlt else None,
            "dltv_sf_range": args.dlt[1] if args.dlt else None,
        }
        atti_cfg = {
            "atti": bool(args.atti),
            "mode": args.atti,
            "conv": args.atti_conv,
            "profile": args.atti_profile,
            "qtn": args.qtn,
        }
        if args.verbose:
            print("basic_cfg: ", basic_cfg)
            print("dlt_cfg", dlt_cfg)
            print("atti_cfg", atti_cfg)
        # Configure device with configuration dicts
        imu.config(
            basic_cfg=basic_cfg,
            dlt_cfg=dlt_cfg,
            atti_cfg=atti_cfg,
            verbose=args.verbose,
        )
        # Create helper for handling sensor data after
        # configuring SensorDevice()
        log = helper.LoggerHelper(
            sensor=imu,
        )
        # Calculate number of samples to collect
        num_samples = args.samples if args.samples else int(args.secs * args.drate)
        # If CSV enabled, send tuple of strings
        # otherwise None means output to console
        fname_param = fn_list if args.csv else None

        imu.goto("Sampling", verbose=args.verbose)
        try:
            log.set_writer(to=fname_param)
            log.write_header(scale_mode=not args.noscale)
            # If csv enabled show tqdm progress indicator
            iter_samples = tqdm(range(num_samples)) if args.csv else range(num_samples)
            for i in iter_samples:
                log.write(sample_data=imu.read_sample(scale_mode=not args.noscale))
            imu.goto("Config", verbose=args.verbose)
        except IOError:
            break
        except KeyboardInterrupt:
            log.write_trailer()
        else:
            log.write_trailer()
        log.get_dev_status()
        break
