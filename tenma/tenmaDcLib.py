"""
    tenmaDcLib is small python library to control a Tenma 72-2540 programmable
    DC power supply
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

import serial
import time
import click


class TenmaException(Exception):
    pass


class Tenma72_2540:
    """
        Control a tenma 72-2540 DC power supply
    """
    def __init__(self, serialPort, debug=False):
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)

        self.NCHANNELS = 1
        # Only 4 physical buttons. But 5 memories are available
        self.NCONFS = 5
        self.MAX_MA = 5000
        self.MAX_MV = 30000
        self.SAFE_MA = 3000
        self.SAFE_MV = 12000
        self.DEBUG = debug

    def setSafeCurrent(self, mA):
        self.SAFE_MA = mA

    def setSafeVoltage(self, mV):
        self.SAFE_MV

    def setPort(self, serialPort):
        self.ser = serial.Serial(port=serialPort,
                                 baudrate=9600,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)

    def __sendCommand(self, command):
        if self.DEBUG:
            print(">> ", command)
        self.ser.write(command.encode('ascii'))
        # Give it time to process
        time.sleep(0.5)

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
        """
        self.__sendCommand("STATUS?")
        statusBytes = self.__readBytes()

        if len(statusBytes) > 1:
            raise TenmaException("Received more bytes than expected when reading status")

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
        return float(self.__readOutput())

    def checkCurrent(self, channel, mA):
        readcurrent = self.readCurrent(channel)

        if readcurrent * 1000 > mA:
            return False, readcurrent

        return True, readcurrent

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

        if mA > self.SAFE_MA:
            print("Current value ({mA} mA) is above safe limit ({safe_mA} mA).".format(
                mA=mA,
                safe_mA=self.SAFE_MA
            ))
            if not click.confirm('Do you want to continue?', default=True):
                print("Aborting. If you want, use --safeC to allow for a different safe current.")
                return

        command = "ISET{channel}:{amperes:.3f}"

        A = float(mA) / 1000.0
        command = command.format(channel=1, amperes=A)

        self.__sendCommand(command)

        readcurrent = self.readCurrent(channel)

        if readcurrent * 1000 != mA:
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

    def checkVoltage(self, channel, mV):
        readvolt = self.readVoltage(channel)

        if readvolt * 1000 > mV:
            return False, readvolt

        return True, readvolt

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

        if mV > self.SAFE_MV:
            print("Voltage value ({mV} mV) is above safe limit ({safe_mV} mV).".format(
                mV=mV,
                safe_mV=self.SAFE_MV
            ))
            if not click.confirm('Do you want to continue?', default=True):
                print("Aborting. If you want, use --safeV to allow for a different safe Voltage.")
                return

        command = "VSET{channel}:{volt:.2f}"

        V = float(mV) / 1000.0
        command = command.format(channel=1, volt=V)

        self.__sendCommand(command)

        readvolt = self.readVoltage(channel)

        if readvolt * 1000 != mV:
            raise TenmaException("Set {set}mV, but read {read}mV".format(
                set=mV,
                read=readvolt * 1000,
            ))

    def runningCurrent(self, channel):
        """
            This does not seem to work
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
            This does not seem to work
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
            Save current configuration. Does not work as one would expect. SAV(4)
            will not save directly to memory 4. We actually need to recall memory
            4, and then save the configuration.
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
             - turn off the output
             - recall memory conf
             - Save to that memory conf

            :param conf: Memory index to store to
            :param channel: Channel with output to store
        """

        self.OFF()

        # Read current voltage
        volt = self.readVoltage(channel)
        curr = self.readCurrent(channel)

        # Load conf
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
            Load existing configuration
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

    def ON(self):
        """
            Turns on the output
        """

        command = "OUT1"
        self.__sendCommand(command)

    def safeON(self):
        """
            Safely turns on the output
        """

        # ToDo: allow channels other than "1"
        safeCurrent, readcurrent = self.checkCurrent(1, self.SAFE_MA)

        if not safeCurrent:
            print("Current ({readcurrent} mA) is set above safe limit ({safe_mA} mA).".format(
                readcurrent=int(readcurrent*1000),
                safe_mA=self.SAFE_MA
            ))
            if not click.confirm('Do you want to continue?', default=True):
                print("Aborting. Either use --current to set a new output current or use --safeC to allow for a different safe current")
                return

        # ToDo: allow channels other than "1"
        safeVoltage, readvolt = self.checkVoltage(1, self.SAFE_MV)
        if not safeVoltage:
            print("Voltage ({readvolt} mV) is set above safe limit ({safe_mV} mV).".format(
                readvolt=int(readvolt*1000),
                safe_mV=self.SAFE_MV
            ))
            if not click.confirm('Do you want to continue?', default=True):
                print("Aborting. Either use --voltage to set a new output voltage or use --safeV to allow for a different safe voltage")
                return

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
