#pragma once

class DeltaTime {

public:
  DeltaTime(uint32_t time = 0.0f) : _time(time) {};

  float getSeconds() { return _time / 1000; }
  uint32_t getMillis() { return _time; }

private:
  float _time;
};
