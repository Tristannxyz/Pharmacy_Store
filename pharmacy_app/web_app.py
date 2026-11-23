import os
import re
import sys
import random
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal

import pandas as pd
from flask import Flask, jsonify, request, render_template, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
import db
import auth
from ml.predict import ModelPredictor
from ml import train

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RestInPillsWeb")

WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
)
app.secret_key = os.getenv("PHARMACY_WEB_SECRET", "restinpills-pharmacy-secret-key-2026")


# ─────────────────────────────────────────────────────────────────────────────
# Transparent MySQL -> SQLite Fallback Mirror (When WAMP/MySQL is offline)
# ─────────────────────────────────────────────────────────────────────────────
_SQLITE_PATH = config.DATABASE_DIR / "pharmacy_web_mirror.sqlite3"
_USING_SQLITE_FALLBACK = False
_ORIG_EXECUTE_QUERY = db.execute_query
_ORIG_EXECUTE_MANY = db.execute_many


def _translate_mysql_to_sqlite(query: str) -> str:
    q = query.strip()
    q = q.replace("%s", "?")
    q = re.sub(r"\bTRUE\b", "1", q, flags=re.IGNORECASE)
    q = re.sub(r"\bFALSE\b", "0", q, flags=re.IGNORECASE)
    q = re.sub(
        r"DATE_SUB\s*\(\s*NOW\s*\(\s*\)\s*,\s*INTERVAL\s+(\d+)\s+DAY\s*\)",
        r"datetime('now', 'localtime', '-\1 days')",
        q,
        flags=re.IGNORECASE,
    )
    q = re.sub(r"\bNOW\s*\(\s*\)", "datetime('now', 'localtime')", q, flags=re.IGNORECASE)
    q = re.sub(r"MONTH\s*\(\s*([a-zA-Z0-9_.]+)\s*\)", r"CAST(strftime('%m', \1) AS INTEGER)", q, flags=re.IGNORECASE)
    q = re.sub(r"DAYOFWEEK\s*\(\s*([a-zA-Z0-9_.]+)\s*\)", r"(CAST(strftime('%w', \1) AS INTEGER) + 1)", q, flags=re.IGNORECASE)
    return q


def _normalize_param(p):
    if isinstance(p, (datetime, date)):
        return p.strftime("%Y-%m-%d %H:%M:%S") if isinstance(p, datetime) else p.strftime("%Y-%m-%d")
    if isinstance(p, Decimal):
        return float(p)
    return p


def _hydrate_row(row_dict: dict) -> dict:
    if not row_dict:
        return row_dict
    out = dict(row_dict)
    for k, v in list(out.items()):
        if isinstance(v, str):
            if k in ("expiry_date", "sale_day") and len(v) >= 10:
                try:
                    out[k] = datetime.strptime(v[:10], "%Y-%m-%d").date()
                except Exception:
                    pass
            elif k in ("created_at", "updated_at", "last_login", "locked_until") and len(v) >= 10:
                try:
                    if len(v) >= 19:
                        out[k] = datetime.strptime(v[:19], "%Y-%m-%d %H:%M:%S")
                    else:
                        out[k] = datetime.strptime(v[:10], "%Y-%m-%d")
                except Exception:
                    pass
        elif k == "is_active" and isinstance(v, int):
            out[k] = bool(v)
    return out


def _sqlite_execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    sql = _translate_mysql_to_sqlite(query)
    norm_params = tuple(_normalize_param(p) for p in (params or ()))
    conn = sqlite3.connect(str(_SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(sql, norm_params)
        if commit:
            conn.commit()
            return cur.lastrowid or cur.rowcount
        if fetchone:
            row = cur.fetchone()
            return _hydrate_row(dict(row)) if row else None
        if fetchall:
            rows = cur.fetchall()
            return [_hydrate_row(dict(r)) for r in rows]
        return None
    finally:
        cur.close()
        conn.close()


def _sqlite_execute_many(query, seq_of_params, commit=True):
    sql = _translate_mysql_to_sqlite(query)
    norm_seq = [tuple(_normalize_param(p) for p in row) for row in seq_of_params]
    conn = sqlite3.connect(str(_SQLITE_PATH))
    cur = conn.cursor()
    try:
        cur.executemany(sql, norm_seq)
        if commit:
            conn.commit()
            return cur.rowcount
        return None
    finally:
        cur.close()
        conn.close()


def _init_sqlite_mirror():
    global _USING_SQLITE_FALLBACK
    _USING_SQLITE_FALLBACK = True
    config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_SQLITE_PATH))
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'sales_personnel',
            is_active INTEGER NOT NULL DEFAULT 1,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT NULL,
            last_login TEXT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            supplier_id INTEGER,
            cost_price REAL NOT NULL DEFAULT 0.00,
            selling_price REAL NOT NULL DEFAULT 0.00,
            stock_qty INTEGER NOT NULL DEFAULT 0,
            reorder_level INTEGER NOT NULL DEFAULT 15,
            expiry_date TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'piece',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            subtotal REAL NOT NULL DEFAULT 0.00,
            discount_percent REAL NOT NULL DEFAULT 0.00,
            discount_amount REAL NOT NULL DEFAULT 0.00,
            total_amount REAL NOT NULL DEFAULT 0.00,
            payment_method TEXT NOT NULL DEFAULT 'CASH',
            amount_paid REAL NOT NULL DEFAULT 0.00,
            change_amount REAL NOT NULL DEFAULT 0.00,
            customer_name TEXT DEFAULT 'Walk-in Customer',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS sales_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL,
            line_total REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reference_note TEXT,
            user_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT DEFAULT '127.0.0.1',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()

    db.execute_query = _sqlite_execute_query
    db.execute_many = _sqlite_execute_many

    db.seed_users()
    db.seed_categories()
    db.seed_suppliers()
    db.seed_products()
    db.seed_sample_sales()
    logger.info("Initialized local SQLite mirror with full RestInPills schema & 55 seeded products.")


def ensure_database_ready():
    try:
        db.init_database()
        logger.info("Connected to MySQL database '%s' on %s:%s.", config.DB_NAME, config.DB_HOST, config.DB_PORT)
    except Exception as err:
        logger.warning("MySQL server unreachable (%s). Activating seamless SQLite mirror...", err)
        _init_sqlite_mirror()


