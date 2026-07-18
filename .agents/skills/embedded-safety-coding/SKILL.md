---
name: Embedded Safety Coding Rules (C/RTOS)
description: 針對 FreeRTOS/OpenRTOS 等嵌入式環境的安全編碼與中斷防護規範，防止死鎖與記憶體越界。
---

# 嵌入式環境安全編碼規範 (Embedded Safety Coding Rules)

本技能定義了在 FreeRTOS/OpenRTOS 環境下進行 C 語言開發時，AI 助手必須遵循的記憶體安全與中斷安全規範。

---

## 1. 嚴禁全域覆蓋 C 標準庫函數（防範連鎖影響）
* **規則**：絕對不允許在全域標頭檔（如 `ctrlboard.h`）中定義 `#define printf app_printf` 或覆蓋其他標準庫函數。
* **原因**：這會導致底層硬體驅動（如 SDIO、WiFi）或第三方庫（如 LwIP、libcurl）在包含該頭文件時，其內部的 printf 被強行替換，從而引入未知的執行緒鎖、臨界區和記憶體讀寫。
* **正確做法**：將日誌重導向限制在特定的應用層原始碼檔案（如 `peripheral.c`、`bt_main.c`）中，在檔案頂部局部定義重新導向宏。

---

## 2. 臨界區與中斷安全規範（防止晶片掛起與全零 MAC）
* **規則**：在寫入共享環形緩衝區（Ring Buffer）或全域狀態時，若使用 FreeRTOS 臨界區 `portENTER_CRITICAL()` / `portEXIT_CRITICAL()`：
  1. **禁止在中斷上下文（ISR）中使用非 ISR 版本**。
  2. 若函數可能在中斷中被間接調用，必須使用 `xPortIsInsideInterrupt()` 進行執行上下文檢測：
     ```c
     if (xPortIsInsideInterrupt()) {
         // 中斷中：直接降級串口輸出，禁止進入臨界區或阻斷
         vprintf(format, args); 
         return;
     }
     ```
* **原因**：在中斷上下文調用非 ISR 臨界區會破壞 ARM Cortex 處理器的中斷巢狀暫存器，導致 SDIO 接收中斷失效，無法辨識 WiFi/BT 晶片，造成 MAC 地址讀出為 `00:00:00:00:00:00`，使整個網路與藍牙功能癱瘓。

---

## 3. 記憶體邊界防禦與 `vsnprintf` 的 C99 特性
* **規則**：使用 `vsnprintf` 或 `snprintf` 格式化日誌至固定長度陣列（例如 `char buf[256]`）後，向環形緩衝區推送長度時，**必須進行長度安全檢查與截斷**：
  ```c
  char buf[256];
  int len = vsnprintf(buf, sizeof(buf), format, args);
  if (len > 0) {
      if (len >= (int)sizeof(buf)) {
          len = (int)sizeof(buf) - 1; // 強制截斷，防止 Stack Overread
      }
      log_ring_buffer_push(buf, len);
  }
  ```
* **原因**：根據 C99 標準，若格式化後的內容大於緩衝區長度，`vsnprintf` 會返回**「理論上需要的總長度」**（例如 300），若直接以該長度進行記憶體複製，會從堆疊（Stack）越界讀取記憶體，造成 Hardware Data Abort 當機重置。
