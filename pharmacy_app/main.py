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
from theme import ThemeAnimator, collect_transition_targets
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

        # Style TTK widgets
        self.setup_ttk_styles()

        # Master layout container
        self.main_container = tk.Frame(self, bg=config.COLORS["background"])
        self.main_container.pack(fill="both", expand=True)

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

        self._available_families = set()
        try:
            self._available_families = set(tkfont.families())
        except Exception:
            pass

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
        style.configure(
            "Treeview",
            background=c["surface"],
            foreground=c["text_dark"],
            rowheight=28,
            fieldbackground=c["surface"],
            font=config.FONTS["body"],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=c["surface_alt"],
            foreground=c["text_dark"],
            font=config.FONTS["body_bold"],
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
        )

        # Notebook & Tab styling
        style.configure("TNotebook", background=c["background"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=c["surface_alt"],
            foreground=c["text_muted"],
            padding=(12, 6),
            font=config.FONTS["body_bold"],
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
                "sign_out": "⏻  Sign Out",
                "nav_dashboard": "⊞   Dashboard",
                "nav_inventory": "◫   Inventory Management",
                "nav_sales": "💳   Point of Sale (POS)",
                "nav_users": "👥   User Management & Logs",
                "nav_analysis": "📈   Knowledge Analysis Studio",
                "nav_profile": "👤   My Profile",
            },
            "Filipino": {
                "settings": "Settings",
                "appearance": "Hitsura",
                "light_mode": "Light mode",
                "dark_mode": "Dark mode",
                "language": "Wika",
                "font": "Font",
                "text_size": "Laki ng teksto",
                "sign_out": "⏻  Mag-sign Out",
                "nav_dashboard": "⊞   Dashboard",
                "nav_inventory": "◫   Pamamahala ng Imbentaryo",
                "nav_sales": "💳   Point of Sale (POS)",
                "nav_users": "👥   Mga User at Logs",
                "nav_analysis": "📈   Knowledge Analysis Studio",
                "nav_profile": "👤   Aking Profile",
            },
            "Spanish": {
                "settings": "Ajustes",
                "appearance": "Apariencia",
                "light_mode": "Light mode",
                "dark_mode": "Dark mode",
                "language": "Idioma",
                "font": "Fuente",
                "text_size": "Tamaño de texto",
                "sign_out": "⏻  Cerrar sesión",
                "nav_dashboard": "⊞   Panel Principal",
                "nav_inventory": "◫   Gestión de Inventario",
                "nav_sales": "💳   Punto de Venta (POS)",
                "nav_users": "👥   Usuarios y Registros",
                "nav_analysis": "📈   Estudio de Analítica",
                "nav_profile": "👤   Mi Perfil",
            },
        }
        tmap = translations.get(lang, translations["English"])
        return tmap.get(key, translations["English"].get(key, key))

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

        tk.Label(
            brand_text_box,
            text="PharmaCare",
            font=("Segoe UI", 16, "bold"),
            bg=_SIDEBAR_BG,
            fg="#ffffff"
        ).pack(anchor="w")

        tk.Label(
            brand_text_box,
            text="Pharmacy & Knowledge Studio",
            font=("Segoe UI", 8),
            bg=_SIDEBAR_BG,
            fg=_NAV_INACTIVE_FG
        ).pack(anchor="w")

        # ── Fetch User & Role ─────────────────────────────────────────────────
        user = auth.SessionManager.get_user() or {}
        role = user.get("role", config.ROLE_ADMIN)
        role_label = config.ROLE_DISPLAY_NAMES.get(role, role)

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
            font=("Segoe UI", 9, "bold"),
            bg=_USER_CHIP_BG,
            fg="#ffffff",
            cursor="hand2"
        )
        lbl_uname.pack(anchor="w")

        lbl_urole = tk.Label(
            user_text_box,
            text=role_label,
            font=("Segoe UI", 8),
            bg=_USER_CHIP_BG,
            fg=_NAV_INACTIVE_FG,
            cursor="hand2"
        )
        lbl_urole.pack(anchor="w", pady=(1, 0))

        # Clicking the user profile chip opens My Profile
        for w in (user_chip, lbl_avatar, user_text_box, lbl_uname, lbl_urole):
            w.bind("<Button-1>", lambda e: self.navigate_to("profile"))

        btn_settings = tk.Button(
            bottom_box,
            text=f"⚙  {self._ui_t('settings')}",
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

    def _apply_global_typography(self):
        """Updates config.FONTS, sidebar labels, and active screen fonts in-place."""
        fam = self._resolve_ui_font_family()
        prefs = getattr(config, "UI_PREFS", {})
        sz = prefs.get("text_size", "M")
        off = {"S": -1, "M": 0, "L": 2, "XL": 3}.get(sz, 0)

        config.FONTS["h1"] = (fam, 20 + off, "bold")
        config.FONTS["h2"] = (fam, 16 + off, "bold")
        config.FONTS["h3"] = (fam, 13 + off, "bold")
        config.FONTS["body"] = (fam, 10 + off)
        config.FONTS["body_bold"] = (fam, 10 + off, "bold")
        config.FONTS["small"] = (fam, 9 + off)
        self.setup_ttk_styles()

        if self.btn_settings is not None and self.btn_settings.winfo_exists():
            self.btn_settings.configure(text=f"⚙  {self._ui_t('settings')}", font=self._ui_font(9, "bold"))
        if self.btn_logout is not None and self.btn_logout.winfo_exists():
            self.btn_logout.configure(text=self._ui_t("sign_out"), font=self._ui_font(9, "bold"))

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
                btn.configure(text=self._ui_t(nav_keys.get(k, k)), font=self._ui_font(9, "bold"))

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

    def build_navigation_items(self, role):
        """Constructs role-tailored sidebar menu items with sleek pill highlights."""
        items = [
            ("dashboard", self._ui_t("nav_dashboard")),
            ("inventory", self._ui_t("nav_inventory")),
            ("sales", self._ui_t("nav_sales")),
            ("users", self._ui_t("nav_users")),
            ("analysis", self._ui_t("nav_analysis")),
            ("profile", self._ui_t("nav_profile")),
        ]

        for key, label in items:
            btn = tk.Button(
                self.sidebar,
                text=label,
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
                    b.config(bg=_NAV_HOVER_BG, fg="#ffffff")
            def on_leave(e, b=btn, k=key):
                if self.active_key != k:
                    b.config(bg=_SIDEBAR_BG, fg=_NAV_INACTIVE_FG)

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
                    font=self._ui_font(9, "bold")
                )
            else:
                btn.config(
                    bg=_SIDEBAR_BG,
                    fg=_NAV_INACTIVE_FG,
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
        email = user.get("email") or "admin@pharmacare.local"
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

