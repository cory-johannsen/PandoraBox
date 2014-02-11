#!/usr/bin/python
import logging
import enum
import Adafruit_BBIO.GPIO as GPIO
import threading
import time
import sys
import Queue

SwitchPosition = enum.enum(UP="UP", DOWN="DOWN", LEFT="LEFT", RIGHT="RIGHT", CENTER="CENTER")

class NavigationSwitch(object):


    def __init__(self, gpioPins={SwitchPosition.UP:"P8_35", 
                                SwitchPosition.DOWN:"P8_33", 
                                SwitchPosition.LEFT:"P8_36", 
                                SwitchPosition.RIGHT:"P8_34", 
                                SwitchPosition.CENTER:"P8_31"}):
        self.logger = logging.getLogger('PandoraBox.NavigationSwitch')
        self.gpioPins = gpioPins
        self.pinStates = {SwitchPosition.UP:GPIO.LOW, 
                        SwitchPosition.DOWN:GPIO.LOW,
                        SwitchPosition.LEFT:GPIO.LOW,
                        SwitchPosition.RIGHT:GPIO.LOW,
                        SwitchPosition.CENTER:GPIO.LOW}
        self.pinThreadRunning = {SwitchPosition.UP:False, 
                        SwitchPosition.DOWN:False,
                        SwitchPosition.LEFT:False,
                        SwitchPosition.RIGHT:False,
                        SwitchPosition.CENTER:False}
        self.pinThreads = {SwitchPosition.UP:None, 
                        SwitchPosition.DOWN:None,
                        SwitchPosition.LEFT:None,
                        SwitchPosition.RIGHT:None,
                        SwitchPosition.CENTER:None}


    def __configureGPIO(self):
        self.logger.info("UP pin " + self.gpioPins[SwitchPosition.UP] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.UP], GPIO.IN, GPIO.PUD_UP)
        self.logger.info("DOWN pin " + self.gpioPins[SwitchPosition.DOWN] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.DOWN], GPIO.IN, GPIO.PUD_UP)
        self.logger.info("LEFT pin " + self.gpioPins[SwitchPosition.LEFT] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.LEFT], GPIO.IN, GPIO.PUD_UP)
        self.logger.info("RIGHT pin " + self.gpioPins[SwitchPosition.RIGHT] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.RIGHT], GPIO.IN, GPIO.PUD_UP)
        self.logger.info("CENTER pin " + self.gpioPins[SwitchPosition.CENTER] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.CENTER], GPIO.IN, GPIO.PUD_UP)


    def __startPinMonitor(self, switchPosition, monitor):
        self.pinThreadRunning[switchPosition] = True
        self.pinThreads[switchPosition] = threading.Thread(target=monitor)
        self.pinThreads[switchPosition].start()


    def __switchMonitor(self, switchPosition):
        self.logger.info("switch monitor engaged for %s", switchPosition)
        lastPinState = self.pinStates[switchPosition]
        while self.pinThreadRunning[switchPosition]:
            pinState = GPIO.input(self.gpioPins[switchPosition])
            if pinState != lastPinState:
                self.logger.debug("switch state change detected for %s", switchPosition)
                self.logger.debug("pin state: %s", pinState)
                self.pinStates[switchPosition] = pinState
                lastPinState = pinState
                if pinState:
                    try:
                        self.eventQueue.put(switchPosition, block=True, timeout=5)
                    except Queue.Full:
                        pass
            time.sleep(0.1)
        self.logger.info("switch monitor terminated for %s", switchPosition)



    def initialize(self):
        self.logger.info("Beginning initialization")
        self.__configureGPIO()
        time.sleep(0.1)
        self.pinStates[SwitchPosition.UP] = GPIO.input(self.gpioPins[SwitchPosition.UP])
        self.pinStates[SwitchPosition.DOWN] = GPIO.input(self.gpioPins[SwitchPosition.DOWN])
        self.pinStates[SwitchPosition.LEFT] = GPIO.input(self.gpioPins[SwitchPosition.LEFT])
        self.pinStates[SwitchPosition.RIGHT] = GPIO.input(self.gpioPins[SwitchPosition.RIGHT])
        self.pinStates[SwitchPosition.CENTER] = GPIO.input(self.gpioPins[SwitchPosition.CENTER])
        self.logger.info("initial pin states: %s", self.pinStates)
        self.logger.info("Initialization complete.")


    def start(self, eventQueue):
        self.logger.info("start - Initiating pin monitors.")
        self.eventQueue = eventQueue
        # set up a thread for each switch that will wait for an edge and then update the internal state variable
        self.__startPinMonitor(SwitchPosition.UP, self.upSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.DOWN, self.downSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.LEFT, self.leftSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.RIGHT, self.rightSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.CENTER, self.centerSwitchMonitor)
        self.logger.info("start - pin monitors active.")


    def stop(self):
        self.pinThreadRunning[SwitchPosition.UP] = False
        self.pinThreadRunning[SwitchPosition.DOWN] = False
        self.pinThreadRunning[SwitchPosition.LEFT] = False
        self.pinThreadRunning[SwitchPosition.RIGHT] = False
        self.pinThreadRunning[SwitchPosition.CENTER] = False


    def upSwitchMonitor(self):
        self.__switchMonitor(SwitchPosition.UP)


    def downSwitchMonitor(self):
        self.__switchMonitor(SwitchPosition.DOWN)


    def leftSwitchMonitor(self):
        self.__switchMonitor(SwitchPosition.LEFT)


    def rightSwitchMonitor(self):
        self.__switchMonitor(SwitchPosition.RIGHT)


    def centerSwitchMonitor(self):
        self.__switchMonitor(SwitchPosition.CENTER)


    def upActive(self):
        return self.pinStates[SwitchPosition.UP]


    def downActive(self):
        return self.pinStates[SwitchPosition.DOWN]


    def leftActive(self):
        return self.pinStates[SwitchPosition.LEFT]


    def rightActive(self):
        return self.pinStates[SwitchPosition.RIGHT]


    def centerActive(self):
        return self.pinStates[SwitchPosition.CENTER]


def main():
    navSwitch = NavigationSwitch()
    navSwitch.initialize()
    navSwitch.start()

    while True:
        try:
            time.sleep(0.1)

        except KeyboardInterrupt:
            print "Keyboard interrupt detected."
            navSwitch.stop();
            sys.exit()

if __name__ == "__main__":
        main()
