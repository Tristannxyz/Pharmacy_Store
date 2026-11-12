import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
import db
import auth

class UsersScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=config.COLORS["background"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg=config.COLORS["surface"], padx=30, pady=16, highlightbackground=config.COLORS["border"], highlightthickness=1)
        header.pack(fill="x", side="top")

        lbl_title = tk.Label(header, text="👥 User Accounts & Security Audit Trail", font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl_title.pack(side="left")

        # Notebook tabs: Users and Audit Log
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=25, pady=15)

        # Tab 1: User Accounts
        self.tab_users = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=15, pady=15)
        self.notebook.add(self.tab_users, text="  User Account Management  ")
        self.setup_users_tab()

        # Tab 2: Audit Logs
        self.tab_audit = tk.Frame(self.notebook, bg=config.COLORS["background"], padx=15, pady=15)
        self.notebook.add(self.tab_audit, text="  Security Audit Logs  ")
        self.setup_audit_tab()

    def setup_users_tab(self):
        # Action Bar
        bar = tk.Frame(self.tab_users, bg=config.COLORS["surface"], padx=15, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        bar.pack(fill="x", pady=(0, 12))

        btn_add = tk.Button(bar, text="+ Add New User", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=12, pady=5, command=self.open_add_user_dialog)
        btn_add.pack(side="left", padx=(0, 6))

        btn_edit = tk.Button(bar, text="✎ Edit User", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"], fg=config.COLORS["text_dark"], relief="flat", cursor="hand2", padx=10, pady=5, command=self.open_edit_user_dialog)
        btn_edit.pack(side="left", padx=4)

        btn_reset_pw = tk.Button(bar, text="🔑 Reset Password", font=config.FONTS["body_bold"], bg=config.COLORS["accent"], fg="white", relief="flat", cursor="hand2", padx=10, pady=5, command=self.open_reset_password_dialog)
        btn_reset_pw.pack(side="left", padx=4)

        btn_unlock = tk.Button(bar, text="🔓 Unlock Account", font=config.FONTS["body_bold"], bg=config.COLORS["warning"], fg="white", relief="flat", cursor="hand2", padx=10, pady=5, command=self.handle_unlock_account)
        btn_unlock.pack(side="left", padx=4)

        btn_toggle_active = tk.Button(bar, text="Toggle Active / Inactive", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], fg=config.COLORS["danger"], relief="flat", cursor="hand2", padx=10, pady=5, command=self.handle_toggle_active)
        btn_toggle_active.pack(side="right")

        # Table
        table_frame = tk.Frame(self.tab_users, bg=config.COLORS["surface"], highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "username", "full_name", "role", "email", "status", "failed_attempts", "last_login", "created_at")
        self.user_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="Username")
        self.user_tree.heading("full_name", text="Full Name")
        self.user_tree.heading("role", text="Assigned Role")
        self.user_tree.heading("email", text="Email")
        self.user_tree.heading("status", text="Account Status")
        self.user_tree.heading("failed_attempts", text="Failed Logins")
        self.user_tree.heading("last_login", text="Last Login")
        self.user_tree.heading("created_at", text="Registered")

        self.user_tree.column("id", width=40, anchor="center")
        self.user_tree.column("username", width=120, anchor="w")
        self.user_tree.column("full_name", width=180, anchor="w")
        self.user_tree.column("role", width=140, anchor="center")
        self.user_tree.column("email", width=170, anchor="w")
        self.user_tree.column("status", width=110, anchor="center")
        self.user_tree.column("failed_attempts", width=90, anchor="center")
        self.user_tree.column("last_login", width=130, anchor="center")
        self.user_tree.column("created_at", width=130, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scroll_y.set)
        self.user_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.user_tree.tag_configure("locked", foreground=config.COLORS["danger"], font=config.FONTS["body_bold"])
        self.user_tree.tag_configure("inactive", foreground=config.COLORS["text_muted"])

        self.load_users()

    def load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        users = db.execute_query("""
            SELECT id, username, full_name, role, email, is_active, failed_attempts, locked_until, last_login, created_at
            FROM users
            ORDER BY id ASC
        """, fetchall=True) or []

        for u in users:
            status = "Active"
            tag = "normal"
            if not u["is_active"]:
                status = "Deactivated"
                tag = "inactive"
            elif u["locked_until"] and u["locked_until"] > datetime.now():
                status = "LOCKED"
                tag = "locked"

            ll_str = u["last_login"].strftime("%Y-%m-%d %H:%M") if u["last_login"] else "Never"
            cr_str = u["created_at"].strftime("%Y-%m-%d") if u["created_at"] else "-"

            role_display = config.ROLE_DISPLAY_NAMES.get(u["role"], u["role"])

            self.user_tree.insert(
                "",
                "end",
                values=(
                    u["id"],
                    u["username"],
                    u["full_name"],
                    role_display,
                    u["email"] or "-",
                    status,
                    u["failed_attempts"],
                    ll_str,
                    cr_str
                ),
                tags=(tag,)
            )

    def open_add_user_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New User Account")
        dlg.geometry("450x450")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=config.COLORS["surface"], padx=25, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text="Create New User", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 10))

        fields = [
            ("Username *", "username", False),
            ("Full Name *", "full_name", False),
            ("Email Address", "email", False),
            ("Initial Password *", "password", True)
        ]
        entries = {}
        for lbl, key, is_pwd in fields:
            tk.Label(card, text=lbl, font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
            e = ttk.Entry(card, font=config.FONTS["body"], show="•" if is_pwd else "")
            e.pack(fill="x", pady=(0, 8))
            entries[key] = e

        tk.Label(card, text="Role Assignment *", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        role_keys = list(config.ROLE_DISPLAY_NAMES.keys())
        role_names = [config.ROLE_DISPLAY_NAMES[k] for k in role_keys]
        combo_role = ttk.Combobox(card, values=role_names, state="readonly")
        combo_role.current(0)
        combo_role.pack(fill="x", pady=(0, 15))

        def save():
            username = entries["username"].get().strip()
            full_name = entries["full_name"].get().strip()
            email = entries["email"].get().strip()
            pwd = entries["password"].get()
            selected_role_idx = combo_role.current()
            role = role_keys[selected_role_idx]

            if not username or not full_name or not pwd:
                messagebox.showerror("Error", "Username, Full Name, and Password are required.", parent=dlg)
                return

            if len(pwd) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters.", parent=dlg)
                return

            try:
                hashed = auth.hash_password(pwd)
                db.execute_query("""
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, hashed, full_name, email, role), commit=True)

                auth.log_audit("USER_CREATE", f"Created user {username} with role {role}")
                messagebox.showinfo("Success", f"User '{username}' created successfully!", parent=dlg)
                dlg.destroy()
                self.load_users()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create user: {e}", parent=dlg)

        btn_save = tk.Button(dlg, text="Save User", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=20, pady=8, command=save)
        btn_save.pack(pady=(0, 15))

    def open_edit_user_dialog(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showinfo("Select User", "Please select a user to edit.")
            return

        user_id = self.user_tree.item(selected[0])["values"][0]
        u_data = db.execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetchone=True)
        if not u_data:
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Edit User - {u_data['username']}")
        dlg.geometry("450x380")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=config.COLORS["surface"], padx=25, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text=f"Edit User: {u_data['username']}", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 10))

        tk.Label(card, text="Full Name *", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_name = ttk.Entry(card, font=config.FONTS["body"])
        ent_name.insert(0, u_data["full_name"])
        ent_name.pack(fill="x", pady=(0, 8))

        tk.Label(card, text="Email Address", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_email = ttk.Entry(card, font=config.FONTS["body"])
        ent_email.insert(0, u_data["email"] or "")
        ent_email.pack(fill="x", pady=(0, 8))

        tk.Label(card, text="Role Assignment *", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        role_keys = list(config.ROLE_DISPLAY_NAMES.keys())
        role_names = [config.ROLE_DISPLAY_NAMES[k] for k in role_keys]
        combo_role = ttk.Combobox(card, values=role_names, state="readonly")
        try:
            curr_idx = role_keys.index(u_data["role"])
            combo_role.current(curr_idx)
        except ValueError:
            combo_role.current(0)
        combo_role.pack(fill="x", pady=(0, 15))

        def update():
            full_name = ent_name.get().strip()
            email = ent_email.get().strip()
            role = role_keys[combo_role.current()]

            if not full_name:
                messagebox.showerror("Error", "Full Name is required.", parent=dlg)
                return

            try:
                db.execute_query("""
                    UPDATE users SET full_name = %s, email = %s, role = %s WHERE id = %s
                """, (full_name, email, role, user_id), commit=True)

                auth.log_audit("USER_UPDATE", f"Updated user {u_data['username']} (Role: {role})")
                messagebox.showinfo("Success", f"User '{u_data['username']}' updated!", parent=dlg)
                dlg.destroy()
                self.load_users()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update user: {e}", parent=dlg)

        btn_update = tk.Button(dlg, text="Save Changes", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=20, pady=8, command=update)
        btn_update.pack(pady=(0, 15))

    def open_reset_password_dialog(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showinfo("Select User", "Please select a user to reset password.")
            return

        user_id = self.user_tree.item(selected[0])["values"][0]
        username = self.user_tree.item(selected[0])["values"][1]

        dlg = tk.Toplevel(self)
        dlg.title(f"Reset Password - {username}")
        dlg.geometry("380x250")
        dlg.configure(bg=config.COLORS["background"])
        dlg.transient(self)
        dlg.grab_set()

        card = tk.Frame(dlg, bg=config.COLORS["surface"], padx=20, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(card, text=f"New Password for {username}:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_new = ttk.Entry(card, font=config.FONTS["body"], show="•")
        ent_new.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Confirm New Password:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(anchor="w", pady=2)
        ent_conf = ttk.Entry(card, font=config.FONTS["body"], show="•")
        ent_conf.pack(fill="x", pady=(0, 15))

        def reset_pwd():
            p1 = ent_new.get()
            p2 = ent_conf.get()
            if not p1 or not p2:
                messagebox.showerror("Error", "Fields cannot be blank.", parent=dlg)
                return
            if p1 != p2:
                messagebox.showerror("Error", "Passwords do not match.", parent=dlg)
                return
            if len(p1) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters.", parent=dlg)
                return

            hashed = auth.hash_password(p1)
            db.execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (hashed, user_id), commit=True)
            auth.log_audit("PASSWORD_RESET", f"Reset password for user {username}")
            messagebox.showinfo("Success", f"Password for '{username}' was reset!", parent=dlg)
            dlg.destroy()

        btn_save = tk.Button(dlg, text="Change Password", font=config.FONTS["body_bold"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", command=reset_pwd)
        btn_save.pack(pady=(0, 15))

    def handle_unlock_account(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showinfo("Select User", "Please select a user to unlock.")
            return

        user_id = self.user_tree.item(selected[0])["values"][0]
        username = self.user_tree.item(selected[0])["values"][1]

        db.execute_query("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s", (user_id,), commit=True)
        auth.log_audit("ACCOUNT_UNLOCKED", f"Account unlocked manually for user {username}")
        messagebox.showinfo("Account Unlocked", f"User '{username}' is now unlocked with failed attempts reset to 0.")
        self.load_users()

    def handle_toggle_active(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showinfo("Select User", "Please select a user to toggle status.")
            return

        user_id = self.user_tree.item(selected[0])["values"][0]
        username = self.user_tree.item(selected[0])["values"][1]

        # Prevent admin from deactivating oneself
        if user_id == auth.SessionManager.get_user_id():
            messagebox.showwarning("Restricted", "You cannot deactivate your own logged-in account.")
            return

        u = db.execute_query("SELECT is_active FROM users WHERE id = %s", (user_id,), fetchone=True)
        new_status = not u["is_active"]
        status_word = "activate" if new_status else "deactivate"

        if messagebox.askyesno("Confirm Status Change", f"Are you sure you want to {status_word} user '{username}'?"):
            db.execute_query("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id), commit=True)
            auth.log_audit("USER_STATUS_CHANGE", f"Changed status of user {username} to {'active' if new_status else 'inactive'}")
            self.load_users()

    def setup_audit_tab(self):
        bar = tk.Frame(self.tab_audit, bg=config.COLORS["surface"], padx=15, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        bar.pack(fill="x", pady=(0, 12))

        tk.Label(bar, text="Filter Action:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left", padx=(0, 5))
        self.combo_audit_action = ttk.Combobox(bar, values=["All Actions", "LOGIN_SUCCESS", "FAILED_LOGIN", "ACCOUNT_LOCKED", "SALE_COMPLETE", "STOCK_MOVEMENT", "PRODUCT_CREATE", "PRODUCT_UPDATE", "USER_CREATE"], state="readonly", width=18)
        self.combo_audit_action.current(0)
        self.combo_audit_action.pack(side="left", padx=(0, 15))
        self.combo_audit_action.bind("<<ComboboxSelected>>", lambda e: self.load_audit_logs())

        btn_refresh = tk.Button(bar, text="↻ Refresh Log", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], relief="flat", cursor="hand2", command=self.load_audit_logs)
        btn_refresh.pack(side="left")

        table_frame = tk.Frame(self.tab_audit, bg=config.COLORS["surface"], highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        cols = ("id", "time", "username", "action", "details", "ip")
        self.audit_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.audit_tree.heading("id", text="ID")
        self.audit_tree.heading("time", text="Timestamp")
        self.audit_tree.heading("username", text="Username / Actor")
        self.audit_tree.heading("action", text="Action Performed")
        self.audit_tree.heading("details", text="Event Details")
        self.audit_tree.heading("ip", text="IP Origin")

        self.audit_tree.column("id", width=40, anchor="center")
        self.audit_tree.column("time", width=140, anchor="center")
        self.audit_tree.column("username", width=120, anchor="w")
        self.audit_tree.column("action", width=160, anchor="center")
        self.audit_tree.column("details", width=400, anchor="w")
        self.audit_tree.column("ip", width=90, anchor="center")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=scroll_y.set)
        self.audit_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.load_audit_logs()

    def load_audit_logs(self):
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        action_filter = self.combo_audit_action.get()
        query = "SELECT id, created_at, username, action, details, ip_address FROM audit_log"
        params = []
        if action_filter != "All Actions":
            query += " WHERE action = %s"
            params.append(action_filter)

        query += " ORDER BY created_at DESC LIMIT 300"
        logs = db.execute_query(query, params, fetchall=True) or []

        for log in logs:
            t_str = log["created_at"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(log["created_at"], "strftime") else str(log["created_at"])
            self.audit_tree.insert(
                "",
                "end",
                values=(
                    log["id"],
                    t_str,
                    log["username"] or "System",
                    log["action"],
                    log["details"] or "-",
                    log["ip_address"]
                )
            )

    def apply_theme(self):
        """Updates Treeview tag colors when switching themes in place."""
        c = config.COLORS
        if hasattr(self, "user_tree") and self.user_tree.winfo_exists():
            self.user_tree.tag_configure("locked", foreground=c["danger"], font=config.FONTS["body_bold"])
            self.user_tree.tag_configure("inactive", foreground=c["text_muted"])

