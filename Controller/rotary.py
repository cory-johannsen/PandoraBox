#!/usr/bin/python
import logging
import enum
import Adafruit_BBIO.GPIO as GPIO
import multiprocessing
import time
import sys

EncoderChannel = enum.enum(A="A", B="B")
Direction = enum.enum(CLOCKWISE="CW", COUNTER_CLOCKWISE="CCW")

class RotaryEncoder(object):


    def __init__(self, gpioPins={EncoderChannel.A:"P8_39", 
                                EncoderChannel.B:"P8_40"},
                                debounceTimeout=0.50):
        self.logger = logging.getLogger('PandoraBox.RotaryEncoder')
        self.gpioPins = gpioPins
        self.pinThreadRunning = False 
        self.pinThread = None 
        self.debounceTimeout = debounceTimeout


    def __configureGPIO(self):
        self.logger.info("Configuring A pin " + self.gpioPins[EncoderChannel.A] + " for input")
        GPIO.setup(self.gpioPins[EncoderChannel.A], GPIO.IN)
        self.logger.info("Configuring B pin " + self.gpioPins[EncoderChannel.B] + " for input")
        GPIO.setup(self.gpioPins[EncoderChannel.B], GPIO.IN)


    def initialize(self):
        self.logger.info("Beginning initialization")
        self.__configureGPIO()
        time.sleep(0.1)
        pinStateA = GPIO.input(self.gpioPins[EncoderChannel.A])
        pinStateB = GPIO.input(self.gpioPins[EncoderChannel.B])
        self.logger.info("initial pin states: A: %s, B: %s", pinStateA, pinStateB)
        self.logger.info("Initialization complete.")


    def start(self, eventQueue):
        self.logger.info("start - Initiating pin monitors.")
        self.eventQueue = eventQueue
        self.pinThreadRunning = True
        self.pinThread = multiprocessing.Process(target=self.encoderMonitor)
        self.pinThread.start()
        self.logger.info("start - pin monitors active.")


    def stop(self):
        self.pinThreadRunning = False
        self.pinThread.terminate()


    def encoderMonitor(self):
        self.logger.info("encoder monitor engaged")
        previousTime = time.time()
        while self.pinThreadRunning:
            GPIO.wait_for_edge(self.gpioPins[EncoderChannel.A], GPIO.FALLING)
            channelBState = GPIO.input(self.gpioPins[EncoderChannel.B])
            currentTime = time.time()
            timeDelta = currentTime - previousTime
            self.logger.debug("Edge detected on channel A. B:%s  Delta: %s", channelBState, timeDelta)
            if timeDelta >= self.debounceTimeout:
                if channelBState == 0:
                    self.logger.info("Counter-Clockwise rotation")
                    try:
                        self.eventQueue.put(Direction.COUNTER_CLOCKWISE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                else:
                    self.logger.info("Clockwise rotation")
                    try:
                        self.eventQueue.put(Direction.CLOCKWISE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                previousTime = currentTime

            #     if GPIO.input(self.gpioPins[EncoderChannel.B]):
            #         self.logger.info("RISING EDGE - HIGH signal on channel %s, delta: %s", EncoderChannel.B, timeDelta)
            #     else:
            #         self.logger.info("FALLING EDGE - LOW signal channel %s, delta: %s", EncoderChannel.B, timeDelta)
            #     previousEventTime = currentEventTime
            # else:
            #     self.logger.debug("bounce")



        self.logger.info("encoder monitor terminated")


    def clockwiseActive(self):
        return self.pinStates[EncoderChannel.B]


    def counterclockwiseActive(self):
        return self.pinStates[EncoderChannel.A]


def main():
    logger = logging.getLogger('PandoraBox.RotaryEncoder')
    logger.setLevel(level=logging.DEBUG)
    consoleHandler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    rotaryEncoder = RotaryEncoder()
    rotaryEncoder.initialize()
    rotaryEncoder.start(None)

    while True:
        try:
            time.sleep(0.1)

        except KeyboardInterrupt:
            print "Keyboard interrupt detected."
            rotaryEncoder.stop();
            sys.exit()

if __name__ == "__main__":
        main()
