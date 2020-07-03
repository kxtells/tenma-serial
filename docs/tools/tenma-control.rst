tenma-control
=============

.. contents::

General Description
-------------------

tenma-control (tenmaControl.py) lets you control your bench power supply directly from the command line
via a serial connection.

This page provides a set of common examples on how to use the tenma-control command. For a full description of the options provided simply run::

   tenma-control -h

The command always expects its input input as milliAmperes and milliVolts:



Print the Tenma version
-----------------------

::

	tenma-control /dev/ttyUSB0

Set the current and the voltage
-------------------------------

For example: 2.2 Amperes 5V::

	tenma-control -c 2200 -v 5000 /dev/ttyUSB0

Turn on the channel output
--------------------------

::

	tenma-control --on /dev/ttyUSB0

Turn off the channel output
---------------------------

::

	tenma-control --off /dev/ttyUSB0

Load an existing memory
-----------------------

::

	tenma-control -r 1
	tenma-control --recall 2

Create a new value for a memory 4
---------------------------------

::

	tenma-control -c 2200 -v 5000 --save 4 /dev/ttyUSB0

Verbose output
--------------

::

	tenma-control -c 2200 -v 5000 --save 4 --verbose /dev/ttyUSB0


Serial output
--------------

::

	tenma-control -c 2200 -v 5000 --save 4 --debug /dev/ttyUSB0



