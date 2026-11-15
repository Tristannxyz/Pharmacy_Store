import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from pathlib import Path
try:
    from PIL import Image, ImageTk, ImageDraw
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
import config
import auth
from theme import lerp_hex
_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
# ── Theme Palettes Matching Reference Screenshots ──────────────────────────────
_LOGIN_PALETTES = {
    "light": {
        "left_bg": "#eef4ff",
        "right_bg": "#f8fafc",
        "split_border": "#e2e8f0",
        "left_divider": "#dce5f4",
        "right_divider": "#e2e8f0",
        "surface": "#ffffff",
        "surface_hover": "#f1f5f9",
        "border": "#e2e8f0",
        "border_hover": "#cbd5e1",
        "focus_border": "#2563eb",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_fg": "#ffffff",
        "dot_admin": "#16a34a",
        "dot_instructor": "#0ea5e9",
        "dot_clerk": "#9333ea",
        "dot_sales": "#ea580c",
        # Subtle animated background motif colors (Light Mode)
        "anim_left_node": "#c7dbff",
        "anim_left_line": "#d9e6ff",
        "anim_left_shape": "#bfd6fe",
        "anim_left_wave": "#d4e3ff",
        "anim_right_node": "#dbe5f4",
        "anim_right_line": "#e6eef8",
        "anim_right_shape": "#d5e2f6",
    },
    "dark": {
        "left_bg": "#0f1a2e",
        "right_bg": "#0b1220",
        "split_border": "#182438",
        "left_divider": "#1c2b42",
        "right_divider": "#1e293b",
        "surface": "#131c2b",
        "surface_hover": "#1b273b",
        "border": "#233044",
        "border_hover": "#334560",
        "focus_border": "#3b72e8",
        "text_primary": "#f8fafc",
        "text_secondary": "#e2e8f0",
        "text_muted": "#94a3b8",
        "accent": "#3b72e8",
        "accent_hover": "#2563eb",
        "accent_fg": "#ffffff",
        "dot_admin": "#22c55e",
        "dot_instructor": "#38bdf8",
        "dot_clerk": "#a855f7",
        "dot_sales": "#f97316",
        # Subtle animated background motif colors (Dark Mode)
        "anim_left_node": "#1d3358",
        "anim_left_line": "#162744",
        "anim_left_shape": "#1b3052",
        "anim_left_wave": "#172947",
        "anim_right_node": "#16243d",
        "anim_right_line": "#121d31",
        "anim_right_shape": "#15223a",
    },
}
# ── Multi-Language Translations ────────────────────────────────────────────────
_TRANSLATIONS = {
    "English": {
        "brand": "RestInPills",
        "smart": "Smart ",
        "ops": "pharmacy operations",
        "hero_sub": "Pharmacy Store Management and Knowledge Analytics",
        "f1_title": "Demand Insights",
        "f1_sub": "See what will sell next week, before it does.",
        "f2_title": "Expiry Guard",
        "f2_sub": "Batch and expiry alerts that cut waste.",
        "f3_title": "Stock Pulse",
        "f3_sub": "Live shelf levels across every branch.",
        "f4_title": "Team Access",
        "f4_sub": "Each role sees only what it needs.",
        "settings": "Settings",
        "appearance": "Appearance",
        "light_mode": "Light mode",
        "dark_mode": "Dark mode",
        "language": "Language",
        "font": "Font",
        "text_size": "Text size",
        "welcome": "Welcome back",
        "welcome_sub": "Sign in to access your designated workspace.",
        "username": "Username",
        "password": "Password",
        "sign_in": "Sign in to system   →",
        "quick_access": "   Quick access   ",
        "role_admin": "Administrator",
        "role_instructor": "Instructor",
        "role_clerk": "Inventory Clerk",
        "role_sales": "Sales Personnel",
    },
    "Filipino": {
        "brand": "RestInPills",
        "smart": "Matalinong ",
        "ops": "operasyon ng botika",
        "hero_sub": "Pamamahala ng Botika at Pagsusuri ng Kaalaman",
        "f1_title": "Demand Insights",
        "f1_sub": "Tingnan kung ano ang mabebenta sa susunod na linggo.",
        "f2_title": "Expiry Guard",
        "f2_sub": "Mga alerto sa batch at pag-expire para iwas-sayang.",
        "f3_title": "Stock Pulse",
        "f3_sub": "Live na antas ng paninda sa bawat sangay.",
        "f4_title": "Team Access",
        "f4_sub": "Nakikita lang ng bawat tungkulin ang kailangan nito.",
        "settings": "Settings",
        "appearance": "Hitsura",
        "light_mode": "Light mode",
        "dark_mode": "Dark mode",
        "language": "Wika",
        "font": "Font",
        "text_size": "Laki ng teksto",
        "welcome": "Maligayang pagbabalik",
        "welcome_sub": "Mag-sign in upang mabuksan ang iyong workspace.",
        "username": "Username",
        "password": "Password",
        "sign_in": "Mag-sign in sa system   →",
        "quick_access": "   Mabilis na access   ",
        "role_admin": "Administrator",
        "role_instructor": "Instructor",
        "role_clerk": "Inventory Clerk",
        "role_sales": "Sales Personnel",
    },
    "Spanish": {
        "brand": "RestInPills",
        "smart": "Operaciones ",
        "ops": "inteligentes de farmacia",
        "hero_sub": "Gestión de Farmacia y Analítica de Conocimiento",
        "f1_title": "Demand Insights",
        "f1_sub": "Vea qué se venderá la próxima semana con anticipación.",
        "f2_title": "Expiry Guard",
        "f2_sub": "Alertas de lotes y vencimientos que reducen pérdidas.",
        "f3_title": "Stock Pulse",
        "f3_sub": "Niveles de inventario en vivo en cada sucursal.",
        "f4_title": "Team Access",
        "f4_sub": "Cada rol accede únicamente a lo que necesita.",
        "settings": "Ajustes",
        "appearance": "Apariencia",
        "light_mode": "Light mode",
        "dark_mode": "Dark mode",
        "language": "Idioma",
        "font": "Fuente",
        "text_size": "Tamaño de texto",
        "welcome": "Bienvenido de nuevo",
        "welcome_sub": "Inicie sesión para acceder a su espacio de trabajo.",
        "username": "Usuario",
        "password": "Contraseña",
        "sign_in": "Iniciar sesión en el sistema   →",
        "quick_access": "   Acceso rápido   ",
        "role_admin": "Administrator",
        "role_instructor": "Instructor",
        "role_clerk": "Inventory Clerk",
        "role_sales": "Sales Personnel",
    },
}
_SIZE_OFFSETS = {"S": -1, "M": 0, "L": 2, "XL": 3}
_FONT_OPTIONS = ["Inter", "Segoe UI", "Calibri", "Arial", "Consolas"]
_LANG_OPTIONS = ["English", "Filipino", "Spanish"]
# Precomputed unit cross vertices (normalized to size=1.0)
_CROSS_RATIO = 0.36
_UNIT_CROSS = (
    (-_CROSS_RATIO, -1.0), (_CROSS_RATIO, -1.0),
    (_CROSS_RATIO, -_CROSS_RATIO), (1.0, -_CROSS_RATIO),
    (1.0, _CROSS_RATIO), (_CROSS_RATIO, _CROSS_RATIO),
    (_CROSS_RATIO, 1.0), (-_CROSS_RATIO, 1.0),
    (-_CROSS_RATIO, _CROSS_RATIO), (-1.0, _CROSS_RATIO),
    (-1.0, -_CROSS_RATIO), (-_CROSS_RATIO, -_CROSS_RATIO),
)
# Precomputed unit capsule vertices (normalized to size=1.0)
_UNIT_CAPSULE = []
for _s_idx in range(9):
    _th = -math.pi / 2 + (math.pi * _s_idx / 8)
    _UNIT_CAPSULE.append((0.675 + math.cos(_th) * 0.52, math.sin(_th) * 0.52))
