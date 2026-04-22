#pragma once

#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include "Controller.h"
#include "FlyHandler.h"
#include "pch.h"

namespace Drone {

struct DroneData {
  float altitude;
  float lat;
  float lng;
  float speed;
};

class Drone {

public:
  Drone() : _gpsSerial(2), _data({0.0f, 0.0f, 0.0f, 0.0f}) {}

  void init() {
    _flyHandler.init();
    // _controller.init();
    // initGPS();

    updateData();
  }

  void initGPS() {
    _gpsSerial.begin(9600, SERIAL_8N1, 16, 17);
    PRINT("Init GPS");
  }

  void onUpdate(DeltaTime dt) {
    // float throttle = _controller.getThrottle();
    // _flyHandler.onUpdate(dt, throttle);

    // PRINT("Satellites: %d\n", _gps.satellites.value());
    updateData();
  }

  void updateData() {
    while (_gpsSerial.available()) {
      _gps.encode(_gpsSerial.read());
    }

    if (_gps.location.isValid()) {
      _data.lat = _gps.location.lat();
      _data.lng = _gps.location.lng();
    }

    if (_gps.altitude.isValid()) {
      _data.altitude = _gps.altitude.meters();
    }

    if (_gps.speed.isValid()) {
      _data.speed = _gps.speed.kmph();
    }
  }

  const DroneData &getDroneData() const { return _data; }
  const Movement &getMovement() const { return _movement; }
  void setMovement(Movement &mov) { _movement = mov; }

private:
  DroneData _data;
  FlyHandler _flyHandler;
  Movement _movement;
  TinyGPSPlus _gps;
  HardwareSerial _gpsSerial;
};

}  // namespace Drone
