import os
import sys
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATASETS_DIR = BASE_DIR / "datasets"
MODELS_DIR = BASE_DIR / "ml" / "models"

# Ensure runtime directories exist
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration (WAMP Default: host=localhost, user=root, password='', port=3306)
DB_HOST = os.getenv("PHARMACY_DB_HOST", "localhost")
DB_USER = os.getenv("PHARMACY_DB_USER", "root")
DB_PASSWORD = os.getenv("PHARMACY_DB_PASSWORD", "")
DB_NAME = os.getenv("PHARMACY_DB_NAME", "pharmacy")
DB_PORT = int(os.getenv("PHARMACY_DB_PORT", 3306))

# Application Settings
APP_NAME = "PharmaCare"
APP_TITLE = "Pharmacy Store Business Management System with Knowledge Analysis"
APP_VERSION = "2.0.0"
CURRENCY = "$"

# Security & Session Settings
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 120

# Low stock & expiry alert thresholds
LOW_STOCK_THRESHOLD = 15
EXPIRY_WARN_DAYS = 90  # 3 months

# Role Definitions
ROLE_ADMIN = "admin"
ROLE_INVENTORY_CLERK = "inventory_clerk"
ROLE_SALES_PERSONNEL = "sales_personnel"
ROLE_INSTRUCTOR = "instructor"

ROLE_DISPLAY_NAMES = {
    ROLE_ADMIN: "Administrator",
    ROLE_INVENTORY_CLERK: "Inventory Clerk",
    ROLE_SALES_PERSONNEL: "Sales Personnel",
    ROLE_INSTRUCTOR: "Academic Instructor"
}

# Role-Based Permissions
ROLE_PERMISSIONS = {
    ROLE_INVENTORY_CLERK: [
        "dashboard_view",
        "inventory_view",
        "inventory_edit",
        "stock_movements",
        "suppliers_manage",
        "categories_manage",
        "profile_view"
    ],
    ROLE_SALES_PERSONNEL: [
        "dashboard_view",
        "sales_pos",
        "sales_history",
        "profile_view"
    ],
    ROLE_ADMIN: [
        "dashboard_view",
        "inventory_view",
        "sales_pos",
        "sales_history",
        "users_manage",
        "audit_logs",
        "analysis_input_predict",
        "profile_view"
    ],
    ROLE_INSTRUCTOR: [
        "dashboard_view",
        "inventory_view",
        "inventory_edit",
        "sales_pos",
        "sales_history",
        "users_manage",
        "audit_logs",
        "analysis_input_predict",
        "analysis_instructor_full",
        "profile_view"
    ]
}

