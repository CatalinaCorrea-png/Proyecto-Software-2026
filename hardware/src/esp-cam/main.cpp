#include <Arduino.h>
#include "Server.h"

Drone::Server server;

void setup() {
  Serial.begin(115200);
  // UART hacia ESP32-C3 — pines definidos en pch.h
  Serial2.begin(115200, SERIAL_8N1, UART_C3_RX_PIN, UART_C3_TX_PIN);
  server.init(Serial2);
}

void loop() {
  server.handleClient();
  server.handleUDP();
  server.handleUART();
  server.sendPeriodicTelemetry();
}
