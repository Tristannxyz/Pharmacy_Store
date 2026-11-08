import os
import sys
import math
import ctypes
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFilter, ImageTk, ImageFont

import config
import auth

# ──────────────────────────────────────────────────────────────────────────────
# HIGH-DPI & FONT LOADING (Windows)
# ──────────────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

_FONTS_LOADED = False
_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_FONT_DIR = _ASSETS_DIR / "fonts"

if sys.platform == "win32" and _FONT_DIR.exists():
    try:
        FR_PRIVATE = 0x10
        for _f in ["SpaceGrotesk-Bold.ttf", "Inter.ttf"]:
            _fp = _FONT_DIR / _f
            if _fp.exists():
                _res = ctypes.windll.gdi32.AddFontResourceExW(str(_fp), FR_PRIVATE, 0)
                if _res > 0:
                    _FONTS_LOADED = True
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS: COLORS & SIZES (Single unified blocks, no magic numbers)
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {
    # Window & Panels
    "window_bg": "#050D17",
    "left_bg": "#0A2236",
    "right_bg": "#FFFFFF",

    # Accents & Brands
    "lime": "#B6F03C",
    "lime_hover": "#C4F65A",
    "lime_pressed": "#9ED82E",
    "teal": "#2DD4BF",
    "sky": "#38BDF8",
    "amber": "#FBBF24",
    "teal_accent": "#0FA593",
    "btn_text": "#06222A",

    # Typography
    "text_white": "#FFFFFF",
    "text_muted": "#9FB6C8",
    "text_dark": "#0A1A28",
    "text_sub": "#4A5B68",
    "text_label": "#14212B",

    # Inputs & Badges
    "input_bg": "#F4F8FA",
    "input_border": "#C4D0D8",
    "input_border_focus": "#0FA593",
    "badge_bg": "#E3F7F3",
    "badge_text": "#0B6B5E",

    # Dividers & Rings
    "divider_left": "#1B3347",
    "divider_right": "#D5DEE3",
    "ring_1": "#10304A",
    "ring_2": "#0E2840",
    "ring_3": "#0B2035",
    "ring_4": "#081A2B",

    # Feature Tiles
    "tile_ml_bg": "#12403F",
    "tile_dash_bg": "#11405A",
    "tile_auth_bg": "#4A3F1A",
    "tile_inv_bg": "#2F4A1B",

    # Status & Alerts
    "error": "#E11D48",
    "success": "#16A34A",
    "info": "#0FA593",
}

SIZES = {
    # Window
    "win_w": 1280,
    "win_h": 800,
    "win_min_w": 1000,
    "win_min_h": 700,

    # Card
    "card_w": 1040,
    "card_h": 600,
    "card_radius": 26,
    "left_w": 540,
    "right_w": 500,

    # Left Panel
    "left_pad_x": 44,
    "left_pad_y": 38,
    "logo_size": 32,
    "feature_tile_size": 40,
    "feature_tile_radius": 8,
    "feature_icon_size": 20,
    "feature_gap": 14,

    # Right Panel
    "right_pad": 44,
    "badge_h": 28,
    "input_h": 50,
    "input_radius": 12,
    "input_border_w": 1.5,
    "eye_btn_size": 50,
    "eye_gap": 8,
    "btn_h": 54,
    "btn_radius": 12,
    "quick_btn_h": 46,
    "quick_btn_w": 196,
    "quick_btn_radius": 12,
    "dot_size": 10,
}

_FAMILY_HEAD = "Space Grotesk" if _FONTS_LOADED else "Segoe UI"
_FAMILY_BODY = "Inter" if _FONTS_LOADED else "Segoe UI"

FONTS = {
    "brand": (_FAMILY_HEAD, -28, "bold"),
    "headline": (_FAMILY_HEAD, -32, "bold"),
    "title": (_FAMILY_HEAD, -34, "bold"),
    "subtitle": (_FAMILY_BODY, -14),
    "paragraph": (_FAMILY_BODY, -14),
    "label": (_FAMILY_BODY, -14, "bold"),
    "body": (_FAMILY_BODY, -14),
    "feature_title": (_FAMILY_BODY, -15, "bold"),
    "feature_desc": (_FAMILY_BODY, -13),
    "badge": (_FAMILY_BODY, -12, "bold"),
    "btn": (_FAMILY_HEAD, -16, "bold"),
    "quick_btn": (_FAMILY_BODY, -13, "bold"),
}

# ──────────────────────────────────────────────────────────────────────────────
# UTILITIES & DRAWING HELPERS (3x Supersampling for clean antialiasing)
# ──────────────────────────────────────────────────────────────────────────────
def hex_to_rgba(h, alpha=255):
    h = h.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[0], rgb[1], rgb[2], int(alpha))


