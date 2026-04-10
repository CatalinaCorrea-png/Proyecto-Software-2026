#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "Math.h"
#include "DeltaTime.h"

namespace Drone {

struct IMUData {
  Vec3 acc;
  Vec3 gyro;
};

class FlyHandler {
public:
  void init();
  void beginRead();
  void onUpdate(DeltaTime dt);
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
