#    Copyright (C) 2017,2019,2020 Jordi Castells
#
#
#   this file is part of tenma-serial
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
    tenmaDcLib is small python library to control a Tenma 72-XXXX programmable
    DC power supply, either from USB or Serial.

    Supported models:

     * 72_2545 -> tested on HW
     * 72_2535 -> Set as manufacturer manual (not tested)
     * 72_2540 -> Set as manufacturer manual (not tested)
     * 72_2550 -> Tested on HW
     * 72_2930 -> Set as manufacturer manual (not tested)
     * 72_2940 -> Set as manufacturer manual (not tested)
     * 72_13320 -> Set as manufacturer manual (not tested)
     * 72_13330 -> Tested on HW

    Other units from Korad or Vellman might work as well since
    they use the same serial protocol.
"""

import serial
import time


class TenmaException(Exception):
    pass


def instantiate_tenma_class_from_device_response(device, debug=False):
    """
        Get a proper Tenma subclass depending on the version
        response from the unit.

        The subclasses mainly deal with the limit checks for each
        unit.
    """
    # First instantiate base to retrieve version
    T = Tenma72Base(device, debug=debug)
    ver = T.getVersion()
    if not ver:
        print("No version found, retrying with newline EOL")
        T.SERIAL_EOL = "\n"
        ver = T.getVersion()
    T.close()

    for cls in Tenma72Base.__subclasses__():
        for match_str in cls.MATCH_STR:
            if match_str in ver:
                return cls(device, debug)

    print("Could not detect Tenma Model, assuming 72_2545")
    return Tenma72_2545(device, debug)

class Tenma72Base(object):
    """
        Control a Tenma 72-XXXX DC bench power supply

        Defaults in this class assume a 72-2540, use
        subclasses for other models
    """
    MATCH_STR = [""]

    # 72Base sets some defaults. Subclasses should define
    # custom limits
    NCHANNELS = 1
    NCONFS = 5
    MAX_MA = 5000
    MAX_MV = 30000
    SERIAL_EOL = ""


    def __init__(self, serialPort, debug=False):
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)

        self.DEBUG = debug


    def setPort(self, serialPort):
        """
            Sets up the serial port with a new COM/tty device

            :param serialPort: COM/tty device
        """
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)


    def _sendCommand(self, command):
        """
            Sends a command to the serial port of a power supply

            :param command: Command to send
        """
        if self.DEBUG:
            print(">> ", command.strip())
        command = command + self.SERIAL_EOL
        self.ser.write(command.encode("ascii"))
        # Give it time to process
        time.sleep(0.2)


    def _readBytes(self):
        """
            Read serial output as a stream of bytes

            :return: Bytes read as a list of integers
        """
        out = []
        while self.ser.inWaiting() > 0:
            out.append(ord(self.ser.read(1)))

        if self.DEBUG:
            print("<< ", ["0x{:02x}".format(v) for v in out])

        return out


    def __readOutput(self):
        """
            Read serial otput as a string

            :return: Data read as a string
        """
        out = ""
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1).decode("ascii")

        if self.DEBUG:
            print("<< ", out.strip())

        return out


    def checkChannel(self, channel):
        """
            Checks that the given channel is valid for the power supply

            :param channel: Channel to check
            :raises TenmaException: If the channel is outside the range for the power supply
        """
        if channel > self.NCHANNELS:
            raise TenmaException("Channel CH{channel} not in range ({nch} channels supported)".format(
                channel=channel,
                nch=self.NCHANNELS
            ))


    def checkVoltage(self, channel, millivolts):
        """
            Checks that the given voltage is valid for the power supply

            :param channel: Channel to check
            :param millivolts: Voltage to check
            :raises TenmaException: If the voltage is outside the range for the power supply
        """
        if millivolts > self.MAX_MV:
            raise TenmaException("Trying to set CH{channel} voltage to {mv}mV, the maximum is {max}mV".format(
                channel=channel,
                mv=millivolts,
                max=self.MAX_MV
            ))


    def checkCurrent(self, channel, milliamps):
        """
            Checks that the given current is valid for the power supply

            :param channel: Channel to check
            :param milliamps: current to check
            :raises TenmaException: If the current is outside the range for the power supply
        """
        if milliamps > self.MAX_MA:
            raise TenmaException("Trying to set CH{channel} current to {ma}mA, the maximum is {max}mA".format(
                channel=channel,
                ma=milliamps,
                max=self.MAX_MA
            ))

    def getVersion(self, serialEol=""):
        """
            Returns a single string with the version of the Tenma Device and Protocol user

            :param serialEol: End of line terminator, defaults to ""
            :return: The version string from the power supply
        """
        self._sendCommand("*IDN?{}".format(serialEol))
        return self.__readOutput()

    def getStatus(self):
        """
            Returns the power supply status as a dictionary of values

            * ch1Mode: "C.V | C.C"
            * ch2Mode: "C.V | C.C"
            * tracking:
                * 00=Independent
                * 01=Tracking series
                * 11=Tracking parallel
            * BeepEnabled: True | False
            * lockEnabled: True | False
            * outEnabled: True | False

            :return: Dictionary of status values
        """
        self._sendCommand("STATUS?")
        statusBytes = self._readBytes()

        status = statusBytes[0]

        ch1mode = (status & 0x01)
        ch2mode = (status & 0x02)
        tracking = (status & 0x0C) >> 2
        beep = (status & 0x10)
        lock = (status & 0x20)
        out = (status & 0x40)

        if tracking == 0:
            tracking = "Independent"
        elif tracking == 1:
            tracking = "Tracking Series"
        elif tracking == 3:
            tracking = "Tracking Parallel"
        else:
            tracking = "Unknown"

        return {
            "ch1Mode": "C.V" if ch1mode else "C.C",
            "ch2Mode": "C.V" if ch2mode else "C.C",
            "Tracking": tracking,
            "BeepEnabled": bool(beep),
            "lockEnabled": bool(lock),
            "outEnabled": bool(out)
        }

    def readCurrent(self, channel):
        """
            Reads the current setting for the given channel

            :param channel: Channel to read the current of
            :return: Current for the channel in Amps as a float
        """
        self.checkChannel(channel)
        commandCheck = "ISET{}?".format(channel)
        self._sendCommand(commandCheck)
        # 72-2550 appends sixth byte from *IDN? to current reading due to firmware bug
        return float(self.__readOutput()[:5])

    def setCurrent(self, channel, milliamps):
        """
            Sets the current of the specified channel

            :param channel: Channel to set the current of
            :param milliamps: Current to set the channel to, in mA
            :raises TenmaException: If the current does not match what was set
            :return: The current the channel was set to in Amps as a float
        """
        self.checkChannel(channel)
        self.checkCurrent(channel, milliamps)

        A = float(milliamps) / 1000.0
        command = "ISET{channel}:{amperes:.3f}".format(channel=channel, amperes=A)

        self._sendCommand(command)
        readcurrent = self.readCurrent(channel)
        readMilliamps = int(readcurrent * 1000)

        if readMilliamps != milliamps:
            raise TenmaException("Set {milliamps}mA, but read {readMilliamps}mA".format(
                milliamps=milliamps,
                readMilliamps=readMilliamps
            ))
        return float(readcurrent)

    def readVoltage(self, channel):
        """
            Reads the voltage setting for the given channel

            :param channel: Channel to read the voltage of
            :return: Voltage for the channel in Volts as a float
        """
        self.checkChannel(channel)

        commandCheck = "VSET{}?".format(channel)
        self._sendCommand(commandCheck)
        return float(self.__readOutput())

    def setVoltage(self, channel, millivolts):
        """
            Sets the voltage of the specified channel

            :param channel: Channel to set the voltage of
            :param millivolts: voltage to set the channel to, in mV
            :raises TenmaException: If the voltage does not match what was set
            :return: The voltage the channel was set to in Volts as a float
        """
        self.checkChannel(channel)
        self.checkVoltage(channel, millivolts)

        volts = float(millivolts) / 1000.0
        command = "VSET{channel}:{volts:.2f}".format(channel=channel, volts=volts)

        self._sendCommand(command)
        readVolts = self.readVoltage(channel)
        readMillivolts = int(readVolts * 1000)

        if readMillivolts != int(millivolts):
            raise TenmaException("Set {millivolts}mV, but read {readMillivolts}mV".format(
                millivolts=millivolts,
                readMillivolts=readMillivolts
            ))
        return float(readVolts)

    def runningCurrent(self, channel):
        """
            Returns the current read of a running channel

            :param channel: Channel to get the running current for
            :return: The running current of the channel in Amps as a float
        """
        self.checkChannel(channel)

        command = "IOUT{}?".format(channel)
        self._sendCommand(command)
        return float(self.__readOutput())

    def runningVoltage(self, channel):
        """
            Returns the voltage read of a running channel

            :param channel: Channel to get the running voltage for
            :return: The running voltage of the channel in volts as a float
        """
        self.checkChannel(channel)

        command = "VOUT{}?".format(channel)
        self._sendCommand(command)
        return float(self.__readOutput())

    def saveConf(self, conf):
        """
            Save current configuration into Memory.

            Does not work as one would expect. SAV(4) will not save directly to memory 4.
            We actually need to recall memory 4, set configuration and then SAV(4)

            :param conf: Memory index to store to
            :raises TenmaException: If the memory index is outside the range
        """
        if conf > self.NCONFS:
            raise TenmaException("Trying to set M{conf} with only {nconf} slots".format(
                conf=conf,
                nconf=self.NCONFS
            ))

        command = "SAV{}".format(conf)
        self._sendCommand(command)

    def saveConfFlow(self, conf, channel):
        """
            Performs a full save flow for the unit.
            Since saveConf only calls the SAV<NR1> command, and that does not
            work as advertised, or expected, at least in 72_2540.

            This will:
             * turn off the output
             * Read the voltage that is set
             * recall memory conf
             * Save to that memory conf

            :param conf: Memory index to store to
            :param channel: Channel with output to store
        """

        self.OFF()

        # Read current voltage
        volt = self.readVoltage(channel)
        curr = self.readCurrent(channel)

        # Load conf (ensure we're on a the proper conf)
        self.recallConf(conf)

        # Load the new conf in the panel
        self.setVoltage(channel, volt * 1000)
        # Load the new conf in the panel
        self.setCurrent(channel, curr * 1000)

        self.saveConf(conf)   # Save current status in current memory

        if self.DEBUG:
            print("Saved to Memory", conf)
            print("Voltage:", volt)
            print("Current:", curr)

    def recallConf(self, conf):
        """
            Load existing configuration in Memory. Same as pressing any Mx button on the unit
        """

        if conf > self.NCONFS:
            raise TenmaException("Trying to recall M{conf} with only {nconf} confs".format(
                conf=conf,
                nconf=self.NCONFS
            ))
        self._sendCommand("RCL{}".format(conf))

    def setOCP(self, enable=True):
        """
            Enable or disable OCP.

            There's no feedback from the serial connection to determine
            whether OCP was set or not.

            :param enable: Boolean to enable or disable
        """
        enableFlag = 1 if enable else 0
        command = "OCP{}".format(enableFlag)
        self._sendCommand(command)


    def setOVP(self, enable=True):
        """
            Enable or disable OVP

            There's no feedback from the serial connection to determine
            whether OVP was set or not.

            :param enable: Boolean to enable or disable
        """
        enableFlag = 1 if enable else 0
        command = "OVP{}".format(enableFlag)
        self._sendCommand(command)


    def setBEEP(self, enable=True):
        """
            Enable or disable BEEP

            There's no feedback from the serial connection to determine
            whether BEEP was set or not.

            :param enable: Boolean to enable or disable
        """
        enableFlag = 1 if enable else 0
        command = "BEEP{}".format(enableFlag)
        self._sendCommand(command)


    def ON(self):
        """
            Turns on the output
        """
        command = "OUT1"
        self._sendCommand(command)


    def OFF(self):
        """
            Turns off the output
        """
        command = "OUT0"
        self._sendCommand(command)


    def close(self):
        """
            Closes the serial port
        """
        self.ser.close()

#
#
# Subclasses defining limits for each unit
# #\ :  Added for sphinx to pickup and document
# this constants
#
#
class Tenma72_2540(Tenma72Base):
    MATCH_STR = ["72-2540"]
    #:
    NCHANNELS = 1
    #: Only 4 physical buttons. But 5 memories are available
    NCONFS = 5
    #:
    MAX_MA = 5000
    #:
    MAX_MV = 30000


class Tenma72_2535(Tenma72Base):
    #:
    MATCH_STR = ["72-2535"]
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 3000
    #:
    MAX_MV = 30000

class Tenma72_2545(Tenma72Base):
    #:
    MATCH_STR = ["72-2545"]
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 2000
    #:
    MAX_MV = 60000

class Tenma72_2550(Tenma72Base):
    #: The 72-2550 we have identifies itself as a Korad KA 6003P internally
    MATCH_STR = ["72-2550", "KORADKA6003P"]
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 3000
    #:
    MAX_MV = 60000

class Tenma72_2930(Tenma72Base):
    #:
    MATCH_STR = ["72-2930"]
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 10000
    #:
    MAX_MV = 30000


class Tenma72_2940(Tenma72Base):
    #:
    MATCH_STR = ["72-2940"]
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 5000
    #:
    MAX_MV = 60000

class Tenma72_13330(Tenma72Base):
    #:
    MATCH_STR = ['72-13330']
    #:
    NCHANNELS = 3
    #:
    NCONFS = 0
    #:
    MAX_MA = 5000
    #:
    MAX_MV = 30000
    #:
    SERIAL_EOL = "\n"
