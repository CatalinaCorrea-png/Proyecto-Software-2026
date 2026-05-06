#include "Server.h"
#include <ArduinoJson.h>

namespace Drone {

void Server::init(Stream& uartC3) {
  _uartC3 = &uartC3;

  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(midRes);
    cfg.setBufferCount(2);
    cfg.setJpeg(70);

    bool ok = Camera.begin(cfg);
    PRINT(ok ? "CAMERA OK\n" : "CAMERA FAIL\n");
  }

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  PRINT("IP: %s\n", WiFi.localIP().toString().c_str());

  webServer.on("/cam-lo.jpg",  [this]() { this->handleJpgLo(); });
  webServer.on("/cam-hi.jpg",  [this]() { this->handleJpgHi(); });
  webServer.on("/cam-mid.jpg", [this]() { this->handleJpgMid(); });
  webServer.on("/stream",      [this]() { this->handleStream(); });
  webServer.on("/status",      [this]() { this->handleDroneData(); });

  webServer.begin();

  _udp.begin(UDP_PORT);
  PRINT("UDP listening on %d\n", UDP_PORT);
}

void Server::handleStream() {
  WiFiClient client = webServer.client();

  client.print("HTTP/1.1 200 OK\r\n"
               "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");

  while (client.connected()) {
    auto frame = esp32cam::capture();

    if (!frame) {
      PRINT("CAPTURE FAIL");
      continue;
    }

    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n");
    client.print("Content-Length: ");
    client.print(frame->size());
    client.print("\r\n\r\n");
    frame->writeTo(client);
    client.print("\r\n");

    handleUDP();
    handleUART();
    yield();
  }

  client.stop();
}

void Server::handleUDP() {
  int packetSize = _udp.parsePacket();
  if (!packetSize)
    return;

  char incoming[128];
  int len = _udp.read(incoming, sizeof(incoming) - 1);
  if (len > 0)
    incoming[len] = 0;

  _remoteIP   = _udp.remoteIP();
  _remotePort = _udp.remotePort();

  sscanf(incoming, "T:%d,Y:%d,P:%d,R:%d", &_throttle, &_yaw, &_pitch, &_roll);

  sendCommandToC3(_throttle, _yaw, _pitch, _roll);
  sendTelemetry();
}

void Server::sendCommandToC3(int16_t t, int16_t y, int16_t p, int16_t r) {
  if (!_uartC3)
    return;
  char buf[64];
  snprintf(buf, sizeof(buf), "T:%d,Y:%d,P:%d,R:%d\n", t, y, p, r);
  _uartC3->print(buf);
}

void Server::handleUART() {
  if (!_uartC3)
    return;

  while (_uartC3->available()) {
    char buf[128];
    int len = _uartC3->readBytesUntil('\n', buf, sizeof(buf) - 1);
    if (len <= 0)
      break;
    buf[len] = 0;
    sscanf(buf, "LAT:%f,LNG:%f,ALT:%f,SPD:%f",
           &_data.lat, &_data.lng, &_data.altitude, &_data.speed);
  }
}

void Server::sendPeriodicTelemetry() {
  if (_remoteIP == IPAddress(0, 0, 0, 0))
    return;
  if (!_telemetryTimer.tick())
    return;
  sendTelemetry();
}

void Server::sendTelemetry() {
  if (_remoteIP == IPAddress(0, 0, 0, 0))
    return;

  char buffer[128];
  snprintf(buffer, sizeof(buffer), "LAT:%.6f,LNG:%.6f,ALT:%.2f",
           _data.lat, _data.lng, _data.altitude);

  _udp.beginPacket(_remoteIP, UDP_TX_PORT);
  _udp.write((uint8_t*)buffer, strlen(buffer));
  _udp.endPacket();
}

void Server::handleDroneData() {
  JsonDocument doc;
  doc["lat"]      = _data.lat;
  doc["lng"]      = _data.lng;
  doc["altitude"] = _data.altitude;
  doc["speed"]    = _data.speed;

  String json;
  serializeJson(doc, json);
  webServer.send(200, "application/json", json);
}

void Server::serveJpg() {
  auto frame = esp32cam::capture();

  if (!frame) {
    PRINT("CAPTURE FAIL");
    webServer.send(503, "", "");
    return;
  }

  webServer.setContentLength(frame->size());
  webServer.send(200, "image/jpeg");
  WiFiClient client = webServer.client();
  frame->writeTo(client);
}

void Server::handleJpgLo() {
  if (!esp32cam::Camera.changeResolution(loRes))
    PRINT("SET-LO-RES FAIL");
  serveJpg();
}

void Server::handleJpgHi() {
  if (!esp32cam::Camera.changeResolution(hiRes))
    PRINT("SET-HI-RES FAIL");
  serveJpg();
}

void Server::handleJpgMid() {
  if (!esp32cam::Camera.changeResolution(midRes))
    PRINT("SET-MID-RES FAIL");
  serveJpg();
}

}  // namespace Drone