# Modern UI Color Palettes (Light & Dark Themes)
THEMES = {
    "light": {
        "primary": "#0f172a",        # Deep Navy / Slate 900
        "primary_light": "#1e293b",  # Slate 800
        "secondary": "#0d9488",      # Modern Teal
        "secondary_dark": "#0f766e", # Deep Teal
        "accent": "#2563eb",         # Royal Blue
        "accent_hover": "#1d4ed8",
        "background": "#f8fafc",     # Light Slate Canvas
        "surface": "#ffffff",        # White Card Surface
        "surface_alt": "#f1f5f9",    # Soft Card Surface
        "border": "#e2e8f0",         # Muted Border
        "text_dark": "#0f172a",      # Crisp Charcoal Text
        "text_muted": "#64748b",     # Slate Muted Text
        "text_subtle": "#94a3b8",    # Subtle Caption Text
        "text_light": "#ffffff",     # White Text
        "success": "#16a34a",        # Green
        "warning": "#d97706",        # Amber Warning
        "danger": "#dc2626",         # Crimson Danger
        "info": "#0284c7",           # Sky Info
        "lime": "#a3e635",
        "lime_text": "#071d32",
        "chart_grid": "#f1f5f9",
        "pill_track": "#e2e8f0",
        "expired_fg": "#991b1b",
        "expired_bg": "#fee2e2",
        "tile_trend_bg": "#e6f7f4",
        "tile_card_bg": "#eff6ff",
        "tile_box_bg": "#f1f5f9",
        "tile_alert_bg": "#fee2e2",
        "tile_clock_bg": "#fef3c7",
        "tile_star_bg": "#e0f2fe",
        "login_panel_r": "#ffffff",
        "login_field_bg": "#f8fafc",
        "login_field_border": "#e2e8f0",
        "login_pill_hover": "#f8fafc",
        "login_pill_border_hover": "#cbd5e1",
        "login_divider": "#e2e8f0",
        # Dedicated POS screen palette (matching prompt specifications)
        "pos_bg": "#f4f6f8",
        "pos_card": "#ffffff",
        "pos_border": "#e1e7ee",
        "pos_text": "#0f1b2d",
        "pos_muted": "#56667b",
        "pos_chip": "#eef2f6",
        "pos_input": "#f8fafc",
        "pos_teal": "#0f766e",
        "pos_teal_text": "#ffffff",
        "pos_lime": "#a3e635",
        "pos_lime_text": "#0c1f33",
        "pos_badge_green_bg": "#e0f4f1",
        "pos_badge_green_fg": "#0f766e",
        "pos_badge_warn_bg": "#fef3c7",
        "pos_badge_warn_fg": "#92400e",
        "pos_badge_danger_bg": "#fee2e2",
        "pos_badge_danger_fg": "#b91c1c",
        "pos_blue": "#1d4ed8",
        "pos_chip_active": "#0f1b2d",
        "pos_totals_bg": "#f8fafc",
        "pos_stepper_bg": "#ffffff",
        "pos_stepper_border": "#e1e7ee",
        "pos_divider": "#e1e7ee",
    },
    "dark": {
        "primary": "#071d32",        # Deep Navy Sidebar
        "primary_light": "#0c263e",  # Elevated Navy
        "secondary": "#14b8a6",      # Bright Teal for Dark Mode
        "secondary_dark": "#0d9488", # Deep Teal
        "accent": "#3b82f6",         # Luminous Blue
        "accent_hover": "#2563eb",
        "background": "#0b1523",     # Deep Slate-Navy Canvas
        "surface": "#111f33",        # Dark Card Surface
        "surface_alt": "#182942",    # Elevated Input / Header Surface
        "border": "#1e3350",         # Subtle Dark Border
        "text_dark": "#f1f5f9",      # Crisp Light Primary Text
        "text_muted": "#94a3b8",     # Slate Muted Text
        "text_subtle": "#64748b",    # Subtle Caption Text
        "text_light": "#ffffff",     # White Text
        "success": "#22c55e",        # Green
        "warning": "#f59e0b",        # Amber Warning
        "danger": "#ef4444",         # Red Danger
        "info": "#38bdf8",           # Sky Info
        "lime": "#a3e635",
        "lime_text": "#071d32",
        "chart_grid": "#1e293b",
        "pill_track": "#1e3350",
        "expired_fg": "#fca5a5",
        "expired_bg": "#450a0a",
        "tile_trend_bg": "#0f2f35",
        "tile_card_bg": "#122645",
        "tile_box_bg": "#1a2a3f",
        "tile_alert_bg": "#3b1822",
        "tile_clock_bg": "#382811",
        "tile_star_bg": "#0e2c44",
        "login_panel_r": "#0f1c2e",
        "login_field_bg": "#182942",
        "login_field_border": "#1e3350",
        "login_pill_hover": "#1f3352",
        "login_pill_border_hover": "#334e75",
        "login_divider": "#1e3350",
        # Dedicated POS screen palette (matching prompt specifications)
        "pos_bg": "#0b1220",
        "pos_card": "#111a2b",
        "pos_border": "#24324a",
        "pos_text": "#e6edf6",
        "pos_muted": "#93a4bc",
        "pos_chip": "#172238",
        "pos_input": "#0f1829",
        "pos_teal": "#14b8a6",
        "pos_teal_text": "#04201d",
        "pos_lime": "#a3e635",
        "pos_lime_text": "#0c1f33",
        "pos_badge_green_bg": "#0d2d30",
        "pos_badge_green_fg": "#5eead4",
        "pos_badge_warn_bg": "#33250d",
        "pos_badge_warn_fg": "#fbbf24",
        "pos_badge_danger_bg": "#3f1515",
        "pos_badge_danger_fg": "#f87171",
        "pos_blue": "#60a5fa",
        "pos_chip_active": "#24324a",
        "pos_totals_bg": "#141f33",
        "pos_stepper_bg": "#172238",
        "pos_stepper_border": "#24324a",
        "pos_divider": "#1e2c44",
    },
}

CURRENT_THEME = "light"
COLORS = dict(THEMES[CURRENT_THEME])


def get_theme() -> str:
    return CURRENT_THEME


def set_theme(mode: str) -> str:
    """Switches active theme in-place so all modules reading COLORS update seamlessly."""
    global CURRENT_THEME
    if mode not in THEMES:
        mode = "light"
    CURRENT_THEME = mode
    COLORS.clear()
    COLORS.update(THEMES[mode])
    return CURRENT_THEME


def toggle_theme() -> str:
    """Toggles between light and dark themes and returns the new active mode."""
    return set_theme("dark" if CURRENT_THEME == "light" else "light")

# Fonts Config
FONTS = {
    "h1": ("Segoe UI", 20, "bold"),
    "h2": ("Segoe UI", 16, "bold"),
    "h3": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10)
}

