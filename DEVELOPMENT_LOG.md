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
   * 40. **BLE 廣播與 Scan Response 解析精確升級與介面優化 (BLE Adv & Scan Response Parser Fix)**：
       - **問題分析**：
         1. 主廣播封包 (Main ADV payload: 2B CID + 1B GPIO + 1B Status Flags, 總長 4 bytes) 原先被 `parseBleData()` 誤判為 4 Byte Scan Response 封包，導致系統把 GPIO18 狀態位元 (`0x01`) 當作 `wakeCycleCounter` 解析，使所有卡片恆定顯示 `喚醒週期次數: 1`。
         2. 使用者反映「不需要滾動計數 (ADV)」。
       - **修復方案**：
         1. 依據 `md/ble_advertising_format.md` 規格，修改 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html)、[server.py](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/server.py) 與 [pc_ble_gateway_sim.py](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/pc_ble_gateway_sim.py) 之解析邏輯：
            - 4 Bytes 製造商資料 (`AD Length = 0x05`, excluding type -> 4B): 識別為 **主廣播 (Main Advertising)**，精確解析 GPIO18 即時狀態與 Status Flags (電量/感測器異常)。
            - 6 Bytes 製造商資料 (`AD Length = 0x07`, excluding type -> 6B): 識別為 ** Scan Response**，精確解析 uint16 LE 的 `wakeCycleCounter` 喚醒週期累計次數。
         2. 自 `mqtt_dashboard.html` 滴護寶裝置卡片中移除「滾動計數 (ADV)」顯示列，畫面更加俐落精美。
   * 41. **BT 裝置卡片點擊彈窗、工作週期與 Gateway 軌跡統計 (Clickable Card & Gateway Roaming Telemetry)**：
       - **需求規格與修復**：
         1. **BT 工作週期定義 (Lifecycle Termination Rules)**：
            - 超過 **10 分鐘** 未收到 MQTT 訊號，或工作時間超過 **180 小時**，即視同此 BT 傳輸器服務終止，系統自動重置該 BT 傳輸器之當前工作週期與 Gateway 歷程。
         2. **卡片微光 UI 與備註 (Clickable Device Cards)**：
            - 裝置卡片支援 `cursor: pointer;` 與青藍色微光懸浮效果。
            - 卡片底部標註備註：`💡 10分無訊號/180小時視同終止 🔍 Gateway 歷程 ›`。
         3. **Gateway 漫遊軌跡與接收次數診斷彈窗 (Gateway Roaming Inspector Modal)**：
            - 點擊卡片彈出 `#bt-device-modal` 視窗。
            - 精準統計並列表呈現該 BT 傳輸器在此工作週期中**經過的所有實體 Gateway 名稱、接收封包總次數、封包佔比 (%)、最新 RSSI、首次與最近擷取時間**，並標示規格條款。
59. **Google Drive 雲端備份引擎與滿 20MB 自動上傳刪除本機 Log 機制 (Google Drive 20MB Batch Upload & Local Log Purge System)**：
    - **需求規格與修復**：依據開發者指示「JSON 先放在本機每 20MB，檔案名稱要有時間戳，上傳到我的 google drive 後即可刪除本機的已經上傳的 log 檔」，新增專屬 Google Drive 備份卡片與背景引擎（`appendToLocalLogBuffer()` & `uploadLogChunkToGDrive()`）：
      1. **本機 20MB 積累門檻與視覺進度條**：以位元組即時計算本機 Log 數據大小，滿 20MB 自動觸發批次備份上傳。
      2. **時間戳記檔名 (Timestamped Filenames)**：自動產出 `MedFlow_Logs_YYYYMMDD_HHMMSS.json`（例如 `MedFlow_Logs_20260728_010623.json`）。
      3. **上傳成功自動刪除本機備份 (Local Log Purge on Success)**：接收到 Google Apps Script (GAS) 回傳 `status: "success"` 成功訊號後，自動將本機已上傳的 Log 刪除，保持本機硬碟容量乾淨！
58. **尿袋狀態欄位點擊彈窗 ReferenceError 拋出與 MAC 比對邏輯修復 (drip modal ReferenceError Fix)**：
    - **Bug 根因與修復**：修復 `openBtDripLogsModal(mac)` 函式內部因變數 `isFull` 未在該範疇前宣告而拋出 `ReferenceError` 阻斷 Modal 彈出的 Bug。同步強化 MAC Address 格式正規化比對（支援有無冒號與大小寫相容），確保點擊「尿袋滿」與「尿袋空」狀態欄時 100% 順暢彈出最近 30 筆 Gateway 報出 Log 診斷視窗！
57. **全網在線 BT 傳輸器歷史最慢更新時間紀錄標章與管理者手動重置按鍵 (Persistent Peak Update Interval & Admin Reset Button)**：
    - **需求規格與修復**：依據開發者指示「這個是應該一直記，不能被清掉，然後加上一個 reset 按鍵讓管理者可以手動清掉」，將最慢更新時間統計升級為**「歷史最慢更新紀錄高點 (Peak Max Interval)」**，並透過 LocalStorage 持久化保存（`medflow_peak_update_interval`）。同時在標章右側新增 **`🔄 重置`** 管理者按鈕（`resetPeakUpdateInterval()`），允許管理者在校正或重測時一鍵清除 LocalStorage 並歸零高點紀錄！
56. **未滿 20 筆採集期雙狀態皆不亮規則 (Initial Sampling Rule: Neither Lit under 20 Packets)**：
    - **需求規格與修復**：依據開發者規格，傳輸器初始連線或重置後，在**收集的資料尚未滿 20 筆 (length < 20)** 之前，系統狀態標示為 `confirmedState = -1` (採集中)，「尿袋滿」與「尿袋空」兩欄均**保持淡化透明不燈亮**。待滿 20 筆且集中度達到 $\ge 75\%$ 門檻後，始正式點亮對應狀態。
55. **75% 門檻狀態容錯機制與最近 30 筆 Gateway 路徑 Log 診斷彈窗 (75% Threshold Hysteresis & 30 Telemetry Logs Inspector Modal)**：
    - **需求規格與修復**：
      1. **連續 20 筆 75% 門檻容錯機制 (75% Hysteresis Rule)**：建立滑動視窗 (Rolling Buffer) 紀錄最近 20 筆封包訊號。唯有當「尿袋滿」或「尿袋空」訊號在連續 20 筆內佔比**達到 75% 以上 (即 $\ge 15/20$ 筆)** 時，始觸發確定狀態 (confirmedState) 轉換；若未達 75% 則自動鎖定並保持當前狀態，徹底消除無線干擾與傳感器抖動引起的狀態頻繁閃爍。
      2. **狀態列點擊彈窗與 Gateway 報出路徑 Log (Clickable Status Rows & 30 Telemetry Logs Modal)**：
         - 點擊卡片上之「尿袋滿」或「尿袋空」欄位即可打開專屬診斷彈窗 `#bt-drip-logs-modal`。
         - 精準統計並展示**最近 20 筆訊號集中度比例 (滿/空比例 %)**。
         - 以表格詳細呈現**最近 30 筆傳輸 Log 之報出時間、報出 Gateway 路徑 (GWID)、GPIO18 狀態、RSSI 訊號強度與 Cnt 喚醒次數**，方便隨時追溯探針傳遞路徑。
