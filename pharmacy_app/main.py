import os
import sys
import tempfile
from pathlib import Path

# Set MPL cache directory to temp to prevent permission errors
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont

import config
import db
import auth
from theme import ThemeAnimator, collect_transition_targets, attach_motion_bg
from screens.login import LoginScreen
from screens.dashboard import DashboardScreen

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_SIDEBAR_BG = "#0D1524"
_USER_CHIP_BG = "#111A2B"
_USER_CHIP_BORDER = "#1E2B42"
_LIME = "#A3E635"
_NAV_INACTIVE_FG = "#9FB0C8"
_NAV_HOVER_BG = "#15213A"

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        
        # Launch fully in full-screen mode automatically
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            self.state("zoomed")

        # Allow F11 to toggle fullscreen and Escape to exit fullscreen seamlessly
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.protocol("WM_DELETE_WINDOW", self.on_close_attempt)

        self._available_families = set()
        try:
            self._available_families = set(tkfont.families())
        except Exception:
            pass
        self._font_spec_cache = {}
        self._typo_idle_scheduled = False

        # Style TTK widgets
        self.setup_ttk_styles()

        # Master layout container
        self.main_container = tk.Frame(self, bg=config.COLORS["background"])
        self.main_container.pack(fill="both", expand=True)
        self.bind("<Map>", self._on_any_widget_map, add="+")

        #Active components
        self.sidebar = None
        self.content_area = None
        self.current_screen = None
        self._login_view = None
        self.btn_theme = None
        self.btn_settings = None
        self.btn_logout = None
        self._sidebar_settings_popover = None
        self._sidebar_active_dropdown = None
        self._is_sidebar_settings_open = False
        self._theme_animator = ThemeAnimator(self)

        # Check / Initialize DB on start
        try:
            db.init_database()
        except Exception as e:
            messagebox.showwarning(
                "Database Connection Warning",
                f"Could not connect to MySQL server on {config.DB_HOST}:{config.DB_PORT}.\n\n"
                f"Error: {e}\n\n"
                "Please make sure WAMP / MySQL is running, or verify config.py settings."
            )

        # Start with Login Screen
        self.show_login_screen()

    def setup_ttk_styles(self):
        c = config.COLORS
        style = ttk.Style(self)
        style.theme_use("clam")

        # Default widget colors for classic tk widgets that omit explicit fg/bg
        self.option_add("*Label.foreground", c["text_dark"])
        self.option_add("*Radiobutton.foreground", c["text_dark"])
        self.option_add("*Radiobutton.selectColor", c["surface_alt"])
        self.option_add("*Checkbutton.foreground", c["text_dark"])
        self.option_add("*Checkbutton.selectColor", c["surface_alt"])
        self.option_add("*Text.foreground", c["text_dark"])
        self.option_add("*Text.background", c["surface"])
        self.option_add("*Text.insertBackground", c["text_dark"])
        self.option_add("*TCombobox*Listbox.background", c["surface"])
        self.option_add("*TCombobox*Listbox.foreground", c["text_dark"])
        self.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        # Treeview styling for data tables
        prefs = getattr(config, "UI_PREFS", {})
        sz_off = {"S": -1, "M": 0, "L": 2, "XL": 3}.get(prefs.get("text_size", "M"), 0)
        body_font = self._ui_font(10)
        body_bold_font = self._ui_font(10, "bold")

        style.configure(
            "Treeview",
            background=c["surface"],
            foreground=c["text_dark"],
            rowheight=max(24, 28 + sz_off * 2),
            fieldbackground=c["surface"],
            font=body_font,
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=c["surface_alt"],
            foreground=c["text_dark"],
            font=body_bold_font,
            relief="flat",
            padding=(6, 6)
        )
        style.map("Treeview.Heading", background=[("active", c["border"])])
        style.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", "white")])

        # Entry, Combobox, and Spinbox styling
        style.configure(
            "TEntry",
            fieldbackground=c["surface_alt"],
            foreground=c["text_dark"],
            insertcolor=c["text_dark"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            font=body_font,
        )
        style.configure(
            "TCombobox",
            fieldbackground=c["surface_alt"],
            background=c["surface_alt"],
            foreground=c["text_dark"],
            arrowcolor=c["text_muted"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            font=body_font,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["surface_alt"])],
            foreground=[("readonly", c["text_dark"])],
            selectbackground=[("readonly", c["surface_alt"])],
            selectforeground=[("readonly", c["text_dark"])],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=c["surface_alt"],
            background=c["surface_alt"],
            foreground=c["text_dark"],
            arrowcolor=c["text_muted"],
            bordercolor=c["border"],
            font=body_font,
        )

        # Notebook & Tab styling
        style.configure("TNotebook", background=c["background"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=c["surface_alt"],
            foreground=c["text_muted"],
            padding=(12, 6),
            font=body_bold_font,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", c["surface"]), ("active", c["border"])],
            foreground=[("selected", c["text_dark"])],
        )

        # Hide scrollbars globally while preserving smooth mousewheel scrolling
        style.layout("Vertical.TScrollbar", [])
        style.layout("Horizontal.TScrollbar", [])
        style.configure(
            "Vertical.TScrollbar",
            background=c["surface_alt"],
            troughcolor=c["background"],
            bordercolor=c["background"],
            arrowcolor=c["text_muted"],
            width=0,
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=c["surface_alt"],
            troughcolor=c["background"],
            bordercolor=c["background"],
            arrowcolor=c["text_muted"],
             width=0,
        )

    def _resolve_ui_font_family(self) -> str:
        prefs = getattr(config, "UI_PREFS", {})
        choice = prefs.get("font", "Inter")
        if choice == "Inter":
            if "Inter" in self._available_families:
                return "Inter"
            if "Segoe UI Variable Text" in self._available_families:
                return "Segoe UI Variable Text"
            return "Segoe UI"
        if choice in self._available_families:
            return choice
        return "Segoe UI"

    def _ui_font(self, base_pt: int, weight: str = "normal"):
        prefs = getattr(config, "UI_PREFS", {})
        sz = prefs.get("text_size", "M")
        offsets = {"S": -1, "M": 0, "L": 2, "XL": 3}
        pt = max(7, base_pt + offsets.get(sz, 0))
        fam = self._resolve_ui_font_family()
        return (fam, pt, "bold") if weight == "bold" else (fam, pt)

    def _ui_t(self, key: str) -> str:
        prefs = getattr(config, "UI_PREFS", {})
        lang = prefs.get("language", "English")
        translations = {
            "English": {
                "settings": "Settings",
                "appearance": "Appearance",
                "light_mode": "Light mode",
                "dark_mode": "Dark mode",
                "language": "Language",
                "font": "Font",
                "text_size": "Text size",
                "sign_out": "  Sign Out",
                "nav_dashboard": "   Dashboard",
                "nav_inventory": "   Inventory Management",
                "nav_sales": "   Point of Sale (POS)",
                "nav_users": "   User Management & Logs",
                "nav_analysis": "   Knowledge Analysis Studio",
                "nav_profile": "   My Profile",
            },
            "Filipino": {
                "settings": "Settings",
                "appearance": "Hitsura",
                "light_mode": "Light mode",
                "dark_mode": "Dark mode",
                "language": "Wika",
                "font": "Font",
                "text_size": "Laki ng teksto",
                "sign_out": "  Mag-sign Out",
                "nav_dashboard": "   Dashboard",
                "nav_inventory": "   Pamamahala ng Imbentaryo",
                "nav_sales": "   Point of Sale (POS)",
                "nav_users": "   Mga User at Logs",
                "nav_analysis": "   Knowledge Analysis Studio",
                "nav_profile": "   Aking Profile",
            },
            "Spanish": {
                "settings": "Ajustes",
                "appearance": "Apariencia",
                "light_mode": "Light mode",
                "dark_mode": "Dark mode",
                "language": "Idioma",
                "font": "Fuente",
                "text_size": "Tamaño de texto",
                "sign_out": "  Cerrar sesión",
                "nav_dashboard": "   Panel Principal",
                "nav_inventory": "   Gestión de Inventario",
                "nav_sales": "   Punto de Venta (POS)",
                "nav_users": "   Usuarios y Registros",
                "nav_analysis": "   Estudio de Analítica",
                "nav_profile": "   Mi Perfil",
            },
        }
        tmap = translations.get(lang, translations["English"])
        return tmap.get(key, translations["English"].get(key, key))

    def _make_nav_icon(self, kind: str, color: str, size: int = 16):
        """Draws crisp 3x supersampled vector icons for sidebar navigation and action buttons."""
        if not hasattr(self, "_nav_icon_cache"):
            self._nav_icon_cache = {}
        cache_key = (kind, color, size)
        if cache_key in self._nav_icon_cache:
            return self._nav_icon_cache[cache_key]

        scale = 3
        s = size * scale
        lw = max(3, int(1.9 * scale))
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        if kind == "dashboard":
            g = int(s * 0.14)
            m = int(s * 0.46)
            e = s - g
            r = int(scale * 2)
            d.rounded_rectangle([g, g, m, m], radius=r, outline=color, width=lw)
            d.rounded_rectangle([s - m, g, e, m], radius=r, outline=color, width=lw)
            d.rounded_rectangle([g, s - m, m, e], radius=r, outline=color, width=lw)
            d.rounded_rectangle([s - m, s - m, e, e], radius=r, outline=color, width=lw)
        elif kind == "inventory":
            cx, cy = s // 2, s // 2
            w = int(s * 0.34)
            h = int(s * 0.20)
            top = [(cx, cy - h * 2), (cx + w, cy - h), (cx, cy), (cx - w, cy - h)]
            d.polygon(top, outline=color)
            d.line([(cx - w, cy - h), (cx - w, cy + h), (cx, cy + h * 2), (cx + w, cy + h), (cx + w, cy - h)], fill=color, width=lw)
            d.line([(cx, cy), (cx, cy + h * 2)], fill=color, width=lw)
        elif kind == "sales":
            x1, y1, x2, y2 = int(s * 0.12), int(s * 0.22), int(s * 0.88), int(s * 0.78)
            d.rounded_rectangle([x1, y1, x2, y2], radius=int(scale * 2.5), outline=color, width=lw)
            d.line([(x1, int(s * 0.42)), (x2, int(s * 0.42))], fill=color, width=lw)
        elif kind == "users":
            r = int(s * 0.16)
            cx, cy = int(s * 0.42), int(s * 0.34)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
            d.arc([int(s * 0.14), int(s * 0.54), int(s * 0.70), int(s * 0.94)], start=180, end=360, fill=color, width=lw)
            d.arc([int(s * 0.56), int(s * 0.20), int(s * 0.84), int(s * 0.48)], start=270, end=90, fill=color, width=lw)
        elif kind == "analysis":
            pts = [(int(s * 0.10), int(s * 0.56)), (int(s * 0.30), int(s * 0.56)), (int(s * 0.44), int(s * 0.20)), (int(s * 0.60), int(s * 0.82)), (int(s * 0.74), int(s * 0.48)), (int(s * 0.90), int(s * 0.48))]
            d.line(pts, fill=color, width=lw)
        elif kind == "profile":
            r = int(s * 0.18)
            cx, cy = s // 2, int(s * 0.34)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
            d.arc([int(s * 0.18), int(s * 0.56), int(s * 0.82), int(s * 0.96)], start=180, end=360, fill=color, width=lw)
        elif kind == "settings":
            import math
            cx, cy = s // 2, s // 2
            r_in = int(s * 0.16)
            r_out = int(s * 0.34)
            d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=color, width=lw)
            for i in range(8):
                ang = i * (math.pi / 4)
                x1 = cx + int(math.cos(ang) * (r_out - scale * 1.5))
                y1 = cy + int(math.sin(ang) * (r_out - scale * 1.5))
                x2 = cx + int(math.cos(ang) * (r_out + scale * 2.2))
                y2 = cy + int(math.sin(ang) * (r_out + scale * 2.2))
                d.line([(x1, y1), (x2, y2)], fill=color, width=lw)
        elif kind == "logout":
            cx, cy = s // 2, int(s * 0.54)
            r = int(s * 0.32)
            d.arc([cx - r, cy - r, cx + r, cy + r], start=300, end=240, fill=color, width=lw)
            d.line([(cx, int(s * 0.14)), (cx, cy)], fill=color, width=lw)

        photo = ImageTk.PhotoImage(img.resize((size, size), Image.LANCZOS))
        self._nav_icon_cache[cache_key] = photo
        return photo

    def set_theme_mode(self, target_mode: str):
        """Smoothly transitions to the requested Light/Dark theme in place."""
        prev_mode = config.get_theme()
        if target_mode == prev_mode:
            return
        self._theme_animator.finish_immediately()
        new_mode = config.set_theme(target_mode)
        self.setup_ttk_styles()

        if self.sidebar is not None:
            targets = collect_transition_targets(self.main_container, prev_mode, new_mode, in_login=False)
            if self.current_screen is not None and hasattr(self.current_screen, "apply_theme"):
                self.current_screen.apply_theme()
            self._theme_animator.start(targets, duration_ms=180, steps=9)
            self._refresh_sidebar_settings_popover()
        elif self._login_view is not None:
            if hasattr(self._login_view, "apply_theme"):
                self._login_view.apply_theme()

    def toggle_theme(self):
        """Smoothly transitions Light/Dark theme in place without tearing down screens."""
        next_mode = "dark" if config.get_theme() == "light" else "light"
        self.set_theme_mode(next_mode)

    def minimize_window(self):
        self.iconify()

    def toggle_maximize_window(self):
        try:
            if self.state() == "zoomed":
                self.state("normal")
                self.geometry("1200x800")
            else:
                self.state("zoomed")
        except Exception:
            curr = self.attributes("-fullscreen")
            self.attributes("-fullscreen", not curr)

    def close_window(self):
        self.on_close_attempt()

    def on_close_attempt(self):
        if messagebox.askyesno("Exit Application", "Are you sure you want to exit the Pharmacy Management System?"):
            auth.logout_user()
            self.destroy()

    def clear_view(self):
        """Destroys current child widgets in main_container."""
        self._theme_animator.finish_immediately()
        self._hide_sidebar_settings_popover()
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.sidebar = None
        self.content_area = None
        self.current_screen = None
        self._login_view = None
        self.btn_theme = None
        self.btn_settings = None
        self.btn_logout = None

    def show_login_screen(self):
        self.clear_view()
        login_view = LoginScreen(
            self.main_container,
            on_login_success=self.on_login_success,
            on_toggle_theme=self.toggle_theme,
        )
        login_view.pack(fill="both", expand=True)
        self._login_view = login_view

    def on_login_success(self, user_data):
        self.build_app_shell()
        self.navigate_to("dashboard")

    def _make_circle_avatar(self, initials, size=36, bg_color=_LIME, text_color="#071d32", font_size=None):
        """Generates supersampled circular avatar image with user initials."""
        scale = 3
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([0, 0, s - 1, s - 1], fill=bg_color)

        font_path = _ASSETS_DIR / "fonts" / "SpaceGrotesk-Bold.ttf"
        if not font_path.exists():
            font_path = _ASSETS_DIR / "fonts" / "Inter.ttf"

        pt = font_size if font_size is not None else max(11, int(size * 0.35))
        try:
            font = ImageFont.truetype(str(font_path), int(pt * scale))
        except Exception:
            font = ImageFont.load_default()

        bbox = d.textbbox((0, 0), initials, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (s - tw) / 2 - bbox[0]
        ty = (s - th) / 2 - bbox[1]
        d.text((tx, ty), initials, fill=text_color, font=font)

        final_img = img.resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(final_img)
        if not hasattr(self, "_avatar_photos"):
            self._avatar_photos = []
        self._avatar_photos.append(photo)
        return photo

    def build_app_shell(self):
        self.clear_view()

        # Shell frame containing sidebar and content area
        shell = tk.Frame(self.main_container, bg=config.COLORS["background"])
        shell.pack(fill="both", expand=True)

        # ── Sidebar (Left) Matching Reference ─────────────────────────────────
        self.sidebar = tk.Frame(shell, bg=_SIDEBAR_BG, width=260, padx=16, pady=20)
        self.sidebar._theme_skip = True
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── Brand Header ──────────────────────────────────────────────────────
        brand_frame = tk.Frame(self.sidebar, bg=_SIDEBAR_BG)
        brand_frame.pack(fill="x", pady=(0, 22))

        logo_path = _ASSETS_DIR / "logo.png"
        self._sidebar_logo_photo = None
        if logo_path.exists():
            try:
                _img = Image.open(logo_path).convert("RGBA").resize((32, 32), Image.LANCZOS)
                self._sidebar_logo_photo = ImageTk.PhotoImage(_img)
                tk.Label(brand_frame, image=self._sidebar_logo_photo, bg=_SIDEBAR_BG, bd=0).pack(side="left", padx=(0, 10))
            except Exception:
                pass

        brand_text_box = tk.Frame(brand_frame, bg=_SIDEBAR_BG)
        brand_text_box.pack(side="left", fill="x", expand=True)

        self._lbl_brand_title = tk.Label(
            brand_text_box,
            text="RestInPills",
            font=self._ui_font(16, "bold"),
            bg=_SIDEBAR_BG,
            fg="#ffffff"
        )
        self._lbl_brand_title.pack(anchor="w")

        self._lbl_brand_sub = tk.Label(
            brand_text_box,
            text="Pharmacy & Knowledge Studio",
            font=self._ui_font(8),
            bg=_SIDEBAR_BG,
            fg=_NAV_INACTIVE_FG
        )
        self._lbl_brand_sub.pack(anchor="w")

        # ── Fetch User & Role ─────────────────────────────────────────────────
        user = auth.SessionManager.get_user() or {}
        role = user.get("role", config.ROLE_ADMIN)
        role_label = config.ROLE_DISPLAY_NAMES.get(role, role)
        self._user_role_en = role_label

        # ── Bottom Box: User Profile Chip + Theme Toggle & Logout ─────────────
        bottom_box = tk.Frame(self.sidebar, bg=_SIDEBAR_BG)
        bottom_box.pack(side="bottom", fill="x")

        # Pinned User Profile Card at bottom (Clickable to view My Profile)
        user_chip = tk.Frame(
            bottom_box,
            bg=_USER_CHIP_BG,
            padx=12,
            pady=10,
            highlightbackground=_USER_CHIP_BORDER,
            highlightthickness=1,
            cursor="hand2"
        )
        user_chip.pack(fill="x", pady=(0, 10))

        # Determine user initials
        full_name = user.get("full_name", "System Administrator")
        words = full_name.split()
        initials = "".join(w[0].upper() for w in words[:2]) if words else "SA"

        avatar_photo = self._make_circle_avatar(initials, size=36)
        lbl_avatar = tk.Label(user_chip, image=avatar_photo, bg=_USER_CHIP_BG, bd=0, cursor="hand2")
        lbl_avatar.pack(side="left", padx=(0, 10))

        user_text_box = tk.Frame(user_chip, bg=_USER_CHIP_BG, cursor="hand2")
        user_text_box.pack(side="left", fill="x", expand=True)

        lbl_uname = tk.Label(
            user_text_box,
            text=full_name,
            font=self._ui_font(9, "bold"),
            bg=_USER_CHIP_BG,
            fg="#ffffff",
            cursor="hand2"
        )
        lbl_uname.pack(anchor="w")
        self._lbl_user_name = lbl_uname

        lbl_urole = tk.Label(
            user_text_box,
            text=role_label,
            font=self._ui_font(8),
            bg=_USER_CHIP_BG,
            fg=_NAV_INACTIVE_FG,
            cursor="hand2"
        )
        lbl_urole.pack(anchor="w", pady=(1, 0))
        self._lbl_user_role = lbl_urole

        # Clicking the user profile chip opens My Profile
        for w in (user_chip, lbl_avatar, user_text_box, lbl_uname, lbl_urole):
            w.bind("<Button-1>", lambda e: self.navigate_to("profile"))

        btn_settings = tk.Button(
            bottom_box,
            text=f"  {self._ui_t('settings')}",
            image=self._make_nav_icon("settings", _NAV_INACTIVE_FG, 15),
            compound="left",
            font=self._ui_font(9, "bold"),
            bg="#0c263e",
            fg=_NAV_INACTIVE_FG,
            activebackground="#1e293b",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
            highlightbackground=_USER_CHIP_BORDER,
            highlightthickness=1,
            command=self._toggle_sidebar_settings
        )
        btn_settings.pack(fill="x", pady=(0, 8))
        self.btn_settings = btn_settings
        self.btn_theme = btn_settings

        btn_logout = tk.Button(
            bottom_box,
            text=self._ui_t("sign_out"),
            image=self._make_nav_icon("logout", _NAV_INACTIVE_FG, 15),
            compound="left",
            font=self._ui_font(9, "bold"),
            bg="#0c263e",
            fg=_NAV_INACTIVE_FG,
            activebackground="#1e293b",
            activeforeground="#ef4444",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
            highlightbackground=_USER_CHIP_BORDER,
            highlightthickness=1,
            command=self.handle_logout
        )
        btn_logout.pack(fill="x")
        self.btn_logout = btn_logout

        # ── Navigation Menu Items ─────────────────────────────────────────────
        self.menu_buttons = {}
        self.active_key = None
        self.build_navigation_items(role)

        # ── Right Content Area ────────────────────────────────────────────────
        self.content_area = tk.Frame(shell, bg=config.COLORS["background"])
        self.content_area.pack(side="right", fill="both", expand=True)

    # ── Sidebar Settings Popover (Matches Login Screen Settings UI) ───────────
    def _sidebar_pop_palette(self) -> dict:
        is_dark = config.get_theme() == "dark"
        if is_dark:
            return {
                "surface": "#131c2b",
                "surface_hover": "#1b273b",
                "border": "#233044",
                "border_hover": "#334560",
                "text_primary": "#f8fafc",
                "text_muted": "#94a3b8",
                "accent": "#3b72e8",
                "accent_hover": "#2563eb",
                "accent_fg": "#ffffff",
            }
        return {
            "surface": "#ffffff",
            "surface_hover": "#f1f5f9",
            "border": "#e2e8f0",
            "border_hover": "#cbd5e1",
            "text_primary": "#0f172a",
            "text_muted": "#64748b",
            "accent": "#2563eb",
            "accent_hover": "#1d4ed8",
            "accent_fg": "#ffffff",
        }

    def _toggle_sidebar_settings(self):
        self._close_sidebar_dropdown()
        if self._is_sidebar_settings_open:
            self._hide_sidebar_settings_popover()
        else:
            self._show_sidebar_settings_popover()

    def _hide_sidebar_settings_popover(self):
        self._close_sidebar_dropdown()
        self._is_sidebar_settings_open = False
        if self._sidebar_settings_popover is not None and self._sidebar_settings_popover.winfo_exists():
            self._sidebar_settings_popover.destroy()
        self._sidebar_settings_popover = None
        if self.btn_settings is not None and self.btn_settings.winfo_exists():
            self.btn_settings.config(fg=_NAV_INACTIVE_FG)

    def _close_sidebar_dropdown(self):
        if self._sidebar_active_dropdown is not None and self._sidebar_active_dropdown.winfo_exists():
            self._sidebar_active_dropdown.destroy()
        self._sidebar_active_dropdown = None

    def _show_sidebar_settings_popover(self):
        self._close_sidebar_dropdown()
        if self._sidebar_settings_popover is not None and self._sidebar_settings_popover.winfo_exists():
            self._sidebar_settings_popover.destroy()

        self._is_sidebar_settings_open = True
        if self.btn_settings is not None and self.btn_settings.winfo_exists():
            self.btn_settings.config(fg=_LIME)

        p = self._sidebar_pop_palette()
        prefs = getattr(config, "UI_PREFS", {})
        cur_theme = config.get_theme()
        cur_lang = prefs.get("language", "English")
        cur_font = prefs.get("font", "Inter")
        cur_size = prefs.get("text_size", "M")

        pop = tk.Frame(
            self.main_container,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
            padx=18,
            pady=16,
            width=276,
        )
        pop._theme_skip = True
        pop.place(x=270, rely=1.0, y=-18, anchor="sw")
        pop.lift()
        self._sidebar_settings_popover = pop

        # Header Row: "Settings" + [×] Close Button
        self._sp_hdr = tk.Frame(pop, bg=p["surface"])
        self._sp_hdr.pack(fill="x", pady=(0, 12))

        self._sp_title = tk.Label(
            self._sp_hdr,
            text=self._ui_t("settings"),
            font=self._ui_font(11, "bold"),
            bg=p["surface"],
            fg=p["text_primary"],
        )
        self._sp_title.pack(side="left")

        self._sp_close = tk.Button(
            self._sp_hdr,
            text="×",
            font=self._ui_font(10, "bold"),
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
            command=self._hide_sidebar_settings_popover,
        )
        self._sp_close.pack(side="right")

        # 1. Appearance: Light mode | Dark mode
        self._sp_lbl_app = tk.Label(
            pop,
            text=self._ui_t("appearance"),
            font=self._ui_font(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._sp_lbl_app.pack(anchor="w", pady=(0, 6))

        self._sp_app_row = tk.Frame(pop, bg=p["surface"])
        self._sp_app_row.pack(fill="x", pady=(0, 12))
        self._sp_app_row.grid_columnconfigure(0, weight=1, uniform="sp_app")
        self._sp_app_row.grid_columnconfigure(1, weight=1, uniform="sp_app")

        self._sp_btn_light = self._make_sp_segmented_btn(
            self._sp_app_row, 0, self._ui_t("light_mode"),
            active=(cur_theme == "light"),
            command=lambda: self.set_theme_mode("light"),
            padx=(0, 4),
        )
        self._sp_btn_dark = self._make_sp_segmented_btn(
            self._sp_app_row, 1, self._ui_t("dark_mode"),
            active=(cur_theme == "dark"),
            command=lambda: self.set_theme_mode("dark"),
            padx=(4, 0),
        )

        # 2. Language Dropdown
        self._sp_lbl_lang = tk.Label(
            pop,
            text=self._ui_t("language"),
            font=self._ui_font(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._sp_lbl_lang.pack(anchor="w", pady=(0, 6))

        self._sp_lang_box, self._sp_lang_val, self._sp_lang_chv = self._make_sp_dropdown(
            pop,
            current_val=cur_lang,
            options=["English", "Filipino", "Spanish"],
            on_select=self._on_sidebar_lang_change,
        )
        self._sp_lang_box.pack(fill="x", pady=(0, 12))

        # 3. Font Dropdown
        self._sp_lbl_font = tk.Label(
            pop,
            text=self._ui_t("font"),
            font=self._ui_font(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._sp_lbl_font.pack(anchor="w", pady=(0, 6))

        self._sp_font_box, self._sp_font_val, self._sp_font_chv = self._make_sp_dropdown(
            pop,
            current_val=cur_font,
            options=["Inter", "Segoe UI", "Calibri", "Arial", "Consolas"],
            on_select=self._on_sidebar_font_change,
        )
        self._sp_font_box.pack(fill="x", pady=(0, 12))

        # 4. Text size: S | M | L | XL
        self._sp_lbl_sz = tk.Label(
            pop,
            text=self._ui_t("text_size"),
            font=self._ui_font(8),
            bg=p["surface"],
            fg=p["text_muted"],
        )
        self._sp_lbl_sz.pack(anchor="w", pady=(0, 6))

        self._sp_sz_row = tk.Frame(pop, bg=p["surface"])
        self._sp_sz_row.pack(fill="x")
        self._sp_size_btns = {}
        for idx, sz in enumerate(["S", "M", "L", "XL"]):
            self._sp_sz_row.grid_columnconfigure(idx, weight=1, uniform="sp_sz")
            px = (0, 3) if idx == 0 else ((3, 0) if idx == 3 else (3, 3))
            self._sp_size_btns[sz] = self._make_sp_segmented_btn(
                self._sp_sz_row, idx, sz,
                active=(cur_size == sz),
                command=lambda s=sz: self._on_sidebar_size_change(s),
                padx=px,
            )

    def _make_sp_segmented_btn(self, parent, col, text, active: bool, command, padx=(0, 0)):
        p = self._sidebar_pop_palette()
        bg = p["accent"] if active else p["surface"]
        fg = p["accent_fg"] if active else p["text_primary"]
        bd_col = p["accent"] if active else p["border"]

        btn = tk.Button(
            parent,
            text=text,
            font=self._ui_font(8, "bold"),
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

    def _make_sp_dropdown(self, parent, current_val: str, options: list, on_select):
        p = self._sidebar_pop_palette()
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
            font=self._ui_font(9, "bold"),
            bg=p["surface"],
            fg=p["text_primary"],
            anchor="w",
            cursor="hand2",
        )
        lbl_val.pack(side="left", fill="x", expand=True)

        lbl_chev = tk.Label(
            box,
            text="⌄",
            font=self._ui_font(9, "bold"),
            bg=p["surface"],
            fg=p["text_muted"],
            cursor="hand2",
        )
        lbl_chev.pack(side="right")

        def open_menu(e):
            self._open_sp_dropdown_menu(box, options, lbl_val.cget("text"), on_select)

        for w in (box, lbl_val, lbl_chev):
            w.bind("<Button-1>", open_menu)
        return box, lbl_val, lbl_chev

    def _open_sp_dropdown_menu(self, anchor_widget, options: list, current_val: str, on_select):
        self._close_sidebar_dropdown()
        p = self._sidebar_pop_palette()

        anchor_widget.update_idletasks()
        ax = anchor_widget.winfo_rootx() - self.main_container.winfo_rootx()
        ay = anchor_widget.winfo_rooty() - self.main_container.winfo_rooty() + anchor_widget.winfo_height() + 2
        aw = anchor_widget.winfo_width()

        menu_frame = tk.Frame(
            self.main_container,
            bg=p["surface"],
            highlightbackground=p["border"],
            highlightthickness=1,
        )
        menu_frame._theme_skip = True
        menu_frame.place(x=ax, y=ay, width=aw)
        menu_frame.lift()
        self._sidebar_active_dropdown = menu_frame

        for opt in options:
            is_sel = (opt == current_val)
            item = tk.Label(
                menu_frame,
                text=opt,
                font=self._ui_font(9, "bold" if is_sel else "normal"),
                bg=p["surface_hover"] if is_sel else p["surface"],
                fg=p["accent"] if is_sel else p["text_primary"],
                anchor="w",
                padx=10,
                pady=6,
                cursor="hand2",
            )
            item.pack(fill="x")
            item.bind("<Button-1>", lambda e, val=opt: (self._close_sidebar_dropdown(), on_select(val)))
            item.bind("<Enter>", lambda e, w=item: w.config(bg=self._sidebar_pop_palette()["surface_hover"]))
            item.bind("<Leave>", lambda e, w=item, s=is_sel: w.config(bg=self._sidebar_pop_palette()["surface_hover"] if s else self._sidebar_pop_palette()["surface"]))

    def _refresh_sidebar_settings_popover(self):
        """Updates the open sidebar Settings popover in-place without rebuilding it."""
        if self._sidebar_settings_popover is None or not self._sidebar_settings_popover.winfo_exists():
            return
        p = self._sidebar_pop_palette()
        prefs = getattr(config, "UI_PREFS", {})
        cur_theme = config.get_theme()
        cur_lang = prefs.get("language", "English")
        cur_font = prefs.get("font", "Inter")
        cur_size = prefs.get("text_size", "M")

        self._sidebar_settings_popover.configure(bg=p["surface"], highlightbackground=p["border"])
        for f in (self._sp_hdr, self._sp_app_row, self._sp_sz_row):
            f.configure(bg=p["surface"])

        self._sp_title.configure(text=self._ui_t("settings"), font=self._ui_font(11, "bold"), bg=p["surface"], fg=p["text_primary"])
        self._sp_close.configure(
            font=self._ui_font(10, "bold"),
            bg=p["surface"],
            fg=p["text_muted"],
            activebackground=p["surface_hover"],
            activeforeground=p["text_primary"],
            highlightbackground=p["border"],
        )

        for lbl, key in (
            (self._sp_lbl_app, "appearance"),
            (self._sp_lbl_lang, "language"),
            (self._sp_lbl_font, "font"),
            (self._sp_lbl_sz, "text_size"),
        ):
            lbl.configure(text=self._ui_t(key), font=self._ui_font(8), bg=p["surface"], fg=p["text_muted"])

        for btn, active, txt_key in (
            (self._sp_btn_light, cur_theme == "light", "light_mode"),
            (self._sp_btn_dark, cur_theme == "dark", "dark_mode"),
        ):
            btn.configure(
                text=self._ui_t(txt_key),
                font=self._ui_font(8, "bold"),
                bg=p["accent"] if active else p["surface"],
                fg=p["accent_fg"] if active else p["text_primary"],
                activebackground=p["accent_hover"] if active else p["surface_hover"],
                activeforeground=p["accent_fg"] if active else p["text_primary"],
                highlightbackground=p["accent"] if active else p["border"],
            )

        for sz, btn in self._sp_size_btns.items():
            active = (cur_size == sz)
            btn.configure(
                font=self._ui_font(8, "bold"),
                bg=p["accent"] if active else p["surface"],
                fg=p["accent_fg"] if active else p["text_primary"],
                activebackground=p["accent_hover"] if active else p["surface_hover"],
                activeforeground=p["accent_fg"] if active else p["text_primary"],
                highlightbackground=p["accent"] if active else p["border"],
            )

        for box, val_l, chv_l, val_txt in (
            (self._sp_lang_box, self._sp_lang_val, self._sp_lang_chv, cur_lang),
            (self._sp_font_box, self._sp_font_val, self._sp_font_chv, cur_font),
        ):
            box.configure(bg=p["surface"], highlightbackground=p["border"])
            val_l.configure(text=val_txt, font=self._ui_font(9, "bold"), bg=p["surface"], fg=p["text_primary"])
            chv_l.configure(font=self._ui_font(9, "bold"), bg=p["surface"], fg=p["text_muted"])

    def _parse_font_spec(self, raw_font: str) -> tuple:
        """Parses any Tkinter font spec into (family, base_pt_size, flags_tuple) with caching."""
        cached = self._font_spec_cache.get(raw_font)
        if cached is not None:
            return cached
        try:
            f_obj = tkfont.Font(root=self, font=raw_font)
            act = f_obj.actual()
            fam = act.get("family", "Segoe UI")
            sz = int(act.get("size", 10))
            if sz < 0:
                sz = max(8, int(round(abs(sz) * 0.75)))
            flags = []
            if act.get("weight") == "bold":
                flags.append("bold")
            if act.get("slant") == "italic":
                flags.append("italic")
            res = (fam, sz, tuple(flags))
        except Exception:
            res = ("Segoe UI", 10, ())
        self._font_spec_cache[raw_font] = res
        return res

    def _translate_content_text(self, en_text: str, lang: str) -> str:
        """Translates known UI phrases and patterns across content screens while preserving dynamic values."""
        if not en_text or lang == "English":
            return en_text

        exact_map = {
            "Filipino": {
                "Pharmacy & Knowledge Studio": "Parmasya at Knowledge Studio",
                "Administrator": "Administrador",
                "Inventory Clerk": "Klerk ng Imbentaryo",
                "Sales Personnel": "Kawani ng Benta",
                "Academic Instructor": "Instruktor",
                "Here is how the pharmacy is doing today.": "Narito ang lagay ng parmasya ngayong araw.",
                "Refresh data": "I-refresh ang datos",
                "Sales Today": "Benta Ngayon",
                "Month-to-Date Revenue": "Kita Ngayong Buwan",
                "Total Products": "Kabuuang Produkto",
                "Low-Stock Alerts": "Alerto sa Mababang Stak",
                "Near-Expiry Alerts": "Malapit Nang Mag-expire",
                "Top Performing Product": "Pinakamabentang Produkto",
                "Current month": "Kasalukuyang buwan",
                "Active in catalog": "Aktibo sa katalogo",
                "Needs restocking": "Kailangang dagdagan",
                "14-day sales revenue trend": "14-araw na tunguhin ng benta",
                "Top 5 products by quantity sold": "Nangungunang 5 produkto sa benta",
                "Sales breakdown by category": "Benta ayon sa kategorya",
                "Stock health distribution": "Kalagayan ng stak",
                "products in catalog": "produkto sa katalogo",
                "Healthy": "Maayos",
                "Low stock": "Mababang stak",
                "Out of stock": "Walang stak",
                "My Profile": "Aking Profile",
                "Session active": "Aktibo ang sesyon",
                "Account details": "Detalye ng account",
                "FULL NAME": "BUONG PANGALAN",
                "USERNAME": "USERNAME",
                "EMAIL ADDRESS": "EMAIL ADDRESS",
                "ASSIGNED ROLE": "TUNGKULIN",
                "Current session": "Kasalukuyang sesyon",
                "STARTED": "SINIMULAN",
                "STATUS": "KATAYUAN",
                "Active": "Aktibo",
                "Inventory Management": "Pamamahala ng Imbentaryo",
                "Product Catalog": "Katalogo ng Produkto",
                "Stock Movements": "Galaw ng Stak",
                "Categories & Suppliers": "Mga Kategorya at Supplier",
                "Point of Sale (POS)": "Punto ng Benta (POS)",
                "Sales History": "Kasaysayan ng Benta",
                "👥 User Accounts & Security Audit Trail": "👥 Mga Account at Audit Trail",
                "+ Add New User": "+ Magdagdag ng User",
                "✎ Edit User": "✎ I-edit ang User",
                "🔑 Reset Password": "🔑 I-reset ang Password",
                "🔓 Unlock Account": "🔓 I-unlock ang Account",
                "Toggle Active / Inactive": "Palitan Aktibo / Di-Aktibo",
                "Filter Action:": "Salain ang Aksyon:",
                "↻ Refresh Log": "↻ I-refresh ang Log",
                "Select Analysis Task:": "Piliin ang Gawain:",
                "⚡ Retrain Models": "⚡ Sanayin Muli ang Modelo",
                "⚙ Prediction Parameters": "⚙ Mga Parameter ng Prediksyon",
                "Machine Learning Model:": "Modelo ng Machine Learning:",
                "📊 Prediction Results & Output Visualizer": "📊 Resulta ng Prediksyon",
                "🚀 Calculate Prediction": "🚀 Kalkulahin ang Prediksyon",
            },
            "Spanish": {
                "Pharmacy & Knowledge Studio": "Estudio de Farmacia y Conocimiento",
                "Administrator": "Administrador",
                "Inventory Clerk": "Encargado de Inventario",
                "Sales Personnel": "Personal de Ventas",
                "Academic Instructor": "Instructor Académico",
                "Here is how the pharmacy is doing today.": "Así va la farmacia el día de hoy.",
                "Refresh data": "Actualizar datos",
                "Sales Today": "Ventas de Hoy",
                "Month-to-Date Revenue": "Ingresos del Mes",
                "Total Products": "Total de Productos",
                "Low-Stock Alerts": "Alertas de Bajo Stock",
                "Near-Expiry Alerts": "Alertas de Próximo Vencimiento",
                "Top Performing Product": "Producto Más Vendido",
                "Current month": "Mes actual",
                "Active in catalog": "Activo en catálogo",
                "Needs restocking": "Necesita reabastecimiento",
                "14-day sales revenue trend": "Tendencia de ingresos de 14 días",
                "Top 5 products by quantity sold": "Top 5 productos por cantidad vendida",
                "Sales breakdown by category": "Ventas por categoría",
                "Stock health distribution": "Distribución de salud del stock",
                "products in catalog": "productos en catálogo",
                "Healthy": "Saludable",
                "Low stock": "Bajo stock",
                "Out of stock": "Sin stock",
                "My Profile": "Mi Perfil",
                "Session active": "Sesión activa",
                "Account details": "Detalles de la cuenta",
                "FULL NAME": "NOMBRE COMPLETO",
                "USERNAME": "USUARIO",
                "EMAIL ADDRESS": "CORREO ELECTRÓNICO",
                "ASSIGNED ROLE": "ROL ASIGNADO",
                "Current session": "Sesión actual",
                "STARTED": "INICIADO",
                "STATUS": "ESTADO",
                "Active": "Activo",
                "Inventory Management": "Gestión de Inventario",
                "Product Catalog": "Catálogo de Productos",
                "Stock Movements": "Movimientos de Stock",
                "Categories & Suppliers": "Categorías y Proveedores",
                "Point of Sale (POS)": "Punto de Venta (POS)",
                "Sales History": "Historial de Ventas",
                "👥 User Accounts & Security Audit Trail": "👥 Cuentas de Usuario y Auditoría",
                "+ Add New User": "+ Añadir Usuario",
                "✎ Edit User": "✎ Editar Usuario",
                "🔑 Reset Password": "🔑 Restablecer Contraseña",
                "🔓 Unlock Account": "🔓 Desbloquear Cuenta",
                "Toggle Active / Inactive": "Alternar Activo / Inactivo",
                "Filter Action:": "Filtrar Acción:",
                "↻ Refresh Log": "↻ Actualizar Registro",
                "Select Analysis Task:": "Seleccionar Tarea de Análisis:",
                "⚡ Retrain Models": "⚡ Reentrenar Modelos",
                "⚙ Prediction Parameters": "⚙ Parámetros de Predicción",
                "Machine Learning Model:": "Modelo de Aprendizaje Automático:",
                "📊 Prediction Results & Output Visualizer": "📊 Resultados de Predicción",
                "🚀 Calculate Prediction": "🚀 Calcular Predicción",
            },
        }

        lang_dict = exact_map.get(lang, {})
        if en_text in lang_dict:
            return lang_dict[en_text]

        # Prefix / suffix pattern translations
        if en_text.startswith("Welcome back, "):
            name = en_text[len("Welcome back, "):]
            if lang == "Filipino":
                return f"Maligayang pagbabalik, {name}"
            if lang == "Spanish":
                return f"Bienvenido de nuevo, {name}"
        if en_text.startswith("Role: "):
            r_val = en_text[len("Role: "):]
            r_tr = lang_dict.get(r_val, r_val)
            if lang == "Filipino":
                return f"Tungkulin: {r_tr}"
            if lang == "Spanish":
                return f"Rol: {r_tr}"
        if en_text.endswith(" transactions"):
            cnt = en_text[:-len(" transactions")]
            if lang == "Filipino":
                return f"{cnt} transaksyon"
            if lang == "Spanish":
                return f"{cnt} transacciones"
        if en_text.endswith(" units sold"):
            cnt = en_text[:-len(" units sold")]
            if lang == "Filipino":
                return f"{cnt} pirasong naibenta"
            if lang == "Spanish":
                return f"{cnt} unidades vendidas"
        if en_text.startswith("Within ") and en_text.endswith(" days"):
            days = en_text[len("Within "):-len(" days")]
            if lang == "Filipino":
                return f"Sa loob ng {days} araw"
            if lang == "Spanish":
                return f"Dentro de {days} días"
        if en_text.endswith(" products expire within 90 days."):
            cnt = en_text[:-len(" products expire within 90 days.")]
            if lang == "Filipino":
                return f"{cnt} produkto ang mag-e-expire sa loob ng 90 araw."
            if lang == "Spanish":
                return f"{cnt} productos vencen en 90 días."
        return en_text

    def _sync_widget_tree_typography(self, root_widget, fam: str, off: int, lang: str):
        """Recursively updates fonts, text sizes, and translations across all widgets in root_widget."""
        if root_widget is None:
            return
        try:
            if not root_widget.winfo_exists():
                return
        except Exception:
            return

        stack = [root_widget]
        while stack:
            w = stack.pop()
            try:
                if not w.winfo_exists() or getattr(w, "_typo_skip", False):
                    continue
            except Exception:
                continue

            # 1. Update widget font if supported
            try:
                cur_font_str = str(w.cget("font"))
            except Exception:
                cur_font_str = ""

            if cur_font_str:
                try:
                    last_set_font = getattr(w, "_last_set_font_str", None)
                    if not hasattr(w, "_base_font_spec") or (last_set_font is not None and cur_font_str != last_set_font):
                        w._base_font_spec = self._parse_font_spec(cur_font_str)

                    orig_fam, base_sz, flags = w._base_font_spec
                    target_fam = orig_fam if (orig_fam == "Courier New" and fam != "Consolas") else fam
                    if getattr(w, "_fixed_pill_badge", False):
                        new_sz = max(7, base_sz + min(1, max(-1, off)))
                    else:
                        new_sz = max(7, base_sz + off)
                    new_font = (target_fam, new_sz, *flags) if flags else (target_fam, new_sz)
                    w.configure(font=new_font)
                    w._last_set_font_str = str(w.cget("font"))
                except Exception:
                    pass

            # 2. Update widget text translation if supported (Labels, Buttons, Checkbuttons, Radiobuttons)
            if isinstance(w, (tk.Label, tk.Button, tk.Checkbutton, tk.Radiobutton, tk.LabelFrame)):
                try:
                    cur_txt = str(w.cget("text"))
                    if cur_txt:
                        last_set_txt = getattr(w, "_last_set_text_str", None)
                        if not hasattr(w, "_base_en_text") or (last_set_txt is not None and cur_txt != last_set_txt):
                            w._base_en_text = cur_txt
                        tr_txt = self._translate_content_text(w._base_en_text, lang)
                        if tr_txt != cur_txt:
                            w.configure(text=tr_txt)
                        w._last_set_text_str = tr_txt
                except Exception:
                    pass

            # 3. Update Canvas text items if widget is a tk.Canvas
            if isinstance(w, tk.Canvas):
                try:
                    base_fonts = getattr(w, "_canvas_base_fonts", None)
                    if base_fonts is None:
                        base_fonts = {}
                        w._canvas_base_fonts = base_fonts
                    for item_id in w.find_all():
                        if w.type(item_id) == "text":
                            if item_id not in base_fonts:
                                item_f = str(w.itemcget(item_id, "font"))
                                base_fonts[item_id] = self._parse_font_spec(item_f) if item_f else ("Segoe UI", 10, ())
                            orig_fam, base_sz, flags = base_fonts[item_id]
                            new_sz = max(7, base_sz + off)
                            new_font = (fam, new_sz, *flags) if flags else (fam, new_sz)
                            w.itemconfigure(item_id, font=new_font)
                except Exception:
                    pass

            try:
                children = w.winfo_children()
                if children:
                    stack.extend(children)
            except Exception:
                pass

    def _on_any_widget_map(self, event=None):
        """Debounced handler so newly opened tabs, refreshed views, or dialogs inherit typography."""
        if self.sidebar is None or self._typo_idle_scheduled:
            return
        self._typo_idle_scheduled = True
        self.after_idle(self._run_deferred_typography_sync)

    def _run_deferred_typography_sync(self):
        self._typo_idle_scheduled = False
        if self.sidebar is None:
            return
        fam = self._resolve_ui_font_family()
        prefs = getattr(config, "UI_PREFS", {})
        sz = prefs.get("text_size", "M")
        off = {"S": -1, "M": 0, "L": 2, "XL": 3}.get(sz, 0)
        lang = prefs.get("language", "English")
        if self.content_area is not None and self.content_area.winfo_exists():
            self._sync_widget_tree_typography(self.content_area, fam, off, lang)
        for child in self.winfo_children():
            if isinstance(child, tk.Toplevel) and child.winfo_exists():
                self._sync_widget_tree_typography(child, fam, off, lang)

    def _apply_global_typography(self):
        """Updates TTK styles, sidebar labels, and the entire active content screen in-place."""
        fam = self._resolve_ui_font_family()
        prefs = getattr(config, "UI_PREFS", {})
        sz = prefs.get("text_size", "M")
        off = {"S": -1, "M": 0, "L": 2, "XL": 3}.get(sz, 0)
        lang = prefs.get("language", "English")

        self.setup_ttk_styles()

        # Update Sidebar Brand & User Chip
        if getattr(self, "_lbl_brand_title", None) is not None and self._lbl_brand_title.winfo_exists():
            self._lbl_brand_title.configure(font=self._ui_font(16, "bold"))
        if getattr(self, "_lbl_brand_sub", None) is not None and self._lbl_brand_sub.winfo_exists():
            self._lbl_brand_sub.configure(
                text=self._translate_content_text("Pharmacy & Knowledge Studio", lang),
                font=self._ui_font(8),
            )
        if getattr(self, "_lbl_user_name", None) is not None and self._lbl_user_name.winfo_exists():
            self._lbl_user_name.configure(font=self._ui_font(9, "bold"))
        if getattr(self, "_lbl_user_role", None) is not None and self._lbl_user_role.winfo_exists():
            role_en = getattr(self, "_user_role_en", "Administrator")
            self._lbl_user_role.configure(
                text=self._translate_content_text(role_en, lang),
                font=self._ui_font(8),
            )

        if self.btn_settings is not None and self.btn_settings.winfo_exists():
            self.btn_settings.configure(
                text=f"  {self._ui_t('settings')}",
                image=self._make_nav_icon("settings", _LIME if self._is_sidebar_settings_open else _NAV_INACTIVE_FG, 15),
                compound="left",
                font=self._ui_font(9, "bold"),
            )
        if self.btn_logout is not None and self.btn_logout.winfo_exists():
            self.btn_logout.configure(
                text=self._ui_t("sign_out"),
                image=self._make_nav_icon("logout", _NAV_INACTIVE_FG, 15),
                compound="left",
                font=self._ui_font(9, "bold"),
            )

        nav_keys = {
            "dashboard": "nav_dashboard",
            "inventory": "nav_inventory",
            "sales": "nav_sales",
            "users": "nav_users",
            "analysis": "nav_analysis",
            "profile": "nav_profile",
        }
        for k, btn in getattr(self, "menu_buttons", {}).items():
            if btn.winfo_exists():
                ic_col = "#0A101C" if k == self.active_key else _NAV_INACTIVE_FG
                btn.configure(
                    text=self._ui_t(nav_keys.get(k, k)),
                    image=self._make_nav_icon(k, ic_col, 16),
                    compound="left",
                    font=self._ui_font(9, "bold"),
                )

        # Update the whole content area and any open Toplevel dialogs
        if self.content_area is not None and self.content_area.winfo_exists():
            self._sync_widget_tree_typography(self.content_area, fam, off, lang)
        for child in self.winfo_children():
            if isinstance(child, tk.Toplevel) and child.winfo_exists():
                self._sync_widget_tree_typography(child, fam, off, lang)

        # Update Matplotlib chart typography on Dashboard if present
        if self.current_screen is not None and hasattr(self.current_screen, "_mpl_charts"):
            for chart in getattr(self.current_screen, "_mpl_charts", []):
                try:
                    if len(chart) == 5:
                        chart_type, fig, ax, canvas, extra = chart
                    elif len(chart) == 3:
                        fig, ax, canvas = chart
                        chart_type, extra = None, {}
                    else:
                        continue

                    if chart_type == "trend":
                        ax.tick_params(labelsize=max(6, 8 + off))
                    elif chart_type == "donut":
                        if "txt_pct" in extra:
                            extra["txt_pct"].set_fontsize(max(12, 18 + off))
                        if "txt_cat" in extra:
                            extra["txt_cat"].set_fontsize(max(7, 9 + off))
                    canvas.draw_idle()
                except Exception:
                    pass

        self._refresh_sidebar_settings_popover()

    def _on_sidebar_lang_change(self, lang: str):
        if hasattr(config, "UI_PREFS"):
            config.UI_PREFS["language"] = lang
        self._apply_global_typography()

    def _on_sidebar_font_change(self, font_name: str):
        if hasattr(config, "UI_PREFS"):
            config.UI_PREFS["font"] = font_name
        self._apply_global_typography()

    def _on_sidebar_size_change(self, sz: str):
        if hasattr(config, "UI_PREFS"):
            config.UI_PREFS["text_size"] = sz
        self._apply_global_typography()

    def _is_nav_allowed(self, key: str, role: str) -> bool:
        """Determines whether a navigation item is permitted for the given role."""
        perms = config.ROLE_PERMISSIONS.get(role)
        if perms is None and auth.SessionManager.is_authenticated():
            perms = config.ROLE_PERMISSIONS.get(auth.SessionManager.get_role(), [])
        if perms is None:
            perms = []

        if key == "dashboard":
            return "dashboard_view" in perms or not perms
        if key == "inventory":
            return "inventory_view" in perms
        if key == "sales":
            return "sales_pos" in perms or "sales_history" in perms
        if key == "users":
            return "users_manage" in perms
        if key == "analysis":
            return "analysis_input_predict" in perms
        if key == "profile":
            return "profile_view" in perms or not perms
        return True

    def build_navigation_items(self, role):
        """Constructs role-tailored sidebar menu items with sleek pill highlights."""
        all_items = [
            ("dashboard", self._ui_t("nav_dashboard")),
            ("inventory", self._ui_t("nav_inventory")),
            ("sales", self._ui_t("nav_sales")),
            ("users", self._ui_t("nav_users")),
            ("analysis", self._ui_t("nav_analysis")),
            ("profile", self._ui_t("nav_profile")),
        ]

        items = [(k, label) for k, label in all_items if self._is_nav_allowed(k, role)]

        for key, label in items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                image=self._make_nav_icon(key, _NAV_INACTIVE_FG, 16),
                compound="left",
                font=self._ui_font(9, "bold"),
                bg=_SIDEBAR_BG,
                fg=_NAV_INACTIVE_FG,
                activebackground=_NAV_HOVER_BG,
                activeforeground="#ffffff",
                relief="flat",
                cursor="hand2",
                anchor="w",
                padx=14,
                pady=9,
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=2)

            # Hover animations
            def on_enter(e, b=btn, k=key):
                if self.active_key != k:
                    b.config(bg=_NAV_HOVER_BG, fg="#ffffff", image=self._make_nav_icon(k, "#ffffff", 16))
            def on_leave(e, b=btn, k=key):
                if self.active_key != k:
                    b.config(bg=_SIDEBAR_BG, fg=_NAV_INACTIVE_FG, image=self._make_nav_icon(k, _NAV_INACTIVE_FG, 16))

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

            self.menu_buttons[key] = btn

    def set_active_menu(self, active_key):
        self.active_key = active_key
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                # Active item styled as vibrant lime pill with dark text
                btn.config(
                    bg=_LIME,
                    fg="#0A101C",
                    image=self._make_nav_icon(key, "#0A101C", 16),
                    font=self._ui_font(9, "bold")
                )
            else:
                btn.config(
                    bg=_SIDEBAR_BG,
                    fg=_NAV_INACTIVE_FG,
                    image=self._make_nav_icon(key, _NAV_INACTIVE_FG, 16),
                    font=self._ui_font(9, "bold")
                )

    def navigate_to(self, screen_name):
        """Routes and displays the requested screen inside content_area with RBAC enforcement."""
        self._hide_sidebar_settings_popover()
        # Enforce RBAC
        role = auth.SessionManager.get_role()
        
        # Check permission mappings
        if screen_name == "inventory" and not auth.SessionManager.has_permission("inventory_view"):
            messagebox.showerror("Access Denied", "You do not have permission to access the Inventory module.")
            return
        if screen_name == "sales" and not (auth.SessionManager.has_permission("sales_pos") or auth.SessionManager.has_permission("sales_history")):
            messagebox.showerror("Access Denied", "You do not have permission to access the Sales module.")
            return
        if screen_name == "users" and not auth.SessionManager.has_permission("users_manage"):
            messagebox.showerror("Access Denied", "You do not have permission to access User Management.")
            return
        if screen_name == "analysis" and not auth.SessionManager.has_permission("analysis_input_predict"):
            messagebox.showerror("Access Denied", "You do not have permission to access Knowledge Analysis.")
            return

        # Destroy active screen widget
        if self.current_screen:
            self.current_screen.destroy()
            self.current_screen = None

        self.set_active_menu(screen_name)

        # Lazy loading of screen views
        if screen_name == "dashboard":
            self.current_screen = DashboardScreen(self.content_area, self)
        elif screen_name == "inventory":
            from screens.inventory import InventoryScreen
            self.current_screen = InventoryScreen(self.content_area, self)
        elif screen_name == "sales":
            from screens.sales import SalesScreen
            self.current_screen = SalesScreen(self.content_area, self)
        elif screen_name == "users":
            from screens.users import UsersScreen
            self.current_screen = UsersScreen(self.content_area, self)
        elif screen_name == "analysis":
            from screens.analysis import AnalysisScreen
            self.current_screen = AnalysisScreen(self.content_area, self)
        elif screen_name == "profile":
            self.current_screen = ProfileScreen(self.content_area, self)

        if self.current_screen:
            self.current_screen.pack(fill="both", expand=True)
            self._apply_global_typography()

    def _make_pill_badge(self, parent, text, fill_color, text_color, parent_bg, border_color=None):
        """Creates a smooth antialiased rounded pill badge label."""
        fnt = tkfont.Font(family="Segoe UI", size=8, weight="bold")
        tw = fnt.measure(text)
        pill_w = max(56, tw + 24)
        pill_h = 24
        scale = 3
        sw, sh = pill_w * scale, pill_h * scale
        r = (pill_h * scale) // 2

        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if border_color:
            d.rounded_rectangle([1, 1, sw - 2, sh - 2], radius=r, fill=fill_color, outline=border_color, width=scale)
        else:
            d.rounded_rectangle([0, 0, sw - 1, sh - 1], radius=r, fill=fill_color)

        final_img = img.resize((pill_w, pill_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(final_img)
        if not hasattr(self, "_avatar_photos"):
            self._avatar_photos = []
        self._avatar_photos.append(photo)

        lbl = tk.Label(
            parent,
            image=photo,
            text=text,
            compound="center",
            font=("Segoe UI", 8, "bold"),
            fg=text_color,
            bg=parent_bg,
            bd=0,
            padx=0,
            pady=0
        )
        lbl._fixed_pill_badge = True
        return lbl

    def handle_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your session?"):
            auth.logout_user()
            self.show_login_screen()


class ProfileScreen(tk.Frame):
    def __init__(self, parent, controller):
        c = config.COLORS
        super().__init__(parent, bg=c["background"], padx=34, pady=26)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self._motion_bg = attach_motion_bg(self, bg_key="background")
        user = auth.SessionManager.get_user() or {}
        is_dark = config.get_theme() == "dark" if hasattr(config, "get_theme") else False
        c = config.COLORS
        page_bg = c["background"]
        hero_bg = "#0c1b2e"
        card_bg = c["surface"]

        # In dark mode: border is completely removed! In light mode: subtle 1px border.
        border_thick = 0 if is_dark else 1
        border_col = c["surface"] if is_dark else "#e6ebf1"
        divider_col = "#1e3350" if is_dark else "#eef2f6"
        lime_col = "#b4e633"

        full_name = user.get("full_name") or "System Administrator"
        username = user.get("username") or "admin"
        email = user.get("email") or "admin@restinpills.local"
        role_raw = user.get("role") or config.ROLE_ADMIN
        role_label = config.ROLE_DISPLAY_NAMES.get(role_raw, role_raw)

        raw_login = user.get("last_login")
        if isinstance(raw_login, datetime):
            started_str = raw_login.strftime("%Y-%m-%d · %H:%M")
        elif raw_login:
            s_val = str(raw_login).strip()
            try:
                dt = datetime.fromisoformat(s_val)
                started_str = dt.strftime("%Y-%m-%d · %H:%M")
            except Exception:
                started_str = s_val[:16].replace(" ", " · ")
        else:
            started_str = datetime.now().strftime("%Y-%m-%d · %H:%M")

        words = full_name.split()
        initials = "".join(w[0].upper() for w in words[:2]) if words else "SA"

        # ── Page Header ──
        self.lbl_title = tk.Label(
            self,
            text="My Profile",
            font=("Segoe UI", 18, "bold"),
            bg=page_bg,
            fg=c["text_dark"]
        )
        self.lbl_title.pack(anchor="w", pady=(0, 18))

        # ── Hero Banner Card (Deep Navy) ──
        self.hero_card = tk.Frame(
            self,
            bg=hero_bg,
            padx=28,
            pady=24,
            highlightthickness=0
        )
        self.hero_card.pack(fill="x", pady=(0, 20))

        avatar_big = self.controller._make_circle_avatar(
            initials,
            size=72,
            bg_color=lime_col,
            text_color="#0c1b2e",
            font_size=22
        )
        tk.Label(self.hero_card, image=avatar_big, bg=hero_bg, bd=0).pack(side="left", padx=(0, 22))

        hero_info = tk.Frame(self.hero_card, bg=hero_bg)
        hero_info.pack(side="left", fill="x", expand=True)

        tk.Label(
            hero_info,
            text=full_name,
            font=("Segoe UI", 17, "bold"),
            bg=hero_bg,
            fg="#ffffff"
        ).pack(anchor="w")

        tk.Label(
            hero_info,
            text=email,
            font=("Segoe UI", 10),
            bg=hero_bg,
            fg="#94a3b8"
        ).pack(anchor="w", pady=(2, 10))

        badges_row = tk.Frame(hero_info, bg=hero_bg)
        badges_row.pack(anchor="w")

        role_pill = self.controller._make_pill_badge(
            badges_row,
            text=role_label,
            fill_color=lime_col,
            text_color="#0c1b2e",
            parent_bg=hero_bg
        )
        role_pill.pack(side="left")

        session_pill = self.controller._make_pill_badge(
            badges_row,
            text="Session active",
            fill_color="#132338",
            text_color="#e2e8f0",
            parent_bg=hero_bg,
            border_color="#2a3f5a"
        )
        session_pill.pack(side="left", padx=(8, 0))

        # ── Bottom Two-Column Cards Row ──
        self.cards_row = tk.Frame(self, bg=page_bg)
        self.cards_row.pack(fill="x", anchor="n")
        self.cards_row.grid_columnconfigure(0, weight=65)
        self.cards_row.grid_columnconfigure(1, weight=35)

        # Left Card: Account details (border removed in dark mode)
        self.acct_card = tk.Frame(
            self.cards_row,
            bg=card_bg,
            padx=28,
            pady=24,
            highlightbackground=border_col,
            highlightthickness=border_thick
        )
        self.acct_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.lbl_acct_title = tk.Label(
            self.acct_card,
            text="Account details",
            font=("Segoe UI", 12, "bold"),
            bg=card_bg,
            fg=c["text_dark"]
        )
        self.lbl_acct_title.pack(anchor="w", pady=(0, 14))

        self.acct_grid = tk.Frame(self.acct_card, bg=card_bg)
        self.acct_grid.pack(fill="x")
        self.acct_grid.grid_columnconfigure(0, weight=1, uniform="acct_col")
        self.acct_grid.grid_columnconfigure(1, weight=1, uniform="acct_col")

        acct_fields = [
            (0, 0, "FULL NAME", full_name, (0, 16), (0, 14)),
            (0, 1, "USERNAME", username, (16, 0), (0, 14)),
            (1, 0, "EMAIL ADDRESS", email, (0, 16), (0, 4)),
            (1, 1, "ASSIGNED ROLE", role_label, (16, 0), (0, 4)),
        ]

        self.cells = []
        self.dividers = []
        self.muted_labels = []
        self.val_labels = []

        for r_idx, c_idx, lbl_txt, val_txt, px, py_bot in acct_fields:
            cell = tk.Frame(self.acct_grid, bg=card_bg)
            cell.grid(row=r_idx, column=c_idx, sticky="ew", padx=px)
            self.cells.append(cell)

            d = tk.Frame(cell, bg=divider_col, height=1)
            d.pack(fill="x", pady=(0, 12))
            self.dividers.append(d)

            ml = tk.Label(
                cell,
                text=lbl_txt,
                font=("Segoe UI", 8, "bold"),
                bg=card_bg,
                fg=c["text_muted"]
            )
            ml.pack(anchor="w")
            self.muted_labels.append(ml)

            vl = tk.Label(
                cell,
                text=val_txt,
                font=("Segoe UI", 10, "bold"),
                bg=card_bg,
                fg=c["text_dark"]
            )
            vl.pack(anchor="w", pady=(3, py_bot[1]))
            self.val_labels.append(vl)

        # Right Card: Current session (border removed in dark mode)
        self.sess_card = tk.Frame(
            self.cards_row,
            bg=card_bg,
            padx=28,
            pady=24,
            highlightbackground=border_col,
            highlightthickness=border_thick
        )
        self.sess_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.lbl_sess_title = tk.Label(
            self.sess_card,
            text="Current session",
            font=("Segoe UI", 12, "bold"),
            bg=card_bg,
            fg=c["text_dark"]
        )
        self.lbl_sess_title.pack(anchor="w", pady=(0, 14))

        sess_fields = [
            ("STARTED", started_str, 14),
            ("STATUS", "Active", 4),
        ]

        for lbl_txt, val_txt, bot_pad in sess_fields:
            s_cell = tk.Frame(self.sess_card, bg=card_bg)
            s_cell.pack(fill="x")
            self.cells.append(s_cell)

            d = tk.Frame(s_cell, bg=divider_col, height=1)
            d.pack(fill="x", pady=(0, 12))
            self.dividers.append(d)

            ml = tk.Label(
                s_cell,
                text=lbl_txt,
                font=("Segoe UI", 8, "bold"),
                bg=card_bg,
                fg=c["text_muted"]
            )
            ml.pack(anchor="w")
            self.muted_labels.append(ml)

            vl = tk.Label(
                s_cell,
                text=val_txt,
                font=("Segoe UI", 10, "bold"),
                bg=card_bg,
                fg=c["text_dark"]
            )
            vl.pack(anchor="w", pady=(3, bot_pad))
            self.val_labels.append(vl)

    def apply_theme(self):
        """Seamless live theme update: removes border in dark mode."""
        if getattr(self, "_motion_bg", None) is not None:
            self._motion_bg.apply_theme()
        is_dark = config.get_theme() == "dark" if hasattr(config, "get_theme") else False
        c = config.COLORS
        page_bg = c["background"]
        card_bg = c["surface"]
        border_thick = 0 if is_dark else 1
        border_col = c["surface"] if is_dark else "#e6ebf1"
        divider_col = "#1e3350" if is_dark else "#eef2f6"

        self.config(bg=page_bg)
        self.lbl_title.config(bg=page_bg, fg=c["text_dark"])
        self.cards_row.config(bg=page_bg)

        for card in [self.acct_card, self.sess_card]:
            card.config(
                bg=card_bg,
                highlightthickness=border_thick,
                highlightbackground=border_col
            )

        self.lbl_acct_title.config(bg=card_bg, fg=c["text_dark"])
        self.lbl_sess_title.config(bg=card_bg, fg=c["text_dark"])

        self.acct_grid.config(bg=card_bg)

        for cell in self.cells:
            cell.config(bg=card_bg)
        for div in self.dividers:
            div.config(bg=divider_col)
        for ml in self.muted_labels:
            ml.config(bg=card_bg, fg=c["text_muted"])
        for vl in self.val_labels:
            vl.config(bg=card_bg, fg=c["text_dark"])

    def handle_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your session?"):
            auth.logout_user()
            self.show_login_screen()

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

