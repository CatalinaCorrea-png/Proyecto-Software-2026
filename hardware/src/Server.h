#pragma once
#include <Arduino.h>
#include "Secrets.h"
#include <esp32cam.h>
#include <WiFi.h>
#include <WebServer.h>
#include "pch.h"
#include "Drone.h"
namespace Drone {

#define UDP_PORT 4210
#define UDP_TX_PORT 4211

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
  void handleStream();
  void handleDroneData();

  void serveJpg();
  void handleJpgLo();
  void handleJpgHi();
  void handleJpgMid();

private:
  void sendTelemetry();

  Drone *_drone;

  WiFiUDP udp;
  IPAddress remoteIP;
  uint16_t remotePort;

  int16_t throttle = 0;
  int16_t yaw = 0;
  int16_t pitch = 0;
  int16_t roll = 0;
};

}  // namespace Drone
