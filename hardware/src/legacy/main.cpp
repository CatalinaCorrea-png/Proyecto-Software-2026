#include <Arduino.h>

#include "Controller.h"
#include "Server.h"
#include "DeltaTime.h"
#include "FlyHandler.h"
#include "Timer.h"
#include "Drone.h"

// Drone::Controller controller;
Drone::Drone drone;
Drone::Server server(&drone);

DeltaTime dt;

uint32_t lastTime = 0.0f;

void setup() {
  Serial.begin(115200);
  server.init();
  // controller.init();
  drone.init();
}

Timer pidTimer(50);  // cada 5ms = 200Hz (200x por seg)
Timer ctrlTimer(5);  // cada 50ms = 20Hz (20x por seg)

void loop() {
  server.handleClient();
  server.handleUDP();
  server.sendPeriodicTelemetry();

  drone.onUpdate(dt);

  /*
  --- Implementacion vieja falta implementacion de controller para ver si deprecar


  // bool updated = controller.getUpdated();

  {
    // Timed secuences

    if (ctrlTimer.tick())

      controller.onUpdate(updated);

      if (pidTimer.tick()) {
        uint32_t time = millis();
        dt = time - lastTime;
        lastTime = time;

        int throttle = controller.getThrottle();
        flyHandler.onUpdate(dt, throttle);
      }
  }
  */
}
