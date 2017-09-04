import serial
import time

class tenma:
    """
        Control a tenma 72-2540 DC power supply
    """
    def __init__(self, serialPort):
        self.ser = serial.Serial(port=serialPort,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE)

        self.NCHANNELS = 4
        self.MAX_MA = 5100


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
        """
            Returns True if current was set correctly, False otherwise
        """
        if channel > self.NCHANNELS:
            return False

        if mA > self.MAX_MA:
            return False

        command = "ISET{channel}:{amperes:.3f}"

        A = float(mA) / 1000.0
        command = command.format(channel=1, amperes=A)

        commandCheck = "ISET{channel}?".format(channel=1)

        self.__sendCommand(command)

        self.__sendCommand(commandCheck)
        readcurrent = float(self.__readOutput())

        if readcurrent * 1000 != mA:
            print "Incorrect current read"
            return False

        return True



    def close(self):
        self.ser.close()

T = tenma('/dev/ttyUSB0')
#T.printVersion()
T.setCurrent(1, 3500)
T.close()
