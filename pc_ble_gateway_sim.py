"""
PC Real Bluetooth Gateway Simulator for MedFlow MQTT Dashboard
---------------------------------------------------------------
STRICT FILTER: ONLY accepts physical MedFlow BT devices matching MAC F44EFD... or A100...
or broadcast local_name starting with MEDFLO. Reject all other BLE devices!
"""

import sys
import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
import paho.mqtt.client as mqtt
from bleak import BleakScanner

# Force UTF-8 encoding for Windows console output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# MQTT Configuration
MQTT_HOST = "mqtt.go6.tw"
MQTT_PORT = 1883
MQTT_USER = "DCareW"
MQTT_PASS = "4rfghy6"
MQTT_TOPIC = "DCare/d/pc_sim_gw"
GW_ID = "PC_SIM_GATEWAY_01"

# In-memory dictionary to track scanned MedFlow BT devices
scanned_devices = {}
device_counters = {}

def get_iso_time():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat()

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[MQTT] Connected to MQTT Broker ({MQTT_HOST}:{MQTT_PORT}) as Writer ({MQTT_USER})")
    else:
        print(f"[MQTT] Connection failed with code: {rc}")

def parse_medflow_data(device, adv_data):
    mac = device.address.replace(":", "").replace("-", "").upper()
    actual_name = adv_data.local_name or device.name or ""
    rssi = adv_data.rssi if adv_data.rssi is not None else -100
    
    # STRICT FILTER: Physical MAC MUST start with F44EFD or A100, OR actual_name starts with MEDFLO
    is_real_medflow = (
        mac.startswith("F44EFD") or 
        mac.startswith("A100") or 
        actual_name.upper().startswith("MEDFLO")
    )
    
    # REJECT all other non-MedFlow devices!
    if not is_real_medflow:
        return False, None

    display_name = actual_name if actual_name else f"MEDFLO-{mac}"
    
    # Construct raw data hex string
    raw_hex = ""
    stat = 0 # Default 0
    bat_low = False
    
    if adv_data.manufacturer_data:
        for mfg_id, data_bytes in adv_data.manufacturer_data.items():
            hex_str = data_bytes.hex().upper()
            raw_hex += f"{mfg_id:04X}{hex_str}"
            if len(data_bytes) >= 2:
                last_byte = data_bytes[-1]
                stat = 0 if (last_byte & 0x01) == 0 else 1
                bat_low = ((last_byte & 0x02) != 0)
    
    if not raw_hex:
        name_hex = display_name.encode("utf-8").hex().upper()
        raw_hex = f"0201061409{name_hex}05FFFFFF0000"

    # Maintain rolling counter
    device_counters[mac] = device_counters.get(mac, 0) + 1
    
    return True, {
        "time": get_iso_time(),
        "gwid": GW_ID,
        "rssi": rssi,
        "stat": stat,
        "cnt": device_counters[mac],
        "mac": mac,
        "name": display_name,
        "data": raw_hex,
        "batteryLow": bat_low,
        "lastSeen": time.time()
    }

def detection_callback(device, advertisement_data):
    is_medflow, parsed_info = parse_medflow_data(device, advertisement_data)
    if is_medflow and parsed_info:
        mac = parsed_info["mac"]
        scanned_devices[mac] = parsed_info

async def ble_scan_loop(mqtt_client):
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    print("[BLE Scanner] Started PC Real Bluetooth BLE Scanner (Strict Filter: F44EFD / A100 / MEDFLO ONLY)...")
    
    try:
        while True:
            await asyncio.sleep(3.0)
            now = time.time()
            
            # Filter active MedFlow devices seen in the last 15 seconds
            active_list = []
            for mac, dev in list(scanned_devices.items()):
                if (now - dev["lastSeen"]) <= 15:
                    payload_dev = {
                        "time": dev["time"],
                        "gwid": dev["gwid"],
                        "rssi": dev["rssi"],
                        "stat": dev["stat"],
                        "cnt": dev["cnt"],
                        "mac": dev["mac"],
                        "data": dev["data"]
                    }
                    active_list.append(payload_dev)

            if len(active_list) > 0:
                json_str = json.dumps(active_list, indent=2)
                mqtt_client.publish(MQTT_TOPIC, json_str, qos=0)
                print(f"[PC Gateway Engine] Scanned {len(active_list)} STRICT MedFlow BT devices! Published JSON to {MQTT_TOPIC}")
                for d in active_list:
                    print(f"   └─ 📶 MAC: {d['mac']} | RSSI: {d['rssi']} dBm | Stat: {d['stat']} | Cnt: {d['cnt']}")
            else:
                print("[PC Gateway Engine] Scanning nearby Bluetooth... (0 MedFlow F44EFD devices detected in range)")
                
    finally:
        await scanner.stop()

def main():
    print("=========================================================")
    print(" MedFlow PC Real Bluetooth Gateway Simulator Engine")
    print(" STRICT FILTER MODE: ONLY F44EFD / A100 / MEDFLO BT Devices")
    print("=========================================================")
    
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.on_connect = on_connect
    
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"[MQTT Error] Failed to connect: {e}")
        return

    try:
        asyncio.run(ble_scan_loop(mqtt_client))
    except KeyboardInterrupt:
        print("\n[PC Gateway Engine] Stopped by user.")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
