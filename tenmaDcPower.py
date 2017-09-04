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

    def close(self):
        self.ser.close()

T = tenma('/dev/ttyUSB0')
T.printVersion()
T.close()
