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

# Modern UI Color Palette
COLORS = {
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
    "text_light": "#ffffff",     # White Text
    "success": "#16a34a",        # Green
    "warning": "#d97706",        # Amber Warning
    "danger": "#dc2626",         # Crimson Danger
    "info": "#0284c7"            # Sky Info
}

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

