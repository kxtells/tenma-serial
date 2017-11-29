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
        self.NCONFS = 4
        self.MAX_MA = 5000
        self.MAX_MV = 30000
        self.DEBUG = debug

    def setPort(self, serialPort):
        self.ser = serial.Serial(port=serialPort,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE)

    def __sendCommand(self, command):
        if self.DEBUG:
            print ">> ", command
        self.ser.write(command)
        time.sleep(0.5) #give it time to process

    def __readOutput(self):
        out=""
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1)

        if self.DEBUG:
            print "<< ", out

        return out

    def getVersion(self):
        self.__sendCommand("*IDN?")
        return self.__readOutput()


    def readCurrent(self, channel):
        if channel > self.NCHANNELS:
            raise TenmaException("Trying to read CH{channel} with only {nch} channels".format(
                channel=channel,
                nch=self.NCHANNELS
                ))

        commandCheck = "ISET{channel}?".format(channel=1)
        self.__sendCommand(commandCheck)
        return float(self.__readOutput())

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

        command = "IOUT{channel}".format(channel=channel)
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

        command = "VOUT{channel}".format(channel=channel)
        self.__sendCommand(command)
        readvolt = self.__readOutput()
        return readvolt

    def saveConf(self, conf):
        """
            Save current configuration
        """
        if conf > self.NCONFS:
            raise TenmaException("Trying to set M{channel} with only {nch} confs".format(
                channel=conf,
                nch=self.NCONFS
                ))

        command = "SAV{conf}".format(conf=conf)
        self.__sendCommand(command)

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

#T = Tenma72_2540('/dev/ttyUSB0')
#print T.getVersion()
##T.setCurrent(1, 2200)
##T.setVoltage(1, 6000)
#
#T.ON()
#
#print T.runningVoltage(1)
#print T.runningCurrent(1)
#
#T.OFF()
#
#T.close()
