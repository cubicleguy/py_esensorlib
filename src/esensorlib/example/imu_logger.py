#!/usr/bin/env python

# MIT License

# Copyright (c) 2024 Seiko Epson Corporation

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
Sensing System IMU using the UART interface and output to stdout
or CSV file. This also demonstrates using the esensorlib pkg.
"""

import argparse
import sys
import time

from tqdm import tqdm

from esensorlib import sensor_device
from esensorlib.example import helper

SUPPORTED_MODELS = [
    "g320pdg0",
    "g320pdgn",
    "g354pdh0",
    "g364pdc0",
    "g364pdca",
    "g365pdc1",
    "g365pdf1",
    "g370pdf1",
    "g370pds0",
    "g330pdg0",
    "g366pdg0",
    "g370pdg0",
    "g370pdt0",
    "g570pr20",
]

parser = argparse.ArgumentParser(
    description="This program is intended as \
                                 sample code for evaluation testing \
                                 the Epson device. This \
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
group_csv = parser.add_argument_group("csv options")

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
    help="specifies baudrate of the serial port, default is 460800. \
    Not all devices support range of baudrates",
    type=int,
    choices=[921600, 460800, 230400, 1000000, 1500000, 2000000],
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
                    moving average filter based on selected output data rate \
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
    choices=SUPPORTED_MODELS,
)

parser.add_argument(
    "--a_range",
    help="specifies to use 16G accelerometer output range instead of 8G. \
                    NOTE: Not all models support this feature.",
    action="store_true",
)

parser.add_argument(
    "--bit16",
    help="specifies to output sensor data in 16-bit resolution, \
                    otherwise use 32-bit.",
    action="store_true",
)

group_csv.add_argument(
    "--csv",
    help="specifies to read sensor data to CSV file otherwise sends \
                     to console.",
    action="store_true",
)

parser.add_argument(
    "--noscale",
    help="specifies to keep sensor data as digital counts \
                    (without applying scale factor conversion)",
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
    help="specifies to enable reset counter (EXT/GPIO2 pin) or sample \
                     counter in the sensor data",
    type=str.lower,
    choices=[
        "reset",
        "sample",
    ],
    default="",
)

mutual_ext_cfg.add_argument(
    "--ext_trigger",
    help="specifies to enable external trigger mode on EXT/GPIO2 pin",
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
                    --atti_conv must be 0 for quaternion output. \
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
    help="Enables AUTO_START function. Run logger again afterwards with --flash_update \
                    to store the register settings to device flash",
    action="store_true",
)

group_flash.add_argument(
    "--init_default",
    help="This sets the flash setting back to \
                    default register settings per datasheet.",
    action="store_true",
)

group_flash.add_argument(
    "--flash_update",
    help="specifies to store current \
                    register settings to device flash.",
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

group_csv.add_argument(
    "--tag",
    help="specifies extra string to append to end of the \
                    filename if CSV is enabled",
    type=str,
    default=None,
)

group_csv.add_argument(
    "--max_rows",
    help="specifies to split CSV files when # of samples exceeds \
          max_rows",
    type=int,
)

args = parser.parse_args()


def supported_device_model(prod_id):
    """
    returns PROD_ID as string
    """
    return prod_id.lower() in SUPPORTED_MODELS


if __name__ == "__main__":
    # Output parsed command parameters
    if args.verbose:
        print(args)

    # Set the sensor model parameter
    if not args.model:
        args.model = "auto"
        print("Model not specified, attempting to auto-detect")

    # Generate filename based on specified settings
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
        if args.tag:
            fn_list.append(args.tag)
    file_index = 0

    # Communicate with device to process runtime switches and parameters
    try:
        imu = sensor_device.SensorDevice(
            port=args.serial_port,
            speed=args.baud_rate,
            if_type="uart",
            model=args.model,
            verbose=args.verbose,
        )
    except IOError:
        print("Port Error: Unable to initialize device")
        sys.exit(1)
    if supported_device_model(imu.info.get("prod_id")) is False:
        print(f"{__file__} does not supported device model: {imu.info.get('prod_id')}")
        sys.exit(1)
    if args.dump_reg:
        imu.get_regdump()
        sys.exit(0)
    # If init_default enabled
    if args.init_default:
        imu.init_backup(verbose=args.verbose)
        sys.exit(0)
    # If flash backup enabled
    if args.flash_update:
        imu.backup_flash(verbose=args.verbose)
        sys.exit(0)
    # Create configuration dict arguments
    device_cfg = {
        "dout_rate": args.drate,
        "filter_sel": args.filter,
        "ndflags": args.ndflags,
        "tempc": args.tempc,
        "counter": args.counter,
        "chksm": args.chksm,
        "uart_auto": True,
        "auto_start": args.autostart,
        "is_32bit": not args.bit16,
        "a_range": args.a_range,
        "ext_trigger": args.ext_trigger,
        # delta angle, delta velocity
        "dlta": bool(args.dlt),
        "dltv": bool(args.dlt),
        "dlta_sf_range": args.dlt[0] if args.dlt else None,
        "dltv_sf_range": args.dlt[1] if args.dlt else None,
        # attitude
        "atti": bool(args.atti),
        "atti_mode": args.atti,
        "atti_conv": args.atti_conv,
        "atti_profile": args.atti_profile,
        "qtn": args.qtn,
        "verbose": args.verbose,
    }
    if args.verbose:
        print("device_cfg: ", device_cfg)
    # Configure device with configuration dict
    imu.set_config(**device_cfg)
    # Create helper for handling sensor data after
    # configuring SensorDevice()
    log = helper.LoggerHelper(
        sensor=imu,
    )
    # Calculate number of samples to collect
    num_samples = int(args.secs * args.drate)
    if args.samples:
        num_samples = args.samples

    # If CSV enabled, send tuple of strings for filename creation
    # otherwise None means output to console
    fname_param = None
    if args.csv:
        fname_param = fn_list

    imu.goto("Sampling", verbose=args.verbose)
    try:
        if args.csv and args.max_rows:
            # Append file_index for csv output and max_rows
            log.set_writer(to=fname_param + [f"{file_index:04}"])
        else:
            log.set_writer(to=fname_param)
        log.write_header(scale_mode=not args.noscale)
        # If csv enabled show progress indicator
        iter_samples = tqdm(range(num_samples)) if args.csv else range(num_samples)

        for i in iter_samples:
            # Create new CSV with header info when max_rows exceeded and increment file_index
            if args.csv and args.max_rows and (i != 0) and (i % args.max_rows) == 0:
                file_index = file_index + 1
                log.set_writer(to=fname_param + [f"{file_index:04}"])
                log.write_header(scale_mode=not args.noscale)
            if args.noscale:
                log.write(sample_data=imu.read_sample_unscaled(verbose=args.verbose))
            else:
                log.write(sample_data=imu.read_sample(verbose=args.verbose))
    except KeyboardInterrupt:
        pass
    imu.goto("Config", verbose=args.verbose)
    log.write_footer()
    log.get_dev_status()
    sys.exit(0)
