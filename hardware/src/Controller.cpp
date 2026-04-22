#include "Controller.h"

namespace Drone {

// void Controller::init() {
//   BP32.setup([this](GamepadPtr gp) { this->onConnectedGamepad(gp); },
//              [this](GamepadPtr gp) { this->onDisconnectedGamepad(gp); });

//   BP32.forgetBluetoothKeys();
// }

// void Controller::onUpdate(bool updated) {
//   if (_gamepad && _gamepad->isConnected()) {
//     int ly = _gamepad->axisY();  // -512 arriba, +512 abajo

//     if (ly < -DEAD_ZONE) {
//       // stick arriba → sube throttle gradualmente
//       int delta = map(-ly, DEAD_ZONE, 512, 1, 5);
//       _throttle = constrain(_throttle + delta, 0, 255);
//     } else if (ly > DEAD_ZONE) {
//       // stick abajo → baja throttle gradualmente
//       int delta = map(ly, DEAD_ZONE, 512, 1, 5);
//       _throttle = constrain(_throttle - delta, 0, 255);
//     }

//     PRINT("Left Stick Y: %d\n", ly);
//     // stick en zona muerta → _throttle no cambia, mantiene altura
//   }
// }

// void Controller::onConnectedGamepad(GamepadPtr gp) {
//   PRINT("Joystick conectado!");
//   _gamepad = gp;
// }

// void Controller::onDisconnectedGamepad(GamepadPtr gp) {
//   PRINT("Joystick desconectado");
//   _gamepad = nullptr;
// }

}  // namespace Drone
