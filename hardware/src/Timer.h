#pragma once

#include <Arduino.h>

class Timer {

public:
  Timer(int interval) : _interval(interval) { _last = millis(); };

  bool tick() {
    uint32_t now = millis();

    if (now - _last >= _interval) {
      _last = now;
      return true;
    }
    return false;
  };

private:
  uint32_t _interval;
  uint32_t _last;
};
