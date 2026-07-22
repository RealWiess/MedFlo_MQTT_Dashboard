# 🏥 MedFlow 滴護寶藍芽動態監測牆 - 全平台安裝與操作說明書 (InstallPack)

本資料夾 `InstallPack` 包含了 **MedFlow 滴護寶藍芽與 MQTT 實時監測牆系統** 的跨平台完整發行包與安裝檔案。

本系統支援 **Windows**、**macOS**、**Android (安卓手機/平板)** 與 **iOS / iPadOS (iPhone / iPad)** 四大作業系統平台。

---

## 📌 作業系統對照與快速啟動指南 (OS Compatibility Guide)

| 平台 (OS) | 推薦使用方式 | 使用對應檔案 / 操作步驟 |
| :--- | :--- | :--- |
| **💻 Windows**<br>(PC / 護理推車) | **雙擊一鍵啟動** 或<br>內建 Chrome / Edge 開啟 | 雙擊執行 `start_win.bat`<br>（或雙擊直接開啟 `mqtt_dashboard.html`） |
| **🍏 macOS**<br>(MacBook / Mac Mini) | **雙擊一鍵啟動** 或<br>Safari / Chrome 開啟 | 雙擊執行 `start_mac.command`<br>（或用 Safari 開啟 `mqtt_dashboard.html`） |
| **📱 Android**<br>(安卓手機 / 平板) | **局域網開頁** +<br>**PWA 安裝至桌面** | 1. 電腦執行 `server.py` 取得局域網 IP (如 `http://192.168.1.100:8080`)<br>2. 安卓用 Chrome 開啟網址，點擊網頁選單「**安裝應用程式**」生成 App |
| **🍎 iOS / iPadOS**<br>(iPhone / iPad) | **局域網開頁** +<br>**新增至主畫面** | 1. 手機/iPad 連接護理站 Wi-Fi 並用 Safari 開啟網址<br>2. 點擊 Safari 下方「**分享**」按鈕 ➜ 選擇「**新增至主畫面**」 |

---

## 💻 1. Windows 作業系統安裝與使用步驟

### 方法 A：1-Click 雙擊一鍵啟動 (推薦)
1. 進入 `InstallPack` 資料夾。
2. **雙擊 `start_win.bat`**。
3. 系統會自動啟動並以視窗載入藍芽動態監測牆網頁。

### 方法 B：網頁瀏覽器直接開啟
1. **雙擊 `mqtt_dashboard.html`**，系統將以您的預設瀏覽器（Chrome / Edge / Firefox）開啟。
2. 開啟後系統將自動連線 MQTT 伺服器並顯示數據。

### 方法 C：桌面原生安裝檔 (.exe Build)
- 資料夾內已附帶 `package.json` 與 `main.js`。在命令列執行 `npm run build:win` 即可打包產出 `MedFlow-Setup.exe` 安裝檔。

---

## 🍏 2. macOS 作業系統安裝與使用步驟

### 方法 A：1-Click 雙擊一鍵啟動 (推薦)
1. 進入 `InstallPack` 資料夾。
2. **雙擊 `start_mac.command`**。
3. 系統將在 Mac 上自動開啟監測牆應用程式視窗。

### 方法 B：Safari / Chrome 開啟
1. 右鍵選擇 `mqtt_dashboard.html` ➜ 以 **Safari** 或 **Google Chrome** 開啟。

### 方法 C：macOS 原生安裝檔 (.dmg Build)
- 在 Mac Terminal 執行 `npm run build:mac` 即可產出支援 Apple Silicon (M1/M2/M3) 與 Intel 晶片之 `MedFlow-Dashboard.dmg` 安裝包。

---

## 📱 3. Android 安卓手機 / 安卓平板使用步驟

1. **共享伺服器啟動**：
   - 在主控電腦（Windows 或 Mac）雙擊執行 `server.py`（或執行 `start_win.bat`）。
   - 終端機畫面上會顯示局域網網址（例如：`http://192.168.1.100:8080`）。
2. **手機/平板開啟**：
   - 將安卓手機或平板連上與電腦相同的 Wi-Fi 網路。
   - 用 **Chrome 瀏覽器** 輸入網址 `http://192.168.1.100:8080`。
3. **一鍵安裝為 App (PWA)**：
   - 開啟網頁後，點擊網址列旁的「**安裝應用程式**」或右上方選單「新增至主畫面」。
   - 手機/平板桌面將生成 **MedFlow 專屬 App 圖示**，未來點擊即可獨立全螢幕運行！

---

## 🍎 4. iPhone / iPad (iOS & iPadOS) 使用步驟

1. **連線局域網**：
   - 確保 iPhone / iPad 已連上護理站 Wi-Fi。
2. **Safari 瀏覽器開啟**：
   - 用 **Safari** 輸入電腦上顯示的網址（例如 `http://192.168.1.100:8080`）。
3. **新增至主畫面 (iOS PWA)**：
   - 點擊 Safari 底部中央的「**分享** (Share)」圖示 📤。
   - 向下滾動選單並點擊「**新增至主畫面** (Add to Home Screen)」➕。
   - 點擊右上角「新增」，iOS 畫面上即可生成 **MedFlow 獨立 App 應用程式**！

---

## ⭐ MedFlow 系統核心功能與防呆機制介紹

1. **⚡ 自動連線 (Auto-Connect)**：
   - 進入藍芽儀表板後 300ms 內自動連線至 MQTT 伺服器 (`mqtt.go6.tw`)，無須手動按連線。

2. **🔴 尿袋滿音效提醒 (Audio Alarm)**：
   - 發生「尿袋滿」時，系統透過 Web Audio API 自動播放 **3 次「叮咚！叮咚！叮咚！」** 門鈴警示聲（100% 離線可用，免外掛音效檔）。

3. **🚨 30 秒卡片全紅告警升級 (Escalation Alert)**：
   - 若尿袋滿狀態持續 30 秒未處置，音效升級為 **6 次叮咚聲**，且**整張病床卡片轉為全紅亮燈與脈衝發光**！

4. **🔝 優先處置自動置頂排序 (Top Priority Sorting)**：
   - 告警或尿袋滿之病床卡片會**自動移動至監測牆最前方（第一排第一個）**，便於醫護人員秒級回應處理。

5. **✏️ 醫護人員資訊校正與解綁**：
   - 卡片右上角提供 `✏️ 編輯` 按鈕（隨時校正錯字、床號、病患資訊）與 `解綁/完成` 按鈕（完成監測任務後動態自監測牆移除）。

6. **🧪 虛擬測試防誤觸鎖定**：
   - 手動點擊切換滿/空狀態僅開放給 `MedFlo-AAAAAAA` 開頭之虛擬測試裝置；實體藍牙感測器（如 `F44EFDD51450`）安全鎖定禁止點擊篡改。

---

## 📂 資料夾檔案清單 (Package Files)

```text
InstallPack/
├── README.md               # 本全平台使用與安裝說明書
├── mqtt_dashboard.html     # 藍芽動態監測牆主程式 (已內建離線資源與響應式排版)
├── start_win.bat           # Windows 1-Click 雙擊啟動檔
├── start_mac.command       # macOS 1-Click 雙擊啟動檔
├── server.py               # 跨平台 Python 局域網分享與 Web 伺服器
├── manifest.json           # PWA 手機/平板 App 安裝描述檔
├── sw.js                   # PWA Service Worker 離線快取
├── package.json            # Electron 桌面原生 App 打包設定
└── main.js                 # Electron 主進程控制器
```

---

*MedFlow 智慧醫療軟體研發團隊 榮譽出品*
