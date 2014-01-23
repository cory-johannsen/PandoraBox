#!/usr/bin/python
import enum

REGISTER = enum(INSTRUCTION=0,DATA=1)

class Display(object):

    def __init__(self, lineCount=4, characterCount=20, dataGpioPins=(32, 33, 34, 35, 36, 37, 38, 39), registerSelectPin=56, enablePin=57):
        self.lineCount = lineCount
        self.characterCount = characterCount
        self.dataGpioPins = dataGpioPins
        self.registerSelectPin = registerSelectPin
        self.enablePin = enablePin


    def selectRegister(register):

    def write(character, line, position):



