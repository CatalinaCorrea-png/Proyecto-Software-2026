#pragma once

#include <Arduino.h>
#include <Bluepad32.h>

namespace Drone {

class Controller {
public:
  const int pwmPin = 18;
  const int pwmPin2 = 19;
  const int pwmChannel = 0;
  const int pwmChannel2 = 1;
  const int pwmFreq = 20000;
  const int pwmResolution = 8;
  const int DEAD_ZONE = 10;

  void init();
  inline bool getUpdated() { return BP32.update(); }
  void onUpdate(bool updated);
  void onConnectedGamepad(GamepadPtr gp);
  void onDisconnectedGamepad(GamepadPtr gp);

private:
  GamepadPtr _gamepad;
};

}  // namespace Drone
