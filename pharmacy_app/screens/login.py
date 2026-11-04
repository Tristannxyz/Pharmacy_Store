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

# ── Design tokens ──────────────────────────────────────────────────────────────
_BG          = "#060c1a"   # deep space background
_PANEL_L     = "#0b1c35"   # left panel navy
_PANEL_L2    = "#0d2244"   # left panel lighter stripe
_PANEL_R     = "#f8fafc"   # right panel off-white
_TEAL        = "#0d9488"   # primary teal
_TEAL_DARK   = "#0f766e"
_TEAL_GLOW   = "#14b8a6"
_LIME        = "#84cc16"   # accent lime (from logo green)
_CARD_BORDER = "#1e3a5f"
_TEXT_DIM    = "#64748b"
_TEXT_MUTED  = "#94a3b8"
_TEXT_WHITE  = "#f1f5f9"
_FIELD_BG    = "#f1f5f9"
_FIELD_BD    = "#cbd5e1"
_FIELD_FOCUS = "#0d9488"
_NAVY_DEEP   = "#020918"


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=_BG)
        self.parent          = parent
        self.on_login_success = on_login_success
        self._logo_photo     = None   # Pillow GC guard

        self.setup_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # MAIN LAYOUT
    # ──────────────────────────────────────────────────────────────────────────
    def setup_ui(self):
        # Full-screen canvas for background
        self.bg_canvas = tk.Canvas(self, bg=_BG, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self._on_resize)

        # Card wrapper (centered via canvas window)
        self.card_host = tk.Frame(self.bg_canvas, bg=_BG)
        self.card_win  = self.bg_canvas.create_window(0, 0, window=self.card_host, anchor="center")

        self._build_card()

        # Trigger initial centering after layout
        self.bg_canvas.update_idletasks()
        cw = self.bg_canvas.winfo_width()
        ch = self.bg_canvas.winfo_height()
        if cw > 1 and ch > 1:
            self.bg_canvas.coords(self.card_win, cw // 2, ch // 2)

    # ──────────────────────────────────────────────────────────────────────────
    # CARD  (outer glow border → split box)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_card(self):
        # Multi-layer glow border effect
        for i, (color, pad) in enumerate([
            ("#1e4d7b", 3),
            ("#0d9488", 1),
        ]):
            rim = tk.Frame(self.card_host, bg=color)
            rim.pack(padx=i * 2, pady=i * 2)
            if i == 0:
                inner_host = rim
        
        card_bg = tk.Frame(inner_host, bg=_PANEL_L)
        card_bg.pack(padx=1, pady=1)

        split = tk.Frame(card_bg, bg=_PANEL_L)
        split.pack()

        self._build_left_panel(split)
        self._build_right_panel(split)

    # ──────────────────────────────────────────────────────────────────────────
    # LEFT HERO PANEL
    # ──────────────────────────────────────────────────────────────────────────
    def _build_left_panel(self, parent):
        # Canvas-based left panel so we can paint decorative shapes
        lc = tk.Canvas(parent, bg=_PANEL_L, width=380, height=500,
                       highlightthickness=0, bd=0)
        lc.pack(side="left")

        # ── background decoration ──────────────────────────────────────────
        # Large translucent circle (top-right bloom)
        lc.create_oval(220, -60, 520, 240, fill=_PANEL_L2, outline="", tags="decor")
        # Bottom-left dark fill
        lc.create_oval(-100, 360, 200, 660, fill="#09192e", outline="", tags="decor")
        # Diagonal accent stripe
        lc.create_polygon(0, 480, 380, 380, 380, 420, 0, 520,
                          fill="#0a2040", outline="", tags="decor")
        lc.create_polygon(0, 510, 380, 410, 380, 425, 0, 535,
                          fill="#0b2344", outline="", tags="decor")
        # Top accent bar
        lc.create_rectangle(0, 0, 380, 4, fill=_TEAL, outline="")
        # Subtle grid dots
        for gx in range(20, 380, 40):
            for gy in range(30, 560, 40):
                lc.create_oval(gx-1, gy-1, gx+1, gy+1, fill="#112040", outline="")

        # ── content frame inside canvas ────────────────────────────────────
        content = tk.Frame(lc, bg=_PANEL_L)
        lc.create_window(35, 40, window=content, anchor="nw", width=310)

        # Logo
        logo_path = _ASSETS_DIR / "logo.png"
        if _PIL_AVAILABLE and logo_path.exists():
            try:
                _img = Image.open(logo_path).convert("RGBA").resize((80, 80), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(_img)
                tk.Label(content, image=self._logo_photo,
                         bg=_PANEL_L, bd=0).pack(anchor="w", pady=(0, 16))
            except Exception:
                self._fallback_emblem(content)
        else:
            self._fallback_emblem(content)

        # App name
        tk.Label(content, text="PharmaCare",
                 font=("Segoe UI", 28, "bold"),
                 bg=_PANEL_L, fg=_TEXT_WHITE).pack(anchor="w")

        # Teal rule under brand
        rule = tk.Frame(content, bg=_TEAL, height=3, width=50)
        rule.pack(anchor="w", pady=(4, 10))

        # Subtitle
        tk.Label(content,
                 text="Pharmacy Store Management\n& Knowledge Analytics",
                 font=("Segoe UI", 11),
                 bg=_PANEL_L, fg=_TEAL_GLOW,
                 justify="left").pack(anchor="w", pady=(0, 20))

        # Description
        tk.Label(content,
                 text="An integrated retail operations platform with\npredictive demand analysis, ML-powered\nforecasting, and real-time inventory health.",
                 font=("Segoe UI", 9),
                 bg=_PANEL_L, fg=_TEXT_MUTED,
                 justify="left").pack(anchor="w", pady=(0, 28))

        # ── feature pills ──────────────────────────────────────────────────
        pills = [
            ("⚡", "ML Forecasting",   "#0d3352", _TEAL_GLOW),
            ("📊", "Live Dashboard",   "#0a2e1a", "#4ade80"),
            ("🔐", "Role-Based Auth",  "#2d1a0e", "#fb923c"),
            ("💊", "Smart Inventory",  "#1a1040", "#a78bfa"),
        ]
        for icon, label, pill_bg, pill_fg in pills:
            pill = tk.Frame(content, bg=pill_bg,
                            highlightbackground=pill_fg,
                            highlightthickness=1)
            pill.pack(fill="x", pady=3, ipady=5, ipadx=8)
            tk.Label(pill, text=f"  {icon}  {label}",
                     font=("Segoe UI", 9, "bold"),
                     bg=pill_bg, fg=pill_fg,
                     anchor="w").pack(side="left")

        # ── bottom italic quote ────────────────────────────────────────────
        lc.create_window(35, 510, anchor="nw", width=310,
                         window=tk.Label(lc,
                             text='"Optimizing dispensary workflow through\nmachine learning and automated audit trails."',
                             font=("Segoe UI", 8, "italic"),
                             bg=_PANEL_L, fg="#3d5a80",
                             justify="left"))

    # ──────────────────────────────────────────────────────────────────────────
    # RIGHT FORM PANEL
    # ──────────────────────────────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=_PANEL_R, width=420)
        right.pack(side="right", fill="both", expand=True)
        right.pack_propagate(False)

        # Inner padded container — compact vertical padding to fit all chips
        form = tk.Frame(right, bg=_PANEL_R, padx=38, pady=26)
        form.pack(fill="both", expand=True)

        # ── secure badge ───────────────────────────────────────────────────
        badge_row = tk.Frame(form, bg=_PANEL_R)
        badge_row.pack(anchor="w", pady=(0, 10))
        badge = tk.Frame(badge_row, bg="#0f172a",
                         highlightbackground=_TEAL, highlightthickness=1)
        badge.pack(side="left")
        tk.Label(badge, text="  🔒  SECURE PORTAL  ",
                 font=("Segoe UI", 7, "bold"),
                 bg="#0f172a", fg=_TEAL_GLOW, pady=4).pack()

        # ── heading ────────────────────────────────────────────────────────
        tk.Label(form, text="Welcome Back",
                 font=("Segoe UI", 22, "bold"),
                 bg=_PANEL_R, fg="#0f172a").pack(anchor="w")
        tk.Label(form,
                 text="Sign in to access your designated workspace",
                 font=("Segoe UI", 9),
                 bg=_PANEL_R, fg=_TEXT_DIM).pack(anchor="w", pady=(2, 16))

        # ── username field ─────────────────────────────────────────────────
        self._field_label(form, "Username")
        self.ent_user = self._styled_entry(form)
        self.ent_user.pack(fill="x", pady=(0, 10))
        self.ent_user.focus_set()

        # ── password field ─────────────────────────────────────────────────
        self._field_label(form, "Password")
        pwd_row = tk.Frame(form, bg=_PANEL_R)
        pwd_row.pack(fill="x", pady=(0, 4))

        self.ent_pwd = self._styled_entry(pwd_row, show="•")
        self.ent_pwd.pack(side="left", fill="x", expand=True)

        self.is_pwd_visible = False
        self.btn_eye = tk.Button(
            pwd_row,
            text="👁",
            font=("Segoe UI Symbol", 10),
            bg="#e2e8f0", fg=_TEXT_DIM,
            activebackground=_TEAL, activeforeground="white",
            relief="flat", bd=0,
            highlightbackground=_FIELD_BD, highlightthickness=1,
            cursor="hand2", padx=10, pady=6,
            command=self._toggle_pwd
        )
        self.btn_eye.pack(side="right", padx=(6, 0))
        self.btn_eye.bind("<Enter>", lambda e: self.btn_eye.config(bg=_TEAL, fg="white"))
        self.btn_eye.bind("<Leave>", lambda e: self.btn_eye.config(
            bg="#ecfdf5" if self.is_pwd_visible else "#e2e8f0",
            fg=_TEAL if self.is_pwd_visible else _TEXT_DIM))

        # ── status message ─────────────────────────────────────────────────
        self.lbl_msg = tk.Label(form, text="",
                                font=("Segoe UI", 9),
                                bg=_PANEL_R, fg=config.COLORS["danger"],
                                wraplength=330, justify="left")
        self.lbl_msg.pack(anchor="w", pady=(2, 8))

        # ── sign-in button ─────────────────────────────────────────────────
        self.btn_login = tk.Button(
            form,
            text="Sign In to System   ➔",
            font=("Segoe UI", 11, "bold"),
            bg=_TEAL, fg="white",
            activebackground=_TEAL_DARK, activeforeground="white",
            relief="flat", bd=0,
            cursor="hand2",
            pady=10,
            command=self.handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 14))
        self.btn_login.bind("<Enter>", lambda e: self.btn_login.config(bg=_TEAL_DARK))
        self.btn_login.bind("<Leave>", lambda e: self.btn_login.config(bg=_TEAL))

        # ── divider with label ─────────────────────────────────────────────
        div_row = tk.Frame(form, bg=_PANEL_R)
        div_row.pack(fill="x", pady=(0, 8))
        tk.Frame(div_row, bg="#e2e8f0", height=1).pack(side="left", fill="x", expand=True, pady=6)
        tk.Label(div_row, text="  Quick Access  ",
                 font=("Segoe UI", 8),
                 bg=_PANEL_R, fg=_TEXT_DIM).pack(side="left")
        tk.Frame(div_row, bg="#e2e8f0", height=1).pack(side="left", fill="x", expand=True, pady=6)

        # ── role chips (2 × 2 grid) ────────────────────────────────────────
        chips_grid = tk.Frame(form, bg=_PANEL_R)
        chips_grid.pack(fill="x")

        roles = [
            ("👑  Administrator",   "admin",           "admin123",      "#0f172a", "#f1f5f9", "#94a3b8"),
            ("🎓  Instructor (ML)", "instructor",      "instructor123", "#1d4ed8", "#eff6ff", "#93c5fd"),
            ("📦  Inventory Clerk", "inventory_clerk", "clerk123",      "#0f766e", "#f0fdf4", "#6ee7b7"),
            ("💳  Sales Personnel", "sales_personnel", "sales123",      "#b45309", "#fffbeb", "#fcd34d"),
        ]
        for i, (lbl, u, p, fg, bg, bd_col) in enumerate(roles):
            r, c = divmod(i, 2)
            btn = tk.Button(
                chips_grid, text=lbl,
                font=("Segoe UI", 8, "bold"),
                bg=bg, fg=fg,
                activebackground=fg, activeforeground="white",
                relief="flat", bd=0,
                highlightthickness=1, highlightbackground=bd_col,
                cursor="hand2", padx=8, pady=6,
                command=lambda un=u, pw=p, lb=lbl: self.fill_quick(un, pw, lb)
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
            chips_grid.grid_columnconfigure(c, weight=1)

        # keybindings
        self.ent_user.bind("<Return>", lambda e: self.ent_pwd.focus_set())
        self.ent_pwd.bind("<Return>",  lambda e: self.handle_login())

    # ──────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────────────
    def _field_label(self, parent, text):
        tk.Label(parent, text=text,
                 font=("Segoe UI", 9, "bold"),
                 bg=_PANEL_R, fg="#334155").pack(anchor="w", pady=(0, 5))

    def _styled_entry(self, parent, show=None):
        """ttk Entry styled to look like a modern rounded input."""
        style = ttk.Style()
        style.configure("Login.TEntry",
                        fieldbackground=_FIELD_BG,
                        bordercolor=_FIELD_BD,
                        lightcolor=_FIELD_BD,
                        darkcolor=_FIELD_BD,
                        insertcolor="#0f172a",
                        padding=(10, 7))
        style.map("Login.TEntry",
                  bordercolor=[("focus", _FIELD_FOCUS)],
                  lightcolor=[("focus", _FIELD_FOCUS)],
                  darkcolor=[("focus", _FIELD_FOCUS)])
        kw = dict(font=("Segoe UI", 11), style="Login.TEntry")
        if show:
            kw["show"] = show
        return ttk.Entry(parent, **kw)

    def _fallback_emblem(self, parent):
        f = tk.Frame(parent, bg="#064e3b", width=48, height=48)
        f.pack(anchor="w", pady=(0, 14))
        f.pack_propagate(False)
        tk.Label(f, text="⚕", font=("Segoe UI Symbol", 22, "bold"),
                 bg="#064e3b", fg="#10b981").place(relx=0.5, rely=0.5, anchor="center")

    # ──────────────────────────────────────────────────────────────────────────
    # BACKGROUND DECORATIONS  (redrawn on resize)
    # ──────────────────────────────────────────────────────────────────────────
    def _on_resize(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100 or h < 100:
            return
        self.bg_canvas.coords(self.card_win, w // 2, h // 2)
        self.bg_canvas.delete("bg_decor")

        # Large ambient glow blobs
        self.bg_canvas.create_oval(-160, -160, 340, 340,
                                   fill="#071428", outline="", tags="bg_decor")
        self.bg_canvas.create_oval(-80, -80, 220, 220,
                                   fill="#09182e", outline="", tags="bg_decor")
        self.bg_canvas.create_oval(w-300, h-300, w+100, h+100,
                                   fill="#071830", outline="", tags="bg_decor")
        self.bg_canvas.create_oval(w-200, h-200, w+40, h+40,
                                   fill="#091e38", outline="", tags="bg_decor")

        # Teal accent rings
        cx, cy = w // 2, h // 2
        for r, alpha_color in [(420, "#071e30"), (480, "#061a2a"), (540, "#051525")]:
            self.bg_canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                       outline=alpha_color, width=1, tags="bg_decor")

        # Subtle watermark ⚕ bottom-right
        self.bg_canvas.create_text(w-50, h-50, text="⚕",
                                   font=("Segoe UI Symbol", 52),
                                   fill="#091830", tags="bg_decor")

        # Raise card on top of decorations
        self.bg_canvas.tag_raise(self.card_win)

    # ──────────────────────────────────────────────────────────────────────────
    # LOGIC
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_pwd(self):
        self.is_pwd_visible = not self.is_pwd_visible
        if self.is_pwd_visible:
            self.ent_pwd.config(show="")
            self.btn_eye.config(text="🙈", bg="#ecfdf5", fg=_TEAL)
        else:
            self.ent_pwd.config(show="•")
            self.btn_eye.config(text="👁", bg="#e2e8f0", fg=_TEXT_DIM)

    def fill_quick(self, username, password, role_label=""):
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, username)
        self.ent_pwd.delete(0, tk.END)
        self.ent_pwd.insert(0, password)
        self.lbl_msg.config(
            text=f"✓ Loaded  {role_label} credentials",
            fg=_TEAL)

    def handle_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pwd.get()

        if not username or not password:
            self.lbl_msg.config(text="Please enter both username and password.",
                                fg="#dc2626")
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
