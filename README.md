# Tenma DC power supply controllers

Provides two basic controllers (tested on Linux) for a TENMA DC power supply via serial interface.

 * tenmaControl (command line utility)
 * gtkIndicator (GTK indicator to sit on tray)

# tenmaControl

## What is this?

A small command line program / library to setup a Tenma 72-XXXX DC POWER SUPPLY from your computer via SERIAL. 

Supports the following models with predefined limits:

    * 72-2545 -> tested on HW
    * 72-2535 -> Set as manufacturer manual (not tested)
    * 72-2540 -> Set as manufacturer manual (not tested)
    * 72-2550 -> Set as manufacturer manual (not tested)
    * 72-2930 -> Set as manufacturer manual (not tested)
    * 72-2940 -> Set as manufacturer manual (not tested)

Also, even if not described, should support [Koradka models](https://sigrok.org/wiki/Korad_KAxxxxP_series) and other Velleman units which are just rebrandings of the same internals.

Originally, Coming back from holidays was hard. So I spent some time with a little game (tongue). You'll find a small explanation of the code in:

[https://jcastellssala.com/2017/10/31/tenma72-2540-linux-control/](https://jcastellssala.com/2017/10/31/tenma72-2540-linux-control/)

## Installing

### From pip

    pip install tenma-serial

### Locally

It does not have many requirements, so you might just clone the repo and run it. install the required packages first.

	pip install -r requirements.txt


## Usage examples

Note that it can be connected via a usb to serial cable, or directly with the provided USB cable. In Linux it identifies the usb as _Bus 001 Device 015: ID 0416:5011 Winbond Electronics Corp. Virtual Com Port
_, running _dmesg_ to get where the /dev/ttyACMX device registerd and pointing tenmaControl.py to that device should work.

### Print the Tenma version

	python tenmaControl.py /dev/ttyUSB0

### Set the current and the voltage

For example: 2.2 Amperes 5V:

	python tenmaControl.py -c 2200 -v 5000 /dev/ttyUSB0

### Turn on the channel output

	python tenmaControl.py --on /dev/ttyUSB0

### Turn OFF the channel output

	python tenmaControl.py --off /dev/ttyUSB0

### Load an existing memory

	python tenmaControl.py -r 1
	python tenmaControl.py --recall 2

### Create a new value for a memory 4

	python tenmaControl.py -c 2200 -v 5000 --save 4 /dev/ttyUSB0

### Print everything

	python tenmaControl.py -c 2200 -v 5000 --save 4 --verbose --debug /dev/ttyUSB0

# gtkIndicator

A very simple GTK indicator to control a tenma DC power supply from a graphical desktop. Provides ON, OFF and RESET facilities. Simply start it with:

	./gtkIndicator.py

# Known Shortcomings:
 * The physical buttons are blocked for a while after connecting.
