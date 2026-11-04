import os
import sys
import tempfile
from pathlib import Path

# Set MPL cache directory to temp to prevent permission errors
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import tkinter as tk
from tkinter import ttk, messagebox

import config
import db
import auth
from screens.login import LoginScreen
from screens.dashboard import DashboardScreen

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        
        # Start maximized in full-screen windowed mode with standard window manager controls
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-fullscreen", True)

        self.bind("<Escape>", self.safeguard_fullscreen)
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

    def safeguard_fullscreen(self, event=None):
        """Prevent accidental exiting of fullscreen mode while providing safe confirmation."""
        ans = messagebox.askyesno(
            "Full-screen Safeguard", 
            "The system is designed to run in Full-Screen mode for optimal workflow.\n\nDo you want to toggle windowed mode?"
        )
        if ans:
            try:
                if self.state() == "zoomed":
                    self.state("normal")
                    self.geometry("1200x800")
                else:
                    self.state("zoomed")
            except Exception:
                curr = self.attributes("-fullscreen")
                self.attributes("-fullscreen", not curr)

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

    def build_app_shell(self):
        self.clear_view()

        # Shell frame containing sidebar and content area
        shell = tk.Frame(self.main_container, bg=config.COLORS["background"])
        shell.pack(fill="both", expand=True)

        # Sidebar (Left)
        self.sidebar = tk.Frame(shell, bg=config.COLORS["primary"], width=260, padx=15, pady=20)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand Logo / App Title
        brand_frame = tk.Frame(self.sidebar, bg=config.COLORS["primary"])
        brand_frame.pack(fill="x", pady=(0, 25))

        lbl_logo = tk.Label(
            brand_frame, 
            text="⚕ PharmaCare", 
            font=("Segoe UI", 16, "bold"), 
            bg=config.COLORS["primary"], 
            fg="white"
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = tk.Label(
            brand_frame, 
            text="Pharmacy & Knowledge Studio", 
            font=("Segoe UI", 8), 
            bg=config.COLORS["primary"], 
            fg=config.COLORS["text_muted"]
        )
        lbl_sub.pack(anchor="w")

        # User Info Chip
        user = auth.SessionManager.get_user() or {}
        role = user.get("role", config.ROLE_ADMIN)
        role_label = config.ROLE_DISPLAY_NAMES.get(role, role)

        user_chip = tk.Frame(self.sidebar, bg=config.COLORS["primary_light"], padx=10, pady=10)
        user_chip.pack(fill="x", pady=(0, 20))

        tk.Label(
            user_chip, 
            text=user.get("full_name", "User"), 
            font=config.FONTS["body_bold"], 
            bg=config.COLORS["primary_light"], 
            fg="white"
        ).pack(anchor="w")

        role_tag = tk.Label(
            user_chip, 
            text=f"● {role_label}", 
            font=("Segoe UI", 8, "bold"), 
            bg=config.COLORS["primary_light"], 
            fg=config.COLORS["secondary"]
        )
        role_tag.pack(anchor="w", pady=(2, 0))

        # Navigation Menu Items Based on Role
        self.menu_buttons = {}
        self.build_navigation_items(role)

        # Bottom Logout & Fullscreen actions
        bottom_box = tk.Frame(self.sidebar, bg=config.COLORS["primary"])
        bottom_box.pack(side="bottom", fill="x")

        btn_fs = tk.Button(
            bottom_box,
            text="⛶ Toggle Full-screen",
            font=config.FONTS["small"],
            bg=config.COLORS["primary_light"],
            fg=config.COLORS["text_muted"],
            relief="flat",
            cursor="hand2",
            pady=6,
            command=self.safeguard_fullscreen
        )
        btn_fs.pack(fill="x", pady=(0, 8))

        btn_logout = tk.Button(
            bottom_box,
            text="⏻ Logout",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["danger"],
            fg="white",
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self.handle_logout
        )
        btn_logout.pack(fill="x")

        # Right Container (Top Bar + Content Area)
        right_container = tk.Frame(shell, bg=config.COLORS["background"])
        right_container.pack(side="right", fill="both", expand=True)

        # Global Top Bar with System Status & Window Controls (Minimize, Maximize, Close)
        app_topbar = tk.Frame(right_container, bg=config.COLORS["surface"], height=38, highlightbackground=config.COLORS["border"], highlightthickness=1)
        app_topbar.pack(fill="x", side="top")

        # Left status
        db_badge = tk.Frame(app_topbar, bg=config.COLORS["surface"], padx=15, pady=6)
        db_badge.pack(side="left")
        tk.Label(
            db_badge,
            text=f"● Database: Connected ({config.DB_NAME})  |  User: {user.get('username')} ({role_label})",
            font=("Segoe UI", 9),
            bg=config.COLORS["surface"],
            fg=config.COLORS["secondary"]
        ).pack(side="left")

        # Content Area
        self.content_area = tk.Frame(right_container, bg=config.COLORS["background"])
        self.content_area.pack(fill="both", expand=True)

    def build_navigation_items(self, role):
        """Constructs role-tailored sidebar menu items."""
        # Common to all roles
        items = [
            ("dashboard", "📊  Dashboard")
        ]

        # Inventory Management
        if role in [config.ROLE_INVENTORY_CLERK, config.ROLE_INSTRUCTOR]:
            items.append(("inventory", "📦  Inventory Management"))
        elif role == config.ROLE_ADMIN:
            items.append(("inventory", "📦  Inventory Catalog"))

        # Sales Module
        if role in [config.ROLE_SALES_PERSONNEL, config.ROLE_INSTRUCTOR]:
            items.append(("sales", "💳  Point of Sale (POS)"))
        elif role == config.ROLE_ADMIN:
            items.append(("sales", "💳  Sales History"))

        # Users Management
        if role in [config.ROLE_ADMIN, config.ROLE_INSTRUCTOR]:
            items.append(("users", "👥  User Management & Logs"))

        # Knowledge Analysis
        if role == config.ROLE_ADMIN:
            items.append(("analysis", "🧠  Knowledge Analysis (Predict)"))
        elif role == config.ROLE_INSTRUCTOR:
            items.append(("analysis", "🧠  Knowledge Analysis Studio"))

        # Add Profile
        items.append(("profile", "👤  My Profile"))

        for key, label in items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=config.FONTS["body_bold"],
                bg=config.COLORS["primary"],
                fg="#cbd5e1",
                activebackground=config.COLORS["secondary"],
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                anchor="w",
                padx=14,
                pady=10,
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=2)
            self.menu_buttons[key] = btn

    def set_active_menu(self, active_key):
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.config(bg=config.COLORS["secondary"], fg="white")
            else:
                btn.config(bg=config.COLORS["primary"], fg="#cbd5e1")

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

