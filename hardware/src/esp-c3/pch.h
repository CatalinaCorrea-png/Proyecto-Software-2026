#pragma once

#include <Arduino.h>
#include <stdint.h>

#define DEBUG
#ifdef DEBUG
  #define PRINT(...) Serial.printf(__VA_ARGS__)
#else
  #define PRINT(...)
#endif

// Motores — pines PWM libres del C3
#define MOTOR_PIN1  2
#define MOTOR_PIN2  3
#define MOTOR_PIN3  4
#define MOTOR_PIN4  5

// MPU6050 I2C
#define MPU_SDA_PIN  6
#define MPU_SCL_PIN  7

// UART desde ESP32-CAM (Serial1)
#define UART_CAM_RX_PIN  8
#define UART_CAM_TX_PIN  9

#include "Timer.h"

inline Timer debugTimer(200);
