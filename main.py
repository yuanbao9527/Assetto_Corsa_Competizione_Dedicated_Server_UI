import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import subprocess
import threading
import sys
import time


class ACCServerManager:
    def __init__(self, root):
        self.root = root
        self.root.title("ACC 服务器管理器 V1.0")
        self.root.geometry("1000x900")

        # --- 路径定义 ---
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.cfg_dir = os.path.join(self.base_dir, 'cfg')
        self.presets_dir = os.path.join(self.base_dir, 'presets')
        self.exe_path = os.path.join(self.base_dir, 'accServer.exe')

        if not os.path.exists(self.presets_dir):
            os.makedirs(self.presets_dir)

        # --- 状态变量 ---
        self.server_process = None
        self.is_running = False

        # --- 基础数据 ---
        self.track_list = [
            "monza", "zolder", "brands_hatch", "silverstone", "paul_ricard",
            "misano", "spa", "nurburgring", "barcelona", "hungaroring",
            "zandvoort", "kyalami", "mount_panorama", "suzuka", "laguna_seca",
            "imola", "oulton_park", "donington", "snetterton", "cota",
            "indianapolis", "watkins_glen", "valencia", "nurburgring_24h"
        ]
        self.car_groups = ["FreeForAll (所有车)", "GT3", "GT4", "GT2", "GTC", "TCX"]
        self.days_of_weekend = ["1 - Friday (周五)", "2 - Saturday (周六)", "3 - Sunday (周日)"]
        self.formation_types = ["3 - Default (位置控制+UI)", "0 - Old (旧式限速器)", "1 - Free (自由/手动)"]
        self.server_modes = ["互联网-公开服 (Public)", "互联网-私服 (Private)", "纯局域网模式 (LAN Only)"]

        self.entries_data_list = []
        self.init_variables()
        self.create_tabs()
        self.create_footer()
        self.on_mode_change(None)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_variables(self):
        # 1. 网络
        self.server_mode = tk.StringVar(value=self.server_modes[0])
        self.udp_port = tk.IntVar(value=9201)
        self.tcp_port = tk.IntVar(value=9201)
        self.max_connections = tk.IntVar(value=85)
        self.lan_discovery = tk.IntVar(value=0)
        self.register_to_lobby = tk.IntVar(value=1)
        self.public_ip = tk.StringVar(value="")

        # 2. 常规
        self.server_name = tk.StringVar(value="ACC Server Name")
        self.admin_password = tk.StringVar(value="")
        self.password = tk.StringVar(value="")
        self.spectator_password = tk.StringVar(value="")
        self.car_group = tk.StringVar(value="FreeForAll (所有车)")
        self.track_medals = tk.IntVar(value=0)
        self.safety_rating = tk.IntVar(value=-1)
        self.racecraft_rating = tk.IntVar(value=-1)
        self.max_car_slots = tk.IntVar(value=30)
        self.dump_leaderboards = tk.IntVar(value=1)
        self.randomize_track = tk.IntVar(value=0)
        self.formation_lap_type = tk.StringVar(value=self.formation_types[0])
        self.short_formation_lap = tk.BooleanVar(value=True)
        self.allow_auto_dq = tk.BooleanVar(value=True)

        # 3. 赛事
        self.track = tk.StringVar(value="spa")
        self.pre_race_wait = tk.IntVar(value=120)
        self.session_over_time = tk.IntVar(value=120)
        self.post_qualy_seconds = tk.IntVar(value=30)
        self.post_race_seconds = tk.IntVar(value=60)
        self.ambient_temp = tk.IntVar(value=26)
        self.cloud_level = tk.DoubleVar(value=0.3)
        self.rain_level = tk.DoubleVar(value=0.0)
        self.weather_randomness = tk.IntVar(value=2)

        self.enable_p = tk.BooleanVar(value=True)
        self.day_p = tk.StringVar(value=self.days_of_weekend[0])
        self.hour_p = tk.IntVar(value=10);
        self.dur_p = tk.IntVar(value=20);
        self.mult_p = tk.IntVar(value=1)
        self.enable_q = tk.BooleanVar(value=True)
        self.day_q = tk.StringVar(value=self.days_of_weekend[1])
        self.hour_q = tk.IntVar(value=14);
        self.dur_q = tk.IntVar(value=15);
        self.mult_q = tk.IntVar(value=1)
        self.enable_r = tk.BooleanVar(value=True)
        self.day_r = tk.StringVar(value=self.days_of_weekend[2])
        self.hour_r = tk.IntVar(value=14);
        self.dur_r = tk.IntVar(value=60);
        self.mult_r = tk.IntVar(value=1)

        # 4. 规则
        self.pit_window = tk.IntVar(value=-1)
        self.mandatory_pit_count = tk.IntVar(value=0)
        self.refuelling_allowed = tk.BooleanVar(value=True)
        self.fixed_refuelling_time = tk.BooleanVar(value=False)
        self.mandatory_refuel = tk.BooleanVar(value=False)
        self.mandatory_tyre = tk.BooleanVar(value=False)
        self.qualify_standing_type = tk.IntVar(value=1)

        # 5. 辅助
        self.disable_ideal_line = tk.BooleanVar(value=False)
        self.disable_auto_steer = tk.BooleanVar(value=False)
        self.sc_level_max = tk.IntVar(value=100)
        self.disable_auto_pit = tk.BooleanVar(value=False)

        # 6. 名单
        self.entry_steam_id = tk.StringVar()
        self.entry_first_name = tk.StringVar()
        self.entry_last_name = tk.StringVar()
        self.entry_race_number = tk.IntVar(value=-1)
        self.entry_is_admin = tk.BooleanVar(value=False)
        self.force_entry_list = tk.BooleanVar(value=False)

    def create_tabs(self):
        tab_control = ttk.Notebook(self.root)

        self.tab_console = ttk.Frame(tab_control)
        self.tab_config = ttk.Frame(tab_control)
        self.tab_settings = ttk.Frame(tab_control)
        self.tab_event = ttk.Frame(tab_control)
        self.tab_rules = ttk.Frame(tab_control)
        self.tab_entrylist = ttk.Frame(tab_control)
        self.tab_help = ttk.Frame(tab_control)  # 新增帮助页

        tab_control.add(self.tab_console, text='▶ 控制台')
        tab_control.add(self.tab_config, text='网络')
        tab_control.add(self.tab_settings, text='常规/编队')
        tab_control.add(self.tab_event, text='赛事/天气')
        tab_control.add(self.tab_rules, text='规则/辅助')
        tab_control.add(self.tab_entrylist, text='名单/管理')
        tab_control.add(self.tab_help, text='💡 帮助/说明')  #

        tab_control.pack(expand=1, fill="both", padx=10, pady=10)

        self.build_console_tab()
        self.build_config_tab()
        self.build_settings_tab()
        self.build_event_tab()
        self.build_rules_tab()
        self.build_entrylist_tab()
        self.build_help_tab()  # 构建帮助页

    def create_footer(self):
        footer_frame = ttk.LabelFrame(self.root, text="配置预设管理")
        footer_frame.pack(fill="x", padx=10, pady=10, side="bottom")
        ttk.Button(footer_frame, text="💾 保存当前配置为预设", command=self.save_preset).pack(side="left", padx=20,
                                                                                             pady=10)
        ttk.Button(footer_frame, text="📂 加载预设", command=self.load_preset).pack(side="left", padx=5, pady=10)
        ttk.Label(footer_frame, text="提示: 预设文件保存在 presets 文件夹中。", foreground="gray").pack(side="right",
                                                                                                       padx=20)

        # --- 新增：增强版帮助页面 ---
    def build_help_tab(self):
            # 创建内部标签页，将指南和命令分开
            help_notebook = ttk.Notebook(self.tab_help)
            help_notebook.pack(fill="both", expand=True, padx=5, pady=5)

            tab_guide = ttk.Frame(help_notebook)
            tab_commands = ttk.Frame(help_notebook)

            help_notebook.add(tab_guide, text='📘 服务器完全指南')
            help_notebook.add(tab_commands, text='⚡ 管理员命令大全')

            # --- 1. 服务器完全指南 (Tab 1) ---
            guide_text = """
    【ACC 服务器核心机制解析】

    1. 公开服 vs 私服 (Public vs Private)
    --------------------------------------------------
    - 公开服 (Public MP):
      * 【绝对不能】设置入服密码，否则无法匹配 。
      * 忽略部分规则：公开服会忽略 assistRules.json (辅助限制) 和 eventRules.json (进站规则) 的部分设定，以保证大众体验。
    - 私服 (Private MP):
      * 必须设置 "入服密码"。
      * 允许完全自定义所有规则，包括强制进站、处罚和辅助限制。

    2. 评分与准入限制 (Requirements)
    --------------------------------------------------
    - 赛道奖章 (Track Medals): 设置为 0-3。要求玩家必须熟悉赛道才能进入。
    - 安全评分 (SA): 设置为 -1 (无限制) 或 0-99。建议公开服设置在 40-70 之间以过滤破坏者。
    - 只有在 "名单/管理" 页添加了 SteamID 的玩家可以无视这些限制强制进入。

    3. 天气系统详解 (Weather Simulation)
    --------------------------------------------------
    ACC 的天气由三个核心参数决定：
    - 云量 (Cloud Level): 决定了基础光照，也影响下雨的概率。0.0=晴天，1.0=暴雨云。
    - 降雨量 (Rain): 决定了"如果下雨"时的雨势基准。如果设为 0 但云量很高，可能只是阴天不降雨。
    - 随机性 (Randomness): 
      * 0 = 静态天气 (死板)。
      * 1-4 = 相当真实的变化。
      * 5-7 = 极端变化 (可能突然暴雨)。

    4. 进站规则 (Pitstops)
    --------------------------------------------------
    - 维修窗口 (Pit Window): 比赛中间允许进站的时间段。设置为 -1 关闭。
    - 强制进站 (Mandatory Count): 必须完成的进站次数。
    - 只有在正赛 (Race) 阶段，进站规则才生效。

    5. 常见错误
    --------------------------------------------------
    - 端口冲突: UDP 和 TCP 端口必须在您的路由器/防火墙中开放，且不能被其他软件占用。
    - 赛程配置: 必须至少包含练习赛(P)或排位赛(Q)中的一个，不能只有正赛(R)。
    - 时间倍率: 尽量避免在短比赛中使用过高的时间倍率（如24倍），这会导致天气变化过于剧烈不真实。
    """
            st = scrolledtext.ScrolledText(tab_guide, width=80, height=30, font=("Microsoft YaHei", 10))
            st.pack(fill="both", expand=True, padx=10, pady=10)
            st.insert(tk.END, guide_text)
            st.configure(state='disabled')

            # --- 2. 管理员命令大全 (Tab 2) ---

            # 顶部提示
            info_frame = ttk.Frame(tab_commands)
            info_frame.pack(fill="x", padx=10, pady=5)
            ttk.Label(info_frame, text="如何使用: 在游戏内聊天框输入，需先获取权限。", foreground="blue").pack(anchor="w")
            ttk.Label(info_frame, text="获取权限: 输入 /admin 你的管理员密码 (例如: /admin 123456)",
                      foreground="black").pack(anchor="w")

            # 表格区域
            columns = ("cmd", "params", "desc")
            tree = ttk.Treeview(tab_commands, columns=columns, show="headings", height=15)

            # 定义列
            tree.column("cmd", width=120, anchor="w")
            tree.column("params", width=150, anchor="w")
            tree.column("desc", width=400, anchor="w")

            tree.heading("cmd", text="命令 (Command)")
            tree.heading("params", text="参数")
            tree.heading("desc", text="功能描述")

            tree.pack(fill="both", expand=True, padx=10, pady=5)

            # 滚动条
            scrollbar = ttk.Scrollbar(tab_commands, orient="vertical", command=tree.yview)
            scrollbar.pack(side="right", fill="y")
            tree.configure(yscrollcommand=scrollbar.set)


            # 格式: (命令, 参数, 描述)
            commands_data = [
                ("/admin", "password", "获取管理员权限。成功后会有提示。"),
                ("/next", "无", "立即跳过当前阶段，进入下一阶段 (例如 P->Q)。"),
                ("/restart", "无", "重启当前阶段。请勿在准备阶段使用。"),
                ("/kick", "车号 (RaceNumber)", "踢出指定车号的玩家。直到服务器重启前可重连。"),
                ("/ban", "车号 (RaceNumber)", "封禁指定车号的玩家。直到服务器重启前不可重连。"),
                ("/dq", "车号 (RaceNumber)", "取消资格 (黑旗)。直接传送回维修区并锁定操作。"),
                ("/clear", "车号 (RaceNumber)", "清除该玩家当前的处罚 (如通过维修区、黑旗)。"),
                ("/clear_all", "无", "清除场上所有车辆的所有处罚。"),
                ("/tp5", "车号 (RaceNumber)", "给予 5秒 罚时。(/tp5c 显示'引发碰撞'原因)"),
                ("/tp15", "车号 (RaceNumber)", "给予 15秒 罚时。(/tp15c 显示'引发碰撞'原因)"),
                ("/dt", "车号 (RaceNumber)", "判罚通过维修区 (DriveThrough)。需3圈内执行。"),
                ("/sg10", "车号 (RaceNumber)", "判罚 10秒 停站 (Stop&Go)。"),
                ("/sg20", "车号 (RaceNumber)", "判罚 20秒 停站 (Stop&Go)。"),
                ("/sg30", "车号 (RaceNumber)", "判罚 30秒 停站 (Stop&Go)。"),
                ("/ballast", "车号 kg(0-100)", "设置BOP负重。例: /ballast 113 15 (给113号车加15kg)。"),
                ("/restrictor", "车号 %(0-20)", "设置进气限制。例: /restrictor 113 5 (限制5%动力)。"),
                ("/manual entrylist", "无", "在 cfg 目录下生成当前在线玩家的 entrylist 文件。"),
            ]

            # 插入数据
            for item in commands_data:
                tree.insert("", "end", values=item)

    # --- 1. 控制台 ---
    def build_console_tab(self):
        ctrl_frame = ttk.LabelFrame(self.tab_console, text="运行控制")
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        self.status_label = ttk.Label(ctrl_frame, text="状态: 已停止", foreground="red", font=("Arial", 12, "bold"))
        self.status_label.pack(side="left", padx=20)
        self.btn_start = ttk.Button(ctrl_frame, text="启动服务器", command=self.start_server)
        self.btn_start.pack(side="left", padx=5)
        self.btn_stop = ttk.Button(ctrl_frame, text="停止服务器", command=self.stop_server, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # 修改按钮文字
        ttk.Button(ctrl_frame, text="仅生成配置 (不启动)", command=self.generate_files_silent).pack(side="right",
                                                                                                    padx=20)

        log_frame = ttk.LabelFrame(self.tab_console, text="实时日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.console_text = tk.Text(log_frame, bg="black", fg="white", font=("Consolas", 9), state="disabled")
        self.console_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.console_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.console_text.config(yscrollcommand=scrollbar.set)
        self.console_text.tag_config("info", foreground="lightgreen")
        self.console_text.tag_config("error", foreground="red")

    # --- 2. 网络 ---
    def build_config_tab(self):
        frame = ttk.LabelFrame(self.tab_config, text="服务器模式")
        frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame, text="选择模式 (自动锁定选项):").pack(anchor="w", padx=10, pady=(10, 0))
        mode_cb = ttk.Combobox(frame, values=self.server_modes, textvariable=self.server_mode, state="readonly",
                               width=40)
        mode_cb.pack(anchor="w", padx=10, pady=5)
        mode_cb.bind("<<ComboboxSelected>>", self.on_mode_change)

        details_frame = ttk.LabelFrame(self.tab_config, text="详细网络参数")
        details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_entry(details_frame, "UDP 端口:", self.udp_port)
        self.create_entry(details_frame, "TCP 端口:", self.tcp_port)
        self.create_entry(details_frame, "Public IP (选填):", self.public_ip)
        self.create_entry(details_frame, "最大连接数:", self.max_connections)

        status_frame = ttk.Frame(details_frame)
        status_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(status_frame, text="当前模式状态:").pack(side="left")
        self.chk_lan = ttk.Checkbutton(status_frame, text="局域网发现", variable=self.lan_discovery, state="disabled")
        self.chk_lan.pack(side="left", padx=10)
        self.chk_lobby = ttk.Checkbutton(status_frame, text="注册到大厅", variable=self.register_to_lobby,
                                         state="disabled")
        self.chk_lobby.pack(side="left", padx=10)

    def on_mode_change(self, event):
        mode = self.server_mode.get()
        if mode == "互联网-公开服 (Public)":
            self.register_to_lobby.set(1);
            self.lan_discovery.set(0)
            self.password.set("");
            if hasattr(self, 'pw_row_frame'): self.pw_row_frame.pack_forget()
        elif mode == "互联网-私服 (Private)":
            self.register_to_lobby.set(1);
            self.lan_discovery.set(0)
            if hasattr(self, 'pw_row_frame'): self.pw_row_frame.pack(fill="x", padx=10, pady=2,
                                                                     after=self.admin_pw_frame)
        elif mode == "纯局域网模式 (LAN Only)":
            self.register_to_lobby.set(0);
            self.lan_discovery.set(1)
            if hasattr(self, 'pw_row_frame'): self.pw_row_frame.pack(fill="x", padx=10, pady=2,
                                                                     after=self.admin_pw_frame)

    # --- 3. 设置 ---
    def build_settings_tab(self):
        frame = ttk.LabelFrame(self.tab_settings, text="常规设置")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_entry(frame, "服务器名称:", self.server_name)
        self.admin_pw_frame = self.create_entry(frame, "管理员密码:", self.admin_password)
        self.pw_row_frame = self.create_entry(frame, "入服密码:", self.password)
        self.create_entry(frame, "观战密码:", self.spectator_password)
        ttk.Label(frame, text="允许车型:").pack(anchor="w", padx=10)
        ttk.Combobox(frame, values=self.car_groups, textvariable=self.car_group, state="readonly").pack(fill="x",padx=10)
        req_frame = ttk.Frame(frame);
        req_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(req_frame, text="SA要求:").pack(side="left");
        ttk.Entry(req_frame, textvariable=self.safety_rating, width=5).pack(side="left")
        ttk.Label(req_frame, text=" 奖章:").pack(side="left");
        ttk.Entry(req_frame, textvariable=self.track_medals, width=5).pack(side="left")
        ttk.Label(req_frame, text=" 车位:").pack(side="left");
        ttk.Entry(req_frame, textvariable=self.max_car_slots, width=5).pack(side="left")
        ttk.Checkbutton(frame, text="保存排行榜", variable=self.dump_leaderboards).pack(anchor="w", padx=10)
        ttk.Checkbutton(frame, text="自动DQ", variable=self.allow_auto_dq).pack(anchor="w", padx=10)
        form_frame = ttk.LabelFrame(self.tab_settings, text="编队圈")
        form_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(form_frame, text="类型:").pack(side="left", padx=5)
        ttk.Combobox(form_frame, values=self.formation_types, textvariable=self.formation_lap_type, state="readonly",
                     width=30).pack(side="left", padx=5)
        ttk.Checkbutton(form_frame, text="短编队圈", variable=self.short_formation_lap).pack(side="left", padx=10)

    # --- 4. 赛事 ---
    def build_event_tab(self):
        frame_env = ttk.LabelFrame(self.tab_event, text="环境与天气")
        frame_env.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame_env, text="赛道:").pack(side="left", padx=5)
        ttk.Combobox(frame_env, values=self.track_list, textvariable=self.track, state="readonly", width=20).pack(
            side="left")
        time_frame = ttk.Frame(frame_env);
        time_frame.pack(side="left", padx=20)
        ttk.Label(time_frame, text="赛前等待:").pack(side="left");
        ttk.Entry(time_frame, textvariable=self.pre_race_wait, width=4).pack(side="left")
        ttk.Label(time_frame, text=" 排位缓冲:").pack(side="left");
        ttk.Entry(time_frame, textvariable=self.post_qualy_seconds, width=4).pack(side="left")
        ttk.Label(time_frame, text=" 正赛缓冲:").pack(side="left");
        ttk.Entry(time_frame, textvariable=self.post_race_seconds, width=4).pack(side="left")
        weather_frame = ttk.LabelFrame(self.tab_event, text="天气参数")
        weather_frame.pack(fill="x", padx=10, pady=5)
        self.create_scale(weather_frame, "环境温度", self.ambient_temp, 10, 35)
        self.create_scale(weather_frame, "云量", self.cloud_level, 0.0, 1.0, 0.01)
        self.create_scale(weather_frame, "降雨量", self.rain_level, 0.0, 1.0, 0.01)
        self.create_scale(weather_frame, "随机性", self.weather_randomness, 0, 7)
        frame_sess = ttk.LabelFrame(self.tab_event, text="赛程安排")
        frame_sess.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_session_row(frame_sess, "练习赛 (P)", self.enable_p, self.day_p, self.hour_p, self.dur_p,
                                self.mult_p)
        self.create_session_row(frame_sess, "排位赛 (Q)", self.enable_q, self.day_q, self.hour_q, self.dur_q,
                                self.mult_q)
        self.create_session_row(frame_sess, "正赛 (R)", self.enable_r, self.day_r, self.hour_r, self.dur_r, self.mult_r)

    def create_session_row(self, parent, title, var_enable, var_day, var_hour, var_dur, var_mult):
        row = ttk.Frame(parent);
        row.pack(fill="x", padx=5, pady=5)
        ttk.Checkbutton(row, text=title, variable=var_enable, width=15).pack(side="left")
        ttk.Label(row, text="日期:").pack(side="left");
        ttk.Combobox(row, values=self.days_of_weekend, textvariable=var_day, state="readonly", width=12).pack(
            side="left")
        ttk.Label(row, text="开始时间:").pack(side="left");
        ttk.Spinbox(row, from_=0, to=23, textvariable=var_hour, width=3).pack(side="left")
        ttk.Label(row, text="时长:").pack(side="left");
        ttk.Entry(row, textvariable=var_dur, width=4).pack(side="left")
        ttk.Label(row, text="倍率:").pack(side="left", padx=(10, 0))

        def update_val(val): var_mult.set(int(float(val)))

        scale = ttk.Scale(row, from_=1, to=24, variable=var_mult, orient="horizontal", length=80, command=update_val)
        scale.pack(side="left")
        ttk.Label(row, textvariable=var_mult, width=3, foreground="blue").pack(side="left", padx=2)
        ttk.Label(row, text="x").pack(side="left")

    # --- 5. 规则 ---
    def build_rules_tab(self):
        frame = ttk.LabelFrame(self.tab_rules, text="规则与辅助")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        pit_frame = ttk.LabelFrame(frame, text="进站规则");
        pit_frame.pack(fill="x", padx=5, pady=5)
        self.create_entry(pit_frame, "维修窗口 (-1关):", self.pit_window)
        self.create_entry(pit_frame, "强制进站次数:", self.mandatory_pit_count)
        sub = ttk.Frame(pit_frame);
        sub.pack(fill="x")
        ttk.Checkbutton(sub, text="允许加油", variable=self.refuelling_allowed).pack(side="left", padx=10)
        ttk.Checkbutton(sub, text="强制加油", variable=self.mandatory_refuel).pack(side="left", padx=10)
        ttk.Checkbutton(sub, text="强制换胎", variable=self.mandatory_tyre).pack(side="left", padx=10)
        ttk.Checkbutton(sub, text="固定加油时间", variable=self.fixed_refuelling_time).pack(side="left", padx=10)
        assist_frame = ttk.LabelFrame(frame, text="辅助限制");
        assist_frame.pack(fill="x", padx=5, pady=10)
        ttk.Checkbutton(assist_frame, text="禁用最佳路线", variable=self.disable_ideal_line).pack(anchor="w", padx=10)
        ttk.Checkbutton(assist_frame, text="禁用自动转向", variable=self.disable_auto_steer).pack(anchor="w", padx=10)
        ttk.Checkbutton(assist_frame, text="禁用自动维修限速", variable=self.disable_auto_pit).pack(anchor="w", padx=10)
        self.create_scale(assist_frame, "SC 限制", self.sc_level_max, 0, 100)

    # --- 6. 名单 ---
    def build_entrylist_tab(self):
        info_frame = ttk.Frame(self.tab_entrylist);
        info_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(info_frame, text="提示: 在此添加的玩家可无视满员进入服务器。勾选管理员则拥有权限，且无需再手动设置成为管理员。",
                  foreground="blue").pack(anchor="w")
        ttk.Checkbutton(info_frame, text="强制名单 (仅名单内玩家可进)", variable=self.force_entry_list).pack(anchor="w")
        input_frame = ttk.LabelFrame(self.tab_entrylist, text="添加玩家");
        input_frame.pack(fill="x", padx=10, pady=5)
        row1 = ttk.Frame(input_frame);
        row1.pack(fill="x", padx=5, pady=5)
        ttk.Label(row1, text="Steam ID:").pack(side="left");
        ttk.Entry(row1, textvariable=self.entry_steam_id, width=20).pack(side="left", padx=5)
        ttk.Label(row1, text="车号:").pack(side="left");
        ttk.Entry(row1, textvariable=self.entry_race_number, width=5).pack(side="left", padx=5)
        row2 = ttk.Frame(input_frame);
        row2.pack(fill="x", padx=5, pady=5)
        ttk.Label(row2, text="名:").pack(side="left");
        ttk.Entry(row2, textvariable=self.entry_first_name, width=8).pack(side="left", padx=5)
        ttk.Label(row2, text="姓:").pack(side="left");
        ttk.Entry(row2, textvariable=self.entry_last_name, width=8).pack(side="left", padx=5)
        ttk.Checkbutton(row2, text="管理员", variable=self.entry_is_admin).pack(side="left", padx=20)
        ttk.Button(input_frame, text="添加", command=self.add_entry).pack(fill="x", padx=5)
        list_frame = ttk.LabelFrame(self.tab_entrylist, text="列表");
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("steam_id", "name", "number", "admin")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        self.tree.heading("steam_id", text="ID");
        self.tree.heading("name", text="姓名")
        self.tree.heading("number", text="No.");
        self.tree.heading("admin", text="Admin")
        self.tree.pack(side="left", fill="both", expand=True)
        ttk.Button(self.tab_entrylist, text="删除选中", command=self.delete_entry).pack(fill="x", padx=10, pady=5)

    def add_entry(self):
        sid = self.entry_steam_id.get().strip()
        if not sid: return
        entry = {"playerID": sid, "firstName": self.entry_first_name.get(), "lastName": self.entry_last_name.get(),
                 "raceNumber": self.entry_race_number.get(), "isServerAdmin": 1 if self.entry_is_admin.get() else 0,
                 "overrideDriverInfo": 1 if self.entry_first_name.get() else 0}
        self.entries_data_list.append(entry)
        self.tree.insert("", "end", values=(sid, f"{entry['firstName']} {entry['lastName']}", entry['raceNumber'],
                                            "是" if entry['isServerAdmin'] else "否"))
        self.entry_steam_id.set("")

    def delete_entry(self):
        sel = self.tree.selection()
        if sel: del self.entries_data_list[self.tree.index(sel[0])]; self.tree.delete(sel[0])

    # --- 辅助 ---
    def create_entry(self, parent, label_text, variable, show=None):
        frame = ttk.Frame(parent);
        frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(frame, text=label_text, width=30).pack(side="left")
        ttk.Entry(frame, textvariable=variable, show=show).pack(side="right", fill="x", expand=True)
        return frame

    def create_scale(self, parent, label, variable, from_, to, resolution=1):
        frame = ttk.Frame(parent);
        frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(frame, text=label).pack(side="top", anchor="w")
        ttk.Scale(frame, from_=from_, to=to, variable=variable, orient="horizontal",
                  command=lambda x: variable.set(float(x) if resolution < 1 else int(float(x)))).pack(fill="x")
        ttk.Label(frame, textvariable=variable).pack(side="right")

    def log(self, message, level="normal"):
        self.console_text.config(state="normal")
        tag = level if level in ["info", "error"] else ""
        self.console_text.insert(tk.END, f"[System] {message}\n", tag)
        self.console_text.see(tk.END)
        self.console_text.config(state="disabled")

    # --- 逻辑 ---
    def start_server(self):
        if self.is_running: return
        if not os.path.exists(self.exe_path):
            messagebox.showerror("错误", f"找不到 {self.exe_path}")
            return
        try:
            if not self.generate_files_silent(show_success=False): return
            self.log("配置文件已更新", "info")
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.server_process = subprocess.Popen(
                [self.exe_path], cwd=self.base_dir,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE,
                universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                startupinfo=startupinfo, encoding='utf-8', errors='replace'
            )
            self.is_running = True
            self.status_label.config(text="状态: 运行中", foreground="green")
            self.btn_start.config(state="disabled");
            self.btn_stop.config(state="normal")
            self.log("正在启动 accServer.exe...", "info")
            threading.Thread(target=self.read_process_output, daemon=True).start()
        except Exception as e:
            self.log(f"启动失败: {str(e)}", "error")

    def read_process_output(self):
        while self.is_running and self.server_process:
            try:
                line = self.server_process.stdout.readline()
                if not line and self.server_process.poll() is not None: break
                if line: self.root.after(0, lambda l=line: self.log(l.strip()))
            except Exception:
                break
        self.is_running = False
        self.root.after(0, lambda: self.status_label.config(text="状态: 已停止", foreground="red"))
        self.root.after(0, lambda: self.btn_start.config(state="normal"))
        self.root.after(0, lambda: self.btn_stop.config(state="disabled"))
        self.root.after(0, lambda: self.log("服务器进程已退出。", "info"))

    def stop_server(self):
        if self.server_process and self.is_running:
            self.log("正在停止服务器...", "info")
            self.server_process.terminate()

    def on_close(self):
        if self.is_running:
            if messagebox.askokcancel("退出", "服务器正在运行，确定要关闭并退出吗？"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()

    def generate_files_silent(self, show_success=True):
        if not os.path.exists(self.cfg_dir):
            try:
                os.makedirs(self.cfg_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建目录: {e}"); return False

        if not (self.enable_p.get() or self.enable_q.get() or self.enable_r.get()):
            messagebox.showerror("配置错误", "至少需要启用一个阶段");
            return False
        if self.enable_r.get() and not (self.enable_p.get() or self.enable_q.get()):

            messagebox.showerror("配置错误", "正赛必须搭配P或Q");
            return False
        if self.server_mode.get() == "互联网-私服 (Private)" and not self.password.get():

            messagebox.showerror("配置错误", "私服必须设置密码");
            return False

        config_data = {
            "udpPort": self.udp_port.get(), "tcpPort": self.tcp_port.get(),
            "maxConnections": self.max_connections.get(),
            "lanDiscovery": self.lan_discovery.get(), "registerToLobby": self.register_to_lobby.get(),
            "configVersion": 1
        }
        if self.public_ip.get().strip(): config_data["publicIP"] = self.public_ip.get().strip()

        form_type_val = int(self.formation_lap_type.get().split(" - ")[0])
        settings_data = {
            "serverName": self.server_name.get(), "adminPassword": self.admin_password.get(),
            "carGroup": self.car_group.get().split(" ")[0], "trackMedalsRequirement": self.track_medals.get(),
            "safetyRatingRequirement": self.safety_rating.get(),
            "racecraftRatingRequirement": self.racecraft_rating.get(),
            "password": self.password.get(), "spectatorPassword": self.spectator_password.get(),
            "maxCarSlots": self.max_car_slots.get(), "dumpLeaderboards": self.dump_leaderboards.get(),
            "randomizeTrackWhenEmpty": self.randomize_track.get(), "centralEntryListPath": "",
            "allowAutoDQ": 1 if self.allow_auto_dq.get() else 0,
            "shortFormationLap": 1 if self.short_formation_lap.get() else 0,
            "dumpEntryList": 1, "formationLapType": form_type_val, "configVersion": 1
        }
        sessions_list = []

        def add_s(en, d, h, du, mu, t):
            if en: sessions_list.append(
                {"hourOfDay": h, "dayOfWeekend": int(d.split(" - ")[0]), "timeMultiplier": mu, "sessionType": t,
                 "sessionDurationMinutes": du})

        add_s(self.enable_p.get(), self.day_p.get(), self.hour_p.get(), self.dur_p.get(), self.mult_p.get(), "P")
        add_s(self.enable_q.get(), self.day_q.get(), self.hour_q.get(), self.dur_q.get(), self.mult_q.get(), "Q")
        add_s(self.enable_r.get(), self.day_r.get(), self.hour_r.get(), self.dur_r.get(), self.mult_r.get(), "R")

        event_data = {
            "track": self.track.get(), "preRaceWaitingTimeSeconds": self.pre_race_wait.get(),
            "sessionOverTimeSeconds": self.session_over_time.get(), "ambientTemp": self.ambient_temp.get(),
            "cloudLevel": round(self.cloud_level.get(), 2), "rain": round(self.rain_level.get(), 2),
            "weatherRandomness": self.weather_randomness.get(), "postQualySeconds": self.post_qualy_seconds.get(),
            "postRaceSeconds": self.post_race_seconds.get(), "configVersion": 1, "sessions": sessions_list
        }
        rules_data = {
            "qualifyStandingType": self.qualify_standing_type.get(), "pitWindowLengthSec": self.pit_window.get(),
            "driverStintTimeSec": -1,
            "mandatoryPitstopCount": self.mandatory_pit_count.get(), "maxTotalDrivingTime": -1, "maxDriversCount": 1,
            "isRefuellingAllowedInRace": self.refuelling_allowed.get(),
            "isRefuellingTimeFixed": self.fixed_refuelling_time.get(),
            "isMandatoryPitstopRefuellingRequired": self.mandatory_refuel.get(),
            "isMandatoryPitstopTyreChangeRequired": self.mandatory_tyre.get(),
            "isMandatoryPitstopSwapDriverRequired": False, "tyreSetCount": 50
        }
        assist_data = {
            "stabilityControlLevelMax": self.sc_level_max.get(),
            "disableAutosteer": 1 if self.disable_auto_steer.get() else 0,
            "disableAutoLights": 0, "disableAutoWiper": 0, "disableAutoEngineStart": 0,
            "disableAutoPitLimiter": 1 if self.disable_auto_pit.get() else 0,
            "disableAutoGear": 0, "disableAutoClutch": 0, "disableIdealLine": 1 if self.disable_ideal_line.get() else 0
        }
        entries = []
        for e in self.entries_data_list:
            sid = e['playerID'];
            if not sid.startswith("S"): sid = "S" + sid
            entries.append({
                "drivers": [
                    {"playerID": sid, "firstName": e['firstName'], "lastName": e['lastName'], "driverCategory": 0}],
                "raceNumber": e['raceNumber'], "forcedCarModel": -1, "overrideDriverInfo": e['overrideDriverInfo'],
                "isServerAdmin": e['isServerAdmin'], "defaultGridPosition": -1, "ballastKg": 0, "restrictor": 0
            })
        entry_data = {"entries": entries, "forceEntryList": 1 if self.force_entry_list.get() else 0}

        try:
            self.save_json("configuration.json", config_data)
            self.save_json("settings.json", settings_data)
            self.save_json("event.json", event_data)
            self.save_json("eventRules.json", rules_data)
            self.save_json("assistRules.json", assist_data)
            self.save_json("entrylist.json", entry_data)
            if show_success:
                messagebox.showinfo("成功", f"配置文件已更新至:\n{self.cfg_dir}")
                self.log("配置文件生成成功", "info")
            return True
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return False

    def save_json(self, filename, data):
        path = os.path.join(self.cfg_dir, filename)
        with open(path, 'w', encoding='utf-16-le') as f: json.dump(data, f, indent=4)

    def save_preset(self):
        file_path = filedialog.asksaveasfilename(initialdir=self.presets_dir, title="保存预设",
                                                 filetypes=[("JSON", "*.json")], defaultextension=".json")
        if not file_path: return
        data = {
            "server_mode": self.server_mode.get(), "udp_port": self.udp_port.get(), "tcp_port": self.tcp_port.get(),
            "max_connections": self.max_connections.get(), "public_ip": self.public_ip.get(),
            "server_name": self.server_name.get(), "admin_password": self.admin_password.get(),
            "password": self.password.get(), "spectator_password": self.spectator_password.get(),
            "car_group": self.car_group.get(), "track_medals": self.track_medals.get(),
            "safety_rating": self.safety_rating.get(), "racecraft_rating": self.racecraft_rating.get(),
            "max_car_slots": self.max_car_slots.get(), "dump_leaderboards": self.dump_leaderboards.get(),
            "randomize_track": self.randomize_track.get(), "formation_lap_type": self.formation_lap_type.get(),
            "short_formation_lap": self.short_formation_lap.get(), "allow_auto_dq": self.allow_auto_dq.get(),
            "track": self.track.get(), "pre_race_wait": self.pre_race_wait.get(),
            "session_over_time": self.session_over_time.get(), "post_qualy_seconds": self.post_qualy_seconds.get(),
            "post_race_seconds": self.post_race_seconds.get(), "ambient_temp": self.ambient_temp.get(),
            "cloud_level": self.cloud_level.get(), "rain_level": self.rain_level.get(),
            "weather_randomness": self.weather_randomness.get(),
            "enable_p": self.enable_p.get(), "day_p": self.day_p.get(), "hour_p": self.hour_p.get(),
            "dur_p": self.dur_p.get(), "mult_p": self.mult_p.get(),
            "enable_q": self.enable_q.get(), "day_q": self.day_q.get(), "hour_q": self.hour_q.get(),
            "dur_q": self.dur_q.get(), "mult_q": self.mult_q.get(),
            "enable_r": self.enable_r.get(), "day_r": self.day_r.get(), "hour_r": self.hour_r.get(),
            "dur_r": self.dur_r.get(), "mult_r": self.mult_r.get(),
            "pit_window": self.pit_window.get(), "mandatory_pit_count": self.mandatory_pit_count.get(),
            "refuelling_allowed": self.refuelling_allowed.get(),
            "fixed_refuelling_time": self.fixed_refuelling_time.get(),
            "mandatory_refuel": self.mandatory_refuel.get(), "mandatory_tyre": self.mandatory_tyre.get(),
            "qualify_standing_type": self.qualify_standing_type.get(),
            "disable_ideal_line": self.disable_ideal_line.get(), "disable_auto_steer": self.disable_auto_steer.get(),
            "sc_level_max": self.sc_level_max.get(), "disable_auto_pit": self.disable_auto_pit.get(),
            "force_entry_list": self.force_entry_list.get(), "entries_data_list": self.entries_data_list
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("成功", f"预设已保存: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def load_preset(self):
        file_path = filedialog.askopenfilename(initialdir=self.presets_dir, title="加载预设",
                                               filetypes=[("JSON", "*.json")])
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.server_mode.set(data.get("server_mode", self.server_modes[0]));
            self.on_mode_change(None)
            self.udp_port.set(data.get("udp_port", 9201));
            self.tcp_port.set(data.get("tcp_port", 9201))
            self.max_connections.set(data.get("max_connections", 85));
            self.public_ip.set(data.get("public_ip", ""))
            self.server_name.set(data.get("server_name", "ACC"));
            self.admin_password.set(data.get("admin_password", ""))
            self.password.set(data.get("password", ""));
            self.spectator_password.set(data.get("spectator_password", ""))
            self.car_group.set(data.get("car_group", "FreeForAll"));
            self.track_medals.set(data.get("track_medals", 0))
            self.safety_rating.set(data.get("safety_rating", -1));
            self.racecraft_rating.set(data.get("racecraft_rating", -1))
            self.max_car_slots.set(data.get("max_car_slots", 30));
            self.dump_leaderboards.set(data.get("dump_leaderboards", 1))
            self.randomize_track.set(data.get("randomize_track", 0));
            self.formation_lap_type.set(data.get("formation_lap_type", self.formation_types[0]))
            self.short_formation_lap.set(data.get("short_formation_lap", True));
            self.allow_auto_dq.set(data.get("allow_auto_dq", True))
            self.track.set(data.get("track", "spa"));
            self.pre_race_wait.set(data.get("pre_race_wait", 120))
            self.session_over_time.set(data.get("session_over_time", 120));
            self.post_qualy_seconds.set(data.get("post_qualy_seconds", 30))
            self.post_race_seconds.set(data.get("post_race_seconds", 60));
            self.ambient_temp.set(data.get("ambient_temp", 26))
            self.cloud_level.set(data.get("cloud_level", 0.3));
            self.rain_level.set(data.get("rain_level", 0.0))
            self.weather_randomness.set(data.get("weather_randomness", 2))
            self.enable_p.set(data.get("enable_p", True));
            self.day_p.set(data.get("day_p", self.days_of_weekend[0]))
            self.hour_p.set(data.get("hour_p", 10));
            self.dur_p.set(data.get("dur_p", 20));
            self.mult_p.set(data.get("mult_p", 1))
            self.enable_q.set(data.get("enable_q", True));
            self.day_q.set(data.get("day_q", self.days_of_weekend[1]))
            self.hour_q.set(data.get("hour_q", 14));
            self.dur_q.set(data.get("dur_q", 15));
            self.mult_q.set(data.get("mult_q", 1))
            self.enable_r.set(data.get("enable_r", True));
            self.day_r.set(data.get("day_r", self.days_of_weekend[2]))
            self.hour_r.set(data.get("hour_r", 14));
            self.dur_r.set(data.get("dur_r", 60));
            self.mult_r.set(data.get("mult_r", 1))
            self.pit_window.set(data.get("pit_window", -1));
            self.mandatory_pit_count.set(data.get("mandatory_pit_count", 0))
            self.refuelling_allowed.set(data.get("refuelling_allowed", True));
            self.fixed_refuelling_time.set(data.get("fixed_refuelling_time", False))
            self.mandatory_refuel.set(data.get("mandatory_refuel", False));
            self.mandatory_tyre.set(data.get("mandatory_tyre", False))
            self.qualify_standing_type.set(data.get("qualify_standing_type", 1))
            self.disable_ideal_line.set(data.get("disable_ideal_line", False));
            self.disable_auto_steer.set(data.get("disable_auto_steer", False))
            self.sc_level_max.set(data.get("sc_level_max", 100));
            self.disable_auto_pit.set(data.get("disable_auto_pit", False))
            self.force_entry_list.set(data.get("force_entry_list", False))
            self.entries_data_list = data.get("entries_data_list", [])
            for item in self.tree.get_children(): self.tree.delete(item)
            for entry in self.entries_data_list:
                sid = entry['playerID'];
                name = f"{entry['firstName']} {entry['lastName']}";
                admin = "是" if entry['isServerAdmin'] else "否"
                self.tree.insert("", "end", values=(sid, name, entry['raceNumber'], admin))
            #messagebox.showinfo("成功", f"预设已加载: {os.path.basename(file_path)}")
            self.log(f"已加载配置预设: {os.path.basename(file_path)}", "info")
        except Exception as e:
            messagebox.showerror("加载失败", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = ACCServerManager(root)
    root.mainloop()
