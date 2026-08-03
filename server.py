import argparse
import os
import sys
import socket
import json
import time
import threading
import asyncio
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

def safe_print(msg):
    try:
        sys.stdout.buffer.write((str(msg) + '\n').encode('utf-8', errors='ignore'))
        sys.stdout.buffer.flush()
    except Exception:
        try:
            print(str(msg).encode('ascii', errors='ignore').decode('ascii'))
        except Exception:
            pass

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

PORT = 8080

# Cache for PC local BLE devices scanned by BleakScanner
local_ble_cache = {}
ble_scan_enabled = True  # Toggled by frontend via /api/ble_control

def start_ble_scanner_background():
    """Start background BleakScanner thread to scan local BLE devices via PC Bluetooth adapter"""
    def _run_scanner():
        try:
            from bleak import BleakScanner
        except ImportError:
            safe_print("[BLE Server Engine] Warning: bleak package not found. Local Bluetooth scanning disabled.")
            return

        safe_print("[BLE Server Engine] Starting local PC Bluetooth hardware scanning engine (Bleak)...")

        async def _async_scan():
            def detection_callback(device, advertisement_data):
                global local_ble_cache
                try:
                    mac = device.address.replace(':', '').replace('-', '').upper()
                    name_raw = advertisement_data.local_name or device.name or ""
                    name = name_raw.upper()

                    mfg_dict = advertisement_data.manufacturer_data or {}
                    has_mfg_ffff = 0xFFFF in mfg_dict

                    # Strict: MFL-/MFS- + 12 hex MAC chars (e.g. MFL-A1B2C3D4E5F6)
                    is_mfl = len(name_raw) == 16 and name.startswith("MFL-") and all(c in "0123456789ABCDEF" for c in name[4:])
                    is_mfs = len(name_raw) == 16 and name.startswith("MFS-") and all(c in "0123456789ABCDEF" for c in name[4:])
                    is_gateway = name.startswith("NMGW2601-") or name.startswith("NMGW-") or name.startswith("GW-")

                    if not is_mfl and not is_mfs and not is_gateway:
                        return

                    mfg_hex = ""
                    if has_mfg_ffff:
                        payload = mfg_dict[0xFFFF]
                        mfg_hex = " ".join(f"{b:02X}" for b in payload)
                    elif mfg_dict:
                        for cid, val in mfg_dict.items():
                            mfg_hex += f"{cid:04X} " + " ".join(f"{b:02X}" for b in val)

                    gpio18_stat = "HIGH"  # Default: bag empty (0x01)
                    battery_low = False
                    sensor_alert = False
                    wake_counter = None

                    # MFL- / MFS- BT v4 Manufacturer Data (0xFFFF) parsing:
                    # Payload: Byte[0]=GPIO18, Byte[1]=flags, Byte[2-3]=wake_cycle uint16 LE
                    if has_mfg_ffff and (is_mfl or is_mfs):
                        payload = mfg_dict[0xFFFF]
                        # Auto-detect and skip Company ID prefix if included
                        offset = 2 if (len(payload) >= 6 and payload[0] == 0xFF and payload[1] == 0xFF) else 0
                        if len(payload) >= offset + 4:
                            gpio18_stat = "HIGH" if payload[offset] == 1 else "LOW"
                            flags = payload[offset + 1]
                            battery_low = bool(flags & 0x01)
                            sensor_alert = bool(flags & 0x02)
                            wake_counter = payload[offset + 2] | (payload[offset + 3] << 8)
                        elif len(payload) >= offset + 2:
                            gpio18_stat = "HIGH" if payload[offset] == 1 else "LOW"
                            flags = payload[offset + 1]
                            battery_low = bool(flags & 0x01)
                            sensor_alert = bool(flags & 0x02)
                        elif len(payload) >= offset + 1:
                            gpio18_stat = "HIGH" if payload[offset] == 1 else "LOW"

                    prev_dev = local_ble_cache.get(mac, {})
                    new_rssi = advertisement_data.rssi
                    rssi_val = new_rssi if (new_rssi is not None and -110 < new_rssi <= 0) else prev_dev.get("rssi", -70)

                    local_ble_cache[mac] = {
                        "mac": mac,
                        "name": name_raw,
                        "rssi": rssi_val,
                        "stat": 1 if gpio18_stat == "HIGH" else 0,
                        "gpio18": gpio18_stat,
                        "wakeCycleCounter": wake_counter if wake_counter is not None else prev_dev.get("wakeCycleCounter", None),
                        "mfg_hex": mfg_hex or prev_dev.get("mfg_hex", ""),
                        "raw_hex": mfg_hex or prev_dev.get("raw_hex", ""),
                        "batteryLow": battery_low or prev_dev.get("batteryLow", False),
                        "sensorAlert": sensor_alert or prev_dev.get("sensorAlert", False),
                        "isGateway": is_gateway,
                        "lastSeen": time.time()
                    }
                    safe_print(f"[BLE Server] Detected: {mac} | {name_raw} | RSSI={rssi_val}")
                except Exception:
                    pass

            try:
                while True:
                    if not ble_scan_enabled:
                        await asyncio.sleep(0.5)
                        continue
                    try:
                        async with BleakScanner() as scanner:
                            safe_print("[BLE Server Engine] Scanner started, listening for BLE advertisements...")
                            while ble_scan_enabled:
                                try:
                                    device, advertisement_data = await asyncio.wait_for(
                                        scanner.advertisement_data().__anext__(), timeout=1.0
                                    )
                                    detection_callback(device, advertisement_data)
                                except asyncio.TimeoutError:
                                    continue  # Check ble_scan_enabled flag
                            safe_print("[BLE Server Engine] Scanner stopped (page switch)")
                    except Exception as inner_ex:
                        safe_print(f"[BLE Server Engine] BleakScanner loop exception: {inner_ex}")
                        await asyncio.sleep(2.0)
            except Exception as ex:
                safe_print(f"[BLE Server Engine] Outer scan error: {ex}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_async_scan())
        except Exception as e:
            print(f"[BLE Server Engine] Event loop ended: {e}")

    t = threading.Thread(target=_run_scanner, daemon=True)
    t.start()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
class ServerSerialManager:
    """Serial port manager in server backend"""
    def __init__(self):
        self.port = None
        self.baudrate = 115200
        self.serial_port = None
        self.is_connected = False
        self.running = False
        self.receive_thread = None
        self.status_thread = None
        self.total_bytes = 0
        self.total_lines = 0
        self.last_receive_time = None
        self._bytes_window = 0
        self.recent_lines = []
        self.status_data = {
            "wifi_connected": False,
            "ssid": "-",
            "ip": "-",
            "ble_count": "-",
            "gw_time": "-"
        }

    def scan_ports(self):
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            return [p.device for p in ports]
        except Exception as e:
            print(f"[Serial Manager] Scan ports error: {e}")
            return []

    def connect(self, port, baudrate=115200):
        # Always clean up any existing connection first
        self.disconnect()

        import serial
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1
                )
                self.port = port
                self.baudrate = baudrate
                self.is_connected = True
                self.running = True
                self.total_bytes = 0
                self.total_lines = 0
                self.status_data = {
                    "wifi_connected": False,
                    "ssid": "-",
                    "ip": "-",
                    "mac": "-",
                    "rssi": "-",
                    "ble_count": "-",
                    "gw_time": "-",
                    "fw_ver": "-",
                    "target_url": "-"
                }
                self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
                self.receive_thread.start()

                # Background status polling thread like original app.py
                self.status_thread = threading.Thread(target=self._status_polling_loop, daemon=True)
                self.status_thread.start()

                # Immediate time sync & status request
                sync_time = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.send_command(f"SET_TIME:{sync_time}")
                self.send_command("GET_STATUS")
                self.send_command("$STATUS")
                return True, f"成功連線至 {port} @ {baudrate} bps"
            except Exception as e:
                self.is_connected = False
                if attempt < max_retries - 1:
                    # Clean up and wait 0.3s for Windows OS handle release
                    self.disconnect()
                    time.sleep(0.3)
                else:
                    err_msg = str(e)
                    if "PermissionError" in err_msg or "存取被拒" in err_msg:
                        err_msg = f"{port} 埠口已被 Windows 系統或其他軟體 (如 Putty/串口終端) 佔用。請先關閉其他開啟 {port} 的程式後再試。"
                    return False, f"連線失敗: {err_msg}"

    def _status_polling_loop(self):
        """Periodically request GET_STATUS & GET_LOGS like original app.py"""
        while self.running and self.is_connected:
            try:
                self.send_command("GET_STATUS")
                time.sleep(1.0)
                self.send_command("GET_LOGS")
                time.sleep(1.0)
            except Exception:
                break

    def disconnect(self):
        self.running = False
        self.is_connected = False
        if self.serial_port:
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None
        self.port = None
        time.sleep(0.2)

    def send_command(self, cmd_str):
        if self.is_connected and self.serial_port:
            try:
                if cmd_str.startswith("SET_WIFI:"):
                    parts = cmd_str[9:].split(",")
                    if parts and parts[0].strip():
                        new_ssid = parts[0].strip()
                        self.status_data["ssid"] = new_ssid
                        self.status_data["uart_real_ssid"] = new_ssid
                elif cmd_str.startswith("SET_WIFI2:"):
                    parts = cmd_str[10:].split(",")
                    if parts and parts[0].strip():
                        new_ssid = parts[0].strip()
                        self.status_data["ssid"] = new_ssid
                        self.status_data["uart_real_ssid"] = new_ssid

                self.serial_port.write((cmd_str + "\n").encode('utf-8'))
                return True
            except Exception as e:
                print(f"[Serial Manager] Send command error: {e}")
                return False
        return False

    def _receive_loop(self):
        buffer = ""
        while self.running and self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    self.total_bytes += len(data)
                    self._bytes_window += len(data)
                    self.last_receive_time = time.time()
                    buffer += data

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self.total_lines += 1
                            self.recent_lines.append(line)
                            if len(self.recent_lines) > 200:
                                self.recent_lines.pop(0)
                            self._parse_serial_line(line)
                else:
                    time.sleep(0.01)
            except Exception as e:
                import traceback
                print(f"[Serial Manager] Receive loop error: {e}")
                traceback.print_exc()
                self.is_connected = False
                self.running = False
                break

    def _parse_serial_line(self, line):
        try:
            # Match MedFlo_PC_App_20260707 reference implementation:
            # Parse JSON STATUS packets directly from USB serial stream
            start = line.find('{')
            end = line.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = line[start:end+1]
                data = json.loads(json_str)
                
                cmd = data.get("cmd", "")
                if cmd == "STATUS" or "wifi_ssid" in data or "ip" in data:
                    is_conn = bool(data.get("wifi_connected", False))
                    ip_val = str(data.get("ip", ""))
                    if ip_val and ip_val not in ("0.0.0.0", "-"):
                        is_conn = True

                    self.status_data["wifi_connected"] = is_conn
                    self.status_data["ssid"] = data.get("wifi_ssid", data.get("ssid", "-"))
                    self.status_data["ip"] = ip_val if ip_val else "-"
                    self.status_data["mac"] = data.get("mac", self.status_data.get("mac", "-"))
                    
                    gw_time = data.get("time")
                    if gw_time:
                        self.status_data["gw_time"] = gw_time
                        if (gw_time.startswith("2012") or gw_time.startswith("1970")) and self.is_connected:
                            now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
                            self.send_command(f"SET_TIME:{now_str}")

                    if "target_url" in data: self.status_data["target_url"] = data["target_url"]
                    if "fw_ver" in data: self.status_data["fw_ver"] = data["fw_ver"]
                    if "log_count" in data: self.status_data["ble_count"] = data["log_count"]
                    if "buf_usage" in data: self.status_data["buf_usage"] = data["buf_usage"]
                    if "ble_disc_passed" in data: self.status_data["ble_disc_passed"] = data["ble_disc_passed"]
                    if "ble_disc_total" in data: self.status_data["ble_disc_total"] = data["ble_disc_total"]

        except Exception:
            pass

        except Exception:
            pass

