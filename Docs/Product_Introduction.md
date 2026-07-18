# MedFlow 智慧醫療物聯網 - 產品系列介紹

**MedFlow** 是一套專為醫療機構與照護中心設計的**智慧醫療物聯網產品系列 (Smart Healthcare IoT Product Family)**。旨在透過非侵入式的感測技術與物聯網架構，即時監控患者的輸液與排泄狀態，減輕醫護人員的巡房負擔並提高病人安全。

目前 MedFlow 旗下規劃兩大核心產品線：

---

## 1. 液面感測 (滴護寶 - Smart IV Drip Monitor)

液面感測系統包含藍牙端點與閘道器，其產品代號分別為：
* **POSEIDON**：代表低功耗藍牙液面偵測端點 (BT Node)。
* **Gateway** (或 Poseidon Gateway)：代表藍牙轉 Wi-Fi 閘道器。

專門用於點滴輸液的即時監控，當點滴用罄或異常時主動警示。

### 1.1 系統組成
* **a. 單點電容觸控貼片 (Single-point Capacitive Touch Sensor)**：夾於點滴滴斗或特定液位高度外側，非侵入式感測液面是否降至警戒線以下。
* **b. 藍牙 (BT) 廣播 (BLE Broadcasting)**：端點偵測器（主控 Actions ATB1113）採用超低功耗藍牙廣播，每 5 秒發送一次液位狀態，確保鈕扣電池（CR2032）能長期運作。
* **c. 藍牙轉 Wi-Fi 閘道器 (BT-to-Wi-Fi Gateway)**：閘道器（主控 ITE IT9866 + M8821CS1）掃描並解析區域內所有點滴端點的廣播封包。
* **d. 雲端伺服器 (Cloud Server)**：閘道器將資料透過 MQTT (SSL) 上傳至雲端伺服器，再經由 WebSocket 即時推送至護理站中控台與醫護行動端 App。

### 1.2 目前最新進度
* **設計接近完成 (Design Near Completion)**：硬體 PCBA 電路與 Layout 設計（V2.0）已定案，藍牙廣播封包格式與網域 MQTT 遙測協定已完成對接，正進行最後階段的韌體驗證。

---

## 2. 尿袋 IO (Smart Urine Bag Monitor)

尿袋 IO 系統專為長期臥床或手術後患者設計，即時監測尿袋的累積尿量與排出速率（Urine Output / Flow Rate），預防急性腎衰竭等併發症。

### 2.1 系統組成
* **a. 多點電容觸控貼片 (Multi-point Capacitive Touch Sensor)**：貼於尿袋外側，利用多個感測通道（Channels）動態測量尿液的高度，進而精確估算當前尿液容量。
* **b. 藍牙 (BT) 廣播 (BLE Broadcasting)**：端點模組以低功耗藍牙定期廣播多點液位電容量資料。
* **c. 藍牙轉 Wi-Fi 閘道器 (BT-to-Wi-Fi Gateway)**：共用護理站現有的閘道器，接收並解析尿袋端點的廣播封包。
* **d. 雲端伺服器 (Cloud Server)**：資料經 MQTT 上傳後，雲端演算法進行高度與容積的非線性換算，即時記錄尿量趨勢圖表，並在尿量過低或過高時發出警示。

### 2.2 目前最新進度
* **初期規劃 (Initial Planning)**：目前處於架構定義與感測貼片通道數規劃階段，正進行多點電容感測貼片的原理驗證（PoC）。
