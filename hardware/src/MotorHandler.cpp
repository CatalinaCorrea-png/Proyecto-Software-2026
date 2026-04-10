#include "MotorHandler.h"

namespace Drone {

uint8_t MotorHandler::_speed = 0;

void MotorHandler::init() {
  ledcSetup(_pwmChannel, _pwmFreq, _pwmResolution);
  ledcAttachPin(_pwmPin, _pwmChannel);
}

void MotorHandler::onUpdate() {
  ledcWrite(_pwmChannel, _speed);
}

void MotorHandler::setSpeed(uint8_t speed) {
  _speed = speed;
}

}  // namespace Drone
