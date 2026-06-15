import os
import json
import subprocess
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 配置文件将安全地保存在你系统的用户目录下
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "claude_launcher_config.json")

def get_sessions_for_project(project_path):
    """
    终极版：全盘全局雷达
    直接无视官方复杂的项目绑定逻辑，扫描整个系统底层的聊天记录！
    """
    claude_dir = os.path.join(os.path.expanduser("~"), ".claude")
    sessions = []
    
    if not os.path.exists(claude_dir):
        return []
        
    all_files = []
    # 1. 暴力递归扫描 .claude 下所有的 .jsonl 记录文件
    for root, dirs, files in os.walk(claude_dir):
        # 跳过无关的缓存目录，加快秒开速度
        if "cache" in root or "backups" in root or "shell-snapshots" in root or "session-env" in root:
            continue
        for file in files:
            if file.endswith(".jsonl") and file != "history.jsonl":
                all_files.append(os.path.join(root, file))
                
    # 2. 逐个解析文件的最后修改时间，并提取聊天内容作为标题
    for file_path in all_files:
        sess_id = os.path.basename(file_path).replace(".jsonl", "")
        try:
            mtime = os.path.getmtime(file_path)
        except:
            continue
            
        time_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        title = "未命名会话"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        msg = json.loads(line)
                        # 找到你发给 AI 的第一句话
                        if msg.get("type") == "message" and msg.get("role") == "user":
                            content = msg.get("content", "")
                            if isinstance(content, list):
                                text_blocks = [b.get("text") for b in content if b.get("type") == "text"]
                                content = " ".join(text_blocks)
                            if isinstance(content, str) and content.strip():
                                title = content.strip()[:35] + ("..." if len(content.strip()) > 35 else "")
                                break
                    except:
                        continue
        except Exception:
            pass
            
        sessions.append({
            "id": sess_id,
            "title": title,
            "time": time_str,
            "mtime": mtime
        })
        
    # 3. 按时间从最新到最旧排序，返回最近的 30 条全局聊天记录
    sessions.sort(key=lambda x: x["mtime"], reverse=True)
    return sessions[:30]
    
    """
    全自动解析算法：
    自动在 ~/.claude/projects/ 目录下寻找当前项目对应的 Claude 历史会话。
    提取每个会话的 UUID、修改时间以及第一条用户消息作为标题。
    """
    project_path = os.path.abspath(project_path)
    projects_dir = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.exists(projects_dir):
        return []
    
    target_project_dir = None
    
    # 策略 1：扫描所有项目目录下的 sessions-index.json，进行精确路径匹配
    for folder in os.listdir(projects_dir):
        folder_path = os.path.join(projects_dir, folder)
        if not os.path.isdir(folder_path):
            continue
            
        index_file = os.path.join(folder_path, "sessions-index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
                    orig_path = index_data.get("originalPath") or index_data.get("projectPath")
                    if orig_path and os.path.abspath(orig_path).lower() == project_path.lower():
                        target_project_dir = folder_path
                        break
            except Exception:
                pass

    # 策略 2：根据 Claude 转换规则进行备用模糊匹配
    if not target_project_dir:
        # D:\2.Web3\2.社媒\个人主页 -> D--2.Web3-2.社媒-个人主页
        base_encoded = project_path.replace(":\\", "--").replace("\\", "-").replace("/", "-")
        # 兼容部分中文路径会被替换为 - 的特殊版本
        non_ascii_encoded = "".join("-" if ord(c) > 127 else c for c in base_encoded)
        
        for folder in os.listdir(projects_dir):
            if folder.lower() in (base_encoded.lower(), non_ascii_encoded.lower()):
                target_project_dir = os.path.join(projects_dir, folder)
                break

    if not target_project_dir:
        return []
        
    sessions = []
    
    # 优先解析官方的 sessions-index.json
    index_file = os.path.join(target_project_dir, "sessions-index.json")
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                entries = index_data.get("entries", [])
                for entry in entries:
                    sess_id = entry.get("id") or entry.get("sessionId")
                    title = entry.get("title") or entry.get("summary") or entry.get("prompt") or "未命名会话"
                    mtime = entry.get("updatedAt") or entry.get("mtime") or ""
                    if sess_id:
                        sessions.append({
                            "id": sess_id,
                            "title": title,
                            "time": mtime
                        })
        except Exception:
            pass
            
    # 如果索引解析为空，直接物理扫描文件并解析首条消息作为标题
    if not sessions:
        candidate_paths = [target_project_dir, os.path.join(target_project_dir, "sessions")]
        for p in candidate_paths:
            if os.path.exists(p) and os.path.isdir(p):
                for file in os.listdir(p):
                    if file.endswith(".jsonl"):
                        file_path = os.path.join(p, file)
                        sess_id = file[:-6] # 移除 .jsonl
                        
                        mtime_epoch = os.path.getmtime(file_path)
                        mtime_str = datetime.datetime.fromtimestamp(mtime_epoch).strftime('%Y-%m-%d %H:%M')
                        
                        title = "未命名会话"
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                for line in f:
                                    msg = json.loads(line)
                                    if msg.get("type") == "message" and msg.get("role") == "user":
                                        content = msg.get("content", "")
                                        if isinstance(content, list):
                                            text_blocks = [b.get("text") for b in content if b.get("type") == "text"]
                                            content = " ".join(text_blocks)
                                        if isinstance(content, str) and content.strip():
                                            title = content.strip()[:35] + ("..." if len(content.strip()) > 35 else "")
                                            break
                        except Exception:
                            pass
                            
                        if not any(s["id"] == sess_id for s in sessions):
                            sessions.append({
                                "id": sess_id,
                                "title": title,
                                "time": mtime_str
                            })
                            
    # 按照时间从新到旧排序
    try:
        sessions.sort(key=lambda x: x.get("time", ""), reverse=True)
    except Exception:
        pass
        
    return sessions

class ClaudeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Code 桌面轻量启动器")
        self.root.geometry("520x590")
        
        # 加载配置
        self.config = self.load_config()
        self.current_sessions = []
        
        # UI 绑定变量
        self.api_name_var = tk.StringVar()
        self.api_url_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.project_path_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="normal")
        
        self.create_widgets()
        self.update_api_list()
        self.update_project_list()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"apis": {}, "projects": []}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def create_widgets(self):
        # 1. API 配置
        api_frame = ttk.LabelFrame(self.root, text=" 1. API 账号配置与选择 ", padding=10)
        api_frame.pack(fill="x", padx=15, pady=5)
        
        ttk.Label(api_frame, text="快速切换账号:").grid(row=0, column=0, sticky="w", pady=2)
        self.api_cb = ttk.Combobox(api_frame, state="readonly")
        self.api_cb.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)
        self.api_cb.bind("<<ComboboxSelected>>", self.on_api_selected)
        
        ttk.Label(api_frame, text="API 别名:").grid(row=1, column=0, sticky="w", pady=2)
        self.api_name_entry = ttk.Entry(api_frame, textvariable=self.api_name_var)
        self.api_name_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=2)
        
        ttk.Label(api_frame, text="接口地址 (Base URL):").grid(row=2, column=0, sticky="w", pady=2)
        self.api_url_entry = ttk.Entry(api_frame, textvariable=self.api_url_var)
        self.api_url_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=2)
        
        ttk.Label(api_frame, text="密钥 (API Key):").grid(row=3, column=0, sticky="w", pady=2)
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=2)
        
        btn_save_api = ttk.Button(api_frame, text="💾 保存/更新当前账号", command=self.save_current_api)
        btn_save_api.grid(row=4, column=1, sticky="w", pady=8)
        
        btn_del_api = ttk.Button(api_frame, text="❌ 删除当前账号", command=self.delete_current_api)
        btn_del_api.grid(row=4, column=2, sticky="e", pady=8)
        
        api_frame.columnconfigure(1, weight=1)
        api_frame.columnconfigure(2, weight=1)

        # 2. 项目目录
        proj_frame = ttk.LabelFrame(self.root, text=" 2. 工作目录（项目文件夹） ", padding=10)
        proj_frame.pack(fill="x", padx=15, pady=5)
        
        ttk.Label(proj_frame, text="历史项目目录:").grid(row=0, column=0, sticky="w", pady=2)
        self.proj_cb = ttk.Combobox(proj_frame, state="readonly")
        self.proj_cb.grid(row=0, column=1, sticky="ew", pady=2)
        self.proj_cb.bind("<<ComboboxSelected>>", self.on_project_selected)
        
        ttk.Label(proj_frame, text="当前项目路径:").grid(row=1, column=0, sticky="w", pady=2)
        self.proj_entry = ttk.Entry(proj_frame, textvariable=self.project_path_var)
        self.proj_entry.grid(row=1, column=1, sticky="ew", pady=2)
        # 绑定键盘抬起事件，实现手动输入路径时也自动刷新历史会话
        self.proj_entry.bind("<KeyRelease>", lambda e: self.on_project_path_changed())
        
        btn_browse = ttk.Button(proj_frame, text="📁 浏览...", command=self.browse_folder)
        btn_browse.grid(row=1, column=2, padx=5, pady=2)
        
        proj_frame.columnconfigure(1, weight=1)

        # 3. 启动模式
        launch_frame = ttk.LabelFrame(self.root, text=" 3. 启动模式 (支持历史对话) ", padding=10)
        launch_frame.pack(fill="x", padx=15, pady=5)
        
        r1 = ttk.Radiobutton(launch_frame, text="新建全新对话", variable=self.mode_var, value="normal", command=self.on_mode_changed)
        r1.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        r2 = ttk.Radiobutton(launch_frame, text="直接继续上次对话", variable=self.mode_var, value="continue", command=self.on_mode_changed)
        r2.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        r3 = ttk.Radiobutton(launch_frame, text="选择历史对话", variable=self.mode_var, value="resume", command=self.on_mode_changed)
        r3.grid(row=0, column=2, sticky="w", padx=10, pady=5)
        
        # 📌 动态弹出的特定会话选择下拉框
        self.session_label = ttk.Label(launch_frame, text="选择特定会话:")
        self.session_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.session_cb = ttk.Combobox(launch_frame, state="readonly")
        self.session_cb.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # 默认隐藏会话选择框，只有选择“选择历史对话”时显示
        self.session_label.grid_remove()
        self.session_cb.grid_remove()
        
        launch_frame.columnconfigure(1, weight=1)

        # 4. 启动按钮
        btn_launch = ttk.Button(self.root, text="🚀 启动 Claude Code 编程助手", command=self.launch_claude, style="Accent.TButton")
        btn_launch.pack(fill="x", padx=15, pady=20)
        
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Microsoft YaHei", 11, "bold"))

    def update_api_list(self):
        apis = list(self.config.get("apis", {}).keys())
        self.api_cb["values"] = apis
        if apis:
            self.api_cb.current(0)
            self.on_api_selected(None)
        else:
            self.api_cb.set("")
            self.api_name_var.set("")
            self.api_url_var.set("")
            self.api_key_var.set("")

    def update_project_list(self):
        projects = self.config.get("projects", [])
        self.proj_cb["values"] = projects
        if projects:
            self.proj_cb.current(0)
            self.on_project_selected(None)

    def on_api_selected(self, event):
        name = self.api_cb.get()
        api_data = self.config["apis"].get(name, {})
        self.api_name_var.set(name)
        self.api_url_var.set(api_data.get("url", ""))
        self.api_key_var.set(api_data.get("key", ""))

    def on_project_selected(self, event):
        path = self.proj_cb.get()
        self.project_path_var.set(path)
        self.on_project_path_changed()

    def on_project_path_changed(self):
        """当项目路径改变时，如果处于‘选择历史对话’模式，则自动重新加载下拉框"""
        if self.mode_var.get() == "resume":
            self.load_sessions_for_current_project()

    def on_mode_changed(self):
        """当单选框切换时，动态显示或隐藏会话下拉框"""
        mode = self.mode_var.get()
        if mode == "resume":
            self.session_label.grid()
            self.session_cb.grid()
            self.load_sessions_for_current_project()
        else:
            self.session_label.grid_remove()
            self.session_cb.grid_remove()

    def load_sessions_for_current_project(self):
        """寻找当前项目路径下的历史会话，并渲染下拉列表"""
        path = self.project_path_var.get().strip()
        if not path or not os.path.exists(path):
            self.session_cb["values"] = ["请先选择有效的工作目录"]
            self.session_cb.set("请先选择有效的工作目录")
            self.current_sessions = []
            return
            
        sessions = get_sessions_for_project(path)
        self.current_sessions = sessions
        
        if not sessions:
            self.session_cb["values"] = ["该项目下暂无历史对话"]
            self.session_cb.set("该项目下暂无历史对话")
            return
            
        display_values = []
        for s in sessions:
            time_str = s.get("time", "")
            if "T" in time_str:  # 格式化 ISO 字符串
                time_str = time_str.replace("T", " ").split(".")[0][:16]
            display_values.append(f"[{time_str}] {s.get('title')}")
            
        self.session_cb["values"] = display_values
        self.session_cb.current(0)

    def save_current_api(self):
        name = self.api_name_var.get().strip()
        url = self.api_url_var.get().strip()
        key = self.api_key_var.get().strip()
        if not name or not url or not key:
            messagebox.showwarning("提示", "请完整填写 API 别名、接口地址和密钥！")
            return
        
        if "apis" not in self.config:
            self.config["apis"] = {}
        self.config["apis"][name] = {"url": url, "key": key}
        self.save_config()
        self.update_api_list()
        self.api_cb.set(name)
        messagebox.showinfo("成功", f"API 账号 '{name}' 已保存。")

    def delete_current_api(self):
        name = self.api_cb.get()
        if not name:
            return
        if messagebox.askyesno("确认", f"确定要删除账号 '{name}' 吗？"):
            self.config["apis"].pop(name, None)
            self.save_config()
            self.update_api_list()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.project_path_var.set(folder)
            self.add_project_to_history(folder)
            self.on_project_path_changed()

    def add_project_to_history(self, path):
        if "projects" not in self.config:
            self.config["projects"] = []
        if path in self.config["projects"]:
            self.config["projects"].remove(path)
        self.config["projects"].insert(0, path)
        self.config["projects"] = self.config["projects"][:10]
        self.save_config()
        self.update_project_list()
        self.proj_cb.set(path)

    def launch_claude(self):
        path = self.project_path_var.get().strip()
        url = self.api_url_var.get().strip()
        key = self.api_key_var.get().strip()
        mode = self.mode_var.get()
        
        if not path or not os.path.exists(path):
            messagebox.showerror("错误", "请选择有效的工作目录（项目文件夹）！")
            return
        if not url or not key:
            messagebox.showerror("错误", "API 地址或密钥不能为空！")
            return
        
        self.add_project_to_history(path)
        
        flags = ""
        if mode == "continue":
            flags = "--continue"
        elif mode == "resume":
            # 检查下拉列表中是否选中了具体历史会话
            selected_idx = self.session_cb.current()
            if selected_idx >= 0 and self.current_sessions:
                selected_val = self.session_cb.get()
                # 过滤占位提示词
                if "该项目下暂无历史对话" not in selected_val and "请先选择有效的工作目录" not in selected_val:
                    selected_session = self.current_sessions[selected_idx]
                    session_id = selected_session.get("id")
                    flags = f"--resume {session_id}" # 精准复活会话！
                else:
                    flags = "--resume"
            else:
                flags = "--resume"
            
        env_vars = os.environ.copy()
        env_vars["ANTHROPIC_BASE_URL"] = url
        env_vars["ANTHROPIC_AUTH_TOKEN"] = key
        env_vars["ANTHROPIC_MODEL"] = "opus[1m]"  # 👈 新增这一行，强制启用 1M 上下文 Opus 模型
        
        # 推荐使用 powershell 启动，体验更佳
        cmd_args = ['cmd.exe', '/c', 'start', 'powershell.exe', '-NoExit', '-Command', f'claude {flags}']
        
        try:
            subprocess.Popen(cmd_args, cwd=path, env=env_vars)
        except Exception as e:
            messagebox.showerror("启动失败", f"无法打开终端窗口: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClaudeLauncher(root)
    root.mainloop()
