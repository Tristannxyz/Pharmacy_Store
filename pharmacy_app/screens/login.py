import tkinter as tk
from tkinter import ttk
from pathlib import Path
try:
    from PIL import Image, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
import config
import auth

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# ── Design Tokens ─────────────────────────────────────────────────────────────
_BG           = "#04101d"   # deep radial canvas background
_PANEL_L      = "#071d32"   # deep navy left hero panel
_PANEL_R      = "#ffffff"   # clean white right form panel
_LIME         = "#a3e635"   # vibrant lime green (button & keyword accent)
_LIME_HOVER   = "#8fe024"   # slightly darker lime on hover
_TEXT_MUTED   = "#8ba3b8"   # soft blue-slate body text
_BORDER_CARD  = "#10334f"   # outer card elevation border
_FIELD_BG     = "#f8fafc"   # input field background
_FIELD_BORDER = "#e2e8f0"   # subtle input field border
_FIELD_FOCUS  = "#0d9488"   # input field focus ring


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=_BG)
        self.parent = parent
        self.on_login_success = on_login_success
        self._logo_photo = None  # Pillow GC protection

        self.setup_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN LAYOUT
    # ──────────────────────────────────────────────────────────────────────────
    def setup_ui(self):
        # Full-screen Canvas with concentric ambient glow rings
        self.bg_canvas = tk.Canvas(self, bg=_BG, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self._on_resize)

        # Card wrapper (centered on canvas)
        self.card_host = tk.Frame(self.bg_canvas, bg=_BG)
        self.card_win = self.bg_canvas.create_window(0, 0, window=self.card_host, anchor="center")

        self._build_card()

        # Initial layout pass to center the card
        self.bg_canvas.update_idletasks()
        cw = self.bg_canvas.winfo_width()
        ch = self.bg_canvas.winfo_height()
        if cw > 1 and ch > 1:
            self.bg_canvas.coords(self.card_win, cw // 2, ch // 2)

    # ──────────────────────────────────────────────────────────────────────────
    # CARD CONTAINER
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card(self):
        # Multi-layer outer elevation border
        glow_outer = tk.Frame(self.card_host, bg="#0b243b", padx=1, pady=1)
        glow_outer.pack()

        border_inner = tk.Frame(glow_outer, bg=_BORDER_CARD, padx=1, pady=1)
        border_inner.pack()

        split_box = tk.Frame(border_inner, bg=_PANEL_L)
        split_box.pack()

        self._build_left_panel(split_box)
        self._build_right_panel(split_box)

    # ──────────────────────────────────────────────────────────────────────────
    # LEFT PANEL (Hero, Logo, Headline & 4 Feature Items)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_left_panel(self, parent):
        left_frame = tk.Frame(parent, bg=_PANEL_L, padx=52, pady=44)
        left_frame.pack(side="left", fill="both", expand=True)

        # ── 1. Brand Logo + Name ──────────────────────────────────────────────
        brand_row = tk.Frame(left_frame, bg=_PANEL_L)
        brand_row.pack(anchor="w", pady=(0, 24))

        logo_path = _ASSETS_DIR / "logo.png"
        if _PIL_AVAILABLE and logo_path.exists():
            try:
                _img = Image.open(logo_path).convert("RGBA").resize((42, 42), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(_img)
                tk.Label(brand_row, image=self._logo_photo, bg=_PANEL_L, bd=0).pack(side="left", padx=(0, 12))
            except Exception:
                self._fallback_logo(brand_row)
        else:
            self._fallback_logo(brand_row)

        tk.Label(
            brand_row,
            text="PharmaCare",
            font=("Segoe UI", 25, "bold"),
            bg=_PANEL_L,
            fg="#ffffff"
        ).pack(side="left")

        # ── 2. Headline with highlighted "need" keyword ───────────────────────
        head_row1 = tk.Frame(left_frame, bg=_PANEL_L)
        head_row1.pack(anchor="w")
        tk.Label(
            head_row1,
            text="Know what you'll ",
            font=("Segoe UI", 23, "bold"),
            bg=_PANEL_L,
            fg="#ffffff"
        ).pack(side="left")
        tk.Label(
            head_row1,
            text="need",
            font=("Segoe UI", 23, "bold"),
            bg=_PANEL_L,
            fg=_LIME
        ).pack(side="left")

        head_row2 = tk.Frame(left_frame, bg=_PANEL_L)
        head_row2.pack(anchor="w", pady=(0, 14))
        tk.Label(
            head_row2,
            text="before the shelf runs out.",
            font=("Segoe UI", 23, "bold"),
            bg=_PANEL_L,
            fg="#ffffff"
        ).pack(side="left")

        # ── 3. Subtitle / Description ─────────────────────────────────────────
        tk.Label(
            left_frame,
            text="Pharmacy store management and knowledge analytics, with ML-powered forecasting and real-time inventory health.",
            font=("Segoe UI", 10),
            bg=_PANEL_L,
            fg=_TEXT_MUTED,
            wraplength=430,
            justify="left"
        ).pack(anchor="w", pady=(0, 24))

        # ── 4. Four Feature Items with Dividers ────────────────────────────────
        features = [
            ("📈", "#2dd4bf", "ML Forecasting", "Predictive demand analysis"),
            ("⊞",  "#38bdf8", "Live Dashboard", "Real-time inventory health"),
            ("🛡", "#fbbf24", "Role-Based Auth", "The right access for every role"),
            ("📦", "#a3e635", "Smart Inventory", "Reorder before the shelf runs out")
        ]

        for i, (icon, icon_col, title, subtitle) in enumerate(features):
            item_row = tk.Frame(left_frame, bg=_PANEL_L)
            item_row.pack(fill="x", pady=6)

            # Icon Badge Box (Dark rounded square)
            icon_box = tk.Frame(
                item_row,
                bg="#0c253d",
                width=44,
                height=44,
                highlightbackground="#143657",
                highlightthickness=1
            )
            icon_box.pack(side="left", padx=(0, 15))
            icon_box.pack_propagate(False)

            tk.Label(
                icon_box,
                text=icon,
                font=("Segoe UI Symbol", 15),
                bg="#0c253d",
                fg=icon_col
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Title & Subtitle Stack aligned directly beside the icon
            text_stack = tk.Frame(item_row, bg=_PANEL_L)
            text_stack.pack(side="left", anchor="w")

            tk.Label(
                text_stack,
                text=title,
                font=("Segoe UI", 11, "bold"),
                bg=_PANEL_L,
                fg="#ffffff",
                anchor="w"
            ).pack(anchor="w")

            tk.Label(
                text_stack,
                text=subtitle,
                font=("Segoe UI", 9),
                bg=_PANEL_L,
                fg=_TEXT_MUTED,
                anchor="w"
            ).pack(anchor="w")

            # Subtle horizontal divider between items
            if i < len(features) - 1:
                tk.Frame(left_frame, bg="#0d263e", height=1).pack(fill="x", pady=5)

    def _fallback_logo(self, parent):
        f = tk.Frame(parent, bg="#064e3b", width=42, height=42)
        f.pack(side="left", padx=(0, 12))
        f.pack_propagate(False)
        tk.Label(f, text="⚕", font=("Segoe UI Symbol", 20, "bold"), bg="#064e3b", fg="#10b981").place(relx=0.5, rely=0.5, anchor="center")

    # ──────────────────────────────────────────────────────────────────────────
    # RIGHT PANEL (Form, Inputs, Lime CTA, Quick Access)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=_PANEL_R)
        right.pack(side="right", fill="both", expand=True)

        form = tk.Frame(right, bg=_PANEL_R, padx=50, pady=40)
        form.pack(fill="both", expand=True)

        # ── 1. Welcome Back Heading ───────────────────────────────────────────
        tk.Label(
            form,
            text="Welcome back",
            font=("Segoe UI", 28, "bold"),
            bg=_PANEL_R,
            fg="#0f172a"
        ).pack(anchor="w")

        tk.Label(
            form,
            text="Sign in to access your designated workspace.",
            font=("Segoe UI", 10),
            bg=_PANEL_R,
            fg="#64748b"
        ).pack(anchor="w", pady=(3, 20))

        # ── 3. Username Field ─────────────────────────────────────────────────
        tk.Label(
            form,
            text="Username",
            font=("Segoe UI", 10, "bold"),
            bg=_PANEL_R,
            fg="#334155"
        ).pack(anchor="w", pady=(0, 6))

        self.ent_user = self._styled_entry(form)
        self.ent_user.pack(fill="x", pady=(0, 14))
        self.ent_user.focus_set()

        # ── 4. Password Field + Eye Toggle Button ─────────────────────────────
        tk.Label(
            form,
            text="Password",
            font=("Segoe UI", 10, "bold"),
            bg=_PANEL_R,
            fg="#334155"
        ).pack(anchor="w", pady=(0, 6))

        pwd_row = tk.Frame(form, bg=_PANEL_R)
        pwd_row.pack(fill="x", pady=(0, 4))

        self.ent_pwd = self._styled_entry(pwd_row, show="•")
        self.ent_pwd.pack(side="left", fill="x", expand=True)

        self.is_pwd_visible = False
        self.btn_eye = tk.Button(
            pwd_row,
            text="👁",
            font=("Segoe UI Symbol", 11),
            bg=_FIELD_BG,
            fg="#64748b",
            activebackground="#e2e8f0",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            highlightbackground=_FIELD_BORDER,
            highlightthickness=1,
            cursor="hand2",
            padx=12,
            pady=7,
            command=self._toggle_pwd
        )
        self.btn_eye.pack(side="right", padx=(8, 0))
        self.btn_eye.bind("<Enter>", lambda e: self.btn_eye.config(bg="#e2e8f0"))
        self.btn_eye.bind("<Leave>", lambda e: self.btn_eye.config(bg="#ecfdf5" if self.is_pwd_visible else _FIELD_BG))

        # ── 5. Feedback / Status Label ────────────────────────────────────────
        self.lbl_msg = tk.Label(
            form,
            text="",
            font=("Segoe UI", 10),
            bg=_PANEL_R,
            fg=config.COLORS["danger"],
            wraplength=400,
            justify="left"
        )
        self.lbl_msg.pack(anchor="w", pady=(2, 8))

        # ── 6. Vibrant Lime Sign-In Button ────────────────────────────────────
        self.btn_login = tk.Button(
            form,
            text="Sign in to system   ➔",
            font=("Segoe UI", 12, "bold"),
            bg=_LIME,
            fg="#0f172a",
            activebackground=_LIME_HOVER,
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=13,
            command=self.handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 16))
        self.btn_login.bind("<Enter>", lambda e: self.btn_login.config(bg=_LIME_HOVER))
        self.btn_login.bind("<Leave>", lambda e: self.btn_login.config(bg=_LIME))

        # ── 7. Quick Access Divider ───────────────────────────────────────────
        div_row = tk.Frame(form, bg=_PANEL_R)
        div_row.pack(fill="x", pady=(0, 12))
        tk.Frame(div_row, bg="#e2e8f0", height=1).pack(side="left", fill="x", expand=True, pady=6)
        tk.Label(div_row, text="   Quick access   ", font=("Segoe UI", 9), bg=_PANEL_R, fg="#94a3b8").pack(side="left")
        tk.Frame(div_row, bg="#e2e8f0", height=1).pack(side="left", fill="x", expand=True, pady=6)

        # ── 8. Quick Access Demo Pills (2x2 Grid) ─────────────────────────────
        chips_grid = tk.Frame(form, bg=_PANEL_R)
        chips_grid.pack(fill="x")

        roles = [
            ("Administrator",   "admin",           "admin123",      "#0d9488"),
            ("Instructor (ML)", "instructor",      "instructor123", "#2563eb"),
            ("Inventory Clerk", "inventory_clerk", "clerk123",      "#9333ea"),
            ("Sales Personnel", "sales_personnel", "sales123",      "#ea580c"),
        ]

        for i, (lbl, u, p, dot_col) in enumerate(roles):
            r, c = divmod(i, 2)
            self._create_quick_pill(chips_grid, r, c, lbl, u, p, dot_col)

        # Keybindings
        self.ent_user.bind("<Return>", lambda e: self.ent_pwd.focus_set())
        self.ent_pwd.bind("<Return>", lambda e: self.handle_login())

    def _create_quick_pill(self, parent, r, c, label_text, username, password, dot_col):
        """Creates a clean rounded-styled pill with a colored dot indicator and text."""
        pill = tk.Frame(
            parent,
            bg="#ffffff",
            highlightbackground="#e2e8f0",
            highlightthickness=1,
            cursor="hand2",
            padx=12,
            pady=8
        )
        pill.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
        parent.grid_columnconfigure(c, weight=1)

        dot = tk.Label(pill, text="●", font=("Segoe UI", 10), bg="#ffffff", fg=dot_col, cursor="hand2")
        dot.pack(side="left", padx=(0, 7))

        text_lbl = tk.Label(
            pill,
            text=label_text,
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            cursor="hand2"
        )
        text_lbl.pack(side="left")

        # Interactive click & hover behavior across the entire pill container
        def on_click(e):
            self.fill_quick(username, password, label_text)

        def on_enter(e):
            pill.config(bg="#f8fafc", highlightbackground="#cbd5e1")
            dot.config(bg="#f8fafc")
            text_lbl.config(bg="#f8fafc")

        def on_leave(e):
            pill.config(bg="#ffffff", highlightbackground="#e2e8f0")
            dot.config(bg="#ffffff")
            text_lbl.config(bg="#ffffff")

        for widget in (pill, dot, text_lbl):
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def _styled_entry(self, parent, show=None):
        """TTK Entry styled with soft modern slate background and teal focus ring."""
        style = ttk.Style()
        style.configure(
            "LoginModern.TEntry",
            fieldbackground=_FIELD_BG,
            bordercolor=_FIELD_BORDER,
            lightcolor=_FIELD_BORDER,
            darkcolor=_FIELD_BORDER,
            insertcolor="#0f172a",
            padding=(12, 9)
        )
        style.map(
            "LoginModern.TEntry",
            bordercolor=[("focus", _FIELD_FOCUS)],
            lightcolor=[("focus", _FIELD_FOCUS)],
            darkcolor=[("focus", _FIELD_FOCUS)]
        )
        kw = dict(font=("Segoe UI", 11), style="LoginModern.TEntry", width=30)
        if show:
            kw["show"] = show
        return ttk.Entry(parent, **kw)

    # ──────────────────────────────────────────────────────────────────────────
    # BACKGROUND CONCENTRIC RINGS
    # ──────────────────────────────────────────────────────────────────────────
    def _on_resize(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100 or h < 100:
            return

        self.bg_canvas.coords(self.card_win, w // 2, h // 2)
        self.bg_canvas.delete("bg_decor")

        cx, cy = w // 2, h // 2

        # Radial concentric rings matching screenshot
        ring_defs = [
            (260, "#082138", 1),
            (360, "#0a2842", 1),
            (480, "#09243c", 1),
            (620, "#071b2e", 1),
            (780, "#051524", 1)
        ]
        for radius, color, width in ring_defs:
            self.bg_canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline=color,
                width=width,
                tags="bg_decor"
            )

        # Soft corner watermark
        self.bg_canvas.create_text(
            w - 50, h - 50,
            text="⚕",
            font=("Segoe UI Symbol", 48),
            fill="#092136",
            tags="bg_decor"
        )

        self.bg_canvas.tag_raise(self.card_win)

    # ──────────────────────────────────────────────────────────────────────────
    # LOGIC & AUTHENTICATION (Unchanged)
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_pwd(self):
        self.is_pwd_visible = not self.is_pwd_visible
        if self.is_pwd_visible:
            self.ent_pwd.config(show="")
            self.btn_eye.config(text="🙈", bg="#ecfdf5", fg="#0d9488")
        else:
            self.ent_pwd.config(show="•")
            self.btn_eye.config(text="👁", bg=_FIELD_BG, fg="#64748b")

    def fill_quick(self, username, password, role_label=""):
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, username)
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, password)
        self.lbl_msg.config(
            text=f"✓ Loaded {role_label} credentials",
            fg="#0d9488"
        )

    def handle_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pwd.get()

        if not username or not password:
            self.lbl_msg.config(text="Please enter both username and password.", fg="#dc2626")
            return

        self.lbl_msg.config(text="Authenticating credentials…", fg="#0284c7")
        self.update_idletasks()

        success, msg, user_data = auth.authenticate_user(username, password)
        if success:
            self.lbl_msg.config(text="Login successful! Redirecting…", fg="#16a34a")
            self.on_login_success(user_data)
        else:
            self.lbl_msg.config(text=msg, fg="#dc2626")
            self.ent_pwd.delete(0, tk.END)
            self.ent_pwd.focus_set()
