#include "PID.h"

namespace Drone {

float PID::compute(float setpoint, float measured, float dt) {
  if (dt <= 0.0f)
    return 0.0f;

  float error = setpoint - measured;
  _integral += error * dt;
  if (_integral > _integralLimit)
    _integral = _integralLimit;
  if (_integral < -_integralLimit)
    _integral = -_integralLimit;
  float derivative = (error - _lastError) / dt;
  _lastError = error;
  return _kp * error + _ki * _integral + _kd * derivative;
}

void PID::reset() {
  _integral = 0;
  _lastError = 0;
}

}  // namespace Drone
