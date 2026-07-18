# MedFlow 韌體開發說明 (Firmware Development Notes)

本目錄主要儲存 **滴護寶 (Smart IV Drip Monitor)** 端點裝置的 MCU 韌體原始碼與開發文件。

---

## 1. 開發環境與框架

* **開發晶片**：ESP32 系列 / 或是 ITE 晶片（如 IT986x 平台，取決於顯示屏與運算規格）。
* **韌體框架**：
  * 若採用 ESP32：使用 ESP-IDF (VS Code Extension) 或 Arduino IDE / PlatformIO。
  * 若採用 ITE：使用 ITE SDK 整合開發環境。
* **通訊協議技術棧**：TCP/IP -> MQTT over TLS / CoAP。

---

## 2. 韌體功能模組設計

```
+-------------------------------------------------------------------+
|                           MCU 韌體架構                            |
|                                                                   |
|   +-----------------------------------------------------------+   |
|   |                      應用邏輯與演算法                     |   |
|   |  * 流速計算法 (Drip Rate)       * 剩餘容積評估            |   |
|   |  * 狀態機管理 (State Machine)   * 警報邏輯控制 (Alarm)     |   |
|   +-----------------------------------------------------------+   |
|         |                        |                     |          |
|   +-----------+            +-----------+         +------------+   |
|   | 連線管理  |            |  電源管理 |         |   驅動層   |   |
|   | * Wi-Fi   |            | * Sleep   |         | * GPIO INT |   |
|   | * MQTT    |            | * Wakeup  |         | * ADC/I2C  |   |
|   | * OTA     |            | * FG Read |         | * PWM/LED  |   |
|   +-----------+            +-----------+         +------------+   |
+-------------------------------------------------------------------+
```

### A. 滴速運算與狀態演算法 (Drip Algorithm)
* **點滴計數 (Pulse Counting)**：
  * 利用 GPIO 外部中斷捕捉紅外線感測器所產生的脈衝訊號。
  * 每滴點滴滴落時觸發一次中斷，記錄時間戳。
* **滴速計算 (Drip Rate Calculation)**：
  * 基於時間滑動視窗 (Sliding Window) 計算每分鐘滴數 (Drops Per Minute, gtt/min)。
  * 偵測超速、極慢速或停止滴落，並根據閥值判定是否觸發警報狀態。
* **重量換算 (Weight-to-Volume)**：
  * 讀取 24-bit ADC 的數值，經過校準後換算為克重，評估剩餘的生理食鹽水/藥液體積。

### B. 電源優化管理 (Power Management)
* **休眠與喚醒機制**：
  * 當系統進入無液滴滴落的待機狀態時，MCU 關閉 Wi-Fi 並進入 Light Sleep / Deep Sleep。
  * 當紅外線對射管偵測到脈衝訊號，或定時器計時結束時，透過 GPIO 外設喚醒 MCU。
* **低電量警報**：
  * 定期讀取電池電量，當電量低於 15% 時，透過 MQTT 發送低電量警報，並降低 LED 亮度以延長生命週期。

### C. 通訊與配網協定 (Network & Provisioning)
* **配網模式 (Provisioning)**：
  * 首次開機或長按功能鍵後進入 BLE 配網模式，由手機 App 設定 Wi-Fi SSID 與密碼。
* **MQTT Telemetry**：
  * 定期 (如每 5 秒) 發送即時 JSON 遙測封包：
    ```json
    {
      "device_id": "MF-DHB-001",
      "drip_rate_gtt": 60,
      "remaining_volume_ml": 250,
      "battery_pct": 85,
      "status": "normal"
    }
    ```
* **OTA 安全韌體更新**：
  * 支援在線升級機制。韌體包會經過加密簽章，下載後進行雙分區 (Partition A/B) 滾動更新。

---

## 3. 開發起步指引

1. **環境配置**：根據專案選擇，安裝對應的晶片開發鏈 (如 ESP-IDF v5.x 或 ITE SDK)。
2. **硬體驗證**：優先編譯讀取 GPIO 的測試專案，確認紅外線接收中斷觸發正常。
3. **通訊驗證**：運行基本的 MQTT Client，確保設備能順利與本機的 MQTT Broker 連線與訂閱/發佈主題。
