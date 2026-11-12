import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageTk
import config
import db
import auth
from theme import SmoothScroller

LOW_STOCK_THRESHOLD = 100
ITEMS_PER_PAGE = 60

# ─────────────────────────────────────────────────────────────────────────────
# Theme & Color Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_pos_palette():
    """Returns color dictionary for current theme matching prompt specs."""
    is_dark = config.get_theme() == "dark"
    if is_dark:
        return {
            "is_dark": True,
            "bg": "#0b1220",
            "card": "#111a2b",
            "border": "#24324a",
            "border_focus": "#14b8a6",
            "text": "#e6edf6",
            "muted": "#93a4bc",
            "subtle": "#64748b",
            "chip": "#172238",
            "chip_active": "#24324a",
            "chip_active_fg": "#ffffff",
            "input": "#0f1829",
            "input_border": "#24324a",
            "teal": "#14b8a6",
            "teal_dark": "#0f766e",
            "teal_text": "#04201d",
            "lime": "#a3e635",
            "lime_text": "#0c1f33",
            "badge_green_bg": "#0d2d30",
            "badge_green_fg": "#5eead4",
            "badge_warn_bg": "#33250d",
            "badge_warn_fg": "#fbbf24",
            "badge_danger_bg": "#3f1515",
            "badge_danger_fg": "#f87171",
            "blue": "#60a5fa",
            "danger": "#f87171",
            "card_active_border": "#14b8a6",
            "totals_bg": "#141f33",
            "stepper_bg": "#172238",
            "stepper_border": "#24324a",
            "divider": "#1e2c44",
        }
    else:
        return {
            "is_dark": False,
            "bg": "#f4f6f8",
            "card": "#ffffff",
            "border": "#e1e7ee",
            "border_focus": "#0f766e",
            "text": "#0f1b2d",
            "muted": "#56667b",
            "subtle": "#94a3b8",
            "chip": "#eef2f6",
            "chip_active": "#0f1b2d",
            "chip_active_fg": "#ffffff",
            "input": "#f8fafc",
            "input_border": "#e1e7ee",
            "teal": "#0f766e",
            "teal_dark": "#0d5c56",
            "teal_text": "#ffffff",
            "lime": "#a3e635",
            "lime_text": "#0c1f33",
            "badge_green_bg": "#e0f4f1",
            "badge_green_fg": "#0f766e",
            "badge_warn_bg": "#fef3c7",
            "badge_warn_fg": "#92400e",
            "badge_danger_bg": "#fee2e2",
            "badge_danger_fg": "#b91c1c",
            "blue": "#1d4ed8",
            "danger": "#dc2626",
            "card_active_border": "#0f766e",
            "totals_bg": "#f8fafc",
            "stepper_bg": "#ffffff",
            "stepper_border": "#e1e7ee",
            "divider": "#e1e7ee",
        }


def split_product_name(full_name: str, fallback_unit: str = ""):
    """Splits full name into product title and strength/form line."""
    full_name = (full_name or "").strip()
    m = re.search(r'\s+(\d.*)$', full_name)
    if m:
        return full_name[:m.start()].strip(), m.group(1).strip()
    m2 = re.search(
        r'\s+(Tablet|Capsule|Syrup|Suspension|Ointment|Cream|Drops|Injection|Spray|Softgel|Chewable.*)$',
        full_name,
        re.IGNORECASE
    )
    if m2:
        return full_name[:m2.start()].strip(), m2.group(1).strip()
    return full_name, (fallback_unit.title() if fallback_unit else "")


# ─────────────────────────────────────────────────────────────────────────────
# Antialiased Icon Generator with Pillow
# ─────────────────────────────────────────────────────────────────────────────

class IconCache:
    """Renders crisp 2x supersampled antialiased icons and caches them."""
    _cache = {}

    @classmethod
    def get(cls, name, size=20, color="#56667b", scale=3):
        key = (name, size, color)
        if key in cls._cache:
            return cls._cache[key]

        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        if name == "search":
            r = int(s * 0.30)
            cx, cy = int(s * 0.40), int(s * 0.40)
            lw = max(2, int(2.2 * scale))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
            hx1 = cx + int(r * 0.707)
            hy1 = cy + int(r * 0.707)
            hx2 = int(s * 0.86)
            hy2 = int(s * 0.86)
            d.line([hx1, hy1, hx2, hy2], fill=color, width=lw)

        elif name == "barcode":
            bars = [(0.10, 0.08), (0.24, 0.06), (0.35, 0.12), (0.52, 0.07), (0.64, 0.10), (0.78, 0.06), (0.88, 0.08)]
            top = int(s * 0.16)
            bottom = int(s * 0.84)
            for pos, width in bars:
                x = int(s * pos)
                w = max(1, int(s * width))
                d.rectangle([x, top, x + w, bottom], fill=color)

        elif name == "check":
            lw = max(2, int(2.4 * scale))
            pts = [(int(s * 0.18), int(s * 0.52)), (int(s * 0.42), int(s * 0.76)), (int(s * 0.84), int(s * 0.26))]
            d.line(pts, fill=color, width=lw, joint="curve")

        elif name == "trash":
            lw = max(1, int(1.8 * scale))
            bx1, by1 = int(s * 0.26), int(s * 0.38)
            bx2, by2 = int(s * 0.74), int(s * 0.88)
            d.rectangle([bx1, by1, bx2, by2], outline=color, width=lw)
            d.line([int(s * 0.18), int(s * 0.32), int(s * 0.82), int(s * 0.32)], fill=color, width=lw)
            d.rectangle([int(s * 0.40), int(s * 0.22), int(s * 0.60), int(s * 0.32)], outline=color, width=lw)
            d.line([int(s * 0.42), int(s * 0.46), int(s * 0.42), int(s * 0.80)], fill=color, width=lw)
            d.line([int(s * 0.58), int(s * 0.46), int(s * 0.58), int(s * 0.80)], fill=color, width=lw)

        elif name == "plus":
            lw = max(2, int(2.5 * scale))
            mid = s // 2
            span = int(s * 0.32)
            d.line([mid - span, mid, mid + span, mid], fill=color, width=lw)
            d.line([mid, mid - span, mid, mid + span], fill=color, width=lw)

        elif name == "minus":
            lw = max(2, int(2.5 * scale))
            mid = s // 2
            span = int(s * 0.32)
            d.line([mid - span, mid, mid + span, mid], fill=color, width=lw)

        final_img = img.resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(final_img)
        cls._cache[key] = photo
        return photo


# ─────────────────────────────────────────────────────────────────────────────
# Reusable UI Components
# ─────────────────────────────────────────────────────────────────────────────

class ToastBanner(tk.Frame):
    """Floating non-blocking notification pill for stock limits or feedback."""
    def __init__(self, parent, **kwargs):
        pal = get_pos_palette()
        super().__init__(parent, bg=pal["badge_warn_bg"], highlightbackground=pal["badge_warn_fg"], highlightthickness=1, padx=12, pady=6, **kwargs)
        self.lbl = tk.Label(self, text="", font=("Segoe UI", 9, "bold"), bg=pal["badge_warn_bg"], fg=pal["badge_warn_fg"])
        self.lbl.pack()
        self._hide_job = None

    def show(self, message, is_error=False, duration_ms=2500):
        pal = get_pos_palette()
        bg = pal["badge_danger_bg"] if is_error else pal["badge_warn_bg"]
        fg = pal["badge_danger_fg"] if is_error else pal["badge_warn_fg"]
        self.config(bg=bg, highlightbackground=fg)
        self.lbl.config(text=message, bg=bg, fg=fg)
        self.lift()
        self.place(relx=0.5, rely=0.03, anchor="n")

        if self._hide_job:
            self.after_cancel(self._hide_job)
        self._hide_job = self.after(duration_ms, self.hide)

    def hide(self):
        self.place_forget()
        self._hide_job = None


