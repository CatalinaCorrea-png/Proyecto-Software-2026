#include "controller.h"

void Controller::setup() {
  ledcSetup(pwmChannel, pwmFreq, pwmResolution);
  ledcSetup(pwmChannel2, pwmFreq, pwmResolution);
  ledcAttachPin(pwmPin, pwmChannel);
  ledcAttachPin(pwmPin2, pwmChannel2);
  BP32.setup(&onConnectedGamepad, &onDisconnectedGamepad);
  BP32.forgetBluetoothKeys();
}

void Controller::onUpdate(bool updated) {
  if (updated && myGamepad && myGamepad->isConnected()) {
    int ly = myGamepad->axisY();
    int ry = myGamepad->axisRY();

    int speed = (ly < -DEAD_ZONE) ? constrain(map(-ly, DEAD_ZONE, 512, 0, 255), 0, 255) : 0;
    int speed2 = (ry < -DEAD_ZONE) ? constrain(map(-ry, DEAD_ZONE, 512, 0, 255), 0, 255) : 0;

    ledcWrite(pwmChannel, speed);
    ledcWrite(pwmChannel2, speed2);

    Serial.printf("LY: %4d → Motor1: %3d | RY: %4d → Motor2: %3d\n", ly, speed, ry, speed2);
  }
}

void Controller::onConnectedGamepad(GamepadPtr gp) {
  Serial.println("Joystick conectado!");
  myGamepad = gp;
}

void Controller::onDisconnectedGamepad(GamepadPtr gp) {
  Serial.println("Joystick desconectado");
  myGamepad = nullptr;
}
