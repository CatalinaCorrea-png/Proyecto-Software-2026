#pragma once

class DeltaTime {

public:
  DeltaTime(uint32_t time = 0.0f) : _time(time) {};

  float getSeconds() const { return _time / 1000; }
  uint32_t getMillis() const { return _time; }

  operator float() const { return getSeconds(); }

private:
  float _time;
};
