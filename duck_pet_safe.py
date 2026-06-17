import json
import math
import random
import sys
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser

try:
    import winsound
except ImportError:
    winsound = None


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "pet_config.json"
TRANSPARENT = "#ff00ff"

DEFAULT_CONFIG = {
    "size": 1.0,
    "speed": 3.0,
    "body_color": "#ffe181",
    "beak_color": "#fe9a22",
    "outline_color": "#841b1e",
    "avoid_mouse": True,
    "sound_enabled": True,
    "messages": [
        "quack",
        "remember to save",
        "hello from your duck",
        "take a short break",
        "you are doing great"
    ]
}


def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    config = DEFAULT_CONFIG.copy()
    for key in DEFAULT_CONFIG:
        if key in data:
            config[key] = data[key]
    return config


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


class SafeDesktopDuck:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("DesktopDuck SAFE")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT)

        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass

        self.scale = float(self.config["size"])
        self.speed = float(self.config["speed"])
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.window_w = 220
        self.window_h = 165
        self.x = random.randint(40, max(80, self.screen_w - 260))
        self.y = max(50, self.screen_h - 210)
        self.vx = self.speed
        self.direction = 1
        self.step = 0
        self.paused = False
        self.dragging = False
        self.drag_offset = (0, 0)
        self.state = "walk"
        self.state_until = 0
        self.next_turn = random.randint(70, 180)
        self.next_talk = random.randint(180, 420)
        self.message_after_id = None
        self.settings_window = None

        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Pause / Resume", command=self.toggle_pause)
        self.menu.add_command(label="Talk", command=self.say_random_message)
        self.menu.add_command(label="Happy", command=lambda: self.set_state("happy", 120))
        self.menu.add_command(label="Sleep", command=lambda: self.set_state("sleep", 220))
        self.menu.add_command(label="Settings", command=self.open_settings)
        self.menu.add_separator()
        self.menu.add_command(label="Bigger", command=lambda: self.change_size(0.1))
        self.menu.add_command(label="Smaller", command=lambda: self.change_size(-0.1))
        self.menu.add_command(label="Faster", command=lambda: self.change_speed(0.5))
        self.menu.add_command(label="Slower", command=lambda: self.change_speed(-0.5))
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.quit)

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Button-3>", self.show_menu)
        self.root.bind("<Escape>", lambda _event: self.quit())

        self.resize_window()
        self.draw()
        self.tick()
        self.root.mainloop()

    def resize_window(self):
        self.window_w = int(230 * self.scale)
        self.window_h = int(170 * self.scale)
        self.canvas.configure(width=self.window_w, height=self.window_h)
        self.clamp_to_screen()
        self.root.geometry(f"{self.window_w}x{self.window_h}+{int(self.x)}+{int(self.y)}")

    def clamp_to_screen(self):
        self.x = max(0, min(self.x, self.screen_w - self.window_w))
        self.y = max(0, min(self.y, self.screen_h - self.window_h - 5))

    def p(self, x, y):
        return x * self.scale, y * self.scale

    def oval(self, x1, y1, x2, y2, **options):
        px1, py1 = self.p(x1, y1)
        px2, py2 = self.p(x2, y2)
        self.canvas.create_oval(min(px1, px2), min(py1, py2), max(px1, px2), max(py1, py2), **options)

    def polygon(self, points, **options):
        scaled = []
        for x, y in points:
            px, py = self.p(x, y)
            scaled.extend([px, py])
        self.canvas.create_polygon(*scaled, **options)

    def line(self, x1, y1, x2, y2, **options):
        self.canvas.create_line(*(self.p(x1, y1) + self.p(x2, y2)), **options)

    def text(self, x, y, **options):
        self.canvas.create_text(*self.p(x, y), **options)

    def draw(self):
        self.canvas.delete("duck")
        body = self.config["body_color"]
        beak = self.config["beak_color"]
        outline = self.config["outline_color"]
        thickness = max(2, int(3 * self.scale))
        frame = int(self.step / 5) % 4
        walk = [-4, 2, 4, -2][frame]
        bounce = 0 if self.state == "sleep" else [0, -2, 0, -1][frame]
        if self.state == "happy":
            bounce -= abs(math.sin(self.step / 5)) * 5
        if self.state == "sleep":
            walk = 0
            bounce = 5

        flip = self.direction

        def fx(x):
            return 115 + (x - 115) * flip

        self.oval(fx(50), 86 + bounce, fx(150), 142 + bounce, fill=body, outline=outline, width=thickness, tags="duck")
        self.oval(fx(100), 52 + bounce, fx(160), 102 + bounce, fill=body, outline=outline, width=thickness, tags="duck")
        self.polygon([(fx(59), 108 + bounce), (fx(22), 98 + bounce), (fx(45), 128 + bounce)], fill=body, outline=outline, tags="duck")
        self.polygon([(fx(155), 69 + bounce), (fx(196), 80 + bounce), (fx(155), 91 + bounce)], fill=beak, outline=outline, tags="duck")

        if self.state == "sleep":
            self.line(fx(121), 73 + bounce, fx(136), 73 + bounce, fill="#111111", width=thickness, tags="duck")
            self.text(fx(184), 35, text="Z", fill="#333333", font=("Segoe UI", max(12, int(16 * self.scale)), "bold"), tags="duck")
        elif self.state == "happy":
            self.line(fx(119), 74 + bounce, fx(129), 80 + bounce, fill="#111111", width=thickness, tags="duck")
            self.line(fx(129), 80 + bounce, fx(140), 73 + bounce, fill="#111111", width=thickness, tags="duck")
            self.text(fx(86), 42 + bounce, text="heart", fill="#ff4b6e", font=("Segoe UI", max(9, int(10 * self.scale)), "bold"), tags="duck")
        else:
            self.oval(fx(121), 68 + bounce, fx(130), 77 + bounce, fill="#111111", outline="", tags="duck")

        self.line(fx(82), 140 + bounce, fx(78), 160 + walk + bounce, fill=outline, width=thickness, tags="duck")
        self.line(fx(124), 140 + bounce, fx(134), 160 - walk + bounce, fill=outline, width=thickness, tags="duck")
        self.polygon([(fx(66), 161 + walk + bounce), (fx(91), 161 + walk + bounce), (fx(78), 169 + walk + bounce)], fill=beak, outline="", tags="duck")
        self.polygon([(fx(122), 161 - walk + bounce), (fx(149), 161 - walk + bounce), (fx(134), 169 - walk + bounce)], fill=beak, outline="", tags="duck")

    def tick(self):
        if not self.paused and not self.dragging:
            self.step += 1
            self.move()
        elif self.dragging:
            self.step += 1
        self.draw()
        self.root.after(33, self.tick)

    def move(self):
        if self.state_until and self.step >= self.state_until:
            self.state = "walk"
            self.state_until = 0

        if self.state == "sleep":
            self.vx = 0
        else:
            self.avoid_mouse()
            self.wander()

        self.x += self.vx
        if self.x <= 0 or self.x >= self.screen_w - self.window_w:
            self.vx *= -1
            self.beep("bump")

        self.direction = 1 if self.vx >= 0 else -1
        self.clamp_to_screen()
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

        self.next_talk -= 1
        if self.next_talk <= 0:
            self.say_random_message()
            self.next_talk = random.randint(260, 720)

    def avoid_mouse(self):
        if not self.config.get("avoid_mouse", True):
            return
        mx = self.root.winfo_pointerx()
        my = self.root.winfo_pointery()
        cx = self.x + self.window_w / 2
        cy = self.y + self.window_h / 2
        if math.hypot(cx - mx, cy - my) < 125:
            self.vx = (-1 if mx > cx else 1) * (self.speed + 3.0)

    def wander(self):
        self.next_turn -= 1
        if self.next_turn > 0:
            return
        self.vx = random.choice([-1, 1]) * random.uniform(self.speed * 0.75, self.speed * 1.25)
        self.next_turn = random.randint(70, 190)

    def set_state(self, state, duration):
        self.state = state
        self.state_until = self.step + duration
        self.beep("quack")

    def say_random_message(self):
        messages = self.config.get("messages") or DEFAULT_CONFIG["messages"]
        message = random.choice(messages)
        self.canvas.delete("bubble")
        x1, y1 = self.p(18, 8)
        x2, y2 = self.p(212, 43)
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="#222222", tags="bubble")
        self.canvas.create_text(
            *self.p(115, 25),
            text=message,
            fill="#111111",
            width=int(178 * self.scale),
            font=("Segoe UI", max(8, int(10 * self.scale)), "bold"),
            tags="bubble",
        )
        self.beep("quack")
        if self.message_after_id is not None:
            self.root.after_cancel(self.message_after_id)
        self.message_after_id = self.root.after(2100, lambda: self.canvas.delete("bubble"))

    def beep(self, kind):
        if winsound is None or not self.config.get("sound_enabled", True):
            return
        pattern = {
            "quack": [(720, 70), (540, 80)],
            "bump": [(260, 55)],
        }.get(kind, [(700, 60)])
        for freq, length in pattern:
            try:
                winsound.Beep(freq, length)
            except RuntimeError:
                return

    def start_drag(self, event):
        self.dragging = True
        self.drag_offset = (event.x, event.y)

    def drag(self, event):
        self.x = event.x_root - self.drag_offset[0]
        self.y = event.y_root - self.drag_offset[1]
        self.clamp_to_screen()
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def stop_drag(self, _event):
        self.dragging = False
        self.vx = random.choice([-1, 1]) * self.speed

    def show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def toggle_pause(self):
        self.paused = not self.paused

    def change_size(self, delta):
        self.scale = max(0.6, min(2.0, self.scale + delta))
        self.config["size"] = round(self.scale, 2)
        save_config(self.config)
        self.resize_window()

    def change_speed(self, delta):
        self.speed = max(0.5, min(12.0, self.speed + delta))
        self.config["speed"] = round(self.speed, 2)
        save_config(self.config)
        self.vx = (1 if self.vx >= 0 else -1) * self.speed

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("DesktopDuck SAFE Settings")
        self.settings_window.attributes("-topmost", True)
        self.settings_window.resizable(False, False)

        frame = tk.Frame(self.settings_window, padx=14, pady=12)
        frame.pack(fill="both", expand=True)

        size_var = tk.DoubleVar(value=self.scale)
        speed_var = tk.DoubleVar(value=self.speed)
        avoid_var = tk.BooleanVar(value=self.config.get("avoid_mouse", True))
        sound_var = tk.BooleanVar(value=self.config.get("sound_enabled", True))
        body_var = tk.StringVar(value=self.config["body_color"])
        beak_var = tk.StringVar(value=self.config["beak_color"])
        outline_var = tk.StringVar(value=self.config["outline_color"])

        tk.Label(frame, text="Settings", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        tk.Label(frame, text="Size").grid(row=1, column=0, sticky="w")
        tk.Scale(frame, from_=0.6, to=2.0, resolution=0.1, orient="horizontal", variable=size_var, length=220).grid(row=1, column=1, columnspan=2)
        tk.Label(frame, text="Speed").grid(row=2, column=0, sticky="w")
        tk.Scale(frame, from_=0.5, to=12.0, resolution=0.5, orient="horizontal", variable=speed_var, length=220).grid(row=2, column=1, columnspan=2)

        self.color_row(frame, 3, "Body", body_var)
        self.color_row(frame, 4, "Beak", beak_var)
        self.color_row(frame, 5, "Outline", outline_var)

        tk.Checkbutton(frame, text="Avoid mouse", variable=avoid_var).grid(row=6, column=0, columnspan=3, sticky="w")
        tk.Checkbutton(frame, text="Sound", variable=sound_var).grid(row=7, column=0, columnspan=3, sticky="w")
        tk.Label(frame, text="Messages").grid(row=8, column=0, sticky="nw", pady=(8, 0))

        messages = tk.Text(frame, width=34, height=6)
        messages.insert("1.0", "\n".join(self.config.get("messages", [])))
        messages.grid(row=8, column=1, columnspan=2, pady=(8, 0))

        buttons = tk.Frame(frame)
        buttons.grid(row=9, column=0, columnspan=3, sticky="e", pady=(12, 0))
        tk.Button(
            buttons,
            text="Apply",
            command=lambda: self.apply_settings(
                size_var, speed_var, avoid_var, sound_var, body_var, beak_var, outline_var, messages
            ),
        ).pack(side="left", padx=(0, 8))
        tk.Button(buttons, text="Close", command=self.settings_window.destroy).pack(side="left")

    def color_row(self, frame, row, label, variable):
        tk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
        preview = tk.Label(frame, textvariable=variable, width=12, bg=variable.get(), relief="solid")
        preview.grid(row=row, column=1, sticky="w", pady=2)

        def choose():
            color = colorchooser.askcolor(initialcolor=variable.get(), parent=self.settings_window)[1]
            if color:
                variable.set(color)
                preview.configure(bg=color)

        tk.Button(frame, text="Pick", command=choose).grid(row=row, column=2, sticky="e", padx=(8, 0))

    def apply_settings(self, size_var, speed_var, avoid_var, sound_var, body_var, beak_var, outline_var, messages):
        message_lines = [line.strip() for line in messages.get("1.0", "end").splitlines() if line.strip()]
        self.scale = float(size_var.get())
        self.speed = float(speed_var.get())
        self.config.update(
            {
                "size": round(self.scale, 2),
                "speed": round(self.speed, 2),
                "avoid_mouse": bool(avoid_var.get()),
                "sound_enabled": bool(sound_var.get()),
                "body_color": body_var.get(),
                "beak_color": beak_var.get(),
                "outline_color": outline_var.get(),
                "messages": message_lines or DEFAULT_CONFIG["messages"],
            }
        )
        save_config(self.config)
        self.resize_window()

    def quit(self):
        save_config(self.config)
        self.root.destroy()


if __name__ == "__main__":
    if sys.platform != "win32":
        print("DesktopDuck SAFE is designed for Windows desktop transparency.")
    SafeDesktopDuck()
