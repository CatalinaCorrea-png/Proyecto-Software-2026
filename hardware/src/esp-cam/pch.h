#pragma once

#include <Arduino.h>
#include <stdint.h>

#define DEBUG
#ifdef DEBUG
  #define PRINT(...) Serial.printf(__VA_ARGS__)
#else
  #define PRINT(...)
#endif

// UART hacia ESP32-C3 — verificar pines disponibles en tu placa AI-Thinker
#define UART_C3_RX_PIN  14
#define UART_C3_TX_PIN  15

#define UDP_PORT     4210
#define UDP_TX_PORT  4211

#include "Timer.h"

inline Timer debugTimer(200);
