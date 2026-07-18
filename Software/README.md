# MedFlow 軟體系統說明 (Software System Notes)

本目錄主要儲存 **滴護寶 (Smart IV Drip Monitor)** 後端伺服器、網頁儀表板 (Web Dashboard) 與行動 App 的程式碼與架構手冊。

---

## 1. 軟體系統架構

```
+-----------------------------------------------------------------+
|                         MedFlow 軟體層                          |
|                                                                 |
|     +--------------------+           +--------------------+     |
|     |   護理站網頁前端   | <-------  |   醫護行動 App     |     |
|     |  (React/Next.js)   |           |  (Flutter/RN)      |     |
|     +--------------------+           +--------------------+     |
|                ^                               ^                |
|                | WebSocket                     | HTTP/APNs      |
|                v                               v                |
|     +-----------------------------------------------------+     |
|     |            應用後端服務 (Backend API Server)         |     |
|     |             (Go / NestJS / Node.js)                 |     |
|     +-----------------------------------------------------+     |
|            ^                     ^                 ^            |
|            | 訂閱遙測            | 快取狀態        | 儲存歷史   |
|            v                     v                 v            |
|     +-------------+       +-------------+   +-------------+     |
|     |  MQTT Broker|       | Redis 快取  |   | PostgreSQL  |     |
|     | (EMQX/Mosq) |       | (即時狀態)  |   | (病歷/設定) |     |
|     +-------------+       +-------------+   +-------------+     |
+-----------------------------------------------------------------+
```

---

## 2. 各模組技術規格

### A. 前端護理站中控台 (Web Dashboard)
* **技術棧**：React (Next.js) 或 Vue 3，配合 Tailwind CSS。
* **功能描述**：
  * **床位平面圖 (Ward Layout Map)**：以圖形化網格呈現各病房與床位點滴狀況，使用綠/黃/紅三色快速標示狀態。
  * **即時趨勢圖表 (Real-time Flow Chart)**：點擊個別病床可展開檢視該點滴剩餘百分比與滴速 (gtt/min) 趨勢。
  * **警報視窗與音效**：當點滴異常時，主動彈出紅色警報並播放警示音，提供一鍵「靜音」或「確認排除」功能。

### B. 後端服務 (API & Stream Server)
* **技術棧**：Node.js (NestJS / TypeScript) 或 Go (Gin / Fiber)。
* **通訊機制**：
  * **MQTT 接收端**：背景訂閱 `DCare/d/#` 主題，解析點滴狀態後存入 Redis，並透過 WebSocket 即時推送至前端。詳細連線與 JSON 格式請參閱 [閘道器連線與 MQTT 通訊規格](file:///c:/Users/JOHN_WIESS/.gemini/antigravity-ide/scratch/MedFlow/Docs/Gateway_Connection_Info.md)。
  * **WebSocket 伺服器**：建立與護理站前端瀏覽器的持久連線，即時廣播設備數據。
  * **RESTful API**：負責設備註冊、病床綁定、歷史警報查詢與醫護人員權限管理。

### C. 資料庫與快取 (Databases)
* **Redis**：用作高頻率設備狀態的記憶體快取。儲存設備在線/離線狀態 (Keep-alive)、最近一次遙測包。
* **PostgreSQL / MySQL**：儲存結構化數據，例如：
  * 設備表 (Devices)：ID、硬體版本、MAC 位址。
  * 病床表 (Beds)：病房號、床位號、目前綁定的設備與病人資訊。
  * 警報歷史 (Alarm Logs)：觸發時間、警報類型（空袋/阻塞/低電量）、確認時間與處理人員。

### D. 行動推播服務 (Notification Engine)
* 整合 Firebase Cloud Messaging (FCM) 與 Apple Push Notification service (APNs)。
* 當點滴發生紅色警報（如流速完全停止），且護理站網頁端在 30 秒內無人點選「確認」時，後端會自動觸發緊急推播給該病房分配的負責護理師手機/智慧手環。
