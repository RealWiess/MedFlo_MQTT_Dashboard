# 滴護寶 (MedFlo) 藍牙貼片 (Sensor Node) 修改建議

本文件記錄了未來針對 MedFlo 藍牙貼片（藍色小裝置）進行韌體或硬體改版時，建議進行的最佳化調整，以提升系統的相容性與穩定性。

## 1. 藍牙廣播 (BLE Advertisement) 格式修正

### 發現問題
目前的藍牙廣播中，自定義廠商資料 (Manufacturer Specific Data) 的 Raw Data 為：
`02 FF 01` (或 `02 FF 00`)
* **長度**: `0x02`
* **類型**: `0xFF` (Manufacturer Specific Data)
* **資料**: `0x01` 或 `0x00`

**問題點：** 根據國際藍牙核心規範 (BLE Core Spec)，當宣告資料類型為 `0xFF` 時，其後方**強制要求必須跟隨 2 bytes 的公司代碼 (Company Identifier Code)**。目前的廣播長度僅為 2，連填寫公司代碼的空間都不足（僅有 1 byte 的資料 `0x01`）。
這種殘缺格式雖然在部分 Android 設備上能被寬容讀取，但在 Windows 藍牙底層 API（或某些嚴格的 Gateway 藍牙協議棧）中，極高機率會被判定為「無效格式」而直接將該段資料丟棄，導致 PC App 或 Gateway 讀不到狀態碼。

### 修改建議 (強烈建議)
未來如果有機會修改貼片的韌體，強烈建議將廣播格式改為合法的 BLE 規範格式。

**修改方案：塞入假的公司代碼 (Dummy Company ID)**
將原本的 `02 FF 01` 修改為：
`04 FF FF FF 01` (或 `04 FF FF FF 00`)

* **`04`**: 長度變更為 4 bytes。
* **`FF`**: 類型維持 Manufacturer Specific Data。
* **`FF FF`**: 填充兩個 FF 作為假的公司代碼 (Company ID = 0xFFFF 代表測試或保留值)。
* **`01` / `00`**: 實際的狀態碼。

**預期效益：** 
修改後，所有作業系統（包含 Windows 與 IT9866 Gateway 的底層 C 語言解析）都能 100% 穩定且合法地讀取到 `01` 或 `00` 的狀態，徹底解決 PC 端軟體無法解析紅綠燈的問題。
