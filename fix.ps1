with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\app_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
content = re.sub(r'text=f"設備 MAC 地址: \{mac\}\n資料來源: Gateway",', 'text=f"設備 MAC 地址: {mac}\\n資料來源: Gateway",', content)

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\app_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

