#pragma once

struct Vec3 {
  Vec3() = default;
  Vec3(float x, float y, float z) {
    this->x = x;
    this->y = y;
    this->z = z;
  };

  Vec3 operator/(float s) const { return Vec3(x / s, y / s, z / s); }

  float x;
  float y;
  float z;
};
