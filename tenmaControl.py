"""
    @author Jordi Castells
    Command line tenma control program for Tenma72_2540
"""

import argparse
from tenmaDcLib import *

parser = argparse.ArgumentParser(description='Control a Tenma 72-2540 power supply connected to a serial port')
parser.add_argument('device', default="/dev/ttyUSB0")
parser.add_argument('-v','--voltage', help='mV to set', required=False, type=int)
parser.add_argument('-c','--current', help='mA to set', required=False, type=int)
parser.add_argument('-s','--save', help='Save current configuration to Memory', required=False, type=int)
parser.add_argument('-r','--recall', help='Load configuration from Memory', required=False, type=int)
parser.add_argument('--on', help='Set output to ON', action="store_true", default=False)
parser.add_argument('--off', help='Set output to OFF', action="store_true", default=False)
parser.add_argument('--verbose', help='Chatty program', action="store_true", default=False)
parser.add_argument('--debug', help='print serial commands', action="store_true", default=False)
args = vars(parser.parse_args())

try:
    VERB = args["verbose"]
    T = Tenma72_2540(args["device"], debug=args["debug"])
    print "VERSION: ",T.getVersion()

    if args["voltage"]:
        if VERB:
            print "Setting voltage to ", args["voltage"]
        T.setVoltage(1, args["voltage"])

    if args["current"]:
        if VERB:
            print "Setting current to ", args["current"]
        T.setCurrent(1, args["current"])

    if args["save"]:
        if VERB:
            print "Saving to Memory", args["save"]

        T.saveConf( args["save"])
        volt = T.readVoltage(1)
        curr = T.readCurrent(1)

        print "Saved to Memory", args["save"]
        print "Voltage:", volt
        print "Current:", curr

    if args["recall"]:
        if VERB:
            print "Loading from Memory: ", args["recall"]

        T.recallConf(args["recall"])
        volt = T.readVoltage(1)
        curr = T.readCurrent(1)

        print "Loaded from Memory: ", args["recall"]
        print "Voltage:", volt
        print "Current:", curr


    if args["on"]:
        if VERB:
            print "Turning OUTPUT ON"
        T.ON()

    if args["off"]:
        if VERB:
            print "Turning OUTPUT OFF"
        T.OFF()

except TenmaException as e:
    print "Lib ERROR: ", repr(e)
except Exception as e:
    print "ERROR: ", repr(e)
finally:
    if VERB:
        print "Closing connection"
    T.close()
