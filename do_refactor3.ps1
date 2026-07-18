import re

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\refactor2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update update_logs_tables
update_logs_replacement = '''    # ==================== 更新 Table ====================
    def update_logs_tables(self):
        """更新 Gateway 表格"""
        filter_text = self.filter_entry.get().strip().upper()

        with self.logs_lock:
            gw_registry = dict(self.gw_device_registry)

        existing_gw_iids = set(self.logs_tree.get_children())
        filtered_gateway_count = 0
        for mac, entry in gw_registry.items():
            if filter_text and filter_text not in mac:
                continue
            filtered_gateway_count += 1
            rssi_str = f"{entry['rssi']} dBm"
            first_t = entry['first_time'][-8:] if len(entry['first_time']) >= 8 else entry['first_time']
            last_t  = entry['last_time'][-8:]  if len(entry['last_time'])  >= 8 else entry['last_time']
            values = (mac, rssi_str, entry['data'], entry['count'], first_t, last_t)
            if mac in existing_gw_iids:
                self.logs_tree.item(mac, values=values)
            else:
                self.logs_tree.insert("", "end", iid=mac, values=values)
        for iid in existing_gw_iids:
            if iid not in gw_registry or (filter_text and filter_text not in iid):
                self.logs_tree.delete(iid)

        connect_str = self.gateway_connect_time.strftime("%H:%M:%S") if self.gateway_connect_time else "未連線"
        if self.gateway_connect_time:
            self.info_gw_label.configure(
                text=f"Gateway 已連線  |  連線時間: {connect_str}  |  設備數: {filtered_gateway_count} 台 (共 {len(gw_registry)} 台)",
                text_color="#3a9cd6"
            )

        self.status_bar.configure(text=f"接收中... 顯示 {filtered_gateway_count} 台 (共 {len(gw_registry)} 台)")'''

content = re.sub(r'    # ==================== 更新 Table ====================.*?    def show_device_details', update_logs_replacement + '\n\n    def show_device_details', content, flags=re.DOTALL)

# Update _update_status_ui to populate the dashboard
update_status_ui_replacement = '''    def _update_status_ui(self):
        """更新狀態卡片UI與 Dashboard"""
        wifi_status = self.status_data.get("wifi_connected", False)
        ssid_text = self.status_data.get("wifi_ssid", "-")
        ip_text = self.status_data.get("ip", "-")
        target_url = self.status_data.get("target_url", "未設定")
        uptime = self.status_data.get("time", "-")
        buf_usage = self.status_data.get("buf_usage", 0.0)

        # Update left panel
        self.status_labels["wifi_connected"].configure(
            text="已連線" if wifi_status else "未連線",
            text_color="#4caf50" if wifi_status else "#f44336"
        )
        self.status_labels["ssid"].configure(text=ssid_text)
        self.status_labels["ip"].configure(text=ip_text)
        log_count = self.status_data.get("log_count", 0)
        self.status_labels["log_count"].configure(text=str(log_count))
        
        # Update right dashboard
        self.dash_ssid_label.configure(text=ssid_text if ssid_text else "無連線", text_color="#4caf50" if wifi_status else "#f44336")
        self.dash_ip_label.configure(text=ip_text)
        self.dash_url_label.configure(text=target_url)
        self.dash_uptime_label.configure(text=uptime)
        
        self.dash_buf_label.configure(text=f"{buf_usage:.1f} %", text_color="#f44336" if buf_usage > 80 else "#ffffff")
        self.dash_buf_progress.set(buf_usage / 100.0)
        if buf_usage > 80:
            self.dash_buf_progress.configure(progress_color="#f44336")
        elif buf_usage > 50:
            self.dash_buf_progress.configure(progress_color="#ff9800")
        else:
            self.dash_buf_progress.configure(progress_color="#4caf50")
'''
content = re.sub(r'    def _update_status_ui\(self\):.*?    def parse_raw_ad', update_status_ui_replacement + '\n    def parse_raw_ad', content, flags=re.DOTALL)


