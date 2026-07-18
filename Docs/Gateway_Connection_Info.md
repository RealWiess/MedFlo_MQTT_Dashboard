# MedFlow 閘道器連線與 MQTT 通訊規格 (Gateway Connection & MQTT Specs)

本文件記錄 **滴護寶 (Smart IV Drip Monitor)** 閘道器 (Gateway) 的連線資訊、MQTT Broker 設定、線上測試工具以及上報之 JSON 資料格式，便於開發與偵錯時快速查閱。

> [!NOTE]
> **本機閘道器開發資料與路徑 (Gateway Design & Source Code Path)**：
> * **硬體與設計資料路徑**：[C:/公司/Design/睿建滴護寶/GW](file:///C:/公司/Design/睿建滴護寶/GW)
> * **原始碼路徑 (開發基礎)**：[C:/SW code/source code/](file:///C:/SW%20code/source%20code/) (依照日期區分，當天若有產生新 source code 並編譯成功，會產生如 ITE9868_GWBuild_YYYYMMDD 的新資料夾)

---

## 1. MQTT 連線設定 (MQTT Broker Settings)

* **MQTT 伺服器 (Host)**: `mqtt.go6.tw`
* **通訊埠 (Ports)**:
  * **8883** (SSL 加密傳輸 - 建議生產環境使用)
  * **1883** (No SSL 明文傳輸 - 僅供測試)
  * **8083** (Websocket SSL 加密 - 前端網頁端連線使用)

### 1.1 發佈權限 (Write / Publish)
* **帳號 (Username)**: `DCareW`
* **密碼 (Password)**: `4rfghy6`
* **發佈主題 (Topic)**: `DCare/d/<gwid>` (請將 `<gwid>` 替換為實際閘道器的 16 碼識別碼)

### 1.2 訂閱權限 (Read / Subscribe)
* **帳號 (Username)**: `DCareR`
* **密碼 (Password)**: `6yhgvfr4`
* **訂閱主題 (Topic)**: `DCare/d/#` (可接收與監聽所有閘道器上報的數據)

---

## 2. 線上測試工具與網址 (Debugging URLs)

在開發與驗證連線時，可使用以下 Noonspace 提供的網頁版 MQTT 測試工具：

* **測試發佈 (Write) 網址**: [Noonspace MQTT Write Tool](https://mqtt.noonspace.com/mainssl/modules/MySpace/index.php?sn=mqtt&pg=ZC4876)
* **測試收訊 (Read) 網址**: [Noonspace MQTT Read Tool](https://mqtt.noonspace.com/mainssl/modules/MySpace/index.php?sn=mqtt&pg=ZC4854)

---

## 3. 閘道器上報 JSON 資料格式 (Payload Format)

閘道器會定期將掃描到的端點遙測資料包裝成 **JSON 陣列** 發送。以下為標準的資料範例：

```json
[
  {
    "channel": 924000000,
    "sf": 10,
    "time": "2024-11-01T10:42:22+08:00",
    "gwip": "192.168.0.19",
    "gwid": "00005813d34aed65",
    "repeater": "00000000ffffffff",
    "systype": 161,
    "rssi": -33,
    "snr": 23,
    "snr_max": 33.8,
    "snr_min": 20,
    "macAddr": "00000000a1001176",
    "data": "00000000",
    "frameCnt": 8,
    "fport": 3
  }
]
```

### 3.1 欄位定義說明 (Field Definitions)

| 欄位名稱 | 資料類型 | 範例值 | 說明 |
| :--- | :--- | :--- | :--- |
| **channel** | Number | `924000000` | 通訊頻道頻率 (Hz) |
| **sf** | Number | `10` | 擴頻因子 (Spreading Factor) |
| **time** | String | `"2024-11-01T10:42:22+08:00"` | 遙測封包生成之 RFC3339 時間戳記 (含時區) |
| **gwip** | String | `"192.168.0.19"` | 閘道器取得之區域網路 IP 位址 |
| **gwid** | String | `"00005813d34aed65"` | 閘道器的 16 碼唯一識別碼 |
| **repeater** | String | `"00000000ffffffff"` | 中繼器識別碼，預設為 `00000000ffffffff` |
| **systype** | Number | `161` | 系統類型代碼，固定為 `161` (代表滴護寶健康照護系統) |
| **rssi** | Number | `-33` | 接收信號強度指示 (dBm) |
| **snr** | Number | `23` | 信號雜訊比 (dB) |
| **snr_max** | Number | `33.8` | 最大信號雜訊比 (dB) |
| **snr_min** | Number | `20` | 最小信號雜訊比 (dB) |
| **macAddr** | String | `"00000000a1001176"` | **偵測端點 (Node) 的 16 碼識別碼** (前 8 碼為 `00000000` + 後 8 碼藍牙 MAC 位址) |
| **data** | String | `"00000000"` | **感測狀態數據 (HEX 格式，固定 8 字符)**。<br>• 前 4 字符預留為 `0000`<br>• 第 5-6 字符為 Rolling Counter (如 `08`) <br>• 最末 2 字符為 Status Byte (如 `1F` 代表液位正常) |
| **frameCnt** | Number | `8` | 滾動訊框計數器，用於確認防重送與丟包 (直接映射藍牙廣播 Rolling Counter) |
| **fport** | Number | `3` | 應用邏輯埠，預設為 `3` |
