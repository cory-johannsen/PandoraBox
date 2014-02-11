#!/usr/bin/python
import subprocess
import threading
import multiprocessing
import Queue
import time
import enum
import display
import signal
import os
import switch
import rotary
import logging 

PandoraEvent = enum.enum(
        ARTIST_BOOKMARK="artistbookmark", 
        SONG_BAN="songban", 
        SONG_BOOKMARK="songbookmark",
        SONG_EXPLAIN="songexplain",  
        SONG_FINISH="songfinish",  
        SONG_LOVE="songlove",  
        SONG_MOVE="songmove",  
        SONG_SHELF="songshelf",  
        SONG_START="songstart",
        STATION_ADD_MUSIC="stationaddmusic",    
        STATION_ADD_SHARED="stationaddshared",   
        STATION_CREATE="stationcreate",   
        STATION_DELETE="stationdelete",
        STATION_FETCH_PLAYLIST="stationfetchplaylist", 
        STATION_QUICK_MIX_TOGGLE="stationquickmixtoggle", 
        STATION_RENAME="stationrename",
        USER_GET_STATIONS="usergetstations",
        PANDORA_CONTROLLER_QUIT="pandoracontrollerquit")


PandoraData = enum.enum(
        ARTIST="artist",
        TITLE="title",
        ALBUM="album",
        STATION_NAME="stationName",
        SONG_DURATION="songDuration",
        SONG_PLAYED="songPlayed",
        STATION_COUNT="stationCount")

PandoraCommand = enum.enum(
        NEXT_SONG="n",
        PAUSE="p",
        LOVE="+",
        BAN="-",
        QUIT="q",
        VOLUME_UP=")",
        VOLUME_DOWN="(",
        STATION_CHANGE="s")


class Screen(object):


    def __init__(self, itemList=["","","",""]):
        self.logger = logging.getLogger('PandoraBox.Screen')
        self.itemList = itemList
        self.scrollIndex = 0


    def items(self):
        return self.itemList


    def setItems(self, itemList):
        self.itemList = itemList


    def getVisibleItems(self):
        self.logger.debug("[getVisibleItems] scrollIndex: %s", str(self.scrollIndex))
        self.logger.debug("[getVisibleItems] list length: %s", str(len(self.itemList)))
        if self.scrollIndex <= len(self.itemList) - 4:
            return self.itemList[self.scrollIndex:]
        else:
            remainderIndex = 4 - (len(self.itemList) - self.scrollIndex)
            self.logger.debug("[getVisibleItems] remainderIndex: %s", str(remainderIndex))
            return self.itemList[self.scrollIndex:] + self.itemList[0:remainderIndex]


    def scrollUp(self):
        if self.scrollIndex >= len(self.itemList):
            self.scrollIndex = 0
        else:
            self.scrollIndex += 1


    def scrollDown(self):
        if self.scrollIndex == 0:
            self.scrollIndex = len(self.itemList) - 1
        else:
            self.scrollIndex -= 1


    def getSelectedIndex(self):
        return self.scrollIndex


    def setSelectedIndex(self, selectedIndex):
        self.scrollIndex = selectedIndex