class ProductCard(tk.Frame):
    """Card widget for catalog grid item."""
    def __init__(self, parent, product_data, on_add, in_cart_qty=0, **kwargs):
        self.pdata = product_data
        self.on_add = on_add
        self.in_cart_qty = in_cart_qty

        pal = get_pos_palette()
        border_col = pal["card_active_border"] if in_cart_qty > 0 else pal["border"]
        border_thick = 2 if in_cart_qty > 0 else 1

        super().__init__(
            parent,
            bg=pal["card"],
            highlightbackground=border_col,
            highlightthickness=border_thick,
            padx=14,
            pady=12,
            cursor="hand2",
            **kwargs
        )

        self.setup_content()
        self.bind_events()

    def setup_content(self):
        pal = get_pos_palette()
        stock = int(self.pdata.get("stock_qty", 0))
        is_out = stock <= 0
        is_low = 0 < stock < LOW_STOCK_THRESHOLD

        # Top row: SKU on left, stock badge on right
        top_row = tk.Frame(self, bg=pal["card"])
        top_row.pack(fill="x", pady=(0, 6))

        lbl_sku = tk.Label(
            top_row,
            text=self.pdata.get("sku", ""),
            font=("Segoe UI", 9),
            bg=pal["card"],
            fg=pal["muted"]
        )
        lbl_sku.pack(side="left")

        # Stock badge
        if is_out:
            b_bg, b_fg, b_txt = pal["badge_danger_bg"], pal["badge_danger_fg"], "Out of stock"
        elif is_low:
            b_bg, b_fg, b_txt = pal["badge_warn_bg"], pal["badge_warn_fg"], f"Low · {stock} left"
        else:
            b_bg, b_fg, b_txt = pal["badge_green_bg"], pal["badge_green_fg"], f"{stock} in stock"

        badge_frame = tk.Frame(top_row, bg=b_bg, padx=6, pady=2)
        badge_frame.pack(side="right")
        lbl_badge = tk.Label(badge_frame, text=b_txt, font=("Segoe UI", 8, "bold"), bg=b_bg, fg=b_fg)
        lbl_badge.pack()

        # Product Title & Subtitle
        name, form = split_product_name(self.pdata.get("name", ""), self.pdata.get("unit", ""))
        lbl_name = tk.Label(
            self,
            text=name,
            font=("Segoe UI", 11, "bold"),
            bg=pal["card"],
            fg=pal["text"] if not is_out else pal["muted"],
            anchor="w",
            justify="left"
        )
        lbl_name.pack(fill="x", pady=(0, 2))

        lbl_form = tk.Label(
            self,
            text=form,
            font=("Segoe UI", 9),
            bg=pal["card"],
            fg=pal["muted"],
            anchor="w"
        )
        lbl_form.pack(fill="x", pady=(0, 8))

        # Bottom row: Price & in-cart indicator on left, lime '+' on right
        bottom_row = tk.Frame(self, bg=pal["card"])
        bottom_row.pack(fill="x", side="bottom")

        price_box = tk.Frame(bottom_row, bg=pal["card"])
        price_box.pack(side="left", fill="y", anchor="w")

        price_val = float(self.pdata.get("selling_price", 0.0))
        lbl_price = tk.Label(
            price_box,
            text=f"{config.CURRENCY}{price_val:.2f}",
            font=("Segoe UI", 14, "bold"),
            bg=pal["card"],
            fg=pal["text"] if not is_out else pal["muted"]
        )
        lbl_price.pack(anchor="w")

        if self.in_cart_qty > 0:
            lbl_incart = tk.Label(
                price_box,
                text=f"{self.in_cart_qty} in cart",
                font=("Segoe UI", 8, "bold"),
                bg=pal["card"],
                fg=pal["teal"]
            )
            lbl_incart.pack(anchor="w")

        # 40x40 lime '+' button
        btn_add = tk.Button(
            bottom_row,
            text="➕",
            font=("Segoe UI", 12, "bold"),
            bg=pal["lime"] if not is_out else pal["chip"],
            fg=pal["lime_text"] if not is_out else pal["muted"],
            activebackground="#84cc16" if not is_out else pal["chip"],
            activeforeground=pal["lime_text"],
            relief="flat",
            bd=0,
            width=3,
            height=1,
            cursor="hand2" if not is_out else "arrow",
            state="normal" if not is_out else "disabled",
            command=self._handle_click_add
        )
        btn_add.pack(side="right")
        self.btn_add = btn_add

        # Smooth hover feedback on '+' button
        def on_add_enter(e):
            if int(self.pdata.get("stock_qty", 0)) > 0:
                btn_add.config(bg="#bef264")
        def on_add_leave(e):
            if int(self.pdata.get("stock_qty", 0)) > 0:
                p = get_pos_palette()
                btn_add.config(bg=p["lime"])
        btn_add.bind("<Enter>", on_add_enter)
        btn_add.bind("<Leave>", on_add_leave)

    def _handle_click_add(self):
        self.on_add(self.pdata, 1)

    def bind_events(self):
        # Card border hover highlight (if not already active in cart)
        def on_card_enter(e):
            if self.in_cart_qty == 0:
                p = get_pos_palette()
                self.config(highlightbackground=p["border_focus"])
        def on_card_leave(e):
            if self.in_cart_qty == 0:
                p = get_pos_palette()
                self.config(highlightbackground=p["border"])

        self.bind("<Enter>", on_card_enter, add="+")
        self.bind("<Leave>", on_card_leave, add="+")

        # Double-click or click card adds 1 unit
        def on_dbl(e):
            if int(self.pdata.get("stock_qty", 0)) > 0:
                self.on_add(self.pdata, 1)

        def walk_bind(w):
            w.bind("<Double-Button-1>", on_dbl)
            w.bind("<Enter>", on_card_enter, add="+")
            w.bind("<Leave>", on_card_leave, add="+")
            for child in w.winfo_children():
                if not isinstance(child, tk.Button):
                    walk_bind(child)

        walk_bind(self)


