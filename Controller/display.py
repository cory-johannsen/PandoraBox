#!/usr/bin/python
import enum
import Adafruit_BBIO.GPIO as GPIO
import time

REGISTER = enum.enum(INSTRUCTION=0,DATA=1)

class Display(object):
    CLEAR_DISPLAY = (1,0,0,0,0,0,0,0)
    RETURN_HOME = (0,1,0,0,0,0,0,0)
    ENTRY_MODE_SET = (0,1,1,0,0,0,0,0)
    DISPLAY_OFF = (0,0,0,1,0,0,0,0)
    DISPLAY_ON = (0,0,1,1,0,0,0,0)
    DISPLAY_ON_WITH_CURSOR = (0,1,1,1,0,0,0,0)
    DISPLAY_ON_WITH_BLINK_CURSOR = (1,1,1,1,0,0,0,0)
    FUNCTION_SET_ONE_LINE = (0,0,0,0,1,1,0,0)
    FUNCTION_SET_TWO_LINE = (0,0,0,1,1,1,0,0)
    CGRAM_ADDRESS_MAP = {
            "A":(1,0,0,0,0,0,1,0),
            "B":(0,1,0,0,0,0,1,0),
            "C":(1,1,0,0,0,0,1,0),
            "D":(0,0,1,0,0,0,1,0),
            "E":(1,0,1,0,0,0,1,0),
            "F":(0,1,1,0,0,0,1,0),
            "G":(1,1,1,0,0,0,1,0),
            "H":(0,0,0,1,0,0,1,0),
            "I":(1,0,0,1,0,0,1,0),
            "J":(0,1,0,1,0,0,1,0),
            "K":(1,1,0,1,0,0,1,0),
            "L":(0,0,1,1,0,0,1,0),
            "M":(1,0,1,1,0,0,1,0),
            "N":(0,1,1,1,0,0,1,0),
            "O":(1,1,1,1,0,0,1,0),
            "P":(0,0,0,0,1,0,1,0),
            "Q":(1,0,0,0,1,0,1,0),
            "R":(0,1,0,0,1,0,1,0),
            "S":(1,1,0,0,1,0,1,0),
            "T":(0,0,1,0,1,0,1,0),
            "U":(1,0,1,0,1,0,1,0),
            "V":(0,1,1,0,1,0,1,0),
            "W":(1,1,1,0,1,0,1,0),
            "X":(0,0,0,1,1,0,1,0),
            "Y":(1,0,0,1,1,0,1,0),
            "Z":(0,1,0,1,1,0,1,0),
            "a":(1,0,0,0,0,1,1,0),
            "b":(0,1,0,0,0,1,1,0),
            "c":(1,1,0,0,0,1,1,0),
            "d":(0,0,1,0,0,1,1,0),
            "e":(1,0,1,0,0,1,1,0),
            "f":(0,1,1,0,0,1,1,0),
            "g":(1,1,1,0,0,1,1,0),
            "h":(0,0,0,1,0,1,1,0),
            "i":(1,0,0,1,0,1,1,0),
            "j":(0,1,0,1,0,1,1,0),
            "k":(1,1,0,1,0,1,1,0),
            "l":(0,0,1,1,0,1,1,0),
            "m":(1,0,1,1,0,1,1,0),
            "n":(0,1,1,1,0,1,1,0),
            "o":(1,1,1,1,0,1,1,0),
            "p":(0,0,0,0,1,1,1,0),
            "q":(1,0,0,0,1,1,1,0),
            "r":(0,1,0,0,1,1,1,0),
            "s":(1,1,0,0,1,1,1,0),
            "t":(0,0,1,0,1,1,1,0),
            "u":(1,0,1,0,1,1,1,0),
            "v":(0,1,1,0,1,1,1,0),
            "w":(1,1,1,0,1,1,1,0),
            "x":(0,0,0,1,1,1,1,0),
            "y":(1,0,0,1,1,1,1,0),
            "z":(0,1,0,1,1,1,1,0),
            "{":(1,1,0,1,1,1,1,0),
            "|":(0,0,1,1,1,1,1,0),
            "}":(1,0,1,1,1,1,1,0),
            "ARROW_RIGHT":(0,1,1,1,1,1,1,0),
            "ARROW_LEFT":(1,1,1,1,1,1,1,0),
            "0":(0,0,0,0,1,1,0,0),
            "1":(1,0,0,0,1,1,0,0),
            "2":(0,1,0,0,1,1,0,0),
            "3":(1,1,0,0,1,1,0,0),
            "4":(0,0,1,0,1,1,0,0),
            "5":(1,0,1,0,1,1,0,0),
            "6":(0,1,1,0,1,1,0,0),
            "7":(1,1,1,0,1,1,0,0),
            "8":(0,0,0,1,1,1,0,0),
            "9":(1,0,0,1,1,1,0,0),
            ":":(0,1,0,1,1,1,0,0),
            ";":(1,1,0,1,1,1,0,0),
            "<":(0,0,1,1,1,1,0,0),
            "=":(1,0,1,1,1,1,0,0),
            ">":(0,1,1,1,1,1,0,0),
            "?":(1,1,1,1,1,1,0,0),
            " ":(0,0,0,0,0,1,0,0),
            "!":(1,0,0,0,0,1,0,0),
            "\"":(0,1,0,0,0,1,0,0),
            "#":(1,1,0,0,0,1,0,0),
            "$":(0,0,1,0,0,1,0,0),
            "%":(1,0,1,0,0,1,0,0),
            "&":(0,1,1,0,0,1,0,0),
            "'":(1,1,1,0,0,1,0,0),
            "(":(0,0,0,1,0,1,0,0),
            ")":(1,0,0,1,0,1,0,0),
            "*":(0,1,0,1,0,1,0,0),
            "+":(1,1,0,1,0,1,0,0),
            ",":(0,0,1,1,0,1,0,0),
            "-":(1,0,1,1,0,1,0,0),
            ".":(0,1,1,1,0,1,0,0),
            "/":(1,1,1,1,0,1,0,0),
         }

    def __init__(self, lineCount=4, characterCount=20, 
            dataGpioPins=("P8_12", "P8_14", "P8_16", "P8_18", "P8_11", "P8_13", "P8_15", "P8_17"), 
            registerSelectPin="P8_28", enablePin="P8_30"):
        self.lineCount = lineCount
        self.characterCount = characterCount
        self.dataGpioPins = dataGpioPins
        self.registerSelectPin = registerSelectPin
        self.enablePin = enablePin


    def __configureGPIO(self):
        print "[Display]  Configuring register select pin " + self.registerSelectPin + " for output"
        GPIO.setup(self.registerSelectPin, GPIO.OUT)
        print "[Display]  Configuring enable pin " + self.enablePin + " for output"
        GPIO.setup(self.enablePin, GPIO.OUT)
        for i in range(0, 8):
            print "[Display]  Configuring data pin " + self.dataGpioPins[i] + " for output as D" + str(i)
            GPIO.setup(self.dataGpioPins[i], GPIO.OUT)


    def __setGpio(self, gpioPin, value):
        GPIO.output(gpioPin, value)


    def __writeByte(self, dataBits, registerSelect):
        self.__setGpio(self.enablePin, 1)
        #time.sleep(0.01)
        self.__setGpio(self.registerSelectPin, registerSelect)
        for i in range(0, 8):
           self.__setGpio(self.dataGpioPins[i], dataBits[i]) 
        #time.sleep(0.01)
        self.__setGpio(self.enablePin, 0)
        #time.sleep(0.01)
           

    def __setAddress(self, address):
        # print("setAddress: address=%s" % (address,))
        binAddress = ('1') + format(address, '07b')
        # print("  binAddress: %s" % (binAddress,))
        ddramAddress = (int(binAddress[7]), 
                int(binAddress[6]), 
                int(binAddress[5]), 
                int(binAddress[4]), 
                int(binAddress[3]), 
                int(binAddress[2]), 
                int(binAddress[1]), 
                int(binAddress[0]))
        # print("  ddramAddress: %s" % (ddramAddress,))
        self.__writeByte(ddramAddress, REGISTER.INSTRUCTION)


    def initialize(self):
        print "[Display] Beginning initialization"
        self.__configureGPIO()
        time.sleep(0.1)
        print "[Display]   Clearing display"
        self.__writeByte(Display.CLEAR_DISPLAY, REGISTER.INSTRUCTION)
        time.sleep(0.5)
        print "[Display]   Returning to home"
        self.__writeByte(Display.RETURN_HOME, REGISTER.INSTRUCTION)
        time.sleep(0.1)
        print "[Display]   Enabling cursor with blink"
        self.__writeByte(Display.DISPLAY_ON_WITH_BLINK_CURSOR, REGISTER.INSTRUCTION)
        time.sleep(0.1)
        print "[Display]   Invoking function set"
        self.__writeByte(Display.FUNCTION_SET_TWO_LINE, REGISTER.INSTRUCTION)
        time.sleep(0.1)
        print "[Display] Initialization complete."


    def setPosition(self, line, position):
        # print("setPosition: line=%s, position=%s" % (line, position))
        address = position
        if line == 1:
            address += 64
        elif line == 2:
            address += 20
        elif line == 3:
            address += 84
        self.__setAddress(address)


    def write(self, character):
        # print "print: ", character
        self.__writeByte(Display.CGRAM_ADDRESS_MAP[character], REGISTER.DATA)


    def writeString(self, string):
        for i in range(len(string)):
            self.write(string[i])


def main():
    display = Display()
    display.initialize()
    index = 0
    for line in range(0, 4):
        for position in range (0, 20):
            if index >= 10:
                index = 0
            print("Printing %s at line %s, position %s" % (index, line, position))
            display.setPosition(line, position)
            display.write(str(index))
            time.sleep(0.5)
            index += 1


if __name__ == "__main__":
        main()
