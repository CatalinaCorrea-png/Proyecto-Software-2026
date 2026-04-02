#pragma once

#include <Arduino.h>
#include <Bluepad32.h>

class Controller {
public:
  GamepadPtr myGamepad;

  const int pwmPin = 18;
  const int pwmPin2 = 19;
  const int pwmChannel = 0;
  const int pwmChannel2 = 1;
  const int pwmFreq = 20000;
  const int pwmResolution = 8;
  const int DEAD_ZONE = 10;

  void setup();
  void onUpdate(bool updated);
  void onConnectedGamepad(GamepadPtr gp);
  void onDisconnectedGamepad(GamepadPtr gp);
};
