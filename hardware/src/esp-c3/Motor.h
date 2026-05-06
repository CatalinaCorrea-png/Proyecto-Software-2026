#pragma once
#include <Arduino.h>

namespace Drone {

class Motor {

public:
  Motor() = default;
  Motor(int pwmPin, int pwmChannel) : _pwmPin(pwmPin), _pwmChannel(pwmChannel) {};

  void init(int pwmPin, int pwmChannel);
  void onUpdate();
  void setSpeed(uint8_t speed);

private:
  uint8_t _speed;
  int _pwmPin;
  int _pwmChannel;
  int _pwmFreq = 20000;
  int _pwmResolution = 8;
};
}  // namespace Drone
