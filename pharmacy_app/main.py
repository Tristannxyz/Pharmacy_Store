import os
import sys
import tempfile
from pathlib import Path

# Set MPL cache directory to temp to prevent permission errors
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

import config
import db
import auth
from screens.login import LoginScreen
from screens.dashboard import DashboardScreen

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_SIDEBAR_BG = "#071d32"
_USER_CHIP_BG = "#0c263e"
_USER_CHIP_BORDER = "#143657"
_LIME = "#a3e635"
_NAV_INACTIVE_FG = "#8ea3b8"
_NAV_HOVER_BG = "#0d2742"

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

        # Active components
        self.sidebar = None
        self.content_area = None
        self.current_screen = None

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
        style = ttk.Style(self)
        style.theme_use("clam")

        # Treeview styling for data tables
        style.configure(
            "Treeview",
            background=config.COLORS["surface"],
            foreground=config.COLORS["text_dark"],
            rowheight=28,
            fieldbackground=config.COLORS["surface"],
            font=config.FONTS["body"],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=config.COLORS["surface_alt"],
            foreground=config.COLORS["text_dark"],
            font=config.FONTS["body_bold"],
            relief="flat",
            padding=(6, 6)
        )
        style.map("Treeview", background=[("selected", config.COLORS["accent"])], foreground=[("selected", "white")])

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
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.sidebar = None
        self.content_area = None
        self.current_screen = None

    def show_login_screen(self):
        self.clear_view()
        login_view = LoginScreen(self.main_container, on_login_success=self.on_login_success)
        login_view.pack(fill="both", expand=True)

    def on_login_success(self, user_data):
        self.build_app_shell()
        self.navigate_to("dashboard")

    def _make_circle_avatar(self, initials, size=36, bg_color=_LIME, text_color="#071d32"):
        """Generates supersampled circular avatar image with user initials."""
        scale = 3
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([0, 0, s - 1, s - 1], fill=bg_color)

        font_path = _ASSETS_DIR / "fonts" / "SpaceGrotesk-Bold.ttf"
        if not font_path.exists():
            font_path = _ASSETS_DIR / "fonts" / "Inter.ttf"

        try:
            font = ImageFont.truetype(str(font_path), int(13 * scale))
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

        # ── User Profile Chip ─────────────────────────────────────────────────
        user = auth.SessionManager.get_user() or {}
        role = user.get("role", config.ROLE_ADMIN)
        role_label = config.ROLE_DISPLAY_NAMES.get(role, role)

        user_chip = tk.Frame(
            self.sidebar,
            bg=_USER_CHIP_BG,
            padx=12,
            pady=10,
            highlightbackground=_USER_CHIP_BORDER,
            highlightthickness=1
        )
        user_chip.pack(fill="x", pady=(0, 22))

        # Determine user initials
        full_name = user.get("full_name", "System Administrator")
        words = full_name.split()
        initials = "".join(w[0].upper() for w in words[:2]) if words else "SA"

        avatar_photo = self._make_circle_avatar(initials, size=36)
        tk.Label(user_chip, image=avatar_photo, bg=_USER_CHIP_BG, bd=0).pack(side="left", padx=(0, 10))

        user_text_box = tk.Frame(user_chip, bg=_USER_CHIP_BG)
        user_text_box.pack(side="left", fill="x", expand=True)

        tk.Label(
            user_text_box,
            text=full_name,
            font=("Segoe UI", 9, "bold"),
            bg=_USER_CHIP_BG,
            fg="#ffffff"
        ).pack(anchor="w")

        tk.Label(
            user_text_box,
            text=role_label,
            font=("Segoe UI", 8),
            bg=_USER_CHIP_BG,
            fg=_NAV_INACTIVE_FG
        ).pack(anchor="w", pady=(1, 0))

        # ── Navigation Menu Items ─────────────────────────────────────────────
        self.menu_buttons = {}
        self.active_key = None
        self.build_navigation_items(role)

        # ── Bottom Logout Action ──────────────────────────────────────────────
        bottom_box = tk.Frame(self.sidebar, bg=_SIDEBAR_BG)
        bottom_box.pack(side="bottom", fill="x")

        btn_logout = tk.Button(
            bottom_box,
            text="⏻  Sign Out",
            font=("Segoe UI", 9, "bold"),
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

        # ── Right Content Area ────────────────────────────────────────────────
        self.content_area = tk.Frame(shell, bg=config.COLORS["background"])
        self.content_area.pack(side="right", fill="both", expand=True)

    def build_navigation_items(self, role):
        """Constructs role-tailored sidebar menu items with sleek pill highlights."""
        items = [
            ("dashboard", "⊞   Dashboard")
        ]

        if role in [config.ROLE_INVENTORY_CLERK, config.ROLE_INSTRUCTOR]:
            items.append(("inventory", "◫   Inventory Management"))
        elif role == config.ROLE_ADMIN:
            items.append(("inventory", "◫   Inventory Catalog"))

        if role in [config.ROLE_SALES_PERSONNEL, config.ROLE_INSTRUCTOR]:
            items.append(("sales", "💳   Point of Sale (POS)"))
        elif role == config.ROLE_ADMIN:
            items.append(("sales", "💳   Sales History"))

        if role in [config.ROLE_ADMIN, config.ROLE_INSTRUCTOR]:
            items.append(("users", "👥   User Management & Logs"))

        if role == config.ROLE_ADMIN:
            items.append(("analysis", "📈   Knowledge Analysis (Predict)"))
        elif role == config.ROLE_INSTRUCTOR:
            items.append(("analysis", "📈   Knowledge Analysis Studio"))

        items.append(("profile", "👤   My Profile"))

        for key, label in items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=("Segoe UI", 9, "bold"),
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
                    fg="#071d32",
                    font=("Segoe UI", 9, "bold")
                )
            else:
                btn.config(
                    bg=_SIDEBAR_BG,
                    fg=_NAV_INACTIVE_FG,
                    font=("Segoe UI", 9, "bold")
                )

    def navigate_to(self, screen_name):
        """Routes and displays the requested screen inside content_area with RBAC enforcement."""
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
            self.current_screen = self.create_profile_view(self.content_area)

        if self.current_screen:
            self.current_screen.pack(fill="both", expand=True)

    def create_profile_view(self, parent):
        user = auth.SessionManager.get_user() or {}
        frame = tk.Frame(parent, bg=config.COLORS["background"], padx=30, pady=25)

        card = tk.Frame(frame, bg=config.COLORS["surface"], padx=30, pady=25, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="x", anchor="n")

        tk.Label(card, text="👤 User Profile", font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 15))

        details = [
            ("Full Name:", user.get("full_name", "N/A")),
            ("Username:", user.get("username", "N/A")),
            ("Email Address:", user.get("email", "N/A")),
            ("Assigned Role:", config.ROLE_DISPLAY_NAMES.get(user.get("role"), user.get("role"))),
            ("Active Session Started:", str(user.get("last_login", "Just now")))
        ]

        for lbl, val in details:
            row = tk.Frame(card, bg=config.COLORS["surface"], pady=6)
            row.pack(fill="x")
            tk.Label(row, text=lbl, font=config.FONTS["body_bold"], width=24, anchor="w", bg=config.COLORS["surface"], fg=config.COLORS["text_muted"]).pack(side="left")
            tk.Label(row, text=val, font=config.FONTS["body"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(side="left")

        return frame

    def handle_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out of your session?"):
            auth.logout_user()
            self.show_login_screen()

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

