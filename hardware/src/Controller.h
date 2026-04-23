#pragma once

// #include <Arduino.h>
#include "pch.h"
namespace Drone {

struct Movement {
  int16_t throttle;
  int16_t pitch;
  int16_t roll;
};

// class Controller {
// public:
//   const int DEAD_ZONE = 10;

//   void init();

//   void onUpdate(bool updated);

//   void onMove(ControllerMovement move);

//   int getMovement() { return _movement; }

// private:
//   ControllerMovement _movement;
// };

}  // namespace Drone
