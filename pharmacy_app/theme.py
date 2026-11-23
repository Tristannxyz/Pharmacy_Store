"""Smooth color-interpolation helpers for transitioning between Light and Dark themes."""
import time
import tkinter as tk
from tkinter import ttk
import config

_BG_ATTRS = ("bg", "highlightbackground", "activebackground", "selectcolor")
_FG_ATTRS = ("fg", "activeforeground", "insertbackground")
_ALL_ATTRS = _BG_ATTRS + _FG_ATTRS

_LIME_HEX = "#a3e635"


def hex_to_rgb(hex_str: str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolates two #RRGGBB colors for t in [0.0, 1.0]."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _build_lookup_maps(prev_mode: str, new_mode: str, in_login: bool):
    old_c = config.THEMES[prev_mode]
    new_c = config.THEMES[new_mode]

    if in_login:
        bg_keys = (
            "login_panel_r",
            "login_field_bg",
            "login_field_border",
            "login_pill_hover",
            "login_pill_border_hover",
            "login_divider",
            "surface_alt",
            "border",
            "secondary",
            "secondary_dark",
            "accent",
            "danger",
        )
    else:
        bg_keys = (
            "surface",
            "background",
            "surface_alt",
            "border",
            "primary",
            "primary_light",
            "secondary",
            "secondary_dark",
            "accent",
            "accent_hover",
            "danger",
            "warning",
            "success",
            "info",
            "tile_trend_bg",
            "tile_card_bg",
            "tile_box_bg",
            "tile_alert_bg",
            "tile_clock_bg",
            "tile_star_bg",
            "pill_track",
            "pos_bg",
            "pos_card",
            "pos_border",
            "pos_chip",
            "pos_input",
            "pos_teal",
            "pos_badge_green_bg",
            "pos_badge_warn_bg",
            "pos_badge_danger_bg",
            "pos_chip_active",
            "pos_totals_bg",
            "pos_stepper_bg",
            "pos_stepper_border",
            "pos_divider",
        )

    fg_keys = (
        "text_dark",
        "text_muted",
        "text_subtle",
        "secondary",
        "secondary_dark",
        "accent",
        "danger",
        "warning",
        "success",
        "info",
        "pos_text",
        "pos_muted",
        "pos_teal",
        "pos_badge_green_fg",
        "pos_badge_warn_fg",
        "pos_badge_danger_fg",
        "pos_blue",
    )

    bg_map = {}
    for k in bg_keys:
        o, n = old_c[k].lower(), new_c[k].lower()
        if o != n and o not in bg_map:
            bg_map[o] = n

    fg_map = {}
    for k in fg_keys:
        o, n = old_c[k].lower(), new_c[k].lower()
        if o != n and o not in fg_map:
            fg_map[o] = n

    return bg_map, fg_map


def collect_transition_targets(root_widget, prev_mode: str, new_mode: str, in_login: bool = False):
    """Collects (widget, attr, start_hex, end_hex) pairs across non-skipped tk widgets."""
    bg_map, fg_map = _build_lookup_maps(prev_mode, new_mode, in_login)
    targets = []

    def walk(w):
        if getattr(w, "_theme_skip", False):
            return

        if not isinstance(w, ttk.Widget):
            try:
                cur_bg = str(w.cget("bg")).lower()
            except tk.TclError:
                cur_bg = ""

            on_lime = cur_bg == _LIME_HEX

            for attr in _ALL_ATTRS:
                try:
                    val = str(w.cget(attr)).lower()
                except tk.TclError:
                    continue
                if not val.startswith("#") or len(val) != 7:
                    continue

                if attr in _BG_ATTRS:
                    dest = bg_map.get(val)
                else:
                    # Keep dark text readable on bright lime pills/buttons
                    if on_lime:
                        continue
                    dest = fg_map.get(val)

                if dest and dest != val:
                    targets.append((w, attr, val, dest))

        for child in w.winfo_children():
            walk(child)

    walk(root_widget)
    return targets


class ThemeAnimator:
    """Runs an eased multi-frame color transition and cancels cleanly on rapid re-toggles."""

    def __init__(self, root_tk):
        self.root = root_tk
        self._after_id = None
        self._active_targets = []
        self._on_complete = None

    def finish_immediately(self):
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

        for w, attr, _, end_hex in self._active_targets:
            try:
                if w.winfo_exists():
                    w.configure(**{attr: end_hex})
            except tk.TclError:
                pass

        cb = self._on_complete
        self._active_targets = []
        self._on_complete = None
        if cb:
            cb()

    def start(self, targets, duration_ms=220, steps=14, on_complete=None):
        self.finish_immediately()

        if not targets or steps <= 1:
            for w, attr, _, end_hex in targets:
                try:
                    if w.winfo_exists():
                        w.configure(**{attr: end_hex})
                except tk.TclError:
                    pass
            if on_complete:
                on_complete()
            return

        self._active_targets = targets
        self._on_complete = on_complete
        duration_s = max(0.05, duration_ms / 1000.0)
        interval = max(10, duration_ms // steps)
        start_t = time.perf_counter()

        def step_frame():
            self._after_id = None
            elapsed = time.perf_counter() - start_t
            t = min(1.0, max(0.04, elapsed / duration_s))
            # Cubic ease-out for silky, smooth deceleration
            inv = 1.0 - t
            eased = 1.0 - (inv * inv * inv)

            for w, attr, start_hex, end_hex in self._active_targets:
                try:
                    if w.winfo_exists():
                        col = end_hex if t >= 1.0 else lerp_hex(start_hex, end_hex, eased)
                        w.configure(**{attr: col})
                except tk.TclError:
                    pass

            if t < 1.0:
                self._after_id = self.root.after(interval, step_frame)
            else:
                cb = self._on_complete
                self._active_targets = []
                self._on_complete = None
                if cb:
                    cb()

        step_frame()


_CURRENT_ACTIVE_CANVAS = None
_GLOBAL_WHEEL_INITIALIZED = False

def _on_global_mousewheel(event):
    global _CURRENT_ACTIVE_CANVAS
    if _CURRENT_ACTIVE_CANVAS is not None and hasattr(_CURRENT_ACTIVE_CANVAS, "_smooth_scroller"):
        return _CURRENT_ACTIVE_CANVAS._smooth_scroller.on_wheel(event)


class SmoothScroller:
    """Provides buttery-smooth momentum scrolling for Tkinter Canvas widgets."""

    def __init__(self, canvas, friction=0.82, speed_factor=3.6):
        global _GLOBAL_WHEEL_INITIALIZED
        self.canvas = canvas
        self.canvas._smooth_scroller = self
        self.friction = friction
        self.speed_factor = speed_factor
        self.velocity = 0.0
        self._anim_job = None

        if not _GLOBAL_WHEEL_INITIALIZED:
            try:
                canvas.bind_all("<MouseWheel>", _on_global_mousewheel)
                _GLOBAL_WHEEL_INITIALIZED = True
            except Exception:
                pass

    def on_wheel(self, event):
        delta = event.delta
        if delta == 0:
            return "break"
        direction = -1.0 if delta > 0 else 1.0
        self.velocity += direction * (abs(delta) / 120.0) * self.speed_factor
        if self._anim_job is None:
            self._step()
        return "break"

    def _step(self):
        if abs(self.velocity) < 0.08:
            self.velocity = 0.0
            self._anim_job = None
            return

        try:
            y0, y1 = self.canvas.yview()
        except tk.TclError:
            self.velocity = 0.0
            self._anim_job = None
            return

        span = y1 - y0
        if span >= 1.0:
            self.velocity = 0.0
            self._anim_job = None
            return

        step_frac = (self.velocity * 0.012)
        new_top = max(0.0, min(1.0 - span, y0 + step_frac))
        self.canvas.yview_moveto(new_top)

        self.velocity *= self.friction
        self._anim_job = self.canvas.after(16, self._step)

    def attach_hover(self, *widgets):
        """Activates mousewheel globally while cursor hovers any attached widget."""
        def _on_enter(e):
            global _CURRENT_ACTIVE_CANVAS
            _CURRENT_ACTIVE_CANVAS = self.canvas

        def _on_leave(e):
            global _CURRENT_ACTIVE_CANVAS
            if _CURRENT_ACTIVE_CANVAS == self.canvas:
                _CURRENT_ACTIVE_CANVAS = None

        for w in widgets:
            if hasattr(w, "bind"):
                try:
                    w.bind("<Enter>", _on_enter, add="+")
                    w.bind("<Leave>", _on_leave, add="+")
                except tk.TclError:
                    pass


import math

class InnerMotionBackground:
    """
    Zero-allocation 60-FPS pharmacy-and-analytics animated background canvas
    (matches LoginScreen motion: drifting hollow medical crosses, tilted pill capsules,
    constellation nodes with connecting edges, and dual Stock Pulse waves)
    for inner application screens after login.
    """

    def __init__(self, parent_frame, bg_key: str = "background"):
        self.parent = parent_frame
        self.bg_key = bg_key
        self._after_id = None
        self._last_ts = time.perf_counter()
        self._phase = 0.0

        c_bg = config.COLORS.get(bg_key, config.COLORS["background"])
        self.canvas = tk.Canvas(parent_frame, bg=c_bg, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        try:
            tk.Misc.lower(self.canvas)
        except Exception:
            pass

        self._crosses = [
            {"rx": 0.10, "ry": 0.16, "size": 11, "speed": 0.011, "phase": 0.4, "sway": 16},
            {"rx": 0.86, "ry": 0.14, "size": 13, "speed": 0.009, "phase": 1.9, "sway": 20},
            {"rx": 0.74, "ry": 0.48, "size": 10, "speed": 0.013, "phase": 3.1, "sway": 15},
            {"rx": 0.22, "ry": 0.84, "size": 12, "speed": 0.010, "phase": 4.5, "sway": 18},
            {"rx": 0.90, "ry": 0.78, "size": 9,  "speed": 0.014, "phase": 5.7, "sway": 14},
            {"rx": 0.48, "ry": 0.28, "size": 10, "speed": 0.010, "phase": 2.3, "sway": 16},
        ]
        self._capsules = [
            {"rx": 0.66, "ry": 0.12, "len": 22, "rad": 5, "angle": 0.55, "speed": 0.008, "rot": 0.35, "phase": 0.8},
            {"rx": 0.91, "ry": 0.38, "len": 19, "rad": 4, "angle": -0.4, "speed": 0.010, "rot": -0.3, "phase": 2.3},
            {"rx": 0.60, "ry": 0.86, "len": 21, "rad": 5, "angle": 0.75, "speed": 0.009, "rot": 0.28, "phase": 4.1},
            {"rx": 0.18, "ry": 0.54, "len": 20, "rad": 5, "angle": -0.5, "speed": 0.009, "rot": 0.30, "phase": 1.4},
        ]
        self._nodes = [
            {"rx": 0.15, "ry": 0.22, "ax": 16, "ay": 12, "sx": 0.48, "sy": 0.42, "ph": 0.6, "r": 3.0},
            {"rx": 0.36, "ry": 0.18, "ax": 18, "ay": 14, "sx": 0.44, "sy": 0.50, "ph": 1.8, "r": 3.4},
            {"rx": 0.64, "ry": 0.18, "ax": 18, "ay": 14, "sx": 0.55, "sy": 0.45, "ph": 0.2, "r": 3.2},
            {"rx": 0.80, "ry": 0.26, "ax": 20, "ay": 15, "sx": 0.42, "sy": 0.52, "ph": 1.4, "r": 3.8},
            {"rx": 0.92, "ry": 0.20, "ax": 14, "ay": 16, "sx": 0.60, "sy": 0.38, "ph": 2.7, "r": 2.8},
            {"rx": 0.72, "ry": 0.46, "ax": 18, "ay": 14, "sx": 0.48, "sy": 0.46, "ph": 3.5, "r": 3.4},
            {"rx": 0.88, "ry": 0.54, "ax": 16, "ay": 18, "sx": 0.38, "sy": 0.56, "ph": 4.8, "r": 3.8},
            {"rx": 0.76, "ry": 0.72, "ax": 19, "ay": 13, "sx": 0.50, "sy": 0.40, "ph": 5.4, "r": 3.2},
        ]

        self._init_pool()
        self.canvas.bind("<Destroy>", self._on_destroy, add="+")
        self._step()

    def _palette(self):
        is_dark = config.get_theme() == "dark"
        if is_dark:
            return {
                "bg": config.COLORS.get(self.bg_key, "#0b111e"),
                "wave1": "#192b48",
                "wave2": "#13293d",
                "node": "#1e3a66",
                "edge": "#172a4a",
                "cross": "#1d3861",
                "pill": "#16354d",
            }
        return {
            "bg": config.COLORS.get(self.bg_key, "#f8fafc"),
            "wave1": "#dbe7fe",
            "wave2": "#e0f2fe",
            "node": "#cbdcfd",
            "edge": "#e1ebfe",
            "cross": "#c7dafc",
            "pill": "#cce5f8",
        }

    def _init_pool(self):
        p = self._palette()
        self._wave_ids = [
            self.canvas.create_line(0, 0, 1, 1, fill=p["wave1"], width=2, smooth=True),
            self.canvas.create_line(0, 0, 1, 1, fill=p["wave2"], width=1, smooth=True),
        ]
        n_nodes = len(self._nodes)
        self._edge_ids = [
            self.canvas.create_line(-10, -10, -10, -10, fill=p["edge"], width=1)
            for _ in range((n_nodes * (n_nodes - 1)) // 2)
        ]
        self._node_ids = [
            self.canvas.create_oval(-10, -10, -10, -10, fill=p["node"], outline="")
            for _ in range(n_nodes)
        ]
        self._cross_ids = [
            self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill="", outline=p["cross"], width=1)
            for _ in self._crosses
        ]
        self._cap_ids = [
            (
                self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill="", outline=p["pill"], width=1, smooth=True),
                self.canvas.create_line(0, 0, 0, 0, fill=p["pill"], width=1),
            )
            for _ in self._capsules
        ]

    def apply_theme(self):
        if not self.canvas.winfo_exists():
            return
        p = self._palette()
        self.canvas.configure(bg=p["bg"])
        self.canvas.itemconfigure(self._wave_ids[0], fill=p["wave1"])
        self.canvas.itemconfigure(self._wave_ids[1], fill=p["wave2"])
        for eid in self._edge_ids:
            self.canvas.itemconfigure(eid, fill=p["edge"])
        for nid in self._node_ids:
            self.canvas.itemconfigure(nid, fill=p["node"])
        for cid in self._cross_ids:
            self.canvas.itemconfigure(cid, outline=p["cross"])
        for bid, did in self._cap_ids:
            self.canvas.itemconfigure(bid, outline=p["pill"])
            self.canvas.itemconfigure(did, fill=p["pill"])

    def _step(self):
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        if not self.canvas.winfo_exists():
            return

        now = time.perf_counter()
        dt = min(0.05, max(0.004, now - self._last_ts))
        self._last_ts = now
        self._phase += dt * 1.45

        w = max(400, self.canvas.winfo_width())
        h = max(300, self.canvas.winfo_height())
        ph = self._phase

        # 1. Waves
        for w_idx, (base_r, amp, freq, spd) in enumerate(((0.90, 14.0, 2.2, 1.0), (0.94, 10.0, 3.1, -0.75))):
            base_y = h * base_r
            pts = []
            steps = 28
            for i in range(steps + 1):
                x = (w * i) / steps
                ang = (i / steps) * math.pi * freq + ph * spd
                y = base_y + math.sin(ang) * amp
                pts.extend((x, y))
            self.canvas.coords(self._wave_ids[w_idx], *pts)

        # 2. Nodes & Edges
        coords = []
        for idx, nd in enumerate(self._nodes):
            nx = nd["rx"] * w + math.sin(ph * nd["sx"] + nd["ph"]) * nd["ax"]
            ny = nd["ry"] * h + math.cos(ph * nd["sy"] + nd["ph"]) * nd["ay"]
            nr = nd["r"]
            coords.append((nx, ny))
            self.canvas.coords(self._node_ids[idx], nx - nr, ny - nr, nx + nr, ny + nr)

        max_d2 = (min(w, h) * 0.25) ** 2
        e_idx = 0
        for i in range(len(coords)):
            x1, y1 = coords[i]
            for j in range(i + 1, len(coords)):
                x2, y2 = coords[j]
                eid = self._edge_ids[e_idx]
                e_idx += 1
                if (x1 - x2) ** 2 + (y1 - y2) ** 2 < max_d2:
                    self.canvas.coords(eid, x1, y1, x2, y2)
                else:
                    self.canvas.coords(eid, -10, -10, -10, -10)

        # 3. Crosses
        for idx, cr in enumerate(self._crosses):
            cr["ry"] -= cr["speed"] * dt
            if cr["ry"] < -0.06:
                cr["ry"] = 1.06
            cx = cr["rx"] * w + math.sin(ph * 0.7 + cr["phase"]) * cr["sway"]
            cy = cr["ry"] * h
            s = cr["size"]
            a = s * 0.36
            self.canvas.coords(
                self._cross_ids[idx],
                cx - a, cy - s, cx + a, cy - s, cx + a, cy - a,
                cx + s, cy - a, cx + s, cy + a, cx + a, cy + a,
                cx + a, cy + s, cx - a, cy + s, cx - a, cy + a,
                cx - s, cy + a, cx - s, cy - a, cx - a, cy - a,
            )

        # 4. Capsules
        for idx, cp in enumerate(self._capsules):
            cp["ry"] -= cp["speed"] * dt
            if cp["ry"] < -0.06:
                cp["ry"] = 1.06
            cx = cp["rx"] * w + math.cos(ph * 0.55 + cp["phase"]) * 14.0
            cy = cp["ry"] * h
            ang = cp["angle"] + math.sin(ph * cp["rot"] + cp["phase"]) * 0.25
            ca, sa = math.cos(ang), math.sin(ang)
            hl = cp["len"] * 0.5
            r = cp["rad"]
            local_pts = [(-hl, -r), (hl, -r), (hl + r * 0.5, 0), (hl, r), (-hl, r), (-hl - r * 0.5, 0)]
            poly = []
            for lx, ly in local_pts:
                poly.extend((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca))
            bid, did = self._cap_ids[idx]
            self.canvas.coords(bid, *poly)
            self.canvas.coords(did, cx + r * sa, cy - r * ca, cx - r * sa, cy + r * ca)

        self._after_id = self.canvas.after(16, self._step)

    def _on_destroy(self, _event=None):
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


def attach_motion_bg(frame, bg_key: str = "background"):
    """Attaches InnerMotionBackground to a frame and stores it on frame._motion_bg."""
    try:
        bg = InnerMotionBackground(frame, bg_key=bg_key)
        frame._motion_bg = bg
        return bg
    except Exception:
        return None


