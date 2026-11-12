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

