import re

with open(r'C:\SW code\source code\MedFlo_PC_App_20260705\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove bleak import
content = re.sub(r'# 嘗試導入 bleak.*?BLEAK_AVAILABLE = False\n', '', content, flags=re.DOTALL)

# 2. Remove BLE vars in __init__
content = re.sub(r'        # 本機藍牙狀態變數.*?self\.ble_logs_lock = threading\.Lock\(\)\n', '', content, flags=re.DOTALL)

# 3. Remove BLE stop in on_closing
content = re.sub(r'        # 2\. 停止本機藍牙掃描.*?except: pass\n', '', content, flags=re.DOTALL)

# 4. Remove BLE methods
content = re.sub(r'    # ==================== 本機藍牙掃描 \(bleak\) 實作 ====================.*?    # ==================== 更新左右兩個 Table 與進行 MAC 比對 ====================', '    # ==================== 更新 Table ====================', content, flags=re.DOTALL)

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\refactor1.py', 'w', encoding='utf-8') as f:
    f.write(content)