def rounded_rect_image(w, h, radius, fill, outline=None, outline_width=1.0, glow=None, scale=3):
    """Renders a supersampled antialiased rounded rectangle with optional glow."""
    glow_pad = int(glow.get("radius", 0) * 1.5) if glow else 0
    total_w = w + glow_pad * 2
    total_h = h + glow_pad * 2

    SW, SH = total_w * scale, total_h * scale
    RW, RH = w * scale, h * scale
    RR = radius * scale
    OX, OY = glow_pad * scale, glow_pad * scale

    im = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    if glow:
        g_im = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g_im)
        g_color = hex_to_rgba(glow["color"], int(255 * glow.get("opacity", 0.18)))
        gd.rounded_rectangle([OX, OY, OX + RW - 1, OY + RH - 1], radius=RR, fill=g_color)
        blurred = g_im.filter(ImageFilter.GaussianBlur(glow["radius"] * scale))
        im = Image.alpha_composite(im, blurred)
        d = ImageDraw.Draw(im)

    fill_rgba = hex_to_rgba(fill) if isinstance(fill, str) else fill
    out_rgba = hex_to_rgba(outline) if (outline and isinstance(outline, str)) else outline
    bw = int(outline_width * scale) if outline else 0

    d.rounded_rectangle([OX, OY, OX + RW - 1, OY + RH - 1], radius=RR, fill=fill_rgba, outline=out_rgba, width=bw)
    return im.resize((total_w, total_h), Image.LANCZOS)


def make_card_surface_image(w=SIZES["card_w"], h=SIZES["card_h"], radius=SIZES["card_radius"],
                            left_w=SIZES["left_w"], glow_margin=30, scale=3):
    """Draws the unified card background (left #0A2236, right #FFFFFF, rounded corners, teal glow)."""
    gw = w + glow_margin * 2
    gh = h + glow_margin * 2
    GW, GH = gw * scale, gh * scale
    W, H, R = w * scale, h * scale, radius * scale
    OX, OY = glow_margin * scale, glow_margin * scale

    # 1. Soft teal glow (18% opacity, blurred)
    glow_im = Image.new("RGBA", (GW, GH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_im)
    gd.rounded_rectangle([OX, OY, OX + W - 1, OY + H - 1], radius=R, fill=hex_to_rgba(COLORS["teal"], int(255 * 0.18)))
    glow_blurred = glow_im.filter(ImageFilter.GaussianBlur(16 * scale))

    # 2. Card body
    card_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card_im)
    cd.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=COLORS["right_bg"])

    # Left panel mask
    left_mask = Image.new("L", (W, H), 0)
    lmd = ImageDraw.Draw(left_mask)
    lmd.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=255)
    lmd.rectangle([left_w * scale, 0, W, H], fill=0)

    left_panel = Image.new("RGBA", (W, H), COLORS["left_bg"])
    card_im.paste(left_panel, (0, 0), left_mask)

    glow_blurred.paste(card_im, (OX, OY), card_im)
    return glow_blurred.resize((gw, gh), Image.LANCZOS)


def make_logo_cross_image(size=SIZES["logo_size"], scale=3):
    """Logo: a 4-square cross drawn as outlines (top & left sky #38BDF8, right & bottom lime #B6F03C)."""
    S = size * scale
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    sw = int(2.0 * scale)
    r = int(2.5 * scale)
    sky = hex_to_rgba(COLORS["sky"])
    lime = hex_to_rgba(COLORS["lime"])

    # Top square
    d.rounded_rectangle([10 * scale, 2 * scale, 22 * scale, 14 * scale], radius=r, outline=sky, width=sw)
    # Left square
    d.rounded_rectangle([2 * scale, 10 * scale, 14 * scale, 22 * scale], radius=r, outline=sky, width=sw)
    # Right square
    d.rounded_rectangle([18 * scale, 10 * scale, 30 * scale, 22 * scale], radius=r, outline=lime, width=sw)
    # Bottom square
    d.rounded_rectangle([10 * scale, 18 * scale, 22 * scale, 30 * scale], radius=r, outline=lime, width=sw)

    return im.resize((size, size), Image.LANCZOS)