for _s_idx in range(9):
    _th = math.pi / 2 + (math.pi * _s_idx / 8)
    _UNIT_CAPSULE.append((-0.675 + math.cos(_th) * 0.52, math.sin(_th) * 0.52))
_UNIT_CAPSULE = tuple(_UNIT_CAPSULE)

class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login_success, on_toggle_theme=None):
        self.theme_mode = config.get_theme() if hasattr(config, "get_theme") else "light"
        if self.theme_mode not in _LOGIN_PALETTES:
            self.theme_mode = "light"
        prefs = getattr(config, "UI_PREFS", {})
        self.lang_choice = prefs.get("language", "English")
        if self.lang_choice not in _TRANSLATIONS:
            self.lang_choice = "English"
        self.font_choice = prefs.get("font", "Inter")
        self.size_choice = prefs.get("text_size", "M")
        if self.size_choice not in _SIZE_OFFSETS:
            self.size_choice = "M"
        p = _LOGIN_PALETTES[self.theme_mode]
        super().__init__(parent, bg=p["right_bg"])
        # Prevent external generic walker from fighting our custom split-screen palette
        self._theme_skip = True
        self.parent = parent
        self.on_login_success = on_login_success
        self.on_toggle_theme = on_toggle_theme
        self._img_refs = []
        self.is_pwd_visible = False
        self.is_settings_open = False
        self._active_dropdown = None
        self.settings_popover = None
        self._anim_after_id = None
        self._theme_fade_id = None
        self._last_frame_time = time.perf_counter()
        self._anim_phase = 0.0
        self._available_families = set()
        try:
            self._available_families = set(tkfont.families())
        except Exception:
            pass
        self._init_particles()
        self.setup_ui()
    def destroy(self):
        for aid in (self._anim_after_id, self._theme_fade_id):
            if aid is not None:
                try:
                    self.after_cancel(aid)
                except Exception:
                    pass
        self._anim_after_id = None
        self._theme_fade_id = None
        super().destroy()
    # ──────────────────────────────────────────────────────────────────────────
    # 60-FPS ZERO-ALLOCATION BACKGROUND MOTION ENGINE
    # ──────────────────────────────────────────────────────────────────────────
    def _init_particles(self):
        """Initializes gentle drifting pharmacy symbols and knowledge-analytics nodes."""
        rng = random.Random(42)
        self._left_particles = []
        kinds = ["cross", "pill", "node", "node", "cross", "pill", "node", "node", "cross", "node", "pill", "node"]
        for kind in kinds:
            self._left_particles.append({
                "kind": kind,
                "nx": rng.uniform(0.06, 0.94),
                "ny": rng.uniform(0.06, 0.94),
                "vx": rng.uniform(-0.011, 0.011) or 0.007,  # normalized units per second
                "vy": rng.uniform(-0.016, -0.006),          # gentle upward float per second
                "size": rng.uniform(9.5, 14.5) if kind != "node" else rng.uniform(3.5, 5.5),
                "angle": rng.uniform(0, math.pi * 2),
                "spin": rng.uniform(-0.45, 0.45),           # radians per second
                "phase": rng.uniform(0, math.pi * 2),
                "ids": (),
            })
        self._right_particles = []
        r_kinds = ["cross", "node", "pill", "node", "cross", "node", "pill", "node", "node", "cross"]
        for kind in r_kinds:
            self._right_particles.append({
                "kind": kind,
                "nx": rng.uniform(0.05, 0.95),
                "ny": rng.uniform(0.05, 0.95),
                "vx": rng.uniform(-0.009, 0.009) or 0.006,
                "vy": rng.uniform(-0.013, -0.005),
                "size": rng.uniform(8.5, 13.0) if kind != "node" else rng.uniform(3.0, 4.8),
                "angle": rng.uniform(0, math.pi * 2),
                "spin": rng.uniform(-0.38, 0.38),
                "phase": rng.uniform(0, math.pi * 2),
                "ids": (),
            })
    def _init_canvas_pool(self, canvas: tk.Canvas, particles: list, is_left: bool):
        """Pre-allocates all vector items once on the canvas so animation updates purely via .coords()."""
        p = self._p()
        node_col = p["anim_left_node"] if is_left else p["anim_right_node"]
        line_col = p["anim_left_line"] if is_left else p["anim_right_line"]
        shape_col = p["anim_left_shape"] if is_left else p["anim_right_shape"]
        wave_col = p["anim_left_wave"] if is_left else ""
        # 1. Pre-allocate pair connection lines (n * (n - 1) // 2)
        n = len(particles)
        pair_lines = []
        for _ in range(n * (n - 1) // 2):
            lid = canvas.create_line(-10, -10, -10, -10, fill=line_col, width=1, state="hidden", tags="bg_anim")
            pair_lines.append(lid)
        # 2. Pre-allocate flowing pulse waves on left canvas
        wave_ids = []
        if is_left:
            for _ in range(2):
                wid = canvas.create_line(0, 0, 10, 0, fill=wave_col, width=1.5, smooth=True, tags="bg_anim")
                wave_ids.append(wid)
        # 3. Pre-allocate particle shapes
        for pt in particles:
            kind = pt["kind"]
            if kind == "node":
                halo_id = canvas.create_oval(0, 0, 1, 1, outline=line_col, width=1, tags="bg_anim")
                dot_id = canvas.create_oval(0, 0, 1, 1, fill=node_col, outline="", tags="bg_anim")
                pt["ids"] = (dot_id, halo_id)
            elif kind == "cross":
                poly_id = canvas.create_polygon(0, 0, 1, 1, 2, 2, outline=shape_col, fill="", width=1.5, tags="bg_anim")
                pt["ids"] = (poly_id,)
            elif kind == "pill":
                poly_id = canvas.create_polygon(0, 0, 1, 1, 2, 2, outline=shape_col, fill="", width=1.5, tags="bg_anim")
                seam_id = canvas.create_line(0, 0, 1, 1, fill=shape_col, width=1.2, tags="bg_anim")
                pt["ids"] = (poly_id, seam_id)
        if is_left:
            self._left_pair_lines = pair_lines
            self._left_wave_ids = wave_ids
        else:
            self._right_pair_lines = pair_lines
    def _recolor_canvas_pool(self, p: dict):
        """Updates colors of pre-allocated background animation items in-place without recreating them."""
        for lid in getattr(self, "_left_pair_lines", ()):
            self.left_canvas.itemconfigure(lid, fill=p["anim_left_line"])
        for wid in getattr(self, "_left_wave_ids", ()):
            self.left_canvas.itemconfigure(wid, fill=p["anim_left_wave"])
        for pt in self._left_particles:
            if pt["kind"] == "node":
                self.left_canvas.itemconfigure(pt["ids"][0], fill=p["anim_left_node"])
                self.left_canvas.itemconfigure(pt["ids"][1], outline=p["anim_left_line"])
            elif pt["kind"] == "cross":
                self.left_canvas.itemconfigure(pt["ids"][0], outline=p["anim_left_shape"])
            elif pt["kind"] == "pill":
                self.left_canvas.itemconfigure(pt["ids"][0], outline=p["anim_left_shape"])
                self.left_canvas.itemconfigure(pt["ids"][1], fill=p["anim_left_shape"])
        for lid in getattr(self, "_right_pair_lines", ()):
            self.right_canvas.itemconfigure(lid, fill=p["anim_right_line"])
        for pt in self._right_particles:
            if pt["kind"] == "node":
                self.right_canvas.itemconfigure(pt["ids"][0], fill=p["anim_right_node"])
                self.right_canvas.itemconfigure(pt["ids"][1], outline=p["anim_right_line"])
            elif pt["kind"] == "cross":
                self.right_canvas.itemconfigure(pt["ids"][0], outline=p["anim_right_shape"])
            elif pt["kind"] == "pill":
                self.right_canvas.itemconfigure(pt["ids"][0], outline=p["anim_right_shape"])
                self.right_canvas.itemconfigure(pt["ids"][1], fill=p["anim_right_shape"])
    def _start_animation(self):
        if self._anim_after_id is not None:
            try:
                self.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        self._last_frame_time = time.perf_counter()
        self._animate_step()
    def _animate_step(self):
        if self._anim_after_id is not None:
            try:
                self.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        if not self.winfo_exists():
            return
        now = time.perf_counter()
        dt = min(0.05, max(0.004, now - self._last_frame_time))
        self._last_frame_time = now
        self._anim_phase += dt * 1.35
        if hasattr(self, "left_canvas") and self.left_canvas.winfo_exists():
            lw = self.left_canvas.winfo_width()
            lh = self.left_canvas.winfo_height()
            if lw > 40 and lh > 40:
                self._update_panel_motion(
                    self.left_canvas, lw, lh, dt,
                    self._left_particles,
                    self._left_pair_lines,
                    self._left_wave_ids,
                )
        if hasattr(self, "right_canvas") and self.right_canvas.winfo_exists():
            rw = self.right_canvas.winfo_width()
            rh = self.right_canvas.winfo_height()
            if rw > 40 and rh > 40:
                self._update_panel_motion(
                    self.right_canvas, rw, rh, dt,
                    self._right_particles,
                    self._right_pair_lines,
                    (),
                )
        # ~60 FPS frame pacing (16ms)
        self._anim_after_id = self.after(16, self._animate_step)
    def _update_panel_motion(self, canvas: tk.Canvas, w: int, h: int, dt: float,
                             particles: list, pair_lines: list, wave_ids: tuple):
        phase = self._anim_phase
        coords = []
        # 1. Advance particle kinematics & update shape coordinates in-place
        for pt in particles:
            sway = math.sin(phase + pt["phase"]) * 0.0055
            pt["nx"] += (pt["vx"] + sway) * dt
            pt["ny"] += pt["vy"] * dt
            pt["angle"] += pt["spin"] * dt
            if pt["ny"] < -0.04:
                pt["ny"] = 1.04
            elif pt["ny"] > 1.04:
                pt["ny"] = -0.04
            if pt["nx"] < -0.04:
                pt["nx"] = 1.04
            elif pt["nx"] > 1.04:
                pt["nx"] = -0.04
            x = pt["nx"] * w
            y = pt["ny"] * h
            coords.append((x, y))
            kind = pt["kind"]
            sz = pt["size"]
            ang = pt["angle"]
            ids = pt["ids"]
            if kind == "node":
                dot_id, halo_id = ids
                canvas.coords(dot_id, x - sz, y - sz, x + sz, y + sz)
                halo = sz + 4.2 + math.sin(phase * 1.6 + pt["phase"]) * 2.0
                canvas.coords(halo_id, x - halo, y - halo, x + halo, y + halo)
            elif kind == "cross":
                poly_id = ids[0]
                ca = math.cos(ang) * sz
                sa = math.sin(ang) * sz
                poly = []
                for ux, uy in _UNIT_CROSS:
                    poly.append(x + ux * ca - uy * sa)
                    poly.append(y + ux * sa + uy * ca)
                canvas.coords(poly_id, *poly)
            elif kind == "pill":
                poly_id, seam_id = ids
                ca = math.cos(ang) * sz
                sa = math.sin(ang) * sz
                poly = []
                for ux, uy in _UNIT_CAPSULE:
                    poly.append(x + ux * ca - uy * sa)
                    poly.append(y + ux * sa + uy * ca)
                canvas.coords(poly_id, *poly)
                rx = -0.52 * sa
                ry = 0.52 * ca
                canvas.coords(seam_id, x - rx, y - ry, x + rx, y + ry)
        # 2. Update constellation connection lines in-place
        max_dist = min(w, h) * 0.28
        max_dist_sq = max_dist * max_dist
        n = len(coords)
        line_idx = 0
        for i in range(n):
            x1, y1 = coords[i]
            for j in range(i + 1, n):
                x2, y2 = coords[j]
                dx = x1 - x2
                dy = y1 - y2
                lid = pair_lines[line_idx]
                line_idx += 1
                if dx * dx + dy * dy < max_dist_sq:
                    canvas.coords(lid, x1, y1, x2, y2)
                    canvas.itemconfigure(lid, state="normal")
                else:
                    canvas.itemconfigure(lid, state="hidden")
        # 3. Update flowing Stock Pulse waves in-place
        if wave_ids:
            wave_specs = (
                (wave_ids[0], 0.91, 13.0, 0.011, 1.0),
                (wave_ids[1], 0.94, 8.5, 0.016, -0.75),
            )
            for wid, base_y_ratio, amp, freq, speed_mult in wave_specs:
                pts = []
                base_y = h * base_y_ratio
                w_phase = phase * speed_mult
                for x in range(0, w + 24, 24):
                    y = base_y + math.sin(x * freq + w_phase) * amp + math.cos(x * 0.0055 - w_phase) * (amp * 0.38)
                    pts.append(x)
                    pts.append(y)
                if len(pts) >= 4:
                    canvas.coords(wid, *pts)
    # ──────────────────────────────────────────────────────────────────────────
    # HELPERS: FONTS, TRANSLATIONS, AND CRISP GRAPHICS
    # ──────────────────────────────────────────────────────────────────────────
    def _resolve_font_family(self) -> str:
        if self.font_choice == "Inter":
            if "Inter" in self._available_families:
                return "Inter"
            if "Segoe UI Variable Text" in self._available_families:
                return "Segoe UI Variable Text"
            return "Segoe UI"
        if self.font_choice in self._available_families:
            return self.font_choice
        return "Segoe UI"
    def _f(self, base_pt: int, weight: str = "normal"):
        fam = self._resolve_font_family()
        offset = _SIZE_OFFSETS.get(self.size_choice, 0)
        pt = max(7, base_pt + offset)
        if weight == "bold":
            return (fam, pt, "bold")
        return (fam, pt)
    def _t(self, key: str) -> str:
        lang_map = _TRANSLATIONS.get(self.lang_choice, _TRANSLATIONS["English"])
        return lang_map.get(key, _TRANSLATIONS["English"].get(key, key))
    def _p(self) -> dict:
        return _LOGIN_PALETTES[self.theme_mode]
    def _draw_cross_logo(self, color: str, size: int = 28):
        """Draws the outlined blue medical cross icon matching the reference screenshot."""
        if not _PIL_AVAILABLE:
            return None
        scale = 4
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        m = int(s * 0.08)
        arm = int(s * 0.34)
        a1 = (s - arm) // 2
        a2 = a1 + arm
        pts = [
            (a1, m), (a2, m),
            (a2, a1), (s - m, a1),
            (s - m, a2), (a2, a2),
            (a2, s - m), (a1, s - m),
            (a1, a2), (m, a2),
            (m, a1), (a1, a1),
            (a1, m)
        ]
        stroke = max(4, int(2.3 * scale))
        d.line(pts, fill=color, width=stroke, joint="curve")
        final = img.resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(final)
        self._img_refs.append(photo)
        return photo
    def _draw_dot(self, color: str, size: int = 10):
        """Draws a crisp anti-aliased colored circle dot for quick access cards."""
        if not _PIL_AVAILABLE:
            return None
        scale = 4
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, s - 3, s - 3], fill=color)
        final = img.resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(final)
        self._img_refs.append(photo)
        return photo
    # ──────────────────────────────────────────────────────────────────────────
    # MAIN SPLIT LAYOUT (BUILT ONCE, UPDATED IN-PLACE)
    # ──────────────────────────────────────────────────────────────────────────
    def setup_ui(self):
        for child in self.winfo_children():
            child.destroy()
        self._img_refs.clear()
        p = self._p()
        self.configure(bg=p["right_bg"])
        # Master 50/50 split container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, uniform="login_half")
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1, uniform="login_half")
        # Left Panel (Canvas for seamless transparent background animation behind text)
        self.left_canvas = tk.Canvas(self, bg=p["left_bg"], highlightthickness=0, bd=0)
        self.left_canvas.grid(row=0, column=0, sticky="nsew")
        self.left_panel = self.left_canvas
        # 1px Vertical Divider
        self.split_line = tk.Frame(self, bg=p["split_border"], width=1)
        self.split_line.grid(row=0, column=1, sticky="ns")
        # Right Panel (Canvas for ambient background animation around login form)
        self.right_canvas = tk.Canvas(self, bg=p["right_bg"], highlightthickness=0, bd=0)
        self.right_canvas.grid(row=0, column=2, sticky="nsew")
        self.right_panel = self.right_canvas
        # Pre-allocate vector animation pools on both canvases
        self._init_canvas_pool(self.left_canvas, self._left_particles, is_left=True)
        self._init_canvas_pool(self.right_canvas, self._right_particles, is_left=False)
        self.left_canvas.bind("<Configure>", self._render_left_canvas_content)
        self._build_right_panel(self.right_canvas)
        if self.is_settings_open:
            self._show_settings_popover()
        self._start_animation()
    # ──────────────────────────────────────────────────────────────────────────
    # LEFT PANEL: BRAND, HEADLINE, SUBTITLE & NUMBERED FEATURES (01 - 04)
    # ──────────────────────────────────────────────────────────────────────────
    def _render_left_canvas_content(self, event=None):
        """Renders left-panel typography & dividers directly on left_canvas above the animated pool."""
        if not hasattr(self, "left_canvas") or not self.left_canvas.winfo_exists():
            return
        c = self.left_canvas
        c.delete("fg_content")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50 or h < 50:
            return
        p = self._p()
        content_w = min(440, max(280, w - 120))
        x0 = max(44, (w - content_w) // 2)
        total_h = 370
        y = max(40, (h - total_h) // 2)
        # 1. Brand Logo + "RestInPills"
        if not hasattr(self, "_cached_cross_logo") or getattr(self, "_cached_cross_color", None) != p["accent"]:
            self._cached_cross_logo = self._draw_cross_logo(p["accent"], size=28)
            self._cached_cross_color = p["accent"]
        if self._cached_cross_logo is not None:
            c.create_image(x0, y + 14, image=self._cached_cross_logo, anchor="w", tags=("fg_content", "fg_logo"))
            brand_x = x0 + 38
        else:
            c.create_text(x0, y + 14, text="✚", font=self._f(18, "bold"), fill=p["accent"], anchor="w", tags=("fg_content", "fg_accent"))
            brand_x = x0 + 32
        c.create_text(
            brand_x, y + 14,
            text=self._t("brand"),
            font=self._f(15, "bold"),
            fill=p["text_primary"],
            anchor="w",
            tags=("fg_content", "fg_primary"),
        )
        y += 54
        # 2. Headline: "Smart " (blue) + "pharmacy operations" (primary)
        head_font = tkfont.Font(font=self._f(24, "bold"))
        smart_txt = self._t("smart")
        ops_txt = self._t("ops")
        smart_w = head_font.measure(smart_txt)
        c.create_text(
            x0, y,
            text=smart_txt,
            font=self._f(24, "bold"),
            fill=p["accent"],
            anchor="nw",
            tags=("fg_content", "fg_accent"),
        )
        c.create_text(
            x0 + smart_w, y,
            text=ops_txt,
            font=self._f(24, "bold"),
            fill=p["text_primary"],
            anchor="nw",
            tags=("fg_content", "fg_primary"),
        )
        y += head_font.metrics("linespace") + 10
        # 3. Subtitle
        c.create_text(
            x0, y,
            text=self._t("hero_sub"),
            font=self._f(10),
            fill=p["text_muted"],
            anchor="nw",
            width=content_w,
            tags=("fg_content", "fg_muted"),
        )
        y += 42
        # 4. Numbered Feature List (01 - 04)
        features = [
            ("01", self._t("f1_title"), self._t("f1_sub")),
            ("02", self._t("f2_title"), self._t("f2_sub")),
            ("03", self._t("f3_title"), self._t("f3_sub")),
            ("04", self._t("f4_title"), self._t("f4_sub")),
        ]
        for num_str, title, subtitle in features:
            c.create_line(x0, y, x0 + content_w, y, fill=p["left_divider"], width=1, tags=("fg_content", "fg_divider"))
            y += 14
            c.create_text(
                x0, y + 2,
                text=num_str,
                font=self._f(9, "bold"),
                fill=p["accent"],
                anchor="nw",
                tags=("fg_content", "fg_accent"),
            )
            tx = x0 + 42
            c.create_text(
                tx, y,
                text=title,
                font=self._f(11, "bold"),
                fill=p["text_primary"],
                anchor="nw",
                tags=("fg_content", "fg_primary"),
            )
            c.create_text(
                tx, y + 21,
                text=subtitle,
                font=self._f(9),
                fill=p["text_muted"],
                anchor="nw",
                width=max(180, content_w - 42),
                tags=("fg_content", "fg_muted"),
            )
            y += 54
    # ──────────────────────────────────────────────────────────────────────────
    # RIGHT PANEL: SETTINGS BUTTON, CENTERED LOGIN FORM, QUICK ACCESS
    # ──────────────────────────────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        p = self._p()
        # ── Top-Right "⚙ Settings" Button ─────────────────────────────────────
        self.settings_btn_wrap = tk.Frame(
            parent,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.settings_btn_wrap.place(relx=1.0, x=-24, y=18, anchor="ne")
        self.lbl_gear = tk.Label(
            self.settings_btn_wrap,
            text="⚙",
            font=self._f(10),
            bg=p["surface"],
            fg=p["text_muted"],
            cursor="hand2",
        )
        self.lbl_gear.pack(side="left", padx=(0, 6))
        self.lbl_set_txt = tk.Label(
            self.settings_btn_wrap,
            text=self._t("settings"),
            font=self._f(9, "bold"),
            bg=p["surface"],
            fg=p["text_primary"],
            cursor="hand2",
        )
        self.lbl_set_txt.pack(side="left")
        for w in (self.settings_btn_wrap, self.lbl_gear, self.lbl_set_txt):
            w.bind("<Button-1>", lambda e: self._toggle_settings_popover())
            w.bind("<Enter>", lambda e: self._hover_card(self.settings_btn_wrap, [self.lbl_gear, self.lbl_set_txt], True))
            w.bind("<Leave>", lambda e: self._hover_card(self.settings_btn_wrap, [self.lbl_gear, self.lbl_set_txt], False))
        # ── Centered Form Box ─────────────────────────────────────────────────
        self.form_wrap = tk.Frame(parent, bg=p["right_bg"])
        self.form_wrap.place(relx=0.5, rely=0.5, anchor="center")
        self.form = tk.Frame(self.form_wrap, bg=p["right_bg"], width=390)
        self.form.pack(fill="both", expand=True)
        # 1. Welcome back heading
        self.lbl_welcome = tk.Label(
            self.form,
            text=self._t("welcome"),
            font=self._f(20, "bold"),
            bg=p["right_bg"],
            fg=p["text_primary"],
        )
        self.lbl_welcome.pack(anchor="w")
        self.lbl_welcome_sub = tk.Label(
            self.form,
            text=self._t("welcome_sub"),
            font=self._f(10),
            bg=p["right_bg"],
            fg=p["text_muted"],
        )
        self.lbl_welcome_sub.pack(anchor="w", pady=(4, 22))
        # 2. Username Field
        self.lbl_user_title = tk.Label(
            self.form,
            text=self._t("username"),
            font=self._f(9, "bold"),
            bg=p["right_bg"],
            fg=p["text_primary"],
        )
        self.lbl_user_title.pack(anchor="w", pady=(0, 6))
        self.user_box, self.ent_user = self._create_entry_box(self.form)
        self.user_box.pack(fill="x", pady=(0, 16))
        self.ent_user.focus_set()
        # 3. Password Field + Eye Toggle Button
        self.lbl_pwd_title = tk.Label(
            self.form,
            text=self._t("password"),
            font=self._f(9, "bold"),
            bg=p["right_bg"],
            fg=p["text_primary"],
        )
        self.lbl_pwd_title.pack(anchor="w", pady=(0, 6))
        self.pwd_row = tk.Frame(self.form, bg=p["right_bg"])
        self.pwd_row.pack(fill="x", pady=(0, 4))
        self.pwd_box, self.ent_pwd = self._create_entry_box(self.pwd_row, show="" if self.is_pwd_visible else "•")
        self.pwd_box.pack(side="left", fill="x", expand=True)
        self.btn_eye = tk.Button(
            self.pwd_row,
            text="🙈" if self.is_pwd_visible else "👁",
            font=self._f(10),
            bg=p["surface"],
            fg=p["accent"] if self.is_pwd_visible else p["text_muted"],
            activebackground=p["surface_hover"],
            activeforeground=p["text_primary"],
            relief="flat",
            bd=0,
            highlightbackground=p["border"],
            highlightthickness=1,
            cursor="hand2",
            padx=12,
            pady=9,
            command=self._toggle_pwd,
        )
        self.btn_eye.pack(side="right", padx=(8, 0))
        self.btn_eye.bind("<Enter>", lambda e: self.btn_eye.config(bg=self._p()["surface_hover"], highlightbackground=self._p()["border_hover"]))
        self.btn_eye.bind("<Leave>", lambda e: self.btn_eye.config(bg=self._p()["surface"], highlightbackground=self._p()["border"]))
        # 4. Feedback / Status Label
        self.lbl_msg = tk.Label(
            self.form,
            text="",
            font=self._f(9),
            bg=p["right_bg"],
            fg=config.COLORS["danger"],
            wraplength=380,
            justify="left",
        )
        self.lbl_msg.pack(anchor="w", pady=(4, 10))
        # 5. Primary Blue "Sign in to system →" Button
        self.btn_login = tk.Button(
            self.form,
            text=self._t("sign_in"),
            font=self._f(10, "bold"),
            bg=p["accent"],
            fg=p["accent_fg"],
            activebackground=p["accent_hover"],
            activeforeground=p["accent_fg"],
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=11,
            command=self.handle_login,
        )
        self.btn_login.pack(fill="x", pady=(0, 22))
        self.btn_login.bind("<Enter>", lambda e: self.btn_login.config(bg=self._p()["accent_hover"]))
        self.btn_login.bind("<Leave>", lambda e: self.btn_login.config(bg=self._p()["accent"]))
        # 6. Quick Access Divider
        self.div_row = tk.Frame(self.form, bg=p["right_bg"])
        self.div_row.pack(fill="x", pady=(0, 14))
        self.div_line_l = tk.Frame(self.div_row, bg=p["right_divider"], height=1)
        self.div_line_l.pack(side="left", fill="x", expand=True, pady=6)
        self.lbl_quick_access = tk.Label(
            self.div_row,
            text=self._t("quick_access"),
            font=self._f(8),
            bg=p["right_bg"],
            fg=p["text_muted"],
        )
        self.lbl_quick_access.pack(side="left")
        self.div_line_r = tk.Frame(self.div_row, bg=p["right_divider"], height=1)
        self.div_line_r.pack(side="left", fill="x", expand=True, pady=6)
        # 7. Quick Access Demo Pills (2x2 Grid)
        self.chips_grid = tk.Frame(self.form, bg=p["right_bg"])
        self.chips_grid.pack(fill="x")
        self.chips_grid.grid_columnconfigure(0, weight=1, uniform="q_col")
        self.chips_grid.grid_columnconfigure(1, weight=1, uniform="q_col")
        self._quick_pills = []
        roles = [
            ("role_admin",      "admin",           "admin123",      "dot_admin"),
            ("role_instructor", "instructor",      "instructor123", "dot_instructor"),
            ("role_clerk",      "inventory_clerk", "clerk123",      "dot_clerk"),
            ("role_sales",      "sales_personnel", "sales123",      "dot_sales"),
        ]
        for i, (role_key, u, p_val, dot_key) in enumerate(roles):
            r, c = divmod(i, 2)
            self._create_quick_pill(self.chips_grid, r, c, role_key, u, p_val, dot_key)
        # Keybindings
        self.ent_user.bind("<Return>", lambda e: self.ent_pwd.focus_set())
        self.ent_pwd.bind("<Return>", lambda e: self.handle_login())
    def _create_entry_box(self, parent, show=None):
        """Creates a sleek bordered input container that adapts cleanly to light and dark modes."""
        p = self._p()
        box = tk.Frame(
            parent,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightcolor=p["focus_border"],
            highlightthickness=1,
            padx=12,
            pady=9,
        )
        kw = dict(
            font=self._f(10),
            bg=p["surface"],
            fg=p["text_primary"],
            insertbackground=p["text_primary"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            width=28,
        )
        if show is not None:
            kw["show"] = show
        ent = tk.Entry(box, **kw)
        ent.pack(fill="x", expand=True)
        ent.bind("<FocusIn>", lambda e: box.config(highlightbackground=self._p()["focus_border"]))
        ent.bind("<FocusOut>", lambda e: box.config(highlightbackground=self._p()["border"]))
        return box, ent
    def _create_quick_pill(self, parent, r, c, role_key, username, password, dot_key):
        p = self._p()
        label_text = self._t(role_key)
        dot_col = p[dot_key]
        padx_cell = (0, 5) if c == 0 else (5, 0)
        pill = tk.Frame(
            parent,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
            cursor="hand2",
            padx=14,
            pady=10,
        )
        pill.grid(row=r, column=c, sticky="nsew", padx=padx_cell, pady=4)
        dot_photo = self._draw_dot(dot_col, size=9)
        if dot_photo is not None:
            dot = tk.Label(pill, image=dot_photo, bg=p["surface"], bd=0, cursor="hand2")
        else:
            dot = tk.Label(pill, text="●", font=self._f(10), bg=p["surface"], fg=dot_col, cursor="hand2")
        dot.pack(side="left", padx=(0, 8))
        text_lbl = tk.Label(
            pill,
            text=label_text,
            font=self._f(9, "bold"),
            bg=p["surface"],
            fg=p["text_primary"],
            cursor="hand2",
        )
        text_lbl.pack(side="left")
        self._quick_pills.append({
            "pill": pill,
            "dot": dot,
            "text_lbl": text_lbl,
            "role_key": role_key,
            "dot_key": dot_key,
            "username": username,
            "password": password,
        })
        def on_click(e):
            self.fill_quick(username, password, self._t(role_key))
        def on_enter(e):
            cur = self._p()
            pill.config(bg=cur["surface_hover"], highlightbackground=cur["border_hover"])
            dot.config(bg=cur["surface_hover"])
            text_lbl.config(bg=cur["surface_hover"])
        def on_leave(e):
            cur = self._p()
            pill.config(bg=cur["surface"], highlightbackground=cur["border"])
            dot.config(bg=cur["surface"])
            text_lbl.config(bg=cur["surface"])
        for widget in (pill, dot, text_lbl):
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    def _hover_card(self, frame, children, entering: bool):
        p = self._p()
        bg = p["surface_hover"] if entering else p["surface"]
        bd = p["border_hover"] if entering else p["border"]
        frame.config(bg=bg, highlightbackground=bd)
        for ch in children:
            ch.config(bg=bg)
    # ──────────────────────────────────────────────────────────────────────────
    # SETTINGS POPOVER (APPEARANCE, LANGUAGE, FONT, TEXT SIZE)
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_settings_popover(self):
        self._close_dropdown()
        if self.is_settings_open:
            self._hide_settings_popover()
        else:
            self._show_settings_popover()
    def _hide_settings_popover(self):
        self._close_dropdown()
        self.is_settings_open = False
        if self.settings_popover is not None and self.settings_popover.winfo_exists():
            self.settings_popover.destroy()
        self.settings_popover = None
    def _show_settings_popover(self):
        self._close_dropdown()
        if self.settings_popover is not None and self.settings_popover.winfo_exists():
            self.settings_popover.destroy()
        self.is_settings_open = True
        p = self._p()
        self.settings_popover = tk.Frame(
            self.right_panel,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
            padx=18,
            pady=16,
            width=276,
        )
        self.settings_popover.place(relx=1.0, x=-24, y=58, anchor="ne")
        self.settings_popover.lift()
        # ── Header Row: "Settings" + [×] Close Button ─────────────────────────
        self._pop_hdr = tk.Frame(self.settings_popover, bg=p["surface"])
        self._pop_hdr.pack(fill="x", pady=(0, 12))
        self._pop_title = tk.Label(
            self._pop_hdr,
            text=self._t("settings"),
            font=self._f(11, "bold"),
            bg=p["surface"],
            fg=p["text_primary"],
        )
        self._pop_title.pack(side="left")
        self._pop_close = tk.Button(
            self._pop_hdr,
            text="×",
            font=self._f(10, "bold"),
            bg=p["surface"],
            fg=p["text_muted"],
            activebackground=p["surface_hover"],
            activeforeground=p["text_primary"],
            relief="flat",
            bd=0,
            highlightbackground=p["border"],
            highlightthickness=1,
            width=2,
            pady=2,
            cursor="hand2",
            command=self._hide_settings_popover,
        )
        self._pop_close.pack(side="right")
        # ── 1. Appearance: Light mode | Dark mode ─────────────────────────────
        self._pop_lbl_app = tk.Label(
            self.settings_popover,
            text=self._t("appearance"),
            font=self._f(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._pop_lbl_app.pack(anchor="w", pady=(0, 6))
        self._pop_app_row = tk.Frame(self.settings_popover, bg=p["surface"])
        self._pop_app_row.pack(fill="x", pady=(0, 12))
        self._pop_app_row.grid_columnconfigure(0, weight=1, uniform="app_mode")
        self._pop_app_row.grid_columnconfigure(1, weight=1, uniform="app_mode")
        self._btn_mode_light = self._make_segmented_btn(
            self._pop_app_row, 0, self._t("light_mode"),
            active=(self.theme_mode == "light"),
            command=lambda: self._set_appearance("light"),
            padx=(0, 4),
        )
        self._btn_mode_dark = self._make_segmented_btn(
            self._pop_app_row, 1, self._t("dark_mode"),
            active=(self.theme_mode == "dark"),
            command=lambda: self._set_appearance("dark"),
            padx=(4, 0),
        )
        # ── 2. Language Dropdown ──────────────────────────────────────────────
        self._pop_lbl_lang = tk.Label(
            self.settings_popover,
            text=self._t("language"),
            font=self._f(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._pop_lbl_lang.pack(anchor="w", pady=(0, 6))
        self._lang_box, self._lang_val_lbl, self._lang_chev_lbl = self._make_dropdown_selector(
            self.settings_popover,
            current_val=self.lang_choice,
            options=_LANG_OPTIONS,
            on_select=self._set_language,
        )
        self._lang_box.pack(fill="x", pady=(0, 12))
        # ── 3. Font Dropdown ──────────────────────────────────────────────────
        self._pop_lbl_font = tk.Label(
            self.settings_popover,
            text=self._t("font"),
            font=self._f(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._pop_lbl_font.pack(anchor="w", pady=(0, 6))
        self._font_box, self._font_val_lbl, self._font_chev_lbl = self._make_dropdown_selector(
            self.settings_popover,
            current_val=self.font_choice,
            options=_FONT_OPTIONS,
            on_select=self._set_font,
        )
        self._font_box.pack(fill="x", pady=(0, 12))
        # ── 4. Text size: S | M | L | XL ──────────────────────────────────────
        self._pop_lbl_sz = tk.Label(
            self.settings_popover,
            text=self._t("text_size"),
            font=self._f(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._pop_lbl_sz.pack(anchor="w", pady=(0, 6))
        self._pop_sz_row = tk.Frame(self.settings_popover, bg=p["surface"])
        self._pop_sz_row.pack(fill="x")
        self._size_btns = {}
        for idx, sz in enumerate(["S", "M", "L", "XL"]):
            self._pop_sz_row.grid_columnconfigure(idx, weight=1, uniform="sz_col")
            px = (0, 3) if idx == 0 else ((3, 0) if idx == 3 else (3, 3))
            self._size_btns[sz] = self._make_segmented_btn(
                self._pop_sz_row, idx, sz,
                active=(self.size_choice == sz),
                command=lambda s=sz: self._set_text_size(s),
                padx=px,
            )
    def _make_segmented_btn(self, parent, col, text, active: bool, command, padx=(0, 0)):
        p = self._p()
        bg = p["accent"] if active else p["surface"]
        fg = p["accent_fg"] if active else p["text_primary"]
        bd_col = p["accent"] if active else p["border"]
        btn = tk.Button(
            parent,
            text=text,
            font=self._f(8, "bold"),
            bg=bg,
            fg=fg,
            activebackground=p["accent_hover"] if active else p["surface_hover"],
            activeforeground=fg,
            relief="flat",
            bd=0,
            highlightbackground=bd_col,
            highlightthickness=1,
            pady=7,
            padx=10,
            cursor="hand2",
            command=command,
        )
        btn.grid(row=0, column=col, sticky="ew", padx=padx)
        return btn
    def _make_dropdown_selector(self, parent, current_val: str, options: list, on_select):
        p = self._p()
        box = tk.Frame(
            parent,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
            padx=10,
            pady=6,
            cursor="hand2",
        )
        lbl_val = tk.Label(
            box,
            text=current_val,
            font=self._f(9, "bold"),
            bg=p["surface"],
            fg=p["text_primary"],
            anchor="w",
            cursor="hand2",
        )
        lbl_val.pack(side="left", fill="x", expand=True)
        lbl_chev = tk.Label(
            box,
            text="⌄",
            font=self._f(9, "bold"),
            bg=p["surface"],
            fg=p["text_muted"],
            cursor="hand2",
        )
        lbl_chev.pack(side="right")
        def open_menu(e):
            self._open_dropdown_menu(box, options, lbl_val.cget("text"), on_select)
        for w in (box, lbl_val, lbl_chev):
            w.bind("<Button-1>", open_menu)
            w.bind("<Enter>", lambda e: self._hover_card(box, [lbl_val, lbl_chev], True))
            w.bind("<Leave>", lambda e: self._hover_card(box, [lbl_val, lbl_chev], False))
        return box, lbl_val, lbl_chev
    def _close_dropdown(self):
        if self._active_dropdown is not None and self._active_dropdown.winfo_exists():
            self._active_dropdown.destroy()
        self._active_dropdown = None
    def _open_dropdown_menu(self, anchor_widget, options: list, current_val: str, on_select):
        self._close_dropdown()
        p = self._p()
        anchor_widget.update_idletasks()
        ax = anchor_widget.winfo_rootx() - self.right_panel.winfo_rootx()
        ay = anchor_widget.winfo_rooty() - self.right_panel.winfo_rooty() + anchor_widget.winfo_height() + 2
        aw = anchor_widget.winfo_width()
        menu_frame = tk.Frame(
            self.right_panel,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
        )
        menu_frame.place(x=ax, y=ay, width=aw)
        menu_frame.lift()
        self._active_dropdown = menu_frame
        for opt in options:
            is_sel = (opt == current_val)
            item = tk.Label(
                menu_frame,
                text=opt,
                font=self._f(9, "bold" if is_sel else "normal"),
                bg=p["surface_hover"] if is_sel else p["surface"],
                fg=p["accent"] if is_sel else p["text_primary"],
                anchor="w",
                padx=10,
                pady=6,
                cursor="hand2",
            )
            item.pack(fill="x")
            item.bind("<Button-1>", lambda e, val=opt: (self._close_dropdown(), on_select(val)))
            item.bind("<Enter>", lambda e, w=item: w.config(bg=self._p()["surface_hover"]))
            item.bind("<Leave>", lambda e, w=item, s=is_sel: w.config(bg=self._p()["surface_hover"] if s else self._p()["surface"]))
    # ──────────────────────────────────────────────────────────────────────────
    # IN-PLACE SMOOTH UPDATES (ZERO WIDGET DESTRUCTION)
    # ──────────────────────────────────────────────────────────────────────────
    def _style_segmented_btn(self, btn: tk.Button, active: bool, p: dict):
        bg = p["accent"] if active else p["surface"]
        fg = p["accent_fg"] if active else p["text_primary"]
        bd_col = p["accent"] if active else p["border"]
        btn.config(
            bg=bg,
            fg=fg,
            activebackground=p["accent_hover"] if active else p["surface_hover"],
            activeforeground=fg,
            highlightbackground=bd_col,
            font=self._f(8, "bold"),
        )
    def _apply_palette_snapshot(self, p: dict, final_pass: bool = False):
        """Applies a palette dict (either interpolated mid-transition or final) across all LoginScreen elements."""
        if not self.winfo_exists() or not hasattr(self, "left_canvas") or not self.left_canvas.winfo_exists():
            return
        self.configure(bg=p["right_bg"])
        self.left_canvas.configure(bg=p["left_bg"])
        self.right_canvas.configure(bg=p["right_bg"])
        self.split_line.configure(bg=p["split_border"])
        # Left canvas foreground items
        self.left_canvas.itemconfigure("fg_primary", fill=p["text_primary"])
        self.left_canvas.itemconfigure("fg_muted", fill=p["text_muted"])
        self.left_canvas.itemconfigure("fg_accent", fill=p["accent"])
        self.left_canvas.itemconfigure("fg_divider", fill=p["left_divider"])
        if final_pass:
            self._cached_cross_logo = self._draw_cross_logo(p["accent"], size=28)
            self._cached_cross_color = p["accent"]
            if self._cached_cross_logo is not None:
                self.left_canvas.itemconfigure("fg_logo", image=self._cached_cross_logo)
        # Background animation pools
        self._recolor_canvas_pool(p)
        # Settings button
        self.settings_btn_wrap.configure(bg=p["surface"], highlightbackground=p["border"])
        self.lbl_gear.configure(bg=p["surface"], fg=p["text_muted"])
        self.lbl_set_txt.configure(bg=p["surface"], fg=p["text_primary"])
        # Right panel form
        for f in (self.form_wrap, self.form, self.pwd_row, self.div_row, self.chips_grid):
            f.configure(bg=p["right_bg"])
        for lbl in (self.lbl_welcome, self.lbl_user_title, self.lbl_pwd_title):
            lbl.configure(bg=p["right_bg"], fg=p["text_primary"])
        for lbl in (self.lbl_welcome_sub, self.lbl_quick_access):
            lbl.configure(bg=p["right_bg"], fg=p["text_muted"])
        self.lbl_msg.configure(bg=p["right_bg"])
        self.div_line_l.configure(bg=p["right_divider"])
        self.div_line_r.configure(bg=p["right_divider"])
        # Entries
        focused_w = self.focus_get()
        for box, ent in ((self.user_box, self.ent_user), (self.pwd_box, self.ent_pwd)):
            is_foc = (focused_w == ent)
            box.configure(
                bg=p["surface"],
                highlightbackground=p["focus_border"] if is_foc else p["border"],
                highlightcolor=p["focus_border"],
            )
            ent.configure(
                bg=p["surface"],
                fg=p["text_primary"],
                insertbackground=p["text_primary"],
            )
        self.btn_eye.configure(
            bg=p["surface"],
            fg=p["accent"] if self.is_pwd_visible else p["text_muted"],
            activebackground=p["surface_hover"],
            activeforeground=p["text_primary"],
            highlightbackground=p["border"],
        )
        self.btn_login.configure(
            bg=p["accent"],
            fg=p["accent_fg"],
            activebackground=p["accent_hover"],
            activeforeground=p["accent_fg"],
        )
        # Quick access pills
        for info in self._quick_pills:
            info["pill"].configure(bg=p["surface"], highlightbackground=p["border"])
            info["dot"].configure(bg=p["surface"])
            info["text_lbl"].configure(bg=p["surface"], fg=p["text_primary"])
            if final_pass:
                dot_photo = self._draw_dot(p[info["dot_key"]], size=9)
                if dot_photo is not None:
                    info["dot"].configure(image=dot_photo)
        # Settings popover if open
        if self.settings_popover is not None and self.settings_popover.winfo_exists():
            self.settings_popover.configure(bg=p["surface"], highlightbackground=p["border"])
            for f in (self._pop_hdr, self._pop_app_row, self._pop_sz_row):
                f.configure(bg=p["surface"])
            self._pop_title.configure(bg=p["surface"], fg=p["text_primary"])
            self._pop_close.configure(
                bg=p["surface"],
                fg=p["text_muted"],
                activebackground=p["surface_hover"],
                activeforeground=p["text_primary"],
                highlightbackground=p["border"],
            )
            for lbl in (self._pop_lbl_app, self._pop_lbl_lang, self._pop_lbl_font, self._pop_lbl_sz):
                lbl.configure(bg=p["surface"], fg=p["text_muted"])
            self._style_segmented_btn(self._btn_mode_light, self.theme_mode == "light", p)
            self._style_segmented_btn(self._btn_mode_dark, self.theme_mode == "dark", p)
            for sz, btn in self._size_btns.items():
                self._style_segmented_btn(btn, self.size_choice == sz, p)
            for box, val_l, chv_l in (
                (self._lang_box, self._lang_val_lbl, self._lang_chev_lbl),
                (self._font_box, self._font_val_lbl, self._font_chev_lbl),
            ):
                box.configure(bg=p["surface"], highlightbackground=p["border"])
                val_l.configure(bg=p["surface"], fg=p["text_primary"])
                chv_l.configure(bg=p["surface"], fg=p["text_muted"])
    def _animate_theme_transition(self, old_mode: str, new_mode: str, duration_ms: int = 180):
        """Smoothly cross-fades all LoginScreen colors from old_mode to new_mode with cubic ease-out."""
        if self._theme_fade_id is not None:
            try:
                self.after_cancel(self._theme_fade_id)
            except Exception:
                pass
            self._theme_fade_id = None
        p_start = _LOGIN_PALETTES[old_mode]
        p_end = _LOGIN_PALETTES[new_mode]
        keys = tuple(p_end.keys())
        start_t = time.perf_counter()
        dur_s = max(0.05, duration_ms / 1000.0)
        def step():
            self._theme_fade_id = None
            if not self.winfo_exists():
                return
            elapsed = time.perf_counter() - start_t
            t = min(1.0, elapsed / dur_s)
            inv = 1.0 - t
            eased = 1.0 - (inv * inv * inv)
            if t >= 1.0:
                self._apply_palette_snapshot(p_end, final_pass=True)
            else:
                blended = {k: lerp_hex(p_start[k], p_end[k], eased) for k in keys}
                self._apply_palette_snapshot(blended, final_pass=False)
                self._theme_fade_id = self.after(16, step)
        step()
    def _refresh_typography_and_text(self):
        """Updates all fonts and translated strings in-place without destroying widgets."""
        p = self._p()
        self._render_left_canvas_content()
        self.lbl_gear.configure(font=self._f(10))
        self.lbl_set_txt.configure(text=self._t("settings"), font=self._f(9, "bold"))
        self.lbl_welcome.configure(text=self._t("welcome"), font=self._f(20, "bold"))
        self.lbl_welcome_sub.configure(text=self._t("welcome_sub"), font=self._f(10))
        self.lbl_user_title.configure(text=self._t("username"), font=self._f(9, "bold"))
        self.lbl_pwd_title.configure(text=self._t("password"), font=self._f(9, "bold"))
        self.ent_user.configure(font=self._f(10))
        self.ent_pwd.configure(font=self._f(10))
        self.btn_eye.configure(font=self._f(10))
        self.lbl_msg.configure(font=self._f(9))
        self.btn_login.configure(text=self._t("sign_in"), font=self._f(10, "bold"))
        self.lbl_quick_access.configure(text=self._t("quick_access"), font=self._f(8))
        for info in self._quick_pills:
            info["text_lbl"].configure(text=self._t(info["role_key"]), font=self._f(9, "bold"))
        if self.settings_popover is not None and self.settings_popover.winfo_exists():
            self._pop_title.configure(text=self._t("settings"), font=self._f(11, "bold"))
            self._pop_close.configure(font=self._f(10, "bold"))
            self._pop_lbl_app.configure(text=self._t("appearance"), font=self._f(8))
            self._pop_lbl_lang.configure(text=self._t("language"), font=self._f(8))
            self._pop_lbl_font.configure(text=self._t("font"), font=self._f(8))
            self._pop_lbl_sz.configure(text=self._t("text_size"), font=self._f(8))
            self._btn_mode_light.configure(text=self._t("light_mode"))
            self._btn_mode_dark.configure(text=self._t("dark_mode"))
            self._style_segmented_btn(self._btn_mode_light, self.theme_mode == "light", p)
            self._style_segmented_btn(self._btn_mode_dark, self.theme_mode == "dark", p)
            for sz, btn in self._size_btns.items():
                self._style_segmented_btn(btn, self.size_choice == sz, p)
            self._lang_val_lbl.configure(text=self.lang_choice, font=self._f(9, "bold"))
            self._lang_chev_lbl.configure(font=self._f(9, "bold"))
            self._font_val_lbl.configure(text=self.font_choice, font=self._f(9, "bold"))
            self._font_chev_lbl.configure(font=self._f(9, "bold"))
    # ── Settings State Handlers ───────────────────────────────────────────────
    def _set_appearance(self, mode: str):
        if mode == self.theme_mode or mode not in _LOGIN_PALETTES:
            return
        old_mode = self.theme_mode
        self.theme_mode = mode
        if hasattr(config, "set_theme"):
            config.set_theme(mode)
        top = self.winfo_toplevel()
        if hasattr(top, "setup_ttk_styles"):
            try:
                top.setup_ttk_styles()
            except Exception:
                pass
        self._animate_theme_transition(old_mode, mode, duration_ms=180)
    def _set_language(self, lang: str):
        if lang == self.lang_choice:
            return
        self.lang_choice = lang
        if hasattr(config, "UI_PREFS"):
            config.UI_PREFS["language"] = lang
        self._refresh_typography_and_text()
    def _set_font(self, font_name: str):
        if font_name == self.font_choice:
            return
        self.font_choice = font_name
        if hasattr(config, "UI_PREFS"):
            config.UI_PREFS["font"] = font_name
        self._refresh_typography_and_text()
    def _set_text_size(self, sz: str):
        if sz == self.size_choice:
            return
        self.size_choice = sz
        if hasattr(config, "UI_PREFS"):
            config.UI_PREFS["text_size"] = sz
        self._refresh_typography_and_text()
    def apply_theme(self):
        """Compatible hook if parent window triggers a theme refresh."""
        new_mode = config.get_theme() if hasattr(config, "get_theme") else "light"
        if new_mode != self.theme_mode and new_mode in _LOGIN_PALETTES:
            old_mode = self.theme_mode
            self.theme_mode = new_mode
            self._animate_theme_transition(old_mode, new_mode, duration_ms=180)
    # ──────────────────────────────────────────────────────────────────────────
    # LOGIC & AUTHENTICATION (Maintained)
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_pwd(self):
        p = self._p()
        self.is_pwd_visible = not self.is_pwd_visible
        if self.is_pwd_visible:
            self.ent_pwd.config(show="")
            self.btn_eye.config(text="🙈", fg=p["accent"])
        else:
            self.ent_pwd.config(show="•")
            self.btn_eye.config(text="👁", fg=p["text_muted"])
    def fill_quick(self, username, password, role_label=""):
        p = self._p()
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, username)
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, password)
        self.lbl_msg.config(
            text=f"✓ Loaded {role_label} credentials",
            fg=p["accent"],
        )
    def handle_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pwd.get()
        if not username or not password:
            self.lbl_msg.config(text="Please enter both username and password.", fg="#dc2626")
            return
        self.lbl_msg.config(text="Authenticating credentials…", fg="#0284c7")
        self.update_idletasks()
        success, msg, user_data = auth.authenticate_user(username, password)
        if success:
            self.lbl_msg.config(text="Login successful! Redirecting…", fg="#16a34a")
            self.on_login_success(user_data)
        else:
            self.lbl_msg.config(text=msg, fg="#dc2626")
            self.ent_pwd.delete(0, tk.END)
            self.ent_pwd.focus_set()
