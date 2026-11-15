import random
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont

import config
import db
import auth
from theme import SmoothScroller


# ─────────────────────────────────────────────────────────────────────────────
# Theme & Color Tokens (Matching Design Specification)
# ─────────────────────────────────────────────────────────────────────────────
T = {
    "bg": "#0A101C",
    "surface": "#111A2B",
    "surface_header": "#0D1524",
    "hover_row": "#15213A",
    "selected_row": "#192843",
    "border_card": "#1E2B42",
    "border_input": "#2A3B5A",
    "text": "#E6EDF7",
    "text_muted": "#9FB0C8",
    "lime": "#A3E635",
    "lime_text": "#0A101C",
    "danger_row": "#1F1620",
    "danger_badge_bg": "#4A1D26",
    "danger_badge_text": "#FFB0B0",
    "danger_bar": "#FF8A8A",
    "success_badge_bg": "#1C3317",
    "success_badge_text": "#B5EC7A",
    "tab_active_bg": "#1C2A44",
    "tab_active_fg": "#FFFFFF",
    "chip_active_bg": "#1C2A44",
    "chip_active_border": "#A3E635",
}


# Category-specific wholesale cost range and retail markup multipliers:
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
    """Generates a realistic cost_price and selling_price pair for a given category."""
    price_range = CATEGORY_PRICE_RANGES.get(cat_name)

    if price_range is None and cat_id is not None:
        try:
            stats = db.execute_query("""
                SELECT MIN(cost_price) AS min_c, MAX(cost_price) AS max_c,
                       AVG(selling_price / NULLIF(cost_price, 0)) AS avg_markup
                FROM products
                WHERE category_id = %s AND is_active = TRUE AND cost_price BETWEEN 0.05 AND 200
            """, (cat_id,), fetchone=True)
            if stats and stats["min_c"] is not None:
                min_c = max(0.10, float(stats["min_c"]) * 0.85)
                max_c = max(min_c + 0.25, float(stats["max_c"]) * 1.15)
                avg_m = float(stats["avg_markup"] or 2.8)
                price_range = (min_c, max_c, max(1.8, avg_m * 0.9), max(2.2, avg_m * 1.1))
        except Exception:
            pass

    if price_range is None:
        price_range = (0.50, 3.50, 2.4, 3.1)

    min_c, max_c, min_m, max_m = price_range
    raw_cost = random.uniform(min_c, max_c)
    cost = max(0.10, round(raw_cost * 20) / 20)

    markup = random.uniform(min_m, max_m)
    raw_sell = max(cost + 0.25, cost * markup)
    sell = max(cost + 0.25, round(raw_sell * 20) / 20)

    return f"{cost:.2f}", f"{sell:.2f}"


class InventoryScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=T["bg"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)
        self.can_edit = self.role in [config.ROLE_INVENTORY_CLERK, config.ROLE_INSTRUCTOR]

        # Active state
        self.active_tab = "catalog"  # "catalog" | "movements" | "meta"
        self.active_chip = "All"     # "All" | "Low stock" | "Expiring soon" | category name
        self.selected_category_id = None
        self.selected_category_name = None
        self.selected_ids = set()    # Set of product IDs currently checked
        self.last_clicked_row_id = None
        self.sort_col = "name"
        self.sort_desc = False

        self._search_job = None
        self._all_products_cache = []
        self._displayed_products = []
        self._categories_cache = []
        self._progress_img_cache = {}

        self.setup_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # Layout Shell: Header & Segmented Tabs
    # ─────────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        # 1. Header Row
        header = tk.Frame(self, bg=T["surface_header"], padx=28, pady=16, highlightbackground=T["border_card"], highlightthickness=1)
        header.pack(fill="x", side="top")

        lbl_title = tk.Label(
            header,
            text="Inventory & Stock Management",
            font=("Segoe UI", 18, "bold"),
            bg=T["surface_header"],
            fg=T["text"]
        )
        lbl_title.pack(side="left")

        # Segmented Control Switch on Right
        switch_frame = tk.Frame(
            header,
            bg=T["surface"],
            padx=4,
            pady=4,
            highlightbackground=T["border_card"],
            highlightthickness=1
        )
        switch_frame.pack(side="right")

        self.tab_buttons = {}
        tab_defs = [
            ("catalog", "Product Catalog"),
            ("movements", "Stock Movements"),
            ("meta", "Suppliers & Categories")
        ]

        for tab_id, tab_label in tab_defs:
            is_active = (tab_id == self.active_tab)
            btn = tk.Button(
                switch_frame,
                text=tab_label,
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=T["tab_active_bg"] if is_active else T["surface"],
                fg=T["tab_active_fg"] if is_active else T["text_muted"],
                activebackground=T["tab_active_bg"],
                activeforeground=T["tab_active_fg"],
                relief="flat",
                bd=0,
                padx=14,
                pady=6,
                cursor="hand2",
                command=lambda tid=tab_id: self.switch_tab(tid)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab_id] = btn

        # Main Views Container
        self.views_container = tk.Frame(self, bg=T["bg"], padx=24, pady=16)
        self.views_container.pack(fill="both", expand=True)

        # Tab Views
        self.view_catalog = tk.Frame(self.views_container, bg=T["bg"])
        self.view_movements = tk.Frame(self.views_container, bg=T["bg"])
        self.view_meta = tk.Frame(self.views_container, bg=T["bg"])

        self.setup_catalog_view()
        self.setup_movements_view()
        self.setup_meta_view()

        self.switch_tab("catalog")

    def switch_tab(self, tab_id):
        self.active_tab = tab_id
        for tid, btn in self.tab_buttons.items():
            is_active = (tid == tab_id)
            btn.config(
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=T["tab_active_bg"] if is_active else T["surface"],
                fg=T["tab_active_fg"] if is_active else T["text_muted"]
            )

        self.view_catalog.pack_forget()
        self.view_movements.pack_forget()
        self.view_meta.pack_forget()

        if tab_id == "catalog":
            self.view_catalog.pack(fill="both", expand=True)
            self.update_kpis()
            self.load_products()
        elif tab_id == "movements":
            self.view_movements.pack(fill="both", expand=True)
            self.load_movements()
        elif tab_id == "meta":
            self.view_meta.pack(fill="both", expand=True)
            self.load_categories()
            self.load_suppliers()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Product Catalog Tab: KPIs, Toolbar, Modern Table, Bulk Actions
    # ─────────────────────────────────────────────────────────────────────────

    def setup_catalog_view(self):
        # 2. KPI Cards Row (4 equal cards)
        self.kpi_frame = tk.Frame(self.view_catalog, bg=T["bg"])
        self.kpi_frame.pack(fill="x", pady=(0, 14))

        for c_idx in range(4):
            self.kpi_frame.grid_columnconfigure(c_idx, weight=1, uniform="kpi")

        self.lbl_kpi_total = self._build_kpi_card(0, "TOTAL PRODUCTS", "0", False)
        self.lbl_kpi_low = self._build_kpi_card(1, "LOW STOCK", "0", True)
        self.lbl_kpi_cats = self._build_kpi_card(2, "CATEGORIES", "0", False)
        self.lbl_kpi_exp = self._build_kpi_card(3, "EXPIRING SOON", "0", False)

        # 3. Toolbar Row (Search, Filter chips, Action buttons)
        self.toolbar_frame = tk.Frame(self.view_catalog, bg=T["bg"])
        self.toolbar_frame.pack(fill="x", pady=(0, 12))

        # Search Bar on Left (height 44px)
        search_box = tk.Frame(
            self.toolbar_frame,
            bg=T["surface"],
            highlightbackground=T["border_input"],
            highlightthickness=1,
            padx=12,
            pady=0
        )
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))

        tk.Label(
            search_box,
            text="🔍",
            font=("Segoe UI", 11),
            bg=T["surface"],
            fg=T["text_muted"]
        ).pack(side="left", padx=(0, 8))

        self.ent_search = tk.Entry(
            search_box,
            font=("Segoe UI", 10),
            bg=T["surface"],
            fg=T["text"],
            insertbackground=T["text"],
            relief="flat",
            bd=0
        )
        self.ent_search.pack(side="left", fill="both", expand=True, ipady=10)
        self.ent_search.insert(0, "Search name, SKU or category")
        self.ent_search.config(fg=T["text_muted"])

        def _on_focus_in(e):
            if self.ent_search.get() == "Search name, SKU or category":
                self.ent_search.delete(0, tk.END)
                self.ent_search.config(fg=T["text"])

        def _on_focus_out(e):
            if not self.ent_search.get().strip():
                self.ent_search.insert(0, "Search name, SKU or category")
                self.ent_search.config(fg=T["text_muted"])

        self.ent_search.bind("<FocusIn>", _on_focus_in)
        self.ent_search.bind("<FocusOut>", _on_focus_out)
        self.ent_search.bind("<KeyRelease>", self._on_search_key)

        # Filter Chips: All, Low stock, Expiring soon, Category ▼
        self.chips_container = tk.Frame(self.toolbar_frame, bg=T["bg"])
        self.chips_container.pack(side="left", padx=(0, 12))

        self.chip_buttons = {}
        for chip_name in ["All", "Low stock", "Expiring soon"]:
            btn = tk.Button(
                self.chips_container,
                text=chip_name,
                font=("Segoe UI", 9, "bold" if chip_name == "All" else "normal"),
                bg=T["chip_active_bg"] if chip_name == "All" else T["surface"],
                fg=T["text"] if chip_name == "All" else T["text_muted"],
                activebackground=T["chip_active_bg"],
                activeforeground=T["text"],
                relief="flat",
                bd=0,
                padx=16,
                pady=10,
                cursor="hand2",
                highlightbackground=T["chip_active_border"] if chip_name == "All" else T["border_input"],
                highlightthickness=1,
                command=lambda name=chip_name: self.set_filter_chip(name)
            )
            btn.pack(side="left", padx=(0, 8))
            self.chip_buttons[chip_name] = btn

        # Category Dropdown Chip
        self.btn_cat_chip = tk.Button(
            self.chips_container,
            text="Category  ▾",
            font=("Segoe UI", 9),
            bg=T["surface"],
            fg=T["text_muted"],
            activebackground=T["chip_active_bg"],
            activeforeground=T["text"],
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            cursor="hand2",
            highlightbackground=T["border_input"],
            highlightthickness=1,
            command=self.open_category_menu
        )
        self.btn_cat_chip.pack(side="left")

        # Right Action Buttons (min 44px height)
        actions_box = tk.Frame(self.toolbar_frame, bg=T["bg"])
        actions_box.pack(side="right")

        self.btn_stock_in_out = tk.Button(
            actions_box,
            text="Stock In / Out",
            font=("Segoe UI", 9, "bold"),
            bg=T["surface"],
            fg=T["text"],
            activebackground=T["hover_row"],
            activeforeground=T["text"],
            relief="flat",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            highlightbackground=T["border_input"],
            highlightthickness=1,
            command=self.handle_toolbar_stock_movement
        )
        self.btn_stock_in_out.pack(side="left", padx=(0, 8))

        if self.can_edit:
            self.btn_add_prod = tk.Button(
                actions_box,
                text="+ Add Product",
                font=("Segoe UI", 9, "bold"),
                bg=T["lime"],
                fg=T["lime_text"],
                activebackground="#84cc16",
                activeforeground=T["lime_text"],
                relief="flat",
                bd=0,
                padx=18,
                pady=10,
                cursor="hand2",
                command=self.open_add_product_modal
            )
            self.btn_add_prod.pack(side="left")

        # Bulk Actions Bar (Shown dynamically when rows are selected)
        self.bulk_bar = tk.Frame(
            self.view_catalog,
            bg=T["tab_active_bg"],
            padx=18,
            pady=8,
            highlightbackground=T["border_input"],
            highlightthickness=1
        )
        self.lbl_bulk_info = tk.Label(
            self.bulk_bar,
            text="0 products selected",
            font=("Segoe UI", 9, "bold"),
            bg=T["tab_active_bg"],
            fg="#FFFFFF"
        )
        self.lbl_bulk_info.pack(side="left")

        if self.can_edit:
            self.btn_bulk_del = tk.Button(
                self.bulk_bar,
                text="🗑  Delete Selected",
                font=("Segoe UI", 9, "bold"),
                bg=T["danger_badge_bg"],
                fg=T["danger_badge_text"],
                activebackground="#7f1d1d",
                activeforeground="#FFFFFF",
                relief="flat",
                bd=0,
                padx=14,
                pady=6,
                cursor="hand2",
                highlightbackground=T["danger_bar"],
                highlightthickness=1,
                command=self.handle_bulk_delete
            )
            self.btn_bulk_del.pack(side="right", padx=(8, 0))

        self.btn_clear_sel = tk.Button(
            self.bulk_bar,
            text="✕ Clear Selection",
            font=("Segoe UI", 8),
            bg=T["surface"],
            fg=T["text_muted"],
            activebackground=T["hover_row"],
            activeforeground=T["text"],
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.clear_selection
        )
        self.btn_clear_sel.pack(side="right")

        # 4. Table Card Container
        self.table_card = tk.Frame(
            self.view_catalog,
            bg=T["surface"],
            highlightbackground=T["border_card"],
            highlightthickness=1
        )
        self.table_card.pack(fill="both", expand=True)

        # Header Row (bg #0D1524)
        self.header_row = tk.Frame(self.table_card, bg=T["surface_header"], height=44)
        self.header_row.pack(fill="x", side="top")
        self.header_row.pack_propagate(False)

        self.setup_table_headers()

        # Scrollable rows area with Canvas + Inner Frame + Scrollbars
        self.canvas_container = tk.Frame(self.table_card, bg=T["surface"])
        self.canvas_container.pack(fill="both", expand=True)

        self.canvas_table = tk.Canvas(self.canvas_container, bg=T["surface"], bd=0, highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas_table.yview)
        self.scroll_x = ttk.Scrollbar(self.canvas_container, orient="horizontal", command=self.canvas_table.xview)

        self.canvas_table.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.canvas_table.pack(side="left", fill="both", expand=True)

        self.table_inner = tk.Frame(self.canvas_table, bg=T["surface"])
        self.table_win_id = self.canvas_table.create_window((0, 0), window=self.table_inner, anchor="nw")

        self.table_inner.bind("<Configure>", lambda e: self.canvas_table.configure(scrollregion=self.canvas_table.bbox("all")))
        self.canvas_table.bind("<Configure>", self._on_canvas_configure)

        self._scroller = SmoothScroller(self.canvas_table, friction=0.82, speed_factor=3.5)
        self._scroller.attach_hover(self.canvas_table, self.table_inner)

        # 5. Table Footer Row
        self.footer_frame = tk.Frame(self.view_catalog, bg=T["bg"], pady=8)
        self.footer_frame.pack(fill="x", side="bottom")

        self.lbl_prod_count = tk.Label(
            self.footer_frame,
            text="Showing 0 of 0 products",
            font=("Segoe UI", 9),
            bg=T["bg"],
            fg=T["text_muted"]
        )
        self.lbl_prod_count.pack(side="left")

        self.lbl_hint = tk.Label(
            self.footer_frame,
            text="Select rows to delete or edit in bulk",
            font=("Segoe UI", 9),
            bg=T["bg"],
            fg=T["text_muted"]
        )
        self.lbl_hint.pack(side="right")

    def _on_canvas_configure(self, event):
        min_width = 1180
        width = max(min_width, event.width)
        self.canvas_table.itemconfig(self.table_win_id, width=width)

    def _build_kpi_card(self, col, label_text, default_val, is_danger=False):
        border_col = T["danger_badge_bg"] if is_danger else T["border_card"]
        val_col = T["danger_bar"] if is_danger else T["text"]

        card = tk.Frame(
            self.kpi_frame,
            bg=T["surface"],
            padx=20,
            pady=16,
            highlightbackground=border_col,
            highlightthickness=1
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        tk.Label(
            card,
            text=label_text,
            font=("Segoe UI", 8, "bold"),
            bg=T["surface"],
            fg=T["text_muted"]
        ).pack(anchor="w")

        lbl_val = tk.Label(
            card,
            text=default_val,
            font=("Segoe UI", 22, "bold"),
            bg=T["surface"],
            fg=val_col
        )
        lbl_val.pack(anchor="w", pady=(6, 0))
        return lbl_val

    # ─────────────────────────────────────────────────────────────────────────
    # Table Header Configuration & Click-to-Sort
    # ─────────────────────────────────────────────────────────────────────────

    def setup_table_headers(self):
        # Header Checkbox
        self.header_chk_var = tk.BooleanVar(value=False)
        self.btn_header_chk = tk.Button(
            self.header_row,
            text="☐",
            font=("Segoe UI", 12, "bold"),
            bg=T["surface_header"],
            fg=T["text_muted"],
            activebackground=T["surface_header"],
            activeforeground=T["lime"],
            relief="flat",
            bd=0,
            cursor="hand2",
            width=3,
            command=self.toggle_select_all
        )
        self.btn_header_chk.pack(side="left", padx=(10, 4))

        # Column definitions: (key, title, width, anchor, has_sort)
        self.col_headers = [
            ("name", "PRODUCT", 260, "w", True),
            ("category", "CATEGORY", 160, "w", True),
            ("stock", "STOCK VS. REORDER", 170, "w", True),
            ("cost", "COST", 90, "e", True),
            ("price", "PRICE", 90, "e", True),
            ("expiry", "EXPIRY", 110, "center", True),
            ("unit", "UNIT", 70, "center", False),
            ("status", "STATUS", 120, "center", True),
            ("actions", "ACTIONS", 90, "center", False),
        ]

        self.header_labels = {}
        for key, title, width, anchor, has_sort in self.col_headers:
            f = tk.Frame(self.header_row, bg=T["surface_header"], width=width)
            f.pack(side="left", fill="y")
            f.pack_propagate(False)

            txt = title
            if has_sort and key == self.sort_col:
                txt += "  ▼" if self.sort_desc else "  ▲"

            lbl = tk.Label(
                f,
                text=txt,
                font=("Segoe UI", 8, "bold"),
                bg=T["surface_header"],
                fg=T["lime"] if key == self.sort_col else T["text_muted"],
                anchor=anchor,
                cursor="hand2" if has_sort else "arrow"
            )
            lbl.pack(fill="both", expand=True, padx=8)

            if has_sort:
                lbl.bind("<Button-1>", lambda e, k=key: self.on_header_click(k))
            self.header_labels[key] = (lbl, title, has_sort)

    def on_header_click(self, col_key):
        if self.sort_col == col_key:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col = col_key
            self.sort_desc = False

        for k, (lbl, orig_title, has_sort) in self.header_labels.items():
            if not has_sort:
                continue
            if k == self.sort_col:
                arrow = "  ▼" if self.sort_desc else "  ▲"
                lbl.config(text=orig_title + arrow, fg=T["lime"])
            else:
                lbl.config(text=orig_title, fg=T["text_muted"])

        self.render_table_rows()

    # ─────────────────────────────────────────────────────────────────────────
    # Live Search, Filtering, Categories Dropdown
    # ─────────────────────────────────────────────────────────────────────────

    def _on_search_key(self, event=None):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(140, self.apply_filters_and_render)

    def set_filter_chip(self, chip_name):
        self.active_chip = chip_name
        self.selected_category_id = None
        self.selected_category_name = None
        self.btn_cat_chip.config(
            text="Category  ▾",
            bg=T["surface"],
            fg=T["text_muted"],
            highlightbackground=T["border_input"]
        )

        for name, btn in self.chip_buttons.items():
            is_active = (name == chip_name)
            btn.config(
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=T["chip_active_bg"] if is_active else T["surface"],
                fg=T["text"] if is_active else T["text_muted"],
                highlightbackground=T["chip_active_border"] if is_active else T["border_input"]
            )

        self.apply_filters_and_render()

    def open_category_menu(self):
        cats = db.execute_query("SELECT id, name FROM categories ORDER BY name ASC", fetchall=True) or []
        menu = tk.Menu(self, tearoff=0, bg=T["surface"], fg=T["text"], activebackground=T["hover_row"], activeforeground=T["lime"], font=("Segoe UI", 9))

        def select_cat(cat_id, cat_name):
            self.selected_category_id = cat_id
            self.selected_category_name = cat_name
            self.active_chip = "Category"

            # Clear other chips
            for btn in self.chip_buttons.values():
                btn.config(
                    font=("Segoe UI", 9, "normal"),
                    bg=T["surface"],
                    fg=T["text_muted"],
                    highlightbackground=T["border_input"]
                )

            disp_name = (cat_name[:14] + "..") if len(cat_name) > 16 else cat_name
            self.btn_cat_chip.config(
                text=f"{disp_name}  ▾",
                font=("Segoe UI", 9, "bold"),
                bg=T["chip_active_bg"],
                fg=T["text"],
                highlightbackground=T["chip_active_border"]
            )
            self.apply_filters_and_render()

        def select_all_cats():
            self.set_filter_chip("All")

        menu.add_command(label="All Categories", command=select_all_cats)
        menu.add_separator()
        for c in cats:
            menu.add_command(label=c["name"], command=lambda cid=c["id"], cname=c["name"]: select_cat(cid, cname))

        x = self.btn_cat_chip.winfo_rootx()
        y = self.btn_cat_chip.winfo_rooty() + self.btn_cat_chip.winfo_height()
        menu.tk_popup(x, y)

    # ─────────────────────────────────────────────────────────────────────────
    # Data Loading & KPIs
    # ─────────────────────────────────────────────────────────────────────────

    def update_kpis(self):
        """Calculates real KPI numbers from the database."""
        try:
            today = date.today()
            warn_date = today + timedelta(days=config.EXPIRY_WARN_DAYS)

            total_res = db.execute_query("SELECT COUNT(*) AS c FROM products WHERE is_active = TRUE", fetchone=True)
            low_res = db.execute_query("SELECT COUNT(*) AS c FROM products WHERE is_active = TRUE AND stock_qty <= reorder_level", fetchone=True)
            cats_res = db.execute_query("SELECT COUNT(*) AS c FROM categories", fetchone=True)
            exp_res = db.execute_query("SELECT COUNT(*) AS c FROM products WHERE is_active = TRUE AND expiry_date <= %s AND expiry_date >= %s", (warn_date, today), fetchone=True)

            self.lbl_kpi_total.config(text=str(total_res["c"] if total_res else 0))
            self.lbl_kpi_low.config(text=str(low_res["c"] if low_res else 0))
            self.lbl_kpi_cats.config(text=str(cats_res["c"] if cats_res else 0))
            self.lbl_kpi_exp.config(text=str(exp_res["c"] if exp_res else 0))
        except Exception:
            pass

    def load_products(self):
        """Fetches active products from database into memory."""
        query = """
            SELECT p.id, p.sku, p.name, c.name as category_name, p.category_id, p.supplier_id,
                   p.cost_price, p.selling_price, p.stock_qty, p.reorder_level, 
                   p.expiry_date, p.unit
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
            ORDER BY p.name ASC
        """
        try:
            self._all_products_cache = db.execute_query(query, fetchall=True) or []
        except Exception:
            self._all_products_cache = []

        self.apply_filters_and_render()

    def apply_filters_and_render(self):
        """Filters catalog by search text, chips, and category."""
        search_raw = self.ent_search.get().strip().lower()
        if search_raw == "search name, sku or category":
            search_raw = ""

        today = date.today()
        warn_date = today + timedelta(days=config.EXPIRY_WARN_DAYS)

        filtered = []
        for p in self._all_products_cache:
            name = (p["name"] or "").lower()
            sku = (p["sku"] or "").lower()
            cat = (p["category_name"] or "").lower()

            # Search text match
            if search_raw:
                if search_raw not in name and search_raw not in sku and search_raw not in cat:
                    continue

            # Chip filters
            if self.active_chip == "Low stock":
                if p["stock_qty"] > p["reorder_level"]:
                    continue
            elif self.active_chip == "Expiring soon":
                exp = p["expiry_date"]
                if hasattr(exp, "date"):
                    exp = exp.date()
                if not (isinstance(exp, date) and today <= exp <= warn_date):
                    continue
            elif self.active_chip == "Category" and self.selected_category_id is not None:
                if p.get("category_id") != self.selected_category_id:
                    continue

            filtered.append(p)

        # Sorting
        def sort_key(item):
            col = self.sort_col
            if col == "name":
                return (item["name"] or "").lower()
            elif col == "category":
                return (item["category_name"] or "").lower()
            elif col == "stock":
                return item["stock_qty"]
            elif col == "cost":
                return float(item["cost_price"] or 0)
            elif col == "price":
                return float(item["selling_price"] or 0)
            elif col == "expiry":
                exp = item["expiry_date"]
                return str(exp) if exp else ""
            elif col == "status":
                return 1 if item["stock_qty"] <= item["reorder_level"] else 0
            return (item["name"] or "").lower()

        filtered.sort(key=sort_key, reverse=self.sort_desc)
        self._displayed_products = filtered
        self.render_table_rows()

    # ─────────────────────────────────────────────────────────────────────────
    # Table Rendering: Checkbox, Progress Bar, Badges, Row Actions
    # ─────────────────────────────────────────────────────────────────────────

    def render_table_rows(self):
        for widget in self.table_inner.winfo_children():
            widget.destroy()

        total_count = len(self._all_products_cache)
        disp_count = len(self._displayed_products)
        self.lbl_prod_count.config(text=f"Showing {disp_count} of {total_count} products")

        if not self._displayed_products:
            empty_lbl = tk.Label(
                self.table_inner,
                text="No products found matching the current filters.",
                font=("Segoe UI", 11),
                bg=T["surface"],
                fg=T["text_muted"],
                pady=60
            )
            empty_lbl.pack(fill="x", expand=True)
            return

        today = date.today()
        warn_date = today + timedelta(days=config.EXPIRY_WARN_DAYS)

        for prod in self._displayed_products:
            pid = prod["id"]
            stock = prod["stock_qty"]
            reorder = max(1, prod["reorder_level"])
            is_low = stock <= reorder

            # Determine status badge text and colors
            if stock <= 0:
                badge_bg = T["danger_badge_bg"]
                badge_fg = T["danger_badge_text"]
                status_txt = "Out of stock"
            elif is_low:
                badge_bg = T["danger_badge_bg"]
                badge_fg = T["danger_badge_text"]
                status_txt = "Low stock"
            else:
                badge_bg = T["success_badge_bg"]
                badge_fg = T["success_badge_text"]
                status_txt = "In stock"

            # Check expiry
            exp_date = prod["expiry_date"]
            if hasattr(exp_date, "strftime"):
                exp_str = exp_date.strftime("%Y-%m-%d")
            else:
                exp_str = str(exp_date or "N/A")

            # Base row background (danger row tint #1F1620 for low stock)
            base_bg = T["danger_row"] if is_low else T["surface"]
            is_checked = pid in self.selected_ids

            row_frame = tk.Frame(self.table_inner, bg=base_bg, height=54)
            row_frame.pack(fill="x", side="top")
            row_frame.pack_propagate(False)

            # Checkbox
            chk_lbl = tk.Label(
                row_frame,
                text="☑" if is_checked else "☐",
                font=("Segoe UI", 12, "bold"),
                bg=base_bg,
                fg=T["lime"] if is_checked else T["border_input"],
                width=3,
                cursor="hand2"
            )
            chk_lbl.pack(side="left", padx=(10, 4))
            chk_lbl.bind("<Button-1>", lambda e, p_id=pid: self.toggle_row_check(p_id))

            # Column 1: PRODUCT (Name bold + SKU below muted)
            f_prod = tk.Frame(row_frame, bg=base_bg, width=260)
            f_prod.pack(side="left", fill="y")
            f_prod.pack_propagate(False)

            p_box = tk.Frame(f_prod, bg=base_bg)
            p_box.pack(fill="both", expand=True, padx=8, pady=6)

            tk.Label(
                p_box,
                text=prod["name"],
                font=("Segoe UI", 10, "bold"),
                bg=base_bg,
                fg=T["text"],
                anchor="w"
            ).pack(fill="x")

            tk.Label(
                p_box,
                text=prod.get("sku", ""),
                font=("Segoe UI", 8),
                bg=base_bg,
                fg=T["text_muted"],
                anchor="w"
            ).pack(fill="x")

            # Column 2: CATEGORY (Pill tag)
            f_cat = tk.Frame(row_frame, bg=base_bg, width=160)
            f_cat.pack(side="left", fill="y")
            f_cat.pack_propagate(False)

            cat_pill = tk.Frame(
                f_cat,
                bg="#172338",
                highlightbackground=T["border_input"],
                highlightthickness=1,
                padx=8,
                pady=2
            )
            cat_pill.pack(side="left", padx=8, pady=12)

            cat_name = prod.get("category_name") or "Unassigned"
            cat_short = (cat_name[:18] + "..") if len(cat_name) > 20 else cat_name
            tk.Label(
                cat_pill,
                text=cat_short,
                font=("Segoe UI", 8),
                bg="#172338",
                fg=T["text"]
            ).pack()

            # Column 3: STOCK VS. REORDER (Stock bold + / min muted + 5px progress bar)
            f_stock = tk.Frame(row_frame, bg=base_bg, width=170)
            f_stock.pack(side="left", fill="y")
            f_stock.pack_propagate(False)

            s_box = tk.Frame(f_stock, bg=base_bg)
            s_box.pack(fill="both", expand=True, padx=8, pady=6)

            s_text_row = tk.Frame(s_box, bg=base_bg)
            s_text_row.pack(fill="x", anchor="w")

            tk.Label(
                s_text_row,
                text=str(stock),
                font=("Segoe UI", 10, "bold"),
                bg=base_bg,
                fg=T["text"]
            ).pack(side="left")

            tk.Label(
                s_text_row,
                text=f"  / {reorder} min",
                font=("Segoe UI", 8),
                bg=base_bg,
                fg=T["text_muted"]
            ).pack(side="left")

            # 5px Progress bar Canvas
            bar_canvas = tk.Canvas(s_box, height=5, width=130, bg=base_bg, bd=0, highlightthickness=0)
            bar_canvas.pack(anchor="w", pady=(4, 0))

            fill_pct = min(1.0, max(0.0, float(stock) / float(reorder * 10.0)))
            fill_w = int(130 * fill_pct)
            bar_col = T["danger_bar"] if is_low else T["lime"]

            # Draw track
            bar_canvas.create_rectangle(0, 0, 130, 5, fill=T["border_card"], outline="")
            # Draw fill
            if fill_w > 0:
                bar_canvas.create_rectangle(0, 0, fill_w, 5, fill=bar_col, outline="")

            # Column 4: COST
            f_cost = tk.Frame(row_frame, bg=base_bg, width=90)
            f_cost.pack(side="left", fill="y")
            f_cost.pack_propagate(False)

            tk.Label(
                f_cost,
                text=f"${float(prod['cost_price']):.2f}",
                font=("Segoe UI", 9),
                bg=base_bg,
                fg=T["text_muted"],
                anchor="e"
            ).pack(fill="both", expand=True, padx=8)

            # Column 5: PRICE
            f_price = tk.Frame(row_frame, bg=base_bg, width=90)
            f_price.pack(side="left", fill="y")
            f_price.pack_propagate(False)

            tk.Label(
                f_price,
                text=f"${float(prod['selling_price']):.2f}",
                font=("Segoe UI", 10, "bold"),
                bg=base_bg,
                fg=T["text"],
                anchor="e"
            ).pack(fill="both", expand=True, padx=8)

            # Column 6: EXPIRY
            f_exp = tk.Frame(row_frame, bg=base_bg, width=110)
            f_exp.pack(side="left", fill="y")
            f_exp.pack_propagate(False)

            tk.Label(
                f_exp,
                text=exp_str,
                font=("Segoe UI", 9),
                bg=base_bg,
                fg=T["text"],
                anchor="center"
            ).pack(fill="both", expand=True, padx=8)

            # Column 7: UNIT
            f_unit = tk.Frame(row_frame, bg=base_bg, width=70)
            f_unit.pack(side="left", fill="y")
            f_unit.pack_propagate(False)

            tk.Label(
                f_unit,
                text=prod.get("unit") or "piece",
                font=("Segoe UI", 9),
                bg=base_bg,
                fg=T["text_muted"],
                anchor="center"
            ).pack(fill="both", expand=True, padx=4)

            # Column 8: STATUS BADGE
            f_status = tk.Frame(row_frame, bg=base_bg, width=120)
            f_status.pack(side="left", fill="y")
            f_status.pack_propagate(False)

            badge_box = tk.Frame(f_status, bg=badge_bg, padx=10, pady=3)
            badge_box.pack(anchor="center", pady=13)

            tk.Label(
                badge_box,
                text=status_txt,
                font=("Segoe UI", 8, "bold"),
                bg=badge_bg,
                fg=badge_fg
            ).pack()

            # Column 9: ROW ACTIONS (Edit, Stock In/Out)
            f_actions = tk.Frame(row_frame, bg=base_bg, width=90)
            f_actions.pack(side="left", fill="y")
            f_actions.pack_propagate(False)

            btn_edit = tk.Button(
                f_actions,
                text="✎",
                font=("Segoe UI", 10, "bold"),
                bg=T["surface"],
                fg=T["text_muted"],
                activebackground=T["hover_row"],
                activeforeground=T["lime"],
                relief="flat",
                bd=0,
                cursor="hand2",
                width=2,
                command=lambda p_id=pid: self.open_edit_product_modal(p_id)
            )
            btn_edit.pack(side="left", padx=(8, 4), pady=11)

            btn_stock_row = tk.Button(
                f_actions,
                text="↕",
                font=("Segoe UI", 11, "bold"),
                bg=T["surface"],
                fg=T["text_muted"],
                activebackground=T["hover_row"],
                activeforeground=T["lime"],
                relief="flat",
                bd=0,
                cursor="hand2",
                width=2,
                command=lambda p_id=pid: self.open_stock_movement_modal(p_id)
            )
            btn_stock_row.pack(side="left", padx=4, pady=11)

            # 1px Bottom Divider
            divider = tk.Frame(self.table_inner, height=1, bg=T["border_card"])
            divider.pack(fill="x")

            # Row Hover & Selection Click Handlers
            def on_enter(e, rf=row_frame, is_l=is_low, p_id=pid):
                if p_id not in self.selected_ids:
                    rf.config(bg=T["hover_row"])

            def on_leave(e, rf=row_frame, is_l=is_low, p_id=pid):
                if p_id in self.selected_ids:
                    rf.config(bg=T["selected_row"])
                else:
                    rf.config(bg=T["danger_row"] if is_l else T["surface"])

            def on_row_click(e, p_id=pid):
                self.last_clicked_row_id = p_id

            row_frame.bind("<Enter>", on_enter)
            row_frame.bind("<Leave>", on_leave)
            row_frame.bind("<Button-1>", on_row_click)

        # Update header checkbox status
        self._update_selection_state()

    # ─────────────────────────────────────────────────────────────────────────
    # Selection & Bulk Actions
    # ─────────────────────────────────────────────────────────────────────────

    def toggle_row_check(self, prod_id):
        if prod_id in self.selected_ids:
            self.selected_ids.remove(prod_id)
        else:
            self.selected_ids.add(prod_id)
        self.render_table_rows()

    def toggle_select_all(self):
        visible_ids = {p["id"] for p in self._displayed_products}
        if visible_ids.issubset(self.selected_ids) and len(visible_ids) > 0:
            self.selected_ids.difference_update(visible_ids)
        else:
            self.selected_ids.update(visible_ids)
        self.render_table_rows()

    def clear_selection(self):
        self.selected_ids.clear()
        self.render_table_rows()

    def _update_selection_state(self):
        count = len(self.selected_ids)
        visible_ids = {p["id"] for p in self._displayed_products}

        if visible_ids and visible_ids.issubset(self.selected_ids):
            self.btn_header_chk.config(text="☑", fg=T["lime"])
        else:
            self.btn_header_chk.config(text="☐", fg=T["text_muted"])

        if count > 0:
            self.lbl_bulk_info.config(text=f"✓  {count} product(s) selected")
            if hasattr(self, "btn_bulk_del"):
                self.btn_bulk_del.config(text=f"🗑  Delete Selected ({count})")
            if not self.bulk_bar.winfo_ismapped():
                self.bulk_bar.pack(fill="x", pady=(0, 10), before=self.table_card)
        else:
            if self.bulk_bar.winfo_ismapped():
                self.bulk_bar.pack_forget()

    def handle_bulk_delete(self):
        count = len(self.selected_ids)
        if count == 0:
            return

        if messagebox.askyesno(
            "Confirm Bulk Deletion",
            f"Are you sure you want to delete {count} selected product(s)?\n\nThis will safely soft-delete them from active catalog."
        ):
            try:
                for pid in list(self.selected_ids):
                    db.execute_query("UPDATE products SET is_active = FALSE WHERE id = %s", (pid,), commit=True)
                    auth.log_audit("PRODUCT_DELETE", f"Soft-deleted product ID {pid}")
                self.selected_ids.clear()
                self.update_kpis()
                self.load_products()
                messagebox.showinfo("Success", f"{count} product(s) successfully deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete products: {e}")

    def handle_toolbar_stock_movement(self):
        if self.selected_ids:
            first_id = next(iter(self.selected_ids))
            self.open_stock_movement_modal(first_id)
        elif self.last_clicked_row_id:
            self.open_stock_movement_modal(self.last_clicked_row_id)
        elif self._displayed_products:
            self.open_stock_movement_modal(self._displayed_products[0]["id"])
        else:
            messagebox.showinfo("Select Product", "No products available to adjust stock.")

    # ─────────────────────────────────────────────────────────────────────────
    # Modals: Add / Edit Product, Stock Movement
    # ─────────────────────────────────────────────────────────────────────────

    def open_add_product_modal(self):
        self.open_product_form("Add New Pharmacy Product")

    def open_edit_product_modal(self, prod_id):
        prod_data = db.execute_query("SELECT * FROM products WHERE id = %s", (prod_id,), fetchone=True)
        if prod_data:
            self.open_product_form("Edit Pharmacy Product", prod_data)

    def open_product_form(self, title, existing_data=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("620x660")
        dlg.configure(bg=T["bg"])
        dlg.transient(self)
        dlg.grab_set()

        categories = db.execute_query("SELECT id, name FROM categories ORDER BY name", fetchall=True) or []
        suppliers = db.execute_query("SELECT id, name FROM suppliers ORDER BY name", fetchall=True) or []

        cat_dict = {c["name"]: c["id"] for c in categories}
        sup_dict = {s["name"]: s["id"] for s in suppliers}

        # Form Header
        tk.Label(
            dlg,
            text=title,
            font=("Segoe UI", 16, "bold"),
            bg=T["bg"],
            fg=T["text"]
        ).pack(pady=(16, 10))

        form_frame = tk.Frame(
            dlg,
            bg=T["surface"],
            padx=25,
            pady=20,
            highlightbackground=T["border_card"],
            highlightthickness=1
        )
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        form_frame.grid_columnconfigure(1, weight=1)

        entries = {}

        def add_field(row, label_text, key, default_val="", is_combo=False, combo_vals=None):
            tk.Label(
                form_frame,
                text=label_text,
                font=("Segoe UI", 9, "bold"),
                bg=T["surface"],
                fg=T["text_muted"]
            ).grid(row=row, column=0, sticky="w", pady=6)

            if is_combo:
                w = ttk.Combobox(form_frame, values=combo_vals or [], state="readonly", width=28)
                if default_val:
                    w.set(default_val)
                elif combo_vals:
                    w.current(0)
            else:
                w = tk.Entry(
                    form_frame,
                    font=("Segoe UI", 10),
                    bg=T["surface_header"],
                    fg=T["text"],
                    insertbackground=T["text"],
                    highlightbackground=T["border_input"],
                    highlightthickness=1,
                    relief="flat"
                )
                w.insert(0, str(default_val))

            w.grid(row=row, column=1, sticky="ew", pady=6, padx=(12, 0), ipady=4)
            entries[key] = w

        current_cat_name = ""
        current_sup_name = ""
        if existing_data:
            for c_name, c_id in cat_dict.items():
                if c_id == existing_data["category_id"]:
                    current_cat_name = c_name
            for s_name, s_id in sup_dict.items():
                if s_id == existing_data["supplier_id"]:
                    current_sup_name = s_name

        add_field(0, "SKU Code *", "sku", existing_data["sku"] if existing_data else f"SKU-{int(datetime.now().timestamp())%100000}")
        add_field(1, "Product Name *", "name", existing_data["name"] if existing_data else "")
        add_field(2, "Category *", "category", current_cat_name, is_combo=True, combo_vals=list(cat_dict.keys()))
        add_field(3, "Supplier", "supplier", current_sup_name, is_combo=True, combo_vals=["None"] + list(sup_dict.keys()))
        add_field(4, "Cost Price ($) *", "cost", existing_data["cost_price"] if existing_data else "1.00")
        add_field(5, "Selling Price ($) *", "price", existing_data["selling_price"] if existing_data else "2.50")
        add_field(6, "Initial Stock *", "stock", existing_data["stock_qty"] if existing_data else "50")
        add_field(7, "Reorder Level *", "reorder", existing_data["reorder_level"] if existing_data else "15")

        exp_val = existing_data["expiry_date"].strftime("%Y-%m-%d") if existing_data and hasattr(existing_data["expiry_date"], "strftime") else (str(existing_data["expiry_date"]) if existing_data else (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"))
        add_field(8, "Expiry (YYYY-MM-DD) *", "expiry", exp_val)
        add_field(9, "Unit (piece/box/strip)", "unit", existing_data["unit"] if existing_data else "piece")

        def regenerate_prices():
            cat_name = entries["category"].get()
            if not cat_name:
                return
            cat_id = cat_dict.get(cat_name)
            new_cost, new_sell = generate_category_prices(cat_name, cat_id)
            entries["cost"].delete(0, "end")
            entries["cost"].insert(0, new_cost)
            entries["price"].delete(0, "end")
            entries["price"].insert(0, new_sell)

        btn_regen = tk.Button(
            form_frame,
            text="↻ Auto Price",
            font=("Segoe UI", 8, "bold"),
            bg=T["surface_header"],
            fg=T["lime"],
            activebackground=T["hover_row"],
            activeforeground=T["lime"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=4,
            highlightbackground=T["border_input"],
            highlightthickness=1,
            command=regenerate_prices
        )
        btn_regen.grid(row=4, column=2, rowspan=2, padx=(8, 0), sticky="ns", pady=6)

        if existing_data is None:
            regenerate_prices()
            entries["category"].bind("<<ComboboxSelected>>", lambda e: regenerate_prices())

        def save():
            sku = entries["sku"].get().strip()
            name = entries["name"].get().strip()
            cat_name = entries["category"].get()
            sup_name = entries["supplier"].get()
            unit = entries["unit"].get().strip() or "piece"

            if not sku or not name or not cat_name:
                messagebox.showerror("Validation Error", "SKU, Product Name, and Category are required.", parent=dlg)
                return

            try:
                cost = float(entries["cost"].get())
                price = float(entries["price"].get())
                stock = int(entries["stock"].get())
                reorder = int(entries["reorder"].get())
                if cost < 0 or price < 0 or stock < 0 or reorder < 0:
                    raise ValueError("Numeric values must be positive.")
            except ValueError as ve:
                messagebox.showerror("Validation Error", f"Invalid numeric field: {ve}", parent=dlg)
                return

            try:
                exp_date = datetime.strptime(entries["expiry"].get().strip(), "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Validation Error", "Expiry date must be in YYYY-MM-DD format.", parent=dlg)
                return

            cat_id = cat_dict.get(cat_name)
            sup_id = sup_dict.get(sup_name) if sup_name != "None" else None

            try:
                if existing_data:
                    db.execute_query("""
                        UPDATE products
                        SET sku = %s, name = %s, category_id = %s, supplier_id = %s, cost_price = %s,
                            selling_price = %s, stock_qty = %s, reorder_level = %s, expiry_date = %s, unit = %s
                        WHERE id = %s
                    """, (sku, name, cat_id, sup_id, cost, price, stock, reorder, exp_date, unit, existing_data["id"]), commit=True)
                    auth.log_audit("PRODUCT_UPDATE", f"Updated product ID {existing_data['id']}: {name} (SKU: {sku})")
                    messagebox.showinfo("Success", f"Product '{name}' updated successfully!", parent=dlg)
                else:
                    new_id = db.execute_query("""
                        INSERT INTO products (sku, name, category_id, supplier_id, cost_price, selling_price, stock_qty, reorder_level, expiry_date, unit)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (sku, name, cat_id, sup_id, cost, price, stock, reorder, exp_date, unit), commit=True)
                    if stock > 0:
                        db.execute_query("""
                            INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
                            VALUES (%s, 'IN', %s, 'Initial inventory stock on creation', %s)
                        """, (new_id, stock, auth.SessionManager.get_user_id()), commit=True)
                    auth.log_audit("PRODUCT_CREATE", f"Created product: {name} (SKU: {sku}, Qty: {stock})")
                    messagebox.showinfo("Success", f"Product '{name}' added successfully!", parent=dlg)

                dlg.destroy()
                self.update_kpis()
                self.load_products()
            except Exception as ex:
                messagebox.showerror("Database Error", f"Failed to save product: {ex}", parent=dlg)

        btn_save = tk.Button(
            dlg,
            text="💾  Save Product",
            font=("Segoe UI", 10, "bold"),
            bg=T["lime"],
            fg=T["lime_text"],
            activebackground="#84cc16",
            activeforeground=T["lime_text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=24,
            pady=10,
            command=save
        )
        btn_save.pack(pady=(0, 16))

    def open_stock_movement_modal(self, prod_id):
        prod = db.execute_query("SELECT id, name, stock_qty, sku FROM products WHERE id = %s", (prod_id,), fetchone=True)
        if not prod:
            messagebox.showinfo("Error", "Product not found.")
            return

        prod_name = prod["name"]
        current_stock = int(prod["stock_qty"])

        dlg = tk.Toplevel(self)
        dlg.title(f"Stock Movement - {prod_name}")
        dlg.geometry("480x420")
        dlg.configure(bg=T["bg"])
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(
            dlg,
            text="Stock In / Out Adjustment",
            font=("Segoe UI", 15, "bold"),
            bg=T["bg"],
            fg=T["text"]
        ).pack(pady=(16, 10))

        card = tk.Frame(
            dlg,
            bg=T["surface"],
            padx=22,
            pady=18,
            highlightbackground=T["border_card"],
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        tk.Label(card, text=f"Product: {prod_name} ({prod['sku']})", font=("Segoe UI", 10, "bold"), bg=T["surface"], fg=T["text"]).pack(anchor="w", pady=2)
        tk.Label(card, text=f"Current Stock: {current_stock}", font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["lime"]).pack(anchor="w", pady=(0, 12))

        tk.Label(card, text="Movement Type:", font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["text_muted"]).pack(anchor="w", pady=2)
        combo_type = ttk.Combobox(card, values=["IN (Restock / Supplier Delivery)", "OUT (Damaged / Expired / Return)", "ADJUSTMENT (Audit Correction)"], state="readonly")
        combo_type.current(0)
        combo_type.pack(fill="x", pady=(0, 12))

        tk.Label(card, text="Quantity Change:", font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["text_muted"]).pack(anchor="w", pady=2)
        ent_qty = tk.Entry(
            card,
            font=("Segoe UI", 10),
            bg=T["surface_header"],
            fg=T["text"],
            insertbackground=T["text"],
            highlightbackground=T["border_input"],
            highlightthickness=1,
            relief="flat"
        )
        ent_qty.pack(fill="x", pady=(0, 12), ipady=4)
        ent_qty.insert(0, "10")

        tk.Label(card, text="Reference / Reason Note:", font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["text_muted"]).pack(anchor="w", pady=2)
        ent_note = tk.Entry(
            card,
            font=("Segoe UI", 10),
            bg=T["surface_header"],
            fg=T["text"],
            insertbackground=T["text"],
            highlightbackground=T["border_input"],
            highlightthickness=1,
            relief="flat"
        )
        ent_note.pack(fill="x", pady=(0, 12), ipady=4)
        ent_note.insert(0, "PO-Replenishment")

        def submit_movement():
            try:
                qty = int(ent_qty.get())
                if qty <= 0:
                    raise ValueError("Quantity must be greater than zero.")
            except ValueError as ve:
                messagebox.showerror("Error", f"Invalid quantity: {ve}", parent=dlg)
                return

            m_val = combo_type.get()
            m_type = "IN" if m_val.startswith("IN") else ("OUT" if m_val.startswith("OUT") else "ADJUSTMENT")
            note = ent_note.get().strip()

            new_stock = current_stock
            if m_type == "IN":
                new_stock += qty
            elif m_type == "OUT":
                if qty > current_stock:
                    messagebox.showerror("Error", f"Cannot stock out {qty} units; only {current_stock} currently in stock.", parent=dlg)
                    return
                new_stock -= qty
            elif m_type == "ADJUSTMENT":
                new_stock = qty

            db.execute_query("UPDATE products SET stock_qty = %s WHERE id = %s", (new_stock, prod_id), commit=True)
            db.execute_query("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (prod_id, m_type, qty, note, auth.SessionManager.get_user_id()), commit=True)

            auth.log_audit("STOCK_MOVEMENT", f"{m_type} {qty} units for {prod_name}. New stock: {new_stock}. Note: {note}")
            messagebox.showinfo("Success", f"Stock movement recorded! New stock: {new_stock}", parent=dlg)
            dlg.destroy()
            self.update_kpis()
            self.load_products()
            self.load_movements()

        btn_confirm = tk.Button(
            dlg,
            text="Confirm Movement",
            font=("Segoe UI", 10, "bold"),
            bg=T["lime"],
            fg=T["lime_text"],
            activebackground="#84cc16",
            activeforeground=T["lime_text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8,
            command=submit_movement
        )
        btn_confirm.pack(pady=(0, 16))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Stock Movements Tab (Audit History)
    # ─────────────────────────────────────────────────────────────────────────

    def setup_movements_view(self):
        top_bar = tk.Frame(
            self.view_movements,
            bg=T["surface"],
            padx=18,
            pady=12,
            highlightbackground=T["border_card"],
            highlightthickness=1
        )
        top_bar.pack(fill="x", pady=(0, 14))

        tk.Label(
            top_bar,
            text="Audit History of Inventory Stock Movements",
            font=("Segoe UI", 12, "bold"),
            bg=T["surface"],
            fg=T["text"]
        ).pack(side="left")

        btn_ref = tk.Button(
            top_bar,
            text="↻ Refresh Log",
            font=("Segoe UI", 9, "bold"),
            bg=T["tab_active_bg"],
            fg=T["lime"],
            activebackground=T["hover_row"],
            activeforeground=T["lime"],
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            highlightbackground=T["border_input"],
            highlightthickness=1,
            command=self.load_movements
        )
        btn_ref.pack(side="right")

        # Movements Table Card
        move_card = tk.Frame(self.view_movements, bg=T["surface"], highlightbackground=T["border_card"], highlightthickness=1)
        move_card.pack(fill="both", expand=True)

        cols = ("id", "date", "sku", "product", "type", "qty", "note", "user")
        self.move_tree = ttk.Treeview(move_card, columns=cols, show="headings", selectmode="browse")

        self.move_tree.heading("id", text="ID")
        self.move_tree.heading("date", text="Timestamp")
        self.move_tree.heading("sku", text="SKU")
        self.move_tree.heading("product", text="Product Name")
        self.move_tree.heading("type", text="Movement Type")
        self.move_tree.heading("qty", text="Quantity")
        self.move_tree.heading("note", text="Reference / Note")
        self.move_tree.heading("user", text="Logged By")

        self.move_tree.column("id", width=50, anchor="center")
        self.move_tree.column("date", width=140, anchor="center")
        self.move_tree.column("sku", width=90, anchor="center")
        self.move_tree.column("product", width=240, anchor="w")
        self.move_tree.column("type", width=100, anchor="center")
        self.move_tree.column("qty", width=80, anchor="center")
        self.move_tree.column("note", width=220, anchor="w")
        self.move_tree.column("user", width=130, anchor="w")

        scroll_y = ttk.Scrollbar(move_card, orient="vertical", command=self.move_tree.yview)
        self.move_tree.configure(yscrollcommand=scroll_y.set)
        self.move_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

    def load_movements(self):
        if not hasattr(self, "move_tree"):
            return
        for item in self.move_tree.get_children():
            self.move_tree.delete(item)

        movements = db.execute_query("""
            SELECT sm.id, sm.created_at, p.sku, p.name as prod_name, sm.movement_type, sm.quantity, sm.reference_note, u.username
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN users u ON sm.user_id = u.id
            ORDER BY sm.created_at DESC
            LIMIT 250
        """, fetchall=True) or []

        for m in movements:
            dt_str = m["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(m["created_at"], "strftime") else str(m["created_at"])
            self.move_tree.insert(
                "",
                "end",
                values=(
                    m["id"],
                    dt_str,
                    m["sku"],
                    m["prod_name"],
                    m["movement_type"],
                    m["quantity"],
                    m["reference_note"] or "-",
                    m["username"] or "System"
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Suppliers & Categories Tab
    # ─────────────────────────────────────────────────────────────────────────

    def setup_meta_view(self):
        panes = tk.PanedWindow(self.view_meta, orient="horizontal", bg=T["bg"], bd=0)
        panes.pack(fill="both", expand=True)

        # Left: Categories Card
        frame_cats = tk.Frame(panes, bg=T["surface"], padx=18, pady=16, highlightbackground=T["border_card"], highlightthickness=1)
        panes.add(frame_cats, width=480)

        c_top = tk.Frame(frame_cats, bg=T["surface"])
        c_top.pack(fill="x", pady=(0, 12))

        tk.Label(c_top, text="Categories Management", font=("Segoe UI", 12, "bold"), bg=T["surface"], fg=T["text"]).pack(side="left")

        if self.can_edit:
            btn_add_cat = tk.Button(
                c_top,
                text="+ Add Category",
                font=("Segoe UI", 8, "bold"),
                bg=T["lime"],
                fg=T["lime_text"],
                relief="flat",
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=self.add_category_dialog
            )
            btn_add_cat.pack(side="right")

        cols_c = ("id", "name", "desc")
        self.cat_tree = ttk.Treeview(frame_cats, columns=cols_c, show="headings", selectmode="browse", height=15)
        self.cat_tree.heading("id", text="ID")
        self.cat_tree.heading("name", text="Category Name")
        self.cat_tree.heading("desc", text="Description")
        self.cat_tree.column("id", width=40, anchor="center")
        self.cat_tree.column("name", width=160, anchor="w")
        self.cat_tree.column("desc", width=220, anchor="w")
        self.cat_tree.pack(fill="both", expand=True)

        # Right: Suppliers Card
        frame_sups = tk.Frame(panes, bg=T["surface"], padx=18, pady=16, highlightbackground=T["border_card"], highlightthickness=1)
        panes.add(frame_sups, width=580)

        s_top = tk.Frame(frame_sups, bg=T["surface"])
        s_top.pack(fill="x", pady=(0, 12))

        tk.Label(s_top, text="Suppliers Directory", font=("Segoe UI", 12, "bold"), bg=T["surface"], fg=T["text"]).pack(side="left")

        if self.can_edit:
            btn_add_sup = tk.Button(
                s_top,
                text="+ Add Supplier",
                font=("Segoe UI", 8, "bold"),
                bg=T["lime"],
                fg=T["lime_text"],
                relief="flat",
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=self.add_supplier_dialog
            )
            btn_add_sup.pack(side="right")

        cols_s = ("id", "name", "contact", "phone", "email")
        self.sup_tree = ttk.Treeview(frame_sups, columns=cols_s, show="headings", selectmode="browse", height=15)
        self.sup_tree.heading("id", text="ID")
        self.sup_tree.heading("name", text="Supplier Name")
        self.sup_tree.heading("contact", text="Contact Person")
        self.sup_tree.heading("phone", text="Phone")
        self.sup_tree.heading("email", text="Email")
        self.sup_tree.column("id", width=40, anchor="center")
        self.sup_tree.column("name", width=150, anchor="w")
        self.sup_tree.column("contact", width=110, anchor="w")
        self.sup_tree.column("phone", width=100, anchor="w")
        self.sup_tree.column("email", width=130, anchor="w")
        self.sup_tree.pack(fill="both", expand=True)

    def load_categories(self):
        if not hasattr(self, "cat_tree"):
            return
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        cats = db.execute_query("SELECT id, name, description FROM categories ORDER BY name", fetchall=True) or []
        for c in cats:
            self.cat_tree.insert("", "end", values=(c["id"], c["name"], c["description"] or "-"))

    def load_suppliers(self):
        if not hasattr(self, "sup_tree"):
            return
        for item in self.sup_tree.get_children():
            self.sup_tree.delete(item)
        sups = db.execute_query("SELECT id, name, contact_person, phone, email FROM suppliers ORDER BY name", fetchall=True) or []
        for s in sups:
            self.sup_tree.insert("", "end", values=(s["id"], s["name"], s["contact_person"] or "-", s["phone"] or "-", s["email"] or "-"))

    def add_category_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Category")
        dlg.geometry("420x280")
        dlg.configure(bg=T["bg"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=T["surface"], padx=22, pady=18, highlightbackground=T["border_card"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(card, text="Category Name *", font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["text"]).pack(anchor="w", pady=2)
        ent_name = tk.Entry(card, font=("Segoe UI", 10), bg=T["surface_header"], fg=T["text"], insertbackground=T["text"], highlightbackground=T["border_input"], highlightthickness=1, relief="flat")
        ent_name.pack(fill="x", pady=(0, 12), ipady=4)

        tk.Label(card, text="Description", font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["text_muted"]).pack(anchor="w", pady=2)
        ent_desc = tk.Entry(card, font=("Segoe UI", 10), bg=T["surface_header"], fg=T["text"], insertbackground=T["text"], highlightbackground=T["border_input"], highlightthickness=1, relief="flat")
        ent_desc.pack(fill="x", pady=(0, 16), ipady=4)

        def save():
            name = ent_name.get().strip()
            desc = ent_desc.get().strip()
            if not name:
                messagebox.showerror("Error", "Category name is required.", parent=dlg)
                return
            try:
                db.execute_query("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, desc), commit=True)
                auth.log_audit("CATEGORY_CREATE", f"Created category: {name}")
                messagebox.showinfo("Success", f"Category '{name}' created!", parent=dlg)
                dlg.destroy()
                self.load_categories()
                self.update_kpis()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save category: {e}", parent=dlg)

        btn_save = tk.Button(dlg, text="Save Category", font=("Segoe UI", 9, "bold"), bg=T["lime"], fg=T["lime_text"], activebackground="#84cc16", activeforeground=T["lime_text"], relief="flat", bd=0, padx=16, pady=6, cursor="hand2", command=save)
        btn_save.pack(pady=(0, 16))

    def add_supplier_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Supplier")
        dlg.geometry("450x380")
        dlg.configure(bg=T["bg"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=T["surface"], padx=22, pady=18, highlightbackground=T["border_card"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        fields = [("Supplier Name *", "name"), ("Contact Person", "contact"), ("Phone", "phone"), ("Email", "email")]
        entries = {}
        for lbl, key in fields:
            tk.Label(card, text=lbl, font=("Segoe UI", 9, "bold"), bg=T["surface"], fg=T["text"]).pack(anchor="w", pady=2)
            e = tk.Entry(card, font=("Segoe UI", 10), bg=T["surface_header"], fg=T["text"], insertbackground=T["text"], highlightbackground=T["border_input"], highlightthickness=1, relief="flat")
            e.pack(fill="x", pady=(0, 8), ipady=3)
            entries[key] = e

        def save():
            name = entries["name"].get().strip()
            contact = entries["contact"].get().strip()
            phone = entries["phone"].get().strip()
            email = entries["email"].get().strip()
            if not name:
                messagebox.showerror("Error", "Supplier name is required.", parent=dlg)
                return
            try:
                db.execute_query("INSERT INTO suppliers (name, contact_person, phone, email) VALUES (%s, %s, %s, %s)", (name, contact, phone, email), commit=True)
                auth.log_audit("SUPPLIER_CREATE", f"Created supplier: {name}")
                messagebox.showinfo("Success", f"Supplier '{name}' created!", parent=dlg)
                dlg.destroy()
                self.load_suppliers()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save supplier: {e}", parent=dlg)

        btn_save = tk.Button(dlg, text="Save Supplier", font=("Segoe UI", 9, "bold"), bg=T["lime"], fg=T["lime_text"], activebackground="#84cc16", activeforeground=T["lime_text"], relief="flat", bd=0, padx=16, pady=6, cursor="hand2", command=save)
        btn_save.pack(pady=(0, 16))

    def apply_theme(self):
        """Theme transition callback."""
        self.update_kpis()
        self.render_table_rows()
