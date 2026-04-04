#include <Arduino.h>
#include "Controller.h"
#include "Server.h"
#include "secrets.h"
#include <WebServer.h>
#include <WiFi.h>

Drone::Controller controller;
Drone::Server server;

void setup() {
  Serial.begin(115200);
  server.setup();
  // controller.setup();
}

void loop() {
  server.handleClient();


  /*
  
  bool updated = controller.getUpdated();

  static unsigned long last = 0;

  if (millis() - last > 50) {
    last = millis();

    controller.onUpdate(updated);
  }
  */
}