def make_feature_tile_image(tile_bg, icon_type, icon_color, size=SIZES["feature_tile_size"],
                            radius=SIZES["feature_tile_radius"], scale=3):
    """Creates a 40x40 rounded-square icon tile with 20px line icon (2px stroke)."""
    S = size * scale
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius * scale, fill=tile_bg)

    ox, oy = 10 * scale, 10 * scale
    sw = int(2.0 * scale)
    col = hex_to_rgba(icon_color)

    if icon_type == "trend":
        # ML Forecasting: trend line
        pts = [(ox + 2 * scale, oy + 14 * scale),
               (ox + 7 * scale, oy + 9 * scale),
               (ox + 12 * scale, oy + 12 * scale),
               (ox + 18 * scale, oy + 4 * scale)]
        d.line(pts, fill=col, width=sw)
        # Arrow tip
        d.line([(ox + 13 * scale, oy + 4 * scale), (ox + 18 * scale, oy + 4 * scale), (ox + 18 * scale, oy + 9 * scale)], fill=col, width=sw)

    elif icon_type == "grid":
        # Live Dashboard: 4-panel grid
        for rx, ry in [(3, 3), (11, 3), (3, 11), (11, 11)]:
            d.rounded_rectangle([ox + rx * scale, oy + ry * scale, ox + (rx + 6) * scale, oy + (ry + 6) * scale],
                                radius=1 * scale, outline=col, width=sw)

    elif icon_type == "shield":
        # Role-Based Auth: shield
        pts = [(ox + 4 * scale, oy + 3 * scale),
               (ox + 16 * scale, oy + 3 * scale),
               (ox + 16 * scale, oy + 10 * scale),
               (ox + 10 * scale, oy + 17 * scale),
               (ox + 4 * scale, oy + 10 * scale),
               (ox + 4 * scale, oy + 3 * scale)]
        d.line(pts, fill=col, width=sw)

    elif icon_type == "box":
        # Smart Inventory: cube/box
        top_pts = [(ox + 10 * scale, oy + 3 * scale),
                   (ox + 17 * scale, oy + 7 * scale),
                   (ox + 10 * scale, oy + 11 * scale),
                   (ox + 3 * scale, oy + 7 * scale),
                   (ox + 10 * scale, oy + 3 * scale)]
        d.line(top_pts, fill=col, width=sw)
        d.line([(ox + 3 * scale, oy + 7 * scale), (ox + 3 * scale, oy + 14 * scale), (ox + 10 * scale, oy + 18 * scale)], fill=col, width=sw)
        d.line([(ox + 17 * scale, oy + 7 * scale), (ox + 17 * scale, oy + 14 * scale), (ox + 10 * scale, oy + 18 * scale)], fill=col, width=sw)
        d.line([(ox + 10 * scale, oy + 11 * scale), (ox + 10 * scale, oy + 18 * scale)], fill=col, width=sw)

    return im.resize((size, size), Image.LANCZOS)


def make_eye_button_image(closed=False, size=SIZES["eye_btn_size"], radius=SIZES["input_radius"], scale=3):
    """50x50 rounded square eye button with clean drawn line icon."""
    S = size * scale
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius * scale,
                        fill=COLORS["input_bg"], outline=hex_to_rgba(COLORS["input_border"]),
                        width=int(SIZES["input_border_w"] * scale))

    ox, oy = 15 * scale, 15 * scale
    sw = int(1.8 * scale)
    fg = hex_to_rgba(COLORS["text_sub"])

    d.arc([ox, oy + 2 * scale, ox + 20 * scale, oy + 18 * scale], 195, 345, fill=fg, width=sw)
    d.arc([ox, oy + 2 * scale, ox + 20 * scale, oy + 18 * scale], 15, 165, fill=fg, width=sw)
    d.ellipse([ox + 7 * scale, oy + 7 * scale, ox + 13 * scale, oy + 13 * scale],
              fill=fg if not closed else None, outline=fg, width=sw)

    if closed:
        d.line([(ox + 2 * scale, oy + 18 * scale), (ox + 18 * scale, oy + 2 * scale)], fill=fg, width=sw)

    return im.resize((size, size), Image.LANCZOS)


def make_lock_icon_image(size=14, scale=3):
    """Draws a 14px crisp lock icon for the badge pill."""
    S = size * scale
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = hex_to_rgba(COLORS["badge_text"])
    sw = int(1.6 * scale)

    # Shackle
    d.arc([3 * scale, 1 * scale, 11 * scale, 9 * scale], 180, 0, fill=col, width=sw)
    # Body
    d.rounded_rectangle([2 * scale, 5 * scale, 12 * scale, 13 * scale], radius=1.5 * scale, fill=col)
    return im.resize((size, size), Image.LANCZOS)


