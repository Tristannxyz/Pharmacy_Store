import random
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import config
import db
import auth

# Category-specific wholesale cost range and retail markup multipliers:
# (min_cost, max_cost, min_markup, max_markup)
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
        # Derive range from existing active catalog items in custom categories
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
        super().__init__(parent, bg=config.COLORS["background"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)
        self.can_edit = self.role in [config.ROLE_INVENTORY_CLERK, config.ROLE_INSTRUCTOR]

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg=config.COLORS["surface"], padx=30, pady=16, highlightbackground=config.COLORS["border"], highlightthickness=1)
        header.pack(fill="x", side="top")

        lbl_title = tk.Label(header, text="📦 Inventory & Stock Management", font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl_title.pack(side="left")

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=25, pady=15)

        # Tab 1: Products
        self.tab_products = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=15, pady=15)
        self.notebook.add(self.tab_products, text="  Product Catalog & Inventory  ")
        self.setup_products_tab()

        # Tab 2: Stock Movements Log
        self.tab_movements = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=15, pady=15)
        self.notebook.add(self.tab_movements, text="  Stock Movements Log  ")
        self.setup_movements_tab()

        # Tab 3: Suppliers & Categories (Visible to Clerk & Instructor)
        if self.can_edit:
            self.tab_meta = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=15, pady=15)
            self.notebook.add(self.tab_meta, text="  Suppliers & Categories  ")
            self.setup_meta_tab()

    def setup_products_tab(self):
        # Action & Filter Bar
        bar = tk.Frame(self.tab_products, bg=config.COLORS["surface"], padx=15, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        bar.pack(fill="x", pady=(0, 12))

        # Search box
        tk.Label(bar, text="Search:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 5))
        self.ent_search = ttk.Entry(bar, font=config.FONTS["body"], width=25)
        self.ent_search.pack(side="left", padx=(0, 15), ipady=3)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_products())

        # Filter by stock/expiry status
        tk.Label(bar, text="Status Filter:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 5))
        self.combo_filter = ttk.Combobox(bar, values=["All Products", "Low Stock", "Near Expiry (90d)", "Expired", "Out of Stock"], state="readonly", width=18)
        self.combo_filter.current(0)
        self.combo_filter.pack(side="left", padx=(0, 15))
        self.combo_filter.bind("<<ComboboxSelected>>", lambda e: self.load_products())

        # CRUD Action buttons (if role has permission)
        if self.can_edit:
            btn_add = tk.Button(bar, text="+ Add Product", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=12, pady=5, command=self.open_add_product_modal)
            btn_add.pack(side="right", padx=4)

            btn_stock = tk.Button(bar, text="↕ Stock In / Out", font=config.FONTS["body_bold"], bg=config.COLORS["accent"], fg="white", relief="flat", cursor="hand2", padx=12, pady=5, command=self.open_stock_movement_modal)
            btn_stock.pack(side="right", padx=4)

            btn_edit = tk.Button(bar, text="✎ Edit", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"], fg=config.COLORS["text_dark"], relief="flat", cursor="hand2", padx=10, pady=5, command=self.open_edit_product_modal)
            btn_edit.pack(side="right", padx=4)

            btn_del = tk.Button(bar, text="🗑 Delete", font=config.FONTS["body_bold"], bg=config.COLORS["danger"], fg="white", relief="flat", cursor="hand2", padx=10, pady=5, command=self.handle_delete_product)
            btn_del.pack(side="right", padx=4)

        # Products Table
        table_frame = tk.Frame(self.tab_products, bg=config.COLORS["surface"], highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "sku", "name", "category", "stock_qty", "reorder_level", "cost_price", "selling_price", "expiry_date", "unit", "status")
        self.prod_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.prod_tree.heading("id", text="ID")
        self.prod_tree.heading("sku", text="SKU")
        self.prod_tree.heading("name", text="Product Name")
        self.prod_tree.heading("category", text="Category")
        self.prod_tree.heading("stock_qty", text="Stock Qty")
        self.prod_tree.heading("reorder_level", text="Reorder Lvl")
        self.prod_tree.heading("cost_price", text="Cost Price")
        self.prod_tree.heading("selling_price", text="Selling Price")
        self.prod_tree.heading("expiry_date", text="Expiry Date")
        self.prod_tree.heading("unit", text="Unit")
        self.prod_tree.heading("status", text="Alert / Status")

        self.prod_tree.column("id", width=40, anchor="center")
        self.prod_tree.column("sku", width=90, anchor="center")
        self.prod_tree.column("name", width=230, anchor="w")
        self.prod_tree.column("category", width=140, anchor="w")
        self.prod_tree.column("stock_qty", width=80, anchor="center")
        self.prod_tree.column("reorder_level", width=80, anchor="center")
        self.prod_tree.column("cost_price", width=80, anchor="e")
        self.prod_tree.column("selling_price", width=80, anchor="e")
        self.prod_tree.column("expiry_date", width=90, anchor="center")
        self.prod_tree.column("unit", width=60, anchor="center")
        self.prod_tree.column("status", width=110, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.prod_tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.prod_tree.xview)
        self.prod_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.prod_tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Row color tags for alerts
        self.prod_tree.tag_configure("low_stock", foreground=config.COLORS["danger"], font=config.FONTS["body_bold"])
        self.prod_tree.tag_configure("near_expiry", foreground=config.COLORS["warning"])
        self.prod_tree.tag_configure("expired", foreground="#991b1b", background="#fee2e2")

        # Status footer
        self.lbl_prod_count = tk.Label(self.tab_products, text="", font=config.FONTS["small"], bg=config.COLORS["background"], fg=config.COLORS["text_muted"])
        self.lbl_prod_count.pack(anchor="w", pady=(6, 0))

        self.load_products()

    def load_products(self):
        for item in self.prod_tree.get_children():
            self.prod_tree.delete(item)

        search_query = self.ent_search.get().strip().lower()
        filter_opt = self.combo_filter.get()

        query = """
            SELECT p.id, p.sku, p.name, c.name as category_name, p.category_id, p.supplier_id,
                   p.cost_price, p.selling_price, p.stock_qty, p.reorder_level, 
                   p.expiry_date, p.unit
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
        """
        params = []

        if search_query:
            query += " AND (LOWER(p.name) LIKE %s OR LOWER(p.sku) LIKE %s OR LOWER(c.name) LIKE %s)"
            pattern = f"%{search_query}%"
            params.extend([pattern, pattern, pattern])

        today = date.today()
        warn_date = today + timedelta(days=config.EXPIRY_WARN_DAYS)

        if filter_opt == "Low Stock":
            query += " AND p.stock_qty <= p.reorder_level AND p.stock_qty > 0"
        elif filter_opt == "Out of Stock":
            query += " AND p.stock_qty <= 0"
        elif filter_opt == "Near Expiry (90d)":
            query += f" AND p.expiry_date <= '{warn_date}' AND p.expiry_date >= '{today}'"
        elif filter_opt == "Expired":
            query += f" AND p.expiry_date < '{today}'"

        query += " ORDER BY p.name ASC"

        products = db.execute_query(query, params, fetchall=True) or []
        for p in products:
            exp_date = p["expiry_date"]
            if hasattr(exp_date, "strftime"):
                exp_str = exp_date.strftime("%Y-%m-%d")
            else:
                exp_str = str(exp_date)

            tag = "normal"
            status = "Normal"
            if p["stock_qty"] <= 0:
                tag = "low_stock"
                status = "OUT OF STOCK"
            elif p["stock_qty"] <= p["reorder_level"]:
                tag = "low_stock"
                status = "LOW STOCK"
            
            # Check expiry
            if isinstance(exp_date, (date, datetime)):
                p_date = exp_date if isinstance(exp_date, date) else exp_date.date()
                if p_date < today:
                    tag = "expired"
                    status = "EXPIRED"
                elif p_date <= warn_date and status == "Normal":
                    tag = "near_expiry"
                    status = "NEAR EXPIRY"

            self.prod_tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["sku"],
                    p["name"],
                    p["category_name"] or "N/A",
                    p["stock_qty"],
                    p["reorder_level"],
                    f"{config.CURRENCY}{float(p['cost_price']):.2f}",
                    f"{config.CURRENCY}{float(p['selling_price']):.2f}",
                    exp_str,
                    p["unit"],
                    status
                ),
                tags=(tag,)
            )

        self.lbl_prod_count.config(text=f"Showing {len(products)} product(s)")

    def open_add_product_modal(self):
        self.open_product_form("Add New Pharmacy Product")

    def open_edit_product_modal(self):
        selected = self.prod_tree.selection()
        if not selected:
            messagebox.showinfo("Select Product", "Please select a product from the table to edit.")
            return

        item_values = self.prod_tree.item(selected[0])["values"]
        prod_id = item_values[0]
        prod_data = db.execute_query("SELECT * FROM products WHERE id = %s", (prod_id,), fetchone=True)
        if prod_data:
            self.open_product_form("Edit Pharmacy Product", prod_data)

    def open_product_form(self, title, existing_data=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("590x640")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        categories = db.execute_query("SELECT id, name FROM categories ORDER BY name", fetchall=True) or []
        suppliers = db.execute_query("SELECT id, name FROM suppliers ORDER BY name", fetchall=True) or []

        cat_dict = {c["name"]: c["id"] for c in categories}
        sup_dict = {s["name"]: s["id"] for s in suppliers}

        # Form Header
        tk.Label(dlg, text=title, font=config.FONTS["h2"], bg=config.COLORS["background"], fg=config.COLORS["text_dark"]).pack(pady=15)

        form_frame = tk.Frame(dlg, bg=config.COLORS["surface"], padx=25, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        form_frame.grid_columnconfigure(1, weight=1)

        # Field Helper
        entries = {}
        def add_field(row, label_text, key, default_val="", is_combo=False, combo_vals=None):
            tk.Label(form_frame, text=label_text, font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).grid(row=row, column=0, sticky="w", pady=4)
            if is_combo:
                w = ttk.Combobox(form_frame, values=combo_vals or [], state="readonly", width=28)
                if default_val:
                    w.set(default_val)
                elif combo_vals:
                    w.current(0)
            else:
                w = ttk.Entry(form_frame, font=config.FONTS["body"], width=30)
                w.insert(0, str(default_val))
            w.grid(row=row, column=1, sticky="ew", pady=4, padx=(10, 0))
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
            font=config.FONTS["small"],
            bg=config.COLORS["surface_alt"],
            fg=config.COLORS["secondary_dark"],
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=4,
            highlightbackground=config.COLORS["border"],
            highlightthickness=1,
            command=regenerate_prices
        )
        btn_regen.grid(row=4, column=2, rowspan=2, padx=(8, 0), sticky="ns", pady=4)

        if existing_data is None:
            # Automatically regenerate cost & selling prices when adding a product
            regenerate_prices()
            entries["category"].bind("<<ComboboxSelected>>", lambda e: regenerate_prices())

        # Save Action
        def save():
            sku = entries["sku"].get().strip()
            name = entries["name"].get().strip()
            cat_name = entries["category"].get()
            sup_name = entries["supplier"].get()
            unit = entries["unit"].get().strip() or "piece"

            # Input validation
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
                    # UPDATE
                    db.execute_query("""
                        UPDATE products
                        SET sku = %s, name = %s, category_id = %s, supplier_id = %s, cost_price = %s,
                            selling_price = %s, stock_qty = %s, reorder_level = %s, expiry_date = %s, unit = %s
                        WHERE id = %s
                    """, (sku, name, cat_id, sup_id, cost, price, stock, reorder, exp_date, unit, existing_data["id"]), commit=True)
                    auth.log_audit("PRODUCT_UPDATE", f"Updated product ID {existing_data['id']}: {name} (SKU: {sku})")
                    messagebox.showinfo("Success", f"Product '{name}' updated successfully!", parent=dlg)
                else:
                    # INSERT
                    new_id = db.execute_query("""
                        INSERT INTO products (sku, name, category_id, supplier_id, cost_price, selling_price, stock_qty, reorder_level, expiry_date, unit)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (sku, name, cat_id, sup_id, cost, price, stock, reorder, exp_date, unit), commit=True)
                    
                    # Record initial stock movement
                    if stock > 0:
                        db.execute_query("""
                            INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
                            VALUES (%s, 'IN', %s, 'Initial inventory stock on creation', %s)
                        """, (new_id, stock, auth.SessionManager.get_user_id()), commit=True)

                    auth.log_audit("PRODUCT_CREATE", f"Created product: {name} (SKU: {sku}, Qty: {stock})")
                    messagebox.showinfo("Success", f"Product '{name}' added successfully!", parent=dlg)

                dlg.destroy()
                self.load_products()
            except Exception as ex:
                messagebox.showerror("Database Error", f"Failed to save product: {ex}", parent=dlg)

        btn_save = tk.Button(dlg, text="💾 Save Product", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=20, pady=8, command=save)
        btn_save.pack(pady=(0, 15))

    def handle_delete_product(self):
        selected = self.prod_tree.selection()
        if not selected:
            messagebox.showinfo("Select Product", "Please select a product to delete.")
            return

        item = self.prod_tree.item(selected[0])["values"]
        prod_id = item[0]
        prod_name = item[2]

        # Confirmation Dialog as required
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{prod_name}' (ID: {prod_id})?\n\nThis will safely soft-delete it from active catalog."):
            db.execute_query("UPDATE products SET is_active = FALSE WHERE id = %s", (prod_id,), commit=True)
            auth.log_audit("PRODUCT_DELETE", f"Soft-deleted product ID {prod_id}: {prod_name}")
            messagebox.showinfo("Deleted", f"Product '{prod_name}' was removed from active catalog.")
            self.load_products()

    def open_stock_movement_modal(self):
        selected = self.prod_tree.selection()
        if not selected:
            messagebox.showinfo("Select Product", "Please select a product to log stock movement.")
            return

        item = self.prod_tree.item(selected[0])["values"]
        prod_id = item[0]
        prod_name = item[2]
        current_stock = int(item[4])

        dlg = tk.Toplevel(self)
        dlg.title(f"Stock Movement - {prod_name}")
        dlg.geometry("450x360")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text=f"Stock In / Out Adjustment", font=config.FONTS["h3"], bg=config.COLORS["background"], fg=config.COLORS["text_dark"]).pack(pady=15)

        card = tk.Frame(dlg, bg=config.COLORS["surface"], padx=20, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        tk.Label(card, text=f"Product: {prod_name}", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        tk.Label(card, text=f"Current Stock: {current_stock}", font=config.FONTS["body"], bg=config.COLORS["surface"], fg=config.COLORS["secondary"]).pack(anchor="w", pady=(0, 10))

        tk.Label(card, text="Movement Type:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        combo_type = ttk.Combobox(card, values=["IN (Restock / Supplier Delivery)", "OUT (Damaged / Expired / Return)", "ADJUSTMENT (Audit Correction)"], state="readonly")
        combo_type.current(0)
        combo_type.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Quantity Change:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_qty = ttk.Entry(card, font=config.FONTS["body"])
        ent_qty.pack(fill="x", pady=(0, 10))
        ent_qty.insert(0, "10")

        tk.Label(card, text="Reference / Reason Note:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_note = ttk.Entry(card, font=config.FONTS["body"])
        ent_note.pack(fill="x", pady=(0, 10))
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

            # Update product stock & insert stock movement
            db.execute_query("UPDATE products SET stock_qty = %s WHERE id = %s", (new_stock, prod_id), commit=True)
            db.execute_query("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, reference_note, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (prod_id, m_type, qty, note, auth.SessionManager.get_user_id()), commit=True)

            auth.log_audit("STOCK_MOVEMENT", f"{m_type} {qty} units for {prod_name}. New stock: {new_stock}. Note: {note}")
            messagebox.showinfo("Success", f"Stock movement recorded! New stock: {new_stock}", parent=dlg)
            dlg.destroy()
            self.load_products()
            self.load_movements()

        btn_confirm = tk.Button(dlg, text="Confirm Movement", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=20, pady=8, command=submit_movement)
        btn_confirm.pack(pady=(0, 15))

    def setup_movements_tab(self):
        # Header & refresh
        top_bar = tk.Frame(self.tab_movements, bg=config.COLORS["surface"], padx=15, pady=10, highlightbackground=config.COLORS["border"], highlightthickness=1)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Complete Audit History of Inventory Stock Movements", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left")
        btn_ref = tk.Button(top_bar, text="↻ Refresh Log", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], relief="flat", cursor="hand2", command=self.load_movements)
        btn_ref.pack(side="right")

        table_frame = tk.Frame(self.tab_movements, bg=config.COLORS["surface"], highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "date", "sku", "product", "type", "qty", "note", "user")
        self.move_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.move_tree.heading("id", text="ID")
        self.move_tree.heading("date", text="Timestamp")
        self.move_tree.heading("sku", text="SKU")
        self.move_tree.heading("product", text="Product Name")
        self.move_tree.heading("type", text="Movement Type")
        self.move_tree.heading("qty", text="Quantity")
        self.move_tree.heading("note", text="Reference / Note")
        self.move_tree.heading("user", text="Logged By")

        self.move_tree.column("id", width=40, anchor="center")
        self.move_tree.column("date", width=140, anchor="center")
        self.move_tree.column("sku", width=90, anchor="center")
        self.move_tree.column("product", width=220, anchor="w")
        self.move_tree.column("type", width=90, anchor="center")
        self.move_tree.column("qty", width=70, anchor="center")
        self.move_tree.column("note", width=200, anchor="w")
        self.move_tree.column("user", width=120, anchor="w")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.move_tree.yview)
        self.move_tree.configure(yscrollcommand=scroll_y.set)
        self.move_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.load_movements()

    def load_movements(self):
        for item in self.move_tree.get_children():
            self.move_tree.delete(item)

        movements = db.execute_query("""
            SELECT sm.id, sm.created_at, p.sku, p.name as prod_name, sm.movement_type, sm.quantity, sm.reference_note, u.username
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN users u ON sm.user_id = u.id
            ORDER BY sm.created_at DESC
            LIMIT 200
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

    def setup_meta_tab(self):
        # Two columns: Categories (Left) and Suppliers (Right)
        panes = tk.PanedWindow(self.tab_meta, orient="horizontal", bg=config.COLORS["background"])
        panes.pack(fill="both", expand=True)

        # Left: Categories
        frame_cats = tk.Frame(panes, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        panes.add(frame_cats, width=450)

        tk.Label(frame_cats, text="Categories Management", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 10))
        btn_add_cat = tk.Button(frame_cats, text="+ Add Category", font=config.FONTS["small"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", command=self.add_category_dialog)
        btn_add_cat.pack(anchor="w", pady=(0, 10))

        cols_c = ("id", "name", "desc")
        self.cat_tree = ttk.Treeview(frame_cats, columns=cols_c, show="headings", selectmode="browse", height=15)
        self.cat_tree.heading("id", text="ID")
        self.cat_tree.heading("name", text="Category Name")
        self.cat_tree.heading("desc", text="Description")
        self.cat_tree.column("id", width=40, anchor="center")
        self.cat_tree.column("name", width=140, anchor="w")
        self.cat_tree.column("desc", width=200, anchor="w")
        self.cat_tree.pack(fill="both", expand=True)

        # Right: Suppliers
        frame_sups = tk.Frame(panes, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        panes.add(frame_sups, width=550)

        tk.Label(frame_sups, text="Suppliers Directory", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 10))
        btn_add_sup = tk.Button(frame_sups, text="+ Add Supplier", font=config.FONTS["small"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", command=self.add_supplier_dialog)
        btn_add_sup.pack(anchor="w", pady=(0, 10))

        cols_s = ("id", "name", "contact", "phone", "email")
        self.sup_tree = ttk.Treeview(frame_sups, columns=cols_s, show="headings", selectmode="browse", height=15)
        self.sup_tree.heading("id", text="ID")
        self.sup_tree.heading("name", text="Supplier Name")
        self.sup_tree.heading("contact", text="Contact Person")
        self.sup_tree.heading("phone", text="Phone")
        self.sup_tree.heading("email", text="Email")
        self.sup_tree.column("id", width=40, anchor="center")
        self.sup_tree.column("name", width=140, anchor="w")
        self.sup_tree.column("contact", width=100, anchor="w")
        self.sup_tree.column("phone", width=90, anchor="w")
        self.sup_tree.column("email", width=120, anchor="w")
        self.sup_tree.pack(fill="both", expand=True)

        self.load_categories()
        self.load_suppliers()

    def load_categories(self):
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        cats = db.execute_query("SELECT id, name, description FROM categories ORDER BY name", fetchall=True) or []
        for c in cats:
            self.cat_tree.insert("", "end", values=(c["id"], c["name"], c["description"] or "-"))

    def load_suppliers(self):
        for item in self.sup_tree.get_children():
            self.sup_tree.delete(item)
        sups = db.execute_query("SELECT id, name, contact_person, phone, email FROM suppliers ORDER BY name", fetchall=True) or []
        for s in sups:
            self.sup_tree.insert("", "end", values=(s["id"], s["name"], s["contact_person"] or "-", s["phone"] or "-", s["email"] or "-"))

    def add_category_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Category")
        dlg.geometry("380x250")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=config.COLORS["surface"], padx=20, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(card, text="Category Name:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_name = ttk.Entry(card, font=config.FONTS["body"])
        ent_name.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Description:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_desc = ttk.Entry(card, font=config.FONTS["body"])
        ent_desc.pack(fill="x", pady=(0, 15))

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
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save category: {e}", parent=dlg)

        btn_save = tk.Button(dlg, text="Save Category", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", command=save)
        btn_save.pack(pady=(0, 15))

    def add_supplier_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Supplier")
        dlg.geometry("420x350")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=config.COLORS["surface"], padx=20, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        fields = [("Supplier Name *", "name"), ("Contact Person", "contact"), ("Phone", "phone"), ("Email", "email")]
        entries = {}
        for lbl, key in fields:
            tk.Label(card, text=lbl, font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
            e = ttk.Entry(card, font=config.FONTS["body"])
            e.pack(fill="x", pady=(0, 6))
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

        btn_save = tk.Button(dlg, text="Save Supplier", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", command=save)
        btn_save.pack(pady=(0, 15))

