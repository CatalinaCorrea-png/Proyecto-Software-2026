#pragma once

#include <Arduino.h>

#define DEBUG  // comment this define to disable prints

#ifdef DEBUG
  #define PRINT(...) Serial.printf(__VA_ARGS__)
#else
  #define PRINT()
#endif

#define MOTOR_PIN1 13
#define MOTOR_PIN2 14
#define MOTOR_PIN3 15
#define MOTOR_PIN4 2

#define MPU_SDA
#define MPU_SLC

namespace Drone {

constexpr float ACC_SCALE = 16384.0f;
constexpr float GYRO_SCALE = 131.0f;

}  // namespace Drone
