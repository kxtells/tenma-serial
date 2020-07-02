#!/usr/bin/python
"""
    gtkIndicator is a small gtk graphical tool to control a Tenma DC power
    supply from a desktop environment.
    Copyright (C) 2017 Jordi Castells

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import glob
import os
import signal
import sys

import gi
import pkg_resources
import serial

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

try:
    from tenma.tenmaDcLib import instantiate_tenma_class_from_device_response, TenmaException
except:
    from tenmaDcLib import instantiate_tenma_class_from_device_response, TenmaException



APPINDICATOR_ID = 'Tenma DC Power'


def serial_ports():
    """ Lists serial port names
        Shamesly ripped from stackOverflow

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class gtkController():
    def __init__(self):
        self.serialPort = "No Port"
        self.serialMenu = None
        self.T = None
        self.itemSet = []
        pass

    def portSelected(self, source):
        oldPort = self.serialPort
        self.serialPort = source.get_label()

        try:
            if not self.T:
                self.T = instantiate_tenma_class_from_device_response(self.serialPort)
            else:
                self.T.setPort(self.serialPort)
        except Exception as e:
            self.setItemSetStatus(False)
            notify.Notification.new("<b>ERROR</b>", repr(e),
                                    gtk.STOCK_DIALOG_ERROR).show()
            self.serialPort = oldPort

        ver = self.T.getVersion()
        if not ver:
            notify.Notification.new("<b>ERROR</b>",
                                    "No response on %s" % self.serialPort,
                                    gtk.STOCK_DIALOG_ERROR).show()
            self.serialPort = oldPort
            self.setItemSetStatus(False)
        else:
            notify.Notification.new("<b>CONNECTED TO</b>", ver, None).show()
            self.setItemSetStatus(True)

        self.item_connectedPort.set_label(self.serialPort)

    def build_serial_submenu(self, source):
        """
            Build the serialSubmenu assuming that it is un runtime (remove,
            existing entries and call show in all new entries)
        """
        if not self.serialMenu:
            self.serialMenu = gtk.Menu()

        for entry in self.serialMenu.get_children():
            self.serialMenu.remove(entry)

        for serialPort in serial_ports():
            menuEntry = gtk.MenuItem(serialPort)
            menuEntry.connect('activate', self.portSelected)
            self.serialMenu.append(menuEntry)
            menuEntry.show()

        sep = gtk.SeparatorMenuItem()
        self.serialMenu.append(sep)
        sep.show()

        menuEntry = gtk.MenuItem("Reload")
        menuEntry.connect('activate', self.build_serial_submenu)
        self.serialMenu.append(menuEntry)
        menuEntry.show()

        return self.serialMenu

    def setItemSetStatus(self, onOff):
        if onOff:
            [i.set_sensitive(True) for i in self.itemSet]
        else:
            [i.set_sensitive(False) for i in self.itemSet]

    def build_gtk_menu(self):
        serialMenu = self.build_serial_submenu(None)

        menu = gtk.Menu()

        self.item_connectedPort = gtk.MenuItem(self.serialPort)
        self.item_connectedPort.set_right_justified(True)
        self.item_connectedPort.set_sensitive(False)

        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.quit)

        item_serial_menu = gtk.MenuItem('Serial')
        item_serial_menu.set_submenu(serialMenu)

        item_on = gtk.MenuItem('ON')
        item_on.connect('activate', self.tenmaTurnOn)

        item_off = gtk.MenuItem('OFF')
        item_off.connect('activate', self.tenmaTurnOff)

        item_reset = gtk.MenuItem('RESET')
        item_reset.connect('activate', self.tenmaReset)

        menu.append(self.item_connectedPort)
        menu.append(item_serial_menu)

        sep = gtk.SeparatorMenuItem()
        menu.append(sep)

        menu.append(item_on)
        menu.append(item_off)
        menu.append(item_reset)

        sep = gtk.SeparatorMenuItem()
        menu.append(sep)

        menu.append(item_quit)

        menu.show_all()

        self.itemSet.extend([item_on, item_off, item_reset])
        self.setItemSetStatus(False)

        return menu

    def quit(self, source):
        gtk.main_quit(self)

    def tenmaTurnOn(self, source):
        try:
            self.T.ON()
        except Exception as e:
            notify.Notification.new("<b>ERROR</b>", repr(e),
                                    gtk.STOCK_DIALOG_ERROR).show()

    def tenmaTurnOff(self, source):
        try:
            self.T.OFF()
        except Exception as e:
            notify.Notification.new("<b>ERROR</b>", repr(e),
                                    gtk.STOCK_DIALOG_ERROR).show()

    def tenmaReset(self, source):
        try:
            self.T.OFF()
            self.T.ON()
        except Exception as e:
            notify.Notification.new("<b>ERROR</b>", repr(e),
                                    gtk.STOCK_DIALOG_ERROR).show()


def main():
    notify.init(APPINDICATOR_ID)
    controller = gtkController()
    indicator = appindicator.Indicator.new(APPINDICATOR_ID,
                                           pkg_resources.resource_filename(__name__, 'logo.png'),
                                           appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(controller.build_gtk_menu())
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()

if __name__ == "__main__":
    main()
