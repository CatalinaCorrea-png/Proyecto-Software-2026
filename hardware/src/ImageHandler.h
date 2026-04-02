#pragma once
#include <Arduino.h>
#include "Secrets.h"
#include <esp32cam.h>

extern WebServer server(80);

class ImageHandler {
public:
  esp32cam::Resolution loRes = esp32cam::Resolution::find(320, 240);
  esp32cam::Resolution midRes = esp32cam::Resolution::find(350, 530);
  esp32cam::Resolution hiRes = esp32cam::Resolution::find(800, 600);

  void setup();
  void serveJpg();
  void handleJpgLo();
  void handleJpgHi();
  void handleJpgMid();
};
