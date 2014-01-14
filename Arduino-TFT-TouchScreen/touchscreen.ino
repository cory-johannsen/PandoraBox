// Arduino-TFT-TouchScreen driver with serial interface

#include <stdint.h>
#include <TFT.h>
#include <TouchScreen.h>
#include <CmdMessenger.h>

#define MEGA

#ifdef SEEEDUINO
  #define YP A2   // must be an analog pin, use "An" notation!
  #define XM A1   // must be an analog pin, use "An" notation!
  #define YM 14   // can be a digital pin, this is A0
  #define XP 17   // can be a digital pin, this is A3 
#endif

#ifdef MEGA
  #define YP A2   // must be an analog pin, use "An" notation!
  #define XM A1   // must be an analog pin, use "An" notation!
  #define YM 54   // can be a digital pin, this is A0
  #define XP 57   // can be a digital pin, this is A3 
#endif

//Measured ADC values for (0,0) and (210-1,320-1)
//TS_MINX corresponds to ADC value when X = 0
//TS_MINY corresponds to ADC value when Y = 0
//TS_MAXX corresponds to ADC value when X = 240 -1
//TS_MAXY corresponds to ADC value when Y = 320 -1

#define TS_MINX 188
#define TS_MAXX 813
#define TS_MINY 169
#define TS_MAXY 874

#define MINPRESSURE 10
#define MAXPRESSURE 1000

String mChannelTitle = "";
String mSongTitle = "";
String mAlbumTitle = "";
int mSongDurationMinutes = 0;
int mSongDurationSeconds = 0;
int mSongPositionMinutes = 0;
int mSongPositionSeconds = 0;


// For better pressure precision, we need to know the resistance
// between X+ and X- Use any multimeter to read it
// For the one we're using, its 300 ohms across the X plate
TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300);
CmdMessenger cmdMessenger = CmdMessenger(Serial1);

void paintLine(int line, String text) {
  char buffer[13];
  memset(buffer, 0, 13);
  text.toCharArray(buffer, 13);
  Tft.drawString(buffer, line * 30, 320, 3, WHITE);
}

void repaint() {
  Tft.paintScreenBlack();
  paintLine(0, mChannelTitle);
  paintLine(1, mSongTitle);
  paintLine(2, mAlbumTitle);
  char buffer[13];
  memset(buffer, 0, 13);
  sprintf(buffer, " %02d:%02d/%02d:%02d", 
    mSongPositionMinutes, mSongPositionSeconds, mSongDurationMinutes, mSongDurationSeconds);
  String timeString(buffer);
  paintLine(3, timeString);
}

// Enumerated definition of support commands
enum {
  CMD_STATUS,
  CMD_CLEAR_SCREEN,
  CMD_SET_CHANNEL_TITLE,
  CMD_SET_SONG_TITLE,
  CMD_SET_ALBUM_TITLE,
  CMD_SET_SONG_DURATION,
  CMD_SET_SONG_POSITION,
  CMD_ACTION_THUMBS_UP,
  CMD_ACTION_THUMBS_DOWN,
  CMD_ACTION_PLAY,
  CMD_ACTION_STOP,
  CMD_ACTION_NEXT_SONG,
  CMD_ACTION_PREV_CHANNEL,
  CMD_ACTION_NEXT_CHANNEL,
  CMD_ERROR,
};

// define the command callbacks
void onUnknownCommand() {
  Serial.println("CMD - onUnknownCommand");
  cmdMessenger.sendCmd(CMD_ERROR, "Unknown command");
}

void onStatus() {
  Serial.println("CMD - onStatus");
  cmdMessenger.sendCmdStart(CMD_STATUS);
  cmdMessenger.sendCmdArg(mChannelTitle);
  cmdMessenger.sendCmdArg(mSongTitle);
  cmdMessenger.sendCmdArg(mSongDurationMinutes);
  cmdMessenger.sendCmdArg(mSongDurationSeconds);
  cmdMessenger.sendCmdArg(mSongPositionMinutes);
  cmdMessenger.sendCmdArg(mSongPositionSeconds);
  cmdMessenger.sendCmdEnd();
}

void onClearScreen() {
  Serial.println("CMD - onClearScreen");
  cmdMessenger.sendCmd(CMD_CLEAR_SCREEN, "Screen clear");
  repaint();
}

