#    Copyright (C) 2017-2023 Jordi Castells
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

     * 72_2545 -> Tested on HW
     * 72_2535 -> Set as manufacturer manual (not tested)
     * 72_2540 -> Tested on HW
     * 72_2550 -> Tested on HW
     * 72-2705 -> Tested on HW
     * 72_2930 -> Set as manufacturer manual (not tested)
     * 72_2940 -> Set as manufacturer manual (not tested)
     * 72_13320 -> Set as manufacturer manual (not tested)
     * 72_13330 -> Tested on HW
     * 72_13360 -> Tested on HW

    Other units from Korad or Vellman might work as well since
    they use the same serial protocol.
"""

import time

import serial


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
    powerSupply = Tenma72Base(device, debug=debug)
    ver = powerSupply.getVersion()
    if not ver:
        if debug:
            print("No version found, retrying with newline EOL")
        ver = powerSupply.getVersion(serialEol="\n")
    powerSupply.close()

    for cls in findSubclassesRecursively(Tenma72Base):
        for matchString in cls.MATCH_STR:
            if matchString in ver:
                return cls(device, debug=debug)

    print("Could not detect Tenma power supply model, assuming 72_2545")
    return Tenma72_2545(device, debug=debug)


def findSubclassesRecursively(cls):
    """
        Finds all subclasses of a given class recursively
    """
    all_subclasses = []
    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(findSubclassesRecursively(subclass))
    return all_subclasses


class TenmaSerialHandler(object):
    """
    A small class that handles serial communication for tenma power supplies.
    """

    def __init__(self, serialPort, serialEOL, debug=False):
        """
            :param serialPort: COM/tty device
            :type serialPort: string
            :param serialEOL: COM/tty device
            :type serialPort: string
        """
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)
        self.SERIAL_EOL = serialEOL

        self.DEBUG = debug

    def setPort(self, serialPort):
        """
            Sets up the serial port with a new COM/tty device

            :param serialPort: COM/tty device
            :type serialPort: string
        """
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)

    def _sendCommand(self, command):
        """
            Sends a command to the serial port of a power supply

            :param command: Command to send
            :type command: string
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

    def _readOutput(self):
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

    def close(self):
        """
            Closes the serial port
        """
        self.ser.close()


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

    def __init__(self, serialPort, debug=False):
        SERIAL_EOL = ""
        self.serialHandler = TenmaSerialHandler(serialPort, SERIAL_EOL, debug=debug)
        self.DEBUG = debug

    def setPort(self, serialPort):
        """
            Sets up the serial port with a new COM/tty device

            :param serialPort: COM/tty device
            :type serialPort: string
        """
        self.serialHandler.setPort(serialPort)

    def _sendCommand(self, command):
        """
            Sends a command to the serial port of a power supply

            :param command: Command to send
            :type command: Command to send
        """
        self.serialHandler._sendCommand(command)

    def _readBytes(self):
        """
            Read serial output as a stream of bytes

            :return: Bytes read as a list of integers
        """
        return self.serialHandler._readBytes()

    def __readOutput(self):
        """
            Read serial otput as a string

            :return: Data read as a string
        """
        return self.serialHandler._readOutput()

    def close(self):
        """
            Closes the serial port
        """
        self.serialHandler.close()

    def checkChannel(self, channel):
        """
            Checks that the given channel is valid for the power supply

            :param channel: Channel to check
            :type channel: int
            :raises TenmaException: If the channel is outside the range for the power supply
        """
        channel = int(channel)
        if channel > self.NCHANNELS or channel < 1:
            raise TenmaException(
                "Channel CH{channel} not in range ({nch} channels supported)".format(
                    channel=channel,
                    nch=self.NCHANNELS))

    def checkVoltage(self, channel, mV):
        """
            Checks that the given voltage is valid for the power supply

            :param channel: Channel to check
            :type channel: int
            :param mV: Voltage to check
            :type mV: int
            :raises TenmaException: If the voltage is outside the range for the power supply
        """
        mV = int(mV)
        if mV > self.MAX_MV or mV < 0:
            raise TenmaException(
                "Trying to set CH{channel} voltage to {mv}mV, the maximum is {max}mV".format(
                    channel=channel,
                    mv=mV,
                    max=self.MAX_MV))

    def checkCurrent(self, channel, mA):
        """
            Checks that the given current is valid for the power supply

            :param channel: Channel to check
            :type channel: int
            :param mA: current to check
            :type mA: int
            :raises TenmaException: If the current is outside the range for the power supply
        """
        mA = int(mA)
        if mA > self.MAX_MA or mA < 0:
            raise TenmaException(
                "Trying to set CH{channel} current to {ma}mA, the maximum is {max}mA".format(
                    channel=channel,
                    ma=mA,
                    max=self.MAX_MA))

    def checkConf(self, conf):
        """
            Checks that the given Memory slot is valid for the power supply

            :param conf: Memory slot to check
            :ptype conf: int
            :raises TenmaException: If the Memory slot is outside the range for the power supply
        """
        conf = int(conf)
        if conf > self.NCONFS or conf < 1:
            raise TenmaException("Trying to use slot M{conf} with only {nconf} slots".format(
                conf=conf,
                nconf=self.NCONFS
            ))

    def getVersion(self, serialEol=""):
        """
            Returns a single string with the version of the Tenma Device and Protocol user

            TODO: Get version probably does not need serialEOL since now we use a specific
            serialHandler per class and the instantiate_function (the only one using it)
            can use `getVersion` from each specific class.

            :param serialEol: End of line terminator, defaults to ""
            :type serialEol: string
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

    def setCurrent(self, channel, mA):
        """
            Sets the current of the specified channel

            :param channel: Channel to set the current of
            :type channel: int
            :param mA: Current to set the channel to, in mA
            :type mA: int
            :raises TenmaException: If the current does not match what was set
            :return: The current the channel was set to in Amps as a float
        """
        self.checkChannel(channel)
        self.checkCurrent(channel, mA)

        A = float(mA) / 1000.0
        command = "ISET{channel}:{amperes:.3f}".format(channel=channel, amperes=A)

        self._sendCommand(command)
        readcurrent = self.readCurrent(channel)
        readMilliamps = int(readcurrent * 1000)

        if readMilliamps != mA:
            raise TenmaException("Set {mA}mA, but read {readMilliamps}mA".format(
                mA=mA,
                readMilliamps=readMilliamps
            ))
        return float(readcurrent)

    def readVoltage(self, channel):
        """
            Reads the voltage setting for the given channel

            :param channel: Channel to read the voltage of
            :type channel: int
            :return: Voltage for the channel in Volts as a float
        """
        self.checkChannel(channel)

        commandCheck = "VSET{}?".format(channel)
        self._sendCommand(commandCheck)
        return float(self.__readOutput())

    def setVoltage(self, channel, mV):
        """
            Sets the voltage of the specified channel

            :param channel: Channel to set the voltage of
            :type channel: int
            :param mV: voltage to set the channel to, in mV
            :type mV: int
            :raises TenmaException: If the voltage does not match what was set
            :return: The voltage the channel was set to in Volts as a float
        """
        self.checkChannel(channel)
        self.checkVoltage(channel, mV)

        volts = float(mV) / 1000.0
        command = "VSET{channel}:{volts:.2f}".format(channel=channel, volts=volts)

        self._sendCommand(command)
        readVolts = self.readVoltage(channel)
        readMillivolts = int(readVolts * 1000)

        if readMillivolts != int(mV):
            raise TenmaException("Set {mV}mV, but read {readMillivolts}mV".format(
                mV=mV,
                readMillivolts=readMillivolts
            ))
        return float(readVolts)

    def runningCurrent(self, channel):
        """
            Returns the current read of a running channel

            :param channel: Channel to get the running current for
            :type channel: int
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
            :type channel: int
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
            :type conf: int
            :raises TenmaException: If the memory index is outside the range
        """
        self.checkConf(conf)
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
            :type conf: int
            :param channel: Channel with output to store
            :type channel: int
        """
        self.checkConf(conf)
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

            :param conf: Memory index to recall
            :type conf: int
        """
        self.checkConf(conf)
        self._sendCommand("RCL{}".format(conf))

    def setOCP(self, enable=True):
        """
            Enable or disable OCP.

            There's no feedback from the serial connection to determine
            whether OCP was set or not.

            :param enable: Boolean to enable or disable
            :type enable: boolean
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
            :type enable: boolean
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
            :type enable: boolean
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

    def setLock(self, enable=True):
        """
            Set the front-panel lock on or off

            :param enable: Enable lock, defaults to True
            :type enable: boolean
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def setTracking(self, trackingMode):
        """
            Sets the tracking mode of the power supply outputs

            :param trackingMode: Tracking mode
            :type trackingMode: boolean
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def startAutoVoltageStep(self, channel, startMillivolts,
                             stopMillivolts, stepMillivolts, stepTime):
        """
            Starts an automatic voltage step from Start mV to Stop mV,
            incrementing by Step mV every Time seconds

            :param channel: Channel to start voltage step on
            :type channel: int
            :param startMillivolts: Starting voltage in mV
            :type startMillivolts: int
            :param stopMillivolts: End voltage in mV
            :type stopMillivolts: int
            :param stepMillivolts: Amount to increase voltage by in mV
            :type stepMillivolts: int
            :param stepTime: Time to wait before each increase, in Seconds
            :type stepTime: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def stopAutoVoltageStep(self, channel):
        """
            Stops the auto voltage step on the specified channel

            :param channel: Channel to stop the auto voltage step on
            :type channel: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def startAutoCurrentStep(self, channel, startMilliamps,
                             stopMilliamps, stepMilliamps, stepTime):
        """
            Starts an automatic current step from Start mA to Stop mA,
            incrementing by Step mA every Time seconds

            :param channel: Channel to start current step on
            :type channel: int
            :param startMilliamps: Starting current in mA
            :type statMilliamps: int
            :param stopMilliamps: End current in mA
            :type stopMilliamps: int
            :param stepMilliamps: Amount to increase current by in mA
            :type stepMilliamps: int
            :param stepTime: Time to wait before each increase, in Seconds
            :type stepTime: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def stopAutoCurrentStep(self, channel):
        """
            Stops the auto current step on the specified channel

            :param channel: Channel to stop the auto current step on
            :type channel: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def setManualVoltageStep(self, channel, stepMillivolts):
        """
            Sets the manual step voltage of the channel
            When a VUP or VDOWN command is sent to the power supply channel, that channel
            will step up or down by stepMillivolts mV

            :param channel: Channel to set the step voltage for
            :type channel: int
            :param stepMillivolts: Voltage to step up or down by when triggered
            :type stepMillivolts: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def stepVoltageUp(self, channel):
        """
            Increse the voltage by the configured step voltage on the specified channel
            Call "setManualVoltageStep" to set the step voltage

            :param channel: Channel to increase the voltage for
            :type channel: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def stepVoltageDown(self, channel):
        """
            Decrese the voltage by the configured step voltage on the specified channel
            Call "setManualVoltageStep" to set the step voltage

            :param channel: Channel to decrease the voltage for
            :type channel: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def setManualCurrentStep(self, channel, stepMilliamps):
        """
            Sets the manual step current of the channel
            When a IUP or IDOWN command is sent to the power supply channel, that channel
            will step up or down by stepMilliamps mA

            :param channel: Channel to set the step current for
            :type channel: int
            :param stepMilliamps: Current to step up or down by when triggered
            :type stepMilliamps: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def stepCurrentUp(self, channel):
        """
            Increse the current by the configured step current on the specified channel
            Call "setManualCurrentStep" to set the step current

            :param channel: Channel to increase the current for
            :type channel: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")

    def stepCurrentDown(self, channel):
        """
            Decrese the current by the configured step current on the specified channel
            Call "setManualCurrentStep" to set the step current

            :param channel: Channel to decrease the current for
            :type channel: int
            :raises NotImplementedError Not implemented in this base class
        """
        raise NotImplementedError("Not supported by all models")


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
    MAX_MA = 5100
    #:
    MAX_MV = 31000


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
    #: Tenma 72-2550 is also manufactured as Korad KA 6003P
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


class Tenma72_2705(Tenma72Base):
    #:
    MATCH_STR = ["72-2705"]
    #:
    NCHANNELS = 1
    #:
    NCONFS = 5
    #:
    MAX_MA = 3100
    #:
    MAX_MV = 31000


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


class Tenma72_13320(Tenma72Base):
    #:
    MATCH_STR = ["72-13320"]
    #:
    NCHANNELS = 3
    #: This unit does actually support 10 slots (0-9) but it's not avialable from the front panel
    NCONFS = 0
    #:
    MAX_MA = 3000
    #:
    MAX_MV = 30000

    def __init__(self, serialPort, debug=False):
        SERIAL_EOL = "\n"
        self.serialHandler = TenmaSerialHandler(serialPort, SERIAL_EOL, debug=debug)
        self.DEBUG = debug

    def getStatus(self):
        """
            Returns the power supply status as a dictionary of values

            * ch1Mode: "C.V | C.C"
            * ch2Mode: "C.V | C.C"
            * tracking:
                * 00=Independent
                * 01=Tracking series
                * 10=Tracking parallel
            * out1Enabled: True | False
            * out2Enabled: True | False

            :return: Dictionary of status values
        """
        self._sendCommand("STATUS?")
        statusBytes = self._readBytes()

        # 72-13330 sends two bytes back, the second being '\n'
        status = statusBytes[0]

        ch1mode = (status & 0x01)
        ch2mode = (status & 0x02)
        tracking = (status & 0x0C) >> 2
        out1 = (status & 0x40)
        out2 = (status & 0x80)

        if tracking == 0:
            tracking = "Independent"
        elif tracking == 1:
            tracking = "Tracking Series"
        elif tracking == 2:
            tracking = "Tracking Parallel"
        else:
            tracking = "Unknown"

        return {
            "ch1Mode": "C.V" if ch1mode else "C.C",
            "ch2Mode": "C.V" if ch2mode else "C.C",
            "Tracking": tracking,
            "out1Enabled": bool(out1),
            "out2Enabled": bool(out2)
        }

    def readCurrent(self, channel):
        """
            Reads the current setting for the given channel

            :param channel: Channel to read the current of
            :type channel: iint
            :return: Current for the channel in Amps as a float
            :raises TenmaException: If trying to read the current of Channel 3
        """
        if channel == 3:
            raise TenmaException("Channel CH3 does not support reading current")
        return super().readCurrent(channel)

    def runningCurrent(self, channel):
        """
            Returns the current read of a running channel

            :param channel: Channel to get the running current for
            :type channel: iint
            :return: The running current of the channel in Amps as a float

            :raises TenmaException: If trying to read the current of Channel 3
        """
        if channel == 3:
            raise TenmaException("Channel CH3 does not support reading current")
        return super().runningCurrent(channel)

    def setVoltage(self, channel, mV):
        """
            Sets the voltage of the specified channel

            :param channel: Channel to set the voltage of
            :type channel: int
            :param mV: voltage to set the channel to, in mV
            :type mV: int
            :return: The voltage the channel was set to in Volts as a float

            :raises TenmaException: If the voltage does not match what was set,
            or if trying to set an invalid voltage on Channel 3
        """
        if channel == 3 and mV not in [2500, 3300, 5000]:
            raise TenmaException("Channel CH3 can only be set to 2500mV, 3300mV or 5000mV")
        return super().setVoltage(channel, mV)

    def setOCP(self, enable=True):
        """
            Enable or disable OCP.

            There's no feedback from the serial connection to determine
            whether OCP was set or not.

            :param enable: Boolean to enable or disable
            :type enable: boolean
            :raises NotImplementedError: This model doesn't support OCP
        """
        raise NotImplementedError("This model does not support OCP")

    def setOVP(self, enable=True):
        """
            Enable or disable OVP

            There's no feedback from the serial connection to determine
            whether OVP was set or not.

            :param enable: Boolean to enable or disable
            :type enable: boolean
            :raises NotImplementedError: This model doesn't support OVP
        """
        raise NotImplementedError("This model does not support OVP")

    def ON(self, channel=None):
        """
            Turns on the output(s)

            :param channel: Channel to turn on, defaults to None (turn all channels on)
            :type channel: int
        """
        if channel is None:
            command = "OUT12:1"
        else:
            self.checkChannel(channel)
            command = "OUT{}:1".format(channel)

        self._sendCommand(command)

    def OFF(self, channel=None):
        """
            Turns off the output(s)

            :param channel: Channel to turn on, defaults to None (turn all channels off)
            :type channel: int
        """
        if channel is None:
            command = "OUT12:0"
        else:
            self.checkChannel(channel)
            command = "OUT{}:0".format(channel)
        self._sendCommand(command)

    def setLock(self, enable=True):
        """
            Set the front-panel lock on or off

            :param enable: Enable lock, defaults to True
            :type enable: boolean
        """
        enableFlag = 1 if enable else 0
        self._sendCommand("LOCK{}".format(enableFlag))

    def setTracking(self, trackingMode):
        """
            Sets the tracking mode of the power supply outputs
            0: Independent
            1: Series
            2: Parallel

            :param trackingMode: one of 0, 1 or 2
            :type trackingMode: int
            :raises TenmaException: If a tracking mode other than 0, 1 or 2 is specified
        """
        if trackingMode not in [0, 1, 2]:
            raise TenmaException(
                ("Tracking mode {} not valid. Use one of:"
                 " 0 (Independent), 1 (Series), 2 (Parallel)").format(trackingMode))
        self._sendCommand("TRACK{}".format(trackingMode))

    def startAutoVoltageStep(self, channel, startMillivolts,
                             stopMillivolts, stepMillivolts, stepTime):
        """
            Starts an automatic voltage step from Start mV to Stop mV,
            incrementing by Step mV every Time seconds

            :param channel: Channel to start voltage step on
            :type channel: int
            :param startMillivolts: Starting voltage in mV
            :type startMillivolts: int
            :param stopMillivolts: End voltage in mV
            :type stopMillivolts: int
            :param stepMillivolts: Amount to increase voltage by in mV
            :type stepMillivolts: int
            :param stepTime: Time to wait before each increase, in Seconds
            :type stepTime: int
            :raises TenmaException: If the channel or voltage is invalid
        """
        self.checkChannel(channel)
        self.checkVoltage(channel, stopMillivolts)
        # TODO: improve this check for when we're stepping down in voltage
        if stepMillivolts > stopMillivolts:
            raise TenmaException(
                ("Channel CH{channel} step voltage {stepMillivolts}V"
                 " higher than stop voltage {stopMillivolts}V").format(
                    channel=channel,
                    stepMillivolts=stepMillivolts,
                    stopMillivolts=stopMillivolts))

        startVolts = float(startMillivolts) / 1000.0
        stopVolts = float(stopMillivolts) / 1000.0
        stepVolts = float(stepMillivolts) / 1000.0

        command = "VASTEP{channel}:{startVolts},{stopVolts},{stepVolts},{stepTime}".format(
            channel=channel,
            startVolts=startVolts,
            stopVolts=stopVolts,
            stepVolts=stepVolts,
            stepTime=stepTime
        )
        self._sendCommand(command)

    def stopAutoVoltageStep(self, channel):
        """
            Stops the auto voltage step on the specified channel

            :param channel: Channel to stop the auto voltage step on
            :type channel: int
        """
        self.checkChannel(channel)
        self._sendCommand("VASTOP{}".format(channel))

    def startAutoCurrentStep(self, channel, startMilliamps,
                             stopMilliamps, stepMilliamps, stepTime):
        """
            Starts an automatic current step from Start mA to Stop mA,
            incrementing by Step mA every Time seconds

            :param channel: Channel to start current step on
            :type channel: int
            :param startMilliamps: Starting current in mA
            :type startMilliamps: int
            :param stopMilliamps: End current in mA
            :type stopMilliamps: int
            :param stepMilliamps: Amount to increase current by in mA
            :type stepMilliamps: int
            :param stepTime: Time to wait before each increase, in Seconds
            :type stepTime: int
            :raises TenmaException: If the channel or current is invalid
        """
        self.checkChannel(channel)
        self.checkCurrent(channel, stopMilliamps)
        if stepMilliamps > stopMilliamps:
            raise TenmaException(
                ("Channel CH{channel} step current {stepMilliamps}mA higher"
                 " than stop current {stopMilliamps}mA").format(
                    channel=channel,
                    stepMilliamps=stepMilliamps,
                    stopMilliamps=stopMilliamps))

        startAmps = float(startMilliamps) / 1000.0
        stopAmps = float(stopMilliamps) / 1000.0
        stepAmps = float(stepMilliamps) / 1000.0

        command = "IASTEP{channel}:{startAmps},{stopAmps},{stepAmps},{stepTime}".format(
            channel=channel,
            startAmps=startAmps,
            stopAmps=stopAmps,
            stepAmps=stepAmps,
            stepTime=stepTime
        )
        self._sendCommand(command)

    def stopAutoCurrentStep(self, channel):
        """
            Stops the auto current step on the specified channel

            :param channel: Channel to stop the auto current step on
            :type channel: int
        """
        self.checkChannel(channel)
        self._sendCommand("IASTOP{}".format(channel))

    def setManualVoltageStep(self, channel, stepMillivolts):
        """
            Sets the manual step voltage of the channel
            When a VUP or VDOWN command is sent to the power supply channel, that channel
            will step up or down by stepMillivolts mV

            :param channel: Channel to set the step voltage for
            :type channel: int
            :param stepMillivolts: Voltage to step up or down by when triggered
            :type stepMillivolts: int
        """
        self.checkChannel(channel)
        self.checkVoltage(channel, stepMillivolts)
        stepVolts = float(stepMillivolts) / 1000.0
        command = "VSTEP{}:{}".format(channel, stepVolts)
        self._sendCommand(command)

    def stepVoltageUp(self, channel):
        """
            Increse the voltage by the configured step voltage on the specified channel
            Call "setManualVoltageStep" to set the step voltage

            :param channel: Channel to increase the voltage for
            :type channel: int
        """
        self.checkChannel(channel)
        self._sendCommand("VUP{}".format(channel))

    def stepVoltageDown(self, channel):
        """
            Decrese the voltage by the configured step voltage on the specified channel
            Call "setManualVoltageStep" to set the step voltage

            :param channel: Channel to decrease the voltage for
            :type channel: int
        """
        self.checkChannel(channel)
        self._sendCommand("VDOWN{}".format(channel))

    def setManualCurrentStep(self, channel, stepMilliamps):
        """
            Sets the manual step current of the channel
            When a IUP or IDOWN command is sent to the power supply channel, that channel
            will step up or down by stepMilliamps mA

            :param channel: Channel to set the step current for
            :type channel: int
            :param stepMilliamps: Current to step up or down by when triggered
            :type stepMilliamps: int
        """
        self.checkChannel(channel)
        self.checkCurrent(channel, stepMilliamps)
        stepAmps = float(stepMilliamps) / 1000.0
        command = "ISTEP{}:{}".format(channel, stepAmps)
        self._sendCommand(command)

    def stepCurrentUp(self, channel):
        """
            Increse the current by the configured step current on the specified channel
            Call "setManualCurrentStep" to set the step current

            :param channel: Channel to increase the current for
            :type channel: int
        """
        self.checkChannel(channel)
        self._sendCommand("IUP{}".format(channel))

    def stepCurrentDown(self, channel):
        """
            Decrese the current by the configured step current on the specified channel
            Call "setManualCurrentStep" to set the step current

            :param channel: Channel to decrease the current for
            :type channel: int
        """
        self.checkChannel(channel)
        self._sendCommand("IDOWN{}".format(channel))


class Tenma72_13330(Tenma72_13320):
    #:
    MATCH_STR = ["72-13330"]
    #:
    NCHANNELS = 3
    #: This unit does actually support 10 slots (0-9) but it's not avialable from the front panel
    NCONFS = 0
    #:
    MAX_MA = 5000
    #:
    MAX_MV = 30000


class Tenma72_13360_base(object):
    """
        Tenma 72-13360 single channel programmable PSU
        This PSU uses the RS485 protocol and only supports a single channel.
        That means that the channel is never specified in the message to the PSU.
        Because of this, the channel parameter removed from all methods.

        It also has other slight variations in protocol such as a ":" separator and the
        STATUS? command returning more general settings.
    """

    NCONFS = 5
    MAX_MA = 15000
    MAX_MV = 60000
    SERIAL_SETTER_SEPARATOR = ":"

    def __init__(self, serialPort, debug=False):
        SERIAL_EOL = "\n"
        self.serialHandler = TenmaSerialHandler(serialPort, SERIAL_EOL, debug=debug)

        self.DEBUG = debug

    def setPort(self, serialPort):
        """
            Sets up the serial port with a new COM/tty device

            :param serialPort: COM/tty device
        """
        self.serialHandler.setPort(serialPort)

    def _sendCommand(self, command):
        """
            Sends a command to the serial port of a power supply

            :param command: Command to send
        """
        self.serialHandler._sendCommand(command)

    def _readBytes(self):
        """
            Read serial output as a stream of bytes

            :return: Bytes read as a list of integers
        """
        return self.serialHandler._readBytes()

    def __readOutput(self):
        """
            Read serial otput as a string

            :return: Data read as a string
        """
        return self.serialHandler._readOutput()

    def close(self):
        """
            Closes the serial port
        """
        self.serialHandler.close()

    def checkVoltage(self, mV):
        """
            Checks that the given voltage is valid for the power supply

            :param mV: Voltage to check
            :raises TenmaException: If the voltage is outside the range for the power supply
        """
        mV = int(mV)
        if mV > self.MAX_MV or mV < 0:
            raise TenmaException(
                "Trying to set voltage to {mv}mV, the maximum is {max}mV".format(
                    mv=mV,
                    max=self.MAX_MV))

    def checkCurrent(self, mA):
        """
            Checks that the given current is valid for the power supply

            :param mA: current to check
            :raises TenmaException: If the current is outside the range for the power supply
        """
        mA = int(mA)
        if mA > self.MAX_MA or mA < 0:
            raise TenmaException(
                "Trying to set current to {ma}mA, the maximum is {max}mA".format(
                    ma=mA,
                    max=self.MAX_MA))

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

            "channelMode ": "C.V" or "C.C",
            "output ": "ON" or "OFF",
            "V/C priority ": "Current priority" or "Voltage priority",
            "beep ": "ON" or "OFF",
            "lock ": "ON" or "OFF",

            :return: Dictionary of status values
        """
        self._sendCommand("STATUS?")
        statusBytes = self._readBytes()

        # 72-13360 sends two bytes back, the second being '\n'
        status = statusBytes[0]

        ch1mode = (status & 0b00000001)
        output = (status & 0b00000010)
        current_priority = (status & 0b00000100)
        beep = (status & 0b00010000)
        lock = (status & 0b00100000)

        return {
            "channelMode ": "C.V" if ch1mode else "C.C",
            "output ": "ON" if output else "OFF",
            "V/C priority ": "Current priority" if current_priority else "Voltage priority",
            "beep ": "ON" if beep else "OFF",
            "lock ": "ON" if lock else "OFF",
        }

    def readCurrent(self):
        """
            Reads the current setting

            :return: Current in Amps as a float
        """
        commandCheck = "ISET?".format()
        self._sendCommand(commandCheck)
        return float(self.__readOutput()[:5])

    def setCurrent(self, mA):
        """
            Sets the current

            :param mA: Current to set the PSU to, in mA
            :raises TenmaException: If the current does not match what was set
            :return: The current the PSU was set to in Amps as a float
        """
        self.checkCurrent(mA)

        A = float(mA) / 1000.0
        command = "ISET:{amperes:.3f}".format(amperes=A)

        self._sendCommand(command)
        readcurrent = self.readCurrent()
        readMilliamps = int(readcurrent * 1000)

        if readMilliamps != mA:
            raise TenmaException("Set {mA}mA, but read {readMilliamps}mA".format(
                mA=mA,
                readMilliamps=readMilliamps
            ))
        return float(readcurrent)

    def readVoltage(self):
        """
            Reads the voltage setting

            :return: Voltage in Volts as a float
        """
        commandCheck = "VSET?"
        self._sendCommand(commandCheck)
        return float(self.__readOutput())

    def setVoltage(self, mV):
        """
            Sets the voltage

            :param mV: voltage to set the PSU to, in mV
            :raises TenmaException: If the voltage does not match what was set
            :return: The voltage the PSU was set to in Volts as a float
        """
        self.checkVoltage(mV)

        volts = float(mV) / 1000.0
        command = "VSET:{volts:.2f}".format(volts=volts)

        self._sendCommand(command)
        readVolts = self.readVoltage()
        readMillivolts = int(readVolts * 1000)

        if readMillivolts != int(mV):
            raise TenmaException("Set {mV}mV, but read {readMillivolts}mV".format(
                mV=mV,
                readMillivolts=readMillivolts
            ))
        return float(readVolts)

    def runningCurrent(self):
        """
            Returns the current when the PSU is running

            :return: The running current of the PSU in Amps as a float
        """
        command = "IOUT?"
        self._sendCommand(command)
        return float(self.__readOutput())

    def runningVoltage(self):
        """
            Returns the voltage read when the PSU is running

            :return: The running voltage of the PSU in volts as a float
        """
        command = "VOUT?"
        self._sendCommand(command)
        return float(self.__readOutput())

    def saveConf(self, conf):
        """
            Save current configuration into Memory.

            :param conf: Memory index to store to
            :raises TenmaException: If the memory index is outside the range
        """
        conf = int(conf)
        if conf > self.NCONFS or conf < 1:
            raise TenmaException("Trying to set M{conf} with only {nconf} slots".format(
                conf=conf,
                nconf=self.NCONFS
            ))

        command = "SAV:{}".format(conf)
        self._sendCommand(command)

    def saveConfFlow(self, conf):
        """
            Alias for saveConf as saveConf works as expected on Tenma 13360
            unlike some other Tenma models
        """
        self.saveConf(conf)

    def recallConf(self, conf):
        """
            Load existing configuration in Memory. Same as pressing any Mx button on the unit
        """
        conf = int(conf)
        if conf > self.NCONFS or conf < 1:
            raise TenmaException("Trying to recall M{conf} with only {nconf} confs".format(
                conf=conf,
                nconf=self.NCONFS
            ))
        self._sendCommand("RCL:{}".format(conf))

    def setBEEP(self, enable=True):
        """
            Enable or disable BEEP

            There's no feedback from the serial connection to determine
            whether BEEP was set or not.

            :param enable: Boolean to enable or disable
        """
        enableFlag = 1 if enable else 0
        command = "BEEP:{}".format(enableFlag)
        self._sendCommand(command)

    def setLock(self, enable=True):
        """
            Set the front-panel lock on or off

            :param enable: Enable lock, defaults to True
        """
        enableFlag = 1 if enable else 0
        self._sendCommand("LOCK:{}".format(enableFlag))

    def ON(self):
        """
            Turns on the output
        """
        command = "OUT:1"
        self._sendCommand(command)

    def OFF(self):
        """
            Turns off the output
        """
        command = "OUT:0"
        self._sendCommand(command)

    def startAutoVoltageStep(self, startMillivolts,
                             stopMillivolts, stepMillivolts, stepTime):
        """
            Starts an automatic voltage step from Start mV to Stop mV,
            incrementing by Step mV every Time seconds

            :param startMillivolts: Starting voltage in mV
            :param stopMillivolts: End voltage in mV
            :param stepMillivolts: Amount to increase voltage by in mV
            :param stepTime: Time to wait before each increase, in Seconds
            :raises TenmaException: If the voltage is invalid
        """
        self.checkVoltage(stopMillivolts)
        if stepMillivolts > stopMillivolts:
            raise TenmaException(
                ("step voltage {stepMillivolts}V"
                 " higher than stop voltage {stopMillivolts}V").format(
                    stepMillivolts=stepMillivolts,
                    stopMillivolts=stopMillivolts))

        startVolts = float(startMillivolts) / 1000.0
        stopVolts = float(stopMillivolts) / 1000.0
        stepVolts = float(stepMillivolts) / 1000.0

        command = "VASTEP:{startVolts},{stopVolts},{stepVolts},{stepTime}".format(
            startVolts=startVolts,
            stopVolts=stopVolts,
            stepVolts=stepVolts,
            stepTime=stepTime
        )
        self._sendCommand(command)

    def stopAutoVoltageStep(self):
        """
            Stops the auto voltage step
        """
        self._sendCommand("VASTOP")

    def startAutoCurrentStep(self, startMilliamps,
                             stopMilliamps, stepMilliamps, stepTime):
        """
            Starts an automatic current step from Start mA to Stop mA,
            incrementing by Step mA every Time seconds

            :param startMilliamps: Starting current in mA
            :param stopMilliamps: End current in mA
            :param stepMilliamps: Amount to increase current by in mA
            :param stepTime: Time to wait before each increase, in Seconds
            :raises TenmaException: If the current is invalid
        """
        self.checkCurrent(stopMilliamps)
        if stepMilliamps > stopMilliamps:
            raise TenmaException(
                ("step current {stepMilliamps}mA higher"
                 " than stop current {stopMilliamps}mA").format(
                    stepMilliamps=stepMilliamps,
                    stopMilliamps=stopMilliamps))

        startAmps = float(startMilliamps) / 1000.0
        stopAmps = float(stopMilliamps) / 1000.0
        stepAmps = float(stepMilliamps) / 1000.0

        command = "IASTEP:{startAmps},{stopAmps},{stepAmps},{stepTime}".format(
            startAmps=startAmps,
            stopAmps=stopAmps,
            stepAmps=stepAmps,
            stepTime=stepTime
        )
        self._sendCommand(command)

    def stopAutoCurrentStep(self):
        """
            Stops the auto current step
        """
        self._sendCommand("IASTOP")

    def setManualVoltageStep(self, stepMillivolts):
        """
            Sets the manual step voltage
            When a VUP or VDOWN command is sent to the power supply, the PSU
            will step up or down by stepMillivolts mV

            :param stepMillivolts: Voltage to step up or down by when triggered
        """
        self.checkVoltage(stepMillivolts)
        stepVolts = float(stepMillivolts) / 1000.0
        command = "VSTEP:{}".format(stepVolts)
        self._sendCommand(command)

    def stepVoltageUp(self):
        """
            Increse the voltage by the configured step voltage
            Call "setManualVoltageStep" to set the step voltage
        """
        self._sendCommand("VUP")

    def stepVoltageDown(self):
        """
            Decrese the voltage by the configured step voltage
            Call "setManualVoltageStep" to set the step voltage
        """
        self._sendCommand("VDOWN")

    def setManualCurrentStep(self, stepMilliamps):
        """
            Sets the manual step current
            When a IUP or IDOWN command is sent to the power supply, the current
            will step up or down by stepMilliamps mA

            :param stepMilliamps: Current to step up or down by when triggered
        """
        self.checkCurrent(stepMilliamps)
        stepAmps = float(stepMilliamps) / 1000.0
        command = "ISTEP:{}".format(stepAmps)
        self._sendCommand(command)

    def stepCurrentUp(self):
        """
            Increse the current by the configured step current.
            Call "setManualCurrentStep" to set the step curchrent
        """
        self._sendCommand("IUP")

    def stepCurrentDown(self):
        """
            Decrese the current by the configured step current.
            Call "setManualCurrentStep" to set the step current
        """
        self._sendCommand("IDOWN")

    def setVoltagePriority(self):
        """
            Prioritize voltage
        """
        self._sendCommand("PRIORITY:0")

    def setCurrentPriority(self):
        """
            Prioritize current
        """
        self._sendCommand("PRIORITY:1")


class Tenma72_13360(Tenma72_13360_base):
    MATCH_STR = ["72-13360"]
