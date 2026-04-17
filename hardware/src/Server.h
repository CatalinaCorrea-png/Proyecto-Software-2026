#pragma once
#include <Arduino.h>
#include "Secrets.h"
#include <esp32cam.h>
#include <WiFi.h>
#include <WebServer.h>
#include "pch.h"

namespace Drone {

class Server {

public:
  esp32cam::Resolution loRes = esp32cam::Resolution::find(320, 240);
  esp32cam::Resolution midRes = esp32cam::Resolution::find(350, 530);
  esp32cam::Resolution hiRes = esp32cam::Resolution::find(800, 600);
  WebServer webServer;

  inline void handleClient() { webServer.handleClient(); }
  void init();
  void serveJpg();
  void handleStream();
  void handleJpgLo();
  void handleJpgHi();
  void handleJpgMid();
};

}  // namespace Drone
