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


    def __init__(self, gpioPins={SwitchPosition.UP:"P8_44", 
                                SwitchPosition.DOWN:"P8_46", 
                                SwitchPosition.LEFT:"P8_43", 
                                SwitchPosition.RIGHT:"P8_45", 
                                SwitchPosition.CENTER:"P8_4"}):
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
        logging.info("[NavigationSwitch]  UP pin " + self.gpioPins[SwitchPosition.UP] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.UP], GPIO.IN, GPIO.PUD_UP)
        logging.info("[NavigationSwitch]  DOWN pin " + self.gpioPins[SwitchPosition.DOWN] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.DOWN], GPIO.IN, GPIO.PUD_UP)
        logging.info("[NavigationSwitch]  LEFT pin " + self.gpioPins[SwitchPosition.LEFT] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.LEFT], GPIO.IN, GPIO.PUD_UP)
        logging.info("[NavigationSwitch]  RIGHT pin " + self.gpioPins[SwitchPosition.RIGHT] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.RIGHT], GPIO.IN, GPIO.PUD_UP)
        logging.info("[NavigationSwitch]  CENTER pin " + self.gpioPins[SwitchPosition.CENTER] + " for input")
        GPIO.setup(self.gpioPins[SwitchPosition.CENTER], GPIO.IN, GPIO.PUD_UP)


    def __startPinMonitor(self, switchPosition, monitor):
        self.pinThreadRunning[switchPosition] = True
        self.pinThreads[switchPosition] = threading.Thread(target=monitor)
        self.pinThreads[switchPosition].start()


    def __switchMonitor(self, switchPosition):
        logging.info("[NavigationSwitch] switch monitor engaged for %s", switchPosition)
        lastPinState = self.pinStates[switchPosition]
        while self.pinThreadRunning[switchPosition]:
            pinState = GPIO.input(self.gpioPins[switchPosition])
            if pinState != lastPinState:
                logging.info("[NavigationSwitch]  switch state change detected for %s", switchPosition)
                logging.debug("[NavigationSwitch]  pin state: %s", pinState)
                self.pinStates[switchPosition] = pinState
                lastPinState = pinState
                if pinState:
                    try:
                        self.eventQueue.put(switchPosition, block=True, timeout=5)
                    except Queue.Full:
                        pass
            time.sleep(0.1)
        logging.info("[NavigationSwitch] switch monitor terminated for %s", switchPosition)



    def initialize(self):
        logging.info("[NavigationSwitch] Beginning initialization")
        self.__configureGPIO()
        time.sleep(0.1)
        self.pinStates[SwitchPosition.UP] = GPIO.input(self.gpioPins[SwitchPosition.UP])
        self.pinStates[SwitchPosition.DOWN] = GPIO.input(self.gpioPins[SwitchPosition.DOWN])
        self.pinStates[SwitchPosition.LEFT] = GPIO.input(self.gpioPins[SwitchPosition.LEFT])
        self.pinStates[SwitchPosition.RIGHT] = GPIO.input(self.gpioPins[SwitchPosition.RIGHT])
        self.pinStates[SwitchPosition.CENTER] = GPIO.input(self.gpioPins[SwitchPosition.CENTER])
        logging.info("[NavigationSwitch]   initial pin states: %s", self.pinStates)
        logging.info("[NavigationSwitch] Initialization complete.")


    def start(self, eventQueue):
        logging.info("[NavigationSwitch] start - Initiating pin monitors.")
        self.eventQueue = eventQueue
        # set up a thread for each switch that will wait for an edge and then update the internal state variable
        self.__startPinMonitor(SwitchPosition.UP, self.upSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.DOWN, self.downSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.LEFT, self.leftSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.RIGHT, self.rightSwitchMonitor)
        self.__startPinMonitor(SwitchPosition.CENTER, self.centerSwitchMonitor)
        logging.info("[NavigationSwitch] start - pin monitors active.")


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


    def simpleUpSwitchMonitor(self):
        print "[NavigationSwitch] Simple UP switch monitor thread beginning execution."
        lastPinState = self.pinStates[SwitchPosition.UP]
        print "[NavigationSwitch]  pinThreadRunning: ", self.pinThreadRunning[SwitchPosition.UP]
        while self.pinThreadRunning[SwitchPosition.UP]:
            pinState = GPIO.input(self.gpioPins[SwitchPosition.UP])
            if pinState != lastPinState:
                print "[NavigationSwitch] Simple UP switch state change detected."
                print "[NavigationSwitch]  pin state: ", pinState
                self.pinStates[SwitchPosition.UP] = pinState
                lastPinState = pinState
                if pinState:
                    try:
                        self.eventQueue.put(SwitchPosition.UP, block=True, timeout=5)
                    except Queue.Full:
                        pass
            time.sleep(0.1)

        print "[NavigationSwitch] Simple UP switch monitor thread terminating."


    def oldUpSwitchMonitor(self):
        print "[NavigationSwitch] UP switch monitor thread beginning execution."
        lastPinState = self.pinStates[SwitchPosition.UP]
        while self.pinThreadRunning[SwitchPosition.UP]:
            pinState = GPIO.input(self.gpioPins[SwitchPosition.UP])
            if pinState != lastPinState:
                print("[NavigationSwitch]  switch state change detected for %s ", SwitchPosition.UP)
                print "[NavigationSwitch]  pin state: ", pinState
                self.pinStates[SwitchPosition.UP] = pinState
                lastPinState = pinState
                if pinState:
                    try:
                        self.eventQueue.put(SwitchPosition.UP, block=True, timeout=5)
                    except Queue.Full:
                        pass

            time.sleep(0.1)
        print "[NavigationSwitch] UP switch monitor thread terminating."


    def oldDownSwitchMonitor(self):
        GPIO.add_event_detect(self.gpioPins[SwitchPosition.DOWN], GPIO.FALLING)
        while self.pinThreadRunning[SwitchPosition.DOWN]:
            if GPIO.event_detected(self.gpioPins[SwitchPosition.DOWN]):
                print "[NavigationSwitch] DOWN switch edge detected."
                self.pinStates[SwitchPosition.DOWN] = GPIO.LOW
            else:
                self.pinStates[SwitchPosition.DOWN] = GPIO.HIGH
            time.sleep(0.1)


    def oldLeftSwitchMonitor(self):
        GPIO.add_event_detect(self.gpioPins[SwitchPosition.LEFT], GPIO.FALLING)
        while self.pinThreadRunning[SwitchPosition.LEFT]:
            if GPIO.event_detected(self.gpioPins[SwitchPosition.LEFT]):
                print "[NavigationSwitch] LEFT switch edge detected."
                self.pinStates[SwitchPosition.LEFT] = GPIO.LOW
            else:
                self.pinStates[SwitchPosition.LEFT] = GPIO.HIGH
            time.sleep(0.1)


    def oldRightSwitchMonitor(self):
        GPIO.add_event_detect(self.gpioPins[SwitchPosition.RIGHT], GPIO.FALLING)
        while self.pinThreadRunning[SwitchPosition.RIGHT]:
            if GPIO.event_detected(self.gpioPins[SwitchPosition.RIGHT]):
                print "[NavigationSwitch] RIGHT switch edge detected."
                self.pinStates[SwitchPosition.RIGHT] = GPIO.LOW
            else:
                self.pinStates[SwitchPosition.RIGHT] = GPIO.HIGH
            time.sleep(0.1)


    def oldCenterSwitchMonitor(self):
        GPIO.add_event_detect(self.gpioPins[SwitchPosition.CENTER], GPIO.FALLING)
        while self.pinThreadRunning[SwitchPosition.CENTER]:
            if GPIO.event_detected(self.gpioPins[SwitchPosition.CENTER]):
                print "[NavigationSwitch] CENTER switch edge detected."
                self.pinStates[SwitchPosition.CENTER] = GPIO.LOW
            else:
                self.pinStates[SwitchPosition.CENTER] = GPIO.HIGH
            time.sleep(0.1)


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
