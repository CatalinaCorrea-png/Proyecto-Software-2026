#pragma once

#include <Arduino.h>
#include <stdint.h>

#define DEBUG  // comment this define to disable prints

#ifdef DEBUG
  #define PRINT(...) Serial.printf(__VA_ARGS__)
#else
  #define PRINT(...)
#endif

#define MOTOR_PIN1 13
#define MOTOR_PIN2 14
#define MOTOR_PIN3 15
#define MOTOR_PIN4 2

#define MPU_SDA_PIN 12  // free pin (SD not used); keep LOW at boot
#define MPU_SCL_PIN 4   // free pin (onboard flash LED — will flicker with I2C activity)

#define UDP_PORT 4210
#define UDP_TX_PORT 4211
