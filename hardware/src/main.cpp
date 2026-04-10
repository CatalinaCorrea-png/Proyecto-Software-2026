#include <Arduino.h>

#include "Controller.h"
#include "Server.h"
#include "DeltaTime.h"
#include "FlyHandler.h"
#include "secrets.h"

Drone::Controller controller;
Drone::Server server;
Drone::FlyHandler flyHandler;

DeltaTime dt;

uint32_t lastTime = 0.0f;

void setup() {
  Serial.begin(115200);
  server.init();
  controller.init();
  flyHandler.init();
}

void loop() {
  uint32_t time = millis();
  dt = time - lastTime;
  lastTime = time;

  server.handleClient();

  bool updated = controller.getUpdated();

  static unsigned long last = 0;

  if (millis() - last > 50) {
    last = millis();

    int throttle = controller.getThrottle();
    flyHandler.onUpdate(dt, throttle);
    controller.onUpdate(updated);
  }
}
