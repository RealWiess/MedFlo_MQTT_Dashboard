---
name: ITE USB Flashing Automation
description: 基於 PcNorWriter GUI 視窗模擬、暫存器探測與 SoC 看門狗軟體重設的一鍵 USB 全自動燒錄規範。
---

# ITE USB 自動化燒錄技能規範 (ITE USB Flashing Automation)

本技能定義了在使用 `PcNorWriter.exe` 與 Python 自動化腳本對 IT9866 進行 USB 燒錄時，AI 助手必須遵循的自動化控制與重啟流程。

---

## 1. 繞過 Windows UIPI 與特權限制
* **規則**：
  1. 使用 Python `ctypes` 調用 Win32 APIs 時，修改 `PcNorWriter` 的路徑欄位必須使用 `SetWindowTextW`，而不是 `SendMessageW(..., WM_SETTEXT)`。
  2. 運行 Python 腳本前，必須設置環境變數 `os.environ["__COMPAT_LAYER"] = "RunAsInvoker"` 以防特權提升不匹配導致系統拒絕跨進程視窗訊息。
* **原因**：Windows 用戶帳戶控制（UAC）會攔截不同權限等級之間的指標傳遞，`SetWindowTextW` 是作業系統內部封裝好的安全機制，可完美繞過 UIPI 限制。

---

## 2. 軟體重啟觸發（REBOOT_TO_BOOTLOADER）
* **規則**：為了免去使用者手動切換開關、拔插 USB 的麻煩，必須實作雙向自動通訊重啟：
  * **PC 端**：自動掃描登錄檔 `HARDWARE\DEVICEMAP\SERIALCOMM` 獲取所有活動 COM 埠，發送 `REBOOT_TO_BOOTLOADER\n` 並等待 2 秒。
  * **Gateway 端**：USB ACM 任務收到指令後，回傳 OK 回應，延時 100ms 確保資料完全發出，接著調用看門狗（Watchdog）硬體重設：
    ```c
    ithWatchDogDisable();
    ithWatchDogSetTimeout(10); // 10ms
    ithWatchDogCtrlEnable(ITH_WD_RESET);
    ithWatchDogEnable();
    while (1);
    ```

---

## 3. 自動一鍵流程（build_and_burn.bat）
* **規則**：自動燒錄批次檔必須嚴格遵循以下順序，並在任一步驟出錯時即刻中斷：
  1. **清除快取**：刪除 `build\openrtos\GW202601\CMakeCache.txt` 檔案以避開絕對路徑陷阱。
  2. **編譯**：執行 CMake 與 Make 生成最新的 `ITE_NOR.ROM`。
  3. **存檔**：拷貝 ROM 並命名為帶時間戳記的格式 `GW202601_YYYYMMDD_HHMMSS.ROM`。
  4. **重啟與燒錄**：執行 `burn_rom.py` 探測 COM 埠發送重啟，隨後啟動 `PcNorWriter` 完成全自動燒錄。
