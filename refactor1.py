import json
import csv
import os
import time
import threading
import asyncio
from collections import OrderedDict
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import customtkinter as ctk
import serial
import serial.tools.list_ports


# 設定外觀模式
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SerialManager:
    """串口管理器，處理串口連線、發送與接收"""
    def __init__(self):
        self.serial_port = None
        self.is_connected = False
        self.receive_callback = None
        self.running = False
        self.receive_thread = None
        self.error_callback = None
        # USB 資料統計
        self.total_bytes_received = 0
        self.total_lines_received = 0
        self.last_receive_time = None
        self._bytes_in_window = 0  # 用於計算每秒速率

    def scan_ports(self):
        """掃描所有可用的COM Port"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port, baudrate=115200):
        """連接到指定的COM Port"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            self.is_connected = True
            self.running = True
            # 啟動接收執行緒
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            success = True
        except Exception as e:
            print(f"連接失敗: {e}")
            self.is_connected = False
            success = False
        return success

    def disconnect(self):
        """斷開串口連線"""
        self.running = False
        self.is_connected = False
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
        # 重置計數
        self.total_bytes_received = 0
        self.total_lines_received = 0
        self.last_receive_time = None
        self._bytes_in_window = 0

    def send_command(self, command):
        """發送指令"""
        if self.is_connected and self.serial_port:
            try:
                self.serial_port.write((command + "\n").encode())
                return True
            except Exception as e:
                print(f"發送失敗: {e}")
                return False
        return False

    def _receive_loop(self):
        """接收資料的執行緒"""
        buffer = ""
        while self.running:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting).decode("utf-8", errors="ignore")
                    # 統計原始位元組數
                    self.total_bytes_received += len(data)
                    self._bytes_in_window += len(data)
                    self.last_receive_time = time.time()
                    buffer += data
                    # 處理完整行
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            self.total_lines_received += 1
                            if self.receive_callback:
                                self.receive_callback(line)
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"接收錯誤: {e}")
                self.running = False
                self.is_connected = False
                if self.error_callback:
                    self.error_callback(str(e))
                break

    def get_stats(self):
        """取得目前 USB 接收統計資料"""
        now = time.time()
        last_t = self.last_receive_time
        idle_sec = round(now - last_t, 1) if last_t else None
        # 傳回計數後清空窗口計數器
        bps = self._bytes_in_window
        self._bytes_in_window = 0
        return {
            "total_bytes": self.total_bytes_received,
            "total_lines": self.total_lines_received,
            "idle_sec": idle_sec,
            "bps_window": bps,
        }