# Category price generator matching screens/inventory.py
CATEGORY_PRICE_RANGES = {
    "Analgesics & Antipyretics":      (0.20, 1.50, 2.5, 3.2),
    "Antibiotics & Antivirals":      (0.45, 2.20, 2.5, 3.1),
    "Antihistamines & Allergy":      (0.25, 2.50, 2.5, 3.2),
    "Cardiovascular & Hypertension": (0.25, 1.20, 2.6, 3.2),
    "Vitamins & Supplements":        (0.15, 0.85, 2.8, 3.5),
    "Gastrointestinal & Digestive":  (0.20, 1.30, 2.6, 3.2),
    "Respiratory & Cough Care":      (0.40, 3.50, 2.5, 3.0),
    "Topical & First Aid":           (0.70, 3.00, 2.4, 2.9),
}


def generate_category_prices(cat_name, cat_id=None):
    price_range = CATEGORY_PRICE_RANGES.get(cat_name)
    if price_range is None:
        price_range = (0.50, 3.50, 2.4, 3.1)
    min_c, max_c, min_m, max_m = price_range
    raw_cost = random.uniform(min_c, max_c)
    cost = max(0.10, round(raw_cost * 20) / 20)
    markup = random.uniform(min_m, max_m)
    raw_sell = max(cost + 0.25, cost * markup)
    sell = max(cost + 0.25, round(raw_sell * 20) / 20)
    return f"{cost:.2f}", f"{sell:.2f}"


def _serialize_dt(val, fmt="%Y-%m-%d %H:%M"):
    if val is None:
        return None
    if hasattr(val, "strftime"):
        return val.strftime(fmt)
    return str(val)[:16]


def _serialize_date(val):
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    return str(val)[:10]


