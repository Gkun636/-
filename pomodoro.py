import tkinter as tk
from tkinter import ttk
import threading
import time
import winsound
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pomodoro_config.json")

DEFAULTS = {
    "work": 25,
    "short_break": 5,
    "long_break": 15,
    "long_break_interval": 4,
}

BG       = "#fbfaf7"
SURFACE  = "#f3f0eb"
SURFACE2 = "#e8e3da"
FG       = "#1c1c1c"
MUTED    = "#9c9488"
GREEN    = "#b7473b"
YELLOW   = "#3a5c8c"
PURPLE   = "#5b7a4c"
BTN_TEXT = "#ffffff"
DISABLED = "#d5d0c8"
RING_TK  = "#e8e3da"
RADIUS   = 14

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k in DEFAULTS:
                if k not in cfg:
                    cfg[k] = DEFAULTS[k]
            return cfg
        except Exception:
            return dict(DEFAULTS)
    return dict(DEFAULTS)

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def _draw_round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a Canvas. Returns the item id."""
    points = [
        x1 + r, y1, x2 - r, y1,
        x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y1 + r, x2, y2 - r,
        x2, y2 - r, x2, y2, x2 - r, y2,
        x2 - r, y2, x1 + r, y2,
        x1 + r, y2, x1, y2, x1, y2 - r,
        x1, y2 - r, x1, y1 + r,
        x1, y1 + r, x1, y1, x1 + r, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)

class RoundedButton:
    """A clickable rounded-rectangle button backed by a Canvas."""

    def __init__(self, canvas, x, y, w, h, text, color, text_color, command,
                 font=("Microsoft YaHei", 11), r=RADIUS):
        self.canvas = canvas
        self.command = command
        self.x, self.y, self.w, self.h = x, y, w, h
        self.r = r
        self.color = color
        self.color_light = self._lighten(color, 0.15)
        self.color_dim = self._darken(color, 0.12)
        self.text_color = text_color
        self.font = font
        self._enabled = True

        self.rect_id = _draw_round_rect(
            canvas, x, y, x + w, y + h, r,
            fill=color, outline="",
        )
        self.text_id = canvas.create_text(
            x + w / 2, y + h / 2, text=text, fill=text_color, font=font,
        )
        self._bind_events()

    def _bind_events(self):
        for tag in (self.rect_id, self.text_id):
            self.canvas.tag_bind(tag, "<Enter>", self._on_enter)
            self.canvas.tag_bind(tag, "<Leave>", self._on_leave)
            self.canvas.tag_bind(tag, "<Button-1>", self._on_click)

    def _unbind_events(self):
        for tag in (self.rect_id, self.text_id):
            self.canvas.tag_unbind(tag, "<Enter>")
            self.canvas.tag_unbind(tag, "<Leave>")
            self.canvas.tag_unbind(tag, "<Button-1>")

    def _on_enter(self, _e):
        if self._enabled:
            self.canvas.itemconfig(self.rect_id, fill=self.color_light)

    def _on_leave(self, _e):
        if self._enabled:
            self.canvas.itemconfig(self.rect_id, fill=self.color)

    def _on_click(self, _e):
        if self._enabled and self.command:
            self.command()

    def config(self, text=None, color=None, text_color=None, enabled=None):
        if text is not None:
            self.canvas.itemconfig(self.text_id, text=text)
        if color is not None:
            self.color = color
            self.color_light = self._lighten(color, 0.15)
            self.color_dim = self._darken(color, 0.12)
            self.canvas.itemconfig(self.rect_id, fill=color)
        if text_color is not None:
            self.text_color = text_color
            self.canvas.itemconfig(self.text_id, fill=text_color)
        if enabled is not None:
            self._enabled = enabled
            if enabled:
                self.canvas.itemconfig(self.rect_id, fill=self.color)
                self.canvas.itemconfig(self.text_id, fill=self.text_color)
                self._bind_events()
            else:
                self.canvas.itemconfig(self.rect_id, fill=self.color_dim)
                self.canvas.itemconfig(self.text_id, fill=DISABLED)
                self._unbind_events()

    @staticmethod
    def _hex_to_rgb(hex_color):
        c = hex_color.lstrip("#")
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

    @staticmethod
    def _lighten(hex_color, amount):
        r, g, b = RoundedButton._hex_to_rgb(hex_color)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _darken(hex_color, amount):
        r, g, b = RoundedButton._hex_to_rgb(hex_color)
        r = int(r * (1 - amount))
        g = int(g * (1 - amount))
        b = int(b * (1 - amount))
        return f"#{r:02x}{g:02x}{b:02x}"

class SettingsDialog:
    def __init__(self, parent, cfg, on_save):
        self.cfg = cfg
        self.on_save = on_save
        self.top = tk.Toplevel(parent)
        self.top.title("自定义时长设置")
        self.top.geometry("320x320")
        self.top.resizable(False, False)
        self.top.configure(bg=BG)
        self.top.transient(parent)
        self.top.grab_set()

        self.top.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        tw, th = 320, 320
        self.top.geometry(f"{tw}x{th}+{px + (pw - tw) // 2}+{py + (ph - th) // 2}")

        pad = {"padx": 16, "pady": 6}
        font = ("Microsoft YaHei", 11)

        tk.Label(self.top, text="⏱ 自定义时长", font=("Microsoft YaHei", 14, "bold"),
                 fg=FG, bg=BG).pack(pady=(20, 14))

        self._add_row("工作时间 (分钟)", "work", font, pad)
        self._add_row("短休 (分钟)", "short_break", font, pad)
        self._add_row("长休 (分钟)", "long_break", font, pad)


        int_frame = tk.Frame(self.top, bg=BG)
        int_frame.pack(fill="x", **pad)
        tk.Label(int_frame, text="每几次工作后长休", font=font, fg=MUTED, bg=BG).pack(side="left")
        self.int_var = tk.IntVar(value=self.cfg.get("long_break_interval", 4))
        int_sb = tk.Spinbox(int_frame, from_=1, to=10, textvariable=self.int_var,
                            width=4, font=font, bg=SURFACE2, fg=FG, buttonbackground=SURFACE2,
                            relief="flat", justify="center")
        int_sb.pack(side="right")

        btn_frame = tk.Frame(self.top, bg=BG)
        btn_frame.pack(pady=(20, 10))
        btn_canvas = tk.Canvas(btn_frame, width=120, height=40, bg=BG, highlightthickness=0)
        btn_canvas.pack()
        RoundedButton(btn_canvas, 0, 0, 120, 40, "保存设置", GREEN, BTN_TEXT,
                      command=self._save, r=10)

    def _add_row(self, label, key, font, pad):
        frame = tk.Frame(self.top, bg=BG)
        frame.pack(fill="x", **pad)
        tk.Label(frame, text=label, font=font, fg=MUTED, bg=BG).pack(side="left")
        var = tk.IntVar(value=self.cfg.get(key, 25))
        setattr(self, f"_{key}_var", var)
        sb = tk.Spinbox(frame, from_=1, to=120, textvariable=var,
                        width=4, font=font, bg=SURFACE2, fg=FG, buttonbackground=SURFACE2,
                        relief="flat", justify="center")
        sb.pack(side="right")

    def _save(self):
        self.cfg["work"] = self._work_var.get()
        self.cfg["short_break"] = self._short_break_var.get()
        self.cfg["long_break"] = self._long_break_var.get()
        self.cfg["long_break_interval"] = self.int_var.get()
        save_config(self.cfg)
        self.on_save()
        self.top.destroy()

class PomodoroTimer:

    IDLE_LABELS = {"work": "🍅 准备开始", "short_break": "☕ 短休", "long_break": "🌴 长休"}
    RUNNING_LABELS = {"work": "工作中...", "short_break": "短休中...", "long_break": "长休中..."}
    FINISHED_LABELS = {"work": "工作完成！休息一下吧 🎉",
                       "short_break": "短休结束，继续加油！",
                       "long_break": "长休结束，准备好了吗？"}
    POPUP_MESSAGES = {
        "work": ("🍅 时间到！", "工作时间结束，休息一下吧～"),
        "short_break": ("☕ 休息结束", "短休结束，继续加油！"),
        "long_break": ("🌴 休息结束", "长休结束，准备好开始工作了吗？"),
    }

    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟")
        self.root.geometry("380x580")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.cfg = load_config()
        self.work_min = self.cfg["work"]
        self.short_break_min = self.cfg["short_break"]
        self.long_break_min = self.cfg["long_break"]
        self.long_break_interval = self.cfg["long_break_interval"]

        self._recalc_seconds()
        self.current_sec = self.work_sec
        self.running = False
        self.paused = False
        self.mode = "work"
        self.completed_sessions = 0
        self._timer_thread = None
        self._lock = threading.Lock()

        self._build_ui()
        self._update_display()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        RING_R = 95
        RING_W = 10
        CX, CY = 120, 120

        # ── Title ──
        title_frame = tk.Frame(self.root, bg=BG)
        title_frame.pack(pady=(20, 6))

        self.status_dot = tk.Canvas(title_frame, width=10, height=10, bg=BG, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 6))
        self._dot_id = self.status_dot.create_oval(0, 0, 10, 10, fill=GREEN, outline="")

        tk.Label(title_frame, text="🍅 准备开始", font=("Microsoft YaHei", 13, "bold"),
                 fg=FG, bg=BG).pack(side="left")
        self.mode_label = title_frame.winfo_children()[-1]

        # ── Circular ring ──
        ring_canvas = tk.Canvas(self.root, width=240, height=240, bg=BG, highlightthickness=0)
        ring_canvas.pack(pady=(2, 2))

        ring_canvas.create_oval(
            CX - RING_R - 6, CY - RING_R - 6, CX + RING_R + 6, CY + RING_R + 6,
            outline="#e0dcd5", width=1
        )
        self.ring_track = ring_canvas.create_arc(
            CX - RING_R, CY - RING_R, CX + RING_R, CY + RING_R,
            start=90, extent=-359.9, style='arc', outline=RING_TK, width=RING_W
        )
        self.ring_progress = ring_canvas.create_arc(
            CX - RING_R, CY - RING_R, CX + RING_R, CY + RING_R,
            start=90, extent=0, style='arc', outline=GREEN, width=RING_W
        )
        ring_canvas.create_oval(
            CX - RING_R + 18, CY - RING_R + 18, CX + RING_R - 18, CY + RING_R - 18,
            fill="#fefdfb", outline=""
        )

        self.timer_label = ring_canvas.create_text(
            CX, CY, text="25:00", fill=FG, font=("Consolas", 46, "bold"),
        )
        self.timer_canvas = ring_canvas

        # ── Session dots ──
        dots_canvas = tk.Canvas(self.root, width=120, height=14, bg=BG, highlightthickness=0)
        dots_canvas.pack(pady=(6, 2))
        self._session_dot_ids = []
        for i in range(self.long_break_interval):
            dx = 16 + i * 24
            dot = dots_canvas.create_oval(dx, 0, dx + 14, 14, fill=SURFACE2, outline="")
            self._session_dot_ids.append(dot)
        self.dots_canvas = dots_canvas

        tk.Label(self.root, text="已完成: 0 个番茄", font=("Microsoft YaHei", 9),
                 fg=MUTED, bg=BG).pack(pady=(0, 8))
        self.session_label = self.root.winfo_children()[-1]

        # ── Progress bar ──
        prog_canvas = tk.Canvas(self.root, width=300, height=8, bg=BG, highlightthickness=0)
        prog_canvas.pack(pady=(0, 14))
        _draw_round_rect(prog_canvas, 0, 0, 300, 8, r=4, fill=SURFACE2, outline="")
        self.prog_bar = _draw_round_rect(prog_canvas, 0, 0, 0, 8, r=4, fill=GREEN, outline="")
        self.prog_canvas = prog_canvas
        self.prog_max_w = 300

        # ── Control buttons ──
        ctrl_canvas = tk.Canvas(self.root, width=300, height=44, bg=BG, highlightthickness=0)
        ctrl_canvas.pack(pady=(0, 10))
        bw = 92

        self.start_btn = RoundedButton(
            ctrl_canvas, 0, 0, bw, 44, "开始", GREEN, BTN_TEXT, self.start, r=12,
        )
        self.pause_btn = RoundedButton(
            ctrl_canvas, bw + 12, 0, bw, 44, "暂停", YELLOW, BTN_TEXT, self.pause, r=12,
        )
        self.pause_btn.config(enabled=False)
        self.reset_btn = RoundedButton(
            ctrl_canvas, (bw + 12) * 2, 0, bw, 44, "重置", "#d4cfc7", FG, self.reset, r=12,
        )

        # ── Mode tabs ──
        mode_canvas = tk.Canvas(self.root, width=300, height=42, bg=BG, highlightthickness=0)
        mode_canvas.pack(pady=(0, 6))
        _draw_round_rect(mode_canvas, 4, 4, 296, 38, r=19, fill=SURFACE2, outline="")

        self.work_btn = RoundedButton(
            mode_canvas, 8, 4, 90, 34, f"工作 {self.work_min}min", GREEN, BTN_TEXT,
            lambda: self.switch_mode("work"), font=("Microsoft YaHei", 9), r=9,
        )
        self.short_btn = RoundedButton(
            mode_canvas, 103, 4, 90, 34, f"短休 {self.short_break_min}min", BG, FG,
            lambda: self.switch_mode("short_break"), font=("Microsoft YaHei", 9), r=9,
        )
        self.long_btn = RoundedButton(
            mode_canvas, 198, 4, 90, 34, f"长休 {self.long_break_min}min", BG, FG,
            lambda: self.switch_mode("long_break"), font=("Microsoft YaHei", 9), r=9,
        )

        # ── Bottom row ──
        bottom_frame = tk.Frame(self.root, bg=BG)
        bottom_frame.pack(pady=(8, 8))

        settings_canvas = tk.Canvas(bottom_frame, width=96, height=32, bg=BG, highlightthickness=0)
        settings_canvas.pack(side="left", padx=(0, 30))
        RoundedButton(settings_canvas, 0, 0, 96, 32, "⚙ 设置", SURFACE2, FG,
                      self._open_settings, font=("Microsoft YaHei", 9), r=9)

        self.top_var = tk.BooleanVar(value=self.cfg.get("always_on_top", False))
        cb = tk.Checkbutton(
            bottom_frame, text="窗口置顶", variable=self.top_var,
            command=self._toggle_top, font=("Microsoft YaHei", 9),
            fg=MUTED, bg=BG, selectcolor=SURFACE,
            activebackground=BG, activeforeground=FG,
        )
        cb.pack(side="left")

    def _timer_loop(self):
        start_time = time.perf_counter()
        elapsed_paused = 0.0
        pause_start = 0.0
        while self.running:
            time.sleep(0.2)
            with self._lock:
                if not self.running:
                    break
                if self.paused:
                    if pause_start == 0.0:
                        pause_start = time.perf_counter()
                    continue
                if pause_start > 0.0:
                    elapsed_paused += time.perf_counter() - pause_start
                    pause_start = 0.0
                elapsed = time.perf_counter() - start_time - elapsed_paused
                remaining = self._total_seconds() - elapsed
                if remaining > 0:
                    self.current_sec = remaining
                else:
                    self.current_sec = 0
                    self.running = False
                    self.root.after(0, self._on_finish)
                    break
                self.root.after(0, self._update_display)

    def _on_finish(self):
        finished_mode = self.mode
        self.mode_label.config(text=self.FINISHED_LABELS.get(finished_mode, "时间到！"))

        if finished_mode == "work":
            self.completed_sessions += 1
            self.session_label.config(text=f"已完成: {self.completed_sessions} 个番茄")
            self._update_dots()
            if self.completed_sessions % self.long_break_interval == 0:
                self.switch_mode("long_break")
            else:
                self.switch_mode("short_break")

        self._set_buttons_state("stopped")
        self.root.deiconify()
        self.root.lift()
        threading.Thread(target=self._ringtone, daemon=True).start()
        self._show_popup(finished_mode)

    def _ringtone(self):
        melody = [
            (988, 120), (0, 40), (1175, 120), (0, 40), (1319, 120), (0, 40),
            (1480, 120), (0, 40), (1568, 120), (0, 40), (1760, 120), (0, 40),
            (1760, 120), (0, 40), (1568, 120), (0, 40), (1480, 120), (0, 40),
            (1760, 120), (0, 40), (1976, 400),
        ]
        try:
            for freq, dur in melody:
                if freq == 0:
                    time.sleep(dur / 1000.0)
                else:
                    winsound.Beep(freq, dur)
            winsound.MessageBeep(0xFFFFFFFF)
        except Exception:
            pass

    def _show_popup(self, finished_mode):
        title, subtitle = self.POPUP_MESSAGES.get(finished_mode, ("⏰ 时间到！", ""))

        def _create():
            try:
                popup = tk.Toplevel(self.root)
                popup.title("番茄钟提醒")
                popup.resizable(False, False)
                popup.configure(bg=BG)
                popup.attributes("-topmost", True)

                tk.Label(popup, text=title, font=("Microsoft YaHei", 18, "bold"),
                         fg=GREEN, bg=BG).pack(pady=(30, 6))
                tk.Label(popup, text=subtitle, font=("Microsoft YaHei", 11),
                         fg=MUTED, bg=BG).pack(pady=(0, 20))

                btn_canvas = tk.Canvas(popup, width=100, height=38, bg=BG, highlightthickness=0)
                btn_canvas.pack()
                RoundedButton(btn_canvas, 0, 0, 100, 38, "知道了", GREEN, BTN_TEXT,
                              command=popup.destroy, r=10)

                popup.bind("<Escape>", lambda e: popup.destroy())

                popup.update_idletasks()
                pw, ph = self.root.winfo_width(), self.root.winfo_height()
                px, py = self.root.winfo_x(), self.root.winfo_y()
                tw, th = popup.winfo_reqwidth() + 20, popup.winfo_reqheight() + 20
                popup.geometry(f"{tw}x{th}+{px + (pw - tw) // 2}+{py + (ph - th) // 2}")

                popup.deiconify()
                popup.lift()
                popup.focus_set()
            except Exception:
                pass

        self.root.after(50, _create)

    def _update_display(self):
        total = self._total_seconds()
        remaining = max(0, int(self.current_sec))
        m, s = divmod(remaining, 60)
        self.timer_canvas.itemconfig(self.timer_label, text=f"{m:02d}:{s:02d}")
        if total > 0:
            ratio = (total - remaining) / total
            extent = -359.9 * ratio
            self.timer_canvas.itemconfig(self.ring_progress, extent=extent)
            w = int(self.prog_max_w * ratio)
            self.prog_canvas.coords(self.prog_bar, 0, 0, w, 8)

    def _rebuild_dots(self):
        self.dots_canvas.delete("all")
        self._session_dot_ids.clear()
        for i in range(self.long_break_interval):
            dx = 16 + i * 24
            dot = self.dots_canvas.create_oval(dx, 0, dx + 14, 14, fill=SURFACE2, outline="")
            self._session_dot_ids.append(dot)

    def _update_dots(self):
        filled = self.completed_sessions % self.long_break_interval
        for i, dot_id in enumerate(self._session_dot_ids):
            color = GREEN if i < filled else SURFACE2
            self.dots_canvas.itemconfig(dot_id, fill=color)

    def _recalc_seconds(self):
        self.work_sec = self.work_min * 60
        self.short_break_sec = self.short_break_min * 60
        self.long_break_sec = self.long_break_min * 60

    def _total_seconds(self):
        return getattr(self, f"{self.mode}_sec")

    def _set_buttons_state(self, state):
        running = state == "running"
        self.start_btn.config(enabled=not running)
        self.pause_btn.config(enabled=running)

    def _highlight_mode(self, active):
        colors = {"work": GREEN, "short_break": YELLOW, "long_break": PURPLE}
        accent = colors.get(active, GREEN)
        self.timer_canvas.itemconfig(self.ring_progress, outline=accent)
        self.status_dot.itemconfig(self._dot_id, fill=accent)
        for btn, mode in [(self.work_btn, "work"), (self.short_btn, "short_break"),
                          (self.long_btn, "long_break")]:
            if mode == active:
                btn.config(color=colors[mode], text_color=BTN_TEXT)
            else:
                btn.config(color=BG, text_color=FG)

    def start(self):
        with self._lock:
            if self.running and self.paused:
                self.paused = False
                self._set_buttons_state("running")
                return
            if self.running:
                return
            self.running = True
            self.paused = False
        self._set_buttons_state("running")
        self.mode_label.config(text=self.RUNNING_LABELS.get(self.mode, "运行中..."))
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

    def pause(self):
        with self._lock:
            if self.running and not self.paused:
                self.paused = True
            else:
                return
        self._set_buttons_state("paused")
        self.mode_label.config(text="⏸ 已暂停")

    def reset(self):
        self.switch_mode(self.mode)

    def switch_mode(self, mode):
        with self._lock:
            self.running = False
            self.paused = False
            self.mode = mode
            self.current_sec = self._total_seconds()
        self._set_buttons_state("stopped")
        self.mode_label.config(text=self.IDLE_LABELS.get(mode, "准备开始"))
        self._highlight_mode(mode)
        self._update_display()

    def _open_settings(self):
        SettingsDialog(self.root, self.cfg, self._on_settings_saved)

    def _on_settings_saved(self):
        self.work_min = self.cfg["work"]
        self.short_break_min = self.cfg["short_break"]
        self.long_break_min = self.cfg["long_break"]
        self.long_break_interval = self.cfg["long_break_interval"]
        self._recalc_seconds()
        self._rebuild_dots()
        self.switch_mode(self.mode)
        self.work_btn.config(text=f"工作 {self.work_min}min")
        self.short_btn.config(text=f"短休 {self.short_break_min}min")
        self.long_btn.config(text=f"长休 {self.long_break_min}min")

    def _toggle_top(self):
        self.root.attributes("-topmost", self.top_var.get())

    def _on_close(self):
        with self._lock:
            self.running = False
        self.cfg["always_on_top"] = self.top_var.get()
        save_config(self.cfg)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 2
    root.geometry(f"+{x}+{y}")
    if app.top_var.get():
        root.attributes("-topmost", True)
    root.mainloop()

if __name__ == "__main__":
    main()