class App(ctk.CTk):
    """主應用程式"""
    def __init__(self):
        super().__init__()

        # 設定視窗
        self.title("MedFlo GW202601 藍牙接收與本機比對工具")
        self.geometry("1400x800")
        self.minsize(1000, 700)

        # 初始化管理器
        self.serial_manager = SerialManager()
        self.serial_manager.receive_callback = self.handle_received_data
        self.serial_manager.error_callback = self.handle_serial_error


        # 資料儲存
        self.status_data = {}
        # Gateway 設備登記簿（與 BLE 圖表相同結構）
        self.gw_device_registry = OrderedDict()
        self.logs_data = []   # 保留撺容 CSV 匯出用
        self.logs_lock = threading.Lock()

        # 計時器控制
        self.status_timer_running = False
        self.logs_timer_running = False
        self.status_timer_id = None
        self.logs_timer_id = None

        # 掃描時間記錄
        self.gateway_connect_time = None
        self.ble_scan_start_time = None
        self.info_bar_timer_id = None

        # 關閉中旗標（防止關閉進行時仍觸發 after 回呼）
        self._is_closing = False

        # 建立UI
        self.setup_ui()

        # 綁定關閉事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """安全關閉應用程式：先停止所有執行緒與 after 定時器，再釋放窗口"""
        if self.serial_manager.is_connected:
            if not messagebox.askokcancel("確認", "設備仍處於連線通訊中，確定要結束程式嗎？"):
                return

        self._is_closing = True

        # 1. 停止所有 after 定時器
        try: self.stop_status_timer()
        except: pass
        try: self.stop_logs_timer()
        except: pass
        try: self.stop_usb_monitor()
        except: pass


        # 3. 斷開串口
        try:
            self.serial_manager.disconnect()
        except: pass

        # 4. 稍待一下讓執行緒有機會退出，再釋放窗口
        self.after(200, self._safe_destroy)

    def _safe_destroy(self):
        """200ms 延遲後安全釋放窗口"""
        try:
            self.destroy()
        except Exception:
            pass

    def setup_ui(self):
        """建立介面元件"""
        # 主要佈局 - 左右兩欄
        self.grid_columnconfigure(0, weight=0, minsize=300)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左側面板
        self.left_frame = ctk.CTkFrame(self, corner_radius=10)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_frame.grid_rowconfigure(3, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # 右側面板
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)
        self.right_frame.grid_rowconfigure(3, weight=1)  # row 3 is tables_container
        self.right_frame.grid_columnconfigure(0, weight=1)

        # ---- 左側面板內容 ----
        # 連線管理區
        self.connection_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.connection_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        self.connection_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.connection_frame, text="COM Port:", font=("Arial", 14)).grid(row=0, column=0, padx=(0,5), pady=5)

        self.port_combo = ctk.CTkComboBox(self.connection_frame, values=["Scanning..."], width=120)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.scan_btn = ctk.CTkButton(self.connection_frame, text="掃描", command=self.scan_ports, width=60)
        self.scan_btn.grid(row=0, column=2, padx=5, pady=5)

        self.connect_btn = ctk.CTkButton(self.connection_frame, text="連接", command=self.toggle_connection, width=70)
        self.connect_btn.grid(row=0, column=3, padx=5, pady=5)

        # 狀態卡片
        self.status_frame = ctk.CTkFrame(self.left_frame, corner_radius=8)
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.status_frame, text="設備狀態", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=(10,5))

        self.status_labels = {}
        status_fields = [
            ("wifi_connected", "WiFi連線"),
            ("ssid", "SSID"),
            ("ip", "IP位址"),
            ("log_count", "日誌數量"),
            ("time_sync", "Gateway時間")
        ]
        for i, (key, label) in enumerate(status_fields):
            frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
            frame.grid(row=i+1, column=0, sticky="ew", padx=10, pady=2)
            frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(frame, text=f"{label}:", font=("Arial", 12)).grid(row=0, column=0, sticky="w")
            self.status_labels[key] = ctk.CTkLabel(frame, text="-", font=("Arial", 12, "bold"))
            self.status_labels[key].grid(row=0, column=1, sticky="w")

        # USB 接收活耶監視區
        self.usb_frame = ctk.CTkFrame(self.left_frame, corner_radius=8, fg_color="#1a2030")
        self.usb_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,5))
        self.usb_frame.grid_columnconfigure(0, weight=1)

        usb_title_row = ctk.CTkFrame(self.usb_frame, fg_color="transparent")
        usb_title_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,2))
        usb_title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(usb_title_row, text="USB 資料接收監視", font=("Arial", 14, "bold"), text_color="#3a9cd6").pack(side="left")
        self.usb_indicator = ctk.CTkLabel(usb_title_row, text="● 未連線", font=("Arial", 12, "bold"), text_color="#666666")
        self.usb_indicator.pack(side="right")

        # 各統計數據欄位
        usb_stats_fields = [
            ("usb_bytes",   "接收 Bytes"),
            ("usb_lines",   "接收行數"),
            ("usb_bps",     "速率 (B/500ms)"),
            ("usb_idle",    "上次收到"),
        ]
        self.usb_labels = {}
        for i, (key, label) in enumerate(usb_stats_fields):
            row_frame = ctk.CTkFrame(self.usb_frame, fg_color="transparent")
            row_frame.grid(row=i+1, column=0, sticky="ew", padx=14, pady=1)
            row_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row_frame, text=f"{label}:", font=("Arial", 11), text_color="#aaaaaa").grid(row=0, column=0, sticky="w")
            self.usb_labels[key] = ctk.CTkLabel(row_frame, text="-", font=("Arial", 11, "bold"), text_color="#dddddd")
            self.usb_labels[key].grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(self.usb_frame, text="", height=4).grid(row=6, column=0)  # 底部間距

        # WiFi設定區 (精簡版，以節省高度)
        self.wifi_frame = ctk.CTkFrame(self.left_frame, corner_radius=8)
        self.wifi_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.wifi_frame.grid_columnconfigure(0, weight=0)
        self.wifi_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.wifi_frame, text="WiFi設定", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(6,4))

        ctk.CTkLabel(self.wifi_frame, text="SSID:", font=("Arial", 11)).grid(row=1, column=0, padx=(10,2), pady=2, sticky="w")
        ssid_container = ctk.CTkFrame(self.wifi_frame, fg_color="transparent")
        ssid_container.grid(row=1, column=1, padx=(2,10), pady=2, sticky="ew")
        ssid_container.grid_columnconfigure(0, weight=1)
        ssid_container.grid_columnconfigure(1, weight=0)
        self.ssid_entry = ctk.CTkComboBox(ssid_container, values=["手動輸入 SSID"], height=24, font=("Arial", 11))
        self.ssid_entry.grid(row=0, column=0, sticky="ew")
        self.scan_wifi_btn = ctk.CTkButton(ssid_container, text="🔄", width=30, height=24, font=("Arial", 11), command=self.scan_wifi_ssids)
        self.scan_wifi_btn.grid(row=0, column=1, padx=(5,0))

        ctk.CTkLabel(self.wifi_frame, text="密碼:", font=("Arial", 11)).grid(row=2, column=0, padx=(10,2), pady=2, sticky="w")
        self.password_entry = ctk.CTkEntry(self.wifi_frame, placeholder_text="請輸入密碼", show="*", height=24, font=("Arial", 11))
        self.password_entry.grid(row=2, column=1, padx=(2,10), pady=2, sticky="ew")

        self.set_wifi_btn = ctk.CTkButton(self.wifi_frame, text="設定WiFi", command=self.set_wifi, height=24, font=("Arial", 11))
        self.set_wifi_btn.grid(row=3, column=0, columnspan=2, padx=10, pady=6)

        # 紀錄操作按鈕
        self.log_actions_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.log_actions_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=4)
        self.log_actions_frame.grid_columnconfigure(0, weight=1)
        self.log_actions_frame.grid_columnconfigure(1, weight=1)

        self.export_btn = ctk.CTkButton(self.log_actions_frame, text="匯出CSV", command=self.export_csv)
        self.export_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.clear_btn = ctk.CTkButton(self.log_actions_frame, text="清除顯示", command=self.clear_logs, fg_color="#d32f2f")
        self.clear_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # ---- 右側面板內容 ----
        # 日誌表頭與本機藍牙控制按鈕
        self.header_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.logs_header = ctk.CTkLabel(self.header_frame, text="藍牙廣播接收比對面板", font=("Arial", 18, "bold"))
        self.logs_header.pack(side="left", padx=5)

        # 本機藍牙控制按鈕
        self.toggle_ble_btn = ctk.CTkButton(self.header_frame, text="開始本機藍牙比對", command=self.toggle_ble_scan, fg_color="#2b719e")
        self.toggle_ble_btn.pack(side="right", padx=5)
        if not BLEAK_AVAILABLE:
            self.toggle_ble_btn.configure(state="disabled", text="本機無藍牙模組 (缺少bleak)")

        # 搜尋過濾
        self.filter_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5,0))
        self.filter_frame.grid_columnconfigure(1, weight=1)
        self.filter_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(self.filter_frame, text="MAC篩選:").grid(row=0, column=0, padx=(0,5))
        self.filter_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="輸入 MAC 地址進行篩選...")
        self.filter_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.filter_entry.bind("<KeyRelease>", lambda e: self.update_logs_tables())

        self.filter_clear_btn = ctk.CTkButton(self.filter_frame, text="清除篩選", command=lambda: (self.filter_entry.delete(0, "end"), self.update_logs_tables()), width=70)
        self.filter_clear_btn.grid(row=0, column=2, padx=5)

        # 掃描資訊列 (顯示開始時間與接收筆數)
        self.info_bar_frame = ctk.CTkFrame(self.right_frame, fg_color="#1a2030", corner_radius=6)
        self.info_bar_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(4,0))
        self.info_bar_frame.grid_columnconfigure(0, weight=1)
        self.info_bar_frame.grid_columnconfigure(1, weight=1)
        self.info_bar_frame.grid_columnconfigure(2, weight=1)

        self.info_gw_label = ctk.CTkLabel(
            self.info_bar_frame,
            text="[ A ] Gateway：尚未連線",
            font=("Arial", 11), text_color="#aaaaaa", anchor="w"
        )
        self.info_gw_label.grid(row=0, column=0, padx=10, pady=4, sticky="w")

        self.info_ble_label = ctk.CTkLabel(
            self.info_bar_frame,
            text="[ B ] 本機藍牙：尚未開始掃描",
            font=("Arial", 11), text_color="#aaaaaa", anchor="center"
        )
        self.info_ble_label.grid(row=0, column=1, padx=10, pady=4)

        self.info_match_label = ctk.CTkLabel(
            self.info_bar_frame,
            text="比對：等待資料...",
            font=("Arial", 11), text_color="#aaaaaa", anchor="e"
        )
        self.info_match_label.grid(row=0, column=2, padx=10, pady=4, sticky="e")

        # 左右兩個 Treeview 表格並排
        self.tables_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.tables_container.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4,10))
        self.tables_container.grid_columnconfigure(0, weight=1)
        self.tables_container.grid_columnconfigure(1, weight=1)
        self.tables_container.grid_rowconfigure(0, weight=1)

        # 設定自訂 Treeview 樣式
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0, rowheight=25)
        style.map("Treeview", background=[("selected", "#1f6aa5")])
        style.configure("Treeview.Heading", background="#1f2122", foreground="white", borderwidth=0)

        # 1. 左邊表格：Gateway (COM)
        self.gateway_table_frame = ctk.CTkFrame(self.tables_container)
        self.gateway_table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.gateway_table_frame.grid_rowconfigure(0, weight=0)
        self.gateway_table_frame.grid_rowconfigure(1, weight=1)
        self.gateway_table_frame.grid_columnconfigure(0, weight=1)
        self.gateway_table_frame.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(self.gateway_table_frame, text="[ A ] Gateway (COM7) 接收紀錄", font=("Arial", 14, "bold"), text_color="#3a9cd6").grid(row=0, column=0, columnspan=2, pady=5)
        
        self.logs_tree = ttk.Treeview(self.gateway_table_frame, columns=("mac", "rssi", "data", "count", "first_time", "last_time"), show="headings", height=15)
        self.logs_tree.heading("mac",        text="實體 MAC 地址")
        self.logs_tree.heading("rssi",       text="RSSI")
        self.logs_tree.heading("data",       text="廣播數據")
        self.logs_tree.heading("count",      text="次數")
        self.logs_tree.heading("first_time", text="首次發現")
        self.logs_tree.heading("last_time",  text="最後時間")
        self.logs_tree.column("mac",        width=140, anchor="center")
        self.logs_tree.column("rssi",       width=70,  anchor="center")
        self.logs_tree.column("data",       width=120, anchor="center")
        self.logs_tree.column("count",      width=55,  anchor="center")
        self.logs_tree.column("first_time", width=90,  anchor="center")
        self.logs_tree.column("last_time",  width=90,  anchor="center")
        
        # 綁定高亮顏色 tag (綠色代表兩邊同步)
        self.logs_tree.tag_configure("matched", background="#2d4a2d", foreground="#a6e22e")

        vsb_g = ttk.Scrollbar(self.gateway_table_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=vsb_g.set)
        self.logs_tree.grid(row=1, column=0, sticky="nsew")
        vsb_g.grid(row=1, column=1, sticky="ns")

        # 2. 右邊表格：本機藍牙 (Bleak)
        self.ble_table_frame = ctk.CTkFrame(self.tables_container)
        self.ble_table_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.ble_table_frame.grid_rowconfigure(0, weight=0)
        self.ble_table_frame.grid_rowconfigure(1, weight=1)
        self.ble_table_frame.grid_columnconfigure(0, weight=1)
        self.ble_table_frame.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(self.ble_table_frame, text="[ B ] 筆電本機 (Notebook BLE) 接收紀錄", font=("Arial", 14, "bold"), text_color="#2b719e").grid(row=0, column=0, columnspan=2, pady=5)
        
        self.ble_tree = ttk.Treeview(self.ble_table_frame, columns=("mac", "rssi", "data", "count", "first_time", "last_time"), show="headings", height=15)
        self.ble_tree.heading("mac",        text="實體 MAC 地址")
        self.ble_tree.heading("rssi",       text="RSSI")
        self.ble_tree.heading("data",       text="廣播數據")
        self.ble_tree.heading("count",      text="次數")
        self.ble_tree.heading("first_time", text="首次發現")
        self.ble_tree.heading("last_time",  text="最後時間")
        self.ble_tree.column("mac",        width=140, anchor="center")
        self.ble_tree.column("rssi",       width=70,  anchor="center")
        self.ble_tree.column("data",       width=120, anchor="center")
        self.ble_tree.column("count",      width=55,  anchor="center")
        self.ble_tree.column("first_time", width=90,  anchor="center")
        self.ble_tree.column("last_time",  width=90,  anchor="center")

        self.ble_tree.tag_configure("matched", background="#2d4a2d", foreground="#a6e22e")

        vsb_b = ttk.Scrollbar(self.ble_table_frame, orient="vertical", command=self.ble_tree.yview)
        self.ble_tree.configure(yscrollcommand=vsb_b.set)
        self.ble_tree.grid(row=1, column=0, sticky="nsew")
        vsb_b.grid(row=1, column=1, sticky="ns")

        # 狀態列
        self.status_bar = ctk.CTkLabel(self, text="就緒", anchor="w", font=("Arial", 11))
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0,5))
        
        # 綁定雙擊事件以開啟歷史紀錄詳細資料
        self.logs_tree.bind("<Double-1>", lambda e: self.show_device_details("gateway"))
        self.ble_tree.bind("<Double-1>", lambda e: self.show_device_details("ble"))

        # 初始化掃描
        self.after(100, self.scan_ports)

    def scan_ports(self):
        """掃描COM Port"""
        self.scan_btn.configure(state="disabled", text="掃描中...")
        self.status_bar.configure(text="正在掃描系統可用 COM Port...")
        self.update()

        # 在背景執行掃描
        def do_scan():
            ports = self.serial_manager.scan_ports()
            self.after(0, lambda: self._update_ports(ports))

        threading.Thread(target=do_scan, daemon=True).start()

    def _update_ports(self, ports):
        """更新Port列表"""
        self.scan_btn.configure(state="normal", text="掃描")
        if ports:
            self.port_combo.configure(values=ports)
            if self.port_combo.get() not in ports:
                self.port_combo.set(ports[0])
            self.status_bar.configure(text=f"找到 {len(ports)} 個可用 COM 序列埠")
        else:
            self.port_combo.configure(values=["無可用Port"])
            self.port_combo.set("無可用Port")
            self.status_bar.configure(text="未找到可用 COM 序列埠，請確認是否插上開發板")

    def toggle_connection(self):
        """切換連線/斷開"""
        if self.serial_manager.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        """連接設備"""
        port = self.port_combo.get()
        if not port or port == "無可用Port":
            messagebox.showwarning("警告", "請選擇有效的 COM Port")
            return

        self.connect_btn.configure(state="disabled", text="連接中...")
        self.status_bar.configure(text=f"正在連接到 {port}...")
        self.update()

        def do_connect():
            success = self.serial_manager.connect(port)
            self.after(0, lambda: self._connection_result(success))

        threading.Thread(target=do_connect, daemon=True).start()

    def _connection_result(self, success):
        """連接結果處理"""
        if success:
            self.connect_btn.configure(text="斷開", fg_color="#d32f2f", state="normal")
            self.gateway_connect_time = datetime.now()
            connect_time_str = self.gateway_connect_time.strftime("%H:%M:%S")
            self.status_bar.configure(text=f"成功連接至設備: {self.port_combo.get()} @ {connect_time_str}")
            self.info_gw_label.configure(
                text=f"[ A ] Gateway 已連線  |  連線時間: {connect_time_str}  |  接收: 0 筆",
                text_color="#3a9cd6"
            )
            # 啟動定時查詢
            self.start_status_timer()
            self.start_logs_timer()
            self.start_usb_monitor()
            
            # 連接成功後立即發送對時指令
            sync_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            self.serial_manager.send_command(f"SET_TIME:{sync_time}")
            # 延遲 1.5 秒再發一次，確保 Gateway 就緒完全準備好後再對時
            self.after(1500, self._delayed_time_sync)
        else:
            self.connect_btn.configure(text="連接", fg_color="#1f6aa5", state="normal")
            self.status_bar.configure(text=f"連線失敗，請確認該 COM 口是否被其他程式佔用")
            messagebox.showerror("錯誤", f"無法開啟 {self.port_combo.get()}")

    def _delayed_time_sync(self):
        """1.5 秒延遲後再發一次對時，確保 Gateway 就緒完全啟動"""
        if self._is_closing or not self.serial_manager.is_connected:
            return
        sync_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.serial_manager.send_command(f"SET_TIME:{sync_time}")
        self.status_bar.configure(text=f"對時已發送: {sync_time}")

    def disconnect_device(self):
        """斷開設備"""
        self.stop_status_timer()
        self.stop_logs_timer()
        self.stop_usb_monitor()
        self.serial_manager.disconnect()
        self.gateway_connect_time = None
        self.connect_btn.configure(text="連接", fg_color="#1f6aa5", state="normal")
        self.status_bar.configure(text="已斷開與設備的連線")
        self.info_gw_label.configure(text="[ A ] Gateway：尚未連線", text_color="#aaaaaa")
        # 清除狀態與 USB 監視顯示
        for key in self.status_labels:
            self.status_labels[key].configure(text="-")
        self.status_data.clear()
        self.usb_indicator.configure(text="● 未連線", text_color="#666666")
        for key in self.usb_labels:
            self.usb_labels[key].configure(text="-", text_color="#dddddd")

    def start_usb_monitor(self):
        """啟動 USB 監視定時刷新"""
        self.usb_monitor_running = True
        self._refresh_usb_stats()

    def stop_usb_monitor(self):
        """停止 USB 監視"""
        self.usb_monitor_running = False
        if hasattr(self, '_usb_monitor_id') and self._usb_monitor_id:
            self.after_cancel(self._usb_monitor_id)
            self._usb_monitor_id = None

    def _refresh_usb_stats(self):
        """刷新 USB 接收統計顯示（每 500ms 執行一次）"""
        if not self.usb_monitor_running:
            return

        stats = self.serial_manager.get_stats()
        total_bytes = stats["total_bytes"]
        total_lines = stats["total_lines"]
        bps = stats["bps_window"]
        idle_sec = stats["idle_sec"]

        # 格式化數字
        if total_bytes >= 1024:
            bytes_str = f"{total_bytes / 1024:.1f} KB  ({total_bytes:,} B)"
        else:
            bytes_str = f"{total_bytes} B"

        idle_str = f"{idle_sec:.1f} 秒前" if idle_sec is not None else "尚未收到資料"

        self.usb_labels["usb_bytes"].configure(text=bytes_str)
        self.usb_labels["usb_lines"].configure(text=f"{total_lines:,} 行")
        self.usb_labels["usb_bps"].configure(text=f"{bps} B")
        self.usb_labels["usb_idle"].configure(text=idle_str)

        # 活耶指示器顏色：根據跨期判斷
        if idle_sec is None:
            # 還沒有收到任何資料
            self.usb_indicator.configure(text="● 等待資料...", text_color="#ff9800")
        elif idle_sec < 3:
            # 3秒內有收到資料 = 經常性活耶
            self.usb_indicator.configure(text="● 傳輸中", text_color="#4caf50")
        elif idle_sec < 10:
            # 3~10秒 = 偏低頻度
            self.usb_indicator.configure(text="● 注意：傳輸跟不上", text_color="#ff9800")
        else:
            # >10秒 = 可能斷線
            self.usb_indicator.configure(text="● 警告：超過 10s 未收到", text_color="#f44336")

        # 安排下次刷新
        self._usb_monitor_id = self.after(500, self._refresh_usb_stats)

    def start_status_timer(self):
        """啟動狀態查詢定時器"""
        self.status_timer_running = True
        self._send_status_request()

    def stop_status_timer(self):
        """停止狀態查詢定時器"""
        self.status_timer_running = False
        if self.status_timer_id:
            self.after_cancel(self.status_timer_id)
            self.status_timer_id = None

    def _send_status_request(self):
        """發送GET_STATUS請求"""
        if self._is_closing:
            return
        if self.serial_manager.is_connected and self.status_timer_running:
            self.serial_manager.send_command("GET_STATUS")
            self.status_timer_id = self.after(2000, self._send_status_request)

    def start_logs_timer(self):
        """啟動日誌查詢定時器"""
        self.logs_timer_running = True
        self._send_logs_request()

    def stop_logs_timer(self):
        """停止日誌查詢定時器"""
        self.logs_timer_running = False
        if self.logs_timer_id:
            self.after_cancel(self.logs_timer_id)
            self.logs_timer_id = None

    def _send_logs_request(self):
        """發送GET_LOGS請求"""
        if self._is_closing:
            return
        if self.serial_manager.is_connected and self.logs_timer_running:
            self.serial_manager.send_command("GET_LOGS")
            self.logs_timer_id = self.after(1000, self._send_logs_request)

    def handle_serial_error(self, err_msg):
        """處理串口連線錯誤（例如 USB 被拔掉）"""
        self.after(0, self._on_serial_disconnect_error, err_msg)

    def _on_serial_disconnect_error(self, err_msg):
        self.disconnect_device()
        self.status_bar.configure(text=f"⚠️ 連線異常中斷 ({err_msg})，請確認 USB 連線是否正常！")
        try:
            messagebox.showwarning("連線中斷", f"與 Gateway 的 USB 連線異常中斷！\n錯誤原因: {err_msg}\n\n請確認 USB 連線正常後重新點擊「連接」。")
        except:
            pass

    def handle_received_data(self, data):
        """處理接收到的資料"""
        try:
            json_data = json.loads(data)
            cmd = json_data.get("cmd", "")

            if cmd == "STATUS":
                self.handle_status(json_data)
            elif cmd == "LOGS":
                self.handle_logs(json_data)
            elif cmd == "SCAN_WIFI":
                self.handle_wifi_scan_result(json_data)

        except json.JSONDecodeError:
            # 忽略非JSON序列除錯訊息
            pass
    def handle_status(self, data):
        """處理狀態資料"""
        if self._is_closing:
            return
        self.status_data = data
        self.after(0, self._update_status_ui)
        
        # 自動對時：若偵測到 Gateway 時間尚未同步，在 Tkinter 主執行緒發送 SET_TIME
        # （不能在 serial reader 執行緒中直接寫入，避免讀寫相互狀）
        gw_time = data.get("time", "")
        if gw_time and (gw_time.startswith("2012") or gw_time.startswith("1970")):
            sync_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            self.after(0, lambda t=sync_time: self.serial_manager.send_command(f"SET_TIME:{t}"))

    def _update_status_ui(self):
        """更新狀態卡片UI"""
        wifi_status = self.status_data.get("wifi_connected", False)
        self.status_labels["wifi_connected"].configure(
            text="已連線" if wifi_status else "未連線",
            text_color="#4caf50" if wifi_status else "#f44336"
        )
        self.status_labels["ssid"].configure(text=self.status_data.get("ssid", "-"))
        self.status_labels["ip"].configure(text=self.status_data.get("ip", "-"))
        log_count = self.status_data.get("log_count", 0)
        self.status_labels["log_count"].configure(text=str(log_count))
        
        # 判斷時間同步狀態
        gw_time = self.status_data.get("time", "")
        if not gw_time and self.logs_data:
            # 如果 STATUS 沒帶時間，嘗試從最新的 log 裡抓取 Gateway 原始時間
            gw_time = self.logs_data[-1].get("_gw_time", "")
            
        if "time_sync" in self.status_labels:
            if gw_time:
                # 假設 2012 代表尚未對時
                if gw_time.startswith("2012"):
                    self.status_labels["time_sync"].configure(text="未同步 (2012)", text_color="#f44336")
                else:
                    self.status_labels["time_sync"].configure(text="已同步", text_color="#4caf50")
            else:
                self.status_labels["time_sync"].configure(text="未知", text_color="#aaaaaa")

    def parse_raw_ad(self, raw_hex):
        i = 0
        mfg_data = {}
        name = ""
        while i < len(raw_hex):
            try:
                length = int(raw_hex[i:i+2], 16)
                if length == 0: break
                ad_type = int(raw_hex[i+2:i+4], 16)
                ad_data = raw_hex[i+4 : i+2 + length*2]
                if ad_type == 0xFF and len(ad_data) >= 4:
                    company_id = int(ad_data[2:4] + ad_data[0:2], 16)
                    mfg_data[company_id] = ad_data[4:]
                elif ad_type in (0x08, 0x09):
                    name = bytes.fromhex(ad_data).decode('utf-8', 'ignore')
                i += 2 + length*2
            except: break
        return mfg_data, name

    def _extract_sensor_info(self, mac, name, mfg_dict, raw_data_str):
        if "9838" in mac:
            with open("debug_838.txt", "a", encoding="utf-8") as df:
                df.write(f"MAC: {mac}, Name: {name}, mfg: {mfg_dict}, raw: {raw_data_str}\n")
        is_sensor = False
        known_macs = {"E613AED238CD", "D3AE84703D4B", "DD7081805A31", "ED673D20F076", 
                      "C44638EFBEDA", "FB2FA39CBF6D", "F0F088119A65", "E465C045F354"}
        if mac in known_macs:
            is_sensor = True

        mfg_hex = ""
        for comp_id, data_hex in mfg_dict.items():
            mfg_hex = data_hex.upper()
            if comp_id == 76 and mfg_hex.startswith("1202") and len(mfg_hex) == 8:
                is_sensor = True
                break
            elif comp_id == 76 and mfg_hex.startswith("10") and len(mfg_hex) >= 14:
                is_sensor = True
                mac = mfg_hex[6:18]
                break
            elif comp_id in (0x0304, 0xFFFF):
                is_sensor = True
                if mfg_hex.startswith("01"):
                    mfg_hex = "🟢 (尿袋空) MEDFLO"
                elif mfg_hex.startswith("00"):
                    mfg_hex = "🔴 (尿袋滿) MEDFLO"
                else:
                    mfg_hex = f"⚪ (狀態未知) MEDFLO [{mfg_hex}]"
                break

        if not is_sensor:
            targets = ["NEXMEDAI", "MEDFLO", "7869887769686573", "776968707679"]
            for t in targets:
                if t in name or t in raw_data_str:
                    is_sensor = True
                    break

        if mfg_hex.startswith("🟢") or mfg_hex.startswith("🔴") or mfg_hex.startswith("⚪"):
            data_show = mfg_hex
        elif "MEDFLO" in name:
            data_show = f"⚪ (未解析) mfg={mfg_dict} raw={raw_data_str[:30]}"
        else:
            data_show = mfg_hex[:20] if mfg_hex else name
            
        return is_sensor, mac, data_show

    def handle_logs(self, data):
        """處理日誌資料 - 寫入 Gateway 設備登記簿"""
        if self._is_closing:
            return
        logs = data.get("logs", [])
        if not logs:
            return

        with self.logs_lock:
            for log in logs:
                mac = log.get("mac", "").upper().replace(":", "")
                data_str = log.get("data", "")
                time_str = log.get("time", "")
                rssi     = log.get("rssi", 0)
                
                mfg_dict, name = self.parse_raw_ad(data_str)
                is_sensor, real_mac, data_show = self._extract_sensor_info(mac, name, mfg_dict, data_str)
                
                if not is_sensor:
                    continue
                    
                mac = real_mac
                data_str = data_show

                # 寫入設備登記簿（以實體 MAC 為 key，首次發現順序，不重排）
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if mac in self.gw_device_registry:
                    entry = self.gw_device_registry[mac]
                    # 只如果時間或數據有變就更新（避免重複日誌視為新貼）
                    if entry["data"] != data_str or entry["_gw_time"] != time_str:
                        entry["rssi"]     = rssi
                        entry["data"]     = data_str
                        entry["count"]   += 1
                        entry["last_time"] = now_str
                        entry["_gw_time"] = time_str
                else:
                    self.gw_device_registry[mac] = {
                        "mac":        mac,
                        "rssi":       rssi,
                        "data":       data_str,
                        "count":      1,
                        "first_time": now_str,
                        "last_time":  now_str,
                        "_gw_time":   time_str,
                    }
                
                # 保留 logs_data 以支援 CSV 匯出
                log["_gw_time"] = time_str
                log["mac"]      = mac
                log["time"]     = now_str
                self.logs_data.append(log)

        # 更新表格
        self.after(0, self.update_logs_tables)

    # ==================== 更新 Table ====================
    def update_logs_tables(self):
        """同時更新 Gateway 表格與本機藍牙表格，並做同步比對"""
        filter_text = self.filter_entry.get().strip().upper()

        # 1. snapshot 兩個 registry
        with self.logs_lock:
            gw_registry = dict(self.gw_device_registry)
        with self.ble_logs_lock:
            ble_registry = dict(self.ble_device_registry)

        # 2. 找出兩邊共同出現的 MAC（比對交集）
        matched_macs = set(gw_registry.keys()).intersection(set(ble_registry.keys()))

        # ── 左表 (Gateway)：以 gw_device_registry 為準，in-place 更新 ──
        existing_gw_iids = set(self.logs_tree.get_children())
        filtered_gateway_count = 0
        for mac, entry in gw_registry.items():
            if filter_text and filter_text not in mac:
                continue
            filtered_gateway_count += 1
            rssi_str = f"{entry['rssi']} dBm"
            tag = "matched" if mac in matched_macs else ""
            first_t = entry['first_time'][-8:] if len(entry['first_time']) >= 8 else entry['first_time']
            last_t  = entry['last_time'][-8:]  if len(entry['last_time'])  >= 8 else entry['last_time']
            values = (mac, rssi_str, entry['data'], entry['count'], first_t, last_t)
            if mac in existing_gw_iids:
                self.logs_tree.item(mac, values=values, tags=(tag,))
            else:
                self.logs_tree.insert("", "end", iid=mac, values=values, tags=(tag,))
        for iid in existing_gw_iids:
            if iid not in gw_registry or (filter_text and filter_text not in iid):
                self.logs_tree.delete(iid)

        # ── 右表 (BLE)：以設備登記簿為準，穩定更新 ──
        # 取得目前 Treeview 中已有的 row（iid = mac）
        existing_iids = set(self.ble_tree.get_children())

        filtered_ble_count = 0
        for mac, entry in ble_registry.items():
            if filter_text and filter_text not in mac:
                continue
            filtered_ble_count += 1
            rssi_str = f"{entry['rssi']} dBm"
            tag = "matched" if mac in matched_macs else ""
            # 時間只顯示 HH:MM:SS 縮短
            first_t = entry['first_time'][-8:] if len(entry['first_time']) >= 8 else entry['first_time']
            last_t  = entry['last_time'][-8:]  if len(entry['last_time'])  >= 8 else entry['last_time']
            values = (mac, rssi_str, entry['data'], entry['count'], first_t, last_t)

            if mac in existing_iids:
                # 已存在的列：in-place 更新，不閃動
                self.ble_tree.item(mac, values=values, tags=(tag,))
            else:
                # 新設備：追加到最後
                self.ble_tree.insert("", "end", iid=mac, values=values, tags=(tag,))

        # 移除已被過濾掉但還在 Treeview 的行（filter 變化時清理）
        for iid in existing_iids:
            if iid not in ble_registry or (filter_text and filter_text not in iid):
                self.ble_tree.delete(iid)

        # 5. 更新資訊列
        connect_str = self.gateway_connect_time.strftime("%H:%M:%S") if self.gateway_connect_time else "未連線"
        if self.gateway_connect_time:
            self.info_gw_label.configure(
                text=f"[ A ] Gateway 已連線  |  連線時間: {connect_str}  |  設備數: {filtered_gateway_count} 台 (共 {len(gw_registry)} 台)",
                text_color="#3a9cd6"
            )

        if self.ble_scan_start_time:
            ble_start_str = self.ble_scan_start_time.strftime("%H:%M:%S")
            total_ble = len(ble_registry)
            self.info_ble_label.configure(
                text=f"[ B ] 本機掃描中 ●  |  開始: {ble_start_str}  |  已找到: {total_ble} 台",
                text_color="#4caf50"
            )

        # 6. 更新比對狀態列
        if matched_macs:
            match_list_str = ", ".join(list(matched_macs)[:3])
            if len(matched_macs) > 3:
                match_list_str += "..."
            self.info_match_label.configure(
                text=f"✅ 已比對 {len(matched_macs)} 台同步",
                text_color="#a6e22e"
            )
            self.status_bar.configure(text=f"✅ 比對成功! 同步設備: [{match_list_str}] (共 {len(matched_macs)} 台) | 左表 {filtered_gateway_count} 台 | 右表 {filtered_ble_count} 台")
        else:
            self.info_match_label.configure(text="比對：等待資料...", text_color="#aaaaaa")
            self.status_bar.configure(text=f"⏳ 正在接收訊號... 左表 {filtered_gateway_count} 台 | 右表 {filtered_ble_count} 台 (尚未發現兩邊同步之藍牙設備)")

    def show_device_details(self, source):
        """雙擊表格項目時，彈出視窗顯示該 MAC 的歷史接收紀錄"""
        tree = self.logs_tree if source == "gateway" else self.ble_tree
        selected = tree.selection()
        if not selected:
            return

        item = tree.item(selected[0])
        mac = item["values"][0]

        # 取得該 MAC 的詳細資訊
        history = []
        if source == "gateway":
            with self.logs_lock:
                history = [log for log in self.logs_data if log.get("mac", "").upper() == mac]
        else:
            # BLE 登記簿只有一筆（已聚合），展開為詳細格式
            with self.ble_logs_lock:
                entry = self.ble_device_registry.get(mac)
            if entry:
                history = [{
                    "mac":   entry["mac"],
                    "rssi":  entry["rssi"],
                    "data":  entry["data"],
                    "time":  f"首次: {entry['first_time']}  /  最後: {entry['last_time']}",
                    "count": entry["count"],
                }]

        # 建立彈出視窗
        detail_win = ctk.CTkToplevel(self)
        detail_win.title(f"[{mac}] 歷史接收紀錄 - 共 {len(history)} 筆")
        detail_win.geometry("600x400")
        detail_win.minsize(500, 300)
        
        # 讓彈出視窗置頂且聚焦
        detail_win.attributes("-topmost", True)
        detail_win.focus_force()

        # 標題
        title_label = ctk.CTkLabel(
            detail_win, 
            text=f"設備 MAC 地址: {mac}\n資料來源: {'Gateway' if source == 'gateway' else '筆電本機'}", 
            font=("Arial", 14, "bold"),
            text_color="#3a9cd6" if source == "gateway" else "#2b719e"
        )
        title_label.pack(pady=10)

        # 表格容器
        table_frame = ctk.CTkFrame(detail_win)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0,15))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 表格
        detail_tree = ttk.Treeview(table_frame, columns=("time", "rssi", "data"), show="headings")
        detail_tree.heading("time", text="接收時間")
        detail_tree.heading("rssi", text="RSSI 訊號")
        detail_tree.heading("data", text="自訂廣播數據" if source == "gateway" else "解析特徵")
        
        detail_tree.column("time", width=180, anchor="center")
        detail_tree.column("rssi", width=100, anchor="center")
        detail_tree.column("data", width=220, anchor="center")

        # 插入歷史紀錄 (最新排在最上面)
        for log in reversed(history):
            t = log.get("time", "")
            r = f"{log.get('rssi', '')} dBm"
            d = log.get("data", "")
            detail_tree.insert("", "end", values=(t, r, d))

        # 滾動條
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=detail_tree.yview)
        detail_tree.configure(yscrollcommand=vsb.set)
        
        detail_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

    def scan_wifi_ssids(self):
        """向 Gateway 發送 WiFi 掃描請求"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("提示", "請先連接 Gateway 的 COM Port 再進行 WiFi 掃描。")
            return
        self.scan_wifi_btn.configure(state="disabled", text="⌛")
        self.status_bar.configure(text="正在掃描周邊 WiFi SSID，請稍候...")
        self.serial_manager.send_command("SCAN_WIFI")

    def handle_wifi_scan_result(self, data):
        """處理 WiFi 掃描結果"""
        status = data.get("status", "")
        
        if status == "SCANNING":
            # Gateway 已收到命令，正在背景掃描，等待結果回來
            self.status_bar.configure(text="Gateway 正在掃描周邊 WiFi，請稍候 (約 5~10 秒)...")
            return
        
        # 完整結果已回傳
        ap_list = data.get("ap_list", [])
        ssids = list(set([ssid for ssid in ap_list if ssid]))
        ssids.sort()
        if not ssids:
            ssids = ["手動輸入 SSID"]
        self.after(0, self._update_ssid_combobox, ssids)

    def _update_ssid_combobox(self, ssids):
        self.ssid_entry.configure(values=ssids)
        if ssids:
            self.ssid_entry.set(ssids[0])
        self.scan_wifi_btn.configure(state="normal", text="🔄")
        self.status_bar.configure(text=f"WiFi 掃描完成！共找到 {len(ssids)} 個熱點。")

    def set_wifi(self):
        """設定WiFi"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("警告", "請先連接設備")
            return

        ssid = self.ssid_entry.get().strip()
        password = self.password_entry.get().strip()

        if not ssid or ssid == "手動輸入 SSID" or ssid == "未偵測到 WiFi":
            messagebox.showwarning("警告", "請輸入或選擇有效的 SSID")
            return

        command = f"SET_WIFI:{ssid},{password}"
        if self.serial_manager.send_command(command):
            self.status_bar.configure(text=f"已送出 WiFi 設定，正在啟動連線檢測... SSID: {ssid}")
            # 停用 UI 以防重複提交
            self.set_wifi_btn.configure(state="disabled")
            self.ssid_entry.configure(state="disabled")
            self.password_entry.configure(state="disabled")
            self.scan_wifi_btn.configure(state="disabled")
            
            # 開始進行連線監測
            import time
            self.target_ssid = ssid
            self.wifi_check_start_time = time.time()
            self.after(1000, self._check_wifi_connection_status)
        else:
            messagebox.showerror("錯誤", "發送指令失敗，請檢查硬體連線是否中斷")

    def _check_wifi_connection_status(self):
        import time
        if not self.serial_manager.is_connected:
            self._restore_wifi_ui()
            return

        elapsed = int(time.time() - self.wifi_check_start_time)
        
        # 取得目前連線的 IP 與 SSID
        current_ip = self.status_data.get("ip", "0.0.0.0") if hasattr(self, "status_data") else "0.0.0.0"
        current_ssid = self.status_data.get("ssid", "") if hasattr(self, "status_data") else ""
        
        if current_ip != "0.0.0.0" and current_ssid == self.target_ssid:
            # 連線成功！
            self._restore_wifi_ui()
            self.password_entry.delete(0, "end")
            self.status_bar.configure(text=f"🎉 WiFi 連線成功！IP地址: {current_ip}")
            messagebox.showinfo("連線成功", f"WiFi 連線成功！\nSSID: {self.target_ssid}\nIP 地址: {current_ip}")
        elif elapsed >= 15:
            # 15 秒超時
            self._restore_wifi_ui()
            self.status_bar.configure(text="⚠️ WiFi 連線超時，請確認密碼是否正確")
            messagebox.showwarning("連線超時", f"WiFi 連線超時！\n\n請確認 SSID【{self.target_ssid}】與密碼是否正確。\n(此時 Gateway 將嘗試在背景繼續連線)")
        else:
            # 繼續等待並更新按鈕文字
            self.set_wifi_btn.configure(text=f"連線中 ({elapsed}s/15s)...")
            self.after(1000, self._check_wifi_connection_status)

    def _restore_wifi_ui(self):
        self.set_wifi_btn.configure(state="normal", text="設定WiFi")
        self.ssid_entry.configure(state="normal")
        self.password_entry.configure(state="normal")
        self.scan_wifi_btn.configure(state="normal")

    def export_csv(self):
        """匯出CSV"""
        with self.logs_lock:
            if not self.logs_data:
                messagebox.showinfo("提示", "目前尚無接收紀錄可供匯出")
                return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV檔案", "*.csv")],
            initialfile=f"medflo_bluetooth_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["藍牙 MAC 地址", "RSSI 訊號強度 (dBm)", "廣播數據 (Hex)", "接收時間"])

                with self.logs_lock:
                    for log in self.logs_data:
                        writer.writerow([
                            log.get("mac", ""),
                            log.get("rssi", ""),
                            log.get("data", ""),
                            log.get("time", "")
                        ])

            self.status_bar.configure(text=f"數據匯出成功! 檔案: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", f"成功將 {len(self.logs_data)} 筆紀錄儲存至 {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("錯誤", f"無法匯出檔案: {str(e)}")

    def clear_logs(self):
        """清除日誌"""
        if messagebox.askyesno("確認", "確定要清除畫面上已接收的所有紀錄嗎？"):
            with self.logs_lock:
                self.logs_data.clear()
            with self.ble_logs_lock:
                self.ble_logs_data.clear()
            self.update_logs_tables()
            self.status_bar.configure(text="左右表格顯示皆已清除")



if __name__ == "__main__":
    app = App()
    app.mainloop()
