/*
 * DreamVision ESP32 Thermal Firmware
 * ─────────────────────────────────
 * MLX90640 32×24 thermal camera → WiFi TCP stream
 * Optional: ST7789 TFT display shows a live heatmap
 *
 * Wiring (I²C for MLX90640):
 *   SDA → GPIO 21
 *   SCL → GPIO 22
 *   VCC → 3.3 V
 *   GND → GND
 *
 * Wiring (SPI for ST7789 TFT, optional):
 *   CS  → GPIO 5
 *   DC  → GPIO 2
 *   RST → GPIO 4
 *   SCK → GPIO 18
 *   SDA → GPIO 23
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>

// ── MLX90640 ──────────────────────────────────────────────────────────────────
#include <Adafruit_MLX90640.h>

// ── TFT display (comment out if no screen attached) ─────────────────────────
#define USE_TFT_DISPLAY  // Remove this line to disable the TFT
#ifdef USE_TFT_DISPLAY
  #include <Adafruit_GFX.h>
  #include <Adafruit_ST7789.h>
  #define TFT_CS   5
  #define TFT_DC   2
  #define TFT_RST  4
  Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);
#endif

// ── WiFi credentials ─────────────────────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_SSID";       // <-- change me
const char* WIFI_PASSWORD = "YOUR_PASSWORD";   // <-- change me

// ── TCP server ────────────────────────────────────────────────────────────────
const uint16_t TCP_PORT = 5000;
WiFiServer   server(TCP_PORT);
WiFiClient   client;

// ── MLX90640 ─────────────────────────────────────────────────────────────────
Adafruit_MLX90640 mlx;
float frame[32 * 24];  // 768 floats

// ── Helpers ──────────────────────────────────────────────────────────────────
// Map a float temp to a 16-bit RGB565 colour (blue→green→red).
uint16_t tempToColor(float t, float tMin, float tMax) {
  float ratio = constrain((t - tMin) / (tMax - tMin), 0.0f, 1.0f);
  uint8_t r = (uint8_t)(ratio * 255);
  uint8_t b = (uint8_t)((1.0f - ratio) * 255);
  uint8_t g = (uint8_t)(ratio < 0.5f ? ratio * 2 * 255 : (1.0f - ratio) * 2 * 255);
  return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);  // RGB565
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n[DreamVision] Booting ESP32 Thermal Firmware...");

  // ── I²C for MLX90640
  Wire.begin(21, 22);
  Wire.setClock(400000);  // 400 kHz fast mode

  if (!mlx.begin(MLX90640_I2CADDR_DEFAULT, &Wire)) {
    Serial.println("[ERROR] MLX90640 not found – check wiring!");
    while (1) delay(1000);
  }
  Serial.println("[OK] MLX90640 initialised.");
  mlx.setMode(MLX90640_CHESS);
  mlx.setResolution(MLX90640_ADC_18BIT);
  mlx.setRefreshRate(MLX90640_4_HZ);

  // ── TFT display
#ifdef USE_TFT_DISPLAY
  tft.init(240, 320);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 10);
  tft.print("DreamVision");
  Serial.println("[OK] ST7789 TFT initialised.");
#endif

  // ── WiFi
  Serial.printf("[WiFi] Connecting to %s ...\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\n[WiFi] Connected – IP: %s\n", WiFi.localIP().toString().c_str());

  // ── TCP server
  server.begin();
  Serial.printf("[TCP]  Listening on port %u\n", TCP_PORT);
}

void loop() {
  // Accept new client if none is connected
  if (!client || !client.connected()) {
    client = server.accept();
    if (client) {
      Serial.printf("[TCP]  Client connected: %s\n",
                    client.remoteIP().toString().c_str());
    }
  }

  // Read one thermal frame
  if (mlx.getFrame(frame) != 0) {
    Serial.println("[WARN] Failed to get MLX90640 frame – retrying");
    return;
  }

  // ── Send frame over TCP as raw binary (768 × 4 bytes = 3072 bytes) ────────
  if (client && client.connected()) {
    // Header: magic + frame size so the Python reader can re-sync
    uint8_t header[8];
    header[0] = 0xAA; header[1] = 0xBB;   // magic bytes
    uint32_t len = 768 * sizeof(float);
    memcpy(header + 2, &len, 4);
    header[6] = 0x00; header[7] = 0x00;   // reserved
    client.write(header, sizeof(header));
    client.write((uint8_t*)frame, len);
    client.flush();
  }

  // ── Optional TFT heatmap ──────────────────────────────────────────────────
#ifdef USE_TFT_DISPLAY
  // Find min/max for colour scaling
  float tMin = frame[0], tMax = frame[0];
  for (int i = 1; i < 768; i++) {
    tMin = min(tMin, frame[i]);
    tMax = max(tMax, frame[i]);
  }
  // Draw 32×24 pixels scaled 7× → ~224×168 centred on 240×320 display
  const int SCALE = 7;
  const int XOFF  = (320 - 32 * SCALE) / 2;
  const int YOFF  = (240 - 24 * SCALE) / 2;
  for (int y = 0; y < 24; y++) {
    for (int x = 0; x < 32; x++) {
      float t  = frame[y * 32 + x];
      uint16_t c = tempToColor(t, tMin, tMax);
      tft.fillRect(XOFF + x * SCALE, YOFF + y * SCALE, SCALE, SCALE, c);
    }
  }
  // Print temperature range overlay
  tft.fillRect(0, 0, 320, 20, ST77XX_BLACK);
  tft.setCursor(4, 2);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE);
  tft.printf("Min: %.1f C   Max: %.1f C", tMin, tMax);
#endif
}
