#include "Controller.h"
#include "MotorHandler.h"

namespace Drone {

void Controller::init() {
  BP32.setup([this](GamepadPtr gp) { this->onConnectedGamepad(gp); },
             [this](GamepadPtr gp) { this->onDisconnectedGamepad(gp); });

  BP32.forgetBluetoothKeys();
}

void Controller::onUpdate(bool updated) {
  if (updated && _gamepad && _gamepad->isConnected()) {
    int ly = _gamepad->axisY();
    int ry = _gamepad->axisRY();

    int speed = (ly < -DEAD_ZONE) ? constrain(map(-ly, DEAD_ZONE, 512, 0, 255), 0, 255) : 0;

    MotorHandler::setSpeed(speed);

    Serial.printf("LY: %4d → Motor1: %3d", ly, speed);
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
