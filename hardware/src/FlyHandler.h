#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "Math.h"
#include "DeltaTime.h"
#include "Motor.h"
#include "PID.h"
#include "pch.h"

namespace Drone {

struct IMUData {
  Vec3 acc;
  Vec3 gyro;
};

class FlyHandler {
public:
  Motor motorFL;
  Motor motorFR;
  Motor motorBL;
  Motor motorBR;

  PID pidRoll{1.2f, 0.01f, 0.4f};
  PID pidPitch{1.2f, 0.01f, 0.4f};

  void init();
  void initIMU();
  void initGPS();
  void beginRead();
  void onUpdate(DeltaTime dt, int throttle);
  IMUData readIMU();

  float getRoll() { return _roll; };
  float getPitch() { return _pitch; };

private:
  uint8_t _address = 0x68;

  float _alpha = 0.98f;
  float _roll = 0;
  float _pitch = 0;
};

}  // namespace Drone
