#pragma once
#include <Arduino.h>
#include "Secrets.h"
#include <esp32cam.h>
#include <WiFi.h>
#include <WebServer.h>
#include "pch.h"
#include "Drone.h"
#include "Timer.h"
namespace Drone {

class Server {

public:
  Server(Drone *drone) : _drone(drone) {}

  esp32cam::Resolution loRes = esp32cam::Resolution::find(320, 240);
  esp32cam::Resolution midRes = esp32cam::Resolution::find(350, 530);
  esp32cam::Resolution hiRes = esp32cam::Resolution::find(800, 600);
  WebServer webServer;

  inline void handleClient() { webServer.handleClient(); }
  void init();

  void handleUDP();
  void sendPeriodicTelemetry();
  void handleStream();
  void handleDroneData();

  void serveJpg();
  void handleJpgLo();
  void handleJpgHi();
  void handleJpgMid();

private:
  void sendTelemetry();

  Drone *_drone;

  WiFiUDP _udp;
  IPAddress _remoteIP;
  uint16_t _remotePort;

  Timer _telemetryTimer{200};  // push telemetría cada 200ms (5Hz)

  int16_t _throttle = 0;
  int16_t _yaw = 0;
  int16_t _pitch = 0;
  int16_t _roll = 0;
};

}  // namespace Drone
