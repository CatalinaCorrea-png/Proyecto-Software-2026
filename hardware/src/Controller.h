#pragma once

#include <Arduino.h>
#include <Bluepad32.h>

namespace Drone {

class Controller {
public:
  const int DEAD_ZONE = 10;

  void init();
  inline bool getUpdated() { return BP32.update(); }
  void onUpdate(bool updated);
  void onConnectedGamepad(GamepadPtr gp);
  void onDisconnectedGamepad(GamepadPtr gp);

  int getThrottle() { return _throttle; }

private:
  GamepadPtr _gamepad;
  int _throttle = 0;
};

}  // namespace Drone
