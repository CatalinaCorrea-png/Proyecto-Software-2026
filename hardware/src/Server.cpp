#include "Server.h"

namespace Drone {
  
void Server::setup() {

    Serial.println();
    {
      using namespace esp32cam;
      Config cfg;
      cfg.setPins(pins::AiThinker);
      cfg.setResolution(loRes);
      cfg.setBufferCount(1);
      cfg.setJpeg(60);

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

    webServer.on("/cam-lo.jpg",  [this]() { this->handleJpgLo(); });
    webServer.on("/cam-hi.jpg",  [this]() { this->handleJpgHi(); });
    webServer.on("/cam-mid.jpg", [this]() { this->handleJpgMid(); });

    webServer.begin();

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

}
