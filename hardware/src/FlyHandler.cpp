#include "FlyHandler.h"

namespace Drone {

void FlyHandler::init() {
  motorFL.init(13, 0);
  motorFR.init(14, 1);
  motorBL.init(15, 2);
  motorBR.init(2, 3);
  // initIMU();
}

void FlyHandler::initIMU() {
  // Wire.begin(21, 22);  // SDA, SCL

  // // MPU6500 (sale de sleep)
  // Wire.beginTransmission(_address);
  // Wire.write(0x6B);  // PWR_MGMT_1
  // Wire.write(0x00);  // wake up
  // Wire.endTransmission();

  // Serial.println("MPU6500 ready");
}

void FlyHandler::beginRead() {
  Wire.beginTransmission(_address);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(_address, (uint8_t)14, (uint8_t)true);
}

void FlyHandler::onUpdate(DeltaTime dt, int throttle) {
  IMUData imu = readIMU();

  float roll_acc = atan2(imu.acc.y, imu.acc.z) * 180 / PI;
  float pitch_acc = atan2(-imu.acc.x, sqrt(imu.acc.y * imu.acc.y + imu.acc.z * imu.acc.z)) * 180 / PI;

  _roll = _alpha * (_roll + imu.gyro.x * dt) + (1 - _alpha) * roll_acc;
  _pitch = _alpha * (_pitch + imu.gyro.y * dt) + (1 - _alpha) * pitch_acc;

  // PID calcula corrección
  float rollOut = pidRoll.compute(0, _roll, dt);  // setpoint = 0 (nivelado)
  float pitchOut = pidPitch.compute(0, _pitch, dt);

  // Mezcla de motores (quadcopter +)
  //        FL         FR          BL          BR
  int fl = throttle + rollOut - pitchOut;  // - roll, - pitch
  int fr = throttle - rollOut - pitchOut;  // + roll, - pitch
  int bl = throttle + rollOut + pitchOut;  // - roll, + pitch
  int br = throttle - rollOut + pitchOut;  // + roll, + pitch

  motorFL.setSpeed(constrain(fl, 0, 255));
  motorFR.setSpeed(constrain(fr, 0, 255));
  motorBL.setSpeed(constrain(bl, 0, 255));
  motorBR.setSpeed(constrain(br, 0, 255));

  motorFL.onUpdate();
  motorFR.onUpdate();
  motorBL.onUpdate();
  motorBR.onUpdate();
}

IMUData FlyHandler::readIMU() {
  beginRead();
  // 6 bytes de acceleracion
  int16_t ax = Wire.read() << 8 | Wire.read();
  int16_t ay = Wire.read() << 8 | Wire.read();
  int16_t az = Wire.read() << 8 | Wire.read();

  Wire.read();  // temp
  Wire.read();  // temp

  // 6 bytes de gyroscopio
  int16_t gx = Wire.read() << 8 | Wire.read();
  int16_t gy = Wire.read() << 8 | Wire.read();
  int16_t gz = Wire.read() << 8 | Wire.read();

  IMUData data;

  data.acc = Vec3(ax, ay, az) / 16384.0;
  data.gyro = Vec3(gx, gy, gz) / 131.0;

  return data;
}

}  // namespace Drone
