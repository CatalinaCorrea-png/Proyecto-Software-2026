#include "PID.h"

namespace Drone {

float PID::compute(float setpoint, float measured, float dt) {
  float error = setpoint - measured;
  _integral += error * dt;
  float derivative = (error - _lastError) / dt;
  _lastError = error;
  return _kp * error + _ki * _integral + _kd * derivative;
}

void PID::reset() {
  _integral = 0;
  _lastError = 0;
}

}  // namespace Drone
