import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import config
import db
import auth

class SalesScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=config.COLORS["background"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)
        self.can_pos = self.role in [config.ROLE_SALES_PERSONNEL, config.ROLE_INSTRUCTOR]

        # Cart state
        self.cart = []  # list of dicts: {"product_id", "sku", "name", "price", "cost", "stock_qty", "qty", "line_total"}

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg=config.COLORS["surface"], padx=30, pady=16, highlightbackground=config.COLORS["border"], highlightthickness=1)
        header.pack(fill="x", side="top")

        lbl_title = tk.Label(header, text="💳 Point of Sale (POS) & Transactions", font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl_title.pack(side="left")

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=25, pady=15)

        if self.can_pos:
            self.tab_pos = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=10, pady=10)
            self.notebook.add(self.tab_pos, text="  New Sales Transaction (POS)  ")
            self.setup_pos_tab()

        self.tab_history = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=10, pady=10)
        self.notebook.add(self.tab_history, text="  Sales & Invoices History  ")
        self.setup_history_tab()

    def setup_pos_tab(self):
        # Two-panel layout: Left is Product Catalog/Search, Right is Cart & Checkout
        paned = tk.PanedWindow(self.tab_pos, orient="horizontal", bg=config.COLORS["background"], sashwidth=6)
        paned.pack(fill="both", expand=True)

        # LEFT PANEL: Product Selector
        left_frame = tk.Frame(paned, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        paned.add(left_frame, width=540)

        tk.Label(left_frame, text="Select Product to Add", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 10))

        # Search Bar
        search_box = tk.Frame(left_frame, bg=config.COLORS["surface"])
        search_box.pack(fill="x", pady=(0, 10))

        tk.Label(search_box, text="Search:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left", padx=(0, 6))
        self.ent_prod_search = ttk.Entry(search_box, font=config.FONTS["body"])
        self.ent_prod_search.pack(side="left", fill="x", expand=True, ipady=3)
        self.ent_prod_search.bind("<KeyRelease>", lambda e: self.load_catalog_products())

        # Product Table
        p_table_frame = tk.Frame(left_frame, bg=config.COLORS["surface"])
        p_table_frame.pack(fill="both", expand=True)

        p_cols = ("id", "sku", "name", "price", "stock")
        self.catalog_tree = ttk.Treeview(p_table_frame, columns=p_cols, show="headings", selectmode="browse", height=12)
        self.catalog_tree.heading("id", text="ID")
        self.catalog_tree.heading("sku", text="SKU")
        self.catalog_tree.heading("name", text="Product Name")
        self.catalog_tree.heading("price", text="Price")
        self.catalog_tree.heading("stock", text="Stock")

        self.catalog_tree.column("id", width=35, anchor="center")
        self.catalog_tree.column("sku", width=75, anchor="center")
        self.catalog_tree.column("name", width=190, anchor="w")
        self.catalog_tree.column("price", width=70, anchor="e")
        self.catalog_tree.column("stock", width=65, anchor="center")

        scroll_p = ttk.Scrollbar(p_table_frame, orient="vertical", command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=scroll_p.set)
        self.catalog_tree.pack(side="left", fill="both", expand=True)
        scroll_p.pack(side="right", fill="y")

        # Double click to add
        self.catalog_tree.bind("<Double-1>", lambda e: self.add_selected_to_cart())

        # Quick Add quantity bar
        add_bar = tk.Frame(left_frame, bg=config.COLORS["surface"], pady=10)
        add_bar.pack(fill="x")

        tk.Label(add_bar, text="Qty:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left", padx=(0, 5))
        self.spn_qty = ttk.Spinbox(add_bar, from_=1, to=1000, width=5)
        self.spn_qty.set(1)
        self.spn_qty.pack(side="left", padx=(0, 10))

        btn_add = tk.Button(add_bar, text="➕ Add to Cart", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=12, pady=6, command=self.add_selected_to_cart)
        btn_add.pack(side="left")

        # RIGHT PANEL: Cart & Checkout
        right_frame = tk.Frame(paned, bg=config.COLORS["surface"], padx=18, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        paned.add(right_frame, width=540)

        cart_head = tk.Frame(right_frame, bg=config.COLORS["surface"])
        cart_head.pack(fill="x", pady=(0, 10))
        tk.Label(cart_head, text="🛒 Active Cart Items", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(side="left")
        
        btn_clear = tk.Button(cart_head, text="Clear Cart", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], relief="flat", cursor="hand2", command=self.clear_cart)
        btn_clear.pack(side="right")

        # Cart Treeview
        c_frame = tk.Frame(right_frame, bg=config.COLORS["surface"])
        c_frame.pack(fill="both", expand=True)

        c_cols = ("sku", "name", "price", "qty", "total")
        self.cart_tree = ttk.Treeview(c_frame, columns=c_cols, show="headings", selectmode="browse", height=7)
        self.cart_tree.heading("sku", text="SKU")
        self.cart_tree.heading("name", text="Product")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.heading("qty", text="Qty")
        self.cart_tree.heading("total", text="Total")

        self.cart_tree.column("sku", width=75, anchor="center")
        self.cart_tree.column("name", width=160, anchor="w")
        self.cart_tree.column("price", width=70, anchor="e")
        self.cart_tree.column("qty", width=55, anchor="center")
        self.cart_tree.column("total", width=75, anchor="e")

        scroll_c = ttk.Scrollbar(c_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=scroll_c.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        scroll_c.pack(side="right", fill="y")

        # Cart remove button
        btn_remove_item = tk.Button(right_frame, text="Remove Selected Item", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], fg=config.COLORS["danger"], relief="flat", cursor="hand2", command=self.remove_selected_cart_item)
        btn_remove_item.pack(anchor="w", pady=(5, 10))

        # Payment & Totals Section
        pay_box = tk.Frame(right_frame, bg=config.COLORS["surface_alt"], padx=15, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        pay_box.pack(fill="x", side="bottom")

        # Customer name
        row_c = tk.Frame(pay_box, bg=config.COLORS["surface_alt"])
        row_c.pack(fill="x", pady=2)
        tk.Label(row_c, text="Customer:", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"]).pack(side="left")
        self.ent_customer = ttk.Entry(row_c, font=config.FONTS["body"])
        self.ent_customer.insert(0, "Walk-in Customer")
        self.ent_customer.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Discount & Payment Method
        row_d = tk.Frame(pay_box, bg=config.COLORS["surface_alt"])
        row_d.pack(fill="x", pady=2)
        tk.Label(row_d, text="Discount (%):", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"]).pack(side="left")
        self.spn_discount = ttk.Spinbox(row_d, from_=0, to=100, width=5, command=self.update_totals)
        self.spn_discount.set(0)
        self.spn_discount.pack(side="left", padx=(10, 20))
        self.spn_discount.bind("<KeyRelease>", lambda e: self.update_totals())

        tk.Label(row_d, text="Method:", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"]).pack(side="left")
        self.combo_pay_method = ttk.Combobox(row_d, values=["CASH", "CARD", "ONLINE"], state="readonly", width=8)
        self.combo_pay_method.current(0)
        self.combo_pay_method.pack(side="right")

        # Subtotal, Discount Amt, Total
        divider = tk.Frame(pay_box, height=1, bg=config.COLORS["border"])
        divider.pack(fill="x", pady=6)

        row_totals = tk.Frame(pay_box, bg=config.COLORS["surface_alt"])
        row_totals.pack(fill="x")
        
        tk.Label(row_totals, text="Subtotal: ", font=config.FONTS["body"], bg=config.COLORS["surface_alt"]).pack(side="left")
        self.lbl_subtotal = tk.Label(row_totals, text="$0.00", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"])
        self.lbl_subtotal.pack(side="left", padx=(0, 20))

        tk.Label(row_totals, text="Total Due: ", font=config.FONTS["h3"], bg=config.COLORS["surface_alt"], fg=config.COLORS["text_dark"]).pack(side="left")
        self.lbl_total = tk.Label(row_totals, text="$0.00", font=config.FONTS["h2"], bg=config.COLORS["surface_alt"], fg=config.COLORS["secondary"])
        self.lbl_total.pack(side="left")

        # Amount paid & Change
        row_cash = tk.Frame(pay_box, bg=config.COLORS["surface_alt"])
        row_cash.pack(fill="x", pady=6)

        tk.Label(row_cash, text="Amount Paid ($):", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"]).pack(side="left")
        self.ent_paid = ttk.Entry(row_cash, font=config.FONTS["body_bold"], width=12)
        self.ent_paid.pack(side="left", padx=(10, 15))
        self.ent_paid.bind("<KeyRelease>", lambda e: self.calculate_change())

        tk.Label(row_cash, text="Change: ", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"]).pack(side="left")
        self.lbl_change = tk.Label(row_cash, text="$0.00", font=config.FONTS["h3"], bg=config.COLORS["surface_alt"], fg=config.COLORS["accent"])
        self.lbl_change.pack(side="left")

        # Checkout Button
        btn_checkout = tk.Button(pay_box, text="✔ Complete Transaction & Print Receipt", font=config.FONTS["h3"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", pady=8, command=self.handle_checkout)
        btn_checkout.pack(fill="x", pady=(10, 0))

        self.load_catalog_products()

    def load_catalog_products(self):
        for item in self.catalog_tree.get_children():
            self.catalog_tree.delete(item)

        search = self.ent_prod_search.get().strip().lower()
        query = "SELECT id, sku, name, selling_price, stock_qty, cost_price FROM products WHERE is_active = TRUE AND stock_qty > 0"
        params = []
        if search:
            query += " AND (LOWER(name) LIKE %s OR LOWER(sku) LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY name ASC LIMIT 100"
        prods = db.execute_query(query, params, fetchall=True) or []
        for p in prods:
            self.catalog_tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["sku"],
                    p["name"],
                    f"{config.CURRENCY}{float(p['selling_price']):.2f}",
                    p["stock_qty"]
                )
            )

    def add_selected_to_cart(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showinfo("Select Product", "Please select a product from the list.")
            return

        item = self.catalog_tree.item(selected[0])["values"]
        prod_id = item[0]
        sku = item[1]
        name = item[2]
        price = float(str(item[3]).replace(config.CURRENCY, ""))
        available_stock = int(item[4])

        try:
            qty = int(self.spn_qty.get())
            if qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Quantity must be an integer >= 1.")
            return

        # Check existing in cart
        existing = next((c for c in self.cart if c["product_id"] == prod_id), None)
        curr_in_cart = existing["qty"] if existing else 0

        if curr_in_cart + qty > available_stock:
            messagebox.showerror("Stock Limit", f"Cannot add {qty} units. Only {available_stock - curr_in_cart} additional units available.")
            return

        # Fetch cost price
        p_row = db.execute_query("SELECT cost_price FROM products WHERE id = %s", (prod_id,), fetchone=True)
        cost = float(p_row["cost_price"]) if p_row else 0.0

        if existing:
            existing["qty"] += qty
            existing["line_total"] = round(existing["qty"] * price, 2)
        else:
            self.cart.append({
                "product_id": prod_id,
                "sku": sku,
                "name": name,
                "price": price,
                "cost": cost,
                "stock_qty": available_stock,
                "qty": qty,
                "line_total": round(qty * price, 2)
            })

        self.refresh_cart_display()

    def remove_selected_cart_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        idx = self.cart_tree.index(selected[0])
        if 0 <= idx < len(self.cart):
            self.cart.pop(idx)
            self.refresh_cart_display()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_cart_display()

    def refresh_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        for c in self.cart:
            self.cart_tree.insert(
                "",
                "end",
                values=(
                    c["sku"],
                    c["name"],
                    f"{config.CURRENCY}{c['price']:.2f}",
                    c["qty"],
                    f"{config.CURRENCY}{c['line_total']:.2f}"
                )
            )
        self.update_totals()

    def update_totals(self):
        subtotal = sum(c["line_total"] for c in self.cart)
        try:
            discount_pct = float(self.spn_discount.get())
            if discount_pct < 0 or discount_pct > 100:
                discount_pct = 0.0
        except ValueError:
            discount_pct = 0.0

        discount_amt = round(subtotal * (discount_pct / 100.0), 2)
        total = max(0.0, round(subtotal - discount_amt, 2))

        self.lbl_subtotal.config(text=f"{config.CURRENCY}{subtotal:.2f}")
        self.lbl_total.config(text=f"{config.CURRENCY}{total:.2f}")
        self.calculate_change()

    def calculate_change(self):
        subtotal = sum(c["line_total"] for c in self.cart)
        try:
            discount_pct = float(self.spn_discount.get())
        except ValueError:
            discount_pct = 0.0
        total = max(0.0, round(subtotal * (1 - discount_pct / 100.0), 2))

        try:
            paid = float(self.ent_paid.get().strip())
        except ValueError:
            paid = 0.0

        change = round(paid - total, 2) if paid >= total else 0.0
        self.lbl_change.config(text=f"{config.CURRENCY}{change:.2f}")

    def handle_checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "There are no items in the cart to process.")
            return

        subtotal = sum(c["line_total"] for c in self.cart)
        try:
            discount_pct = float(self.spn_discount.get())
        except ValueError:
            discount_pct = 0.0
        discount_amt = round(subtotal * (discount_pct / 100.0), 2)
        total = max(0.0, round(subtotal - discount_amt, 2))

        try:
            paid = float(self.ent_paid.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Payment", "Please enter a valid numeric amount paid.")
            return

        if paid < total:
            messagebox.showerror("Insufficient Payment", f"Amount paid ({config.CURRENCY}{paid:.2f}) is less than total due ({config.CURRENCY}{total:.2f}).")
            return

        change = round(paid - total, 2)
        customer = self.ent_customer.get().strip() or "Walk-in Customer"
        pay_method = self.combo_pay_method.get()
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
            self.show_receipt_dialog(inv_no, customer, pay_method, self.cart, subtotal, discount_amt, total, paid, change)

            # Reset cart & UI
            self.clear_cart()
            self.ent_paid.delete(0, tk.END)
            self.load_catalog_products()
            self.load_sales_history()

        except Exception as e:
            messagebox.showerror("Transaction Error", f"Failed to complete transaction: {e}")

    def show_receipt_dialog(self, inv_no, customer, pay_method, cart_items, subtotal, discount_amt, total, paid, change):
        dlg = tk.Toplevel(self)
        dlg.title(f"Official Receipt - {inv_no}")
        dlg.geometry("450x620")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)

        txt_frame = tk.Frame(dlg, bg="white", padx=20, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        txt_frame.pack(fill="both", expand=True, padx=20, pady=20)

        receipt_text = tk.Text(txt_frame, font=("Courier New", 10), bg="white", relief="flat")
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

        btn_close = tk.Button(dlg, text="Done & Print Receipt", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=20, pady=8, command=dlg.destroy)
        btn_close.pack(pady=(0, 15))

    def setup_history_tab(self):
        # Filter Bar
        bar = tk.Frame(self.tab_history, bg=config.COLORS["surface"], padx=15, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        bar.pack(fill="x", pady=(0, 12))

        tk.Label(bar, text="Search Invoice:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left", padx=(0, 5))
        self.ent_inv_search = ttk.Entry(bar, font=config.FONTS["body"], width=20)
        self.ent_inv_search.pack(side="left", padx=(0, 15))
        self.ent_inv_search.bind("<KeyRelease>", lambda e: self.load_sales_history())

        btn_refresh = tk.Button(bar, text="↻ Refresh", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], relief="flat", cursor="hand2", command=self.load_sales_history)
        btn_refresh.pack(side="left")

        btn_view_details = tk.Button(bar, text="👁 View Invoice Items", font=config.FONTS["body_bold"], bg=config.COLORS["accent"], fg="white", relief="flat", cursor="hand2", padx=12, pady=4, command=self.view_selected_invoice_details)
        btn_view_details.pack(side="right")

        # History Table
        table_frame = tk.Frame(self.tab_history, bg=config.COLORS["surface"], highlightbackground=config.COLORS["border"], highlightthickness=1)
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

        self.load_sales_history()

    def load_sales_history(self):
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

        dlg = tk.Toplevel(self)
        dlg.title(f"Invoice Breakdown: {inv_no}")
        dlg.geometry("540x380")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)

        tk.Label(dlg, text=f"Invoice Breakdown - {inv_no}", font=config.FONTS["h3"], bg=config.COLORS["background"]).pack(pady=12)

        tree_f = tk.Frame(dlg, bg=config.COLORS["surface"], padx=10, pady=10)
        tree_f.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        cols = ("sku", "name", "qty", "price", "total")
        t = ttk.Treeview(tree_f, columns=cols, show="headings", height=8)
        t.heading("sku", text="SKU")
        t.heading("name", text="Product")
        t.heading("qty", text="Qty")
        t.heading("price", text="Unit Price")
        t.heading("total", text="Total")

        t.column("sku", width=80, anchor="center")
        t.column("name", width=200, anchor="w")
        t.column("qty", width=60, anchor="center")
        t.column("price", width=80, anchor="e")
        t.column("total", width=90, anchor="e")

        for it in items:
            t.insert("", "end", values=(it["sku"], it["name"], it["quantity"], f"{config.CURRENCY}{float(it['unit_price']):.2f}", f"{config.CURRENCY}{float(it['line_total']):.2f}"))

        t.pack(fill="both", expand=True)

