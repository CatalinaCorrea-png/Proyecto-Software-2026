#include <Arduino.h>
#include "Drone.h"
#include "DeltaTime.h"
#include "Timer.h"

Drone::Drone drone;

uint32_t lastTime = 0;
Timer telemetryTimer(100);
Timer logTimer(500);

void setup() {
  Serial.begin(115200);
  PRINT("=== ESP32-C3 boot ===\n");
  Serial1.begin(115200, SERIAL_8N1, UART_CAM_RX_PIN, UART_CAM_TX_PIN);
  PRINT("Serial1 OK — RX:%d TX:%d\n", UART_CAM_RX_PIN, UART_CAM_TX_PIN);
  drone.init();
  PRINT("Drone init OK\n");
  lastTime = millis();
}

void loop() {
  // Leer comandos enviados por el ESP32-CAM
  if (Serial1.available()) {
    char buf[64];
    int len = Serial1.readBytesUntil('\n', buf, sizeof(buf) - 1);
    if (len > 0) {
      buf[len] = 0;
      int16_t t = 0, y = 0, p = 0, r = 0;
      if (sscanf(buf, "T:%d,Y:%d,P:%d,R:%d", &t, &y, &p, &r) == 4) {
        Drone::Movement mov = {t, p, r};
        drone.setMovement(mov);
        PRINT("CMD recibido — T:%d Y:%d P:%d R:%d\n", t, y, p, r);
      }
    }
  }

  uint32_t now = millis();
  DeltaTime dt(now - lastTime);
  lastTime = now;

  drone.onUpdate(dt);

  PRINT("Updated");

  if (logTimer.tick()) {
    const Drone::FlyHandler &fh = drone.getFlyHandler();
    const Drone::Movement &mov = drone.getMovement();
    PRINT("[LOG] roll:%.2f pitch:%.2f | throttle:%d pitch_in:%d roll_in:%d\n", fh.getRoll(), fh.getPitch(),
          mov.throttle, mov.pitch, mov.roll);
  }

  // Enviar telemetría al CAM para que la reenvíe por UDP/HTTP
  if (telemetryTimer.tick()) {
    const Drone::DroneData &data = drone.getDroneData();
    char buf[128];
    snprintf(buf, sizeof(buf), "LAT:%.6f,LNG:%.6f,ALT:%.2f,SPD:%.2f\n", data.lat, data.lng, data.altitude, data.speed);
    Serial1.print(buf);
  }
}
