# Tenma DC power supply controllers

Provides two basic controllers (tested on Linux) for a TENMA DC power supply via serial interface. Working on python 2.7 and python 3.

 * tenmaControl.py (tenma-control) (command line utility)
 * gtkIndicator.py (tenma-applet) (GTK indicator to sit on tray)

# tenmaControl

## What is this?

A small command line program / library to setup a Tenma 72-XXXX DC POWER SUPPLY from your computer via SERIAL.

Supports the following models with predefined limits:

    * 72-2545 -> Tested on HW (@kxtells)
    * 72-2535 -> Set as manufacturer manual (not tested)
    * 72-2540 -> Tested on HW (thomas-phillips-nz)
    * 72-2550 -> Tested on HW (@kxtells)
    * 72-2705 -> Tested on HW (@ollie1400)
    * 72-2710 -> Tested on HW (r202401, renier.daudey)
    * 72-2930 -> Tested on HW (@Thomas-Vreys)
    * 72-2940 -> Set as manufacturer manual (not tested)
    * 72-13320 -> Set as manufacturer manual (not tested)
    * 72-13330 -> Tested on HW (thomas-phillips-nz)
    * 72-13360 -> Tested on HW (Sebastian Norlin)

Also, even if not described, should support [Koradka
models](https://sigrok.org/wiki/Korad_KAxxxxP_series) and other Velleman units
which are just rebrandings of the same internals. Might need to set the
appropiate `MATCH_STR` in the source code, feel free to open a PR if you test
it in a known hardware unit.

Originally, Coming back from holidays was hard. So I spent some time with a
little game setting up our power supply(tongue). You'll find a small
explanation of the original code in:

[https://jcastellssala.com/2017/10/31/tenma72-2540-linux-control/](https://jcastellssala.com/2017/10/31/tenma72-2540-linux-control/)

## Installing

### From pip

    pip install tenma-serial

pip install will leave `tenma-control` and `tenma-applet` in your PATH ready to use.

### Locally

It does not have many requirements, so you might just clone the repo and run it. install the required packages first.

	pip install -r requirements.txt


## Usage examples

Note that it can be connected via a usb to serial cable, or directly with the
provided USB cable. In Linux it identifies the usb as `Bus 001 Device 015: ID
0416:5011 Winbond Electronics Corp. Virtual Com Port `, running `dmesg` to get
where the /dev/ttyACMX device registerd and pointing tenmaControl.py to that
device should work.

any of the following examples can run via `tenma-control` or `tenmaControl.py`.

### Print the Tenma version

	tenmaControl.py /dev/ttyUSB0

### Set the current and the voltage

For example: 2.2 Amperes 5V:

	tenmaControl.py -c 2200 -v 5000 /dev/ttyUSB0

### Turn on the channel output

	tenmaControl.py --on /dev/ttyUSB0

### Turn OFF the channel output

	tenmaControl.py --off /dev/ttyUSB0

### Load an existing memory

	tenmaControl.py -r 1
	tenmaControl.py --recall 2

### Create a new value for a memory 4

	tenmaControl.py -c 2200 -v 5000 --save 4 /dev/ttyUSB0

### Print everything

	tenmaControl.py -c 2200 -v 5000 --save 4 --verbose --debug /dev/ttyUSB0

# tenma-applet gtkIndicator

A very simple GTK indicator to control a tenma DC power supply from a GTK based desktop (GNOME or similar).
Provides ON, OFF and RESET facilities. Simply start it with:

WARN: This applet is barely maintained and has not been tested in newer GNOME versions.

    tenma-applet

Or directly from the source code via:

	./gtkIndicator.py

## Known Shortcomings:
 * The physical buttons are blocked for a while after connecting.

# Testing:
This project contains some [pytest](https://pytest.org) tests to make it easier to add support for new power supply variants, and validate changes to the code.

These tests live under the `tests/` directory in `test_tenma.py`.  There are two environment variables used by the tests:
 * TENMA_MODEL - set this to the MATCH_STR of the power supply you're testing. Defaults to 72-2540
 * TENMA_PORT - Optional: set this to the COM/tty port on you PC connected to the power supply. Defaults to auto-finding the port

The tests were written against 72-2540, there are no extra tests for the 72-133XX models (yet). We curerntly test:
 * PSU init/version string
 * Set/get voltage
 * Set/get current
 * Save/recall memory in all slots
 * Set/unset beep
 * Turn output on/off

**Note: Before testing, disconnect everything from the power supply. We try to test as safely as possible, but no promises are made**

First, install pytest:

    pip install pytest

Then you can run the tests from the root directory of the repo:

    python -m pytest

You can set the environment variables when you run the test:

    # Windows:
    $env:TENMA_MODEL='72-2550'; $env:TENMA_PORT='COM7'; python -m pytest

    # Linux:
    TENMA_MODEL='72-2550' TENMA_PORT='COM7' python -m pytest
