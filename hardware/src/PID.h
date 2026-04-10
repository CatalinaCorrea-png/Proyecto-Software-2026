class PID {
public:
  PID(float kp, float ki, float kd) : _kp(kp), _ki(ki), _kd(kd) {}

  float compute(float setpoint, float measured, float dt) {
    float error = setpoint - measured;
    _integral += error * dt;
    float derivative = (error - _lastError) / dt;
    _lastError = error;
    return _kp * error + _ki * _integral + _kd * derivative;
  }

  void reset() {
    _integral = 0;
    _lastError = 0;
  }

private:
  float _kp, _ki, _kd;
  float _integral = 0;
  float _lastError = 0;
};