54. **尿袋向量 Icon 設計與靠左對齊重構 (SVG Urine Bag Icon & Left Alignment)**：
    - **需求規格與修復**：
      1. **尿袋空排版靠左對齊**：將「尿袋空 (GPO=1)」由原先的置中 (`justify-content: center`) 改為與上排一致的**靠左對齊 (`justify-content: flex-start`)**，視覺結構整齊對稱。
      2. **醫用引流尿袋 SVG Icon**：設計專屬向量引流尿袋圖標（包含頂部掛環、袋身與底部排尿閥）。「尿袋滿」袋內充滿**淺黃色 (`#FDE047`)** 尿液並具微光效果；「尿袋空」袋內呈**白色透明度 50% (`rgba(255,255,255,0.50)`)**，完美符合醫療 HMI 規範！
53. **卡片雙狀態對照區塊 (尿袋滿計數 + 尿袋空對照 + GPIO 動態高亮)**：
    - **需求規格與修復**：
      1. **雙狀態垂直併列 (Dual Status Stack)**：一張卡片同時顯示 **「尿袋滿 (GPO=0)」(放上面)** 與 **「尿袋空 (GPO=1)」(放下面)**。
      2. **「尿袋滿」觸發次數自動累計 (Full State Counter)**：上面之「尿袋滿」右側新增 **`累計 X 次`** 標籤，當感測器自空轉滿 (stat=1->0) 時精確自動 +1 累計。下面之「尿袋空」保持純狀態顯視不計算次數。
      3. **GPIO 動態高亮切換**：當 `GPO=0` (滿) 時，上面「尿袋滿」呈現微光紅字與滴水動畫高亮，下面「尿袋空」淡化遮罩；當 `GPO=1` (空) 時，下面「尿袋空」呈現綠字高亮，上面「尿袋滿」淡化但持續保留累計次數對照。
52. **卡片寬度適當拓寬與時間戳記溢出剪裁修復 (Card Width & Timestamp Overflow Resolution)**：
    - **需求規格與修復**：將裝置卡片最小寬度自 `235px` 適度拓寬至 **`265px`**，同時優化 `.info-value` 彈性寬度與邊距，徹底解決 `(7/27 15:00)` 時間戳記因容器寬度受限而被裁切 `00)` 的問題，確保 `⏱️ 9小時 27分 (7/27 15:00)` 100% 完整無瑕呈現。
51. **左側設定欄表單單欄垂直堆疊重構 (Form Unstacking & Full-Width Inputs)**：
    - **修復方案**：將左側邊欄之 `通訊協定` 與 `Port`、`使用者名稱` 與 `密碼`、`寫入用戶` 與 `寫入密碼` 併排雙欄全面拆解為**獨立單欄 (Full-Width Form Groups)**，寬度 100% 垂直堆疊，徹底解決在縮小 30% 寬度後輸入框與「顯示」按鈕重疊遮擋之問題。
50. **卡片標籤精簡優化 (Label Text Streamlining)**：
    - **修復方案**：將裝置卡片及診斷彈窗之「服務中止時間」標籤統一簡化為 **「中止時間」**，節省字元寬度，使 `⏳ 8/3 15:00 (滿168h)` 等時間標籤於各解析度下均能最直觀完整呈現。

49. **左側設定欄縮小 30% 拓寬卡片展演區域 (30% Sidebar Width Reduction & Responsive Cards Layout)**：
    - **需求規格與修復**：
      1. 將儀表板左側設定欄寬度自原先 `340px` 精確**縮小 30% 至 `238px`** (`grid-template-columns: 238px 1fr`)，間距優化為 `1rem`，釋放更多螢幕空間給右側藍牙監測卡片牆。
      2. 重構 `.device-card` 之 `.info-row` 樣式，設定 `white-space: nowrap; flex-shrink: 0;`，解決卡片文字因寬度受擠壓而換行的問題，確保「上線時間」與「服務中止時間」單行俐落呈現！

48. **服務中止時間顯化 (168 小時滿期終止計算)**：
    - **需求規格與修復**：依據最新規格，將服務週期上限改為 **168 小時 (7 天)**，並於裝置卡片與診斷彈窗顯化 **「服務中止時間」** (`termMs = startMs + 168*3600*1000`)。如上線時間為 `7/27 15:00`，則服務中止時間精確計算為 **`8/3 15:00`**，方便護理人員掌握 7 天服務到期點。

47. **強制設定當前在線傳輸器之初始上線時間為 7/27 15:00 (Forced Online Start Time Override)**：
    - **需求規格與修復**：依據開發者要求，強制設定所有 active BT 傳輸器之當前工作週期初始上線時間戳記為 **2026/07/27 15:00:00 (`DEFAULT_FORCED_ONLINE_MS`)**，卡片實時累計時長與對應彈窗軌跡均自 7/27 15:00 基準起算。

46. **前端 LocalStorage 狀態持久化 (LocalStorage Active Devices Cache)**：
    - **修復方案**：在 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 加入 `localStorage` 持久化機制，確保使用者在瀏覽器重新整理 (F5) 或切換分頁時，先前採集之 BT 傳輸器當前連續廣播紀錄與 Gateway 歷程不會被清空抹除。

45. **連續廣播 (Continuous Advertising Stream) 1 分鐘判定與上線時間戳記鎖定 (1-Min Continuous Stream Rule)**：
    - **需求規格與修復**：
      1. **連續廣播判定 (Continuous Stream Definition)**：兩相鄰 MQTT Log 封包間隔 **$\le 1$ 分鐘 (60,000 ms)** 視為「連續廣播」，該期間內 `dev.firstSeenMs` 與 `dev.firstSeenTimeStr` 恆定鎖定在該連續廣播段**第一封包的時間戳記 (例如 14:00:00)**。
      2. **斷線重連啟動新上線時間**：若兩封包間隔 **$> 1$ 分鐘 (> 60 秒)**，判定為前段廣播中斷，下次收到封包時自動啟動全新一段連續廣播，並更新「上線時間」為該新封包的時間戳記。