def make_quick_btn_image(w, h, label, dot_color, hovered=False, scale=3):
    """Draws a quick access button with smooth border, 10px dot, and label."""
    W, H, R = w * scale, h * scale, SIZES["quick_btn_radius"] * scale
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    border_col = COLORS["teal_accent"] if hovered else COLORS["divider_right"]
    bw = int((1.8 if hovered else 1.0) * scale)

    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=R, fill=COLORS["right_bg"], outline=hex_to_rgba(border_col), width=bw)

    # 10px colored dot at x=16
    dx = 16 * scale
    dy = (H // 2)
    dr = 5 * scale
    d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=hex_to_rgba(dot_color))

    # Text
    try:
        f = ImageFont.truetype(str(_FONT_DIR / "Inter.ttf"), int(13 * scale))
    except Exception:
        f = ImageFont.load_default()

    d.text((32 * scale, dy), label, fill=hex_to_rgba(COLORS["text_label"]), font=f, anchor="lm")
    return im.resize((w, h), Image.LANCZOS)


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM REUSABLE WIDGETS
# ──────────────────────────────────────────────────────────────────────────────
class RoundedEntry(tk.Frame):
    """Entry with supersampled rounded border that glows on focus."""
    def __init__(self, parent, width, height=SIZES["input_h"], radius=SIZES["input_radius"],
                 bg_color=COLORS["input_bg"], border_color=COLORS["input_border"],
                 focus_border=COLORS["input_border_focus"], font=FONTS["body"], show=None):
        super().__init__(parent, bg=COLORS["right_bg"], width=width, height=height)
        self.pack_propagate(False)

        self.custom_width = width
        self.custom_height = height

        # Normal and Focused background images
        self._im_normal = ImageTk.PhotoImage(
            rounded_rect_image(width, height, radius, bg_color, border_color, SIZES["input_border_w"])
        )
        self._im_focus = ImageTk.PhotoImage(
            rounded_rect_image(width, height, radius, bg_color, focus_border, 2.0,
                               glow={"color": COLORS["teal_accent"], "opacity": 0.25, "radius": 4})
        )

        self._bg_lbl = tk.Label(self, image=self._im_normal, bg=COLORS["right_bg"], bd=0)
        self._bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        kw = dict(bg=bg_color, relief="flat", bd=0, highlightthickness=0, font=font, fg=COLORS["text_dark"])
        if show:
            kw["show"] = show
        self.entry = tk.Entry(self, **kw)
        self.entry.place(x=14, rely=0.5, relwidth=0.90, anchor="w")

        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_blur)

    def _on_focus(self, e):
        self._bg_lbl.config(image=self._im_focus)

    def _on_blur(self, e):
        self._bg_lbl.config(image=self._im_normal)

    def get(self):
        return self.entry.get()

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def insert(self, index, string):
        self.entry.insert(index, string)

    def focus_set(self):
        self.entry.focus_set()

    def bind(self, sequence=None, func=None, add=None):
        self.entry.bind(sequence, func, add)

    def config(self, **kwargs):
        self.entry.config(**kwargs)


class RoundedButton(tk.Label):
    """Pill-smooth button with soft glow, hover and pressed feedback."""
    def __init__(self, parent, width, height, radius, text, bg_color, text_color,
                 hover_bg, pressed_bg, font=FONTS["btn"], command=None, glow_color=None):
        super().__init__(parent, bg=COLORS["right_bg"], bd=0, cursor="hand2")
        self.command = command

        # Render 3 states
        def _render_btn(fill, glow=True):
            glow_spec = {"color": glow_color, "opacity": 0.35, "radius": 6} if (glow and glow_color) else None
            im = rounded_rect_image(width, height, radius, fill, glow=glow_spec)
            # Draw text directly on button for perfect crisp typography
            d = ImageDraw.Draw(im)
            cx = im.width // 2
            cy = im.height // 2
            try:
                f_name = "SpaceGrotesk-Bold.ttf" if _FONTS_LOADED else "Inter.ttf"
                f = ImageFont.truetype(str(_FONT_DIR / f_name), int(16 * 3))
            except Exception:
                f = ImageFont.load_default()
            d.text((cx, cy), text, fill=hex_to_rgba(text_color), font=f, anchor="mm")
            return ImageTk.PhotoImage(im)

        self._img_norm = _render_btn(bg_color, glow=True)
        self._img_hover = _render_btn(hover_bg, glow=True)
        self._img_press = _render_btn(pressed_bg, glow=False)

        self.config(image=self._img_norm)
        self.bind("<Enter>", lambda e: self.config(image=self._img_hover))
        self.bind("<Leave>", lambda e: self.config(image=self._img_norm))
        self.bind("<Button-1>", lambda e: self.config(image=self._img_press))
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_release(self, e):
        self.config(image=self._img_hover)
        if self.command:
            self.command()


