# MedFlow 智慧醫療物聯網 - 系統架構與產品規格書

## 1. 專案背景與目的 (Background & Objectives)
在臨床照護中，點滴輸液監控是一項高頻率且高風險的工作。傳統上需仰賴護理人員定時巡房巡視點滴袋剩餘量，當點滴用罄未及時處理時，容易導致血液回流、管路阻塞甚至氣體進入等風險。

**MedFlow（滴護寶 - 包含藍牙偵測端點 POSEIDON 與閘道器 Gateway）** 旨在提供非侵入式的智慧點滴液位監測方案，相容於市面上多數點滴規格，協助醫療院所進行輸液數位化集中管理。

---

## 2. 系統拓撲與佈署圖 (Deployment Topology)

系統通訊分為本地端點廣播與閘道器上雲兩部分：

```
[ 病房點滴架 (端點) ]
  ├─ 點滴架 1 ─ Poseidon 偵測器 (AS3112 BLE Node 1)  ─┐
  ├─ 點滴架 2 ─ Poseidon 偵測器 (AS3112 BLE Node 2)  ─┼─> (BLE 廣播 5s 間隔)
  └─ 點滴架 N ─ Poseidon 偵測器 (AS3112 BLE Node N)  ─┘         │
                                                               │
                                                               v
                                                      [ 護理站中控閘道器 ]
                                                      Poseidon Gateway
                                                      (ITE IT9866 SoC + M8821CS1)
                                                               │
                                                               │ (Wi-Fi / Ethernet - MQTT)
                                                               v
                                                      [ 雲端 / 醫院本地伺服器 ]
                                                      MQTT Broker (mqtt.go6.tw)
                                                               │
                                                               v
                                                      [ 護理站 / 醫護終端 ]
                                                        ├─ Web API Server & DB
                                                        ├─ 電腦瀏覽器 (中控大螢幕)
                                                        └─ 手機 App / 手環 (行動告警)
```

---

## 3. 核心業務情境與數據流 (Use Cases & Data Flows)

### 情境 A：點滴即將用罄告警 (Drip Depletion Alert)
1. **觸發條件**：點滴液位低於偵測端點觸碰板的臨界面，Tontek BS211C-1 觸控 IC 輸出轉為低電位（GPIO18 = Low）。
2. **數據流向**：
   - 偵測端點（AS3112）讀取到 GPIO18 = Low，將 BLE 廣播封包中的 Manufacturer Specific Data 數值設為 `0x00`。
   - 裝置端狀態指示燈（LED，GPIO20）會亮起提示。
   - 本地 Poseidon Gateway（IT9866）掃描到該端點的藍牙 MAC 位址與 `data = 00000000` 狀態。
   - 閘道器將其封裝為 JSON 資料，透過 MQTT 發佈至主題 `DCare/d/<gwid>`。
   - 後端接收到警告訊息，透過 WebSocket 更新護理站中控台，對應床位背景轉為紅黃色並閃爍，提示護理人員前去更換點滴。

---

## 4. 硬體與安全合規考慮 (Safety & Compliance)
* **電氣隔離 (Electrical Isolation)**：設備需符合醫療級安全規範，外殼應採用防潑水（IPX4 以上）與抗化學消毒劑腐蝕的醫療級 ABS 塑料。
* **電池安全性**：採用超低功耗廣播設計，使用符合安全規範的 CR2032 鈕扣電池，排除大容量鋰電池充電過熱或膨脹的安全隱患。
* **無線射頻干擾 (RF Immunity)**：採用低功率 BLE 藍牙廣播，發射功率符合醫院醫療設備電磁相容性 (EMC, IEC 60601-1-2) 規範，避免干擾其他生理監視器或精密醫療儀器。
* **非侵入式設計**：感測器模組採用電容觸碰感應，夾在點滴管路或滴斗外部，絕不接觸藥液，確保零污染與無菌性。

---

## 5. 詳細技術規格
完整的硬體接腳配置、藍牙廣播 PDU 位元組定義與 MQTT 伺服器 JSON 規格，請參閱：
* [Poseidon 系統設計與規格說明書](file:///c:/Users/JOHN_WIESS/.gemini/antigravity-ide/scratch/MedFlow/Docs/Poseidon_Design_Specs.md)
* [閘道器連線與 MQTT 通訊規格](file:///c:/Users/JOHN_WIESS/.gemini/antigravity-ide/scratch/MedFlow/Docs/Gateway_Connection_Info.md)
* [閘道器功能設計概念書](file:///c:/Users/JOHN_WIESS/.gemini/antigravity-ide/scratch/MedFlow/Docs/Gateway_Functional_Specs.md)
* [尿袋監測器設計規格與操作 SOP](file:///c:/Users/JOHN_WIESS/.gemini/antigravity-ide/scratch/MedFlow/Docs/Urine_Bag_Monitor_Specs.md)
