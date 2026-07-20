# MedFlow 研發日誌 (Development Log)

## 專案名稱：MedFlow MQTT Dashboard & Gateway 監控工具
**專案目錄**：`C:\SW code\source code\MefFlo_MQTT_Dashbaord`

---

## [2026-07-20] 修復 MQTT Server 連線視窗凍結與效能優化

### 1. 問題現象 (Bug Description)
當使用者在 `mqtt_dashboard.html` 點擊「連接伺服器」嘗試連線至 MQTT Broker (`mqtt.go6.tw`) 時，介面呈現無響應、視窗凍結 (GUI Freeze) 的現象。即使點擊中斷或取消連線，視窗仍持續卡死。

### 2. 根因探討 (Root Cause Analysis)
1. **連線狀態機異常 (State Machine Bug)**：
   * 當按鈕處於「連線中...」(`connecting`) 狀態時，`client.connected` 為 `false`。
   * 若使用者此時點擊「取消連接」（調用 `toggleConnection()`），原程式判斷 `client.connected` 為假，竟會再次調用 `connectMQTT()`，導致同時開啟多個 WebSocket 連線，每秒大量拋出 error/close 事件並頻繁重試，卡死 JavaScript Event Loop。
2. **無節制的 DOM 重繪 (Layout Thrashing)**：
   * 每次收到 MQTT 遙測封包，`processDashboardMessage()` 會立即調用 `renderDevicesGrid()` 覆寫 `innerHTML`。高頻數據流下（每秒數十筆封包）觸發極高頻率的 DOM 重繪，引發瀏覽器畫面凍結。
3. **預設連線協定與 Port 號衝突**：
   * 原 UI 下拉選單預設為 `wss://` 搭配 Port `8083`。
   * 經 Socket 埠號探測實測，`mqtt.go6.tw` 的 **8083 Port 為非加密 `ws://` WebSockets**（`8883` 則為明文 TCP）。用 `wss://` 連接 8083 會因 SSL Handshake 失敗引發快速重試風暴與 console 報錯。

### 3. 解決方案 (Fix Implementation)
1. **重構連線狀態機與安全清理 (`cleanupClient`)**：
   * 在 `connectMQTT()` 與 `disconnectMQTT()` 執行時，先呼叫 `cleanupClient()`：徹底移除既有 listener (`client.removeAllListeners()`)，並執行 `client.end(true)` 強制關閉舊 Socket。
   * 明確區分 `disconnected` | `connecting` | `connected` 三種狀態。在 `connecting` 狀態下點擊按鈕時，確切執行 `disconnectMQTT()` 清除連線，不再重複調用 `connectMQTT()`。
   * 連線與連接期間自動禁用/啟用輸入欄位，避免競態條件。
2. **節流防抖與 DOM 數量上限**：
   * 為 `renderDevicesGrid()` 增加 100ms 節流 (Throttle)，保證每秒最多更新 10 次 DOM，保持介面維繫 60 FPS 流暢度。
   * 限制即時日誌區域的最大 DOM 節點數量為 100 筆，避免長時間運行導致記憶體洩漏與選單凍結。
3. **更正預設連線參數**：
   * 預設連線調整為 `ws://mqtt.go6.tw:8083/mqtt`，已實測驗證可瞬間完成 WebSocket 握手與 Topic (`DCare/d/#`) 訂閱。

### 4. 驗證結果 (Verification)
* **連線測試**：點擊「連接伺服器」，介面瞬間流暢切換，視窗完全無凍結或卡頓；點擊「取消連接」能瞬間中斷並還原。
* **通訊測試**：成功連接至 `ws://mqtt.go6.tw:8083/mqtt` 並發送/接收 `DCare/d/test_gw` 訊息，即時儀表板與日誌皆順暢更新。
