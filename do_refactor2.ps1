import re

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\refactor1.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace setup_ui right frame header
ui_replacement = '''        # ---- 右側面板內容 ----
        # Gateway 狀態儀表板 (Dashboard)
        self.dashboard_frame = ctk.CTkFrame(self.right_frame, fg_color="#1a2030", corner_radius=8)
        self.dashboard_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        self.dashboard_frame.grid_columnconfigure(0, weight=1)
        self.dashboard_frame.grid_columnconfigure(1, weight=1)
        self.dashboard_frame.grid_columnconfigure(2, weight=1)

        # Dashboard Title
        dash_title_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        dash_title_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        ctk.CTkLabel(dash_title_frame, text="Gateway 硬體資源與狀態監控面板", font=("Arial", 16, "bold"), text_color="#3a9cd6").pack(side="left")

        # Column 0: AP & Network Info
        self.dash_ap_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.dash_ap_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(self.dash_ap_frame, text="AP SSID:", font=("Arial", 12), text_color="#aaaaaa").pack(anchor="w")
        self.dash_ssid_label = ctk.CTkLabel(self.dash_ap_frame, text="-", font=("Arial", 14, "bold"))
        self.dash_ssid_label.pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self.dash_ap_frame, text="IP 位址:", font=("Arial", 12), text_color="#aaaaaa").pack(anchor="w")
        self.dash_ip_label = ctk.CTkLabel(self.dash_ap_frame, text="-", font=("Arial", 14, "bold"))
        self.dash_ip_label.pack(anchor="w")

        # Column 1: Target URL & Uptime
        self.dash_url_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.dash_url_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(self.dash_url_frame, text="資料上傳目標 (Target URL):", font=("Arial", 12), text_color="#aaaaaa").pack(anchor="w")
        self.dash_url_label = ctk.CTkLabel(self.dash_url_frame, text="-", font=("Arial", 12, "bold"), text_color="#a6e22e")
        self.dash_url_label.pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self.dash_url_frame, text="Gateway 時間 (Uptime):", font=("Arial", 12), text_color="#aaaaaa").pack(anchor="w")
        self.dash_uptime_label = ctk.CTkLabel(self.dash_url_frame, text="-", font=("Arial", 14, "bold"))
        self.dash_uptime_label.pack(anchor="w")

        # Column 2: Buffer Usage Progress Bar
        self.dash_res_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        self.dash_res_frame.grid(row=1, column=2, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(self.dash_res_frame, text="Log 緩衝區使用率 (Buffer Usage):", font=("Arial", 12), text_color="#aaaaaa").pack(anchor="w")
        self.dash_buf_label = ctk.CTkLabel(self.dash_res_frame, text="0.0 %", font=("Arial", 14, "bold"))
        self.dash_buf_label.pack(anchor="e", pady=(0, 2))
        self.dash_buf_progress = ctk.CTkProgressBar(self.dash_res_frame, height=12)
        self.dash_buf_progress.pack(fill="x")
        self.dash_buf_progress.set(0)

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

        self.info_gw_label = ctk.CTkLabel(
            self.info_bar_frame,
            text="Gateway：尚未連線",
            font=("Arial", 11), text_color="#aaaaaa", anchor="w"
        )
        self.info_gw_label.grid(row=0, column=0, padx=10, pady=4, sticky="w")

        # 全寬 Table
        self.tables_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.tables_container.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4,10))
        self.tables_container.grid_columnconfigure(0, weight=1)
        self.tables_container.grid_rowconfigure(0, weight=1)

        # 設定自訂 Treeview 樣式
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", borderwidth=0, rowheight=25)
        style.map("Treeview", background=[("selected", "#1f6aa5")])
        style.configure("Treeview.Heading", background="#1f2122", foreground="white", borderwidth=0)

        # 1. 唯一表格：Gateway Logs
        self.gateway_table_frame = ctk.CTkFrame(self.tables_container)
        self.gateway_table_frame.grid(row=0, column=0, sticky="nsew")
        self.gateway_table_frame.grid_rowconfigure(0, weight=0)
        self.gateway_table_frame.grid_rowconfigure(1, weight=1)
        self.gateway_table_frame.grid_columnconfigure(0, weight=1)
        self.gateway_table_frame.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(self.gateway_table_frame, text="Gateway 原始廣播資料流 (USB UART)", font=("Arial", 14, "bold"), text_color="#3a9cd6").grid(row=0, column=0, columnspan=2, pady=5)
        
        self.logs_tree = ttk.Treeview(self.gateway_table_frame, columns=("mac", "rssi", "data", "count", "first_time", "last_time"), show="headings", height=15)
        self.logs_tree.heading("mac",        text="實體 MAC 地址")
        self.logs_tree.heading("rssi",       text="RSSI")
        self.logs_tree.heading("data",       text="廣播數據")
        self.logs_tree.heading("count",      text="次數")
        self.logs_tree.heading("first_time", text="首次發現")
        self.logs_tree.heading("last_time",  text="最後時間")
        self.logs_tree.column("mac",        width=150, anchor="center")
        self.logs_tree.column("rssi",       width=80,  anchor="center")
        self.logs_tree.column("data",       width=250, anchor="center")
        self.logs_tree.column("count",      width=60,  anchor="center")
        self.logs_tree.column("first_time", width=120,  anchor="center")
        self.logs_tree.column("last_time",  width=120,  anchor="center")

        vsb_g = ttk.Scrollbar(self.gateway_table_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=vsb_g.set)
        self.logs_tree.grid(row=1, column=0, sticky="nsew")
        vsb_g.grid(row=1, column=1, sticky="ns")

        # 狀態列
        self.status_bar = ctk.CTkLabel(self, text="就緒", anchor="w", font=("Arial", 11))
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0,5))
        
        # 綁定雙擊事件以開啟歷史紀錄詳細資料
        self.logs_tree.bind("<Double-1>", lambda e: self.show_device_details("gateway"))

        # 初始化掃描
        self.after(100, self.scan_ports)'''

content = re.sub(r'        # ---- 右側面板內容 ----.*?        self\.after\(100, self\.scan_ports\)', ui_replacement, content, flags=re.DOTALL)

with open(r'C:\Users\JOHN_WIESS\.gemini\antigravity-ide\scratch\MedFlow\refactor2.py', 'w', encoding='utf-8') as f:
    f.write(content)