# Update disconnect logic to clear dashboard
disconnect_replacement = '''    def disconnect_device(self):
        """斷開設備"""
        self.stop_status_timer()
        self.stop_logs_timer()
        self.stop_usb_monitor()
        self.serial_manager.disconnect()
        self.gateway_connect_time = None
        self.connect_btn.configure(text="連接", fg_color="#1f6aa5", state="normal")
        self.status_bar.configure(text="已斷開與設備的連線")
        self.info_gw_label.configure(text="Gateway：尚未連線", text_color="#aaaaaa")
        # 清除狀態與 USB 監視顯示
        for key in self.status_labels:
            if key in self.status_labels:
                self.status_labels[key].configure(text="-")
        self.status_data.clear()
        self.usb_indicator.configure(text="● 未連線", text_color="#666666")
        for key in self.usb_labels:
            self.usb_labels[key].configure(text="-", text_color="#dddddd")
        
        # 清除 Dashboard
        self.dash_ssid_label.configure(text="-", text_color="#aaaaaa")
        self.dash_ip_label.configure(text="-")
        self.dash_url_label.configure(text="-")
        self.dash_uptime_label.configure(text="-")
        self.dash_buf_label.configure(text="0.0 %", text_color="#aaaaaa")
        self.dash_buf_progress.set(0)
'''

content = re.sub(r'    def disconnect_device\(self\):.*?    def start_usb_monitor', disconnect_replacement + '\n    def start_usb_monitor', content, flags=re.DOTALL)

# Fix show_device_details to remove BLE logic completely
show_detail_replacement = '''    def show_device_details(self, source):
        """雙擊表格項目時，彈出視窗顯示該 MAC 的歷史接收紀錄"""
        tree = self.logs_tree
        selected = tree.selection()
        if not selected:
            return

        item = tree.item(selected[0])
        mac = item["values"][0]

        # 取得該 MAC 的詳細資訊
        history = []
        with self.logs_lock:
            history = [log for log in self.logs_data if log.get("mac", "").upper() == mac]

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
            text=f"設備 MAC 地址: {mac}\\n資料來源: Gateway", 
            font=("Arial", 14, "bold"),
            text_color="#3a9cd6"
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
        detail_tree.heading("data", text="自訂廣播數據")
        
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
        vsb.grid(row=0, column=1, sticky="ns")'''

content = re.sub(r'    def show_device_details\(self, source\):.*?    def scan_wifi_ssids', show_detail_replacement + '\n\n    def scan_wifi_ssids', content, flags=re.DOTALL)

# Fix clear_logs to remove ble_logs_data
clear_logs_replacement = '''    def clear_logs(self):
        """清除日誌"""
        if messagebox.askyesno("確認", "確定要清除畫面上已接收的所有紀錄嗎？"):
            with self.logs_lock:
                self.logs_data.clear()
            self.update_logs_tables()
            self.status_bar.configure(text="表格顯示皆已清除")'''
            
content = re.sub(r'    def clear_logs\(self\):.*?        self\.status_bar\.configure\(text="左右表格顯示皆已清除"\)', clear_logs_replacement, content, flags=re.DOTALL)

# Fix _connection_result
conn_result_replacement = '''    def _connection_result(self, success):
        """連接結果處理"""
        if success:
            self.connect_btn.configure(text="斷開", fg_color="#d32f2f", state="normal")
            self.gateway_connect_time = datetime.now()
            connect_time_str = self.gateway_connect_time.strftime("%H:%M:%S")
            self.status_bar.configure(text=f"成功連接至設備: {self.port_combo.get()} @ {connect_time_str}")
            self.info_gw_label.configure(
                text=f"Gateway 已連線  |  連線時間: {connect_time_str}  |  接收: 0 筆",
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
            messagebox.showerror("錯誤", f"無法開啟 {self.port_combo.get()}")'''
content = re.sub(r'    def _connection_result\(self, success\):.*?                messagebox\.showerror\("錯誤", f"無法開啟 \{self\.port_combo\.get\(\)\}"\)', conn_result_replacement, content, flags=re.DOTALL)

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\app_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

