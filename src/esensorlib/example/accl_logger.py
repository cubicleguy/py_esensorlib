#!/usr/bin/env python

# MIT License

# Copyright (c) 2024, 2025 Seiko Epson Corporation

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
Sensing System accelerometer using the UART interface and output to stdout
or CSV file. This also demonstrates using the esensorlib pkg.
"""

import argparse
import sys
import time

from loguru import logger
from tqdm import tqdm

from esensorlib import sensor_device
from esensorlib.example import helper

SUPPORTED_MODELS = [
    "a352ad10",
    "a370ad10",
]


def get_args():
    """
    returns parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="This program is intended as sample code for "
        "evaluation testing the Epson device. This "
        "program will initialize the device with user "
        "specified arguments and retrieve sensor data "
        "and format the output to console or CSV file. "
        "Other misc. utility functions are described "
        "in the help."
    )

    group_bfields = parser.add_argument_group("output field options")
    group_flash = parser.add_argument_group("flash-related options")
    group_debug = parser.add_argument_group("debug options")
    group_csv = parser.add_argument_group("csv options")

    mutual_smpl_time = parser.add_mutually_exclusive_group()

    parser.add_argument(
        "-s",
        "--serial_port",
        help="specifies the serial port comxx or /dev/ttyUSBx.",
        type=str,
    )

    parser.add_argument(
        "-b",
        "--baud_rate",
        help="specifies baudrate of the serial port, default is 460800. "
        "Not all devices support range of baudrates. This assumes "
        "the device serial port baudrate is already configured. "
        "Refer to device datasheet.",
        type=int,
        choices=[460800, 230400, 115200],
        default=460800,
    )

    mutual_smpl_time.add_argument(
        "--secs",
        help="specifies time duration of reading sensor data in "
        "seconds, default 5 seconds. Press CTRL-C to abort "
        "and exit early.",
        type=float,
        default=5,
    )

    mutual_smpl_time.add_argument(
        "--samples",
        help="specifies the approx number samples to read sensor "
        "data. Press CTRL-C to abort and exit early.",
        type=int,
    )

    parser.add_argument(
        "--drate",
        help="specifies ACCL output data rate in sps, default is 200sps.",
        type=float,
        choices=[
            1000,
            500,
            200,
            100,
            50,
        ],
        default=200,
    )

    parser.add_argument(
        "--filter",
        help="specifies the filter selection. If not specified, "
        "filter based on selected output data rate "
        "will automatically be selected. NOTE: Refer to datasheet "
        "for valid settings.",
        type=str.lower,
        choices=[
            "k64_fc83",
            "k64_fc220",
            "k128_fc36",
            "k128_fc110",
            "k128_fc350",
            "k512_fc9",
            "k512_fc16",
            "k512_fc60",
            "k512_fc210",
            "k512_fc460",
        ],
    )

    parser.add_argument(
        "--model",
        help="specifies the ACCL model type, if not specified will auto-detect.",
        type=str.lower,
        choices=SUPPORTED_MODELS,
    )

    group_csv.add_argument(
        "--csv",
        help="specifies to read sensor data to CSV file otherwise sends " "to console.",
        action="store_true",
    )

    parser.add_argument(
        "--tilt",
        help="specifies tilt output for each X-Y-Z axes as a 3-bit enable "
        "mask (a 1 in bit position enables tilt output on that axis).",
        type=int,
        choices=[0, 1, 2, 3, 4, 5, 6, 7],
        default=0,
    )

    parser.add_argument(
        "--noscale",
        help="specifies to keep sensor data as digital counts (without "
        "applying scale factor conversion).",
        action="store_true",
    )

    parser.add_argument(
        "--reduced_noise",
        help="specifies to enabled reduced noise floor condition."
        "Otherwise, standard noise floor condition selected.",
        action="store_true",
    )

    parser.add_argument(
        "--dis_temp_stabil",
        help="specifies to disable bias stabilization against thermal "
        "shock. Otherwise, enabled.",
        action="store_true",
    )

    group_bfields.add_argument(
        "--ndflags",
        help="specifies to enable ND/EA flags in sensor data.",
        action="store_true",
    )

    group_bfields.add_argument(
        "--tempc",
        help="specifies to enable temperature data in sensor data.",
        action="store_true",
    )

    group_bfields.add_argument(
        "--chksm",
        help="specifies to enable 16-bit checksum in sensor data.",
        action="store_true",
    )

    parser.add_argument(
        "--counter",
        help="specifies to enable sample counter in the sensor data.",
        action="store_true",
    )

    parser.add_argument(
        "--ext_trigger",
        help="specifies the external trigger mode on EXT pin. "
        "NOTE: Refer to datasheet for valid settings for the model.",
        type=str.lower,
        choices=[
            "disabled",
            "ext_trig_pos",
            "ext_trig_neg",
            "1pps_pos",
            "1pps_neg",
        ],
        default="disabled",
    )

    group_flash.add_argument(
        "--autostart",
        help="Enables AUTO_START function. Run logger again afterwards "
        "with --flash_update to store current register settings "
        "to device flash.",
        action="store_true",
    )

    group_flash.add_argument(
        "--init_default",
        help="This sets the device flash setting back to default "
        "register settings per datasheet.",
        action="store_true",
    )

    group_flash.add_argument(
        "--flash_update",
        help="specifies to store the current device register settings "
        "to device flash without configuring the device. Run the "
        "logger program with desired settings first, before "
        "re-running with the --flash_update option.",
        action="store_true",
    )

    group_debug.add_argument(
        "--dump_reg",
        help="specifies to read out all the registers from the "
        "device without configuring device.",
        action="store_true",
    )

    group_debug.add_argument(
        "--no_init",
        help="specifies to NOT initialize the device and assumes "
        "device is pre-configured for with --autostart and "
        "already in SAMPLING mode.\n"
        "NOTE: User-specified options must match device programmed "
        " --autostart settings.",
        action="store_true",
    )

    group_debug.add_argument(
        "--verbose",
        help="specifies to enable low-level register messages " "for debugging.",
        action="store_true",
    )

    group_csv.add_argument(
        "--tag",
        help="specifies an extra string to append to end of the "
        "filename if CSV is enabled.",
        type=str,
        default=None,
    )

    group_csv.add_argument(
        "--max_rows",
        help="specifies to split CSV files when the number of samples "
        "exceeds specified max_rows.",
        type=int,
    )

    return parser.parse_args()


