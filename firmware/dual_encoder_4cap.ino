#include <Wire.h>
#include <SoftI2C.h>
#include <CapacitiveSensor.h>

// Capacitive sensor: D7 send, D8 receive
CapacitiveSensor cs = CapacitiveSensor(7, 8);

// Second encoder on soft I2C pins D3 (SDA) and D4 (SCL)
SoftI2C softI2C(3, 4);

void setup() {
  Serial.begin(9600);
  Wire.begin();
  softI2C.begin();

  cs.set_CS_AutocaL_Millis(0xFFFFFFFF); // disable auto-calibrate
}

float readHardI2C() {
  Wire.beginTransmission(0x36);
  Wire.write(0x0E);
  Wire.endTransmission(false);
  Wire.requestFrom(0x36, 2);
  int high = Wire.read();
  int low  = Wire.read();
  int raw  = ((high & 0x0F) << 8) | low;
  return raw * 360.0 / 4096.0;
}

float readSoftI2C() {
  softI2C.beginTransmission(0x36);
  softI2C.write(0x0E);
  softI2C.endTransmission(false);
  softI2C.requestFrom(0x36, 2);
  int high = softI2C.read();
  int low  = softI2C.read();
  int raw  = ((high & 0x0F) << 8) | low;
  return raw * 360.0 / 4096.0;
}

void loop() {
  float yaw   = readHardI2C();
  float pitch = readSoftI2C();

  long capVal = cs.capacitiveSensor(30);

  // print two vals (same reading duplicated for format consistency)
  Serial.print(yaw);
  Serial.print(",");
  Serial.print(pitch);
  Serial.print(",v1:");
  Serial.print(capVal);
  Serial.print(",v2:");
  Serial.println(capVal);

  delay(100);
}
