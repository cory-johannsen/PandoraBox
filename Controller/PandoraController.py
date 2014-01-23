#!/usr/bin/python
import serial
import subprocess
import threading
import time
import Queue


def enum(**enums):
        return type('Enum', (), enums)


CommandType = enum(
    CMD_STATUS=0,
    CMD_CLEAR_SCREEN=1,
    CMD_SET_CHANNEL_TITLE=2,
    CMD_SET_SONG_TITLE=3,
    CMD_SET_ARTIST=4,
    CMD_SET_ALBUM_TITLE=5,
    CMD_SET_SONG_DURATION=6,
    CMD_SET_SONG_POSITION=7,
    CMD_ACTION_THUMBS_UP=8,
    CMD_ACTION_THUMBS_DOWN=9,
    CMD_ACTION_PLAY=10,
    CMD_ACTION_STOP=11,
    CMD_ACTION_NEXT_SONG=12,
    CMD_ACTION_PREV_CHANNEL=13,
    CMD_ACTION_NEXT_CHANNEL=14,
    CMD_ERROR=15
)


class PandoraController(object):

    def __init__(self, tty, baudRate):
        #print "__init__ entered"
        self.tty = tty
        self.baudRate = baudRate
        self.ttfSerial = serial.Serial(tty, baudRate)
        self.isRunning = True
        self.isInputThreadRunning = False
        self.isOutputThreadRunning = False
        self.isPianomanRunning = False
        self.mChannelTitle = "Channel"
        self.mChannelId = ""
        self.mSongTitle = "Song Title"
        self.mArtist = "Artist"
        self.mAlbumTitle = "Album Title"
        self.mDurationMinutes = 0
        self.mDurationSeconds = 0
        self.mPositionMinutes = 0
        self.mPositionSeconds = 0
        self.mCommandQueue = Queue.Queue()

    def start(self):
        #print "start entered"
        self.isRunning = True

        #print "Starting console."
        self.consoleThread = threading.Thread(target=self.processConsoleInput)
        self.consoleThread.setDaemon(True)
        self.consoleThread.start()

        self.isInputThreadRunning = True
        self.inputThread = threading.Thread(target=self.receive)
        self.inputThread.setDaemon(True)
        self.inputThread.start()

        self.isOutputThreadRunning = True
        self.outputThread = threading.Thread(target=self.transmit)
        self.outputThread.setDaemon(True)
        self.outputThread.start()

        #print "starting pianobar process."
        self.isPianobarRunning = True
        self.pianobarProcess = subprocess.Popen("/usr/local/bin/pianobar", 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE)
        self.pianobarStdoutThread = threading.Thread(target=self.processPianobarStdout)
        self.pianobarStdoutThread.setDaemon(True)
        self.pianobarStdoutThread.start()
        self.pianobarStderrThread = threading.Thread(target=self.processPianobarStderr)
        self.pianobarStderrThread.setDaemon(True)
        self.pianobarStderrThread.start()

    def stop(self):
        #print "stop entered"
        self.isRunning = False

    def join(self):
        self.consoleThread.join()
        self.inputThread.join()
        self.outputThread.join()
        self.pianobarThread.join()

    def processConsoleInput(self):
        while self.isRunning:
            consoleCommand = raw_input(">>")
            if "exit" in consoleCommand:
                self.isRunning = False
            else:
                print "Unknown command: " + consoleCommand

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

    def receive(self):
        print "receive entered"
        try:
            while self.isRunning and self.isInputThreadRunning:
                nextCommand = self.ttfSerial.readline()
                commandFields = nextCommand.split(",")
                if commandFields[0] == CommandType.CMD_ACTION_THUMBS_DOWN:
                    print "Thumbs down received."
                if commandFields[0] == CommandType.CMD_ACTION_THUMBS_UP:
                    print "Thumbs down received."
                # print "COMMAND: " + nextCommand
                # self.pianomanCtl = open("/home/root/.config/pianobar/ctl", "w")

        except serial.SerialException, ex:
            self.isRunning = False
            print ex
            raise

    def transmit(self):
        print "transmit entered"
        try:
            while self.isRunning and self.isOutputThreadRunning:
                nextCommand = self.mCommandQueue.get()
                if nextCommand == CommandType.CMD_SET_CHANNEL_TITLE:
                    self.ttfSerial.write("%s,%s;\r\n" %
                                        (CommandType.CMD_SET_CHANNEL_TITLE,
                                        self.mChannelTitle))
                elif nextCommand == CommandType.CMD_SET_SONG_TITLE:
                    self.ttfSerial.write("%s,%s;\r\n" %
                                        (CommandType.CMD_SET_SONG_TITLE,
                                        self.mSongTitle))
                elif nextCommand == CommandType.CMD_SET_ARTIST:
                    self.ttfSerial.write("%s,%s;\r\n" %
                                        (CommandType.CMD_SET_ARTIST,
                                        self.mArtist))
                elif nextCommand == CommandType.CMD_SET_ALBUM_TITLE:
                    self.ttfSerial.write("%s,%s;\r\n" %
                                        (CommandType.CMD_SET_ALBUM_TITLE,
                                        self.mAlbumTitle))
                elif nextCommand == CommandType.CMD_SET_SONG_DURATION:
                    self.ttfSerial.write("%s,%s,%s;\r\n" %
                                        (CommandType.CMD_SET_SONG_DURATION,
                                        self.mDurationMinutes,
                                        self.mDurationSeconds))
                elif nextCommand == CommandType.CMD_SET_SONG_POSITION:
                    self.ttfSerial.write("%s,%s,%s;\r\n" %
                                        (CommandType.CMD_SET_SONG_POSITION,
                                        self.mPositionMinutes,
                                        self.mPositionSeconds))

        except serial.SerialException, ex:
            self.isRunning = False
            print ex
            raise


def main():
    pandoraController = PandoraController('/dev/ttyO1', 115200)

    pandoraController.start()
    pandoraController.join()

if __name__ == '__main__':
    main()
