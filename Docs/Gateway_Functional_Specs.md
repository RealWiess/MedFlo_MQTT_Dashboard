# MedFlow 閘道器功能設計概念書 (Gateway Functional Design Concept)

本文件詳細記錄 **滴護寶 (Smart IV Drip Monitor) 閘道器 (Gateway)** 的功能設計概念、與 Windows 應用程式的互動機制、OTA 升級架構以及時間同步設計。

---

## 1. Windows USB 連線與資料通訊 (USB Connectivity)

* **設計概念**：閘道器（ITE IT9866/IT9868）需支援透過 USB 接口與 Windows 電腦建立實體連線。
* **運作機制與現有實作**：
  * 當閘道器以 USB 連接至 Windows 電腦時，能將閘道器內部的運作狀態、硬體參數以及收到的遙測資訊即時上報給 Windows 應用程式。
  * **程式碼實作**：目前在 Gateway 原始碼中的 [peripheral.c](file:///C:/公司/Design/睿建滴護寶/GW/source code/ITE9868_Build_20260703/project/kg70/wsp/peripheral.c#L284-L316) 內已實作了 [UsbdAcmProcessTask()](file:///C:/公司/Design/睿建滴護寶/GW/source code/ITE9868_Build_20260703/project/kg70/wsp/peripheral.c#L284)，利用 ITE SDK 的 `ITP_DEVICE_USBDACM` 虛擬串口 (USB CDC ACM) 與 Windows PC 連線，進行雙向資料讀寫（目前為 Loopback 測試）。

---

## 2. Windows 輔助管理工具 (Windows App Functionality)

設計一個專用的 **Windows 電腦端應用程式**，供醫護管理人員或工程師進行現場設定、診斷與監控：

### 2.1 滴護寶 BLE 廣播 Log 監控
* **特定過濾**：閘道器**僅接收並處理「滴護寶」系列（含液位 POSEIDON 與尿袋模組）的藍牙廣播**，自動過濾掉其他雜亂的藍牙裝置。
* **Log 紀錄顯示**：App 可即時顯示 Gateway 收到的所有滴護寶廣播 Log，包括：
  * 接收日期與時間 (Timestamp)。
  * 設備 MAC 位址（床位識別）。
  * 感測狀態數據與 RSSI 值。

### 2.2 記憶體快取與 Buffer 狀態監控
* App 介面可呈現閘道器當前儲存 BLE 廣播 Log 的緩衝區 (Buffer) 狀態與使用率。
* 提供「Buffer 是否足夠」的警示，避免因網路斷線導致本地資料溢出 (Overflow) 或丟失。

### 2.3 Wi-Fi 網路與雲端狀態配置
* **Wi-Fi 設定**：可經由 App 設定閘道器要連接的無線基地台 AP（SSID 與密碼）。
* **雲端上傳狀態**：App 需即時反饋「當前收集到的 BT 廣播 Log 是否已成功透過 Wi-Fi/MQTT 上傳至雲端伺服器」。
* **參數修改**：使用者可透過此 App 完整掌握當前 Gateway 的運作狀況，並直接修改與儲存系統設定值。

---

## 3. OTA 韌體在線升級 (Over-the-Air Update)

為了便於後續的功能擴充與系統維護，閘道器需具備安全穩定的韌體更新機制：
* **版本發布偵測**：當雲端或管理軟體發布新的韌體版本時，閘道器能自動或經由使用者觸發進行下載。
* **雙分區更新**：採用 ITE SDK 提供的雙分區 (A/B Partition) 升級保護機制，若升級失敗或損毀可自動復原，防止設備變磚。

---

## 4. Wi-Fi 連線時間同步 (Time Synchronization)

* **同步機制**：每當閘道器成功建立 Wi-Fi 連線時，需立即觸發網路時間同步（例如透過 NTP 伺服器同步或 MQTT 伺服器時間回傳）。
* **時間寫入**：同步取得正確的日期與時間後，即時寫入閘道器外掛的 **XS3500 RTC** 晶片，確保本地生成的 Log 時間戳記完全精確。