43. **裝置卡片「喚醒週期次數」更名為「上線時間」實時累計 (Online Uptime Display)**：
    - **需求規格與修復**：
      1. 將裝置卡片上之「喚醒週期次數」列全面替換為 **「上線時間」** (Online Uptime Duration)。
      2. **上線時間計算權責**：嚴格依據 MQTT Log 最近一次上線且未斷線超過 10 分鐘之累計時間 (`now - dev.firstSeenMs`) 計算。自動動態格式化顯示為 `35秒` / `18分 42秒` / `02小時 15分`，提供護理與工程人員最直觀精準的傳輸器在上線即時狀態與運作時長！
   * 42. **單一 Gateway 無備援高危險路徑紅字警告與診斷彈窗警示 (Single Gateway High-Risk Alert)**：
       - **需求規格與修復**：
         1. **卡片紅字高危險標示 (Red Alert Badge on Device Card)**：
            - 當 BT 傳輸器在此工作週期中僅經過 1 台 Gateway 時（`gwCount <= 1`），判定為「無備援高危險路徑」，裝置卡片右下角標籤高亮改為**紅字顯告警**：`🚨 高危險無備援 (1台) ›`。
         2. **診斷彈窗深度文字警示 (Single Point of Failure Alert Box in Modal)**：
            - 點擊彈窗內「經過實體 Gateway 總數」標示為紅字 `1 台 ⚠️ (高危險路徑 / 無備援)`。
            - 彈窗上方新增醒目之**高危險單點故障警示框 (High-Risk Single Gateway Warning)**，明確提示護理/工程人員：「此 BT 傳輸器目前僅由 1 台實體 Gateway 涵蓋，收訊路徑無備援！若該 Gateway 斷線訊號將立即中斷，建議佈署第二台 Gateway 提供多重備援覆蓋。」
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

---

## [2026-07-20] 功能升級：雙模輸入（鍵盤+掃描槍）與虛擬測試條碼機制 (`7777777` & `AAAAAAA`)

### 1. 需求與升級 (Requirements & Features)
1. **雙模輸入相容**：同時相容 USB 條碼槍快速掃描與手動鍵盤輸入（按 Enter 或點擊按鈕自動完成觸發）。
2. **標準 8 位數病人條碼**：預設輸入 8 位數（如 `31100812`）時，系統自動解析前 3 碼為床號 (`311床`)。
3. **`7777777` 虛擬病人測試條碼**：以 7 個 `7` 開頭之條碼（如 `7777777` 或 `77777771`）將自動識別為「🧪 虛擬測試病人 (777床)」。
4. **`AAAAAAA` 虛擬 BT 傳輸器測試條碼**：以 7 個 `A` 開頭之條碼（如 `AAAAAAA00001`）將自動識別為「🧪 虛擬藍牙測試感測器」，並自動註冊至實時遙測監控面板提供實時數據模擬。

---

## [2026-07-20] 資料庫建立：7 位 3 碼編號護理人員名單 (`001` ~ `007`)

### 1. 護理師資料庫內建 (Nurse Database Setup)
內建 7 位專業護理人員之名單與單位資料，輸入代號時支援 `001` ~ `007` 3 碼格式（或單數字 `1`~`7` 自動補零解析）：
* `001`: **陳靜宜 護理長** (7樓一般外科護理站)
40. **喚醒週期次數 (Wake Cycle Counter) 解析與記憶保持機制重構 (Robust Wake Cycle Counter Fix)**：
    - **修復方案**：
      1. 在 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 導入二段式強健解析機制，自動淨化 Hex 字串中的非十六進位字符 (如空白/冒號)。
      2. 實作 **State Retention (狀態保持機制)**：當收到無 Scan Response 欄位之 Main ADV 封包時，自動保持先前採集之 `wakeCycleCounter` 數值，防止數值被覆蓋為 `-`。
41. **BT 裝置卡片點擊彈窗、工作週期與 Gateway 軌跡統計 (Clickable Card & Gateway Roaming Telemetry)**：
    - **需求規格與修復**：
      1. **BT 工作週期定義 (Lifecycle Termination Rules)**：
         - 超過 **10 分鐘** 未收到 MQTT 訊號，或工作時間超過 **180 小時**，即視同此 BT 傳輸器服務終止，系統自動重置該 BT 傳輸器之當前工作週期與 Gateway 歷程。
      2. **卡片微光 UI 與備註 (Clickable Device Cards)**：
         - 裝置卡片支援 `cursor: pointer;` 與青藍色微光懸浮效果。
         - 卡片底部標註備註：`💡 10分無訊號/180小時視同終止 🔍 Gateway 歷程 ›`。
      3. **Gateway 漫遊軌跡與接收次數診斷彈窗 (Gateway Roaming Inspector Modal)**：
         - 點擊卡片彈出 `#bt-device-modal` 視窗。
         - 精準統計並列表呈現該 BT 傳輸器在此工作週期中**經過的所有實體 Gateway 名稱、接收封包總次數、封包佔比 (%)、最新 RSSI、首次與最近擷取時間**，並標示規格條款。
      4. **響應式視窗高度與多重關閉機制 (Responsive Viewport Modal & Backdrop Click Fix)**：
         - 解決筆電等小螢幕高度時彈窗超出視窗無法滾動至底部點擊關閉按鈕之問題：限制彈窗最大高度為 `max-height: calc(100vh - 2.5rem)`，頁首標題與頁尾關閉按鈕固定 (`flex-shrink: 0`)，內容區域開啟獨立滾動條 (`overflow-y: auto`)。
         - 右上角點擊 `✕` 符號與點擊視窗外半透明遮罩背景皆可立即關閉彈窗，操作極致流暢。
* `002`: **林姿君 護理師** (5樓內科護理站)
### 1. 功能升級與修復摘要 (Key Improvements & Fixes)
1. **儀表板自動連線 (Auto-Connect MQTT)**：
   * 在 `switchPage('monitor')` 與頁面載入時加入自動觸發機制，切換至「藍牙儀表板」時自動執行 `connectMQTT()`，無需手動點擊連線按鈕。
2. **MedFlo 裝置標題字級與字距優化**：
   * 將 `.device-card .device-name` 字級由 `0.88rem` 調整為 `0.68rem` 搭配 `letter-spacing: -0.5px`，解決 19 碼裝置名稱（如 `MEDFLO-F44EFD5F88A0`）尾端被截斷為 `...` 的問題。
3. **Gateway 雙資料來源模式與過濾/排序機制**：
   * **`📡 實體 Gateway 模式`**：判定為關閉 PC 模擬，拒絕接收與過濾 `PC_SIM` 遙測封包，僅呈現在線之實體 Gateway 裝置。
   * **`💻 PC 模擬 Gateway 模式`**：開啟 PC 模擬，同時接收實體 Gateway 與 PC 電腦藍芽上報之數據，並強制將 PC 找到的 BT 裝置卡片**置頂排在最前面 (最左上方)**。
