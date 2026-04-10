#pragma once
#include <Arduino.h>

namespace Drone {

class Motor {

public:
  Motor(int pwmPin, int pwmChannel) : _pwmPin(pwmPin), _pwmChannel(pwmChannel) {}

  void init();
  void onUpdate();
  void setSpeed(uint8_t speed);

private:
  uint8_t _speed;
  const int _pwmPin;
  const int _pwmChannel;
  const int _pwmFreq = 20000;
  const int _pwmResolution = 8;
};
}  // namespace Drone
