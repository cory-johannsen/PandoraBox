#!/usr/bin/python
import subprocess
import threading
import time
import Queue
import enum
import display


class PandoraController(object):
    STATION_TITLE_POSITION={"line":0,"position":0} 
    SONG_TITLE_POSITION={"line":1,"position":0}
    ARTIST_POSITION={"line":2,"position":0} 
    ALBUM_TITLE_POSITION={"line":2,"position":10} 
    TIME_POSITION={"line":3,"position":0} 

    def __init__(self, tty, baudRate):
        #print "__init__ entered"
        self.isRunning = True
        self.mStationTitle = "Channel"
        self.mStationId = ""
        self.mSongTitle = "Song Title"
        self.mArtist = "Artist"
        self.mAlbumTitle = "Album"
        self.mDurationMinutes = 0
        self.mDurationSeconds = 0
        self.mPositionMinutes = 0
        self.mPositionSeconds = 0
        self.display = display.Display()


    def start(self):
        #print "start entered"
        self.isRunning = True

        self.display.initialize()
        self.isDisplayThreadRunning = True
        self.displayThread = threading.Thread(target=self.refreshDisplay)
        self.displayThread.daemon = True
        self.displayThread.start()

        #print "starting pianobar process."
        # self.isPianobarRunning = True
        # self.pianobarProcess = subprocess.Popen("/usr/local/bin/pianobar", 
        #         stdin=subprocess.PIPE, 
        #         stdout=subprocess.PIPE, 
        #         stderr=subprocess.PIPE)
        # self.pianobarStdoutThread = threading.Thread(target=self.processPianobarStdout)
        # self.pianobarStdoutThread.setDaemon(True)
        # self.pianobarStdoutThread.start()
        # self.pianobarStderrThread = threading.Thread(target=self.processPianobarStderr)
        # self.pianobarStderrThread.setDaemon(True)
        # self.pianobarStderrThread.start()


    def stop(self):
        #print "stop entered"
        self.isRunning = False


    def join(self):
        # self.pianobarThread.join()
        self.displayThread.join()


    def refreshDisplay(self):
        self.display.setPosition(PandoraController.STATION_TITLE_POSITION["line"], PandoraController.STATION_TITLE_POSITION["position"])
        self.display.writeString(self.mStationTitle)
        self.display.setPosition(PandoraController.SONG_TITLE_POSITION["line"], PandoraController.SONG_TITLE_POSITION["position"])
        self.display.writeString(self.mSongTitle)
        self.display.setPosition(PandoraController.ARTIST_POSITION["line"], PandoraController.ARTIST_POSITION["position"])
        self.display.writeString(self.mArtist)
        self.display.setPosition(PandoraController.ALBUM_TITLE_POSITION["line"], PandoraController.ALBUM_TITLE_POSITION["position"])
        self.display.writeString(self.mAlbumTitle)
        self.display.setPosition(PandoraController.TIME_POSITION["line"], PandoraController.TIME_POSITION["position"])
        self.display.writeString("00:00 / 00:00")


    def processPianobarStdout(self):
        print "processPianobarStdout entered"
        outputBuffer = ""
        lastTimeUpdate = 0
        lastRedraw = 0
        while self.isRunning and self.isPianobarRunning:
            nextChar = self.pianobarProcess.stdout.read(1)
            if nextChar == '' and self.pianobarProcess.stdout.poll() != None:
                self.isPianobarRunning = False
            if nextChar != '':
                if nextChar != '\r':
                    outputBuffer += nextChar
                else:    
                    # A full line has arrived from pianobar, decode it
                    currentTime = time.time()
                    # print ("currentTime: %s, lastTimeUpdate: %s" % (currentTime, lastTimeUpdate))
                    pianobarOutput = outputBuffer.strip()
                    if pianobarOutput.find(" Station") >= 0:
                        print "PIANOBAR out: " + pianobarOutput
                        parts = pianobarOutput.split('"')
                        # print "  parts:"
                        # print parts
                        self.mChannelTitle = parts[1]
                        self.mChannelId = parts[2]
                        print "Channel title: " + self.mChannelTitle
                        self.mCommandQueue.put(CommandType.CMD_SET_CHANNEL_TITLE)
                    if pianobarOutput.find(" Song") >= 0:
                        print "PIANOBAR out: " + pianobarOutput
                        parts = pianobarOutput.split('"')
                        if len(parts) >= 5:
                            print "  parts:"
                            print parts
                            self.mSongTitle = parts[1]
                            self.mArtist = parts[3]
                            self.mAlbumTitle = parts[5]
                            print "Song title: " + self.mSongTitle
                            print "Artist: " + self.mArtist
                            print "Album title: " + self.mAlbumTitle
                            self.mCommandQueue.put(CommandType.CMD_SET_SONG_TITLE)
                            self.mCommandQueue.put(CommandType.CMD_SET_ARTIST)
                            self.mCommandQueue.put(CommandType.CMD_SET_ALBUM_TITLE)
                    if pianobarOutput.find(" Time") >= 0:
                        # print "PIANOBAR out: " + pianobarOutput
                        parts = pianobarOutput.split('"')
                        # print "  parts:"
                        # print parts
                        if len(parts) >= 2:
                            parts = parts[2].split("/")
                            if len(parts) >= 2:
                                remainingTime = parts[0].split(":")
                                totalTime = parts[1].split(":")
                                minutesRemaining = remainingTime[0]
                                secondsRemaining = remainingTime[1]
                                totalMinutes = totalTime[0]
                                totalSeconds = totalTime[1]
                                if int(totalMinutes) != int(self.mDurationMinutes) or int(totalSeconds) != int(self.mDurationSeconds):
                                    self.mDurationMinutes = int(totalMinutes)
                                    self.mDurationSeconds = int(totalSeconds)
                                    self.mCommandQueue.put(CommandType.CMD_SET_SONG_DURATION)
                                if int(minutesRemaining) != int(self.mPositionMinutes) or int(secondsRemaining) != int(self.mPositionSeconds):
                                    self.mPositionMinutes = abs(int(minutesRemaining))
                                    self.mPositionSeconds = int(secondsRemaining)
                                    if currentTime - lastTimeUpdate >= 3:
                                        self.mCommandQueue.put(CommandType.CMD_SET_SONG_POSITION)
                                        lastTimeUpdate = currentTime

                    if currentTime - lastRedraw >= 10:
                        self.mCommandQueue.put(CommandType.CMD_SET_CHANNEL_TITLE)
                        self.mCommandQueue.put(CommandType.CMD_SET_SONG_TITLE)
                        self.mCommandQueue.put(CommandType.CMD_SET_ARTIST)
                        self.mCommandQueue.put(CommandType.CMD_SET_ALBUM_TITLE)
                        self.mCommandQueue.put(CommandType.CMD_SET_SONG_DURATION)
                        lastRedraw = currentTime


                    outputBuffer = ""


    def processPianobarStderr(self):
        print "processPianobarStderr entered"
        outputBuffer = ""
        while self.isRunning and self.isPianobarRunning:
            nextChar = self.pianobarProcess.stderr.read(1)
            if nextChar == '' and self.pianobarProcess.stderr.poll() != None:
                self.isPianobarRunning = False
            if nextChar != '':
                if nextChar != '\r' and nextChar != '\n':
                    outputBuffer += nextChar
                else:    
                    # A full line has arrived from pianobar, decode it
                    pianobarOutput = outputBuffer.strip()
                    # print "PIANOBAR err: " + pianobarOutput
                    outputBuffer = ""


def main():
    pandoraController = PandoraController('/dev/ttyO1', 115200)

    pandoraController.start()
    pandoraController.join()

if __name__ == '__main__':
    main()