class PandoraController(object):
    LINE_1_POSITION={"line":0,"position":0} 
    LINE_2_POSITION={"line":1,"position":0}
    LINE_3_POSITION={"line":2,"position":0} 
    LINE_4_POSITION={"line":3,"position":0} 

    def __init__(self, eventFifo="/home/ubuntu/.config/pandorabox/events", 
            commandFifo='/home/ubuntu/.config/pianobar/ctl'):
        #self.logger.info("__init__ entered"
        self.logger = logging.getLogger('PandoraBox.PandoraController')
        self.isRunning = True
        self.display = display.Display()
        self.navigationSwitch = switch.NavigationSwitch()
        self.rotaryEncoder = rotary.RotaryEncoder()
        self.eventFifoPath = eventFifo
        self.commandFifoPath = commandFifo
        self.eventQueue = multiprocessing.Queue()
        self.commandQueue = multiprocessing.Queue()
        self.songScreen = Screen(itemList=["--------------------", "PandoraBox", "Version 1.0", "--------------------"])
        self.stationScreen = Screen(itemList=["--------------------", "PandoraBox", "Version 1.0", "--------------------"])
        self.currentScreen = self.stationScreen
        self.isPlaying = False


    def start(self):
        self.logger.info("Starting execution.")
        self.isRunning = True

        self.display.initialize()
        self.isDisplayThreadRunning = True
        self.displayThread = threading.Thread(target=self.refreshDisplay)
        self.displayThread.daemon = True
        self.displayThread.start()

        self.isPianobarEventThreadRunning = True
        self.pianobarEventThread = threading.Thread(target=self.processPianobarEvents)
        self.pianobarEventThread.daemon = True
        self.pianobarEventThread.start()

        self.isCommandThreadRunning = True
        self.commandThread = threading.Thread(target=self.processCommands)
        self.commandThread.daemon = True
        self.commandThread.start()

        self.isInputEventThreadRunning = True
        self.inputEventThread = threading.Thread(target=self.processInputEvents)
        self.inputEventThread.daemon = True
        self.inputEventThread.start()

        self.isPianobarThreadRunning = True
        self.pianobarThread = threading.Thread(target=self.pianobarThread)
        # self.pianobarThread.daemon = True
        self.pianobarThread.start()

        self.logger.info("Execution initiated.")


    def stop(self):
        self.logger.info("Stopping execution.")
        self.isRunning = False


    def join(self):
        self.logger.info("join entered")
        self.commandThread.join()
        self.inputEventThread.join()
        self.displayThread.join()
        # launch a terminator thread that will close the event FIFO if it is still open
        # after a timeout.  This works around the blocking nature of the FIFO
        self.fifoTerminatorThread = threading.Thread(target=self.fifoTerminator)
        self.fifoTerminatorThread.start()
        self.pianobarEventThread.join()
        self.logger.info("join completed")


    def fifoTerminator(self):
        time.sleep(5)
        with open(self.eventFifoPath, 'w') as fifo:
            fifo.write(PandoraEvent.PANDORA_CONTROLLER_QUIT)
            fifo.close()


    def processInputEvents(self):
        self.logger.info("Input Event processing thread executing.")
        self.navigationSwitch.initialize()
        self.navigationSwitch.start(self.eventQueue)
        self.rotaryEncoder.initialize()
        self.rotaryEncoder.start(self.eventQueue)
        while self.isRunning:
            try:
                event = self.eventQueue.get(block=True, timeout=5)
                if event == switch.SwitchPosition.UP:
                    self.logger.info("UP switch event received.")
                    try:
                        self.commandQueue.put(PandoraCommand.NEXT_SONG, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.DOWN:
                    self.logger.info("DOWN switch event received.")
                    try:
                        self.commandQueue.put(PandoraCommand.PAUSE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.LEFT:
                    self.logger.info("LEFT switch event received.")
                    try:
                        self.commandQueue.put(PandoraCommand.BAN, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.RIGHT:
                    self.logger.info("RIGHT switch event received.")
                    try:
                        self.commandQueue.put(PandoraCommand.LOVE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.CENTER:
                    self.logger.info("CENTER switch event recieved.")
                    try:
                        self.commandQueue.put(PandoraCommand.PAUSE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == rotary.Direction.CLOCKWISE:
                    self.logger.info("CLOCKWISE rotary event recieved.")
                    try:
                        if self.currentScreen == self.songScreen:
                            self.commandQueue.put(PandoraCommand.VOLUME_UP, block=True, timeout=5)
                        else:
                            self.stationScreen.scrollUp()
                    except Queue.Full:
                        pass
                elif event == rotary.Direction.COUNTER_CLOCKWISE:
                    self.logger.info("COUNTER_CLOCKWISE rotary event recieved.")
                    try:
                        if self.currentScreen == self.songScreen:
                            self.commandQueue.put(PandoraCommand.VOLUME_DOWN, block=True, timeout=5)
                        else:
                            self.stationScreen.scrollDown()
                    except Queue.Full:
                        pass
                elif event == rotary.Click.CLICK:
                    self.logger.info("CLICK rotary event recieved.")
                    try:
                        if self.currentScreen == self.songScreen:
                            self.logger.info("Current screen is Song screen.  Setting to Station List screen.")
                            self.currentScreen = self.stationScreen
                            self.commandQueue.put(PandoraCommand.STATION_CHANGE, block=True, timeout=5)
                        else:
                            self.logger.info("Current screen is Station List screen.  Setting to Song screen.")
                            self.currentScreen = self.songScreen
                            changeStationCommand = PandoraCommand.STATION_CHANGE + str(self.stationScreen.getSelectedIndex())
                            if not self.isPlaying:
                                self.isPlaying = True
                                changeStationCommand = str(self.stationScreen.getSelectedIndex())
                            self.commandQueue.put(changeStationCommand, block=True, timeout=5)
                    except Queue.Full:
                        pass
                else:
                    self.logger.info("Input event received: %s", event)

            except Queue.Empty:
                pass
        self.navigationSwitch.stop()
        self.rotaryEncoder.stop()
        self.logger.info("Input Event processing thread terminated.")



    def processPianobarEvents(self):
        self.logger.info("Pianobar Event processing thread executing.")
        while self.isRunning and self.isPianobarEventThreadRunning:
            with open(self.eventFifoPath, 'r') as fifo:
                self.logger.debug("eventFifo is opened.")
                nextEvent = fifo.read().strip()
                tokens = nextEvent.split("\n")
                self.logger.debug("[processPianobarEvents] tokens: %s" % (tokens,))
                event = tokens[0]
                self.logger.info("[processPianobarEvents]     event: %s", event)
                if event == PandoraEvent.SONG_START:
                    self.logger.debug("[processPianobarEvents] SONG_START event intercepted")
                    del(tokens[0])
                    for dataParameter in tokens:
                        parameterName = dataParameter.split("=")[0]
                        parameterValue = dataParameter.split("=")[1]
                        if parameterName == PandoraData.STATION_NAME:
                            self.logger.debug("Station name: %s", parameterValue)
                            self.songScreen.items()[0] = parameterValue
                        elif parameterName == PandoraData.ARTIST:
                            self.logger.debug("Artist: %s", parameterValue)
                            self.songScreen.items()[1] = parameterValue
                        elif parameterName == PandoraData.TITLE:
                            self.logger.debug("Song title: %s", parameterValue)
                            self.songScreen.items()[2] = parameterValue
                        elif parameterName == PandoraData.ALBUM:
                            self.logger.debug("Album title: %s", parameterValue)
                            self.songScreen.items()[3] = parameterValue
                elif event == PandoraEvent.USER_GET_STATIONS:
                    self.logger.info("[processPianobarEvents] USER_GET_STATIONS event intercepted")    
                    del(tokens[0])
                    stationCount = 0
                    for dataParameter in tokens:
                        parameterName = dataParameter.split("=")[0]
                        parameterValue = dataParameter.split("=")[1]
                        if parameterName == PandoraData.STATION_COUNT:
                            self.logger.debug("Station count: %s", parameterValue)
                            stationCount = parameterValue
                    stationNames = []
                    for stationIndex in range(0, int(stationCount)):
                        stationTokenId = "station" + str(stationIndex) + "="
                        stationToken = [s for s in tokens if stationTokenId in s]
                        self.logger.debug("  %s: %s", stationTokenId, stationToken)
                        stationName = stationToken[0][len(stationTokenId):]
                        self.logger.debug("  stationName: %s", stationName)
                        stationNames.append(str(stationIndex) + " " + stationName)
                    self.logger.debug("[processPianobarEvents]  stationNames: %s", stationNames)
                    self.stationScreen.setSelectedIndex(0)
                    self.stationScreen.setItems(stationNames)
                        
                elif event == PandoraEvent.PANDORA_CONTROLLER_QUIT:
                    self.logger.info("Terminate event received.");
                    self.isPianobarEventThreadRunning = False
        self.logger.info("Pianobar Event processing thread terminated.")


    def processCommands(self):
        self.logger.info("Command processing thread executing.")
        # self.commandFifo = open(self.commandFifoPath, "w")
        while self.isRunning and self.isCommandThreadRunning:
            try:
                command = self.commandQueue.get(block=True, timeout=5)
                self.logger.info("Processing command %s", command)
                commandFifo = open(self.commandFifoPath, "w")
                commandFifo.write(command + "\r\n")
                commandFifo.close()
            except Queue.Empty:
                pass
        self.logger.info("Command processing thread terminated.")


    def refreshDisplay(self):
        self.logger.info("Display thread executing")
        previousLine1 = ""
        previousLine2 = ""
        previousLine3 = ""
        previousLine4 = ""
        while self.isRunning and self.isDisplayThreadRunning:
            currentLines = self.currentScreen.getVisibleItems()
            self.logger.debug("[refreshDisplay] currentLines: %s", currentLines)

            if previousLine1 != currentLines[0]:
                self.logger.info("Line 1 text changed.  Was: %s, Now: %s", previousLine1, currentLines[0])
                self.display.setPosition(PandoraController.LINE_1_POSITION["line"], PandoraController.LINE_2_POSITION["position"])
                line1 = currentLines[0].ljust(20, ' ')
                if len(line1) > 20:
                    line1 = line1[:20]
                self.display.writeString(line1)
                previousLine1 = currentLines[0]
            if previousLine2 != currentLines[1]:
                self.logger.info("Line 2 text changed.  Was: %s, Now: %s", previousLine2, currentLines[1])
                self.display.setPosition(PandoraController.LINE_2_POSITION["line"], PandoraController.LINE_2_POSITION["position"])
                line2 = currentLines[1].ljust(20, ' ')
                if len(line2) > 20:
                    line2 = line2[:20]
                self.display.writeString(line2)
                previousLine2 = currentLines[1]
            if previousLine3 != currentLines[2]:
                self.logger.info("Line 3 text changed.  Was: %s, Now: %s", previousLine3, currentLines[2])
                self.display.setPosition(PandoraController.LINE_3_POSITION["line"], PandoraController.LINE_3_POSITION["position"])
                line3 = currentLines[2].ljust(20, ' ')
                if len(line3) > 20:
                    line3 = line3[:20]
                self.display.writeString(line3)
                previousLine3 = currentLines[2]
            if previousLine4 != currentLines[3]:
                self.logger.info("Line 4 text changed.  Was: %s, Now: %s", previousLine4, currentLines[3])
                self.display.setPosition(PandoraController.LINE_4_POSITION["line"], PandoraController.LINE_4_POSITION["position"])
                line4 = currentLines[3].ljust(20, ' ')
                if len(line4) > 20:
                    line4 = line4[:20]
                self.display.writeString(line4)
                previousLine4 = currentLines[3]
            time.sleep(1)
        self.logger.info("Display thread terminating")


    def pianobarThread(self):
        self.logger.info("Starting pianobar subprocess.")
        subprocess.call("/usr/bin/pianobar")
        self.logger.info("pianobar subprocess dead.")


def main():
    logger = logging.getLogger('PandoraBox')
    logger.setLevel(level=logging.INFO)
    consoleHandler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] %(levelname)s - %(message)s')
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    pandoraController = PandoraController()

    pandoraController.start()

    while pandoraController.isRunning:
        try :
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected.")
            pandoraController.stop();

    pandoraController.join()
    logger.info("Exiting.")

if __name__ == '__main__':
    main()