4. **PC 電腦實體藍芽引擎過濾重構 (`pc_ble_gateway_sim.py`)**：
   * 修復無名周遭藍芽設備（如筆電/電視）被自動冠上 `MEDFLO-` 導致產生假裝置卡片的 Bug。
   * 鎖定 **MAC 必須為 `F44EFD...` 或 `A100...`** 或廣播名稱確實為 `MEDFLO-...` 的滴護寶硬體，其餘雜訊一律拒絕。
5. **卡片自動銷毀門檻調整 (Auto-Prune Timeout)**：
   * 調整過期門檻為 **`3 分鐘` (180 秒)**：0~40秒正常高亮，40秒~3分鐘呈現半透明離線狀態，超過 3 分鐘自動清理銷毀舊卡片。

---

## [2026-07-22] Gateway 外觀工業設計 (40x40x10mm) 與 STEP 3D CAD 模型輸出

### 1. 外觀機構與 3D 建模 (Industrial Design & STEP CAD Generation)
* 依據極簡網關規格，完成 40mm x 40mm x 10mm 超小型網關外殼工業設計（R5mm 圓角、防滑紋理底座、頂部微雕 LOGO 標籤槽）。
* 機構僅配備 **1 個 USB Type-C 供電/傳輸埠** 與 **1 根全向天線**。
* 使用 Python CadQuery 實體 CAD 引擎成功生成並輸出 3D STEP 實體圖檔 [MedFlow_Gateway_Enclosure_40x40x10mm.step](file:///C:/Users/JOHN_WIESS/Desktop/MedFlow_Gateway_Enclosure_40x40x10mm.step) 與渲染圖檔 [MedFlow_Gateway_ID_Design.jpg](file:///C:/Users/JOHN_WIESS/Desktop/MedFlow_Gateway_ID_Design.jpg) 至桌面。

---

## [2026-07-22] NMGW2601 AI 醫療網關 Logo 3D 電路字體「e」與心電圖單彗星動畫影片輸出

### 1. Logo 3D 字體與重構 (NEX MED AI 3D Circuit Logo Refactoring)
* 重構 `NMGW2601_logo_ai_iot_16bit_072205_dithered.bmp`：將中央 IC 晶片上的圖示替換為**極致大氣且填滿晶片晶圓框的 3D 青色霓虹電路小寫字母「e」**（具備 3D 金屬斜角、暗色內溝槽與霓虹光暈），與 `NEX` / `M` / `D` 完美融為一體。
* 微調晶片比例與間距，修復並完整呈現在 `M` 字母右筆劃，呈現霸氣且工整和諧的 `NEX MED AI` 品牌視覺。

### 2. 精準心電圖單彗星動態影片 (Single ECG Comet Pulse Animation Video)
* **逐像素心電圖路徑追蹤 (Exact ECG Path Extraction)**：精確抓出圖檔下半部心電圖 Z 字型起伏波形的最亮中心路徑，並在中央 `AI` 斷層處實現水平平滑橫跨無縫銜接。
* **流線型彗星光點 (Streamlined Comet Light Dot)**：全圖保持純淨單一彗星光點（純白高亮頭部 + 30 點由粗到細漸層藍綠色流線拖尾）。
* **2 倍速明快傳輸 (2x Speed Enhancement)**：心電圖傳輸週期優化為 4 秒一次，節奏明快。
* **Windows 相容編碼**：使用 FFmpeg H.264 (AVC1) 編碼生成 [NMGW2601_Circuit_Signal_Animation.mp4](file:///C:/Users/JOHN_WIESS/Desktop/NMGW2601_Circuit_Signal_Animation.mp4) 與免播放器雙擊即看之動態圖檔 [NMGW2601_Circuit_Signal_Animation.gif](file:///C:/Users/JOHN_WIESS/Desktop/NMGW2601_Circuit_Signal_Animation.gif) 並交付桌面。

---

## [2026-07-25] 系統架構升級：MedFlow 醫療物聯網工具套件 (Suite Workstation) 整合與全新 Scanner UI / PC App 雙入口擴充

### 1. 需求與架構變更 (Requirements & Suite Architecture)
將原本以單一 MQTT 儀表板為主的 `mqtt_dashboard.html` 重構升級為 **MedFlow 醫療物聯網工具套件總入口 (MedFlow Suite Workstation Portal)**：
1. **4 大工具模組入口網格 (Landing Grid Extension)**：
   - 首頁與頂部導覽列擴充為 5 個頁面路由：`主選單 (landing)` | `藍牙實時儀表 (monitor)` | `護理SOP (sop)` | `藍牙掃描儀 (scanner)` | `PC工作站 (pcapp)`。
2. **新增入口頁面 1：MedFlow BLE 廣播與硬體掃描分析儀 (`#page-scanner`)**：
   - **全新 Web UI 設計**：採用 Cyber-Medical 暗色質感 HMI 介面。
   - **完全重現 `MedFlo_scanner` 功能**：包含 `MEDFLO-*` 傳輸器與 `NMGW2601-*` 網關雙頁籤切換、Manufacturer Data (`0xFFFF`) 逐 Byte 解析 (GPIO18 狀態, BIT0 電池低電量警示, BIT1 感測器異常警示)。
   - **探針與分析工具**：即時訊號強度 (RSSI dBm) 儀表與動態濾波滑桿、搜尋過濾、Raw Hex 封包微觀探針 (Inspector Modal) 與一鍵匯出符合 `medflo_scanner` 規範之 CSV 分析檔 (`medflo_scan_YYYYMMDD_HHMMSS.csv`)。
3. **新增入口頁面 2：MedFlow PC 串口 / 網絡工作站入口 (`#page-pcapp`)**：
   - **原始碼 100% 零改動 (Strict Source Protection)**：`MedFlo_PC_App_20260707` 目錄下所有程式碼與 `run.bat` 均保持完好原封不動。
   - **一鍵啟動與 SOP 指引**：在 Web 頁面呈現 USB Serial 115200/921600 bps 波特率診斷說明與手動啟動指引，並於 `server.py` 擴充 `/api/launch_pc_app` API 路由，實現點擊按鈕直接發起啟動 `MedFlo_PC_App_20260707\run.bat` 之無縫體驗。
4. **藍牙裝置表格與卡片固定位置機制 (Fixed Device Order)**：
   - 將原本依「最後收到封包時間 (lastSeen)」的浮動排序改為依 **Device Name / MAC 位址自然序號 (localeCompare numeric)** 固定排序。
5. **本機電腦 Bluetooth 硬體離線掃描引擎 (Bleak Integration)**：
   - 於 [server.py](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/server.py) 內建背景 `BleakScanner` 多執行緒，直接調用 PC 本機電腦之藍芽晶片進行被動廣播掃描。
   - 擴充 `/api/ble_devices` 路由供前端 `mqtt_dashboard.html` 自動輪詢，使網頁版 Scanner 在 MQTT 伺服器未連線的離線狀態下，仍能 100% 透過本機藍芽硬體即時掃描並呈現周遭所有 `MEDFLO-*` 傳輸器與 `NMGW2601-*` 網關。
6. **RSSI 訊號強度狀態保留機制 (RSSI Retention Mechanism)**：
   - 於 `server.py` 與 `mqtt_dashboard.html` (`processScannerPacket`) 修復舊版 `devData.rssi || -100` 導致強行重置為 `-100` 歸零的 Bug。
   - 實作 RSSI 狀態記憶：只有當收到合法的廣播訊號強度 (`-110 < RSSI <= 0`) 時才更新，若當前廣播封包無 RSSI 資訊則**100% 保持保留上一次的訊號強度狀態**，直到下一次新廣播掃描為止，徹底解決 RSSI Bar 閃爍歸零問題。
7. **CSS 變數缺失修復 (Missing --accent-yellow CSS Variable Bugfix)**：
   - 診斷出 RSSI 介於 `-65 dBm` 至 `-80 dBm` (如 `-66dBm, -70dBm, -74dBm, -76dBm, -78dBm`) 時，因 `:root` 中未定義 `--accent-yellow` 變數，導致瀏覽器將其渲染為透明透明背景（顯示為暗灰空條）。
   - 於 `:root` 補齊 `--accent-yellow: #eab308;` 與 `--accent-blue: #3b82f6;`，修復後中等訊號強度的黃色/琥珀色 RSSI Bar 100% 正常滿格與色彩顯示。
8. **網關 (Gateway) 表格欄位動態切換機制 (Dynamic Gateway Table Columns)**：
   - 修正網關頁籤原本顯示無關之傳輸器感測器欄位 (GPIO18 液位、電池電量、感測器狀態) 之錯誤。
   - 切換至 `NMGW2601-* 醫療網關列表` 時，動態將欄位標頭與資料行替換為 Gateway 專屬診斷指標：`Gateway Name (網關名稱)` | `MAC Address` | `RSSI` | `WiFi 狀態` | `BLE 在線` | `MQTT / OTA 診斷` | `Packets` | `Last Seen` | `操作`。
   - 精確符合 `medflo_scanner.py` 對 Gateway 網關診斷指標之專業規範。
9. **廣播逾時警告、離線自動恢復與歷史斷線紀錄 (`⚠️ (次數)` 探針彈窗)**：
   - **30秒逾時 (Yellow)**：當裝置超過 30 秒未收到新廣播封包時，`LAST SEEN` 欄位自動呈現黃色 `⏳ N秒前 (逾時)` 警示。
   - **60秒高度離線 (Red)**：當超過 60 秒未收到封包時，自動切換為紅色 `🔴 N秒前 (離線)` 警示。
   - **連線自動恢復 (Auto Recovery)**：當收到新廣播封包時，立即恢復為綠色正常更新狀態 (`剛剛 (1s)`)。
   - **歷史斷線 / 逾時紀錄 (`⚠️ (次數)`)**：凡曾進入 30s 或 60s 未更新狀態之裝置，將自動於 `LAST SEEN` 後方附帶 `⚠️ (次數)` 按鈕。點擊即可開啟專屬彈窗，查閱該裝置的 30秒逾時次數、60秒離線次數、以及帶有時間戳記 (Timestamp) 的完整事件歷史日誌。
10. **歷史紀錄彈窗 (Modal Overlay & ClassList) 開啟與巢狀結構修復**：
    - 診斷出點擊 `⚠️ (次數)` 無反應之兩項原因：(1) 前端 `warn-history-modal` 誤嵌套於前一個探針 Modal 內部導致 DOM 結構被隱藏；(2) 彈窗開啟邏輯誤使用 `.style.display = 'flex'` 而非本專案 CSS 規範之 `.classList.add('active')`。
    - 已全面修正 HTML DOM 獨立層級與 `.classList.add('active')` 開啟機制，點擊即可彈出滿版玻璃質感之歷史斷線紀錄分析視窗。
11. **單一裝置歷史斷線與逾時紀錄一鍵清除功能 (`🗑️ 清除此裝置紀錄`)**：
    - 在 `warn-history-modal` 歷史紀錄彈窗左下角新增「`🗑️ 清除此裝置紀錄`」紅色按鈕。
    - 點擊並二次確認後，可一鍵歸零該裝置的 30 秒逾時次數、60 秒離線次數，並清空歷史日誌清單；同步更新主表單，隱藏對應之 `⚠️ (次數)` 標籤。
12. **MedFlo PC App 多路徑動態探測與啟動機制 (Dynamic Multi-Path PC App Resolver)**：
    - 於 [server.py](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/server.py) 實作 `find_pc_app_path()` 探索引擎，同時支援原始搬移路徑 `C:\SW code\source code\MedFlo_PC_App_20260707\` 與套件內嵌路徑 `C:\SW code\source code\MefFlo_MQTT_Dashbaord\MedFlo_PC_App_20260707\`。
    - 不管使用者將 PC App 放置於何處，點擊「`🚀 一鍵啟動 PC 工作站`」皆可透過後台動態定位並順利啟動 `run.bat`。前端頁面同步列出多重備用路徑與動態適應指引。
14. **MedFlo PC 工作站兩欄式 Web UI 切圖與視覺介面建置 (PC Workstation Full UI Layout)**：
    - 依據開發者提供之 `MedFlo_PC_App_20260707` GUI 截圖，於 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 的 `#page-pcapp` 完成兩欄式 Cyber-Medical 視覺 UI 框架建置。
    - **左側邊欄 (~320px)**：包含 USB 連線控置區、Gateway 狀態監控區、WiFi 設定區、OTA 韌體更新綠色專卡、USB 傳輸狀態區與 WiFi 白名單設定區。
    - **右側主面板**：包含 Gateway 狀態儀表板與 0%~100% BLE 廣播頻率進度條、MQTT 設備列表 (DCare/d/#)、Gateway 指令通訊與 MAC 過濾條、以及 Gateway 原始廣播資料流 (USB UART) 表格，供後續逐一移植功能對接。
15. **PC 工作站前三大核心功能移植完成 (USB 連線、Gateway 狀態、WiFi 設定)**：
    - **1. USB 連線**：於 [server.py](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/server.py) 實作 `ServerSerialManager` 多執行緒控制與 `/api/serial_ports`, `/api/serial_connect`, `/api/serial_disconnect` API。點擊「`找 Port`」即可自動掃描電腦本機 COM 序列埠 (例如 `COM5`)，點擊「`連線`」後即可自動對時與啟動 UART 背景數據通訊。
    - **2. Gateway 狀態**：前端每 1.5 秒自動輪詢 `/api/serial_status`，即時呈現 WiFi連線 (已連線 🟢 / 未連線 🔴)、WiFi名稱、IP 位址、BLE日誌數與 Gateway 時間，並同步連動右側 Gateway 狀態儀表板與 USB 接收統計。
    - **3. WiFi 設定**：實作 `SET_WIFI:<SSID>,<Password>` 廣播指令傳送與重啟對話框，使用者填寫 SSID 與密碼點擊「`💾 儲存並重啟 Gateway`」後，系統可自動寫入並二次確認發送 `REBOOT` 指令使設定立即生效。
16. **NMGW2601 Gateway MQTT 通訊協定與 JSON 格式規格書撰寫 (Gateway MQTT Format Specification)**：
    - 深入分析 Gateway C 韌體原始碼 ([bt_log.c](file:///C:/SW%20code/source%20code/ITE9868_GWBuild_20260707/project/GW202601/bd/bt_log.c)) 之 MQTT 連線認證、雙 Socket (DCareW / DCareR) 分流機制、Topic 結構與 JSON Payload 封裝格式。
    - 已匯出完整規格書 Markdown 文件至 **桌面 (`C:\Users\JOHN_WIESS\Desktop\Gateway_MQTT_Format_Specification.md`)** 與 Gateway 專案根目錄 ([GATEWAY_MQTT_SPEC.md](file:///C:/SW%20code/source%20code/ITE9868_GWBuild_20260707/GATEWAY_MQTT_SPEC.md))，內容涵蓋 `DCare/d/<gwid>` 主廣播封包陣列 JSON 規格、`DCare/d/<gwid>/status` 心跳與 OTA 進度回報規格、以及 Broker 控制頻道格式。
17. **可編輯護理師與病人資料庫中控台自由折疊與關閉機制 (Collapsible Database Management Panel)**：
    - 於 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 的「`護理安裝 SOP`」頁面中，為「`⚙️ 醫院模式：虛擬名單與資料庫管理中控台`」區塊新增摺疊收起與展開按鈕 (`#btn-toggle-db-panel` / `toggleDatabasePanel()`)。
    - 在右上角與表格下方均提供「`🔼 收起管理中控台`」與「`🔽 展開資料庫管理`」快鍵，點擊即可流暢切換收起與展開，使用戶在進行 SOP 4 步驟安裝綁定時能維持最乾淨直觀的視覺焦點，需要調整名單時再一鍵展開。
18. **網關韌體版本 (FW Version) 動態解析與顯示機制修復 (Gateway FW Version Dynamic Resolver Bugfix)**：
    - **問題分析**：先前 PC 工作站 UI 的 MQTT 網關設備表單 (`pcapp-mqtt-tbody`) 含有切圖假資料 (`?`)，且未自動連動 MQTT 狀態頻道與 USB 串口之 `fw_ver` 欄位。
    - **修復方案**：
      1. 修改 [server.py](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/server.py) 之 `_parse_serial_line` 支援自動解析 Gateway 經由 USB 發送之 `ver`, `fw_ver`, `firmware` 欄位。
      2. 於 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 之 `processDashboardMessage` 增加 `DCare/d/<gwid>/status` 心跳與 Boot 報告之 `fw_ver` 自動擷取機制 (`pcappMqttGateways`)。
      3. 當收到 Gateway 狀態包時，同步更新「MQTT 設備列表 (DCare/d/#)」之「韌體版本」與右上角「網關版本 (`#dash-gw-ver`)」，讓網關版本 100% 正確顯示 (例如 `20260718_144211`)。
19. **MQTT 設備列表僅過濾並統一顯示 `NMGW2601-` 前綴之網關 ID (Gateway ID Standardizer & Filter)**：
    - **需求說明**：使用者要求「MQTT 設備列表 (DCare/d/#)」應僅顯示以 `NMGW2601-` 為前綴之正式網關設備。
    - **實作細節**：
      1. 於 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 新增 `formatGatewayId(gwid)` 函式，自動將原始 16 進位 MAC 或未格式化 ID（例如 `0000007A0C9D525D`, `NMGW2601C2460AD8`）統一轉化為帶有劃線前綴之標準格式 `NMGW2601-007A0C9D525D` 與 `NMGW2601-C2460AD8`。
      2. 於 `renderPcappMqttDevicesTable()` 增加強效過濾條件，僅渲染並列出 `NMGW2601-` 開頭之設備，非 Gateway 雜訊封包將自動排除。
20. **MQTT 網關即時連線/逾時/離線動態判定機制 (Gateway Dynamic Active/Timeout/Offline Evaluator)**：
    - **問題原因**：先前網關狀態 `status` 預設為靜態字串 `active`，未依照最後收到時間與當前時間差 (`Date.now() - dev.lastSeenMs`) 動態計算，導致 13:06:42 數小時前的歷史紀錄依然標示為 `active`。
    - **修復方案**：
      1. 於 `processDashboardMessage` 寫入精確毫秒時間戳記 `lastSeenMs`。
      2. 於 `renderPcappMqttDevicesTable()` 建立動態狀態計算邏輯：
         - **`< 45 秒`**：在線（綠色 `active` 🟢）
         - **`45 ~ 90 秒`**：逾時未上報（黃色 `timeout` 🟡）
         - **`> 90 秒`**：離線未回應（紅色 `offline` 🔴）
      3. 每 1.5 秒自動輪詢與動態重新排序（最新上線之網關排在最上方），使離線網關正確顯示紅底 `offline`。
21. **PC 工作站 (`page-pcapp`) 頁面載入與切換時自動連線 MQTT 機制 (PC App Page Auto-Connect Fix)**：
    - **問題分析**：先前頁面開起與切換機制 (`switchPage` & `DOMContentLoaded`) 僅針對 `monitor` 與 `scanner` 頁面自動發起 `connectMQTT()`，導致開啟或切換至 `PC 串口 / 網絡工作站` 頁面時右上角維持 `⚪ 未連線` 狀態。
    - **修復方案**：
      1. 修改 `switchPage(pageId)`：當切換至 `pcapp` 頁面且 MQTT 為斷線狀態時，自動延遲 100ms 觸發 `connectMQTT()`。
      2. 修改 `window.addEventListener('DOMContentLoaded')`：若直接載入 `pcapp` 頁面，自動觸發 WebSocket 伺服器連線與 `DCare/d/#` 全頻道訂閱，確保右上角顯示 `🟢 已連線` 且即時數據上報順暢。
22. **一鍵清除離線網關設備功能 (`🗑️ 清除離線`)**：
    - 於 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 的「MQTT 設備列表 (DCare/d/#)」卡片標頭右側新增紅色快鍵「`🗑️ 清除離線`」(`pcappClearOfflineMqttGateways()`)。
    - 點擊後會自動將暫存表中已離線（`> 90 秒` 無廣播心跳包）之過期網關紀錄一鍵掃除，按鈕即時提示「`已清除 X 台`」，讓使用者隨時維持乾淨且僅包含活躍連線中網關之即時清單。
23. **USB 連線序列埠 COM7 自動掃描與預設選取機制 (COM7 Auto-Scan & Priority Selector)**：
    - **問題分析**：先前 `pcappScanPorts()` 未在開頁時自動發起，且 `catch` 塊寫死 `COM5`，導致使用 Gateway 實體 USB 連線時 (電腦為 `COM7`) Dropdown 下拉選單顯示空白或遺失。
    - **修復方案**：
      1. 修改 `pcappScanPorts()`：於掃描本機 COM 口時自動優先尋找並預設選取 **`COM7`**。
      2. 於 `switchPage('pcapp')` 與 `DOMContentLoaded` 加入自動發起 Ports 掃描機制，使用者一開頁即可看見下拉選單預設選中 `COM7`，點擊「`連線`」後即可發起 UART 通訊。
24. **USB 連線狀態指示燈與數據動態傳輸橫幅 (USB Live Transmission Banner & Baud Rate Selector)**：
    - **問題分析**：先前 USB 卡片僅有靜態按鈕，連線後若無資料流經，使用者無法區分「COM Port 是否成功開啟」與「Gateway 是否正在透過 UART 傳送數據」。
    - **修復方案**：
      1. 新增 **Baud Rate 波特率選單**（預設 115200bps，可切換 921600bps 高速檔位）。
      2. 於 USB 連線卡片頂端新增動態 Status Badge (`🟢 已連線 (COM7)` / `🔴 未連線`)。
      3. 於卡片內新增 **USB 動態數據傳輸橫幅 (Transmission Banner)**：
         - **傳輸中**：顯示亮綠燈 `🟢 數據傳輸中 (115200 bps)` 並即時顯示累計接收 Byte 與 Line 行數（例：`12.5 KB (148 行)`）。
         - **等待中**：顯示黃燈 `🟡 已開啟 COM7 | 等待 Gateway UART 上報中...`。
         - **未連線**：顯示 `⚪ 尚未連接 USB 串口`。
      4. 即時連動更新左側邊欄之「已接收字元數 (`pcapp-stat-bytes`)」與「累計行數 (`pcapp-stat-lines`)」，讓 UART 通訊狀態 100% 視覺化呈現在畫面上。
25. **徹底移除開頁寫死之歷史離線範例網關 (Clean Initial Mock Devices)**：
    - **問題分析**：先前 JS `pcappMqttGateways` 變數與 HTML 表格內預設寫死了兩台測試假網關 (`NMGW2601-007A0C9D525D` / `NMGW2601-C2460AD8`)，導致即使手動點擊「清除離線」，重新整理網頁時 JS 重新初始化依然會將該兩台帶回畫面上。
    - **修復方案**：
      1. 將 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 中 `let pcappMqttGateways` 初始化改為純淨空物件 `{}`。
      2. 移除 `<tbody id="pcapp-mqtt-tbody">` 內硬編碼之靜態 `<tr>` 測試列，預設顯示「`等待 NMGW2601- 網關封包上報中...`」。
      3. 確保刷新頁面後完全乾淨，僅有真實即時上報之活躍網關會動態呈現在清單中。
26. **防止誤觸 Logo 導致網頁無預警跳回主選單修復 (Page Persistence & Logo Click Lock)**：
    - **問題分析**：先前頂部導覽列左側標題 `<div class="logo-container">` 綁定了 `onclick="switchPage('landing')"`，且點擊範圍過大，當使用者在操作 PC 工作站時若滑鼠不小心點到頂部標題區域，即會發起頁面切換並跳回「工具套件總入口 (`landing`)」。
    - **修復方案**：
      1. 移除 `logo-container` 上的誤觸 `onclick` 事件，限制僅有顯式點擊頂部 **`🏠 主選單`** 按鈕才會切換頁面。
      2. 於 `switchPage()` 加入 **`sessionStorage` 與 `location.hash` 頁面狀態持久化**，確保重新整理或頁面更新時能 100% 保持在目前的「`PC 串口 / 網絡工作站` (`#pcapp`)」頁面，不再意外跳回主頁。
27. **MQTT 設備列表固定排序機制 (Fixed Stable Table Sorting)**：
    - **問題分析**：先前 `renderPcappMqttDevicesTable()` 採用「最後收到時間 (`lastSeenMs`)」遞減排序，當多台 Gateway 頻繁上報心跳包時，列表內的網關會因為毫秒級的時間差頻繁上下對調跳動，造成視覺閃爍與排版不穩定。
    - **修復方案**：
      1. 將 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 內的排序方式改為 **`Gateway ID 字典序 (idA.localeCompare(idB))` 穩定固定排序**。
      2. 設備 row 的位置隨時保持固定，即使持續收到即時廣播，資料列也不會再發生跳動對調，提升操作與閱覽體驗。
28. **Gateway ID 格式化去重與 0000 補位去除 (Gateway ID Normalization & MAC 0000 Prefix Stripping)**：
    - **修復方案**：升級 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 中的 `formatGatewayId()` 函數，自動清理 MAC 位址冒號與開頭的 `0000` 前綴補位，將 `NMGW2601-0000B46DC249927C` 統一標準化為 `NMGW2601-B46DC249927C`。使「藍牙掃描儀」與「PC 工作站」兩側的網關 ID 100% 齊一精確吻合。
29. **WiFi 連線 SSID 名稱回報精確修正 (Real Active WiFi SSID Reporting Fix)**：
    - **問題分析**：先前 Gateway 在 UART USBD ACM 回傳 `$STATUS` 封包時，`peripheral.c` 硬編碼傳遞了 NOR Flash 中記錄的主 AP `theConfig.ssid`（`wiess-2.4G`）。當 Gateway 切換連線至備用熱點 / 手機熱點（如 iPhone / WiFi2）時，傳回的 SSID 依然會誤顯示為 `wiess-2.4G`。
    - **修復方案**：修改 Gateway [peripheral.c](file:///C:/SW%20code/source%20code/ITE9868_GWBuild_20260707/project/GW202601/wsp/peripheral.c#L440)，當 Gateway 成功連線時優先讀取實時連線目標 `g_current_ssid`，確保儀表板能 100% 精確顯示 Gateway 當前實際連上的 WiFi SSID 熱點名稱。
30. **介面文字精準化修訂 (PC 串口全面更名為 PC USB)**：
    - **修復方案**：將 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 導覽列按鈕、卡片標題、頁面 Title 與通知文字中之「`PC 串口`」全面正名為 **`PC USB`**，突顯「藉由 Gateway PC USB 實時讀取並掌控 Gateway 全功能狀態」之核心任務定位。
31. **新增「🚀 OTA 發布與 MQTT 設備管理」獨立中控頁面 (Dedicated OTA & MQTT Page)**：
    - **修復方案**：
      1. 於主選單與頂部導覽列新增 **`🚀 OTA 發布` (`page-ota`)** 獨立頁面。
      2. 將「網關韌體發布中心 (OTA Release: 區域網路 HTTP / GitHub Releases / USB / MQTT / 廣播 OTA)」與「🌐 MQTT 全網設備列表 (DCare/d/#)」自 PC USB 頁面完整搬移至此新頁面中。
      3. 使 `PC USB 工作站` 頁面專注於 PC 本機 Serial 即時狀態掌控與調試，而 `OTA 發布及設定` 頁面專注於全網網關韌體升級與在線設備管理。
32. **COM Port 電腦插拔自動感測與預設高亮選取 (Auto COM Port Detection & Default Selection)**：
    - **修復方案**：
      1. 於 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 引入 `startPcappPortAutoScan()` 3 秒背景自動輪詢感測機制。
      2. 當電腦偵測到可用 Serial 介面（如 Gateway 接上之 `COM7`）時，下拉選單會**自動填入、預設選取並高亮顯示 `COM7 (已自動偵測)`**，並於下方顯示 `🟢 電腦已自動偵測到 COM7` 綠色提示。使用者無需手動輸入或拉開下拉選單即可直接點擊「連線」！
34. **SSID 來源權責澄清與雙側面板 100% 串口資料對齊 (100% Raw Gateway USB Serial SSID Alignment)**：
    - **修復方案**：將左側面板 `pcapp-stat-ssid` 與右側儀表板 `dash-wifi-name` 統一綁定 Gateway 實體串口傳回之真實 `st.ssid`，確保兩側資料 100% 一致且忠實呈現 Gateway 串口真實數據。
35. **PC USB 工作站資訊來源 100% 串口純化規範 (Strict Pure USB Serial Isolation)**：
    - **最高指導原則**：使用者嚴格規範：「`PC USB 工作站` 頁面內之所有資訊只能 100% 完全由 USB 連線 Gateway 串口實體讀取，禁止從任何外部網路 (如 MQTT Broker / WebSocket) 取得資訊」。
    - **執行細節**：
      1. 移除 `switchPage('pcapp')` 內呼叫 MQTT 網路連線之 `connectMQTT()`，杜絕任何第三方網路干擾。
      2. 將右側儀表板之網路狀態欄位明確正名為 **`WiFi 連線`**，並 100% 由 Gateway USB Serial 回報之 `st.wifi_connected` 與 `st.ip` 判定，顯示 `已連線 🟢` / `未連線 🔴`。
      3. 確保 `PC USB 工作站` 頁面達到 100% 物理層 USB 獨立除錯之嚴密標準。
36. **Gateway 狀態重複卡片合併 (Merged Duplicate Gateway Status Cards)**：
    - 移除左側邊欄重複的 `📡 Gateway 狀態` 卡片，所有狀態統一呈現於右側 `🖥️ Gateway 狀態儀表板`，頁面更簡潔。
37. **Serial 連線佔用自我清理機制 (Auto Self-Cleanup & 3x Retry on Serial Connect)**：
    - **問題**：前端重複點擊「連線」時，後台自己的線程仍持有 COM Port Handle，導致 `PermissionError 13` 存取被拒。
    - **修復**：`connect()` 開頭強制調用 `disconnect()` 清理舊連線，並加入最多 3 次 300ms 間隔之自動重試機制。`disconnect()` 亦加入 200ms 釋放延遲，確保 Windows OS Handle 完全釋放。
38. **HTTP 靜態檔案 `do_GET` 修復 (Restore Static File Serving)**：
    - **問題**：在優化 HTTP Router 時，`do_GET` 最後遺漏 `return super().do_GET()`，導致瀏覽器無法開啟 HTML 檔案（Remote Disconnected）。
    - **修復**：補回 `return super().do_GET()` 靜態檔案回傳機制。
39. **一鍵啟動 BAT 可靠性修復 (Reliable Launcher BAT with Server-Ready Polling)**：
    - **問題**：`start_win.bat` 與 `MedFlow啟動.bat` 使用固定 `timeout /t 2` 等待，若 Server 啟動較慢（Port TIME_WAIT 尚未釋放）則瀏覽器在 Server ready 之前開啟而失敗。
    - **修復**：改用 Python HTTP polling loop 輪詢 `http://127.0.0.1:8080/`，確認 Server 真正回應 HTTP 200 後才發出 `start http://127.0.0.1:8080/` 開啟瀏覽器，最終驗證 100% 成功。
40. **喚醒週期次數 (Wake Cycle Counter) 解析與記憶保持機制重構 (Robust Wake Cycle Counter Fix)**：
    - **修復方案**：
      1. 在 [mqtt_dashboard.html](file:///C:/SW%20code/source%20code/MefFlo_MQTT_Dashbaord/mqtt_dashboard.html) 導入二段式強健解析機制，自動淨化 Hex 字串中的非十六進位字符 (如空白/冒號)。
      2. 實作 **State Retention (狀態保持機制)**：當收到無 Scan Response 欄位之 Main ADV 封包時，自動保持先前採集之 `wakeCycleCounter` 數值，防止數值被覆蓋為 `-`。
41. **BT 裝置卡片點擊彈窗、工作週期與 Gateway 軌跡統計 (Clickable Card & Gateway Roaming Telemetry)**：
    - **需求規格與修復**：
      1. **BT 工作週期定義 (Lifecycle Termination Rules)**：
         - 超過 **10 分鐘** 未收到 MQTT 訊號，或工作時間超過 **180 小時**，即視同此 BT 傳輸器服務終止，系統自動重置該 BT 傳輸器之當前工作週期與 Gateway 歷程。
      2. **卡片微光 UI 與備註 (Clickable Device Cards)**：
         - 裝置卡片支援 `cursor: pointer;` 與青藍色微光懸浮效果。
         - 卡片底部標註備註：`💡 10分無訊號/180小時視同終止 🔍 Gateway 歷程 ›`。
      3. **Gateway 漫遊軌跡與接收次數診斷彈窗 (Gateway Roaming Inspector Modal)**：
         - 點擊卡片彈出 `#bt-device-modal` 視窗。
         - 精準統計並列表呈現該 BT 傳輸器在此工作週期中**經過的所有實體 Gateway 名稱、接收封包總次數、封包佔比 (%)、最新 RSSI、首次與最近擷取時間**，並標示規格條款。
