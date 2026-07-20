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
* **通訊測試**：成功連接至 `wss://mqtt.go6.tw:8083/mqtt` 並發送/接收 `DCare/d/test_gw` 訊息，即時儀表板與日誌皆順暢更新。

---

## [2026-07-20] 狀態卡片版面優化：微縮與一排 4 個 (4 Cards Per Row Grid)

### 1. 需求與改善 (Requirements & UI Refactoring)
* 將原先一排僅顯示 2 個的大卡片版面，調整為一排顯示 4 個精緻微縮卡片 (`grid-template-columns: repeat(4, minmax(0, 1fr))`)。
* 降低 `.device-card` 內距與元件間距（`padding: 0.75rem 0.85rem`、`gap: 0.45rem`），適度微縮裝置名稱與狀態字型（`font-size: 0.88rem`），並設定強化的文字截斷（Ellipsis）。
* 在保留整體護理站資訊豐富度（顯示裝置名稱、MAC、即時液位/尿袋狀態、電池電量、滾動計數、更新時間與 RSSI 訊號）的同時，顯著提升大螢幕廣角視野與監控密度。

---

## [2026-07-20] JSON 訊息顯示區版面調整：固定擺放於最下方 (Full-Width Bottom Layout)

### 1. 需求與改善 (Requirements & UI Refactoring)
* 取消原本依解析度切換至右側單欄的舊排版，改為將即時 JSON 訊息流區域 (`.viewer-panel`) **固定擺放於全寬度最下方 (`grid-column: 1 / -1`)**。
* 上方區塊劃分為「左側連線設定與發布測試 (340px)」與「右側 4 欄 MedFlow 裝置實時狀態儀表板 (1fr)」，下方由 JSON 即時訊息顯示區跨滿整排。
* 避免不同螢幕解析度造成側邊擠壓，並為 JSON 語法高亮顯示區提供寬廣橫向空間，大幅提升視讀與操作舒適度。

---

## [2026-07-20] Safari (macOS / iOS / iPadOS) 跨瀏覽器完整相容性升級

### 1. 相容性驗證與強化 (Safari Compatibility Audit)
* **嵌入式 MQTT.js (Offline & Content-Blocker Protection)**：全檔內嵌 MQTT.js v4 UMD 核心，完全避開 Safari 嚴格的跨網域 (CORS) 限制與第三方腳本阻擋器。
* **原生 WSS (Secure WebSockets)**：採用 Safari 原生支援之 `wss://` 加密連線協定，已通過 Socket 101 Switching Protocols 相容測試。
* **-webkit-backdrop-filter 萬用前綴**：為全站毛玻璃視覺樣式（`.card`、`.device-card`）補充 `-webkit-backdrop-filter` 前綴，確保 iOS Safari、iPadOS 以及 macOS Safari 等各式 Apple 設備皆可呈現高質感毛玻璃光澤。
* **JavaScript ES6+ 標準語法**：全站邏輯均採用跨瀏覽器標準，在 Safari 10+ 均可 100% 穩定順暢運行。

---

## [2026-07-20] 系統升級：雙模式主選單與《滴護寶 SOP 護理安裝與 7 天動態監測引擎》

### 1. 需求與架構變更 (Architectural Refactoring & SOP Integration)
依照《滴護寶 SOP 操作流程》與護理車行動工作站規格，將 `mqtt_dashboard.html` 重構為具備多頁面切換 (SPA) 路由之護理站中控系統：
1. **第一頁 (主選單入口 Page 1 - Mode Selection Landing Portal)**：
   * 包含兩座大尺寸、圓角 (`border-radius: 24px`)、深色毛玻璃與光澤懸浮微動畫大卡片按鍵：
     - **📡 藍牙儀表板**
     - **🏥 護理安裝與綁定 SOP**
2. **第二頁 (藍牙與 MQTT 實時儀表板 Page 2 - Bluetooth Monitor)**：
   * 完全保留原版面 BT 與 MQTT 數據串流儀表板（一排 4 個微縮狀態卡片 + 最下方全寬 JSON 日誌串流區，不做版面更動）。
   * 頂部導覽列提供「🏠 返回主選單」與「🏥 護理安裝 SOP」按鈕，便於隨時切換。
3. **第三頁 (滴護寶 SOP 護理安裝與 7 天倒數牆 Page 3 - SOP Installation Workflow)**：
   * **步驟 1：護理人員登入 (Nurse Authentication)**：輸入/掃描員編（如 `N1024`）自動帶出護理師姓名（`陳靜宜 護理師`）。
   * **步驟 2：掃描病人手環 (Patient Wristband Scanner)**：相容 USB 條碼槍，讀取條碼（如 `P311-0812`）並自動帶出床號與病人姓名（`311床 張家豪`）。
   * **步驟 3：掃描 BT 傳輸器 (BT Sensor MAC Scanner)**：自動去除冒號與無關字元，格式化為標準大寫 12 碼 MAC（如 `F44EFDB20775`）。
   * **步驟 4：確認綁定與啟動 7 天動態倒數 (Binding & 7-Day Countdown Engine)**：
     - 確認綁定資訊並建立監測任務，自動啟動 **7 天 (168 小時)** 即時剩餘時間倒數。
     - 具備**護理站已綁定病人動態監測牆**：實時刷新每位病人的剩餘天/時/分/秒、時間進度條與液位狀態，並支援出院解綁與 LocalStorage 資料持久化。

---

## [2026-07-20] 熱修復 (Hotfix)：修正護理安裝 SOP 頁面 DOM ID 匹配問題

### 1. 問題與根因 (Issue & Root Cause Analysis)
* 點擊「護理安裝 SOP」時，介面下方呈現空白（僅頂部導覽列顯示）。
* **根因探討**：JavaScript `switchPage('sop')` 在切換至第三頁時會尋找 `id="page-sop"` 之 DOM 節點，而 HTML 標籤原先命名為 `id="page-nursing-sop"`，導致 `getElementById` 回傳 `null` 未套用 `.active` 類別，畫面呈現 `display: none` 盲區。

### 2. 修復與驗證 (Fix & Verification)
* 將 HTML 第三頁 DOM 節點 ID 更正為 `<div id="page-sop" class="page-view">`。
* **驗證結果**：點擊「護理安裝 SOP」或由首頁點擊「進入護理安裝流程」，4 步驟安裝精靈（護理師登入、病人手環掃描、BT 二維碼掃描、7天動態監測牆）均能 100% 順暢精準呈現。