void onSetChannelTitle() {
  Serial.println("CMD - onSetChannelTitle");
  mChannelTitle = cmdMessenger.readStringArg();
  cmdMessenger.sendCmd(CMD_SET_CHANNEL_TITLE, mChannelTitle);
  repaint();
}

void onSetSongTitle() {
  Serial.println("CMD - onSetSongTitle");
  mSongTitle = cmdMessenger.readStringArg();
  cmdMessenger.sendCmd(CMD_SET_SONG_TITLE, mSongTitle);
  repaint();
}

void onSetAlbumTitle() {
  Serial.println("CMD - onSetAlbumTitle");
  mAlbumTitle = cmdMessenger.readStringArg();
  cmdMessenger.sendCmd(CMD_SET_ALBUM_TITLE, mAlbumTitle);
  repaint();
}

void onSetSongDuration() {
  Serial.println("CMD - onSetSongDuration");
  mSongDurationMinutes = cmdMessenger.readIntArg();
  mSongDurationSeconds = cmdMessenger.readIntArg();
  cmdMessenger.sendCmdStart(CMD_SET_SONG_DURATION);
  cmdMessenger.sendCmdArg(mSongDurationMinutes);
  cmdMessenger.sendCmdArg(mSongDurationSeconds);
  cmdMessenger.sendCmdEnd();
  repaint();
}

void onSetSongPosition() {
  Serial.println("CMD - onSetSongPosition");
  mSongPositionMinutes = cmdMessenger.readIntArg();
  mSongPositionSeconds = cmdMessenger.readIntArg();
  cmdMessenger.sendCmdStart(CMD_SET_SONG_POSITION);
  cmdMessenger.sendCmdArg(mSongPositionMinutes);
  cmdMessenger.sendCmdArg(mSongPositionSeconds);
  cmdMessenger.sendCmdEnd();
  repaint();
}

void attachCommandCallbacks() {
  cmdMessenger.attach(onUnknownCommand);
  cmdMessenger.attach(CMD_STATUS, onStatus);
  cmdMessenger.attach(CMD_CLEAR_SCREEN, onClearScreen);
  cmdMessenger.attach(CMD_SET_CHANNEL_TITLE, onSetChannelTitle);
  cmdMessenger.attach(CMD_SET_SONG_TITLE, onSetSongTitle);
  cmdMessenger.attach(CMD_SET_ALBUM_TITLE, onSetAlbumTitle);
  cmdMessenger.attach(CMD_SET_SONG_DURATION, onSetSongDuration);
  cmdMessenger.attach(CMD_SET_SONG_POSITION, onSetSongPosition);
}

void setup(void) {
  Serial.begin(9600);
  Serial.println("Initializing TFT...");
  Tft.init();
  Serial.println("Setting pin 0 mode to output...");
  pinMode(0,OUTPUT);
  Serial.println("Switching display to landscape mode...");
  Tft.setOrientation(0);
  Serial.println("Switching display direction...");
  Tft.setDisplayDirect(DOWN2UP);
  Serial.println("Drawing text to screen...");
  Tft.drawString("Channel", 0, 320, 3, WHITE);
  Tft.drawString("Song Title", 30, 320, 3, WHITE);
  Tft.drawString("Album Title", 60, 320, 3, WHITE);
  Tft.drawString("00:00 / 00:00", 90, 320, 3, WHITE);
  
  Serial.println("Initializing serial port 1...");
  Serial1.begin(115200);

  Serial.println("Configuring CmdMessenger for CRLF...");
  cmdMessenger.printLfCr();

  Serial.println("Attaching command callbacks...");
  attachCommandCallbacks();
}

void loop(void) {
  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();

  // a point object holds x y and z coordinates
  Point p = ts.getPoint();
  
  // we have some minimum pressure we consider 'valid'
  // pressure of 0 means no pressing!
  if (p.z > MINPRESSURE && p.z < MAXPRESSURE) {
    Serial.print("X = "); 
    Serial.print(p.x);
    Serial.print("\tY = "); 
    Serial.print(p.y);
    Serial.print("\tPressure = "); 
    Serial.println(p.z);

    cmdMessenger.sendCmd(CMD_SET_CHANNEL_TITLE, "Testing");
  }

}
