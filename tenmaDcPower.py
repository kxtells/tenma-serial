import serial
import time

class TenmaException(Exception):
    pass

class Tenma:
    """
        Control a tenma 72-2540 DC power supply
    """
    def __init__(self, serialPort):
        self.ser = serial.Serial(port=serialPort,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE)

        self.NCHANNELS = 1
        self.MAX_MA = 5100
        self.MAX_MV = 31000


    def __sendCommand(self, command):
        self.ser.write(command)
        time.sleep(1) #give it time to process

    def __readOutput(self):
        out=""
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1)
        return out

    def printVersion(self):
        self.__sendCommand("*IDN?")
        print self.__readOutput()

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

        commandCheck = "ISET{channel}?".format(channel=1)

        self.__sendCommand(command)

        self.__sendCommand(commandCheck)
        readcurrent = float(self.__readOutput())

        if readcurrent * 1000 != mA:
            raise TenmaException("Set {set}mA, but read {read}mA".format(
                set=mA,
                read=readcurrent * 1000,
                ))

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

        commandCheck = "VSET{channel}?".format(channel=1)

        self.__sendCommand(command)

        self.__sendCommand(commandCheck)
        readvolt = float(self.__readOutput())

        if readvolt * 1000 != mV:
            raise TenmaException("Set {set}mV, but read {read}mV".format(
                set=mV,
                read=readvolt * 1000,
                ))

    def close(self):
        self.ser.close()

T = Tenma('/dev/ttyUSB0')
#T.printVersion()
T.setCurrent(1, 2200)
T.setVoltage(1, 5000)
T.close()
