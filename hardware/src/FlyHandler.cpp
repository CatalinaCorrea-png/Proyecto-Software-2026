#include "FlyHandler.h"
namespace Drone {

void FlyHandler::init() {
  motorFL.init(MOTOR_PIN1, 0);
  motorFR.init(MOTOR_PIN2, 1);
  motorBL.init(MOTOR_PIN3, 2);
  motorBR.init(MOTOR_PIN4, 3);
  // initIMU();
}

void FlyHandler::initIMU() {
  Wire.begin(MPU_SDA_PIN, MPU_SCL_PIN);

  Wire.beginTransmission(_address);
  Wire.write(0x6B);  // PWR_MGMT_1
  Wire.write(0x00);  // wake up
  Wire.endTransmission();

  _imuReady = true;
}

bool FlyHandler::beginRead() {
  Wire.beginTransmission(_address);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  return Wire.requestFrom(_address, (uint8_t)14, (uint8_t)true) == 14;
}

void FlyHandler::onUpdate(DeltaTime dt, Movement &mov) {
  IMUData imu = readIMU();

  float roll_acc = atan2(imu.acc.y, imu.acc.z) * RAD_TO_DEG;
  float pitch_acc = atan2(-imu.acc.x, sqrt(imu.acc.y * imu.acc.y + imu.acc.z * imu.acc.z)) * RAD_TO_DEG;

  _roll = _alpha * (_roll + imu.gyro.x * dt) + (1 - _alpha) * roll_acc;
  _pitch = _alpha * (_pitch + imu.gyro.y * dt) + (1 - _alpha) * pitch_acc;

  // int16_t normalizedRoll = map(mov.roll, INPUT_MIN_VALUE, INPUT_MAX_VALUE, -15, 15);
  // int16_t normalizedPitch = map(mov.roll, INPUT_MIN_VALUE, INPUT_MAX_VALUE, -15, 15);

  // PID calcula correccion
  float rollOut = pidRoll.compute(mov.roll * 0.15f, _roll, dt);  // escalar a grados el roll y pitch
  float pitchOut = pidPitch.compute(mov.pitch * 0.15f, _pitch, dt);

  // Mezcla de motores (quadcopter +)
  //        FL         FR          BL          BR
  
  int fl = mov.throttle + rollOut - pitchOut;  // - roll, - pitch
  int fr = mov.throttle - rollOut - pitchOut;  // + roll, - pitch
  int bl = mov.throttle + rollOut + pitchOut;  // - roll, + pitch
  int br = mov.throttle - rollOut + pitchOut;  // + roll, + pitch

  PRINT("Potencia: motor FL: %d, motor FR: %d, motor BL: %d, motor BR: %d\n", fl, fr, bl, br);

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
  if (!_imuReady || !beginRead()) {
    return IMUData{};
  }
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
