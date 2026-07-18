with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\app_final.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'text=f"設備 MAC 地址:' in line and 'Gateway' not in line:
        lines[i] = '            text=f"設備 MAC 地址: {mac}\\n資料來源: Gateway",\n'
        # there is probably a newline split, delete the next line if it is just 'Gateway"'
        if 'Gateway"' in lines[i+1] or '資料來源' in lines[i+1]:
            lines[i+1] = ''

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\app_final.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