def supported_device_model(prod_id):
    """
    returns True if PROD_ID is in supported models list
    """
    return prod_id.lower() in SUPPORTED_MODELS


if __name__ == "__main__":
    # Parse arguments
    args = get_args()
    if args.verbose:
        logger.debug(f"args = {args}")

    # Set the sensor model parameter
    if not args.model:
        if args.no_init:
            print(
                "When using --no_init, device model must be specified with --model <model name>"
            )
            sys.exit(1)
        args.model = "auto"
        print("Model not specified, attempting to auto-detect")

    # Generate filename based on specified settings
    if args.csv:
        fn_list = [time.strftime("%Y%m%d-%H%M%S")]

        if args.noscale:
            fn_list.append("NSCL")
        else:
            fn_list.append("SCL")
        if args.ndflags:
            fn_list.append("NDF")
        if args.tempc:
            fn_list.append("TC")
        if args.counter:
            fn_list.append("CNT")
        if args.chksm:
            fn_list.append("CHK")
        if args.tag:
            fn_list.append(args.tag)

    file_index = 0

    # Communicate with device to process runtime switches and parameters
    try:
        accl = sensor_device.SensorDevice(
            port=args.serial_port,
            speed=args.baud_rate,
            if_type="uart",
            model=args.model,
            verbose=args.verbose,
            no_init=args.no_init,
        )
    except IOError:
        print("Port Error: Unable to initialize device")
        sys.exit(1)
    if supported_device_model(accl.info.get("prod_id")) is False:
        print(f"{__file__} does not supported device model: {accl.info.get('prod_id')}")
        sys.exit(1)
    if args.dump_reg:
        accl.get_regdump()
        sys.exit(0)
    if args.init_default:
        accl.init_backup(verbose=args.verbose)
        sys.exit(0)
    if args.flash_update:
        accl.backup_flash(verbose=args.verbose)
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
        "ext_trigger": args.ext_trigger,
        "tilt": args.tilt,
        "reduced_noise": args.reduced_noise,
        "temp_stabil": not args.dis_temp_stabil,
        "verbose": args.verbose,
        "no_init": args.no_init,
    }
    if args.verbose:
        logger.debug(f"device_cfg: {device_cfg}")

    # Configure device with configuration dict
    accl.set_config(**device_cfg)
    # Create helper for handling sensor data after
    # configuring SensorDevice()
    log = helper.LoggerHelper(
        sensor=accl,
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

    accl.goto("sampling")
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
                log.write(sample_data=accl.read_sample_unscaled(verbose=args.verbose))
            else:
                log.write(sample_data=accl.read_sample(verbose=args.verbose))
    except KeyboardInterrupt:
        pass
    accl.goto("config")
    log.write_footer()
    log.get_dev_status()
    sys.exit(0)
