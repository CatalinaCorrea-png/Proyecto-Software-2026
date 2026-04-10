#include "Controller.h"

namespace Drone {

void Controller::init() {
  ledcSetup(pwmChannel, pwmFreq, pwmResolution);
  ledcSetup(pwmChannel2, pwmFreq, pwmResolution);
  ledcAttachPin(pwmPin, pwmChannel);
  ledcAttachPin(pwmPin2, pwmChannel2);
  BP32.setup([this](GamepadPtr gp) { this->onConnectedGamepad(gp); },
             [this](GamepadPtr gp) { this->onDisconnectedGamepad(gp); });

  BP32.forgetBluetoothKeys();
}

void Controller::onUpdate(bool updated) {
  if (updated && _gamepad && _gamepad->isConnected()) {
    int ly = _gamepad->axisY();
    int ry = _gamepad->axisRY();

    int speed = (ly < -DEAD_ZONE) ? constrain(map(-ly, DEAD_ZONE, 512, 0, 255), 0, 255) : 0;
    int speed2 = (ry < -DEAD_ZONE) ? constrain(map(-ry, DEAD_ZONE, 512, 0, 255), 0, 255) : 0;

    ledcWrite(pwmChannel, speed);
    ledcWrite(pwmChannel2, speed2);

    Serial.printf("LY: %4d → Motor1: %3d | RY: %4d → Motor2: %3d\n", ly, speed, ry, speed2);
  }
}

void Controller::onConnectedGamepad(GamepadPtr gp) {
  Serial.println("Joystick conectado!");
  _gamepad = gp;
}

void Controller::onDisconnectedGamepad(GamepadPtr gp) {
  Serial.println("Joystick desconectado");
  _gamepad = nullptr;
}

}  // namespace Drone
