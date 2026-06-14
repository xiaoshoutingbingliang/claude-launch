import os
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# 配置文件将安全地保存在你系统的用户目录下
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "claude_launcher_config.json")

class ClaudeLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Code 桌面轻量启动器")
        self.root.geometry("520x550")
        
        # 加载本地保存的配置
        self.config = self.load_config()
        
        # UI 绑定变量
        self.api_name_var = tk.StringVar()
        self.api_url_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.project_path_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="normal") # normal (新建), continue (继续), resume (历史)
        
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
        # 1. API 选择与管理
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

        # 2. 项目目录管理
        proj_frame = ttk.LabelFrame(self.root, text=" 2. 工作目录（项目文件夹） ", padding=10)
        proj_frame.pack(fill="x", padx=15, pady=5)
        
        ttk.Label(proj_frame, text="历史项目目录:").grid(row=0, column=0, sticky="w", pady=2)
        self.proj_cb = ttk.Combobox(proj_frame, state="readonly")
        self.proj_cb.grid(row=0, column=1, sticky="ew", pady=2)
        self.proj_cb.bind("<<ComboboxSelected>>", self.on_project_selected)
        
        ttk.Label(proj_frame, text="当前项目路径:").grid(row=1, column=0, sticky="w", pady=2)
        self.proj_entry = ttk.Entry(proj_frame, textvariable=self.project_path_var)
        self.proj_entry.grid(row=1, column=1, sticky="ew", pady=2)
        
        btn_browse = ttk.Button(proj_frame, text="📁 浏览...", command=self.browse_folder)
        btn_browse.grid(row=1, column=2, padx=5, pady=2)
        
        proj_frame.columnconfigure(1, weight=1)

        # 3. 启动模式选择
        launch_frame = ttk.LabelFrame(self.root, text=" 3. 启动模式 (支持历史对话) ", padding=10)
        launch_frame.pack(fill="x", padx=15, pady=5)
        
        r1 = ttk.Radiobutton(launch_frame, text="新建全新对话", variable=self.mode_var, value="normal")
        r1.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        r2 = ttk.Radiobutton(launch_frame, text="直接继续上次对话", variable=self.mode_var, value="continue")
        r2.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        r3 = ttk.Radiobutton(launch_frame, text="列出历史对话并选择", variable=self.mode_var, value="resume")
        r3.grid(row=0, column=2, sticky="w", padx=10, pady=5)

        # 4. 启动按钮
        btn_launch = ttk.Button(self.root, text="🚀 启动 Claude Code 编程助手", command=self.launch_claude, style="Accent.TButton")
        btn_launch.pack(fill="x", padx=15, pady=20)
        
        # 按钮样式微调
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
        self.project_path_var.set(self.proj_cb.get())

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

    def add_project_to_history(self, path):
        if "projects" not in self.config:
            self.config["projects"] = []
        if path in self.config["projects"]:
            self.config["projects"].remove(path)
        self.config["projects"].insert(0, path)
        self.config["projects"] = self.config["projects"][:10] # 最多记住10个历史项目路径
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
        
        # 将当前目录追加进历史
        self.add_project_to_history(path)
        
        # 决定 Claude Code 的启动参数
        flags = ""
        if mode == "continue":
            flags = "--continue"
        elif mode == "resume":
            flags = "--resume"
            
        # 组装启动命令：开启一个全新的 cmd 窗口，设置临时变量，进入对应文件夹，然后运行 claude
        cmd_str = f'start cmd.exe /k "cd /d \\"{path}\\" && set ANTHROPIC_BASE_URL={url} && set ANTHROPIC_AUTH_TOKEN={key} && claude {flags}"'
        
        try:
            subprocess.Popen(cmd_str, shell=True)
        except Exception as e:
            messagebox.showerror("启动失败", f"无法打开终端窗口: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClaudeLauncher(root)
    root.mainloop()