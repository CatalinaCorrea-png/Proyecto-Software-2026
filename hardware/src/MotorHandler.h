#pragma once
#include <Arduino.h>

namespace Drone {

class MotorHandler {

public:
  void init();
  void onUpdate();
  static void setSpeed(uint8_t speed);

private:
  static uint8_t _speed;
  const int _pwmPin = 18;
  const int _pwmChannel = 0;
  const int _pwmFreq = 20000;
  const int _pwmResolution = 8;
};
}  // namespace Drone
