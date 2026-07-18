with open(r'C:\SW code\source code\MedFlo_PC_App_20260705\requirements.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(r'C:\SW code\source code\MedFlo_PC_App_20260705\requirements.txt', 'w', encoding='utf-8') as f:
    for line in lines:
        if 'bleak' not in line:
            f.write(line)