class CartLine(tk.Frame):
    """Row widget for cart item line."""
    def __init__(self, parent, item_data, on_qty_change, on_remove, **kwargs):
        pal = get_pos_palette()
        super().__init__(parent, bg=pal["card"], padx=10, pady=8, **kwargs)
        self.item_data = item_data
        self.on_qty_change = on_qty_change
        self.on_remove = on_remove

        self.setup_ui()

    def setup_ui(self):
        pal = get_pos_palette()

        # Left: Product name + unit price
        left_box = tk.Frame(self, bg=pal["card"])
        left_box.pack(side="left", fill="both", expand=True)

        lbl_name = tk.Label(
            left_box,
            text=self.item_data.get("name", ""),
            font=("Segoe UI", 10, "bold"),
            bg=pal["card"],
            fg=pal["text"],
            anchor="w",
            justify="left",
            wraplength=140
        )
        lbl_name.pack(anchor="w")

        price = float(self.item_data.get("price", 0.0))
        lbl_unit = tk.Label(
            left_box,
            text=f"{config.CURRENCY}{price:.2f} each",
            font=("Segoe UI", 8),
            bg=pal["card"],
            fg=pal["muted"]
        )
        lbl_unit.pack(anchor="w")

        # Right-most: Trash button
        btn_del = tk.Button(
            self,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            bg=pal["card"],
            fg=pal["muted"],
            activebackground=pal["card"],
            activeforeground=pal["danger"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=4,
            command=lambda: self.on_remove(self.item_data["product_id"])
        )
        btn_del.pack(side="right", padx=(6, 0))

        # Line total
        total = float(self.item_data.get("line_total", 0.0))
        lbl_tot = tk.Label(
            self,
            text=f"{config.CURRENCY}{total:.2f}",
            font=("Segoe UI", 10, "bold"),
            bg=pal["card"],
            fg=pal["text"],
            width=7,
            anchor="e"
        )
        lbl_tot.pack(side="right", padx=(6, 6))

        # Quantity stepper: [ - ] qty [ + ]
        stepper_box = tk.Frame(self, bg=pal["stepper_bg"], highlightbackground=pal["stepper_border"], highlightthickness=1)
        stepper_box.pack(side="right", padx=(6, 6))

        btn_minus = tk.Button(
            stepper_box,
            text="—",
            font=("Segoe UI", 8, "bold"),
            bg=pal["stepper_bg"],
            fg=pal["text"],
            relief="flat",
            bd=0,
            width=2,
            cursor="hand2",
            command=lambda: self.on_qty_change(self.item_data["product_id"], -1)
        )
        btn_minus.pack(side="left")

        lbl_qty = tk.Label(
            stepper_box,
            text=str(self.item_data.get("qty", 1)),
            font=("Segoe UI", 9, "bold"),
            bg=pal["stepper_bg"],
            fg=pal["text"],
            width=3
        )
        lbl_qty.pack(side="left")

        btn_plus = tk.Button(
            stepper_box,
            text="+",
            font=("Segoe UI", 9, "bold"),
            bg=pal["stepper_bg"],
            fg=pal["text"],
            relief="flat",
            bd=0,
            width=2,
            cursor="hand2",
            command=lambda: self.on_qty_change(self.item_data["product_id"], 1)
        )
        btn_plus.pack(side="left")


# ─────────────────────────────────────────────────────────────────────────────
# Main Redesigned SalesScreen
# ─────────────────────────────────────────────────────────────────────────────

class SalesScreen(tk.Frame):
    def __init__(self, parent, controller):
        pal = get_pos_palette()
        super().__init__(parent, bg=pal["bg"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)
        self.can_pos = auth.SessionManager.has_permission("sales_pos") or self.role in [config.ROLE_ADMIN, config.ROLE_INSTRUCTOR, config.ROLE_SALES_PERSONNEL]

        # Cart state
        self.cart = []  # list of dicts: {"product_id", "sku", "name", "price", "cost", "stock_qty", "qty", "line_total"}
        self.selected_category_id = None  # None = "All", "LOW_STOCK" = low stock
        self.active_discount_pct = 0.0
        self.selected_pay_method = "CASH"

        # Catalog data & responsive layout state
        self._all_catalog_products = []
        self._filtered_catalog_products = []
        self._current_cols = 3
        self._reflow_job = None
        self._search_job = None
        self._categories_list = []

        self.setup_ui()
        self.bind_shortcuts()

    # ─────────────────────────────────────────────────────────────────────────
    # Top Header & View Switcher
    # ─────────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        pal = get_pos_palette()

        # Top Header Bar (1px bottom border)
        header = tk.Frame(
            self,
            bg=pal["card"],
            padx=28,
            pady=16,
            highlightbackground=pal["border"],
            highlightthickness=1
        )
        header.pack(fill="x", side="top")
        self.header_bar = header

        # Left: Title + Subtitle
        h_left = tk.Frame(header, bg=pal["card"])
        h_left.pack(side="left")

        self.lbl_head_title = tk.Label(
            h_left,
            text="Point of Sale",
            font=("Segoe UI", 18, "bold"),
            bg=pal["card"],
            fg=pal["text"]
        )
        self.lbl_head_title.pack(anchor="w")

        self.lbl_head_subtitle = tk.Label(
            h_left,
            text="Ring up a sale, take payment and print the receipt.",
            font=("Segoe UI", 9),
            bg=pal["card"],
            fg=pal["muted"]
        )
        self.lbl_head_subtitle.pack(anchor="w", pady=(1, 0))

        # Right: Segmented Switch [ New sale ] [ Sales & invoices history ]
        switch_frame = tk.Frame(
            header,
            bg=pal["chip"],
            padx=4,
            pady=4,
            highlightbackground=pal["border"],
            highlightthickness=1
        )
        switch_frame.pack(side="right")
        self.switch_frame = switch_frame

        self.btn_tab_pos = tk.Button(
            switch_frame,
            text="New sale",
            font=("Segoe UI", 9, "bold"),
            bg=pal["card"],
            fg=pal["text"],
            relief="flat",
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            command=lambda: self.switch_view("pos")
        )
        self.btn_tab_pos.pack(side="left")

        self.btn_tab_history = tk.Button(
            switch_frame,
            text="Sales & invoices history",
            font=("Segoe UI", 9),
            bg=pal["chip"],
            fg=pal["muted"],
            relief="flat",
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            command=lambda: self.switch_view("history")
        )
        self.btn_tab_history.pack(side="left")

        self._active_view = "pos" if self.can_pos else "history"

        # Smooth hover animations on segmented switch
        def _pos_enter(e):
            if self._active_view != "pos":
                p = get_pos_palette()
                self.btn_tab_pos.config(bg=p["border"], fg=p["text"])
        def _pos_leave(e):
            if self._active_view != "pos":
                p = get_pos_palette()
                self.btn_tab_pos.config(bg=p["chip"], fg=p["muted"])
        self.btn_tab_pos.bind("<Enter>", _pos_enter)
        self.btn_tab_pos.bind("<Leave>", _pos_leave)

        def _hist_enter(e):
            if self._active_view != "history":
                p = get_pos_palette()
                self.btn_tab_history.config(bg=p["border"], fg=p["text"])
        def _hist_leave(e):
            if self._active_view != "history":
                p = get_pos_palette()
                self.btn_tab_history.config(bg=p["chip"], fg=p["muted"])
        self.btn_tab_history.bind("<Enter>", _hist_enter)
        self.btn_tab_history.bind("<Leave>", _hist_leave)

        # Main Content Container
        self.content_container = tk.Frame(self, bg=pal["bg"])
        self.content_container.pack(fill="both", expand=True, padx=24, pady=16)

        # 1. POS View Container (Two Columns: Flexible Left, Fixed Right ~400px)
        self.pos_view = tk.Frame(self.content_container, bg=pal["bg"])
        self.pos_view.grid_columnconfigure(0, weight=1)
        self.pos_view.grid_columnconfigure(1, weight=0, minsize=380)
        self.pos_view.grid_rowconfigure(0, weight=1)

        # 2. History View Container
        self.history_view = tk.Frame(self.content_container, bg=pal["bg"])

        # Setup both sub-views
        self.setup_pos_view()
        self.setup_history_view()

        # Initial view
        if self.can_pos:
            self.switch_view("pos")
        else:
            self.switch_view("history")

    def switch_view(self, view_name):
        self._active_view = view_name
        pal = get_pos_palette()
        if view_name == "pos":
            self.history_view.pack_forget()
            self.pos_view.pack(fill="both", expand=True)

            self.btn_tab_pos.config(bg=pal["card"], fg=pal["text"], font=("Segoe UI", 9, "bold"))
            self.btn_tab_history.config(bg=pal["chip"], fg=pal["muted"], font=("Segoe UI", 9))
            self.load_catalog_products()
        else:
            self.pos_view.pack_forget()
            self.history_view.pack(fill="both", expand=True)

            self.btn_tab_pos.config(bg=pal["chip"], fg=pal["muted"], font=("Segoe UI", 9))
            self.btn_tab_history.config(bg=pal["card"], fg=pal["text"], font=("Segoe UI", 9, "bold"))
            self.load_sales_history()

    # ─────────────────────────────────────────────────────────────────────────
    # POS View Layout: Left Column (Catalog) & Right Column (Cart & Checkout)
    # ─────────────────────────────────────────────────────────────────────────

    def setup_pos_view(self):
        pal = get_pos_palette()

        # ── LEFT COLUMN: Product Catalog ──────────────────────────────────────
        self.col_catalog = tk.Frame(self.pos_view, bg=pal["bg"])
        self.col_catalog.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.col_catalog.grid_rowconfigure(2, weight=1)
        self.col_catalog.grid_columnconfigure(0, weight=1)

        # Floating toast notification
        self.toast = ToastBanner(self.col_catalog)

        # 1. Search Bar (52px high, card background, 1px border, 14px radius look)
        search_card = tk.Frame(
            self.col_catalog,
            bg=pal["card"],
            highlightbackground=pal["border"],
            highlightthickness=1,
            padx=14,
            pady=10
        )
        search_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.search_card = search_card

        # Search icon on left
        self.icon_search = IconCache.get("search", size=18, color=pal["muted"])
        lbl_s_icon = tk.Label(search_card, image=self.icon_search, bg=pal["card"])
        lbl_s_icon.pack(side="left", padx=(0, 10))
        self.lbl_s_icon = lbl_s_icon

        # Search input
        self.ent_search = tk.Entry(
            search_card,
            font=("Segoe UI", 11),
            bg=pal["card"],
            fg=pal["text"],
            insertbackground=pal["text"],
            relief="flat",
            bd=0
        )
        self.ent_search.pack(side="left", fill="x", expand=True)
        self.ent_search.insert(0, "Search by name or SKU, or scan a barcode")
        self.ent_search.bind("<FocusIn>", self._on_search_focus_in)
        self.ent_search.bind("<FocusOut>", self._on_search_focus_out)
        self.ent_search.bind("<KeyRelease>", self._on_search_key)
        self.ent_search.bind("<Return>", self._on_search_enter)

        # Barcode icon on right
        self.icon_barcode = IconCache.get("barcode", size=22, color=pal["muted"])
        lbl_b_icon = tk.Label(search_card, image=self.icon_barcode, bg=pal["card"])
        lbl_b_icon.pack(side="right", padx=(8, 0))
        self.lbl_b_icon = lbl_b_icon

        # 2. Category Chips Bar
        self.chips_frame = tk.Frame(self.col_catalog, bg=pal["bg"])
        self.chips_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.build_category_chips()

        # 3. Product Cards Grid (Scrollable Canvas)
        grid_container = tk.Frame(self.col_catalog, bg=pal["bg"])
        grid_container.grid(row=2, column=0, sticky="nsew")
        grid_container.grid_rowconfigure(0, weight=1)
        grid_container.grid_columnconfigure(0, weight=1)

        self.canvas_catalog = tk.Canvas(grid_container, bg=pal["bg"], bd=0, highlightthickness=0)
        self.canvas_catalog.grid(row=0, column=0, sticky="nsew")

        self.scroll_catalog = ttk.Scrollbar(grid_container, orient="vertical", command=self.canvas_catalog.yview)
        self.scroll_catalog.grid(row=0, column=1, sticky="ns")
        self.canvas_catalog.configure(yscrollcommand=self.scroll_catalog.set)

        self.cards_inner_frame = tk.Frame(self.canvas_catalog, bg=pal["bg"])
        self.canvas_window_id = self.canvas_catalog.create_window((0, 0), window=self.cards_inner_frame, anchor="nw")

        self.cards_inner_frame.bind("<Configure>", lambda e: self.canvas_catalog.configure(scrollregion=self.canvas_catalog.bbox("all")))
        self.canvas_catalog.bind("<Configure>", self._on_catalog_canvas_resize)

        # Smooth momentum scrolling
        self._catalog_scroller = SmoothScroller(self.canvas_catalog, friction=0.82, speed_factor=3.6)
        self._catalog_scroller.attach_hover(self.canvas_catalog, self.cards_inner_frame)

        # 4. Catalog Footer Counter ("Showing X of Y products")
        footer_frame = tk.Frame(self.col_catalog, bg=pal["bg"], pady=6)
        footer_frame.grid(row=3, column=0, sticky="ew")

        self.lbl_catalog_count = tk.Label(
            footer_frame,
            text="Showing 0 of 0 products",
            font=("Segoe UI", 9),
            bg=pal["bg"],
            fg=pal["muted"]
        )
        self.lbl_catalog_count.pack(side="left")

        # ── RIGHT COLUMN: "Current sale" Panel ────────────────────────────────
        self.col_cart = tk.Frame(
            self.pos_view,
            bg=pal["card"],
            highlightbackground=pal["border"],
            highlightthickness=1,
            padx=18,
            pady=16,
            width=400
        )
        self.col_cart.grid(row=0, column=1, sticky="nsew")
        self.col_cart.pack_propagate(False)

        self.setup_cart_panel()

    # ─────────────────────────────────────────────────────────────────────────
    # Category Chips
    # ─────────────────────────────────────────────────────────────────────────

    def build_category_chips(self):
        """Builds rounded pill buttons for category filtering."""
        for w in self.chips_frame.winfo_children():
            w.destroy()

        pal = get_pos_palette()

        # Query categories from database
        try:
            cats = db.execute_query("SELECT id, name FROM categories ORDER BY id ASC", fetchall=True) or []
        except Exception:
            cats = []

        # Short friendly display names
        cat_map = {
            "Analgesics & Antipyretics": "Analgesics",
            "Antibiotics & Antivirals": "Antibiotics",
            "Cardiovascular & Hypertension": "Cardiovascular",
            "Vitamins & Supplements": "Vitamins & Supplements",
            "Gastrointestinal & Digestive": "Gastrointestinal",
            "Antihistamines & Allergy": "Antihistamines",
            "Respiratory & Cough Care": "Respiratory",
            "Topical & First Aid": "First Aid"
        }

        chips = [("All", None)]
        for c in cats:
            name = cat_map.get(c["name"], c["name"][:16])
            chips.append((name, c["id"]))
        chips.append(("Low stock", "LOW_STOCK"))

        self.chip_buttons = {}
        for name, cid in chips:
            is_active = (self.selected_category_id == cid)
            bg = pal["chip_active"] if is_active else pal["chip"]
            fg = pal["chip_active_fg"] if is_active else pal["text"]
            bd_col = pal["chip_active"] if is_active else pal["border"]

            btn = tk.Button(
                self.chips_frame,
                text=name,
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=bg,
                fg=fg,
                activebackground=pal["chip_active"],
                activeforeground=pal["chip_active_fg"],
                relief="flat",
                bd=0,
                padx=12,
                pady=4,
                cursor="hand2",
                highlightbackground=bd_col,
                highlightthickness=1,
                command=lambda target_id=cid: self._on_chip_selected(target_id)
            )
            btn.pack(side="left", padx=(0, 8), pady=2)
            self.chip_buttons[cid] = btn

            if not is_active:
                def _c_enter(e, b=btn):
                    p = get_pos_palette()
                    b.config(bg=p["border"], fg=p["text"])
                def _c_leave(e, b=btn):
                    p = get_pos_palette()
                    b.config(bg=p["chip"], fg=p["text"])
                btn.bind("<Enter>", _c_enter)
                btn.bind("<Leave>", _c_leave)

    def _on_chip_selected(self, category_id):
        self.selected_category_id = category_id
        self.build_category_chips()
        self.filter_products()

    # ─────────────────────────────────────────────────────────────────────────
    # Catalog Search & Filtering
    # ─────────────────────────────────────────────────────────────────────────

    def _on_search_focus_in(self, e):
        if self.ent_search.get() == "Search by name or SKU, or scan a barcode":
            self.ent_search.delete(0, tk.END)
            pal = get_pos_palette()
            self.ent_search.config(fg=pal["text"])

    def _on_search_focus_out(self, e):
        if not self.ent_search.get().strip():
            self.ent_search.insert(0, "Search by name or SKU, or scan a barcode")
            pal = get_pos_palette()
            self.ent_search.config(fg=pal["muted"])

    def _on_search_key(self, e):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(140, self.filter_products)

    def _on_search_enter(self, e):
        """Barcode scanner or quick Enter match: adds item directly to cart."""
        text = self.ent_search.get().strip()
        if not text or text == "Search by name or SKU, or scan a barcode":
            return

        # 1. Exact match on SKU
        exact_sku = next((p for p in self._all_catalog_products if p.get("sku", "").lower() == text.lower()), None)
        if exact_sku:
            self.add_product_to_cart(exact_sku, 1)
            self.ent_search.delete(0, tk.END)
            self.filter_products()
            return

        # 2. If single or filtered match available, add first match
        if self._filtered_catalog_products:
            first = self._filtered_catalog_products[0]
            self.add_product_to_cart(first, 1)
            self.toast.show(f"Added {first.get('name', 'Product')}")

    def load_catalog_products(self):
        """Loads active products from database into memory."""
        query = """
            SELECT id, sku, name, selling_price, stock_qty, cost_price, category_id, unit 
            FROM products 
            WHERE is_active = TRUE
            ORDER BY name ASC
        """
        try:
            self._all_catalog_products = db.execute_query(query, fetchall=True) or []
        except Exception:
            self._all_catalog_products = []

        self.filter_products()

    def filter_products(self):
        """Applies search term and category filters, then renders grid."""
        raw_search = self.ent_search.get().strip()
        if raw_search == "Search by name or SKU, or scan a barcode":
            raw_search = ""
        s = raw_search.lower()

        results = []
        for p in self._all_catalog_products:
            # Category filter
            if self.selected_category_id == "LOW_STOCK":
                if int(p.get("stock_qty", 0)) >= LOW_STOCK_THRESHOLD:
                    continue
            elif self.selected_category_id is not None:
                if p.get("category_id") != self.selected_category_id:
                    continue

            # Text filter
            if s:
                p_name = p.get("name", "").lower()
                p_sku = p.get("sku", "").lower()
                if s not in p_name and s not in p_sku:
                    continue

            results.append(p)

        self._filtered_catalog_products = results
        self.render_product_cards()

    # ─────────────────────────────────────────────────────────────────────────
    # Responsive Grid Rendering
    # ─────────────────────────────────────────────────────────────────────────

    def _on_catalog_canvas_resize(self, event):
        w = event.width
        self.canvas_catalog.itemconfig(self.canvas_window_id, width=w)
        if w < 100:
            return

        gap = 14
        card_min_w = 200
        cols = max(1, (w - gap) // (card_min_w + gap))
        if cols != self._current_cols:
            self._current_cols = cols
            if self._reflow_job:
                self.after_cancel(self._reflow_job)
            self._reflow_job = self.after(80, self.render_product_cards)

    def render_product_cards(self):
        """Re-draws all cards in the responsive grid."""
        for w in self.cards_inner_frame.winfo_children():
            w.destroy()

        pal = get_pos_palette()
        paged_items = self._filtered_catalog_products[:ITEMS_PER_PAGE]
        cols = max(1, self._current_cols)

        for col_idx in range(cols):
            self.cards_inner_frame.grid_columnconfigure(col_idx, weight=1, uniform="col")

        if not paged_items:
            empty_lbl = tk.Label(
                self.cards_inner_frame,
                text="No products found matching your search.",
                font=("Segoe UI", 11),
                bg=pal["bg"],
                fg=pal["muted"],
                pady=40
            )
            empty_lbl.grid(row=0, column=0, columnspan=cols)
        else:
            for idx, prod in enumerate(paged_items):
                r = idx // cols
                c = idx % cols
                # Check in-cart quantity
                in_cart = next((item for item in self.cart if item["product_id"] == prod["id"]), None)
                in_cart_qty = in_cart["qty"] if in_cart else 0

                card = ProductCard(
                    self.cards_inner_frame,
                    product_data=prod,
                    on_add=self.add_product_to_cart,
                    in_cart_qty=in_cart_qty
                )
                card.grid(row=r, column=c, padx=7, pady=7, sticky="nsew")

                if hasattr(self, "_catalog_scroller"):
                    def _attach_cat(w):
                        self._catalog_scroller.attach_hover(w)
                        for ch in w.winfo_children():
                            _attach_cat(ch)
                    _attach_cat(card)

        # Update counter footer
        total_matching = len(self._filtered_catalog_products)
        displayed = len(paged_items)
        self.lbl_catalog_count.config(text=f"Showing {displayed} of {total_matching} products")

    # ─────────────────────────────────────────────────────────────────────────
    # RIGHT COLUMN: "Current sale" Panel
    # ─────────────────────────────────────────────────────────────────────────

    def setup_cart_panel(self):
        pal = get_pos_palette()

        # a) Header row: "Current sale", "X line items · Y units", "Clear cart"
        head_row = tk.Frame(self.col_cart, bg=pal["card"])
        head_row.pack(fill="x", pady=(0, 10))

        h_info = tk.Frame(head_row, bg=pal["card"])
        h_info.pack(side="left")

        self.lbl_cart_title = tk.Label(
            h_info,
            text="Current sale",
            font=("Segoe UI", 13, "bold"),
            bg=pal["card"],
            fg=pal["text"]
        )
        self.lbl_cart_title.pack(anchor="w")

        self.lbl_cart_units = tk.Label(
            h_info,
            text="0 line items · 0 units",
            font=("Segoe UI", 8),
            bg=pal["card"],
            fg=pal["muted"]
        )
        self.lbl_cart_units.pack(anchor="w")

        self.btn_clear_cart = tk.Button(
            head_row,
            text="Clear cart",
            font=("Segoe UI", 9, "bold"),
            bg=pal["card"],
            fg=pal["danger"],
            activebackground=pal["card"],
            activeforeground=pal["danger"],
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.clear_cart
        )
        self.btn_clear_cart.pack(side="right")

        # b) Customer row: "Customer" label + entry field
        cust_box = tk.Frame(self.col_cart, bg=pal["card"])
        cust_box.pack(fill="x", pady=(0, 10))

        tk.Label(
            cust_box,
            text="Customer",
            font=("Segoe UI", 8, "bold"),
            bg=pal["card"],
            fg=pal["muted"]
        ).pack(anchor="w", pady=(0, 2))

        self.ent_customer = tk.Entry(
            cust_box,
            font=("Segoe UI", 10),
            bg=pal["input"],
            fg=pal["text"],
            insertbackground=pal["text"],
            relief="flat",
            highlightbackground=pal["input_border"],
            highlightthickness=1,
            justify="left"
        )
        self.ent_customer.insert(0, "Walk-in Customer")
        self.ent_customer.pack(fill="x", ipady=6)

        # c) Cart lines list (Scrollable)
        cart_scroll_frame = tk.Frame(self.col_cart, bg=pal["card"])
        cart_scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.canvas_cart = tk.Canvas(cart_scroll_frame, bg=pal["card"], bd=0, highlightthickness=0)
        self.canvas_cart.pack(side="left", fill="both", expand=True)

        self.scroll_cart = ttk.Scrollbar(cart_scroll_frame, orient="vertical", command=self.canvas_cart.yview)
        self.scroll_cart.pack(side="right", fill="y")
        self.canvas_cart.configure(yscrollcommand=self.scroll_cart.set)

        self.cart_items_frame = tk.Frame(self.canvas_cart, bg=pal["card"])
        self.cart_window_id = self.canvas_cart.create_window((0, 0), window=self.cart_items_frame, anchor="nw")

        self.cart_items_frame.bind(
            "<Configure>",
            lambda e: self.canvas_cart.configure(scrollregion=self.canvas_cart.bbox("all"))
        )
        self.canvas_cart.bind(
            "<Configure>",
            lambda e: self.canvas_cart.itemconfig(self.cart_window_id, width=e.width)
        )
        self._cart_scroller = SmoothScroller(self.canvas_cart, friction=0.82, speed_factor=3.2)
        self._cart_scroller.attach_hover(self.canvas_cart, self.cart_items_frame)

        # d) Totals Block (Slightly tinted background)
        self.totals_block = tk.Frame(
            self.col_cart,
            bg=pal["totals_bg"],
            highlightbackground=pal["border"],
            highlightthickness=1,
            padx=14,
            pady=12
        )
        self.totals_block.pack(fill="x", side="bottom")

        # 1. Subtotal row
        sub_row = tk.Frame(self.totals_block, bg=pal["totals_bg"])
        sub_row.pack(fill="x", pady=2)

        self.lbl_sub_title = tk.Label(sub_row, text="Subtotal", font=("Segoe UI", 9), bg=pal["totals_bg"], fg=pal["muted"])
        self.lbl_sub_title.pack(side="left")

        self.lbl_subtotal = tk.Label(sub_row, text=f"{config.CURRENCY}0.00", font=("Segoe UI", 10, "bold"), bg=pal["totals_bg"], fg=pal["text"])
        self.lbl_subtotal.pack(side="right")

        # 2. Discount row: pills 0% / 5% / 10% / 20%
        disc_row = tk.Frame(self.totals_block, bg=pal["totals_bg"])
        disc_row.pack(fill="x", pady=(4, 6))

        self.lbl_disc_title = tk.Label(disc_row, text="Discount", font=("Segoe UI", 9), bg=pal["totals_bg"], fg=pal["muted"])
        self.lbl_disc_title.pack(side="left")

        self.disc_buttons = {}
        for pct in [0, 5, 10, 20]:
            is_sel = (self.active_discount_pct == pct)
            btn = tk.Button(
                disc_row,
                text=f"{pct}%",
                font=("Segoe UI", 8, "bold" if is_sel else "normal"),
                bg=pal["teal"] if is_sel else pal["chip"],
                fg=pal["teal_text"] if is_sel else pal["text"],
                relief="flat",
                bd=0,
                padx=6,
                pady=2,
                cursor="hand2",
                command=lambda p=pct: self.set_discount_pct(p)
            )
            btn.pack(side="left", padx=(6, 0))
            self.disc_buttons[pct] = btn

            def _d_ent(e, b=btn, p_val=pct):
                if self.active_discount_pct != p_val:
                    p = get_pos_palette()
                    b.config(bg=p["border"])
            def _d_lve(e, b=btn, p_val=pct):
                if self.active_discount_pct != p_val:
                    p = get_pos_palette()
                    b.config(bg=p["chip"])
            btn.bind("<Enter>", _d_ent)
            btn.bind("<Leave>", _d_lve)

        # Custom discount button
        self.btn_disc_custom = tk.Button(
            disc_row,
            text="Custom",
            font=("Segoe UI", 8),
            bg=pal["chip"],
            fg=pal["text"],
            relief="flat",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._prompt_custom_discount
        )
        self.btn_disc_custom.pack(side="right")

        def _dc_ent(e):
            if self.active_discount_pct in [0, 5, 10, 20]:
                p = get_pos_palette()
                self.btn_disc_custom.config(bg=p["border"])
        def _dc_lve(e):
            if self.active_discount_pct in [0, 5, 10, 20]:
                p = get_pos_palette()
                self.btn_disc_custom.config(bg=p["chip"])
        self.btn_disc_custom.bind("<Enter>", _dc_ent)
        self.btn_disc_custom.bind("<Leave>", _dc_lve)

        # Divider line
        div1 = tk.Frame(self.totals_block, height=1, bg=pal["divider"])
        div1.pack(fill="x", pady=6)

        # 3. Total Due row: "Total due" on left, amount in 24px bold teal on right
        tot_row = tk.Frame(self.totals_block, bg=pal["totals_bg"])
        tot_row.pack(fill="x", pady=2)

        self.lbl_tot_title = tk.Label(tot_row, text="Total due", font=("Segoe UI", 11, "bold"), bg=pal["totals_bg"], fg=pal["text"])
        self.lbl_tot_title.pack(side="left")

        self.lbl_total = tk.Label(
            tot_row,
            text=f"{config.CURRENCY}0.00",
            font=("Segoe UI", 20, "bold"),
            bg=pal["totals_bg"],
            fg=pal["teal"]
        )
        self.lbl_total.pack(side="right")

        # Payment method is exclusively CASH (Card & E-wallet removed per requirement)
        self.selected_pay_method = "CASH"
        self.pay_method_buttons = {}

        # 5. Amount paid entry & Change display
        cash_row = tk.Frame(self.totals_block, bg=pal["totals_bg"])
        cash_row.pack(fill="x", pady=(2, 6))

        p_left = tk.Frame(cash_row, bg=pal["totals_bg"])
        p_left.pack(side="left", fill="x", expand=True)

        tk.Label(p_left, text="Amount paid", font=("Segoe UI", 8), bg=pal["totals_bg"], fg=pal["muted"]).pack(anchor="w")
        self.ent_paid = tk.Entry(
            p_left,
            font=("Segoe UI", 11, "bold"),
            bg=pal["input"],
            fg=pal["text"],
            insertbackground=pal["text"],
            relief="flat",
            highlightbackground=pal["input_border"],
            highlightthickness=1,
            justify="left",
            width=10
        )
        self.ent_paid.pack(fill="x", ipady=4, pady=(2, 0))
        self.ent_paid.bind("<KeyRelease>", lambda e: self.calculate_change())

        p_right = tk.Frame(cash_row, bg=pal["totals_bg"])
        p_right.pack(side="right", padx=(10, 0))

        tk.Label(p_right, text="Change", font=("Segoe UI", 8), bg=pal["totals_bg"], fg=pal["muted"]).pack(anchor="e")
        self.lbl_change = tk.Label(
            p_right,
            text=f"{config.CURRENCY}0.00",
            font=("Segoe UI", 15, "bold"),
            bg=pal["totals_bg"],
            fg=pal["blue"]
        )
        self.lbl_change.pack(anchor="e")

        # Underpayment / short warning
        self.lbl_short = tk.Label(
            self.totals_block,
            text="",
            font=("Segoe UI", 8, "bold"),
            bg=pal["totals_bg"],
            fg=pal["danger"]
        )
        self.lbl_short.pack(anchor="e")

        # 6. Quick cash pills: [ Exact ] [ $5 ] [ $10 ] [ $20 ]
        quick_row = tk.Frame(self.totals_block, bg=pal["totals_bg"])
        quick_row.pack(fill="x", pady=(2, 10))

        btn_exact = tk.Button(
            quick_row,
            text="Exact",
            font=("Segoe UI", 8),
            bg=pal["chip"],
            fg=pal["text"],
            relief="flat",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self._set_exact_cash
        )
        btn_exact.pack(side="left", padx=(0, 4))

        def _ex_ent(e):
            p = get_pos_palette()
            btn_exact.config(bg=p["border"])
        def _ex_lve(e):
            p = get_pos_palette()
            btn_exact.config(bg=p["chip"])
        btn_exact.bind("<Enter>", _ex_ent)
        btn_exact.bind("<Leave>", _ex_lve)

        for amount in [5, 10, 20]:
            b = tk.Button(
                quick_row,
                text=f"${amount}",
                font=("Segoe UI", 8),
                bg=pal["chip"],
                fg=pal["text"],
                relief="flat",
                bd=0,
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda a=amount: self._set_quick_cash(a)
            )
            b.pack(side="left", padx=4)

            def _qc_ent(e, btn=b):
                p = get_pos_palette()
                btn.config(bg=p["border"])
            def _qc_lve(e, btn=b):
                p = get_pos_palette()
                btn.config(bg=p["chip"])
            b.bind("<Enter>", _qc_ent)
            b.bind("<Leave>", _qc_lve)

        # 7. Primary button: "✓ Complete sale & print receipt" (56px high, teal)
        self.icon_check = IconCache.get("check", size=18, color=pal["teal_text"])
        self.btn_checkout = tk.Button(
            self.totals_block,
            text="  Complete sale & print receipt",
            image=self.icon_check,
            compound="left",
            font=("Segoe UI", 11, "bold"),
            bg=pal["teal"],
            fg=pal["teal_text"],
            activebackground=pal["teal_dark"],
            activeforeground=pal["teal_text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10,
            command=self.handle_checkout
        )
        self.btn_checkout.pack(fill="x", pady=(4, 0))

    # ─────────────────────────────────────────────────────────────────────────
    # Cart State Actions
    # ─────────────────────────────────────────────────────────────────────────

    def add_product_to_cart(self, prod_data, qty=1):
        """Adds a unit of product to cart or increments existing quantity."""
        prod_id = prod_data["id"]
        available_stock = int(prod_data.get("stock_qty", 0))

        if available_stock <= 0:
            self.toast.show(f"{prod_data.get('name', 'Product')} is out of stock.", is_error=True)
            return

        existing = next((c for c in self.cart if c["product_id"] == prod_id), None)
        curr_in_cart = existing["qty"] if existing else 0

        if curr_in_cart + qty > available_stock:
            self.toast.show(
                f"Cannot add more: only {available_stock} available in stock.",
                is_error=True
            )
            return

        # Fetch cost price if not present
        cost = float(prod_data.get("cost_price", 0.0))
        price = float(prod_data.get("selling_price", 0.0))

        if existing:
            existing["qty"] += qty
            existing["line_total"] = round(existing["qty"] * price, 2)
        else:
            self.cart.append({
                "product_id": prod_id,
                "sku": prod_data.get("sku", ""),
                "name": prod_data.get("name", ""),
                "price": price,
                "cost": cost,
                "stock_qty": available_stock,
                "qty": qty,
                "line_total": round(qty * price, 2)
            })

        self.refresh_cart_display()
        self.render_product_cards()

    def update_cart_item_qty(self, prod_id, delta):
        """Modifies cart item quantity via stepper buttons."""
        item = next((c for c in self.cart if c["product_id"] == prod_id), None)
        if not item:
            return

        new_qty = item["qty"] + delta
        if new_qty <= 0:
            self.remove_cart_item(prod_id)
            return

        if new_qty > item["stock_qty"]:
            self.toast.show(f"Stock limit reached: only {item['stock_qty']} in stock.", is_error=True)
            return

        item["qty"] = new_qty
        item["line_total"] = round(item["qty"] * item["price"], 2)

        self.refresh_cart_display()
        self.render_product_cards()

    def remove_cart_item(self, prod_id):
        """Removes a product line from active cart."""
        self.cart = [c for c in self.cart if c["product_id"] != prod_id]
        self.refresh_cart_display()
        self.render_product_cards()

    def clear_cart(self):
        """Clears all items in the cart."""
        self.cart.clear()
        self.refresh_cart_display()
        self.render_product_cards()

    def refresh_cart_display(self):
        """Re-renders cart rows, totals, and buttons."""
        for w in self.cart_items_frame.winfo_children():
            w.destroy()

        pal = get_pos_palette()
        if not self.cart:
            empty_lbl = tk.Label(
                self.cart_items_frame,
                text="Cart is empty\n\nClick '+' on products to add items.",
                font=("Segoe UI", 9),
                bg=pal["card"],
                fg=pal["muted"],
                pady=30,
                justify="center"
            )
            empty_lbl.pack(fill="both", expand=True)
        else:
            for idx, item in enumerate(self.cart):
                line = CartLine(
                    self.cart_items_frame,
                    item_data=item,
                    on_qty_change=self.update_cart_item_qty,
                    on_remove=self.remove_cart_item
                )
                line.pack(fill="x", expand=True)

                if hasattr(self, "_cart_scroller"):
                    def _attach_cart(w):
                        self._cart_scroller.attach_hover(w)
                        for ch in w.winfo_children():
                            _attach_cart(ch)
                    _attach_cart(line)

                if idx < len(self.cart) - 1:
                    div = tk.Frame(self.cart_items_frame, height=1, bg=pal["divider"])
                    div.pack(fill="x")

        # Update cart header line
        total_items = len(self.cart)
        total_units = sum(c["qty"] for c in self.cart)
        self.lbl_cart_units.config(text=f"{total_items} line items · {total_units} units")

        # Update totals
        self.update_totals()

    def set_discount_pct(self, pct):
        """Sets discount percentage from pill button."""
        self.active_discount_pct = float(pct)
        pal = get_pos_palette()
        for p, b in self.disc_buttons.items():
            is_sel = (p == pct)
            b.config(
                bg=pal["teal"] if is_sel else pal["chip"],
                fg=pal["teal_text"] if is_sel else pal["text"],
                font=("Segoe UI", 8, "bold" if is_sel else "normal")
            )
        self.btn_disc_custom.config(bg=pal["chip"], fg=pal["text"], font=("Segoe UI", 8))
        self.update_totals()

    def _prompt_custom_discount(self):
        """Opens small dialog to input custom discount percentage."""
        pal = get_pos_palette()
        dlg = tk.Toplevel(self)
        dlg.title("Custom Discount %")
        dlg.geometry("260x140")
        dlg.configure(bg=pal["card"])
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Enter Discount (%):", font=("Segoe UI", 10, "bold"), bg=pal["card"], fg=pal["text"]).pack(pady=(16, 6))
        ent = tk.Entry(dlg, font=("Segoe UI", 11), justify="center", width=8)
        ent.pack(pady=4)
        ent.insert(0, str(int(self.active_discount_pct)))
        ent.focus_set()

        def apply_val():
            try:
                val = float(ent.get().strip())
                val = max(0.0, min(100.0, val))
                self.active_discount_pct = val
                for b in self.disc_buttons.values():
                    b.config(bg=pal["chip"], fg=pal["text"], font=("Segoe UI", 8))
                self.btn_disc_custom.config(bg=pal["teal"], fg=pal["teal_text"], font=("Segoe UI", 8, "bold"))
                self.update_totals()
                dlg.destroy()
            except ValueError:
                pass

        ent.bind("<Return>", lambda e: apply_val())
        tk.Button(dlg, text="Apply", font=("Segoe UI", 9, "bold"), bg=pal["teal"], fg=pal["teal_text"], relief="flat", bd=0, padx=12, pady=4, command=apply_val).pack(pady=8)

    def set_payment_method(self, method_val):
        """Sets active payment method."""
        self.selected_pay_method = method_val
        pal = get_pos_palette()
        for val, b in self.pay_method_buttons.items():
            is_sel = (val == method_val)
            b.config(
                bg=pal["teal"] if is_sel else pal["chip"],
                fg=pal["teal_text"] if is_sel else pal["text"],
                font=("Segoe UI", 9, "bold" if is_sel else "normal")
            )

    def _set_exact_cash(self):
        subtotal = sum(c["line_total"] for c in self.cart)
        discount_amt = round(subtotal * (self.active_discount_pct / 100.0), 2)
        total = max(0.0, round(subtotal - discount_amt, 2))
        self.ent_paid.delete(0, tk.END)
        self.ent_paid.insert(0, f"{total:.2f}")
        self.calculate_change()

    def _set_quick_cash(self, amount):
        self.ent_paid.delete(0, tk.END)
        self.ent_paid.insert(0, f"{amount:.2f}")
        self.calculate_change()

    def update_totals(self):
        """Calculates subtotal, discount, total due, and updates checkout button state."""
        subtotal = sum(c["line_total"] for c in self.cart)
        discount_amt = round(subtotal * (self.active_discount_pct / 100.0), 2)
        total = max(0.0, round(subtotal - discount_amt, 2))

        self.lbl_subtotal.config(text=f"{config.CURRENCY}{subtotal:.2f}")
        self.lbl_total.config(text=f"{config.CURRENCY}{total:.2f}")

        # Disable checkout button if cart is empty
        pal = get_pos_palette()
        if not self.cart:
            self.btn_checkout.config(
                state="disabled",
                bg=pal["chip"],
                fg=pal["muted"],
                cursor="arrow"
            )
        else:
            self.btn_checkout.config(
                state="normal",
                bg=pal["teal"],
                fg=pal["teal_text"],
                cursor="hand2"
            )

        self.calculate_change()

    def calculate_change(self):
        """Live calculates change and short warnings."""
        subtotal = sum(c["line_total"] for c in self.cart)
        discount_amt = round(subtotal * (self.active_discount_pct / 100.0), 2)
        total = max(0.0, round(subtotal - discount_amt, 2))

        raw_paid = self.ent_paid.get().strip()
        try:
            paid = float(raw_paid)
        except ValueError:
            paid = 0.0

        if paid >= total:
            change = round(paid - total, 2)
            self.lbl_change.config(text=f"{config.CURRENCY}{change:.2f}")
            self.lbl_short.config(text="")
        else:
            short = round(total - paid, 2)
            self.lbl_change.config(text=f"{config.CURRENCY}0.00")
            if raw_paid:
                self.lbl_short.config(text=f"Short by {config.CURRENCY}{short:.2f}")
            else:
                self.lbl_short.config(text="")

    # ─────────────────────────────────────────────────────────────────────────
    # Checkout & Receipt (Preserving Exact Backend Logic)
    # ─────────────────────────────────────────────────────────────────────────

    def handle_checkout(self):
        """Processes transaction, deducts inventory, records movements, and prints receipt."""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "There are no items in the cart to process.")
            return

        subtotal = sum(c["line_total"] for c in self.cart)
        discount_pct = self.active_discount_pct
        discount_amt = round(subtotal * (discount_pct / 100.0), 2)
        total = max(0.0, round(subtotal - discount_amt, 2))

        try:
            paid = float(self.ent_paid.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Payment", "Please enter a valid numeric amount paid.")
            return

        if paid < total:
            messagebox.showerror(
                "Insufficient Payment",
                f"Amount paid ({config.CURRENCY}{paid:.2f}) is less than total due ({config.CURRENCY}{total:.2f})."
            )
            return

        change = round(paid - total, 2)
        customer = self.ent_customer.get().strip() or "Walk-in Customer"
        pay_method = self.selected_pay_method
        user_id = auth.SessionManager.get_user_id()

        # Generate unique Invoice No
        inv_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # 1. Insert Sales Header
            sale_id = db.execute_query("""
                INSERT INTO sales (invoice_no, user_id, subtotal, discount_percent, discount_amount, total_amount, payment_method, amount_paid, change_amount, customer_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (inv_no, user_id, subtotal, discount_pct, discount_amt, total, pay_method, paid, change, customer), commit=True)

            # 2. Insert Items & Deduct Stock
            for item in self.cart:
                # Insert item
                db.execute_query("""
                    INSERT INTO sales_items (sale_id, product_id, quantity, unit_price, unit_cost, line_total)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (sale_id, item["product_id"], item["qty"], item["price"], item["cost"], item["line_total"]), commit=True)

                # Deduct stock
                db.execute_query("""
                    UPDATE products 
                    SET stock_qty = stock_qty - %s 
                    WHERE id = %s
                """, (item["qty"], item["product_id"]), commit=True)

                # Record stock movement OUT
                db.execute_query("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
                    VALUES (%s, 'OUT', %s, %s, %s)
                """, (item["product_id"], item["qty"], f"Sale: {inv_no}", user_id), commit=True)

            # Audit log
            auth.log_audit("SALE_COMPLETE", f"Processed invoice {inv_no} for {customer}. Total: {config.CURRENCY}{total:.2f}")

            # Show receipt dialog
            self.show_receipt_dialog(inv_no, customer, pay_method, list(self.cart), subtotal, discount_amt, total, paid, change)

            # Reset cart & UI
            self.clear_cart()
            self.ent_paid.delete(0, tk.END)
            self.lbl_short.config(text="")
            self.load_catalog_products()
            self.load_sales_history()

        except Exception as e:
            messagebox.showerror("Transaction Error", f"Failed to complete transaction: {e}")

    def show_receipt_dialog(self, inv_no, customer, pay_method, cart_items, subtotal, discount_amt, total, paid, change):
        """Displays official printable receipt modal dialog."""
        pal = get_pos_palette()
        dlg = tk.Toplevel(self)
        dlg.title(f"Official Receipt - {inv_no}")
        dlg.geometry("450x640")
        dlg.configure(bg=pal["bg"])
        dlg.transient(self)

        txt_frame = tk.Frame(
            dlg,
            bg=pal["card"],
            padx=20,
            pady=20,
            highlightbackground=pal["border"],
            highlightthickness=1
        )
        txt_frame.pack(fill="both", expand=True, padx=20, pady=20)

        receipt_text = tk.Text(
            txt_frame,
            font=("Courier New", 10),
            bg=pal["card"],
            fg=pal["text"],
            relief="flat"
        )
        receipt_text.pack(fill="both", expand=True)

        lines = [
            "==========================================",
            "           PHARMACARE PHARMACY            ",
            "       123 Healthcare Blvd, Suite 100     ",
            "            Tel: +1-800-555-0199          ",
            "==========================================",
            f"Invoice No : {inv_no}",
            f"Date/Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Cashier    : {self.user.get('full_name', 'Staff')}",
            f"Customer   : {customer}",
            f"Pay Method : {pay_method}",
            "------------------------------------------",
            f"{'Item':<22} {'Qty':>4} {'Price':>6} {'Total':>7}",
            "------------------------------------------"
        ]

        for item in cart_items:
            i_name = item['name'][:21]
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
            "=========================================="
        ])

        receipt_text.insert("1.0", "\n".join(lines))
        receipt_text.config(state="disabled")

        btn_close = tk.Button(
            dlg,
            text="Done & Print Receipt",
            font=("Segoe UI", 10, "bold"),
            bg=pal["teal"],
            fg=pal["teal_text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=8,
            command=dlg.destroy
        )
        btn_close.pack(pady=(0, 15))

    # ─────────────────────────────────────────────────────────────────────────
    # History View (Preserved Table, Filter & Item Inspector)
    # ─────────────────────────────────────────────────────────────────────────

    def setup_history_view(self):
        pal = get_pos_palette()

        # Top Filter Bar
        bar = tk.Frame(
            self.history_view,
            bg=pal["card"],
            padx=16,
            pady=12,
            highlightbackground=pal["border"],
            highlightthickness=1
        )
        bar.pack(fill="x", pady=(0, 12))

        tk.Label(
            bar,
            text="Search Invoice:",
            font=("Segoe UI", 9, "bold"),
            bg=pal["card"],
            fg=pal["text"]
        ).pack(side="left", padx=(0, 8))

        self.ent_inv_search = tk.Entry(
            bar,
            font=("Segoe UI", 10),
            bg=pal["input"],
            fg=pal["text"],
            insertbackground=pal["text"],
            relief="flat",
            highlightbackground=pal["input_border"],
            highlightthickness=1,
            width=22
        )
        self.ent_inv_search.pack(side="left", padx=(0, 15), ipady=3)
        self.ent_inv_search.bind("<KeyRelease>", lambda e: self.load_sales_history())

        btn_refresh = tk.Button(
            bar,
            text="↻ Refresh",
            font=("Segoe UI", 9),
            bg=pal["chip"],
            fg=pal["text"],
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.load_sales_history
        )
        btn_refresh.pack(side="left")

        btn_view_details = tk.Button(
            bar,
            text="👁 View Invoice Items",
            font=("Segoe UI", 9, "bold"),
            bg=pal["teal"],
            fg=pal["teal_text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=5,
            command=self.view_selected_invoice_details
        )
        btn_view_details.pack(side="right")

        # History Table
        table_frame = tk.Frame(
            self.history_view,
            bg=pal["card"],
            highlightbackground=pal["border"],
            highlightthickness=1
        )
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "invoice_no", "date", "cashier", "customer", "subtotal", "discount", "total", "method", "paid")
        self.hist_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.hist_tree.heading("id", text="ID")
        self.hist_tree.heading("invoice_no", text="Invoice #")
        self.hist_tree.heading("date", text="Date / Time")
        self.hist_tree.heading("cashier", text="Cashier")
        self.hist_tree.heading("customer", text="Customer")
        self.hist_tree.heading("subtotal", text="Subtotal")
        self.hist_tree.heading("discount", text="Discount")
        self.hist_tree.heading("total", text="Total")
        self.hist_tree.heading("method", text="Payment")
        self.hist_tree.heading("paid", text="Paid")

        self.hist_tree.column("id", width=40, anchor="center")
        self.hist_tree.column("invoice_no", width=160, anchor="center")
        self.hist_tree.column("date", width=140, anchor="center")
        self.hist_tree.column("cashier", width=110, anchor="w")
        self.hist_tree.column("customer", width=130, anchor="w")
        self.hist_tree.column("subtotal", width=80, anchor="e")
        self.hist_tree.column("discount", width=70, anchor="e")
        self.hist_tree.column("total", width=80, anchor="e")
        self.hist_tree.column("method", width=70, anchor="center")
        self.hist_tree.column("paid", width=80, anchor="e")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=scroll_y.set)
        self.hist_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.hist_tree.bind("<Double-1>", lambda e: self.view_selected_invoice_details())

    def load_sales_history(self):
        """Loads and updates sales invoice history records."""
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        search = self.ent_inv_search.get().strip() if hasattr(self, "ent_inv_search") else ""
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
        sales = db.execute_query(query, params, fetchall=True) or []

        for s in sales:
            dt_str = s["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(s["created_at"], "strftime") else str(s["created_at"])
            self.hist_tree.insert(
                "",
                "end",
                values=(
                    s["id"],
                    s["invoice_no"],
                    dt_str,
                    s["cashier"] or "N/A",
                    s["customer_name"] or "Walk-in",
                    f"{config.CURRENCY}{float(s['subtotal']):.2f}",
                    f"{config.CURRENCY}{float(s['discount_amount']):.2f}",
                    f"{config.CURRENCY}{float(s['total_amount']):.2f}",
                    s["payment_method"],
                    f"{config.CURRENCY}{float(s['amount_paid']):.2f}"
                )
            )

    def view_selected_invoice_details(self):
        """Displays breakdown dialog of items for the selected invoice."""
        selected = self.hist_tree.selection()
        if not selected:
            messagebox.showinfo("Select Invoice", "Please select a sale record to view its line items.")
            return

        item = self.hist_tree.item(selected[0])["values"]
        sale_id = item[0]
        inv_no = item[1]

        items = db.execute_query("""
            SELECT si.id, p.sku, p.name, si.quantity, si.unit_price, si.line_total
            FROM sales_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = %s
        """, (sale_id,), fetchall=True) or []

        pal = get_pos_palette()
        dlg = tk.Toplevel(self)
        dlg.title(f"Invoice Breakdown: {inv_no}")
        dlg.geometry("560x400")
        dlg.configure(bg=pal["bg"])
        dlg.transient(self)

        tk.Label(
            dlg,
            text=f"Invoice Breakdown - {inv_no}",
            font=("Segoe UI", 12, "bold"),
            bg=pal["bg"],
            fg=pal["text"]
        ).pack(pady=14)

        tree_f = tk.Frame(
            dlg,
            bg=pal["card"],
            padx=10,
            pady=10,
            highlightbackground=pal["border"],
            highlightthickness=1
        )
        tree_f.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols = ("sku", "name", "qty", "price", "total")
        t = ttk.Treeview(tree_f, columns=cols, show="headings", height=8)
        t.heading("sku", text="SKU")
        t.heading("name", text="Product")
        t.heading("qty", text="Qty")
        t.heading("price", text="Unit Price")
        t.heading("total", text="Total")

        t.column("sku", width=80, anchor="center")
        t.column("name", width=220, anchor="w")
        t.column("qty", width=60, anchor="center")
        t.column("price", width=80, anchor="e")
        t.column("total", width=90, anchor="e")

        for it in items:
            t.insert(
                "",
                "end",
                values=(
                    it["sku"],
                    it["name"],
                    it["quantity"],
                    f"{config.CURRENCY}{float(it['unit_price']):.2f}",
                    f"{config.CURRENCY}{float(it['line_total']):.2f}"
                )
            )

        t.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Keyboard Shortcuts & Mousewheel Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def bind_shortcuts(self):
        """Binds Ctrl+F, F2, Delete, F9, Ctrl+Enter shortcuts."""
        # Top-level window binding
        root = self.winfo_toplevel()
        root.bind("<Control-f>", lambda e: self._focus_search())
        root.bind("<F2>", lambda e: self._focus_search())
        root.bind("<F9>", lambda e: self.handle_checkout())
        root.bind("<Control-Return>", lambda e: self.handle_checkout())
        root.bind("<Delete>", lambda e: self._delete_cart_line())

    def _focus_search(self):
        self.ent_search.focus_set()
        self.ent_search.select_range(0, tk.END)
        return "break"

    def _delete_cart_line(self):
        if self.cart:
            self.remove_cart_item(self.cart[-1]["product_id"])

    def _bind_mousewheel(self, canvas, inner):
        def _on_wheel(event):
            delta = event.delta
            if delta == 0:
                return
            canvas.yview_scroll(int(-1 * (delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_wheel)
        inner.bind("<MouseWheel>", _on_wheel)

    # ─────────────────────────────────────────────────────────────────────────
    # Live Theming Support
    # ─────────────────────────────────────────────────────────────────────────

    def apply_theme(self):
        """Updates icons and non-animatable assets without destroying active widgets."""
        pal = get_pos_palette()

        self.icon_search = IconCache.get("search", size=18, color=pal["muted"])
        if hasattr(self, "lbl_s_icon") and self.lbl_s_icon.winfo_exists():
            self.lbl_s_icon.config(image=self.icon_search)

        self.icon_barcode = IconCache.get("barcode", size=22, color=pal["muted"])
        if hasattr(self, "lbl_b_icon") and self.lbl_b_icon.winfo_exists():
            self.lbl_b_icon.config(image=self.icon_barcode)

        self.icon_check = IconCache.get("check", size=18, color=pal["teal_text"])
        if hasattr(self, "btn_checkout") and self.btn_checkout.winfo_exists():
            self.btn_checkout.config(
                image=self.icon_check,
                activebackground=pal["teal_dark"],
                activeforeground=pal["teal_text"]
            )

        if hasattr(self, "ent_search") and self.ent_search.winfo_exists():
            if self.ent_search.get() == "Search by name or SKU, or scan a barcode":
                self.ent_search.config(fg=pal["muted"])
            else:
                self.ent_search.config(fg=pal["text"])
