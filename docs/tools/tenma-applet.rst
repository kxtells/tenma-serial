tenma-applet
============

.. contents::

General Description
-------------------

tenma-applet (gtkIndicator.py) lets you control your bench power supply using a simple GTK applet sitting on the system bar.

It provides basic ON/OFF and Memory selection. Current version is limited to the values already set in the unit.

To start it::
   
   tenma-applet

Select the serial connection
-----------------------------

tenma-applet lists the available serial connections under the `serial` menu. Simply selecting a connection and the applet tries to retrieve the model information and connect to it.