server_serial_mgr = ServerSerialManager()

class MedFlowHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/serial_ports'):
            self.handle_get_serial_ports()
            return
        if self.path.startswith('/api/serial_status'):
            self.handle_get_serial_status()
            return
        if self.path.startswith('/api/launch_pc_app'):
            self.handle_launch_pc_app()
            return
        if self.path.startswith('/api/pc_app_info'):
            self.handle_get_pc_app_info()
            return
        if self.path.startswith('/api/ble_devices'):
            self.handle_get_ble_devices()
            return
        if self.path.startswith('/api/ble_control'):
            self.handle_ble_control()
            return
        if self.path.startswith('/api/ble_status'):
            self.handle_get_ble_status()
            return
        if self.path == '/' or self.path == '':
            self.path = '/mqtt_dashboard.html'
        return super().do_GET()
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/serial_connect':
            self.handle_post_serial_connect()
            return
        if self.path == '/api/serial_disconnect':
            self.handle_post_serial_disconnect()
            return
        if self.path == '/api/serial_send':
            self.handle_post_serial_send()
            return
        if self.path == '/api/launch_pc_app':
            self.handle_launch_pc_app()
            return
        self.send_error(404, "Endpoint not found")

    def handle_get_serial_ports(self):
        ports = server_serial_mgr.scan_ports()
        body = json.dumps({"ports": ports}, ensure_ascii=False).encode('utf-8')
        self._send_json_response(200, body)

    def handle_get_serial_status(self):
        res = {
            "is_connected": server_serial_mgr.is_connected,
            "port": server_serial_mgr.port,
            "baudrate": server_serial_mgr.baudrate,
            "status": server_serial_mgr.status_data,
            "bytes": server_serial_mgr.total_bytes,
            "lines": server_serial_mgr.total_lines,
            "recent_lines": list(server_serial_mgr.recent_lines)
        }
        body = json.dumps(res, ensure_ascii=False).encode('utf-8')
        self._send_json_response(200, body)

    def handle_post_serial_connect(self):
        length = int(self.headers.get('Content-Length', 0))
        data_bytes = self.rfile.read(length) if length > 0 else b'{}'
        try:
            req = json.loads(data_bytes.decode('utf-8'))
            port = req.get("port", "COM5")
            baudrate = int(req.get("baudrate", 115200))
            ok, msg = server_serial_mgr.connect(port, baudrate)
            code = 200 if ok else 400
            resp = {"success": ok, "message": msg, "port": port}
        except Exception as e:
            code = 500
            resp = {"success": False, "message": str(e)}
        self._send_json_response(code, json.dumps(resp, ensure_ascii=False).encode('utf-8'))

    def handle_post_serial_disconnect(self):
        server_serial_mgr.disconnect()
        self._send_json_response(200, json.dumps({"success": True, "message": "已成功斷開串口連線"}, ensure_ascii=False).encode('utf-8'))

    def handle_post_serial_send(self):
        length = int(self.headers.get('Content-Length', 0))
        data_bytes = self.rfile.read(length) if length > 0 else b'{}'
        try:
            req = json.loads(data_bytes.decode('utf-8'))
            command = req.get("command", "")
            ok = server_serial_mgr.send_command(command)
            code = 200 if ok else 400
            resp = {"success": ok, "command": command}
        except Exception as e:
            code = 500
            resp = {"success": False, "message": str(e)}
        self._send_json_response(code, json.dumps(resp, ensure_ascii=False).encode('utf-8'))

    def _send_json_response(self, code, body):
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, BrokenPipeError, ConnectionResetError, OSError):
            pass

    def handle_ble_control(self):
        global ble_scan_enabled, local_ble_cache
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)
        enable = query.get('enable', [''])[0]
        if enable == '1':
            ble_scan_enabled = True
            safe_print("[BLE Server API] BLE scan ENABLED by frontend")
        elif enable == '0':
            ble_scan_enabled = False
            local_ble_cache.clear()
            safe_print("[BLE Server API] BLE scan DISABLED by frontend, cache cleared")
        resp = {"ble_scan_enabled": ble_scan_enabled}
        body = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self._send_json_response(200, body)

    def handle_get_ble_devices(self):
        global local_ble_cache
        now = time.time()
        active_list = []
        for mac, dev in list(local_ble_cache.items()):
            if now - dev.get("lastSeen", 0) <= 300:
                active_list.append(dev)
        
        safe_print(f"[BLE Server API] /api/ble_devices returning {len(active_list)} active devices (total cache: {len(local_ble_cache)})")
        body = json.dumps(active_list, ensure_ascii=False).encode('utf-8')
        self._send_json_response(200, body)

    def handle_get_ble_status(self):
        now = time.time()
        active_cnt = sum(1 for dev in local_ble_cache.values() if now - dev.get("lastSeen", 0) <= 300)
        resp = {
            "status": "ok",
            "bt_enabled": True,
            "scanning": True,
            "engine": "Bleak Python Local PC Adapter",
            "active_devices_count": active_cnt,
            "total_cached_count": len(local_ble_cache)
        }
        body = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self._send_json_response(200, body)

    def find_pc_app_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)
        candidates = [
            os.path.join(parent_dir, 'MedFlo_PC_App_20260707'), # C:\SW code\source code\MedFlo_PC_App_20260707
            os.path.join(base_dir, 'MedFlo_PC_App_20260707'),   # C:\SW code\source code\MefFlo_MQTT_Dashbaord\MedFlo_PC_App_20260707
            r"C:\SW code\source code\MedFlo_PC_App_20260707",
            r"C:\SW code\source code\MefFlo_MQTT_Dashbaord\MedFlo_PC_App_20260707"
        ]
        for cand in candidates:
            bat = os.path.join(cand, 'run.bat')
            if os.path.exists(bat):
                return cand, bat
        return candidates[0], os.path.join(candidates[0], 'run.bat')

    def handle_get_pc_app_info(self):
        cand_dir, cand_bat = self.find_pc_app_path()
        exists = os.path.exists(cand_bat)
        resp = {
            "exists": exists,
            "app_dir": cand_dir,
            "bat_path": cand_bat
        }
        body = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_launch_pc_app(self):
        import subprocess
        app_dir, bat_path = self.find_pc_app_path()
        
        try:
            if os.path.exists(bat_path):
                subprocess.Popen(['cmd.exe', '/c', 'start', 'run.bat'], cwd=app_dir, shell=True)
                resp = {
                    "status": "ok",
                    "message": f"已成功從路徑 [{app_dir}] 調用系統啟動 MedFlo PC App (run.bat)！",
                    "app_dir": app_dir,
                    "bat_path": bat_path
                }
                code = 200
            else:
                resp = {"status": "error", "message": f"找不到啟動檔: {bat_path}"}
                code = 404
        except Exception as e:
            resp = {"status": "error", "message": f"啟動失敗: {str(e)}"}
            code = 500

        body = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def main(enable_ble=True, auto_open_browser=True):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if enable_ble:
        start_ble_scanner_background()
        ble_status = "BLE Local Scan: ENABLED"
    else:
        ble_status = "BLE Local Scan: DISABLED (--no-ble)"
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{PORT}/mqtt_dashboard.html"

    safe_print("=" * 65)
    safe_print("MedFlow Bluetooth Dynamic Dashboard Server Started")
    safe_print("=" * 65)
    safe_print(f"   {ble_status}")
    safe_print(f"Local PC: http://localhost:{PORT}")
    safe_print(f"Mobile / Network URL: {url}")
    safe_print("=" * 65)

    if auto_open_browser:
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass

    HTTPServer.allow_reuse_address = True
    httpd = HTTPServer(('0.0.0.0', PORT), MedFlowHTTPHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止。")
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MedFlow MQTT Dashboard Server')
    parser.add_argument('--no-ble', action='store_true', help='停用本機 BLE 藍牙背景掃描（避免與 MedFlo_scanner 等桌面工具搶佔藍牙適配器）')
    parser.add_argument('--no-browser', action='store_true', help='啟動後不自動打開瀏覽器頁面（適用於由批次檔進行外部輪詢與開啟的情況）')
    args = parser.parse_args()
    main(enable_ble=not args.no_ble, auto_open_browser=not args.no_browser)
