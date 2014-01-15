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

#define DRAW_MIN_X 0
#define DRAW_MIN_Y 0
#define DRAW_MAX_X 240
#define DRAW_MAX_Y 320

String mChannelTitle = "Channel";
String mSongTitle = "Song Title";
String mAlbumTitle = "Album Title";
int mSongDurationMinutes = 0;
int mSongDurationSeconds = 0;
int mSongPositionMinutes = 0;
int mSongPositionSeconds = 0;
bool mButtonDown = false;
int mLastTouchX = -1;
int mLastTouchY = -1;
unsigned long mLastTouchEventTime = 0;

// For better pressure precision, we need to know the resistance
// between X+ and X- Use any multimeter to read it
// For the one we're using, its 300 ohms across the X plate
TouchScreen touchScreen = TouchScreen(XP, YP, XM, YM, 300);
CmdMessenger cmdMessenger = CmdMessenger(Serial1);

#define LINE_HEIGHT 30
#define LINE_POSITION 320
#define FONT_SIZE 3
#define LINE_BUFFER_SIZE 13
void paintLine(int line, String text) {
  char buffer[LINE_BUFFER_SIZE];
  memset(buffer, 0, LINE_BUFFER_SIZE);
  text.toCharArray(buffer, LINE_BUFFER_SIZE);
  Tft.drawString(buffer, line * LINE_HEIGHT, LINE_POSITION, FONT_SIZE, WHITE);
}

#define BUTTON_WIDTH 120
#define BUTTON_HEIGHT 60
#define BUTTON_TEXT_POSITION 200
void paintUpButton() {
  Tft.fillRectangle(DRAW_MAX_X - BUTTON_HEIGHT, 
                    DRAW_MIN_Y + BUTTON_WIDTH, 
                    BUTTON_HEIGHT, 
                    BUTTON_WIDTH, 
                    GREEN);
  Tft.drawString("UP", BUTTON_TEXT_POSITION, 75, FONT_SIZE, BLACK);
}

void paintDownButton() {
  Tft.fillRectangle(DRAW_MAX_X - BUTTON_HEIGHT, 
                    DRAW_MAX_Y, 
                    BUTTON_HEIGHT, 
                    BUTTON_WIDTH, 
                    RED);
  Tft.drawString("DOWN", BUTTON_TEXT_POSITION, 310, FONT_SIZE, BLACK);
}

#define CHANNEL_TITLE_LINE 0
#define SONG_TITLE_LINE 1
#define ALBUM_TITLE_LINE 2
#define TIME_LINE 3
void repaint() {
  Tft.paintScreenBlack();
  paintLine(CHANNEL_TITLE_LINE, mChannelTitle);
  paintLine(SONG_TITLE_LINE, mSongTitle);
  paintLine(ALBUM_TITLE_LINE, mAlbumTitle);
  char buffer[LINE_BUFFER_SIZE];
  memset(buffer, 0, LINE_BUFFER_SIZE);
  sprintf(buffer, " %02d:%02d/%02d:%02d", 
    mSongPositionMinutes, mSongPositionSeconds, mSongDurationMinutes, mSongDurationSeconds);
  String timeString(buffer);
  paintLine(TIME_LINE, timeString);
  paintUpButton();
  paintDownButton();

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
  
  Serial.println("Initializing serial port 1...");
  Serial1.begin(115200);

  Serial.println("Configuring CmdMessenger for CRLF...");
  cmdMessenger.printLfCr();

  Serial.println("Attaching command callbacks...");
  attachCommandCallbacks();

  Serial.println("Painting...");
  repaint();
}

#define DOWN_BUTTON_TOUCH_X_MIN 185
#define DOWN_BUTTON_TOUCH_Y_MIN 165
#define DOWN_BUTTON_TOUCH_X_MAX 300
#define DOWN_BUTTON_TOUCH_Y_MAX 430
bool isDownButton(int x, int y) {
  Serial.print();
  return (x >= DOWN_BUTTON_TOUCH_X_MIN) &&
         (x <= DOWN_BUTTON_TOUCH_X_MAX) &&
         (y >= DOWN_BUTTON_TOUCH_Y_MIN) &&
         (y <= DOWN_BUTTON_TOUCH_Y_MAX);
}

#define UP_BUTTON_TOUCH_X_MIN 185
#define UP_BUTTON_TOUCH_Y_MIN 635
#define UP_BUTTON_TOUCH_X_MAX 300
#define UP_BUTTON_TOUCH_Y_MAX 915
bool isUpButton(int x, int y) {
  return (x >= UP_BUTTON_TOUCH_X_MIN) &&
         (x <= UP_BUTTON_TOUCH_X_MAX) &&
         (y >= UP_BUTTON_TOUCH_Y_MIN) &&
         (y <= UP_BUTTON_TOUCH_Y_MAX);
}

#define BUTTON_EVENT_DELAY 1000
void loop(void) {
  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();

  int currentTime = millis();
  if (currentTime >= mLastTouchEventTime + BUTTON_EVENT_DELAY) {
    // Record when a touch event begins
    if (touchScreen.pressure() >= 10) {
      if (!mButtonDown) {
        Serial.println("Touch event starting.");
      }
      mButtonDown = true;
      mLastTouchX = touchScreen.readTouchX();
      mLastTouchY = touchScreen.readTouchY();
    }
    else {
      if (mButtonDown) {
        Serial.println("Touch event ended.");
        // The touch event has ended
        mButtonDown = false;
        if (isUpButton(mLastTouchX, mLastTouchY)) {
          cmdMessenger.sendCmd(CMD_ACTION_THUMBS_UP, "Thumbs Up");
        }
        if (isDownButton(mLastTouchX, mLastTouchY)) {
          cmdMessenger.sendCmd(CMD_ACTION_THUMBS_DOWN, "Thumbs Down");
        }
        mLastTouchEventTime = currentTime;
      }
      mLastTouchX = -1;
      mLastTouchY = -1;
    }
  }

}
