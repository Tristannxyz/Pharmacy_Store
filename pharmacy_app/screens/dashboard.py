import os
import tempfile
# Ensure matplotlib cache is in writable temp dir to avoid permission warnings
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import config
import db
import auth

class DashboardScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=config.COLORS["background"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)

        self.setup_ui()

    def setup_ui(self):
        # Header Bar
        header = tk.Frame(self, bg=config.COLORS["surface"], padx=30, pady=18, highlightbackground=config.COLORS["border"], highlightthickness=1)
        header.pack(fill="x", side="top")

        welcome_text = f"Welcome back, {self.user.get('full_name', 'User')}!"
        lbl_welcome = tk.Label(header, text=welcome_text, font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl_welcome.pack(side="left")

        role_badge = tk.Label(
            header, 
            text=f"Role: {config.ROLE_DISPLAY_NAMES.get(self.role, self.role)}", 
            font=config.FONTS["body_bold"], 
            bg=config.COLORS["secondary"], 
            fg=config.COLORS["text_light"],
            padx=12,
            pady=4
        )
        role_badge.pack(side="right", padx=(10, 0))

        btn_refresh = tk.Button(
            header,
            text="↻ Refresh Data",
            font=config.FONTS["small"],
            bg=config.COLORS["surface_alt"],
            fg=config.COLORS["text_dark"],
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.refresh_dashboard
        )
        btn_refresh.pack(side="right")

        # Scrollable container for cards and charts
        self.canvas = tk.Canvas(self, bg=config.COLORS["background"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=config.COLORS["background"], padx=25, pady=20)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Ensure scrollable frame expands with canvas width
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.render_content()

    def fetch_metrics(self):
        """Fetches live metrics from MySQL database with safe fallback handling."""
        today_str = date.today().strftime("%Y-%m-%d")
        month_start_str = date.today().replace(day=1).strftime("%Y-%m-%d")

        try:
            # 1. Total sales today
            sales_today = db.execute_query(
                "SELECT COALESCE(SUM(total_amount), 0) AS total, COUNT(*) as cnt FROM sales WHERE DATE(created_at) = %s",
                (today_str,),
                fetchone=True
            )

            # 2. Monthly revenue
            monthly_sales = db.execute_query(
                "SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales WHERE DATE(created_at) >= %s",
                (month_start_str,),
                fetchone=True
            )

            # 3. Total products
            prod_stats = db.execute_query(
                "SELECT COUNT(*) AS total_prods, COALESCE(SUM(stock_qty * cost_price), 0) AS inventory_val FROM products WHERE is_active = TRUE",
                fetchone=True
            )

            # 4. Low stock count
            low_stock = db.execute_query(
                "SELECT COUNT(*) AS cnt FROM products WHERE is_active = TRUE AND stock_qty <= reorder_level",
                fetchone=True
            )

            # 5. Near expiry count
            expiry_limit = (date.today() + timedelta(days=config.EXPIRY_WARN_DAYS)).strftime("%Y-%m-%d")
            near_expiry = db.execute_query(
                "SELECT COUNT(*) AS cnt FROM products WHERE is_active = TRUE AND expiry_date <= %s",
                (expiry_limit,),
                fetchone=True
            )

            # 6. Top product overall
            top_prod = db.execute_query("""
                SELECT p.name, SUM(si.quantity) as total_qty
                FROM sales_items si
                JOIN products p ON si.product_id = p.id
                GROUP BY p.id, p.name
                ORDER BY total_qty DESC
                LIMIT 1
            """, fetchone=True)

            return {
                "sales_today": float(sales_today["total"] if sales_today else 0.0),
                "sales_today_count": int(sales_today["cnt"] if sales_today else 0),
                "monthly_revenue": float(monthly_sales["total"] if monthly_sales else 0.0),
                "total_products": int(prod_stats["total_prods"] if prod_stats else 0),
                "inventory_value": float(prod_stats["inventory_val"] if prod_stats else 0.0),
                "low_stock_count": int(low_stock["cnt"] if low_stock else 0),
                "near_expiry_count": int(near_expiry["cnt"] if near_expiry else 0),
                "top_product_name": top_prod["name"] if top_prod else "N/A",
                "top_product_qty": int(top_prod["total_qty"] if top_prod else 0)
            }
        except Exception as e:
            return {
                "sales_today": 0.0,
                "sales_today_count": 0,
                "monthly_revenue": 0.0,
                "total_products": 0,
                "inventory_value": 0.0,
                "low_stock_count": 0,
                "near_expiry_count": 0,
                "top_product_name": "Database Offline",
                "top_product_qty": 0
            }

    def render_content(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        metrics = self.fetch_metrics()

        # KPI Cards Container
        cards_container = tk.Frame(self.scrollable_frame, bg=config.COLORS["background"])
        cards_container.pack(fill="x", pady=(0, 20))

        # Define KPI cards based on role
        if self.role == config.ROLE_INVENTORY_CLERK:
            cards_data = [
                ("Total Active Products", f"{metrics['total_products']:,}", "In Catalog", config.COLORS["accent"]),
                ("Low-Stock Alerts", f"{metrics['low_stock_count']}", "At or below reorder", config.COLORS["danger"] if metrics['low_stock_count'] > 0 else config.COLORS["success"]),
                ("Near-Expiry Alerts", f"{metrics['near_expiry_count']}", f"Expiring in {config.EXPIRY_WARN_DAYS}d", config.COLORS["warning"] if metrics['near_expiry_count'] > 0 else config.COLORS["success"]),
                ("Total Inventory Value", f"{config.CURRENCY}{metrics['inventory_value']:,.2f}", "At Cost Valuation", config.COLORS["secondary"])
            ]
        elif self.role == config.ROLE_SALES_PERSONNEL:
            cards_data = [
                ("Sales Today", f"{config.CURRENCY}{metrics['sales_today']:,.2f}", f"{metrics['sales_today_count']} Transactions", config.COLORS["secondary"]),
                ("Month-to-Date Revenue", f"{config.CURRENCY}{metrics['monthly_revenue']:,.2f}", "Current Month", config.COLORS["accent"]),
                ("Best-Selling Item", metrics["top_product_name"][:20], f"{metrics['top_product_qty']} units sold", config.COLORS["info"]),
                ("Catalog Items", f"{metrics['total_products']}", "Available Products", config.COLORS["primary_light"])
            ]
        else: # Admin & Instructor (Full Overview)
            cards_data = [
                ("Sales Today", f"{config.CURRENCY}{metrics['sales_today']:,.2f}", f"{metrics['sales_today_count']} Transactions", config.COLORS["secondary"]),
                ("Month-to-Date Revenue", f"{config.CURRENCY}{metrics['monthly_revenue']:,.2f}", "Current Month", config.COLORS["accent"]),
                ("Total Products", f"{metrics['total_products']:,}", "Active in Catalog", config.COLORS["primary_light"]),
                ("Low-Stock Alerts", f"{metrics['low_stock_count']}", "Needs Restocking", config.COLORS["danger"] if metrics['low_stock_count'] > 0 else config.COLORS["success"]),
                ("Near-Expiry Alerts", f"{metrics['near_expiry_count']}", f"Within {config.EXPIRY_WARN_DAYS} days", config.COLORS["warning"] if metrics['near_expiry_count'] > 0 else config.COLORS["success"]),
                ("Top Performing Product", metrics["top_product_name"][:18], f"{metrics['top_product_qty']} units", config.COLORS["info"])
            ]

        # Render cards dynamically
        num_cards = len(cards_data)
        cols = 3 if num_cards == 6 else 4
        for i, (title, value, subtext, color) in enumerate(cards_data):
            row = i // cols
            col = i % cols
            card = self.create_kpi_card(cards_container, title, value, subtext, color)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            cards_container.grid_columnconfigure(col, weight=1)

        # Charts Section
        self.render_charts()

    def create_kpi_card(self, parent, title, value, subtext, accent_color):
        card = tk.Frame(parent, bg=config.COLORS["surface"], padx=18, pady=16, highlightbackground=config.COLORS["border"], highlightthickness=1)
        
        # Color bar top accent
        accent_strip = tk.Frame(card, bg=accent_color, height=4)
        accent_strip.pack(fill="x", side="top", pady=(0, 10))

        lbl_title = tk.Label(card, text=title, font=config.FONTS["small"], bg=config.COLORS["surface"], fg=config.COLORS["text_muted"])
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(card, text=value, font=config.FONTS["h1"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl_val.pack(anchor="w", pady=(4, 2))

        lbl_sub = tk.Label(card, text=subtext, font=("Segoe UI", 8), bg=config.COLORS["surface"], fg=config.COLORS["text_muted"])
        lbl_sub.pack(anchor="w")

        return card

    def render_charts(self):
        """Builds and embeds responsive Matplotlib figures into Tkinter."""
        chart_section = tk.Frame(self.scrollable_frame, bg=config.COLORS["background"])
        chart_section.pack(fill="both", expand=True, pady=(10, 20))

        # Chart Grid
        chart_grid = tk.Frame(chart_section, bg=config.COLORS["background"])
        chart_grid.pack(fill="both", expand=True)
        chart_grid.grid_columnconfigure(0, weight=1)
        chart_grid.grid_columnconfigure(1, weight=1)

        if self.role in [config.ROLE_ADMIN, config.ROLE_INSTRUCTOR]:
            # 4 Full Charts
            self.embed_sales_trend_chart(chart_grid, 0, 0)
            self.embed_top_products_chart(chart_grid, 0, 1)
            self.embed_sales_category_chart(chart_grid, 1, 0)
            self.embed_stock_level_chart(chart_grid, 1, 1)

        elif self.role == config.ROLE_INVENTORY_CLERK:
            # 2 Inventory-focused Charts
            self.embed_stock_level_chart(chart_grid, 0, 0)
            self.embed_sales_category_chart(chart_grid, 0, 1)

        elif self.role == config.ROLE_SALES_PERSONNEL:
            # 2 Sales-focused Charts
            self.embed_sales_trend_chart(chart_grid, 0, 0)
            self.embed_top_products_chart(chart_grid, 0, 1)

    def embed_sales_trend_chart(self, parent, row, col):
        """Chart 1: Sales Trend (Past 14 Days)"""
        container = tk.Frame(parent, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        container.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        lbl = tk.Label(container, text="14-Day Sales Revenue Trend", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl.pack(anchor="w", pady=(0, 10))

        try:
            trend_data = db.execute_query("""
                SELECT DATE(created_at) as sale_day, SUM(total_amount) as daily_rev
                FROM sales
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                GROUP BY DATE(created_at)
                ORDER BY sale_day ASC
            """, fetchall=True)
        except Exception:
            trend_data = None

        fig = Figure(figsize=(5.5, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)

        if trend_data:
            dates = [d["sale_day"].strftime("%m/%d") if hasattr(d["sale_day"], "strftime") else str(d["sale_day"])[-5:] for d in trend_data]
            revenues = [float(d["daily_rev"]) for d in trend_data]
            ax.plot(dates, revenues, marker="o", color=config.COLORS["secondary_dark"], linewidth=2, markersize=5)
            ax.fill_between(dates, revenues, color=config.COLORS["secondary"], alpha=0.15)
        else:
            ax.text(0.5, 0.5, "No recent sales recorded", ha="center", va="center", color=config.COLORS["text_muted"])

        ax.set_facecolor(config.COLORS["surface"])
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def embed_top_products_chart(self, parent, row, col):
        """Chart 2: Top 5 Products Sold"""
        container = tk.Frame(parent, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        container.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        lbl = tk.Label(container, text="Top 5 Products by Quantity Sold", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl.pack(anchor="w", pady=(0, 10))

        try:
            top_data = db.execute_query("""
                SELECT p.name, SUM(si.quantity) as total_qty
                FROM sales_items si
                JOIN products p ON si.product_id = p.id
                GROUP BY p.id, p.name
                ORDER BY total_qty DESC
                LIMIT 5
            """, fetchall=True)
        except Exception:
            top_data = None

        fig = Figure(figsize=(5.5, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)

        if top_data:
            names = [d["name"][:16] + ".." if len(d["name"]) > 16 else d["name"] for d in reversed(top_data)]
            qtys = [int(d["total_qty"]) for d in reversed(top_data)]
            bars = ax.barh(names, qtys, color=config.COLORS["accent"], height=0.55)
            ax.bar_label(bars, padding=4, color=config.COLORS["text_dark"], fontsize=8)
        else:
            ax.text(0.5, 0.5, "No sales recorded yet", ha="center", va="center", color=config.COLORS["text_muted"])

        ax.set_facecolor(config.COLORS["surface"])
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, axis="x", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def embed_sales_category_chart(self, parent, row, col):
        """Chart 3: Sales by Category"""
        container = tk.Frame(parent, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        container.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        lbl = tk.Label(container, text="Sales Breakdown by Category", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl.pack(anchor="w", pady=(0, 10))

        try:
            cat_data = db.execute_query("""
                SELECT c.name, COALESCE(SUM(si.line_total), 0) as total_rev
                FROM sales_items si
                JOIN products p ON si.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                GROUP BY c.id, c.name
                HAVING total_rev > 0
                ORDER BY total_rev DESC
                LIMIT 5
            """, fetchall=True)
        except Exception:
            cat_data = None

        fig = Figure(figsize=(5.5, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)

        palette = [config.COLORS["secondary"], config.COLORS["accent"], config.COLORS["info"], config.COLORS["warning"], "#8b5cf6"]

        if cat_data:
            labels = [c["name"][:14] for c in cat_data]
            values = [float(c["total_rev"]) for c in cat_data]
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=labels, 
                autopct="%1.0f%%", 
                colors=palette[:len(values)],
                startangle=140,
                textprops=dict(color=config.COLORS["text_dark"], fontsize=8)
            )
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)
                autotext.set_weight("bold")
        else:
            ax.text(0.5, 0.5, "No category sales recorded", ha="center", va="center", color=config.COLORS["text_muted"])

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def embed_stock_level_chart(self, parent, row, col):
        """Chart 4: Stock Status & Replenishment Needs"""
        container = tk.Frame(parent, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        container.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        lbl = tk.Label(container, text="Stock Health Distribution", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl.pack(anchor="w", pady=(0, 10))

        try:
            counts = db.execute_query("""
                SELECT 
                    SUM(CASE WHEN stock_qty <= 0 THEN 1 ELSE 0 END) as out_of_stock,
                    SUM(CASE WHEN stock_qty > 0 AND stock_qty <= reorder_level THEN 1 ELSE 0 END) as low_stock,
                    SUM(CASE WHEN stock_qty > reorder_level THEN 1 ELSE 0 END) as healthy_stock
                FROM products
                WHERE is_active = TRUE
            """, fetchone=True)
        except Exception:
            counts = {"out_of_stock": 0, "low_stock": 0, "healthy_stock": 0}

        fig = Figure(figsize=(5.5, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)

        labels = ["Healthy Stock", "Low Stock", "Out of Stock"]
        values = [
            int(counts["healthy_stock"] or 0),
            int(counts["low_stock"] or 0),
            int(counts["out_of_stock"] or 0)
        ]
        bar_colors = [config.COLORS["success"], config.COLORS["warning"], config.COLORS["danger"]]

        bars = ax.bar(labels, values, color=bar_colors, width=0.5)
        ax.bar_label(bars, padding=4, color=config.COLORS["text_dark"], fontsize=9, fontweight="bold")

        ax.set_facecolor(config.COLORS["surface"])
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh_dashboard(self):
        self.render_content()

