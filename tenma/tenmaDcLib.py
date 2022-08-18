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
     * 72_2550 -> Set as manufacturer manual (not tested)
     * 72_2930 -> Set as manufacturer manual (not tested)
     * 72_2940 -> Set as manufacturer manual (not tested)

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
        Control a tenma 72-XXXX DC bench power supply

        Defaults in this class assume a 72-2540, use
        subclasses for other models
    """
    MATCH_STR = ['']

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
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)

    def __sendCommand(self, command):
        if self.DEBUG:
            print(">> ", command)
        command = command + self.SERIAL_EOL
        self.ser.write(command.encode('ascii'))
        # Give it time to process
        time.sleep(0.2)

    def __readBytes(self):
        """
            Read serial output as a stream of bytes
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
        """
        out = ""
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1).decode('ascii')

        if self.DEBUG:
            print("<< ", out)

        return out

    def getVersion(self):
        """
            Returns a single string with the version of the Tenma Device and Protocol user
        """
        self.__sendCommand("*IDN?")
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
        """
        self.__sendCommand("STATUS?")
        statusBytes = self.__readBytes()

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
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to read CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
            ))

        commandCheck = "ISET{channel}?".format(channel=1)
        self.__sendCommand(commandCheck)
        return float(self.__readOutput()[:5]) # 72-2550 appends sixth byte from *IDN? to current reading due to firmware bug

    def setCurrent(self, channel, mA):
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to set CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
            ))

        if mA > self.MAX_MA:
            raise TenmaException("Trying to set CH{channel} to {ma}mA, the maximum is {max}mA".format(
                channel=channel,
                ma=mA,
                max=self.MAX_MA
            ))

        command = "ISET{channel}:{amperes:.3f}"

        A = float(mA) / 1000.0
        command = command.format(channel=1, amperes=A)

        self.__sendCommand(command)
        readcurrent = self.readCurrent(channel)

        if int(readcurrent * 1000) != mA:
            raise TenmaException("Set {set}mA, but read {read}mA".format(
                set=mA,
                read=readcurrent * 1000,
            ))

    def readVoltage(self, channel):
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to read CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
            ))

        commandCheck = "VSET{channel}?".format(channel=1)
        self.__sendCommand(commandCheck)
        return float(self.__readOutput())

    def setVoltage(self, channel, mV):
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to set CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
            ))

        if mV > self.MAX_MV:
            raise TenmaException("Trying to set CH{channel} to {mv}mV, the maximum is {max}mV".format(
                channel=channel,
                mv=mV,
                max=self.MAX_MV
            ))

        command = "VSET{channel}:{volt:.2f}"

        V = float(mV) / 1000.0
        command = command.format(channel=1, volt=V)

        self.__sendCommand(command)
        readvolt = self.readVoltage(channel)

        if int(readvolt * 1000) != int(mV):
            raise TenmaException("Set {set}mV, but read {read}mV".format(
                set=mV,
                read=readvolt * 1000,
            ))

    def runningCurrent(self, channel):
        """
            Returns the current read of a running channel
        """
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to read CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
            ))

        command = "IOUT{channel}?".format(channel=channel)
        self.__sendCommand(command)
        readcurrent = self.__readOutput()
        return readcurrent

    def runningVoltage(self, channel):
        """
            Returns the voltage read of a running channel
        """
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to read CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
            ))

        command = "VOUT{channel}?".format(channel=channel)
        self.__sendCommand(command)
        readvolt = self.__readOutput()
        return readvolt

    def saveConf(self, conf):
        """
            Save current configuration into Memory.

            Does not work as one would expect. SAV(4) will not save directly to memory 4.
            We actually need to recall memory 4, set configuration and then SAV(4)
        """
        if conf > self.NCONFS:
            raise TenmaException("Trying to set M{channel} with only {nch} confs".format(
                channel=conf,
                nch=self.NCONFS
            ))

        command = "SAV{conf}".format(conf=conf)
        self.__sendCommand(command)

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
            raise TenmaException("Trying to recall M{channel} with only {nch} confs".format(
                channel=conf,
                nch=self.NCONFS
            ))

        command = "RCL{conf}".format(conf=conf)
        self.__sendCommand(command)

    def setOCP(self, enable=True):
        """
            Enable or disable OCP.

            There's no feedback from the serial connection to determine
            whether OCP was set or not.

            :param enable: Boolean to enable or disable
        """
        conf = 1 if enable else 0
        command = "OCP{conf}".format(conf=conf)
        self.__sendCommand(command)

    def setOVP(self, enable=True):
        """
            Enable or disable OVP

            There's no feedback from the serial connection to determine
            whether OVP was set or not.

            :param enable: Boolean to enable or disable
        """
        conf = 1 if enable else 0
        command = "OVP{conf}".format(conf=conf)
        self.__sendCommand(command)

    def setBEEP(self, enable=True):
        """
            Enable or disable BEEP

            There's no feedback from the serial connection to determine
            whether BEEP was set or not.

            :param enable: Boolean to enable or disable
        """
        conf = 1 if enable else 0
        command = "BEEP{conf}".format(conf=conf)
        self.__sendCommand(command)


    def ON(self):
        """
            Turns on the output
        """

        command = "OUT1"
        self.__sendCommand(command)

    def OFF(self):
        """
            Turns OFF the output
        """

        command = "OUT0"
        self.__sendCommand(command)

    def close(self):
        self.ser.close()

#
#
# Subclasses defining limits for each unit
# #\ :  Added for sphinx to pickup and document
# this constants
#
#
class Tenma72_2540(Tenma72Base):
    MATCH_STR = ['72-2540']
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
    MATCH_STR = ['72-2535']
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
    MATCH_STR = ['72-2545']
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 2000
    #:
    MAX_MV = 60000

class Tenma72_2550(Tenma72Base):
    #:
    MATCH_STR = ['72-2550', 'KORADKA6003P']
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
    MATCH_STR = ['72-2930']
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
    MATCH_STR = ['72-2940']
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
