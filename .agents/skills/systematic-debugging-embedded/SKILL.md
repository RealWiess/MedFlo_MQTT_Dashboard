---
name: Systematic Debugging for Embedded Firmware
description: 韌體除錯鐵律：遇到任何 Bug、當機、開機失敗或異常行為時，必須先系統化追根因，嚴禁猜測性修復。適用於 ITE SoC / OpenRTOS / C 嵌入式環境。
---

# 嵌入式韌體系統化除錯規範 (Systematic Debugging for Embedded)

> **靈感來源**：[obra/superpowers — systematic-debugging](https://github.com/obra/superpowers)
> **改寫目的**：將原版針對 Web/App 的除錯方法論，重寫為適合 ITE IT986x SoC、OpenRTOS、C 語言嵌入式韌體開發的版本。

---

## 鐵律 (The Iron Law)

```
嚴禁在未找到根因之前嘗試修復。
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.
```

隨機猜測式修改不僅浪費時間，還會：
- 引入新的隱藏 Bug（特別是在 ISR 和共享資源場景）
- 掩蓋真正的根因，使未來除錯更困難
- 產生「改了三個地方才好了，但不知道哪個是關鍵」的混亂歷史

**宣告**：進入除錯模式時，先說「我正在使用系統化除錯流程，先收集證據再修改。」

---

## 適用場景

在以下任何情況下啟動本流程：

- 韌體當機、重啟、Data Abort
- 開機失敗或成功率偏低
- BLE/WiFi 功能異常（連線失敗、Scan 沒結果、MAC 全零）
- UART log 出現異常輸出或靜默
- 周邊設備行為異常（GPIO、CAN-FD、I²C、SPI）
- 編譯通過但燒錄後行為不符預期
- 間歇性問題（「有時候會」型 Bug）

**特別需要本流程的時刻**：
- ⚡ 時間壓力很大（緊急修復最容易猜錯）
- 🔄 已經嘗試修過但問題反覆出現
- 🤔 對問題的理解很模糊（「不知道為什麼壞了」）

---

## Phase 1：證據收集（必做，不可跳過）

目標：建立客觀事實基礎。**在此階段絕不修改任何 source code。**

### 1.1 重現問題

- [ ] 問題能穩定重現嗎？記錄重現步驟。
- [ ] 間歇性問題：記錄發生頻率、是否與特定操作/時序/溫度相關。
- [ ] 確認問題出現的「邊界條件」：哪些情況會觸發、哪些情況不會。

### 1.2 收集 UART Log

```
這是嵌入式除錯的第一手證據，等同於 Web 開發中的 console.log + stack trace。
```

- [ ] 完整擷取問題發生前後的 UART 輸出（包含時間戳記）
- [ ] 標記最後一行正常輸出 → 第一行異常輸出之間的「斷點」
- [ ] 搜尋 Error / Abort / Fault / Assert / HardFault 等關鍵字
- [ ] 若 UART 完全靜默：確認是否為 Boot 階段失敗（SPI Tool 查詢開機模式）

### 1.3 檢查硬體狀態

- [ ] SPI Tool：查詢 Chip ID、開機模式、Memory 運行狀態
- [ ] 供電電壓是否正常（IVDD 1.2V、IO 3.3V）
- [ ] 晶片溫度是否異常
- [ ] 是否有最近的硬體變更（板子版本、零件替換）

### 1.4 檢查最近變更

- [ ] `git log -5` 或 `git diff HEAD~1` 確認最近改了什麼
- [ ] 閱讀 DEVELOPMENT_LOG.md 確認是否有已知相關問題
- [ ] 確認 CMake cache 是否被正確清除（避免編譯到舊程式碼）

---

## Phase 2：根因隔離

目標：縮小問題範圍，定位到具體的模組/函數/暫存器。

### 2.1 二分法定位

```
將問題空間持續切半，直到找到最小可重現範圍。
```

- **軟體二分法**：`git bisect` 或手動回退到上一個已知正常的 commit，確認問題是否存在
- **模組隔離**：逐一停用可疑模組（WiFi、BLE、CAN、LCD 等），確認問題是否消失
- **時序隔離**：加入延遲或調整初始化順序，確認是否為 Race Condition

### 2.2 假設→驗證循環

每一輪隔離都遵循：

```
1. 基於證據提出一個具體假設
   例：「BLE 初始化在 WiFi 驅動上電前就啟動，導致 RTL8821 的 HCI 通道未建立」

2. 設計一個能證偽的實驗
   例：「將 BLE 初始化等待時間從 8s 改為 15s，觀察是否仍然失敗」

3. 只改一個變數，觀察結果

4. 記錄結果，不管成功或失敗
```

> [!CAUTION]
> **嚴禁同時修改多個變數！** 在嵌入式環境中，同時改兩個東西而「好了」，你永遠不知道是哪個修復起作用的，下次同類問題又會浪費時間。

### 2.3 常見嵌入式根因類型

| 根因類型 | 典型症狀 | 調查方向 |
|---------|--------|---------|
| **Race Condition** | 間歇性當機、開機成功率不穩 | 加 log 看初始化順序、加 mutex |
| **Stack Overflow** | HardFault、Data Abort | 檢查 Task stack size、避免大型局部變數 |
| **記憶體越界** | 隨機當機、資料損毀 | 檢查 snprintf/memcpy 長度、Ring Buffer 邊界 |
| **ISR 安全性** | 死鎖、周邊失效、MAC 全零 | 確認 ISR 中未使用非 ISR 版 API（參見 embedded-safety-coding skill）|
| **電源/時序** | 開機失敗、高溫、不穩定 | 查電壓、查上電時序、查 DDR timing |
| **CMake 快取** | 改了程式碼但行為沒變 | 刪除 CMakeCache.txt + CMakeFiles 後重編 |
| **Flash 燒錄** | 燒錄後無反應 | 確認 NOR/NAND ID 正確、SPI Tool 驗證 |

---

## Phase 3：修復與驗證

**只有在 Phase 1 & 2 完成、根因明確後，才能進入本階段。**

### 3.1 修復原則

1. **最小修改原則**：只改根因直接相關的程式碼，不順便「改善」其他東西
2. **可逆性**：確保修改可以輕鬆回退 (`git commit` 前後各有乾淨的狀態)
3. **針對根因而非症狀**：如果根因是 Stack Overflow，修復方式是增加 stack size 或減少局部變數，不是加 try-catch 吞掉錯誤

### 3.2 驗證清單

修復後必須依序完成以下驗證：

- [ ] **CMake cache 清除**：刪除 `build\openrtos\GW202601\CMakeCache.txt` 及 `CMakeFiles\`
- [ ] **編譯通過**：完整 rebuild 無 error 無 warning
- [ ] **ROM 備份**：將 ITE_NOR.ROM 複製並重命名為 `GW202601_YYYYMMDD_HHMMSS.ROM`
- [ ] **燒錄驗證**：燒入後確認 UART log 正常啟動
- [ ] **問題重現測試**：用 Phase 1 記錄的重現步驟，確認問題已消失
- [ ] **回歸測試**：確認原本正常的功能沒有被破壞（BLE 連線、WiFi 連線、CAN 通訊等）

### 3.3 記錄到研發日誌

修復完成後，必須在 `DEVELOPMENT_LOG.md` 中記錄：

```markdown
## YYYY-MM-DD：[問題標題]

**症狀**：[描述觀察到的現象]
**根因**：[明確的技術原因]
**修復**：[改了哪些檔案、改了什麼]
**驗證**：[如何確認修復有效]
**教訓**：[未來如何避免同類問題]
```

---

## 反模式清單（嚴禁行為）

| ❌ 反模式 | ✅ 正確做法 |
|----------|-----------|
| 「試試看改這個會不會好」 | 先收集證據，提出假設，設計實驗 |
| 同時改三個地方然後說「好了」 | 一次只改一個變數 |
| 改了不 commit，繼續改下一個 | 每個有意義的修改都要 commit |
| 「加個 sleep 就好了」 | 找出為什麼需要 sleep，解決時序根因 |
| 「把 warning 關掉就不報錯了」 | warning 是線索，追查而非隱藏 |
| 編譯完不清 CMake cache | 每次 rebuild 前確認 cache 已清 |
| 修好了但不更新研發日誌 | 每次修復都要記錄到 DEVELOPMENT_LOG.md |
