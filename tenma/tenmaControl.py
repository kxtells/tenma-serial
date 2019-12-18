"""
    Command line tenma control program for Tenma72_2540
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
    @author Jordi Castells
"""

import argparse

from tenmaDcLib import *


def main():
    parser = argparse.ArgumentParser(description='Control a Tenma 72-2540 power supply connected to a serial port')
    parser.add_argument('device', default="/dev/ttyUSB0")
    parser.add_argument('-v', '--voltage', help='set mV', required=False, type=int)
    parser.add_argument('-c', '--current', help='set mA', required=False, type=int)
    parser.add_argument('--safeC', help='set safety current limit to mA', required=False, type=int)
    parser.add_argument('--safeV', help='set safety voltage limit to mV', required=False, type=int)
    parser.add_argument('-C', '--channel', help='channel to set (if not provided, 1 will be used)', required=False, type=int, default=1)
    parser.add_argument('-s', '--save', help='Save current configuration to Memory', required=False, type=int)
    parser.add_argument('-r', '--recall', help='Load configuration from Memory', required=False, type=int)
    parser.add_argument('-S', '--status', help='Retrieve and print system status', required=False, action="store_true", default=False)
    parser.add_argument('--ocp-enable', help='Enable overcurrent protection', required=False, action="store_true", default=False)
    parser.add_argument('--ocp-disable', help='Disable overcurrent pritection', required=False, action="store_true", default=False)
    parser.add_argument('--ovp-enable', help='Enable overvoltage protection', required=False, action="store_true", default=False)
    parser.add_argument('--ovp-disable', help='Disable overvoltage pritection', required=False, action="store_true", default=False)
    parser.add_argument('--on', help='Set output to ON', action="store_true", default=False)
    parser.add_argument('--safeOn', help='Safely set output to ON', action="store_true", default=False)
    parser.add_argument('--off', help='Set output to OFF', action="store_true", default=False)
    parser.add_argument('--verbose', help='Chatty program', action="store_true", default=False)
    parser.add_argument('--debug', help='print serial commands', action="store_true", default=False)
    parser.add_argument('--script', help='runs from script. Only print result of query, no version', action="store_true", default=False)
    parser.add_argument('--actualCurrent', help='returns the actual current reading', action="store_true", default=False)
    parser.add_argument('--actualVoltage', help='returns the actual voltage reading', action="store_true", default=False)
    args = vars(parser.parse_args())

    try:
        VERB = args["verbose"]
        T = Tenma72_2540(args["device"], debug=args["debug"])
        if not args["script"]:
            print("VERSION: ", T.getVersion())

        if args["ocp_enable"]:
            if VERB:
                print("Enable overcurrent protection")
            T.setOCP(True)

        if args["ocp_disable"]:
            if VERB:
                print("Disable overcurrent protection")
            T.setOCP(False)

        if args["ovp_enable"]:
            if VERB:
                print("Enable overvoltage protection")
            T.setOVP(True)

        if args["ovp_disable"]:
            if VERB:
                print("Disable overvoltage protection")
            T.setOVP(False)

        if args["safeC"]:
            if VERB:
                print("Setting safe current to ", args["safeC"])
            T.setSafeCurrent(args["safeC"])

        if args["safeV"]:
            if VERB:
                print("Setting safe voltage to ", args["safeV"])
            T.setSafeCurrent(args["safeV"])

        if args["voltage"]:
            if VERB:
                print("Setting voltage to ", args["voltage"])
            T.setVoltage(args["channel"], args["voltage"])

        if args["current"]:
            if VERB:
                print("Setting current to ", args["current"])
            T.setCurrent(args["channel"], args["current"])

        if args["save"]:
            if VERB:
                print("Saving to Memory", args["save"])

            T.saveConfFlow(args["save"], args["channel"])

        if args["recall"]:
            if VERB:
                print("Loading from Memory: ", args["recall"])

            T.recallConf(args["recall"])
            volt = T.readVoltage(args["channel"])
            curr = T.readCurrent(args["channel"])

            print("Loaded from Memory: ", args["recall"])
            print("Voltage:", volt)
            print("Current:", curr)

        if args["off"]:
            if VERB:
                print("Turning OUTPUT OFF")
            T.OFF()

        if args["safeOn"]:
            if VERB:
                print("Safely turning OUTPUT ON")
            T.safeON()

        if args["on"]:
            if VERB:
                print("Turning OUTPUT ON")
            T.ON()

        if args["status"]:
            if VERB:
                print("Retrieving status")
            print(T.getStatus())

        if args["actualCurrent"]:
            if VERB:
                print("Retrieving actual Current")
            print(T.runningCurrent(args["channel"]))

        if args["actualVoltage"]:
            if VERB:
                print("Retrieving actual Voltage")
            print(T.runningVoltage(args["channel"]))

    except TenmaException as e:
        print("Lib ERROR: ", repr(e))
    finally:
        if VERB:
            print("Closing connection")
        T.close()

if __name__ == "__main__":
    main()
