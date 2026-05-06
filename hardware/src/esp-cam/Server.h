#pragma once
#include <Arduino.h>
#include "Secrets.h"
#include <esp32cam.h>
#include <WiFi.h>
#include <WiFiUDP.h>
#include <WebServer.h>
#include "pch.h"
#include "Timer.h"

namespace Drone {

struct DroneData {
  float lat      = 0.0f;
  float lng      = 0.0f;
  float altitude = 0.0f;
  float speed    = 0.0f;
};

class Server {
public:
  Server() = default;

  esp32cam::Resolution loRes  = esp32cam::Resolution::find(320, 240);
  esp32cam::Resolution midRes = esp32cam::Resolution::find(350, 530);
  esp32cam::Resolution hiRes  = esp32cam::Resolution::find(800, 600);
  WebServer webServer;

  void init(Stream& uartC3);
  inline void handleClient() { webServer.handleClient(); }

  void handleUDP();
  void handleUART();
  void sendPeriodicTelemetry();

  void handleStream();
  void handleDroneData();
  void serveJpg();
  void handleJpgLo();
  void handleJpgHi();
  void handleJpgMid();

private:
  void sendTelemetry();
  void sendCommandToC3(int16_t t, int16_t y, int16_t p, int16_t r);

  Stream*   _uartC3 = nullptr;
  DroneData _data;

  WiFiUDP   _udp;
  IPAddress _remoteIP;
  uint16_t  _remotePort = 0;

  Timer _telemetryTimer{1000};

  int16_t _throttle = 0;
  int16_t _yaw      = 0;
  int16_t _pitch    = 0;
  int16_t _roll     = 0;
};

}  // namespace Drone