class IconButton(tk.Label):
    """50x50 rounded square icon button for password toggle."""
    def __init__(self, parent, size=SIZES["eye_btn_size"], command=None):
        super().__init__(parent, bg=COLORS["right_bg"], bd=0, cursor="hand2")
        self.command = command
        self._closed = True

        self._img_closed = ImageTk.PhotoImage(make_eye_button_image(closed=True, size=size))
        self._img_open = ImageTk.PhotoImage(make_eye_button_image(closed=False, size=size))

        self.config(image=self._img_closed)
        self.bind("<Button-1>", self._on_click)

    def _on_click(self, e):
        self._closed = not self._closed
        self.config(image=self._img_closed if self._closed else self._img_open)
        if self.command:
            self.command(not self._closed)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN LOGIN SCREEN
# ──────────────────────────────────────────────────────────────────────────────
class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=COLORS["window_bg"])
        self.parent = parent
        self.on_login_success = on_login_success
        self._photo_refs = []  # GC Guard for all dynamic PhotoImages

        # Ensure window is 1280x800, centered, min 1000x700
        self._configure_window()
        self.setup_ui()

    def _configure_window(self):
        """Enforces 1280x800, centered on screen, minsize 1000x700."""
        try:
            top = self.winfo_toplevel()
            top.attributes("-fullscreen", False)
            top.minsize(SIZES["win_min_w"], SIZES["win_min_h"])
            sw = top.winfo_screenwidth()
            sh = top.winfo_screenheight()
            x = max(0, (sw - SIZES["win_w"]) // 2)
            y = max(0, (sh - SIZES["win_h"]) // 2)
            top.geometry(f"{SIZES['win_w']}x{SIZES['win_h']}+{x}+{y}")
        except Exception:
            pass

    def setup_ui(self):
        # Full-window Canvas behind everything
        self.bg_canvas = tk.Canvas(self, bg=COLORS["window_bg"], highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self._on_resize)

        # Card Container placed at center of canvas
        self._build_card()

    # ──────────────────────────────────────────────────────────────────────────
    # BACKGROUND RENDERER (Pillow ImageDraw + GaussianBlur concentric rings + 3 dots)
    # ──────────────────────────────────────────────────────────────────────────
    def _draw_background_rings(self, w, h):
        """Renders 4 thin concentric circles + 3 colored dots with Pillow."""
        scale = 2
        W, H = w * scale, h * scale
        im = Image.new("RGBA", (W, H), COLORS["window_bg"])
        d = ImageDraw.Draw(im)

        cx, cy = W // 2, H // 2

        # 4 thin concentric circles centered on window (radii ~ 320, 460, 600, 690 px)
        rings = [
            (320 * scale, COLORS["ring_1"]),
            (460 * scale, COLORS["ring_2"]),
            (600 * scale, COLORS["ring_3"]),
            (690 * scale, COLORS["ring_4"])
        ]
        for r, col in rings:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=hex_to_rgba(col), width=int(1.0 * scale))

        # 3 tiny dots: lime #B6F03C, teal #2DD4BF, sky #38BDF8
        dots = [
            (320 * scale, math.radians(48), COLORS["lime"], 3.5 * scale),
            (460 * scale, math.radians(205), COLORS["teal"], 3.5 * scale),
            (600 * scale, math.radians(312), COLORS["sky"], 3.5 * scale)
        ]
        for r, angle, col, dr in dots:
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            d.ellipse([px - dr, py - dr, px + dr, py + dr], fill=hex_to_rgba(col))

        out = im.resize((w, h), Image.LANCZOS)
        return ImageTk.PhotoImage(out)

    def _on_resize(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100 or h < 100:
            return

        # Redraw background canvas image
        self._bg_img = self._draw_background_rings(w, h)
        self._photo_refs.append(self._bg_img)
        self.bg_canvas.delete("bg_tag")
        self.bg_canvas.create_image(0, 0, image=self._bg_img, anchor="nw", tags="bg_tag")

        # Reposition card image and window items at center
        cx, cy = w // 2, h // 2
        self.bg_canvas.coords(self._card_bg_win, cx, cy)
        self.bg_canvas.coords(self._left_win, cx - SIZES["card_w"] // 2 + SIZES["left_w"] // 2, cy)
        self.bg_canvas.coords(self._right_win, cx - SIZES["card_w"] // 2 + SIZES["left_w"] + SIZES["right_w"] // 2, cy)

        # Raise widgets on top of background
        self.bg_canvas.tag_raise(self._card_bg_win)
        self.bg_canvas.tag_raise(self._left_win)
        self.bg_canvas.tag_raise(self._right_win)

    # ──────────────────────────────────────────────────────────────────────────
    # CARD ASSEMBLY
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card(self):
        # 1. Supersampled Card Background PhotoImage with rounded corners & teal glow
        self._card_surface_img = ImageTk.PhotoImage(make_card_surface_image())
        self._photo_refs.append(self._card_surface_img)

        self._card_bg_win = self.bg_canvas.create_image(0, 0, image=self._card_surface_img, anchor="center")

        # 2. Left Panel Container (52% width)
        self.left_panel = tk.Frame(self.bg_canvas, bg=COLORS["left_bg"], width=SIZES["left_w"] - 20, height=SIZES["card_h"] - 30)
        self.left_panel.pack_propagate(False)
        self._left_win = self.bg_canvas.create_window(0, 0, window=self.left_panel, anchor="center")

        # 3. Right Panel Container (48% width)
        self.right_panel = tk.Frame(self.bg_canvas, bg=COLORS["right_bg"], width=SIZES["right_w"] - 20, height=SIZES["card_h"] - 30)
        self.right_panel.pack_propagate(False)
        self._right_win = self.bg_canvas.create_window(0, 0, window=self.right_panel, anchor="center")

        self._populate_left_panel()
        self._populate_right_panel()

    # ──────────────────────────────────────────────────────────────────────────
    # LEFT PANEL (Top logo, inline headline, paragraph, pinned 4 feature items)
    # ──────────────────────────────────────────────────────────────────────────
    def _populate_left_panel(self):
        inner = tk.Frame(self.left_panel, bg=COLORS["left_bg"], padx=24, pady=20)
        inner.pack(fill="both", expand=True)

        # ── 1. Top Logo + Brand ───────────────────────────────────────────────
        brand_row = tk.Frame(inner, bg=COLORS["left_bg"])
        brand_row.pack(anchor="w", pady=(0, 16))

        self._logo_img = ImageTk.PhotoImage(make_logo_cross_image(SIZES["logo_size"]))
        self._photo_refs.append(self._logo_img)

        logo_lbl = tk.Label(brand_row, image=self._logo_img, bg=COLORS["left_bg"], bd=0)
        logo_lbl.pack(side="left", padx=(0, 12))

        tk.Label(
            brand_row,
            text="PharmaCare",
            font=FONTS["brand"],
            bg=COLORS["left_bg"],
            fg=COLORS["text_white"]
        ).pack(side="left")

        # ── 2. Headline with inline lime "need" ────────────────────────────────
        head_box = tk.Text(
            inner,
            bg=COLORS["left_bg"],
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=2,
            cursor="arrow"
        )
        head_box.tag_configure("white", foreground=COLORS["text_white"], font=FONTS["headline"], spacing2=0)
        head_box.tag_configure("lime", foreground=COLORS["lime"], font=FONTS["headline"], spacing2=0)
        head_box.insert("end", "Know what you'll ", "white")
        head_box.insert("end", "need", "lime")
        head_box.insert("end", " before the shelf runs out.", "white")
        head_box.configure(state="disabled")
        head_box.pack(anchor="w", fill="x", pady=(0, 10))

        # ── 3. Paragraph ──────────────────────────────────────────────────────
        tk.Label(
            inner,
            text="Pharmacy store management and knowledge analytics, with ML-powered forecasting and real-time inventory health.",
            font=FONTS["paragraph"],
            bg=COLORS["left_bg"],
            fg=COLORS["text_muted"],
            wraplength=440,
            justify="left"
        ).pack(anchor="w", pady=(0, 18))

        # ── 4. Feature List Pinned to Bottom ──────────────────────────────────
        feat_box = tk.Frame(inner, bg=COLORS["left_bg"])
        feat_box.pack(side="bottom", fill="x")

        features = [
            ("trend", COLORS["teal"], COLORS["tile_ml_bg"], "ML Forecasting", "Predictive demand analysis"),
            ("grid", COLORS["sky"], COLORS["tile_dash_bg"], "Live Dashboard", "Real-time inventory health"),
            ("shield", COLORS["amber"], COLORS["tile_auth_bg"], "Role-Based Auth", "The right access for every role"),
            ("box", COLORS["lime"], COLORS["tile_inv_bg"], "Smart Inventory", "Reorder before the shelf runs out")
        ]

        for i, (itype, icol, tbg, title, desc) in enumerate(features):
            row = tk.Frame(feat_box, bg=COLORS["left_bg"])
            row.pack(fill="x", pady=5)

            # 40x40 rounded-square icon tile
            tile_img = ImageTk.PhotoImage(make_feature_tile_image(tbg, itype, icol))
            self._photo_refs.append(tile_img)

            tile_lbl = tk.Label(row, image=tile_img, bg=COLORS["left_bg"], bd=0)
            tile_lbl.pack(side="left", padx=(0, SIZES["feature_gap"]))

            # Stacked title + description, LEFT-ALIGNED (anchor="w")
            txt_stack = tk.Frame(row, bg=COLORS["left_bg"])
            txt_stack.pack(side="left", fill="y", anchor="w")

            tk.Label(
                txt_stack,
                text=title,
                font=FONTS["feature_title"],
                bg=COLORS["left_bg"],
                fg=COLORS["text_white"],
                anchor="w"
            ).pack(anchor="w")

            tk.Label(
                txt_stack,
                text=desc,
                font=FONTS["feature_desc"],
                bg=COLORS["left_bg"],
                fg=COLORS["text_muted"],
                anchor="w"
            ).pack(anchor="w")

            # 1px line separator (rgba white 10% = #1B3347)
            if i < len(features) - 1:
                tk.Frame(feat_box, bg=COLORS["divider_left"], height=1).pack(fill="x", pady=(3, 3))

    # ──────────────────────────────────────────────────────────────────────────
    # RIGHT PANEL (Badge, Form, Lime CTA, Quick Access)
    # ──────────────────────────────────────────────────────────────────────────
    def _populate_right_panel(self):
        inner = tk.Frame(self.right_panel, bg=COLORS["right_bg"], padx=34, pady=20)
        inner.pack(fill="both", expand=True)

        content_w = SIZES["right_w"] - 20 - 68  # available width ~412px

        # ── 1. Badge Pill (Lock + "Secure portal", bg #E3F7F3, text #0B6B5E) ───
        badge_box = tk.Frame(inner, bg=COLORS["badge_bg"], padx=10, pady=4)
        badge_box.pack(anchor="w", pady=(0, 10))

        self._lock_img = ImageTk.PhotoImage(make_lock_icon_image(13))
        self._photo_refs.append(self._lock_img)

        tk.Label(badge_box, image=self._lock_img, bg=COLORS["badge_bg"], bd=0).pack(side="left", padx=(0, 6))
        tk.Label(
            badge_box,
            text="Secure portal",
            font=FONTS["badge"],
            bg=COLORS["badge_bg"],
            fg=COLORS["badge_text"]
        ).pack(side="left")

        # ── 2. Title & Subtitle ───────────────────────────────────────────────
        tk.Label(
            inner,
            text="Welcome back",
            font=FONTS["title"],
            bg=COLORS["right_bg"],
            fg=COLORS["text_dark"]
        ).pack(anchor="w")

        tk.Label(
            inner,
            text="Sign in to access your designated workspace.",
            font=FONTS["subtitle"],
            bg=COLORS["right_bg"],
            fg=COLORS["text_sub"]
        ).pack(anchor="w", pady=(2, 16))

        # ── 3. Username Field ─────────────────────────────────────────────────
        tk.Label(
            inner,
            text="Username",
            font=FONTS["label"],
            bg=COLORS["right_bg"],
            fg=COLORS["text_label"]
        ).pack(anchor="w", pady=(0, 5))

        self.ent_user = RoundedEntry(inner, width=content_w)
        self.ent_user.pack(anchor="w", pady=(0, 12))
        self.ent_user.focus_set()

        # ── 4. Password Field with 50x50 Eye Button ───────────────────────────
        tk.Label(
            inner,
            text="Password",
            font=FONTS["label"],
            bg=COLORS["right_bg"],
            fg=COLORS["text_label"]
        ).pack(anchor="w", pady=(0, 5))

        pwd_row = tk.Frame(inner, bg=COLORS["right_bg"])
        pwd_row.pack(anchor="w", fill="x", pady=(0, 6))

        pwd_w = content_w - SIZES["eye_btn_size"] - SIZES["eye_gap"]
        self.ent_pwd = RoundedEntry(pwd_row, width=pwd_w, show="•")
        self.ent_pwd.pack(side="left")

        self.btn_eye = IconButton(pwd_row, size=SIZES["eye_btn_size"], command=self._toggle_password)
        self.btn_eye.pack(side="right")

        # Feedback / status message
        self.lbl_msg = tk.Label(
            inner,
            text="",
            font=FONTS["subtitle"],
            bg=COLORS["right_bg"],
            fg=COLORS["error"],
            wraplength=content_w,
            justify="left"
        )
        self.lbl_msg.pack(anchor="w", pady=(0, 6))

        # ── 5. Primary Lime Button "Sign in to system  →" ──────────────────────
        self.btn_login = RoundedButton(
            inner,
            width=content_w,
            height=SIZES["btn_h"],
            radius=SIZES["btn_radius"],
            text="Sign in to system   \u2192",
            bg_color=COLORS["lime"],
            text_color=COLORS["btn_text"],
            hover_bg=COLORS["lime_hover"],
            pressed_bg=COLORS["lime_pressed"],
            font=FONTS["btn"],
            glow_color=COLORS["lime"],
            command=self.handle_login
        )
        self.btn_login.pack(anchor="w", pady=(0, 14))

        # ── 6. Divider Row: line, "Quick access", line ─────────────────────────
        div_row = tk.Frame(inner, bg=COLORS["right_bg"])
        div_row.pack(fill="x", pady=(0, 10))

        tk.Frame(div_row, bg=COLORS["divider_right"], height=1).pack(side="left", fill="x", expand=True, pady=6)
        tk.Label(
            div_row,
            text="   Quick access   ",
            font=FONTS["feature_desc"],
            bg=COLORS["right_bg"],
            fg=COLORS["text_sub"]
        ).pack(side="left")
        tk.Frame(div_row, bg=COLORS["divider_right"], height=1).pack(side="left", fill="x", expand=True, pady=6)

        # ── 7. Quick Access 2x2 Grid ──────────────────────────────────────────
        grid_frame = tk.Frame(inner, bg=COLORS["right_bg"])
        grid_frame.pack(fill="x")

        roles = [
            ("Administrator",   "admin",           "admin123",      COLORS["teal_accent"]),
            ("Instructor (ML)", "instructor",      "instructor123", "#2F7DE1"),
            ("Inventory Clerk", "inventory_clerk", "clerk123",      "#7C5CE0"),
            ("Sales Personnel", "sales_personnel", "sales123",      "#E08A1E"),
        ]

        q_btn_w = (content_w - 10) // 2
        for i, (lbl, u, p, dot_col) in enumerate(roles):
            r, c = divmod(i, 2)
            self._create_quick_access_pill(grid_frame, r, c, q_btn_w, SIZES["quick_btn_h"], lbl, u, p, dot_col)

        # Keybindings
        self.ent_user.bind("<Return>", lambda e: self.ent_pwd.focus_set())
        self.ent_pwd.bind("<Return>", lambda e: self.handle_login())

    def _create_quick_access_pill(self, parent, r, c, w, h, label, username, password, dot_color):
        """Creates a rounded quick access button with hover border and dot indicator."""
        img_norm = ImageTk.PhotoImage(make_quick_btn_image(w, h, label, dot_color, hovered=False))
        img_hover = ImageTk.PhotoImage(make_quick_btn_image(w, h, label, dot_color, hovered=True))
        self._photo_refs.extend([img_norm, img_hover])

        btn = tk.Label(parent, image=img_norm, bg=COLORS["right_bg"], bd=0, cursor="hand2")
        btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
        parent.grid_columnconfigure(c, weight=1)

        btn.bind("<Enter>", lambda e: btn.config(image=img_hover))
        btn.bind("<Leave>", lambda e: btn.config(image=img_norm))
        btn.bind("<Button-1>", lambda e: self.fill_quick(username, password, label))

    # ──────────────────────────────────────────────────────────────────────────
    # AUTHENTICATION & FUNCTIONALITY (Unchanged logic)
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_password(self, show_plain):
        if show_plain:
            self.ent_pwd.config(show="")
        else:
            self.ent_pwd.config(show="•")

    def fill_quick(self, username, password, role_label=""):
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, username)
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, password)
        self.lbl_msg.config(text=f"Loaded {role_label} credentials", fg=COLORS["info"])
        self.ent_pwd.focus_set()

    def handle_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pwd.get()

        if not username or not password:
            self.lbl_msg.config(text="Please enter both username and password.", fg=COLORS["error"])
            return

        self.lbl_msg.config(text="Authenticating credentials…", fg=COLORS["info"])
        self.update_idletasks()

        success, msg, user_data = auth.authenticate_user(username, password)
        if success:
            self.lbl_msg.config(text="Login successful! Redirecting…", fg=COLORS["success"])
            self.on_login_success(user_data)
        else:
            self.lbl_msg.config(text=msg, fg=COLORS["error"])
            self.ent_pwd.delete(0, tk.END)
            self.ent_pwd.focus_set()
