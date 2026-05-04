#pragma once

namespace Drone {

class PID {
public:
  PID(float kp, float ki, float kd, float integralLimit = 200.0f)
    : _kp(kp), _ki(ki), _kd(kd), _integralLimit(integralLimit) {}

  float compute(float setpoint, float measured, float dt);
  void reset();

private:
  float _kp, _ki, _kd;
  float _integralLimit;
  float _integral = 0;
  float _lastError = 0;
};

}  // namespace Drone
