#!/usr/bin/python
import subprocess
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
        PANDORA_CONTROLLER_QUIT="pandoracontrollerquit")


PandoraData = enum.enum(
        ARTIST="artist",
        TITLE="title",
        ALBUM="album",
        STATION_NAME="stationName",
        SONG_DURATION="songDuration",
        SONG_PLAYED="songPlayed")

PandoraCommand = enum.enum(
        NEXT_SONG="n",
        PAUSE="p",
        LOVE="+",
        BAN="-")

class PandoraController(object):
    STATION_TITLE_POSITION={"line":0,"position":0} 
    SONG_TITLE_POSITION={"line":1,"position":0}
    ARTIST_POSITION={"line":2,"position":0} 
    ALBUM_TITLE_POSITION={"line":3,"position":0} 
    TIME_POSITION={"line":3,"position":0} 

    def __init__(self, eventFifo="/home/ubuntu/.config/pandorabox/events", 
            commandFifo='/home/ubuntu/.config/pianobar/ctl'):
        #self.logger.info("__init__ entered"
        self.logger = logging.getLogger('PandoraBox.PandoraController')
        self.isRunning = True
        self.stationTitle = "Station Name"
        self.stationId = ""
        self.songTitle = "Song Title"
        self.artist = "Artist"
        self.albumTitle = "Album"
        self.durationMinutes = 0
        self.durationSeconds = 0
        self.positionMinutes = 0
        self.positionSeconds = 0
        self.display = display.Display()
        self.navigationSwitch = switch.NavigationSwitch()
        self.rotaryEncoder = rotary.RotaryEncoder()
        self.eventFifoPath = eventFifo
        self.commandFifoPath = commandFifo
        self.eventQueue = multiprocessing.Queue()
        self.commandQueue = multiprocessing.Queue()


    def start(self):
        self.logger.info("Starting execution.")
        self.isRunning = True

        self.display.initialize()
        self.isDisplayThreadRunning = True
        self.displayThread = multiprocessing.Process(target=self.refreshDisplay)
        # self.displayThread.daemon = True
        self.displayThread.start()

        self.isPianobarEventThreadRunning = True
        self.pianobarEventThread = multiprocessing.Process(target=self.processPianobarEvents)
        # self.eventThread.daemon = True
        self.pianobarEventThread.start()

        self.isCommandThreadRunning = True
        self.commandThread = multiprocessing.Process(target=self.processCommands)
        # self.commandThread.daemon = True
        self.commandThread.start()

        self.isInputEventThreadRunning = True
        self.inputEventThread = multiprocessing.Process(target=self.processInputEvents)
        self.inputEventThread.start()

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
                    self.logger.info("UP switch event recieved.")
                    try:
                        self.commandQueue.put(PandoraCommand.NEXT_SONG, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.DOWN:
                    self.logger.info("DOWN switch event recieved.")
                    try:
                        self.commandQueue.put(PandoraCommand.PAUSE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.LEFT:
                    self.logger.info("LEFT switch event recieved.")
                    try:
                        self.commandQueue.put(PandoraCommand.BAN, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.RIGHT:
                    self.logger.info("RIGHT switch event recieved.")
                    try:
                        self.commandQueue.put(PandoraCommand.LOVE, block=True, timeout=5)
                    except Queue.Full:
                        pass
                elif event == switch.SwitchPosition.CENTER:
                    self.logger.info("CENTER switch event recieved.")
                    try:
                        self.commandQueue.put(PandoraCommand.NEXT_SONG, block=True, timeout=5)
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
            # self.eventFifo = open(self.eventFifoPath, "r")
            with open(self.eventFifoPath, 'r') as fifo:
                self.logger.debug("eventFifo is opened.")
                nextEvent = fifo.read().strip()
                # print("processEvents] event: %s\n" % (nextEvent,))
                tokens = nextEvent.split("\n")
                # print("processEvents] tokens: %s" % (tokens,))
                event = tokens[0]
                # self.logger.info("processPianobarEvents]     event: ", event
                if event == PandoraEvent.SONG_START:
                    # self.logger.info("processPianobarEvents] SONG_START event intercepted"
                    del(tokens[0])
                    for dataParameter in tokens:
                        # self.logger.info("processPianobarEvents]   data parameter: ", dataParameter
                        parameterName = dataParameter.split("=")[0]
                        parameterValue = dataParameter.split("=")[1]
                        # self.logger.info("processPianobarEvents]     name: ", parameterName
                        # self.logger.info("processPianobarEvents]     value: ", parameterValue
                        if parameterName == PandoraData.STATION_NAME:
                            self.logger.debug("Station name: ", parameterValue)
                            self.stationTitle = parameterValue
                        elif parameterName == PandoraData.ARTIST:
                            self.logger.debug("Artist: ", parameterValue)
                            self.artist = parameterValue
                        elif parameterName == PandoraData.TITLE:
                            self.logger.debug("Song title: ", parameterValue)
                            self.songTitle = parameterValue
                        elif parameterName == PandoraData.ALBUM:
                            self.logger.debug("Album title: ", parameterValue)
                            self.albumTitle = parameterValue
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
                commandFifo.write(command)
                commandFifo.close()
            except Queue.Empty:
                pass
        self.logger.info("Command processing thread terminated.")


    def refreshDisplay(self):
        self.logger.info("Display thread executing")
        lastStationTitle = ""
        lastSongTitle = ""
        lastArtist = ""
        lastAlbum = ""
        while self.isRunning and self.isDisplayThreadRunning:
            if self.stationTitle != lastStationTitle:
                self.logger.debug("Station name change.  Was: %s, Now: %s", lastStationTitle, self.stationTitle)
                self.display.setPosition(PandoraController.STATION_TITLE_POSITION["line"], PandoraController.STATION_TITLE_POSITION["position"])
                stationTitle = self.stationTitle.ljust(20, ' ')
                if len(stationTitle) > 20:
                    stationTitle = stationTitle[:20]
                self.display.writeString(stationTitle)
                lastStationTitle = self.stationTitle

            if self.songTitle != lastSongTitle:
                self.logger.debug("Song title change.  Was: %s, Now: %s", lastSongTitle, self.songTitle)
                songTitle = self.songTitle.ljust(20, ' ')
                if len(songTitle) > 20:
                    songTitle = songTitle[:20]
                self.display.setPosition(PandoraController.SONG_TITLE_POSITION["line"], PandoraController.SONG_TITLE_POSITION["position"])
                self.display.writeString(songTitle)
                lastSongTitle = self.songTitle

            if self.artist != lastArtist:
                self.logger.debug("Artist change.  Was: %s, Now: %s", lastArtist, self.artist)
                artist = self.artist.ljust(20, ' ')
                if len(artist) > 20:
                    artist = artist[:20]
                self.display.setPosition(PandoraController.ARTIST_POSITION["line"], PandoraController.ARTIST_POSITION["position"])
                self.display.writeString(artist)
                lastArtist = self.artist

            if self.albumTitle != lastAlbum: 
                self.logger.debug("Album name change.  Was: %s, Now: %s", lastAlbum, self.albumTitle)
                album = self.albumTitle.ljust(20, ' ')
                if len(album) > 20:
                    album = album[:20]
                self.display.setPosition(PandoraController.ALBUM_TITLE_POSITION["line"], PandoraController.ALBUM_TITLE_POSITION["position"])
                self.display.writeString(album)
                lastAlbum = self.albumTitle
            time.sleep(1)
        self.logger.info("Display thread terminating")


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