def _user_payload(user_dict):
    if not user_dict:
        return None
    role = user_dict.get("role", config.ROLE_ADMIN)
    perms = config.ROLE_PERMISSIONS.get(role, [])
    return {
        "id": user_dict.get("id"),
        "username": user_dict.get("username"),
        "full_name": user_dict.get("full_name"),
        "email": user_dict.get("email") or "admin@restinpills.local",
        "role": role,
        "role_display": config.ROLE_DISPLAY_NAMES.get(role, role),
        "permissions": perms,
        "last_login": _serialize_dt(user_dict.get("last_login"), "%Y-%m-%d · %H:%M")
        or datetime.now().strftime("%Y-%m-%d · %H:%M"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Web Pages & Static Asset Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(str(ASSETS_DIR), filename)


# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap, Preferences & Authentication API
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/bootstrap", methods=["GET"])
def api_bootstrap():
    user = auth.SessionManager.get_user()
    return jsonify({
        "app_name": config.APP_NAME,
        "app_title": config.APP_TITLE,
        "currency": config.CURRENCY,
        "db_name": config.DB_NAME,
        "expiry_warn_days": config.EXPIRY_WARN_DAYS,
        "low_stock_threshold": config.LOW_STOCK_THRESHOLD,
        "prefs": getattr(config, "UI_PREFS", {
            "theme": config.get_theme(),
            "language": "English",
            "font": "Inter",
            "text_size": "M",
        }),
        "role_display_names": config.ROLE_DISPLAY_NAMES,
        "role_permissions": config.ROLE_PERMISSIONS,
        "user": _user_payload(user),
    })


@app.route("/api/prefs", methods=["POST"])
def api_update_prefs():
    data = request.get_json(silent=True) or {}
    if "theme" in data and data["theme"] in ("light", "dark"):
        config.set_theme(data["theme"])
    if hasattr(config, "UI_PREFS"):
        for k in ("language", "font", "text_size"):
            if k in data and data[k]:
                config.UI_PREFS[k] = data[k]
    return jsonify({"ok": True, "prefs": config.UI_PREFS})


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    success, msg, user_data = auth.authenticate_user(username, password)
    if not success:
        return jsonify({"ok": False, "message": msg}), 401
    return jsonify({
        "ok": True,
        "message": msg,
        "user": _user_payload(user_data),
    })


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    auth.logout_user()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard API (Matches screens/dashboard.py)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    today_str = date.today().strftime("%Y-%m-%d")
    month_start_str = date.today().replace(day=1).strftime("%Y-%m-%d")
    expiry_limit = (date.today() + timedelta(days=config.EXPIRY_WARN_DAYS)).strftime("%Y-%m-%d")

    try:
        sales_today = db.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) AS total, COUNT(*) as cnt FROM sales WHERE DATE(created_at) = %s",
            (today_str,),
            fetchone=True,
        )
        monthly_sales = db.execute_query(
            "SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales WHERE DATE(created_at) >= %s",
            (month_start_str,),
            fetchone=True,
        )
        prod_stats = db.execute_query(
            "SELECT COUNT(*) AS total_prods, COALESCE(SUM(stock_qty * cost_price), 0) AS inventory_val FROM products WHERE is_active = TRUE",
            fetchone=True,
        )
        low_stock = db.execute_query(
            "SELECT COUNT(*) AS cnt FROM products WHERE is_active = TRUE AND stock_qty <= reorder_level",
            fetchone=True,
        )
        near_expiry = db.execute_query(
            "SELECT COUNT(*) AS cnt FROM products WHERE is_active = TRUE AND expiry_date <= %s",
            (expiry_limit,),
            fetchone=True,
        )
        top_prod = db.execute_query(
            """
            SELECT p.name, COALESCE(SUM(si.quantity), 0) as total_qty
            FROM sales_items si
            JOIN products p ON si.product_id = p.id
            GROUP BY p.id, p.name
            ORDER BY total_qty DESC
            LIMIT 1
            """,
            fetchone=True,
        )
        metrics = {
            "sales_today": float(sales_today["total"] if sales_today else 0.0),
            "sales_today_count": int(sales_today["cnt"] if sales_today else 0),
            "monthly_revenue": float(monthly_sales["total"] if monthly_sales else 0.0),
            "total_products": int(prod_stats["total_prods"] if prod_stats else 0),
            "inventory_value": float(prod_stats["inventory_val"] if prod_stats else 0.0),
            "low_stock_count": int(low_stock["cnt"] if low_stock else 0),
            "near_expiry_count": int(near_expiry["cnt"] if near_expiry else 0),
            "top_product_name": top_prod["name"] if top_prod else "N/A",
            "top_product_qty": int(top_prod["total_qty"] if top_prod else 0),
        }
    except Exception as e:
        logger.error("Dashboard metrics error: %s", e)
        metrics = {
            "sales_today": 0.0,
            "sales_today_count": 0,
            "monthly_revenue": 0.0,
            "total_products": 0,
            "inventory_value": 0.0,
            "low_stock_count": 0,
            "near_expiry_count": 0,
            "top_product_name": "N/A",
            "top_product_qty": 0,
        }

    # 1. 14-day sales revenue trend
    try:
        trend_rows = db.execute_query(
            """
            SELECT DATE(created_at) as sale_day, SUM(total_amount) as daily_rev
            FROM sales
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
            GROUP BY DATE(created_at)
            ORDER BY sale_day ASC
            """,
            fetchall=True,
        ) or []
    except Exception:
        trend_rows = []

    trend_14d = []
    for r in trend_rows:
        sd = r.get("sale_day")
        lbl = sd.strftime("%m/%d") if hasattr(sd, "strftime") else str(sd)[-5:].replace("-", "/")
        trend_14d.append({"date": lbl, "revenue": round(float(r.get("daily_rev") or 0.0), 2)})

    # 2. Top 5 products by quantity sold
    try:
        top_rows = db.execute_query(
            """
            SELECT p.name, COALESCE(SUM(si.quantity), 0) as total_qty
            FROM products p
            JOIN sales_items si ON si.product_id = p.id
            GROUP BY p.id, p.name
            ORDER BY total_qty DESC
            LIMIT 5
            """,
            fetchall=True,
        ) or []
    except Exception:
        top_rows = []

    if not top_rows:
        top_rows = [
            {"name": "Aspirin 81mg Low D", "total_qty": 52},
            {"name": "Paracetamol 120mg", "total_qty": 38},
            {"name": "Ibuprofen 400mg", "total_qty": 36},
            {"name": "Ibuprofen 200mg", "total_qty": 34},
            {"name": "Amoxicillin 500mg", "total_qty": 31},
        ]
    top_5_products = [
        {"name": r["name"][:19].rstrip() if len(r["name"]) > 20 else r["name"], "full_name": r["name"], "qty": int(r["total_qty"])}
        for r in top_rows
    ]

    # 3. Sales breakdown by category
    try:
        cat_rows = db.execute_query(
            """
            SELECT c.name, COALESCE(SUM(si.line_total), 0) as total_rev
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id
            LEFT JOIN sales_items si ON si.product_id = p.id
            GROUP BY c.id, c.name
            ORDER BY total_rev DESC
            LIMIT 3
            """,
            fetchall=True,
        ) or []
    except Exception:
        cat_rows = []

    total_cat_rev = sum(float(c.get("total_rev") or 0.0) for c in cat_rows)
    sales_by_category = []
    if total_cat_rev > 0 and cat_rows:
        for c in cat_rows:
            raw_name = c["name"]
            if "Analgesic" in raw_name:
                disp = "Analgesics"
            elif "Antibiotic" in raw_name:
                disp = "Antibiotics"
            elif "Vitamin" in raw_name:
                disp = "Vitamins & Supplements"
            else:
                disp = raw_name.split("&")[0].strip()
            rev = float(c.get("total_rev") or 0.0)
            pct = int(round((rev / total_cat_rev) * 100))
            sales_by_category.append({"name": disp, "revenue": round(rev, 2), "pct": pct})
    else:
        sales_by_category = [
            {"name": "Analgesics", "revenue": 78.0, "pct": 78},
            {"name": "Antibiotics", "revenue": 22.0, "pct": 22},
            {"name": "Vitamins & Supplements", "revenue": 0.0, "pct": 0},
        ]

    # 4. Stock health distribution
    try:
        sh = db.execute_query(
            """
            SELECT 
                COUNT(*) as total_prods,
                COALESCE(SUM(CASE WHEN stock_qty <= 0 THEN 1 ELSE 0 END), 0) as out_of_stock,
                COALESCE(SUM(CASE WHEN stock_qty > 0 AND stock_qty <= reorder_level THEN 1 ELSE 0 END), 0) as low_stock,
                COALESCE(SUM(CASE WHEN stock_qty > reorder_level THEN 1 ELSE 0 END), 0) as healthy_stock
            FROM products
            WHERE is_active = TRUE
            """,
            fetchone=True,
        ) or {}
    except Exception:
        sh = {}

    stock_health = {
        "total": int(sh.get("total_prods") or metrics["total_products"]),
        "healthy": int(sh.get("healthy_stock") or 0),
        "low_stock": int(sh.get("low_stock") or 0),
        "out_of_stock": int(sh.get("out_of_stock") or 0),
        "near_expiry": metrics["near_expiry_count"],
    }

    return jsonify({
        "metrics": metrics,
        "trend_14d": trend_14d,
        "top_5_products": top_5_products,
        "sales_by_category": sales_by_category,
        "stock_health": stock_health,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Inventory Management API (Matches screens/inventory.py)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/inventory", methods=["GET"])
def api_inventory():
    today = date.today()
    warn_date = today + timedelta(days=config.EXPIRY_WARN_DAYS)

    products_raw = db.execute_query(
        """
        SELECT p.id, p.sku, p.name, c.name as category_name, p.category_id, p.supplier_id,
               s.name as supplier_name,
               p.cost_price, p.selling_price, p.stock_qty, p.reorder_level, 
               p.expiry_date, p.unit
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.is_active = TRUE
        ORDER BY p.name ASC
        """,
        fetchall=True,
    ) or []

    categories = db.execute_query(
        "SELECT id, name, description FROM categories ORDER BY name ASC",
        fetchall=True,
    ) or []

    suppliers = db.execute_query(
        "SELECT id, name, contact_person, phone, email, address FROM suppliers ORDER BY name ASC",
        fetchall=True,
    ) or []

    products = []
    low_count = 0
    exp_soon_count = 0

    for p in products_raw:
        stock_qty = int(p.get("stock_qty") or 0)
        reorder_lvl = int(p.get("reorder_level") or 15)
        is_low = stock_qty <= reorder_lvl
        if is_low:
            low_count += 1

        exp_raw = p.get("expiry_date")
        exp_date = exp_raw.date() if hasattr(exp_raw, "date") else exp_raw
        if isinstance(exp_date, str):
            try:
                exp_date = datetime.strptime(exp_date[:10], "%Y-%m-%d").date()
            except Exception:
                exp_date = None

        is_expiring_soon = False
        is_expired = False
        if isinstance(exp_date, date):
            if exp_date < today:
                is_expired = True
            elif today <= exp_date <= warn_date:
                is_expiring_soon = True
                exp_soon_count += 1

        products.append({
            "id": p["id"],
            "sku": p["sku"],
            "name": p["name"],
            "category_id": p["category_id"],
            "category_name": p.get("category_name") or "Uncategorized",
            "supplier_id": p.get("supplier_id"),
            "supplier_name": p.get("supplier_name") or "None",
            "cost_price": float(p.get("cost_price") or 0.0),
            "selling_price": float(p.get("selling_price") or 0.0),
            "stock_qty": stock_qty,
            "reorder_level": reorder_lvl,
            "expiry_date": _serialize_date(exp_raw),
            "unit": p.get("unit") or "piece",
            "is_low": is_low,
            "is_expiring_soon": is_expiring_soon,
            "is_expired": is_expired,
            "status_text": "Low stock" if is_low else "In stock",
        })

    return jsonify({
        "kpis": {
            "total_products": len(products),
            "low_stock": low_count,
            "categories_count": len(categories),
            "expiring_soon": exp_soon_count,
        },
        "products": products,
        "categories": categories,
        "suppliers": suppliers,
    })


@app.route("/api/inventory/auto-price", methods=["POST"])
def api_auto_price():
    data = request.get_json(silent=True) or {}
    cat_name = data.get("category_name") or ""
    cat_id = data.get("category_id")
    cost, sell = generate_category_prices(cat_name, cat_id)
    return jsonify({"cost_price": cost, "selling_price": sell})


@app.route("/api/inventory/product", methods=["POST"])
def api_create_product():
    data = request.get_json(silent=True) or {}
    sku = (data.get("sku") or "").strip()
    name = (data.get("name") or "").strip()
    cat_id = data.get("category_id")
    sup_id = data.get("supplier_id") or None
    unit = (data.get("unit") or "piece").strip() or "piece"

    if not sku or not name or not cat_id:
        return jsonify({"ok": False, "message": "SKU, Product Name, and Category are required."}), 400

    try:
        cost = float(data.get("cost_price", 0))
        price = float(data.get("selling_price", 0))
        stock = int(data.get("stock_qty", 0))
        reorder = int(data.get("reorder_level", 15))
        if cost < 0 or price < 0 or stock < 0 or reorder < 0:
            raise ValueError("Numeric values must be non-negative.")
        exp_date = datetime.strptime((data.get("expiry_date") or "").strip(), "%Y-%m-%d").date()
    except Exception as ve:
        return jsonify({"ok": False, "message": f"Validation error: {ve}"}), 400

    try:
        new_id = db.execute_query(
            """
            INSERT INTO products (sku, name, category_id, supplier_id, cost_price, selling_price, stock_qty, reorder_level, expiry_date, unit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (sku, name, int(cat_id), int(sup_id) if sup_id else None, cost, price, stock, reorder, exp_date, unit),
            commit=True,
        )
        if stock > 0:
            db.execute_query(
                """
                INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
                VALUES (%s, 'IN', %s, 'Initial inventory stock on creation', %s)
                """,
                (new_id, stock, auth.SessionManager.get_user_id()),
                commit=True,
            )
        auth.log_audit("PRODUCT_CREATE", f"Created product: {name} (SKU: {sku}, Qty: {stock})")
        return jsonify({"ok": True, "message": f"Product '{name}' added successfully!", "id": new_id})
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Failed to save product: {ex}"}), 400


@app.route("/api/inventory/product/<int:prod_id>", methods=["PUT"])
def api_update_product(prod_id):
    data = request.get_json(silent=True) or {}
    sku = (data.get("sku") or "").strip()
    name = (data.get("name") or "").strip()
    cat_id = data.get("category_id")
    sup_id = data.get("supplier_id") or None
    unit = (data.get("unit") or "piece").strip() or "piece"

    if not sku or not name or not cat_id:
        return jsonify({"ok": False, "message": "SKU, Product Name, and Category are required."}), 400

    try:
        cost = float(data.get("cost_price", 0))
        price = float(data.get("selling_price", 0))
        stock = int(data.get("stock_qty", 0))
        reorder = int(data.get("reorder_level", 15))
        if cost < 0 or price < 0 or stock < 0 or reorder < 0:
            raise ValueError("Numeric values must be non-negative.")
        exp_date = datetime.strptime((data.get("expiry_date") or "").strip(), "%Y-%m-%d").date()
    except Exception as ve:
        return jsonify({"ok": False, "message": f"Validation error: {ve}"}), 400

    try:
        db.execute_query(
            """
            UPDATE products
            SET sku = %s, name = %s, category_id = %s, supplier_id = %s, cost_price = %s,
                selling_price = %s, stock_qty = %s, reorder_level = %s, expiry_date = %s, unit = %s
            WHERE id = %s
            """,
            (sku, name, int(cat_id), int(sup_id) if sup_id else None, cost, price, stock, reorder, exp_date, unit, prod_id),
            commit=True,
        )
        auth.log_audit("PRODUCT_UPDATE", f"Updated product ID {prod_id}: {name} (SKU: {sku})")
        return jsonify({"ok": True, "message": f"Product '{name}' updated successfully!"})
    except Exception as ex:
        return jsonify({"ok": False, "message": f"Failed to update product: {ex}"}), 400


@app.route("/api/inventory/bulk-delete", methods=["POST"])
def api_bulk_delete_products():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    if not ids:
        return jsonify({"ok": False, "message": "No products selected."}), 400
    for pid in ids:
        db.execute_query("UPDATE products SET is_active = FALSE WHERE id = %s", (int(pid),), commit=True)
        auth.log_audit("PRODUCT_DELETE", f"Soft-deleted product ID {pid}")
    return jsonify({"ok": True, "message": f"{len(ids)} product(s) successfully deleted."})


@app.route("/api/inventory/stock-movement", methods=["POST"])
def api_stock_movement():
    data = request.get_json(silent=True) or {}
    prod_id = data.get("product_id")
    m_type = (data.get("movement_type") or "IN").upper()
    if m_type.startswith("IN"):
        m_type = "IN"
    elif m_type.startswith("OUT"):
        m_type = "OUT"
    else:
        m_type = "ADJUSTMENT"

    try:
        qty = int(data.get("quantity", 0))
        if qty <= 0:
            raise ValueError("Quantity must be greater than zero.")
    except Exception as ve:
        return jsonify({"ok": False, "message": str(ve)}), 400

    prod = db.execute_query("SELECT id, name, stock_qty, sku FROM products WHERE id = %s", (prod_id,), fetchone=True)
    if not prod:
        return jsonify({"ok": False, "message": "Product not found."}), 404

    current_stock = int(prod["stock_qty"])
    new_stock = current_stock
    if m_type == "IN":
        new_stock += qty
    elif m_type == "OUT":
        if qty > current_stock:
            return jsonify({"ok": False, "message": f"Cannot stock out {qty} units; only {current_stock} currently in stock."}), 400
        new_stock -= qty
    elif m_type == "ADJUSTMENT":
        new_stock = qty

    note = (data.get("reference_note") or "PO-Replenishment").strip()
    db.execute_query("UPDATE products SET stock_qty = %s WHERE id = %s", (new_stock, prod_id), commit=True)
    db.execute_query(
        """
        INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (prod_id, m_type, qty, note, auth.SessionManager.get_user_id()),
        commit=True,
    )
    auth.log_audit("STOCK_MOVEMENT", f"{m_type} {qty} units for {prod['name']}. New stock: {new_stock}. Note: {note}")
    return jsonify({"ok": True, "message": f"Stock movement recorded! New stock: {new_stock}", "new_stock": new_stock})


@app.route("/api/inventory/movements", methods=["GET"])
def api_get_movements():
    rows = db.execute_query(
        """
        SELECT sm.id, sm.created_at, p.sku, p.name as prod_name, sm.movement_type, sm.quantity, sm.reference_note, u.username
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.id
        LEFT JOIN users u ON sm.user_id = u.id
        ORDER BY sm.created_at DESC
        LIMIT 250
        """,
        fetchall=True,
    ) or []
    out = []
    for m in rows:
        out.append({
            "id": m["id"],
            "created_at": _serialize_dt(m.get("created_at")),
            "sku": m["sku"],
            "prod_name": m["prod_name"],
            "movement_type": m["movement_type"],
            "quantity": int(m["quantity"]),
            "reference_note": m.get("reference_note") or "-",
            "username": m.get("username") or "System",
        })
    return jsonify({"movements": out})


@app.route("/api/inventory/category", methods=["POST"])
def api_add_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    desc = (data.get("description") or "").strip()
    if not name:
        return jsonify({"ok": False, "message": "Category name is required."}), 400
    try:
        db.execute_query("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, desc), commit=True)
        auth.log_audit("CATEGORY_CREATE", f"Created category: {name}")
        return jsonify({"ok": True, "message": f"Category '{name}' created!"})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Failed to save category: {e}"}), 400


@app.route("/api/inventory/supplier", methods=["POST"])
def api_add_supplier():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    contact = (data.get("contact_person") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    if not name:
        return jsonify({"ok": False, "message": "Supplier name is required."}), 400
    try:
        db.execute_query(
            "INSERT INTO suppliers (name, contact_person, phone, email) VALUES (%s, %s, %s, %s)",
            (name, contact, phone, email),
            commit=True,
        )
        auth.log_audit("SUPPLIER_CREATE", f"Created supplier: {name}")
        return jsonify({"ok": True, "message": f"Supplier '{name}' created!"})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Failed to save supplier: {e}"}), 400


# ─────────────────────────────────────────────────────────────────────────────
# Point of Sale (POS) & Sales History API (Matches screens/sales.py)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/sales/checkout", methods=["POST"])
def api_sales_checkout():
    data = request.get_json(silent=True) or {}
    cart = data.get("cart") or []
    if not cart:
        return jsonify({"ok": False, "message": "There are no items in the cart to process."}), 400

    discount_pct = max(0.0, min(100.0, float(data.get("discount_percent") or 0.0)))
    customer = (data.get("customer_name") or "").strip() or "Walk-in Customer"
    pay_method = (data.get("payment_method") or "CASH").upper()

    subtotal = 0.0
    resolved_items = []
    for c_item in cart:
        pid = int(c_item["product_id"])
        qty = int(c_item["qty"])
        prod = db.execute_query("SELECT id, name, selling_price, cost_price, stock_qty FROM products WHERE id = %s", (pid,), fetchone=True)
        if not prod:
            return jsonify({"ok": False, "message": f"Product ID {pid} not found."}), 404
        if qty > int(prod["stock_qty"]):
            return jsonify({"ok": False, "message": f"Insufficient stock for {prod['name']} (Available: {prod['stock_qty']})."}), 400
        price = float(prod["selling_price"])
        cost = float(prod["cost_price"])
        line_total = round(price * qty, 2)
        subtotal += line_total
        resolved_items.append({
            "product_id": pid,
            "name": prod["name"],
            "qty": qty,
            "price": price,
            "cost": cost,
            "line_total": line_total,
        })

    subtotal = round(subtotal, 2)
    discount_amt = round(subtotal * (discount_pct / 100.0), 2)
    total = max(0.0, round(subtotal - discount_amt, 2))

    try:
        paid = float(data.get("amount_paid", total))
    except Exception:
        return jsonify({"ok": False, "message": "Please enter a valid numeric amount paid."}), 400

    if paid < total:
        return jsonify({
            "ok": False,
            "message": f"Amount paid ({config.CURRENCY}{paid:.2f}) is less than total due ({config.CURRENCY}{total:.2f}).",
        }), 400

    change = round(paid - total, 2)
    user = auth.SessionManager.get_user() or {}
    user_id = user.get("id") or 1
    cashier_name = user.get("full_name") or "Staff"
    inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    sale_id = db.execute_query(
        """
        INSERT INTO sales (invoice_no, user_id, subtotal, discount_percent, discount_amount, total_amount, payment_method, amount_paid, change_amount, customer_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (inv_no, user_id, subtotal, discount_pct, discount_amt, total, pay_method, paid, change, customer),
        commit=True,
    )

    for item in resolved_items:
        db.execute_query(
            """
            INSERT INTO sales_items (sale_id, product_id, quantity, unit_price, unit_cost, line_total)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (sale_id, item["product_id"], item["qty"], item["price"], item["cost"], item["line_total"]),
            commit=True,
        )
        db.execute_query(
            "UPDATE products SET stock_qty = stock_qty - %s WHERE id = %s",
            (item["qty"], item["product_id"]),
            commit=True,
        )
        db.execute_query(
            """
            INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
            VALUES (%s, 'OUT', %s, %s, %s)
            """,
            (item["product_id"], item["qty"], f"Sale: {inv_no}", user_id),
            commit=True,
        )

    auth.log_audit("SALE_COMPLETE", f"Processed invoice {inv_no} for {customer}. Total: {config.CURRENCY}{total:.2f}")

    # Build official RESTINPILLS PHARMACY receipt lines
    lines = [
        "==========================================",
        "           RESTINPILLS PHARMACY           ",
        "       123 Healthcare Blvd, Suite 100     ",
        "            Tel: +1-800-555-0199          ",
        "==========================================",
        f"Invoice No : {inv_no}",
        f"Date/Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Cashier    : {cashier_name}",
        f"Customer   : {customer}",
        f"Pay Method : {pay_method}",
        "------------------------------------------",
        f"{'Item':<22} {'Qty':>4} {'Price':>6} {'Total':>7}",
        "------------------------------------------",
    ]
    for item in resolved_items:
        i_name = item["name"][:21]
        lines.append(f"{i_name:<22} {item['qty']:>4} {item['price']:>6.2f} {item['line_total']:>7.2f}")
    lines.extend([
        "------------------------------------------",
        f"{'Subtotal:':<30} {config.CURRENCY}{subtotal:>9.2f}",
        f"{'Discount:':<30} -{config.CURRENCY}{discount_amt:>8.2f}",
        f"{'TOTAL AMOUNT:':<30} {config.CURRENCY}{total:>9.2f}",
        f"{'Amount Paid:':<30} {config.CURRENCY}{paid:>9.2f}",
        f"{'Change Due:':<30} {config.CURRENCY}{change:>9.2f}",
        "==========================================",
        "       Thank you for your purchase!       ",
        "       Please keep for your records.      ",
        "==========================================",
    ])

    return jsonify({
        "ok": True,
        "invoice_no": inv_no,
        "sale_id": sale_id,
        "receipt_text": "\n".join(lines),
        "summary": {
            "subtotal": subtotal,
            "discount_amount": discount_amt,
            "total": total,
            "paid": paid,
            "change": change,
        },
    })


@app.route("/api/sales/history", methods=["GET"])
def api_sales_history():
    search = (request.args.get("search") or "").strip()
    query = """
        SELECT s.id, s.invoice_no, s.created_at, u.username as cashier, s.customer_name, 
               s.subtotal, s.discount_amount, s.total_amount, s.payment_method, s.amount_paid
        FROM sales s
        LEFT JOIN users u ON s.user_id = u.id
    """
    params = []
    if search:
        query += " WHERE s.invoice_no LIKE %s OR s.customer_name LIKE %s"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY s.created_at DESC LIMIT 200"

    rows = db.execute_query(query, params, fetchall=True) or []
    sales = []
    for s in rows:
        sales.append({
            "id": s["id"],
            "invoice_no": s["invoice_no"],
            "date": _serialize_dt(s.get("created_at")),
            "cashier": s.get("cashier") or "N/A",
            "customer": s.get("customer_name") or "Walk-in",
            "subtotal": float(s.get("subtotal") or 0.0),
            "discount": float(s.get("discount_amount") or 0.0),
            "total": float(s.get("total_amount") or 0.0),
            "method": s.get("payment_method") or "CASH",
            "paid": float(s.get("amount_paid") or 0.0),
        })
    return jsonify({"sales": sales})


@app.route("/api/sales/invoice/<int:sale_id>", methods=["GET"])
def api_invoice_items(sale_id):
    items = db.execute_query(
        """
        SELECT si.id, p.sku, p.name, si.quantity, si.unit_price, si.line_total
        FROM sales_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = %s
        """,
        (sale_id,),
        fetchall=True,
    ) or []
    out = [
        {
            "sku": it["sku"],
            "name": it["name"],
            "quantity": int(it["quantity"]),
            "unit_price": float(it["unit_price"]),
            "line_total": float(it["line_total"]),
        }
        for it in items
    ]
    return jsonify({"items": out})


# ─────────────────────────────────────────────────────────────────────────────
# Users & Security Audit Logs API (Matches screens/users.py)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/users", methods=["GET"])
def api_get_users():
    rows = db.execute_query(
        """
        SELECT id, username, full_name, role, email, is_active, failed_attempts, locked_until, last_login, created_at
        FROM users
        ORDER BY id ASC
        """,
        fetchall=True,
    ) or []
    now = datetime.now()
    users = []
    for u in rows:
        status = "Active"
        tag = "normal"
        locked_until = u.get("locked_until")
        if not u.get("is_active"):
            status = "Deactivated"
            tag = "inactive"
        elif isinstance(locked_until, datetime) and locked_until > now:
            status = "LOCKED"
            tag = "locked"
        users.append({
            "id": u["id"],
            "username": u["username"],
            "full_name": u["full_name"],
            "role": u["role"],
            "role_display": config.ROLE_DISPLAY_NAMES.get(u["role"], u["role"]),
            "email": u.get("email") or "-",
            "is_active": bool(u.get("is_active")),
            "status": status,
            "tag": tag,
            "failed_attempts": int(u.get("failed_attempts") or 0),
            "last_login": _serialize_dt(u.get("last_login")) or "Never",
            "created_at": _serialize_date(u.get("created_at")) or "-",
        })
    return jsonify({"users": users})


@app.route("/api/users", methods=["POST"])
def api_create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    pwd = data.get("password") or ""
    role = data.get("role") or config.ROLE_ADMIN

    if not username or not full_name or not pwd:
        return jsonify({"ok": False, "message": "Username, Full Name, and Password are required."}), 400
    if len(pwd) < 6:
        return jsonify({"ok": False, "message": "Password must be at least 6 characters."}), 400

    try:
        hashed = auth.hash_password(pwd)
        db.execute_query(
            """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, hashed, full_name, email, role),
            commit=True,
        )
        auth.log_audit("USER_CREATE", f"Created user {username} with role {role}")
        return jsonify({"ok": True, "message": f"User '{username}' created successfully!"})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Failed to create user: {e}"}), 400


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def api_update_user(user_id):
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    role = data.get("role") or config.ROLE_ADMIN
    if not full_name:
        return jsonify({"ok": False, "message": "Full Name is required."}), 400
    u_data = db.execute_query("SELECT username FROM users WHERE id = %s", (user_id,), fetchone=True)
    if not u_data:
        return jsonify({"ok": False, "message": "User not found."}), 404
    db.execute_query(
        "UPDATE users SET full_name = %s, email = %s, role = %s WHERE id = %s",
        (full_name, email, role, user_id),
        commit=True,
    )
    auth.log_audit("USER_UPDATE", f"Updated user {u_data['username']} (Role: {role})")
    return jsonify({"ok": True, "message": f"User '{u_data['username']}' updated!"})


@app.route("/api/users/<int:user_id>/reset-password", methods=["POST"])
def api_reset_password(user_id):
    data = request.get_json(silent=True) or {}
    p1 = data.get("password") or ""
    p2 = data.get("confirm_password") or ""
    if not p1 or not p2:
        return jsonify({"ok": False, "message": "Fields cannot be blank."}), 400
    if p1 != p2:
        return jsonify({"ok": False, "message": "Passwords do not match."}), 400
    if len(p1) < 6:
        return jsonify({"ok": False, "message": "Password must be at least 6 characters."}), 400
    u_data = db.execute_query("SELECT username FROM users WHERE id = %s", (user_id,), fetchone=True)
    if not u_data:
        return jsonify({"ok": False, "message": "User not found."}), 404
    hashed = auth.hash_password(p1)
    db.execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (hashed, user_id), commit=True)
    auth.log_audit("PASSWORD_RESET", f"Reset password for user {u_data['username']}")
    return jsonify({"ok": True, "message": f"Password for '{u_data['username']}' was reset!"})


@app.route("/api/users/<int:user_id>/unlock", methods=["POST"])
def api_unlock_user(user_id):
    u_data = db.execute_query("SELECT username FROM users WHERE id = %s", (user_id,), fetchone=True)
    if not u_data:
        return jsonify({"ok": False, "message": "User not found."}), 404
    db.execute_query("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s", (user_id,), commit=True)
    auth.log_audit("ACCOUNT_UNLOCKED", f"Account unlocked manually for user {u_data['username']}")
    return jsonify({"ok": True, "message": f"User '{u_data['username']}' is now unlocked with failed attempts reset to 0."})


@app.route("/api/users/<int:user_id>/toggle-active", methods=["POST"])
def api_toggle_user_active(user_id):
    if user_id == auth.SessionManager.get_user_id():
        return jsonify({"ok": False, "message": "You cannot deactivate your own logged-in account."}), 400
    u = db.execute_query("SELECT username, is_active FROM users WHERE id = %s", (user_id,), fetchone=True)
    if not u:
        return jsonify({"ok": False, "message": "User not found."}), 404
    new_status = not bool(u["is_active"])
    db.execute_query("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id), commit=True)
    auth.log_audit("USER_STATUS_CHANGE", f"Changed status of user {u['username']} to {'active' if new_status else 'inactive'}")
    return jsonify({"ok": True, "message": f"User '{u['username']}' is now {'Active' if new_status else 'Deactivated'}."})


@app.route("/api/audit-logs", methods=["GET"])
def api_audit_logs():
    action_filter = (request.args.get("action") or "All Actions").strip()
    query = "SELECT id, created_at, username, action, details, ip_address FROM audit_log"
    params = []
    if action_filter and action_filter != "All Actions":
        query += " WHERE action = %s"
        params.append(action_filter)
    query += " ORDER BY created_at DESC LIMIT 300"
    rows = db.execute_query(query, params, fetchall=True) or []
    logs = []
    for log in rows:
        logs.append({
            "id": log["id"],
            "time": _serialize_dt(log.get("created_at"), "%Y-%m-%d %H:%M:%S"),
            "username": log.get("username") or "System",
            "action": log["action"],
            "details": log.get("details") or "-",
            "ip": log.get("ip_address") or "127.0.0.1",
        })
    return jsonify({"logs": logs})


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Analysis Studio API (Matches screens/analysis.py + ml/)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/analysis/task/<task_name>", methods=["GET"])
def api_analysis_task(task_name):
    if task_name not in ("product_demand", "sales_revenue", "slow_moving", "best_selling"):
        return jsonify({"ok": False, "message": "Unknown analysis task."}), 400

    _, _, meta = ModelPredictor.get_models(task_name)

    csv_file = config.DATASETS_DIR / f"{task_name}.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file)
        columns = list(df.columns)
        total_rows = int(len(df))
        preview_rows = df.head(300).to_dict(orient="records")
    else:
        columns = []
        total_rows = 0
        preview_rows = []

    return jsonify({
        "ok": True,
        "task_name": task_name,
        "metadata": meta,
        "dataset": {
            "filename": csv_file.name,
            "total_rows": total_rows,
            "total_cols": len(columns),
            "columns": columns,
            "rows": preview_rows,
        },
    })


@app.route("/api/analysis/predict", methods=["POST"])
def api_analysis_predict():
    data = request.get_json(silent=True) or {}
    task_name = data.get("task_name") or "product_demand"
    model_type = "rf" if data.get("model_type", "rf") == "rf" else "linear"
    p = data.get("params") or {}

    try:
        if task_name == "product_demand":
            res = ModelPredictor.predict_product_demand(
                category=p.get("category", "Analgesics & Antipyretics"),
                unit_price=float(p.get("unit_price", 12.50)),
                cost_price=float(p.get("cost_price", 5.00)),
                month=int(p.get("month", 11)),
                day_of_week=int(p.get("day_of_week", 5)),
                is_flu_season=int(p.get("is_flu_season", 1)),
                is_rainy_season=int(p.get("is_rainy_season", 0)),
                is_promotion=int(p.get("is_promotion", 1)),
                discount_percent=float(p.get("discount_percent", 15)),
                stock_level=int(p.get("stock_level", 150)),
                model_type=model_type,
            )
            primary_text = f"Predicted Demand: {res['predicted_demand']:.0f} units"
            sub_text = f"Confidence Interval: {res['confidence_interval']} | Algorithm: {res['model_used']} (R²: {res['r2_score']:.3f})"
            chart = {
                "type": "bar",
                "title": "Predicted Demand with ±RMSE Confidence Interval",
                "y_label": "Quantity Demanded (Units)",
                "labels": ["Lower Error Bound", "Predicted Demand", "Upper Error Bound"],
                "values": [res["lower_bound"], res["predicted_demand"], res["upper_bound"]],
                "colors": ["accent", "teal", "accent"],
            }

        elif task_name == "sales_revenue":
            res = ModelPredictor.predict_sales_revenue(
                month=int(p.get("month", 12)),
                day_of_week=int(p.get("day_of_week", 6)),
                is_weekend=int(p.get("is_weekend", 1)),
                is_holiday=int(p.get("is_holiday", 1)),
                is_flu_season=int(p.get("is_flu_season", 1)),
                is_rainy_season=int(p.get("is_rainy_season", 0)),
                promo_active=int(p.get("promo_active", 1)),
                foot_traffic=int(p.get("foot_traffic", 230)),
                prescriptions_filled=int(p.get("prescriptions_filled", 75)),
                avg_basket_size=float(p.get("avg_basket_size", 38.50)),
                model_type=model_type,
            )
            primary_text = f"Projected Daily Revenue: {config.CURRENCY}{res['predicted_revenue']:,.2f}"
            sub_text = f"Confidence Interval: {res['confidence_interval']} | Algorithm: {res['model_used']} (R²: {res['r2_score']:.3f})"
            chart = {
                "type": "bar",
                "title": "Projected Revenue Envelope",
                "y_label": "Daily Revenue ($)",
                "labels": ["Min Bound", "Projected Revenue", "Max Bound"],
                "values": [res["lower_bound"], res["predicted_revenue"], res["upper_bound"]],
                "colors": ["accent", "teal", "accent"],
                "currency": True,
            }

        elif task_name == "slow_moving":
            res = ModelPredictor.predict_slow_moving(
                category=p.get("category", "Cardiovascular & Hypertension"),
                unit_price=float(p.get("unit_price", 45.00)),
                stock_qty=int(p.get("stock_qty", 280)),
                shelf_life_days=int(p.get("shelf_life_days", 365)),
                days_since_last_sale=int(p.get("days_since_last_sale", 48)),
                monthly_sales_velocity=float(p.get("monthly_sales_velocity", 6.5)),
                is_seasonal=int(p.get("is_seasonal", 0)),
                discount_applied=float(p.get("discount_applied", 0)),
                model_type=model_type,
            )
            primary_text = f"Turnover Ratio: {res['predicted_turnover_ratio']:.1f}% ({res['status_label']})"
            sub_text = f"{res['recommendation']} | Algorithm: {res['model_used']} (R²: {res['r2_score']:.3f})"
            chart = {
                "type": "threshold_hbar",
                "title": "Product Turnover Ratio vs Risk Threshold",
                "x_label": "Turnover Ratio (%)",
                "value": res["predicted_turnover_ratio"],
                "threshold": 15.0,
                "is_danger": res["is_slow_moving"],
            }

        elif task_name == "best_selling":
            res = ModelPredictor.predict_best_selling(
                category=p.get("category", "Respiratory & Cough Care"),
                unit_price=float(p.get("unit_price", 8.50)),
                historical_monthly_demand=float(p.get("historical_monthly_demand", 320)),
                customer_rating=float(p.get("customer_rating", 4.8)),
                month=int(p.get("month", 12)),
                is_flu_season=int(p.get("is_flu_season", 1)),
                is_rainy_season=int(p.get("is_rainy_season", 0)),
                promo_active=int(p.get("promo_active", 1)),
                stock_availability=float(p.get("stock_availability", 98.0)),
                model_type=model_type,
            )
            primary_text = f"Projected Monthly Volume: {res['projected_units']:,} units ({res['tier_classification']})"
            sub_text = f"Algorithm: {res['model_used']} (Model R²: {res['r2_score']:.3f})"
            chart = {
                "type": "bar",
                "title": "Benchmarked Sales Tier Classification",
                "y_label": "Monthly Units",
                "labels": ["Tier 3: Moderate", "Tier 2: Steady Core", "Tier 1: Top Seller", "Projected"],
                "values": [60, 160, 320, res["projected_units"]],
                "colors": ["muted", "accent", "teal", "lime"],
            }
        else:
            return jsonify({"ok": False, "message": "Unknown task."}), 400

        return jsonify({
            "ok": True,
            "result": res,
            "primary_text": primary_text,
            "sub_text": sub_text,
            "is_danger": bool(res.get("is_slow_moving", False)),
            "chart": chart,
        })
    except Exception as ex:
        return jsonify({"ok": False, "message": str(ex)}), 400


@app.route("/api/analysis/retrain", methods=["POST"])
def api_analysis_retrain():
    data = request.get_json(silent=True) or {}
    task_name = data.get("task_name") or "product_demand"
    try:
        meta = train.train_and_evaluate_task(task_name)
        auth.log_audit("ML_RETRAIN", f"Retrained Machine Learning models for task '{task_name}'")
        return jsonify({
            "ok": True,
            "message": f"Models for task '{task_name}' have been retrained and persisted successfully!",
            "metadata": meta,
        })
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error retraining models: {e}"}), 500


ensure_database_ready()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Starting RestInPills Web Server at http://127.0.0.1:%s", port)
    app.run(host="127.0.0.1", port=port, debug=False)
