#include "Server.h"
#include <ArduinoJson.h>
#include "Controller.h"
namespace Drone {

void Server::init() {

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

  PRINT("http://");
  PRINT("IP: %s\n", WiFi.localIP().toString().c_str());
  PRINT("  /cam-lo.jpg");
  PRINT("  /cam-hi.jpg");
  PRINT("  /cam-mid.jpg");
  PRINT("  /stream");
  PRINT("  /status");

  webServer.on("/cam-lo.jpg", [this]() { this->handleJpgLo(); });
  webServer.on("/cam-hi.jpg", [this]() { this->handleJpgHi(); });
  webServer.on("/cam-mid.jpg", [this]() { this->handleJpgMid(); });
  webServer.on("/stream", [this]() { this->handleStream(); });
  webServer.on("/status", [this]() { this->handleDroneData(); });

  webServer.begin();

  _udp.begin(UDP_PORT);
  PRINT("\nUDP listening on %d\n", UDP_PORT);
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
    yield();
  }

  client.stop();
}

void Server::sendPeriodicTelemetry() {
  if (_remoteIP == IPAddress(0, 0, 0, 0))
    return;
  if (!_telemetryTimer.tick())
    return;
  sendTelemetry();
}

void Server::handleUDP() {
  int packetSize = _udp.parsePacket();
  if (packetSize) {
    char incoming[128];

    int len = _udp.read(incoming, sizeof(incoming) - 1);
    if (len > 0)
      incoming[len] = 0;

    // guardar origen (para responder)
    _remoteIP = _udp.remoteIP();
    _remotePort = _udp.remotePort();

    // formato: T:1200,Y:0,P:0,R:0
    sscanf(incoming, "T:%d,Y:%d,P:%d,R:%d", &_throttle, &_yaw, &_pitch, &_roll);

    Movement mov = {_throttle, _pitch, _roll};

    _drone->setMovement(mov);

    PRINT("RX UDP -> T:%d Y:%d P:%d R:%d\n", _throttle, _yaw, _pitch, _roll);

    // responder telemetría
    sendTelemetry();
  }
}

void Server::sendTelemetry() {
  if (_remoteIP == IPAddress(0, 0, 0, 0))
    return;

  char buffer[128];

  const DroneData &data = _drone->getDroneData();

  sprintf(buffer, "LAT:%.6f,LNG:%.6f,ALT:%.2f", data.lat, data.lng, data.altitude);

  _udp.beginPacket(_remoteIP, UDP_TX_PORT);
  _udp.write((uint8_t *)buffer, strlen(buffer));
  _udp.endPacket();
}

void Server::handleDroneData() {
  JsonDocument doc;
  const DroneData &data = _drone->getDroneData();

  doc["lat"] = data.lat;
  doc["lng"] = data.lng;
  doc["altitude"] = data.altitude;
  doc["speed"] = data.speed;
  // doc["battery"] = data.battery;

  String json;
  serializeJson(doc, json);

  webServer.send(200, "application/json", json);
}

void Server::serveJpg() {
  auto frame = esp32cam::capture();

  if (frame == nullptr) {
    PRINT("CAPTURE FAIL");
    webServer.send(503, "", "");
    return;
  }
  PRINT("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(), static_cast<int>(frame->size()));

  webServer.setContentLength(frame->size());
  webServer.send(200, "image/jpeg");
  WiFiClient client = webServer.client();
  frame->writeTo(client);
}

void Server::handleJpgLo() {
  if (!esp32cam::Camera.changeResolution(loRes)) {
    PRINT("SET-LO-RES FAIL");
  }
  serveJpg();
}

void Server::handleJpgHi() {
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    PRINT("SET-HI-RES FAIL");
  }
  serveJpg();
}

void Server::handleJpgMid() {
  if (!esp32cam::Camera.changeResolution(midRes)) {
    PRINT("SET-MID-RES FAIL");
  }
  serveJpg();
}

}  // namespace Drone
