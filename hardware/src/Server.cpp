#include "Server.h"

namespace Drone {

void Server::init() {

  Serial.println();
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(hiRes);
    cfg.setBufferCount(2);
    cfg.setJpeg(80);

    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.print("http://");
  Serial.println(WiFi.localIP());
  Serial.println("  /cam-lo.jpg");
  Serial.println("  /cam-hi.jpg");
  Serial.println("  /cam-mid.jpg");
  Serial.println("  /stream");

  webServer.on("/cam-lo.jpg", [this]() { this->handleJpgLo(); });
  webServer.on("/cam-hi.jpg", [this]() { this->handleJpgHi(); });
  webServer.on("/cam-mid.jpg", [this]() { this->handleJpgMid(); });
  webServer.on("/stream", [this]() { this->handleStream(); });

  webServer.begin();
}

void Server::handleStream() {
  WiFiClient client = webServer.client();

  client.print("HTTP/1.1 200 OK\r\n"
               "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");

  while (client.connected()) {
    auto frame = esp32cam::capture();

    if (!frame) {
      Serial.println("CAPTURE FAIL");
      continue;
    }

    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n");
    client.print("Content-Length: ");
    client.print(frame->size());
    client.print("\r\n\r\n");

    frame->writeTo(client);
    client.print("\r\n");

    delay(30);  // controla FPS
    yield();
  }

  client.stop();
}

void Server::serveJpg() {
  auto frame = esp32cam::capture();

  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    webServer.send(503, "", "");
    return;
  }
  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(), static_cast<int>(frame->size()));

  webServer.setContentLength(frame->size());
  webServer.send(200, "image/jpeg");
  WiFiClient client = webServer.client();
  frame->writeTo(client);
}

void Server::handleJpgLo() {
  if (!esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  }
  serveJpg();
}

void Server::handleJpgHi() {
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}

void Server::handleJpgMid() {
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}

}  // namespace Drone
