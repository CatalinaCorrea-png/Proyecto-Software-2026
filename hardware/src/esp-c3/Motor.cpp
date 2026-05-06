#include "Motor.h"

namespace Drone {

void Motor::init(int pwmPin, int pwmChannel) {
  _pwmPin = pwmPin;
  _pwmChannel = pwmChannel;
  ledcSetup(_pwmChannel, _pwmFreq, _pwmResolution);
  ledcAttachPin(_pwmPin, _pwmChannel);
}

void Motor::onUpdate() {
  ledcWrite(_pwmChannel, _speed);
}

void Motor::setSpeed(uint8_t speed) {
  _speed = speed;
}

}  // namespace Drone
