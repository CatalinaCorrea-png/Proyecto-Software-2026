#include "controller.h"
#include "secrets.h"
#include <WebServer.h>
#include <WiFi.h>

Controller controller;
imageHandler imageHandler;

void setup() {
  Serial.begin(115200);
  imageHandler.setup();
  controller.setup();
}

void loop() {
  server.handleClient();

  bool updated = BP32.update();

  static unsigned long last = 0;

  if (millis() - last > 20) {
    last = millis();

    controller.onUpdate(updated);
  }
}
