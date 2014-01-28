#!/usr/bin/python
import subprocess
import threading
import time
import Queue
import enum
import display
import signal
import os

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
        STATION_RENAME="stationrename")


PandoraData = enum.enum(
        ARTIST="artist",
        TITLE="title",
        ALBUM="album",
        STATION_NAME="stationName",
        SONG_DURATION="songDuration",
        SONG_PLAYED="songPlayed")


class PandoraController(object):
    STATION_TITLE_POSITION={"line":0,"position":0} 
    SONG_TITLE_POSITION={"line":1,"position":0}
    ARTIST_POSITION={"line":2,"position":0} 
    ALBUM_TITLE_POSITION={"line":3,"position":0} 
    TIME_POSITION={"line":3,"position":0} 

    def __init__(self, eventFifo="/home/ubuntu/.config/pandorabox/events", 
            commandFifo='/home/ubuntu/.config/pianobar/ctl'):
        #print "__init__ entered"
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
        self.eventFifoPath = eventFifo
        self.commandFifoPath = commandFifo


    def start(self):
        print "[PandoraController] start entered"
        self.isRunning = True

        self.display.initialize()
        self.isDisplayThreadRunning = True
        self.displayThread = threading.Thread(target=self.refreshDisplay)
        # self.displayThread.daemon = True
        self.displayThread.start()

        self.isEventThreadRunning = True
        self.eventThread = threading.Thread(target=self.processEvents)
        # self.eventThread.daemon = True
        self.eventThread.start()

        self.isCommandThreadRunning = True
        self.commandThread = threading.Thread(target=self.processCommands)
        # self.commandThread.daemon = True
        self.commandThread.start()
        print "[PandoraController] start completed"


    def stop(self):
        print "[PandoraController] stop entered"
        self.isRunning = False


    def join(self):
        print "[PandoraController] join entered"
        self.commandThread.join()
        self.eventThread.join()
        self.displayThread.join()
        print "[PandoraController] join completed"


    def processEvents(self):
        print "[PandoraController] Event processing thread executing."
        while self.isRunning and self.isEventThreadRunning:
            # self.eventFifo = open(self.eventFifoPath, "r")
            with open(self.eventFifoPath, 'r') as fifo:
                print "[PandoraController.processEvents] eventFifo is opened."
                nextEvent = fifo.read().strip()
                # print("[PandoraController.processEvents] event: %s\n" % (nextEvent,))
                tokens = nextEvent.split("\n")
                # print("[PandoraController.processEvents] tokens: %s" % (tokens,))
                event = tokens[0]
                print "[PandoraController.processEvents]     event: ", event
                if event == PandoraEvent.SONG_START:
                    print "[PandoraController.processEvents] SONG_START event intercepted"
                    del(tokens[0])
                    for dataParameter in tokens:
                        print "[PandoraController.processEvents]   data parameter: ", dataParameter
                        parameterName = dataParameter.split("=")[0]
                        parameterValue = dataParameter.split("=")[1]
                        print "[PandoraController.processEvents]     name: ", parameterName
                        print "[PandoraController.processEvents]     value: ", parameterValue
                        if parameterName == PandoraData.STATION_NAME:
                            self.stationTitle = parameterValue
                        elif parameterName == PandoraData.ARTIST:
                            self.artist = parameterValue
                        elif parameterName == PandoraData.TITLE:
                            self.songTitle = parameterValue
                        elif parameterName == PandoraData.ALBUM:
                            self.albumTitle = parameterValue




        print "[PandoraController] Event processing thread terminated."


    def processCommands(self):
        print "[PandoraController] Command processing thread executing."
        # self.commandFifo = open(self.commandFifoPath, "w")
        while self.isRunning and self.isCommandThreadRunning:
            # print("[PandorController.processCommands]  isRunning: %s, isCommandThreadRunning: %s" % (self.isRunning, self.isCommandThreadRunning))
            time.sleep(1)
        print "[PandoraController] Command processing thread terminated."


    def refreshDisplay(self):
        print "[PandoraController] Display thread executing"
        lastStationTitle = ""
        lastSongTitle = ""
        lastArtist = ""
        lastAlbum = ""
        cycleCounter = 0
        while self.isRunning and self.isDisplayThreadRunning:
            if cycleCounter >= 10:
                cycleCounter = 0
            if self.stationTitle != lastStationTitle or cycleCounter == 0:
                print("Station name change.  Was: %s, Now: %s" % (lastStationTitle, self.stationTitle))
                self.display.setPosition(PandoraController.STATION_TITLE_POSITION["line"], PandoraController.STATION_TITLE_POSITION["position"])
                stationTitle = self.stationTitle.ljust(20, ' ')
                if len(stationTitle) > 20:
                    stationTitle = stationTitle[:20]
                self.display.writeString(stationTitle)
                lastStationTitle = self.stationTitle

            if self.songTitle != lastSongTitle or cycleCounter == 0:
                print("Song title change.  Was: %s, Now: %s" % (lastSongTitle, self.songTitle))
                songTitle = self.songTitle.ljust(20, ' ')
                if len(songTitle) > 20:
                    songTitle = songTitle[:20]
                self.display.setPosition(PandoraController.SONG_TITLE_POSITION["line"], PandoraController.SONG_TITLE_POSITION["position"])
                self.display.writeString(songTitle)
                lastSongTitle = self.songTitle

            if self.artist != lastArtist or cycleCounter == 0:
                print("Artist change.  Was: %s, Now: %s" % (lastArtist, self.artist))
                artist = self.artist.ljust(20, ' ')
                if len(artist) > 20:
                    artist = artist[:20]
                self.display.setPosition(PandoraController.ARTIST_POSITION["line"], PandoraController.ARTIST_POSITION["position"])
                self.display.writeString(artist)
                lastArtist = self.artist

            if self.albumTitle != lastAlbum or cycleCounter == 0: 
                print("Album name change.  Was: %s, Now: %s" % (lastAlbum, self.albumTitle))
                album = self.albumTitle.ljust(20, ' ')
                if len(album) > 20:
                    album = album[:20]
                self.display.setPosition(PandoraController.ALBUM_TITLE_POSITION["line"], PandoraController.ALBUM_TITLE_POSITION["position"])
                self.display.writeString(album)
                lastAlbum = self.albumTitle
            # self.display.setPosition(PandoraController.TIME_POSITION["line"], PandoraController.TIME_POSITION["position"])
            # posMins = "{0:02d}".format(self.positionMinutes)
            # posSecs = "{0:02d}".format(self.positionSeconds)
            # durMins = "{0:02d}".format(self.durationMinutes)
            # durSecs = "{0:02d}".format(self.durationSeconds)
            # self.display.writeString(posMins + ":" + posSecs + "/" + durMins  + ":" + durSecs)
            cycleCounter += 1
            time.sleep(1)
        print "[PandoraController] Display thread terminating"


def main():
    pandoraController = PandoraController()

    pandoraController.start()

    while pandoraController.isRunning:
        try :
            time.sleep(1)
        except KeyboardInterrupt:
            print "Keyboard interrupt detected."
            pandoraController.stop();

    pandoraController.join()
    print "Exiting."

if __name__ == '__main__':
    main()
