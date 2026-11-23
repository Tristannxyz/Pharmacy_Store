/* ═══════════════════════════════════════════════════════════════════════════
   RestInPills — Complete Web Frontend Controller (app.js)
   Mirrors Login Screen, 60-FPS Canvas Animation, Settings Popover, & All 6 Screens
   ═══════════════════════════════════════════════════════════════════════════ */

const STATE = {
  user: null,
  currency: "$",
  dbName: "pharmacy",
  expiryWarnDays: 90,
  prefs: {
    theme: "light",
    language: "English",
    font: "Inter",
    text_size: "M",
  },
  activeScreen: "dashboard",
  settingsContext: null,
  // Dashboard cache
  dashboardData: null,
  // Inventory state
  invTab: "catalog",
  invData: null,
  invSearch: "",
  invChip: "All",
  invCatId: null,
  invSortCol: "name",
  invSortDesc: false,
  invSelectedIds: new Set(),
  invMovements: [],
  // POS state
  posTab: "pos",
  posSearch: "",
  posCatFilter: "All",
  cart: [],
  discountPct: 0,
  payMethod: "CASH",
  salesHistory: [],
  selectedInvoiceId: null,
  // Users state
  usersTab: "users",
  usersList: [],
  selectedUserId: null,
  auditLogs: [],
  auditActionFilter: "All Actions",
  // Knowledge Analysis state
  analysisTask: "product_demand",
  analysisTab: "prediction",
  analysisData: null,
  lastPredictionResult: null,
};

/* ───────────────────────────────────────────────────────────────────────────
   1. MULTILINGUAL TRANSLATION DICTIONARY (English / Filipino / Spanish)
   ─────────────────────────────────────────────────────────────────────────── */
const I18N = {
  English: {
    settings: "Settings",
    appearance: "Appearance",
    light_mode: "Light mode",
    dark_mode: "Dark mode",
    language: "Language",
    font: "Font",
    text_size: "Text size",
    hero_smart: "Smart",
    hero_ops: " pharmacy operations",
    hero_sub: "Pharmacy Store Management and Knowledge Analytics",
    f1_title: "Demand Insights",
    f1_desc: "See what will sell next week, before it does.",
    f2_title: "Expiry Guard",
    f2_desc: "Batch and expiry alerts that cut waste.",
    f3_title: "Stock Pulse",
    f3_desc: "Live shelf levels across every branch.",
    f4_title: "Team Access",
    f4_desc: "Each role sees only what it needs.",
    welcome: "Welcome back",
    sign_in_sub: "Sign in to access your designated workspace",
    username: "Username",
    password: "Password",
    sign_in_btn: "Sign in to system  →",
    quick_access: "Quick access",
    role_admin: "Administrator",
    role_instructor: "Instructor",
    role_clerk: "Inventory Clerk",
    role_sales: "Sales Personnel",
    brand_sub: "Pharmacy & Knowledge Studio",
    sign_out: "⏻  Sign Out",
    nav_dashboard: "⊞   Dashboard",
    nav_inventory: "◫   Inventory Management",
    nav_sales: "💳   Point of Sale (POS)",
    nav_users: "👥   User Management & Logs",
    nav_analysis: "📈   Knowledge Analysis Studio",
    nav_profile: "👤   My Profile",
    dash_sub: "Here is how the pharmacy is doing today.",
    refresh_data: "Refresh data",
    sales_today: "Sales Today",
    mtd_revenue: "Month-to-Date Revenue",
    total_products: "Total Products",
    low_stock_alerts: "Low-Stock Alerts",
    near_expiry_alerts: "Near-Expiry Alerts",
    top_performing: "Top Performing Product",
    current_month: "Current month",
    active_in_catalog: "Active in catalog",
    needs_restocking: "Needs restocking",
    trend_14d: "14-day sales revenue trend",
    top_5_prods: "Top 5 products by quantity sold",
    sales_by_cat: "Sales breakdown by category",
    stock_health: "Stock health distribution",
    prods_in_catalog: "products in catalog",
    healthy: "Healthy",
    low_stock: "Low stock",
    out_of_stock: "Out of stock",
  },
  Filipino: {
    settings: "Settings",
    appearance: "Hitsura",
    light_mode: "Light mode",
    dark_mode: "Dark mode",
    language: "Wika",
    font: "Font",
    text_size: "Laki ng teksto",
    hero_smart: "Matalinong",
    hero_ops: " operasyon ng parmasya",
    hero_sub: "Pamamahala ng Parmasya at Knowledge Analytics",
    f1_title: "Demand Insights",
    f1_desc: "Alamin ang mabenta sa susunod na linggo.",
    f2_title: "Expiry Guard",
    f2_desc: "Alerto sa batch at expiry upang iwas-sayang.",
    f3_title: "Stock Pulse",
    f3_desc: "Live na antas ng paninda sa bawat sangay.",
    f4_title: "Team Access",
    f4_desc: "Bawat tungkulin ay may angkop na access.",
    welcome: "Maligayang pagbabalik",
    sign_in_sub: "Mag-sign in upang buksan ang iyong workspace",
    username: "Username",
    password: "Password",
    sign_in_btn: "Mag-sign in sa system  →",
    quick_access: "Mabilis na access",
    role_admin: "Administrador",
    role_instructor: "Instruktor",
    role_clerk: "Klerk ng Imbentaryo",
    role_sales: "Kawani ng Benta",
    brand_sub: "Parmasya at Knowledge Studio",
    sign_out: "⏻  Mag-sign Out",
    nav_dashboard: "⊞   Dashboard",
    nav_inventory: "◫   Pamamahala ng Imbentaryo",
    nav_sales: "💳   Point of Sale (POS)",
    nav_users: "👥   Mga User at Logs",
    nav_analysis: "📈   Knowledge Analysis Studio",
    nav_profile: "👤   Aking Profile",
    dash_sub: "Narito ang lagay ng parmasya ngayong araw.",
    refresh_data: "I-refresh ang datos",
    sales_today: "Benta Ngayon",
    mtd_revenue: "Kita Ngayong Buwan",
    total_products: "Kabuuang Produkto",
    low_stock_alerts: "Alerto sa Mababang Stak",
    near_expiry_alerts: "Malapit Nang Mag-expire",
    top_performing: "Pinakamabentang Produkto",
    current_month: "Kasalukuyang buwan",
    active_in_catalog: "Aktibo sa katalogo",
    needs_restocking: "Kailangang dagdagan",
    trend_14d: "14-araw na tunguhin ng benta",
    top_5_prods: "Nangungunang 5 produkto sa benta",
    sales_by_cat: "Benta ayon sa kategorya",
    stock_health: "Kalagayan ng stak",
    prods_in_catalog: "produkto sa katalogo",
    healthy: "Maayos",
    low_stock: "Mababang stak",
    out_of_stock: "Walang stak",
  },
  Spanish: {
    settings: "Ajustes",
    appearance: "Apariencia",
    light_mode: "Modo claro",
    dark_mode: "Modo oscuro",
    language: "Idioma",
    font: "Fuente",
    text_size: "Tamaño de texto",
    hero_smart: "Operaciones",
    hero_ops: " inteligentes de farmacia",
    hero_sub: "Gestión de Farmacia y Analítica de Conocimiento",
    f1_title: "Demand Insights",
    f1_desc: "Vea qué se venderá la próxima semana.",
    f2_title: "Expiry Guard",
    f2_desc: "Alertas de lotes y caducidad sin desperdicio.",
    f3_title: "Stock Pulse",
    f3_desc: "Niveles de stock en vivo en cada sucursal.",
    f4_title: "Team Access",
    f4_desc: "Cada rol ve solo lo que necesita.",
    welcome: "Bienvenido de nuevo",
    sign_in_sub: "Inicie sesión para acceder a su espacio de trabajo",
    username: "Usuario",
    password: "Contraseña",
    sign_in_btn: "Iniciar sesión en el sistema  →",
    quick_access: "Acceso rápido",
    role_admin: "Administrador",
    role_instructor: "Instructor",
    role_clerk: "Encargado de Inventario",
    role_sales: "Personal de Ventas",
    brand_sub: "Estudio de Farmacia y Conocimiento",
    sign_out: "⏻  Cerrar Sesión",
    nav_dashboard: "⊞   Panel Principal",
    nav_inventory: "◫   Gestión de Inventario",
    nav_sales: "💳   Punto de Venta (POS)",
    nav_users: "👥   Usuarios y Registros",
    nav_analysis: "📈   Estudio de Analítica",
    nav_profile: "👤   Mi Perfil",
    dash_sub: "Así va la farmacia el día de hoy.",
    refresh_data: "Actualizar datos",
    sales_today: "Ventas de Hoy",
    mtd_revenue: "Ingresos del Mes",
    total_products: "Total de Productos",
    low_stock_alerts: "Alertas de Bajo Stock",
    near_expiry_alerts: "Alertas de Próximo Vencimiento",
    top_performing: "Producto Más Vendido",
    current_month: "Mes actual",
    active_in_catalog: "Activo en catálogo",
    needs_restocking: "Necesita reabastecimiento",
    trend_14d: "Tendencia de ingresos de 14 días",
    top_5_prods: "Top 5 productos por cantidad vendida",
    sales_by_cat: "Ventas por categoría",
    stock_health: "Distribución de salud del stock",
    prods_in_catalog: "productos en catálogo",
    healthy: "Saludable",
    low_stock: "Bajo stock",
    out_of_stock: "Sin stock",
  },
};

function t(key) {
  const dict = I18N[STATE.prefs.language] || I18N.English;
  return dict[key] || I18N.English[key] || key;
}

/* ───────────────────────────────────────────────────────────────────────────
   2. 60-FPS LOGIN BACKGROUND ANIMATION (Matches screens/login.py)
   ─────────────────────────────────────────────────────────────────────────── */
let loginAnimId = null;
const loginParticles = {
  phase: 0,
  crosses: [
    { rx: 0.14, ry: 0.12, size: 11, speed: 0.011, phase: 0.4, sway: 16 },
    { rx: 0.84, ry: 0.16, size: 14, speed: 0.009, phase: 1.9, sway: 20 },
    { rx: 0.76, ry: 0.48, size: 10, speed: 0.013, phase: 3.1, sway: 15 },
    { rx: 0.22, ry: 0.88, size: 13, speed: 0.010, phase: 4.5, sway: 18 },
    { rx: 0.88, ry: 0.78, size: 9,  speed: 0.014, phase: 5.7, sway: 14 },
  ],
  capsules: [
    { rx: 0.68, ry: 0.11, len: 24, rad: 6, angle: 0.55, speed: 0.008, rot: 0.35, phase: 0.8 },
    { rx: 0.89, ry: 0.38, len: 20, rad: 5, angle: -0.4, speed: 0.010, rot: -0.3, phase: 2.3 },
    { rx: 0.62, ry: 0.86, len: 22, rad: 5, angle: 0.75, speed: 0.009, rot: 0.28, phase: 4.1 },
  ],
  nodes: [
    { rx: 0.64, ry: 0.18, ax: 18, ay: 14, sx: 0.55, sy: 0.45, ph: 0.2, r: 3.5 },
    { rx: 0.78, ry: 0.26, ax: 22, ay: 16, sx: 0.42, sy: 0.52, ph: 1.4, r: 4.2 },
    { rx: 0.90, ry: 0.20, ax: 15, ay: 18, sx: 0.60, sy: 0.38, ph: 2.7, r: 3.0 },
    { rx: 0.72, ry: 0.42, ax: 20, ay: 15, sx: 0.48, sy: 0.46, ph: 3.5, r: 3.8 },
    { rx: 0.86, ry: 0.52, ax: 17, ay: 20, sx: 0.38, sy: 0.56, ph: 4.8, r: 4.2 },
    { rx: 0.75, ry: 0.68, ax: 21, ay: 14, sx: 0.50, sy: 0.40, ph: 5.4, r: 3.4 },
    { rx: 0.88, ry: 0.84, ax: 16, ay: 16, sx: 0.44, sy: 0.50, ph: 1.0, r: 3.8 },
  ],
};

function startLoginAnimation() {
  const canvas = document.getElementById("login-bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let lastTs = performance.now();

  function frame(now) {
    const loginView = document.getElementById("login-view");
    if (!loginView || loginView.classList.contains("hidden")) {
      loginAnimId = null;
      return;
    }
    const dt = Math.min(0.05, Math.max(0.004, (now - lastTs) / 1000));
    lastTs = now;
    loginParticles.phase += dt * 1.45;

    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth || 600;
    const h = canvas.clientHeight || 800;
    if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
    }
    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    const isDark = STATE.prefs.theme === "dark";
    const colWave1 = isDark ? "rgba(59, 114, 232, 0.24)" : "rgba(37, 99, 235, 0.16)";
    const colWave2 = isDark ? "rgba(29, 78, 216, 0.18)" : "rgba(96, 165, 250, 0.15)";
    const colNode  = isDark ? "rgba(59, 130, 246, 0.35)" : "rgba(37, 99, 235, 0.25)";
    const colEdge  = isDark ? "rgba(59, 130, 246, 0.16)" : "rgba(37, 99, 235, 0.12)";
    const colCross = isDark ? "rgba(59, 130, 246, 0.32)" : "rgba(37, 99, 235, 0.22)";
    const colPill  = isDark ? "rgba(96, 165, 250, 0.30)" : "rgba(37, 99, 235, 0.20)";

    const ph = loginParticles.phase;

    // 1. Dual Stock Pulse Sine Waves at Bottom
    [
      { base: 0.90, amp: 14, freq: 2.2, speed: 1.0, col: colWave1, lw: 2 },
      { base: 0.93, amp: 10, freq: 3.1, speed: -0.75, col: colWave2, lw: 1.5 },
    ].forEach((wv) => {
      ctx.beginPath();
      const baseY = h * wv.base;
      const steps = 42;
      for (let i = 0; i <= steps; i++) {
        const x = (w * i) / steps;
        const angle = (i / steps) * Math.PI * wv.freq + ph * wv.speed;
        const y = baseY + Math.sin(angle) * wv.amp + Math.cos(angle * 0.6) * (wv.amp * 0.35);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = wv.col;
      ctx.lineWidth = wv.lw;
      ctx.stroke();
    });

    // 2. Knowledge Analytics Constellation Nodes & Edges
    const coords = loginParticles.nodes.map((nd) => ({
      x: nd.rx * w + Math.sin(ph * nd.sx + nd.ph) * nd.ax,
      y: nd.ry * h + Math.cos(ph * nd.sy + nd.ph) * nd.ay,
      r: nd.r + Math.sin(ph * 1.2 + nd.ph) * 0.7,
    }));

    const maxDistSq = Math.pow(Math.min(w, h) * 0.26, 2);
    ctx.strokeStyle = colEdge;
    ctx.lineWidth = 1;
    for (let i = 0; i < coords.length; i++) {
      for (let j = i + 1; j < coords.length; j++) {
        const dx = coords[i].x - coords[j].x;
        const dy = coords[i].y - coords[j].y;
        if (dx * dx + dy * dy < maxDistSq) {
          ctx.beginPath();
          ctx.moveTo(coords[i].x, coords[i].y);
          ctx.lineTo(coords[j].x, coords[j].y);
          ctx.stroke();
        }
      }
    }
    coords.forEach((c) => {
      ctx.beginPath();
      ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
      ctx.fillStyle = colNode;
      ctx.fill();
    });

    // 3. Drifting Hollow Medical Crosses (✚)
    ctx.strokeStyle = colCross;
    ctx.lineWidth = 1.6;
    loginParticles.crosses.forEach((cr) => {
      cr.ry -= cr.speed * dt;
      if (cr.ry < -0.06) cr.ry = 1.06;
      const cx = cr.rx * w + Math.sin(ph * 0.7 + cr.phase) * cr.sway;
      const cy = cr.ry * h;
      const s = cr.size;
      const a = s * 0.36;
      ctx.beginPath();
      ctx.moveTo(cx - a, cy - s);
      ctx.lineTo(cx + a, cy - s);
      ctx.lineTo(cx + a, cy - a);
      ctx.lineTo(cx + s, cy - a);
      ctx.lineTo(cx + s, cy + a);
      ctx.lineTo(cx + a, cy + a);
      ctx.lineTo(cx + a, cy + s);
      ctx.lineTo(cx - a, cy + s);
      ctx.lineTo(cx - a, cy + a);
      ctx.lineTo(cx - s, cy + a);
      ctx.lineTo(cx - s, cy - a);
      ctx.lineTo(cx - a, cy - a);
      ctx.closePath();
      ctx.stroke();
    });

    // 4. Floating Tilted Pill Capsules
    ctx.strokeStyle = colPill;
    ctx.lineWidth = 1.6;
    loginParticles.capsules.forEach((cp) => {
      cp.ry -= cp.speed * dt;
      if (cp.ry < -0.06) cp.ry = 1.06;
      const cx = cp.rx * w + Math.cos(ph * 0.55 + cp.phase) * 14;
      const cy = cp.ry * h;
      const ang = cp.angle + Math.sin(ph * cp.rot + cp.phase) * 0.25;
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(ang);
      const hl = cp.len * 0.5;
      const r = cp.rad;
      ctx.beginPath();
      ctx.roundRect(-hl, -r, cp.len, r * 2, r);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, -r);
      ctx.lineTo(0, r);
      ctx.stroke();
      ctx.restore();
    });

    ctx.restore();
    loginAnimId = requestAnimationFrame(frame);
  }

  if (!loginAnimId) {
    loginAnimId = requestAnimationFrame(frame);
  }
}

/* ───────────────────────────────────────────────────────────────────────────
   3. SETTINGS POPOVER & GLOBAL APPEARANCE / TYPOGRAPHY / LANGUAGE
   ─────────────────────────────────────────────────────────────────────────── */
function applyPrefsToDOM() {
  const html = document.documentElement;
  html.setAttribute("data-theme", STATE.prefs.theme || "light");
  html.setAttribute("data-font", STATE.prefs.font || "Inter");
  html.setAttribute("data-size", STATE.prefs.text_size || "M");

  // Update Settings Popover active states
  const btnLight = document.getElementById("btn-theme-light");
  const btnDark = document.getElementById("btn-theme-dark");
  if (btnLight && btnDark) {
    btnLight.classList.toggle("active", STATE.prefs.theme === "light");
    btnDark.classList.toggle("active", STATE.prefs.theme === "dark");
  }
  const selLang = document.getElementById("select-language");
  if (selLang) selLang.value = STATE.prefs.language || "English";

  const selFont = document.getElementById("select-font");
  if (selFont) selFont.value = STATE.prefs.font || "Inter";

  document.querySelectorAll(".pop-size-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-size") === STATE.prefs.text_size);
  });

  // Translate static [data-i18n] elements
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = t(key);
  });

  // Re-render sidebar and active screen if logged in so whole content updates live
  if (STATE.user) {
    renderSidebar();
    renderActiveScreen(false);
  }
}

async function syncPrefsToBackend() {
  try {
    await fetch("/api/prefs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(STATE.prefs),
    });
  } catch (e) {
    // Non-blocking
  }
}

function toggleSettingsPopover(context) {
  const pop = document.getElementById("settings-popover");
  if (!pop) return;
  if (!pop.classList.contains("hidden") && STATE.settingsContext === context) {
    closeSettingsPopover();
    return;
  }
  STATE.settingsContext = context;
  pop.classList.remove("pos-login", "pos-sidebar", "hidden");
  pop.classList.add(context === "login" ? "pos-login" : "pos-sidebar");
}

function closeSettingsPopover() {
  const pop = document.getElementById("settings-popover");
  if (pop) pop.classList.add("hidden");
  STATE.settingsContext = null;
}

function setThemeMode(mode) {
  STATE.prefs.theme = mode;
  applyPrefsToDOM();
  syncPrefsToBackend();
}

function setLanguage(lang) {
  STATE.prefs.language = lang;
  applyPrefsToDOM();
  syncPrefsToBackend();
}

function setFontFamily(font) {
  STATE.prefs.font = font;
  applyPrefsToDOM();
  syncPrefsToBackend();
}

function setTextSize(sz) {
  STATE.prefs.text_size = sz;
  applyPrefsToDOM();
  syncPrefsToBackend();
}

/* ───────────────────────────────────────────────────────────────────────────
   4. AUTHENTICATION, QUICK ACCESS & RBAC NAVIGATION
   ─────────────────────────────────────────────────────────────────────────── */
function togglePasswordVisibility() {
  const inp = document.getElementById("login-password");
  const btn = document.getElementById("btn-toggle-pwd");
  if (!inp || !btn) return;
  if (inp.type === "password") {
    inp.type = "text";
    btn.textContent = "🙈";
  } else {
    inp.type = "password";
    btn.textContent = "👁";
  }
}

function fillQuickCredentials(username, password, roleLabel) {
  const u = document.getElementById("login-username");
  const p = document.getElementById("login-password");
  const msg = document.getElementById("login-msg");
  if (u) u.value = username;
  if (p) p.value = password;
  if (msg) {
    msg.style.color = "var(--accent)";
    msg.textContent = `✓ Loaded ${roleLabel} credentials`;
  }
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const u = (document.getElementById("login-username")?.value || "").trim();
  const p = document.getElementById("login-password")?.value || "";
  const msg = document.getElementById("login-msg");

  if (!u || !p) {
    if (msg) {
      msg.style.color = "#dc2626";
      msg.textContent = "Please enter both username and password.";
    }
    return;
  }

  if (msg) {
    msg.style.color = "#0284c7";
    msg.textContent = "Authenticating credentials…";
  }

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      if (msg) {
        msg.style.color = "#dc2626";
        msg.textContent = data.message || "Invalid username or password.";
      }
      const pEl = document.getElementById("login-password");
      if (pEl) pEl.value = "";
      return;
    }
    if (msg) {
      msg.style.color = "#16a34a";
      msg.textContent = "Login successful! Redirecting…";
    }
    STATE.user = data.user;
    closeSettingsPopover();
    enterAppShell();
  } catch (err) {
    if (msg) {
      msg.style.color = "#dc2626";
      msg.textContent = `Connection error: ${err.message}`;
    }
  }
}

async function handleLogout() {
  if (!confirm("Are you sure you want to log out of your session?")) return;
  closeSettingsPopover();
  try {
    await fetch("/api/auth/logout", { method: "POST" });
  } catch (e) {}
  STATE.user = null;
  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("login-view").classList.remove("hidden");
  const pEl = document.getElementById("login-password");
  if (pEl) pEl.value = "";
  const msg = document.getElementById("login-msg");
  if (msg) msg.textContent = "";
  startLoginAnimation();
}

function isNavAllowed(key) {
  const perms = STATE.user?.permissions || [];
  if (key === "dashboard") return perms.includes("dashboard_view") || perms.length === 0;
  if (key === "inventory") return perms.includes("inventory_view");
  if (key === "sales") return perms.includes("sales_pos") || perms.includes("sales_history");
  if (key === "users") return perms.includes("users_manage");
  if (key === "analysis") return perms.includes("analysis_input_predict");
  if (key === "profile") return perms.includes("profile_view") || perms.length === 0;
  return true;
}

function getInitials(fullName) {
  const words = (fullName || "System Administrator").trim().split(/\s+/);
  return words.slice(0, 2).map((w) => w[0]?.toUpperCase() || "").join("") || "SA";
}

function renderSidebar() {
  if (!STATE.user) return;
  document.getElementById("sidebar-user-avatar").textContent = getInitials(STATE.user.full_name);
  document.getElementById("sidebar-user-name").textContent = STATE.user.full_name;
  document.getElementById("sidebar-user-role").textContent = STATE.user.role_display;

  const navItems = [
    { key: "dashboard", label: t("nav_dashboard") },
    { key: "inventory", label: t("nav_inventory") },
    { key: "sales", label: t("nav_sales") },
    { key: "users", label: t("nav_users") },
    { key: "analysis", label: t("nav_analysis") },
    { key: "profile", label: t("nav_profile") },
  ].filter((item) => isNavAllowed(item.key));

  const navEl = document.getElementById("sidebar-nav");
  navEl.innerHTML = navItems
    .map(
      (item) => `
      <button type="button" class="nav-item-btn ${STATE.activeScreen === item.key ? "active" : ""}" onclick="navigateTo('${item.key}')">
        ${escapeHtml(item.label)}
      </button>
    `
    )
    .join("");
}

function enterAppShell() {
  document.getElementById("login-view").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  STATE.activeScreen = "dashboard";
  renderSidebar();
  navigateTo("dashboard");
}

function navigateTo(screenKey) {
  closeSettingsPopover();
  if (!isNavAllowed(screenKey)) {
    showToast("Access Denied: You do not have permission to access this module.");
    return;
  }
  STATE.activeScreen = screenKey;
  renderSidebar();
  renderActiveScreen(true);
}

async function renderActiveScreen(fetchFresh = true) {
  const key = STATE.activeScreen;
  if (key === "dashboard") await renderDashboardScreen(fetchFresh);
  else if (key === "inventory") await renderInventoryScreen(fetchFresh);
  else if (key === "sales") await renderSalesScreen(fetchFresh);
  else if (key === "users") await renderUsersScreen(fetchFresh);
  else if (key === "analysis") await renderAnalysisScreen(fetchFresh);
  else if (key === "profile") renderProfileScreen();
}

/* ───────────────────────────────────────────────────────────────────────────
   5. SCREEN 1: EXECUTIVE DASHBOARD (Matches screens/dashboard.py)
   ─────────────────────────────────────────────────────────────────────────── */
function kpiTileSvg(type, color) {
  if (type === "trend") {
    return `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M4 17L9.5 11.5L13.5 14.5L20 7M20 7H15M20 7V12" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }
  if (type === "card") {
    return `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="2.5" stroke="${color}" stroke-width="2.1"/><path d="M3 10H21" stroke="${color}" stroke-width="2.1"/><rect x="6" y="13.5" width="4" height="2.2" fill="${color}"/></svg>`;
  }
  if (type === "box") {
    return `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 3L20 7.5V16.5L12 21L4 16.5V7.5L12 3Z" stroke="${color}" stroke-width="2" stroke-linejoin="round"/><path d="M12 12L20 7.5M12 12V21M12 12L4 7.5" stroke="${color}" stroke-width="2"/></svg>`;
  }
  if (type === "alert") {
    return `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 4L21 19H3L12 4Z" stroke="${color}" stroke-width="2.1" stroke-linejoin="round"/><path d="M12 10V14" stroke="${color}" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="16.8" r="1.1" fill="${color}"/></svg>`;
  }
  if (type === "clock") {
    return `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8.5" stroke="${color}" stroke-width="2.1"/><path d="M12 7.5V12L15.5 12" stroke="${color}" stroke-width="2.1" stroke-linecap="round"/></svg>`;
  }
  return `<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 3.5L14.7 9L20.8 9.9L16.4 14.2L17.4 20.3L12 17.4L6.6 20.3L7.6 14.2L3.2 9.9L9.3 9L12 3.5Z" stroke="${color}" stroke-width="2" stroke-linejoin="round"/></svg>`;
}

async function renderDashboardScreen(fetchFresh = true) {
  const container = document.getElementById("screen-container");
  if (fetchFresh || !STATE.dashboardData) {
    const res = await fetch("/api/dashboard");
    STATE.dashboardData = await res.json();
  }
  const d = STATE.dashboardData;
  const m = d.metrics;
  const sh = d.stock_health;
  const user = STATE.user || { username: "admin", full_name: "System Administrator", role_display: "Administrator" };

  const topProdName = m.top_product_name && m.top_product_name.length > 18 ? m.top_product_name.slice(0, 18).trim() : m.top_product_name;
  const maxTopQty = Math.max(1, ...(d.top_5_products || []).map((p) => p.qty));
  const top5Html = (d.top_5_products || [])
    .map((p, idx) => {
      const pct = Math.round((p.qty / maxTopQty) * 100);
      const fillCol = idx === 0 ? "#a3e635" : "#2563eb";
      return `
        <div class="bar-row">
          <div class="bar-label" title="${escapeHtml(p.full_name)}">${escapeHtml(p.name)}</div>
          <div class="pill-track"><div class="pill-fill" style="width:${pct}%;background:${fillCol}"></div></div>
          <div class="bar-qty">${p.qty}</div>
        </div>
      `;
    })
    .join("");

  const catColors = ["#0d9488", "#2563eb", "#a3e635"];
  const cats = d.sales_by_category || [];
  const topCat = cats[0] || { name: "Analgesics", pct: 79 };
  const legendHtml = cats
    .map(
      (c, i) => `
      <div class="legend-item">
        <div class="legend-left">
          <span class="legend-dot" style="background:${catColors[i % catColors.length]}"></span>
          <span>${escapeHtml(c.name)}</span>
        </div>
        <span class="legend-pct">${c.pct}%</span>
      </div>
    `
    )
    .join("");

  const shTotal = Math.max(1, sh.total);
  const shRows = [
    { label: t("healthy"), count: sh.healthy, color: "#0d9488" },
    { label: t("low_stock"), count: sh.low_stock, color: "#f59e0b" },
    { label: t("out_of_stock"), count: sh.out_of_stock, color: "#ef4444" },
  ]
    .map((r) => {
      const pct = r.count > 0 ? Math.max(6, Math.round((r.count / shTotal) * 100)) : 0;
      return `
        <div class="bar-row">
          <div class="bar-label">${escapeHtml(r.label)}</div>
          <div class="pill-track"><div class="pill-fill" style="width:${pct}%;background:${r.color}"></div></div>
          <div class="bar-qty">${r.count}</div>
        </div>
      `;
    })
    .join("");

  const welcomeGreeting =
    STATE.prefs.language === "Filipino"
      ? `Maligayang pagbabalik, ${user.full_name}`
      : STATE.prefs.language === "Spanish"
      ? `Bienvenido de nuevo, ${user.full_name}`
      : `Welcome back, ${user.full_name}`;

  const roleBadgeLabel =
    STATE.prefs.language === "Filipino"
      ? `Tungkulin: ${user.role_display}`
      : STATE.prefs.language === "Spanish"
      ? `Rol: ${user.role_display}`
      : `Role: ${user.role_display}`;

  container.innerHTML = `
    <div class="dash-status-line">
      <span class="status-dot">●</span>
      <span>Database connected (${escapeHtml(STATE.dbName)})  •  User: ${escapeHtml(user.username)} (${escapeHtml(user.role_display)})</span>
    </div>

    <div class="dash-header-row">
      <div>
        <h1 class="dash-greeting-title">${escapeHtml(welcomeGreeting)}</h1>
        <p class="dash-greeting-sub">${escapeHtml(t("dash_sub"))}</p>
      </div>
      <div class="dash-header-actions">
        <button type="button" class="btn-surface" onclick="renderDashboardScreen(true)">${escapeHtml(t("refresh_data"))}</button>
        <div class="role-lime-badge">${escapeHtml(roleBadgeLabel)}</div>
      </div>
    </div>

    <!-- 6 KPI Cards Grid -->
    <div class="dash-kpi-grid">
      <div class="dash-kpi-card">
        <div class="kpi-icon-tile" style="background:var(--tile-trend-bg)">${kpiTileSvg("trend", "#0d9488")}</div>
        <div>
          <div class="kpi-card-title">${escapeHtml(t("sales_today"))}</div>
          <div class="kpi-card-value">${STATE.currency}${m.sales_today.toFixed(2)}</div>
          <div class="kpi-card-sub">${m.sales_today_count} transactions</div>
        </div>
      </div>

      <div class="dash-kpi-card">
        <div class="kpi-icon-tile" style="background:var(--tile-card-bg)">${kpiTileSvg("card", "#2563eb")}</div>
        <div>
          <div class="kpi-card-title">${escapeHtml(t("mtd_revenue"))}</div>
          <div class="kpi-card-value">${STATE.currency}${m.monthly_revenue.toFixed(2)}</div>
          <div class="kpi-card-sub">${escapeHtml(t("current_month"))}</div>
        </div>
      </div>

      <div class="dash-kpi-card">
        <div class="kpi-icon-tile" style="background:var(--tile-box-bg)">${kpiTileSvg("box", "#64748b")}</div>
        <div>
          <div class="kpi-card-title">${escapeHtml(t("total_products"))}</div>
          <div class="kpi-card-value">${m.total_products}</div>
          <div class="kpi-card-sub">${escapeHtml(t("active_in_catalog"))}</div>
        </div>
      </div>

      <div class="dash-kpi-card">
        <div class="kpi-icon-tile" style="background:var(--tile-alert-bg)">${kpiTileSvg("alert", "#ef4444")}</div>
        <div>
          <div class="kpi-card-title">${escapeHtml(t("low_stock_alerts"))}</div>
          <div class="kpi-card-value">${m.low_stock_count}</div>
          <div class="kpi-card-sub">${escapeHtml(t("needs_restocking"))}</div>
        </div>
      </div>

      <div class="dash-kpi-card">
        <div class="kpi-icon-tile" style="background:var(--tile-clock-bg)">${kpiTileSvg("clock", "#f59e0b")}</div>
        <div>
          <div class="kpi-card-title">${escapeHtml(t("near_expiry_alerts"))}</div>
          <div class="kpi-card-value">${m.near_expiry_count}</div>
          <div class="kpi-card-sub">Within ${STATE.expiryWarnDays} days</div>
        </div>
      </div>

      <div class="dash-kpi-card">
        <div class="kpi-icon-tile" style="background:var(--tile-star-bg)">${kpiTileSvg("star", "#0284c7")}</div>
        <div>
          <div class="kpi-card-title">${escapeHtml(t("top_performing"))}</div>
          <div class="kpi-card-value compact">${escapeHtml(topProdName)}</div>
          <div class="kpi-card-sub">${m.top_product_qty} units sold</div>
        </div>
      </div>
    </div>

    <!-- 4 Analytics Cards Grid -->
    <div class="dash-charts-grid">
      <!-- Card 1: 14-day sales revenue trend -->
      <div class="dash-chart-card">
        <div class="chart-card-title">${escapeHtml(t("trend_14d"))}</div>
        <div class="trend-canvas-wrap">
          <canvas id="dash-trend-canvas"></canvas>
        </div>
      </div>

      <!-- Card 2: Top 5 products by quantity sold -->
      <div class="dash-chart-card">
        <div class="chart-card-title">${escapeHtml(t("top_5_prods"))}</div>
        <div class="bar-list">${top5Html}</div>
      </div>

      <!-- Card 3: Sales breakdown by category -->
      <div class="dash-chart-card">
        <div class="chart-card-title">${escapeHtml(t("sales_by_cat"))}</div>
        <div class="donut-layout">
          <div class="donut-wrap">
            <canvas id="dash-donut-canvas" width="185" height="185"></canvas>
            <div class="donut-center">
              <div class="donut-pct">${topCat.pct}%</div>
              <div class="donut-cat">${escapeHtml(topCat.name)}</div>
            </div>
          </div>
          <div class="donut-legend">${legendHtml}</div>
        </div>
      </div>

      <!-- Card 4: Stock health distribution -->
      <div class="dash-chart-card">
        <div class="chart-card-title">${escapeHtml(t("stock_health"))}</div>
        <div class="stock-health-hero">
          <span class="stock-health-big">${sh.total}</span>
          <span class="stock-health-sub">${escapeHtml(t("prods_in_catalog"))}</span>
        </div>
        <div class="bar-list">${shRows}</div>
        <div class="stock-health-footer">${sh.near_expiry} products expire within ${STATE.expiryWarnDays} days.</div>
      </div>
    </div>
  `;

  drawDashboardTrendChart(d.trend_14d || []);
  drawDashboardDonutChart(cats);
}

function drawDashboardTrendChart(points) {
  const canvas = document.getElementById("dash-trend-canvas");
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 520;
  const h = 215;
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const isDark = STATE.prefs.theme === "dark";
  const gridCol = isDark ? "#1a2436" : "#f1f5f9";
  const textCol = isDark ? "#64748b" : "#94a3b8";
  const surfaceCol = isDark ? "#131c2e" : "#ffffff";

  const padL = 38, padR = 16, padT = 14, padB = 28;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const maxRev = Math.max(100, ...points.map((p) => p.revenue));
  const yMax = Math.ceil(maxRev / 25) * 25;
  const yTicks = [0, 25, 50, 75, 100].map((t) => Math.round((t / 100) * yMax));

  ctx.font = `11px ${getComputedStyle(document.documentElement).getPropertyValue("--font-family")}`;
  ctx.fillStyle = textCol;
  ctx.strokeStyle = gridCol;
  ctx.lineWidth = 1;

  yTicks.forEach((tv) => {
    const y = padT + plotH - (tv / yMax) * plotH;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText(String(tv), padL - 8, y);
  });

  if (!points.length) {
    ctx.textAlign = "center";
    ctx.fillText("No recent sales recorded", w / 2, h / 2);
    return;
  }

  const coords = points.map((p, idx) => ({
    x: padL + (points.length === 1 ? plotW / 2 : (idx / (points.length - 1)) * plotW),
    y: padT + plotH - (Math.min(yMax, p.revenue) / yMax) * plotH,
    label: p.date,
  }));

  // Gradient fill underneath
  ctx.beginPath();
  ctx.moveTo(coords[0].x, padT + plotH);
  coords.forEach((c) => ctx.lineTo(c.x, c.y));
  ctx.lineTo(coords[coords.length - 1].x, padT + plotH);
  ctx.closePath();
  ctx.fillStyle = "rgba(20, 184, 166, 0.14)";
  ctx.fill();

  // Line
  ctx.beginPath();
  coords.forEach((c, i) => (i === 0 ? ctx.moveTo(c.x, c.y) : ctx.lineTo(c.x, c.y)));
  ctx.strokeStyle = "#0d9488";
  ctx.lineWidth = 2.3;
  ctx.stroke();

  // Markers & X labels
  coords.forEach((c) => {
    ctx.beginPath();
    ctx.arc(c.x, c.y, 4.2, 0, Math.PI * 2);
    ctx.fillStyle = surfaceCol;
    ctx.fill();
    ctx.strokeStyle = "#0d9488";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = textCol;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(c.label, c.x, padT + plotH + 8);
  });
}

function drawDashboardDonutChart(cats) {
  const canvas = document.getElementById("dash-donut-canvas");
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const size = 185;
  canvas.width = size * dpr;
  canvas.height = size * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const cx = size / 2;
  const cy = size / 2;
  const rOuter = 78;
  const rInner = 55;
  const palette = ["#0d9488", "#2563eb", "#a3e635"];
  const isDark = STATE.prefs.theme === "dark";
  const surfaceCol = isDark ? "#131c2e" : "#ffffff";

  const vals = cats.map((c) => Math.max(0.5, c.pct));
  const total = vals.reduce((a, b) => a + b, 0) || 1;
  let startAngle = -Math.PI / 2;

  vals.forEach((v, idx) => {
    const slice = (v / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, rOuter, startAngle, startAngle + slice);
    ctx.arc(cx, cy, rInner, startAngle + slice, startAngle, true);
    ctx.closePath();
    ctx.fillStyle = palette[idx % palette.length];
    ctx.fill();
    ctx.strokeStyle = surfaceCol;
    ctx.lineWidth = 2.5;
    ctx.stroke();
    startAngle += slice;
  });
}

/* ───────────────────────────────────────────────────────────────────────────
   6. SCREEN 2: INVENTORY MANAGEMENT (Matches screens/inventory.py)
   ─────────────────────────────────────────────────────────────────────────── */
async function renderInventoryScreen(fetchFresh = true) {
  const container = document.getElementById("screen-container");
  if (fetchFresh || !STATE.invData) {
    const res = await fetch("/api/inventory");
    STATE.invData = await res.json();
  }
  const canEdit = (STATE.user?.permissions || []).includes("inventory_edit");
  const k = STATE.invData.kpis;

  container.innerHTML = `
    <div class="screen-top-bar">
      <div>
        <h1 class="screen-title">Inventory Management</h1>
      </div>
      <div class="tab-pills-bar">
        <button type="button" class="tab-pill-btn ${STATE.invTab === "catalog" ? "active" : ""}" onclick="switchInvTab('catalog')">Product Catalog</button>
        <button type="button" class="tab-pill-btn ${STATE.invTab === "movements" ? "active" : ""}" onclick="switchInvTab('movements')">Stock Movements</button>
        <button type="button" class="tab-pill-btn ${STATE.invTab === "meta" ? "active" : ""}" onclick="switchInvTab('meta')">Suppliers &amp; Categories</button>
      </div>
      ${
        canEdit
          ? `<div class="action-btns-row">
               <button type="button" class="btn-surface" onclick="openStockMovementModal()">⇅ Stock In / Out</button>
               <button type="button" class="btn-lime" onclick="openProductModal()">+ Add Product</button>
             </div>`
          : ""
      }
    </div>

    <div class="inv-kpi-row">
      <div class="inv-kpi-card">
        <div class="inv-kpi-label">TOTAL PRODUCTS</div>
        <div class="inv-kpi-val">${k.total_products}</div>
      </div>
      <div class="inv-kpi-card ${k.low_stock > 0 ? "danger-border" : ""}">
        <div class="inv-kpi-label">LOW STOCK ALERTS</div>
        <div class="inv-kpi-val ${k.low_stock > 0 ? "danger-text" : ""}">${k.low_stock}</div>
      </div>
      <div class="inv-kpi-card">
        <div class="inv-kpi-label">CATEGORIES</div>
        <div class="inv-kpi-val">${k.categories_count}</div>
      </div>
      <div class="inv-kpi-card ${k.expiring_soon > 0 ? "danger-border" : ""}">
        <div class="inv-kpi-label">EXPIRING SOON (${STATE.expiryWarnDays}D)</div>
        <div class="inv-kpi-val ${k.expiring_soon > 0 ? "danger-text" : ""}">${k.expiring_soon}</div>
      </div>
    </div>

    <div id="inv-tab-body"></div>
  `;

  if (STATE.invTab === "catalog") renderInvCatalogTab();
  else if (STATE.invTab === "movements") await renderInvMovementsTab();
  else renderInvMetaTab();
}

function switchInvTab(tab) {
  STATE.invTab = tab;
  renderInventoryScreen(false);
}

function getFilteredProducts() {
  const prods = STATE.invData?.products || [];
  const q = (STATE.invSearch || "").trim().toLowerCase();
  const filtered = prods.filter((p) => {
    if (q && !p.name.toLowerCase().includes(q) && !p.sku.toLowerCase().includes(q) && !p.category_name.toLowerCase().includes(q)) {
      return false;
    }
    if (STATE.invChip === "Low stock" && !p.is_low) return false;
    if (STATE.invChip === "Expiring soon" && !p.is_expiring_soon) return false;
    if (STATE.invChip === "Category" && STATE.invCatId && p.category_id !== Number(STATE.invCatId)) return false;
    return true;
  });

  const col = STATE.invSortCol;
  filtered.sort((a, b) => {
    let va = a[col], vb = b[col];
    if (col === "category") { va = a.category_name; vb = b.category_name; }
    if (col === "stock") { va = a.stock_qty; vb = b.stock_qty; }
    if (col === "cost") { va = a.cost_price; vb = b.cost_price; }
    if (col === "price") { va = a.selling_price; vb = b.selling_price; }
    if (col === "expiry") { va = a.expiry_date; vb = b.expiry_date; }
    if (col === "status") { va = a.is_low ? 1 : 0; vb = b.is_low ? 1 : 0; }
    if (typeof va === "string") return STATE.invSortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
    return STATE.invSortDesc ? vb - va : va - vb;
  });
  return filtered;
}

function renderInvCatalogTab() {
  const body = document.getElementById("inv-tab-body");
  if (!body) return;
  const canEdit = (STATE.user?.permissions || []).includes("inventory_edit");
  const cats = STATE.invData?.categories || [];
  const filtered = getFilteredProducts();
  const selCount = STATE.invSelectedIds.size;

  const catOptions = `<option value="">All Categories</option>` + cats
    .map((c) => `<option value="${c.id}" ${Number(STATE.invCatId) === c.id ? "selected" : ""}>${escapeHtml(c.name)}</option>`)
    .join("");

  const sortArrow = (col) => (STATE.invSortCol === col ? (STATE.invSortDesc ? " ▼" : " ▲") : "");

  const rowsHtml = filtered
    .map((p) => {
      const checked = STATE.invSelectedIds.has(p.id);
      const pct = Math.min(100, Math.round((p.stock_qty / Math.max(1, p.reorder_level * 3)) * 100));
      const barCol = p.is_low ? "var(--danger)" : "var(--lime)";
      return `
        <tr>
          <td style="width:40px;text-align:center">
            <input type="checkbox" ${checked ? "checked" : ""} onchange="toggleInvSelect(${p.id}, this.checked)" />
          </td>
          <td>
            <div class="prod-cell-name">${escapeHtml(p.name)}</div>
            <div class="prod-cell-sku">${escapeHtml(p.sku)}</div>
          </td>
          <td><span class="cat-badge">${escapeHtml(p.category_name)}</span></td>
          <td style="min-width:160px">
            <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:3px">
              <strong>${p.stock_qty}</strong>
              <span style="color:var(--text-muted)">min ${p.reorder_level}</span>
            </div>
            <div class="pill-track" style="height:6px"><div class="pill-fill" style="width:${pct}%;background:${barCol}"></div></div>
          </td>
          <td>${STATE.currency}${p.cost_price.toFixed(2)}</td>
          <td><strong>${STATE.currency}${p.selling_price.toFixed(2)}</strong></td>
          <td>${escapeHtml(p.expiry_date)}</td>
          <td>${escapeHtml(p.unit)}</td>
          <td>
            <span class="status-pill ${p.is_low ? "status-low" : "status-ok"}">${escapeHtml(p.status_text)}</span>
          </td>
          <td>
            ${
              canEdit
                ? `<button type="button" class="row-icon-btn" onclick="openProductModal(${p.id})" title="Edit Product">✎</button>
                   <button type="button" class="row-icon-btn" onclick="openStockMovementModal(${p.id})" title="Adjust Stock">⇅</button>`
                : `<span style="color:var(--text-muted);font-size:0.78rem">View only</span>`
            }
          </td>
        </tr>
      `;
    })
    .join("");

  body.innerHTML = `
    <div class="filter-toolbar">
      <div class="search-box">
        <span>🔍</span>
        <input type="text" placeholder="Search name, SKU or category" value="${escapeHtml(STATE.invSearch)}" oninput="onInvSearch(this.value)" />
      </div>
      <div class="chip-group">
        <button type="button" class="filter-chip ${STATE.invChip === "All" ? "active" : ""}" onclick="setInvChip('All')">All</button>
        <button type="button" class="filter-chip ${STATE.invChip === "Low stock" ? "active" : ""}" onclick="setInvChip('Low stock')">Low stock</button>
        <button type="button" class="filter-chip ${STATE.invChip === "Expiring soon" ? "active" : ""}" onclick="setInvChip('Expiring soon')">Expiring soon</button>
        <select class="filter-chip ${STATE.invChip === "Category" ? "active" : ""}" onchange="setInvCategory(this.value)">
          ${catOptions}
        </select>
      </div>
    </div>

    ${
      selCount > 0
        ? `<div class="filter-toolbar" style="background:var(--surface-alt)">
             <strong>✓ ${selCount} product(s) selected</strong>
             <div class="action-btns-row">
               <button type="button" class="btn-surface" onclick="clearInvSelection()">✕ Clear Selection</button>
               ${canEdit ? `<button type="button" class="btn-danger" onclick="handleBulkDeleteProducts()">🗑 Delete Selected (${selCount})</button>` : ""}
             </div>
           </div>`
        : ""
    }

    <div class="table-card">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th style="width:40px;text-align:center">
                <input type="checkbox" ${filtered.length > 0 && filtered.every((p) => STATE.invSelectedIds.has(p.id)) ? "checked" : ""} onchange="toggleInvSelectAll(this.checked)" />
              </th>
              <th onclick="sortInvBy('name')">PRODUCT${sortArrow("name")}</th>
              <th onclick="sortInvBy('category')">CATEGORY${sortArrow("category")}</th>
              <th onclick="sortInvBy('stock')">STOCK VS. REORDER${sortArrow("stock")}</th>
              <th onclick="sortInvBy('cost')">COST${sortArrow("cost")}</th>
              <th onclick="sortInvBy('price')">PRICE${sortArrow("price")}</th>
              <th onclick="sortInvBy('expiry')">EXPIRY${sortArrow("expiry")}</th>
              <th>UNIT</th>
              <th onclick="sortInvBy('status')">STATUS${sortArrow("status")}</th>
              <th>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml || `<tr><td colspan="10" style="text-align:center;padding:2.5rem;color:var(--text-muted)">No products found matching the current filters.</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:0.6rem;font-size:0.8rem;color:var(--text-muted)">
      <span>Showing ${filtered.length} of ${(STATE.invData?.products || []).length} products</span>
      <span>Select rows to delete or edit in bulk</span>
    </div>
  `;
}

function onInvSearch(val) {
  STATE.invSearch = val;
  renderInvCatalogTab();
}
function setInvChip(chip) {
  STATE.invChip = chip;
  STATE.invCatId = null;
  renderInvCatalogTab();
}
function setInvCategory(catId) {
  if (!catId) {
    setInvChip("All");
  } else {
    STATE.invChip = "Category";
    STATE.invCatId = Number(catId);
    renderInvCatalogTab();
  }
}
function sortInvBy(col) {
  if (STATE.invSortCol === col) STATE.invSortDesc = !STATE.invSortDesc;
  else {
    STATE.invSortCol = col;
    STATE.invSortDesc = false;
  }
  renderInvCatalogTab();
}
function toggleInvSelect(id, checked) {
  if (checked) STATE.invSelectedIds.add(id);
  else STATE.invSelectedIds.delete(id);
  renderInvCatalogTab();
}
function toggleInvSelectAll(checked) {
  const visible = getFilteredProducts();
  visible.forEach((p) => (checked ? STATE.invSelectedIds.add(p.id) : STATE.invSelectedIds.delete(p.id)));
  renderInvCatalogTab();
}
function clearInvSelection() {
  STATE.invSelectedIds.clear();
  renderInvCatalogTab();
}

async function handleBulkDeleteProducts() {
  const ids = Array.from(STATE.invSelectedIds);
  if (!ids.length) return;
  if (!confirm(`Are you sure you want to delete ${ids.length} selected product(s)?`)) return;
  const res = await fetch("/api/inventory/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
  const data = await res.json();
  if (data.ok) {
    STATE.invSelectedIds.clear();
    showToast(data.message);
    await renderInventoryScreen(true);
  } else {
    alert(data.message);
  }
}

async function renderInvMovementsTab() {
  const body = document.getElementById("inv-tab-body");
  if (!body) return;
  const res = await fetch("/api/inventory/movements");
  const data = await res.json();
  STATE.invMovements = data.movements || [];

  const rows = STATE.invMovements
    .map(
      (m) => `
      <tr>
        <td>${m.id}</td>
        <td>${escapeHtml(m.created_at)}</td>
        <td>${escapeHtml(m.sku)}</td>
        <td><strong>${escapeHtml(m.prod_name)}</strong></td>
        <td><span class="status-pill ${m.movement_type === "IN" ? "status-ok" : m.movement_type === "OUT" ? "status-low" : "status-warn"}">${escapeHtml(m.movement_type)}</span></td>
        <td><strong>${m.quantity}</strong></td>
        <td>${escapeHtml(m.reference_note)}</td>
        <td>${escapeHtml(m.username)}</td>
      </tr>
    `
    )
    .join("");

  body.innerHTML = `
    <div class="filter-toolbar">
      <strong>Audit History of Inventory Stock Movements</strong>
      <button type="button" class="btn-surface" onclick="renderInvMovementsTab()">↻ Refresh Log</button>
    </div>
    <div class="table-card">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>SKU</th>
              <th>Product Name</th>
              <th>Movement Type</th>
              <th>Quantity</th>
              <th>Reference / Note</th>
              <th>Logged By</th>
            </tr>
          </thead>
          <tbody>${rows || `<tr><td colspan="8" style="text-align:center;padding:2rem">No stock movements recorded yet.</td></tr>`}</tbody>
        </table>
      </div>
    </div>
  `;
}

function renderInvMetaTab() {
  const body = document.getElementById("inv-tab-body");
  if (!body) return;
  const canEdit = (STATE.user?.permissions || []).includes("inventory_edit");
  const cats = STATE.invData?.categories || [];
  const sups = STATE.invData?.suppliers || [];

  body.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1.2fr;gap:1.1rem">
      <div class="table-card" style="padding:1rem">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.85rem">
          <strong>Categories Management</strong>
          ${canEdit ? `<button type="button" class="btn-lime" onclick="openAddCategoryModal()">+ Add Category</button>` : ""}
        </div>
        <div class="table-scroll" style="max-height:420px">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Category Name</th><th>Description</th></tr></thead>
            <tbody>
              ${cats.map((c) => `<tr><td>${c.id}</td><td><strong>${escapeHtml(c.name)}</strong></td><td>${escapeHtml(c.description || "-")}</td></tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>

      <div class="table-card" style="padding:1rem">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.85rem">
          <strong>Suppliers Directory</strong>
          ${canEdit ? `<button type="button" class="btn-lime" onclick="openAddSupplierModal()">+ Add Supplier</button>` : ""}
        </div>
        <div class="table-scroll" style="max-height:420px">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Supplier Name</th><th>Contact</th><th>Phone</th><th>Email</th></tr></thead>
            <tbody>
              ${sups.map((s) => `<tr><td>${s.id}</td><td><strong>${escapeHtml(s.name)}</strong></td><td>${escapeHtml(s.contact_person || "-")}</td><td>${escapeHtml(s.phone || "-")}</td><td>${escapeHtml(s.email || "-")}</td></tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

function openProductModal(prodId = null) {
  const existing = prodId ? (STATE.invData?.products || []).find((p) => p.id === prodId) : null;
  const cats = STATE.invData?.categories || [];
  const sups = STATE.invData?.suppliers || [];
  const defaultExpiry = new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10);

  showModal(`
    <h3 style="font-size:1.2rem;font-weight:800;margin-bottom:1rem">${existing ? "Edit Pharmacy Product" : "Add New Pharmacy Product"}</h3>
    <div class="form-row"><label>SKU Code *</label><input id="m-sku" value="${escapeHtml(existing ? existing.sku : "SKU-" + Math.floor(10000 + Math.random() * 89999))}" /></div>
    <div class="form-row"><label>Product Name *</label><input id="m-name" value="${escapeHtml(existing ? existing.name : "")}" /></div>
    <div class="form-row">
      <label>Category *</label>
      <select id="m-cat" onchange="${existing ? "" : "autoGenerateModalPrice()"}">
        ${cats.map((c) => `<option value="${c.id}" data-name="${escapeHtml(c.name)}" ${existing && existing.category_id === c.id ? "selected" : ""}>${escapeHtml(c.name)}</option>`).join("")}
      </select>
    </div>
    <div class="form-row">
      <label>Supplier</label>
      <select id="m-sup">
        <option value="">None</option>
        ${sups.map((s) => `<option value="${s.id}" ${existing && existing.supplier_id === s.id ? "selected" : ""}>${escapeHtml(s.name)}</option>`).join("")}
      </select>
    </div>
    <div class="form-row">
      <label>Cost Price ($) *</label>
      <div style="display:flex;gap:0.4rem;width:210px">
        <input id="m-cost" style="flex:1" value="${existing ? existing.cost_price.toFixed(2) : "1.00"}" />
        <button type="button" class="btn-surface" style="padding:0.3rem 0.55rem;font-size:0.75rem" onclick="autoGenerateModalPrice()">↻ Auto</button>
      </div>
    </div>
    <div class="form-row"><label>Selling Price ($) *</label><input id="m-price" value="${existing ? existing.selling_price.toFixed(2) : "2.50"}" /></div>
    <div class="form-row"><label>Stock Quantity *</label><input id="m-stock" type="number" value="${existing ? existing.stock_qty : 50}" /></div>
    <div class="form-row"><label>Reorder Level *</label><input id="m-reorder" type="number" value="${existing ? existing.reorder_level : 15}" /></div>
    <div class="form-row"><label>Expiry (YYYY-MM-DD) *</label><input id="m-expiry" value="${escapeHtml(existing ? existing.expiry_date : defaultExpiry)}" /></div>
    <div class="form-row"><label>Unit (piece/box/strip)</label><input id="m-unit" value="${escapeHtml(existing ? existing.unit : "piece")}" /></div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-lime" onclick="saveProductModal(${existing ? existing.id : "null"})">💾 Save Product</button>
    </div>
  `);
  if (!existing) autoGenerateModalPrice();
}

async function autoGenerateModalPrice() {
  const sel = document.getElementById("m-cat");
  if (!sel) return;
  const opt = sel.options[sel.selectedIndex];
  const res = await fetch("/api/inventory/auto-price", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category_id: sel.value, category_name: opt?.getAttribute("data-name") || "" }),
  });
  const data = await res.json();
  if (data.cost_price) document.getElementById("m-cost").value = data.cost_price;
  if (data.selling_price) document.getElementById("m-price").value = data.selling_price;
}

async function saveProductModal(prodId) {
  const payload = {
    sku: document.getElementById("m-sku").value,
    name: document.getElementById("m-name").value,
    category_id: document.getElementById("m-cat").value,
    supplier_id: document.getElementById("m-sup").value || null,
    cost_price: document.getElementById("m-cost").value,
    selling_price: document.getElementById("m-price").value,
    stock_qty: document.getElementById("m-stock").value,
    reorder_level: document.getElementById("m-reorder").value,
    expiry_date: document.getElementById("m-expiry").value,
    unit: document.getElementById("m-unit").value,
  };
  const url = prodId ? `/api/inventory/product/${prodId}` : "/api/inventory/product";
  const method = prodId ? "PUT" : "POST";
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!data.ok) {
    alert(data.message);
    return;
  }
  closeModal();
  showToast(data.message);
  await renderInventoryScreen(true);
}

function openStockMovementModal(prodId = null) {
  const prods = STATE.invData?.products || [];
  let target = prodId ? prods.find((p) => p.id === prodId) : null;
  if (!target && STATE.invSelectedIds.size > 0) {
    const firstId = Array.from(STATE.invSelectedIds)[0];
    target = prods.find((p) => p.id === firstId);
  }
  if (!target) target = prods[0];
  if (!target) return;

  showModal(`
    <h3 style="font-size:1.2rem;font-weight:800;margin-bottom:0.8rem">Stock In / Out Adjustment</h3>
    <p style="font-size:0.88rem;font-weight:700;margin-bottom:0.2rem">Product: ${escapeHtml(target.name)} (${escapeHtml(target.sku)})</p>
    <p style="font-size:0.84rem;color:var(--secondary);font-weight:700;margin-bottom:1rem">Current Stock: ${target.stock_qty}</p>
    <div class="form-row">
      <label>Movement Type</label>
      <select id="sm-type">
        <option value="IN">IN (Restock / Supplier Delivery)</option>
        <option value="OUT">OUT (Damaged / Expired / Return)</option>
        <option value="ADJUSTMENT">ADJUSTMENT (Audit Correction)</option>
      </select>
    </div>
    <div class="form-row"><label>Quantity Change</label><input id="sm-qty" type="number" value="10" /></div>
    <div class="form-row"><label>Reference / Reason Note</label><input id="sm-note" value="PO-Replenishment" /></div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-lime" onclick="submitStockMovement(${target.id})">Confirm Movement</button>
    </div>
  `);
}

async function submitStockMovement(prodId) {
  const payload = {
    product_id: prodId,
    movement_type: document.getElementById("sm-type").value,
    quantity: document.getElementById("sm-qty").value,
    reference_note: document.getElementById("sm-note").value,
  };
  const res = await fetch("/api/inventory/stock-movement", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!data.ok) {
    alert(data.message);
    return;
  }
  closeModal();
  showToast(data.message);
  await renderInventoryScreen(true);
}

function openAddCategoryModal() {
  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800;margin-bottom:1rem">Add New Category</h3>
    <div class="form-row"><label>Category Name *</label><input id="cat-name" /></div>
    <div class="form-row"><label>Description</label><input id="cat-desc" /></div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-lime" onclick="submitAddCategory()">Save Category</button>
    </div>
  `);
}

async function submitAddCategory() {
  const res = await fetch("/api/inventory/category", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: document.getElementById("cat-name").value,
      description: document.getElementById("cat-desc").value,
    }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  closeModal();
  showToast(data.message);
  await renderInventoryScreen(true);
}

function openAddSupplierModal() {
  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800;margin-bottom:1rem">Add New Supplier</h3>
    <div class="form-row"><label>Supplier Name *</label><input id="sup-name" /></div>
    <div class="form-row"><label>Contact Person</label><input id="sup-contact" /></div>
    <div class="form-row"><label>Phone</label><input id="sup-phone" /></div>
    <div class="form-row"><label>Email</label><input id="sup-email" /></div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-lime" onclick="submitAddSupplier()">Save Supplier</button>
    </div>
  `);
}

async function submitAddSupplier() {
  const res = await fetch("/api/inventory/supplier", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: document.getElementById("sup-name").value,
      contact_person: document.getElementById("sup-contact").value,
      phone: document.getElementById("sup-phone").value,
      email: document.getElementById("sup-email").value,
    }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  closeModal();
  showToast(data.message);
  await renderInventoryScreen(true);
}

/* ───────────────────────────────────────────────────────────────────────────
   7. SCREEN 3: POINT OF SALE (POS) & SALES HISTORY (Matches screens/sales.py)
   ─────────────────────────────────────────────────────────────────────────── */
async function renderSalesScreen(fetchFresh = true) {
  const container = document.getElementById("screen-container");
  if (fetchFresh || !STATE.invData) {
    const res = await fetch("/api/inventory");
    STATE.invData = await res.json();
  }

  container.innerHTML = `
    <div class="screen-top-bar">
      <h1 class="screen-title">Point of Sale (POS)</h1>
      <div class="tab-pills-bar">
        <button type="button" class="tab-pill-btn ${STATE.posTab === "pos" ? "active" : ""}" onclick="switchPosTab('pos')">Point of Sale</button>
        <button type="button" class="tab-pill-btn ${STATE.posTab === "history" ? "active" : ""}" onclick="switchPosTab('history')">Sales History</button>
      </div>
    </div>
    <div id="pos-tab-body"></div>
  `;

  if (STATE.posTab === "pos") renderPosTerminalTab();
  else await renderSalesHistoryTab();
}

function switchPosTab(tab) {
  STATE.posTab = tab;
  renderSalesScreen(false);
}

function renderPosTerminalTab() {
  const body = document.getElementById("pos-tab-body");
  if (!body) return;
  const cats = ["All", ...(STATE.invData?.categories || []).map((c) => c.name)];

  body.innerHTML = `
    <div class="pos-split">
      <!-- Left Catalog Pane -->
      <div class="pos-catalog-pane">
        <div class="filter-toolbar" style="margin-bottom:0.65rem">
          <div class="search-box" style="max-width:100%">
            <span>🔍</span>
            <input id="pos-search-input" type="text" placeholder="Search by name or SKU, or scan a barcode" value="${escapeHtml(STATE.posSearch)}" oninput="onPosSearch(this.value)" />
          </div>
        </div>
        <div class="chip-group" style="margin-bottom:0.75rem">
          ${cats
            .map(
              (c) => `
              <button type="button" class="filter-chip ${STATE.posCatFilter === c ? "active" : ""}" onclick="setPosCat('${escapeHtml(c)}')">
                ${escapeHtml(c.split("&")[0].trim())}
              </button>
            `
            )
            .join("")}
        </div>
        <div class="pos-grid-scroll">
          <div id="pos-products-grid" class="pos-products-grid"></div>
        </div>
      </div>

      <!-- Right Cart & Checkout Pane -->
      <div class="pos-cart-pane">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong style="font-size:1.05rem">Current Sale</strong>
          <button type="button" class="btn-surface" style="padding:0.28rem 0.65rem;font-size:0.78rem" onclick="clearPosCart()">Clear Cart</button>
        </div>

        <div style="margin-top:0.55rem">
          <input id="pos-customer" type="text" placeholder="Walk-in Customer" style="width:100%;padding:0.45rem 0.65rem;border-radius:5px;border:1px solid var(--border);background:var(--surface-alt);color:var(--text-dark);font-size:0.84rem" />
        </div>

        <div id="pos-cart-items" class="pos-cart-items"></div>

        <!-- Discount Presets -->
        <div style="margin-bottom:0.55rem">
          <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.25rem">Discount</div>
          <div class="chip-group">
            ${[0, 5, 10, 20]
              .map(
                (d) => `
                <button type="button" class="filter-chip ${STATE.discountPct === d ? "active" : ""}" style="padding:0.28rem 0.55rem;font-size:0.76rem" onclick="setPosDiscount(${d})">
                  ${d === 0 ? "None" : d === 20 ? "Senior/PWD 20%" : d + "%"}
                </button>
              `
              )
              .join("")}
          </div>
        </div>

        <!-- Payment Method -->
        <div style="margin-bottom:0.55rem">
          <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.25rem">Payment Method</div>
          <div class="chip-group">
            ${["CASH", "CARD", "GCASH"]
              .map(
                (pm) => `
                <button type="button" class="filter-chip ${STATE.payMethod === pm ? "active" : ""}" style="padding:0.28rem 0.65rem;font-size:0.76rem" onclick="setPosPayMethod('${pm}')">
                  ${pm}
                </button>
              `
              )
              .join("")}
          </div>
        </div>

        <div id="pos-totals-box" class="pos-summary-box"></div>

        <div style="display:flex;gap:0.45rem;margin-bottom:0.55rem">
          <input id="pos-amount-paid" type="number" step="0.01" placeholder="Amount Paid ($)" oninput="updatePosTotalsUI()" style="flex:1;padding:0.48rem 0.65rem;border-radius:5px;border:1px solid var(--border);background:var(--surface-alt);color:var(--text-dark)" />
          <button type="button" class="btn-surface" style="padding:0.45rem 0.65rem;font-size:0.78rem" onclick="setExactPosCash()">Exact</button>
        </div>

        <button id="btn-pos-checkout" type="button" class="btn-teal" style="width:100%;padding:0.75rem;font-size:0.95rem" onclick="submitPosCheckout()">
          ✓ Complete Sale
        </button>
      </div>
    </div>
  `;

  renderPosCatalogCards();
  renderPosCartItems();
}

function onPosSearch(val) {
  STATE.posSearch = val;
  renderPosCatalogCards();
}
function setPosCat(cat) {
  STATE.posCatFilter = cat;
  renderPosTerminalTab();
}

function renderPosCatalogCards() {
  const grid = document.getElementById("pos-products-grid");
  if (!grid) return;
  const q = (STATE.posSearch || "").trim().toLowerCase();
  const prods = (STATE.invData?.products || []).filter((p) => {
    if (STATE.posCatFilter !== "All" && p.category_name !== STATE.posCatFilter) return false;
    if (q && !p.name.toLowerCase().includes(q) && !p.sku.toLowerCase().includes(q)) return false;
    return true;
  });

  grid.innerHTML = prods
    .map(
      (p) => `
      <div class="pos-prod-card" onclick="addToPosCart(${p.id})">
        <div>
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.4rem">
            <div class="pos-prod-title">${escapeHtml(p.name)}</div>
            <span class="status-pill ${p.stock_qty <= 0 ? "status-low" : p.is_low ? "status-warn" : "status-ok"}" style="font-size:0.7rem;flex-shrink:0">
              ${p.stock_qty <= 0 ? "Out" : p.stock_qty + " left"}
            </span>
          </div>
          <div class="pos-prod-sub">${escapeHtml(p.sku)} • ${escapeHtml(p.unit)}</div>
        </div>
        <div class="pos-prod-bottom">
          <span class="cat-badge">${escapeHtml(p.category_name.split("&")[0].trim())}</span>
          <span class="pos-prod-price">${STATE.currency}${p.selling_price.toFixed(2)}</span>
        </div>
      </div>
    `
    )
    .join("");
}

function addToPosCart(prodId) {
  const p = (STATE.invData?.products || []).find((x) => x.id === prodId);
  if (!p) return;
  if (p.stock_qty <= 0) {
    showToast(`Out of Stock: '${p.name}' is currently out of stock.`);
    return;
  }
  const existing = STATE.cart.find((c) => c.product_id === prodId);
  if (existing) {
    if (existing.qty + 1 > p.stock_qty) {
      showToast(`Stock limit reached (${p.stock_qty} available).`);
      return;
    }
    existing.qty += 1;
    existing.line_total = Number((existing.qty * existing.price).toFixed(2));
  } else {
    STATE.cart.push({
      product_id: p.id,
      name: p.name,
      sku: p.sku,
      price: p.selling_price,
      cost: p.cost_price,
      max_stock: p.stock_qty,
      qty: 1,
      line_total: p.selling_price,
    });
  }
  renderPosCartItems();
}

function changeCartQty(prodId, delta) {
  const idx = STATE.cart.findIndex((c) => c.product_id === prodId);
  if (idx === -1) return;
  const item = STATE.cart[idx];
  const nextQty = item.qty + delta;
  if (nextQty <= 0) {
    STATE.cart.splice(idx, 1);
  } else if (nextQty <= item.max_stock) {
    item.qty = nextQty;
    item.line_total = Number((item.qty * item.price).toFixed(2));
  } else {
    showToast(`Only ${item.max_stock} units available in stock.`);
  }
  renderPosCartItems();
}

function clearPosCart() {
  STATE.cart = [];
  renderPosCartItems();
}
function setPosDiscount(pct) {
  STATE.discountPct = pct;
  renderPosTerminalTab();
}
function setPosPayMethod(pm) {
  STATE.payMethod = pm;
  renderPosTerminalTab();
}

function getPosTotals() {
  const subtotal = Number(STATE.cart.reduce((s, c) => s + c.line_total, 0).toFixed(2));
  const discountAmt = Number((subtotal * (STATE.discountPct / 100)).toFixed(2));
  const total = Math.max(0, Number((subtotal - discountAmt).toFixed(2)));
  return { subtotal, discountAmt, total };
}

function setExactPosCash() {
  const { total } = getPosTotals();
  const inp = document.getElementById("pos-amount-paid");
  if (inp) inp.value = total.toFixed(2);
  updatePosTotalsUI();
}

function renderPosCartItems() {
  const listEl = document.getElementById("pos-cart-items");
  if (!listEl) return;
  if (!STATE.cart.length) {
    listEl.innerHTML = `<div style="text-align:center;padding:2.2rem 0.5rem;color:var(--text-muted);font-size:0.84rem">Cart is empty. Click products on the left to add items.</div>`;
  } else {
    listEl.innerHTML = STATE.cart
      .map(
        (c) => `
        <div class="cart-item-row">
          <div style="flex:1;min-width:0">
            <div style="font-size:0.84rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(c.name)}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">${STATE.currency}${c.price.toFixed(2)} each</div>
          </div>
          <div class="qty-stepper">
            <button type="button" class="qty-btn" onclick="changeCartQty(${c.product_id}, -1)">−</button>
            <strong style="min-width:22px;text-align:center;font-size:0.84rem">${c.qty}</strong>
            <button type="button" class="qty-btn" onclick="changeCartQty(${c.product_id}, 1)">+</button>
          </div>
          <div style="min-width:58px;text-align:right;font-weight:700;font-size:0.85rem">${STATE.currency}${c.line_total.toFixed(2)}</div>
        </div>
      `
      )
      .join("");
  }
  updatePosTotalsUI();
}

function updatePosTotalsUI() {
  const box = document.getElementById("pos-totals-box");
  if (!box) return;
  const { subtotal, discountAmt, total } = getPosTotals();
  const paidRaw = parseFloat(document.getElementById("pos-amount-paid")?.value || "0");
  const paid = isNaN(paidRaw) ? 0 : paidRaw;
  const change = paid >= total ? paid - total : 0;

  box.innerHTML = `
    <div class="pos-sum-line"><span>Subtotal</span><strong>${STATE.currency}${subtotal.toFixed(2)}</strong></div>
    <div class="pos-sum-line"><span>Discount (${STATE.discountPct}%)</span><strong>-${STATE.currency}${discountAmt.toFixed(2)}</strong></div>
    <div class="pos-sum-total"><span>Total Due</span><span>${STATE.currency}${total.toFixed(2)}</span></div>
    <div class="pos-sum-line" style="margin-top:0.35rem;margin-bottom:0">
      <span>Change Due</span>
      <strong style="color:${paid > 0 && paid < total ? "var(--danger)" : "var(--text-dark)"}">
        ${paid > 0 && paid < total ? `Short by ${STATE.currency}${(total - paid).toFixed(2)}` : `${STATE.currency}${change.toFixed(2)}`}
      </strong>
    </div>
  `;
}

async function submitPosCheckout() {
  if (!STATE.cart.length) {
    showToast("Cart is empty.");
    return;
  }
  const { total } = getPosTotals();
  const paidInp = document.getElementById("pos-amount-paid");
  const paidVal = paidInp && paidInp.value.trim() !== "" ? parseFloat(paidInp.value) : total;

  const res = await fetch("/api/sales/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cart: STATE.cart,
      discount_percent: STATE.discountPct,
      payment_method: STATE.payMethod,
      customer_name: document.getElementById("pos-customer")?.value || "Walk-in Customer",
      amount_paid: paidVal,
    }),
  });
  const data = await res.json();
  if (!data.ok) {
    alert(data.message);
    return;
  }

  STATE.cart = [];
  STATE.discountPct = 0;
  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800">Official Receipt — ${escapeHtml(data.invoice_no)}</h3>
    <pre class="receipt-pre">${escapeHtml(data.receipt_text)}</pre>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem">
      <button type="button" class="btn-surface" onclick="window.print()">🖨 Print</button>
      <button type="button" class="btn-teal" onclick="closeModal()">Done &amp; Close</button>
    </div>
  `);
  await renderSalesScreen(true);
}

async function renderSalesHistoryTab(searchQuery = "") {
  const body = document.getElementById("pos-tab-body");
  if (!body) return;
  const res = await fetch(`/api/sales/history?search=${encodeURIComponent(searchQuery)}`);
  const data = await res.json();
  STATE.salesHistory = data.sales || [];

  const rows = STATE.salesHistory
    .map(
      (s) => `
      <tr>
        <td>${s.id}</td>
        <td><strong>${escapeHtml(s.invoice_no)}</strong></td>
        <td>${escapeHtml(s.date)}</td>
        <td>${escapeHtml(s.cashier)}</td>
        <td>${escapeHtml(s.customer)}</td>
        <td>${STATE.currency}${s.subtotal.toFixed(2)}</td>
        <td>${STATE.currency}${s.discount.toFixed(2)}</td>
        <td><strong>${STATE.currency}${s.total.toFixed(2)}</strong></td>
        <td><span class="cat-badge">${escapeHtml(s.method)}</span></td>
        <td>${STATE.currency}${s.paid.toFixed(2)}</td>
        <td><button type="button" class="row-icon-btn" onclick="openInvoiceItemsModal(${s.id}, '${escapeHtml(s.invoice_no)}')">👁 Items</button></td>
      </tr>
    `
    )
    .join("");

  body.innerHTML = `
    <div class="filter-toolbar">
      <div class="search-box">
        <span>🔍</span>
        <input type="text" placeholder="Search Invoice # or Customer..." value="${escapeHtml(searchQuery)}" oninput="renderSalesHistoryTab(this.value)" />
      </div>
      <button type="button" class="btn-surface" onclick="renderSalesHistoryTab('')">↻ Refresh</button>
    </div>
    <div class="table-card">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Invoice #</th>
              <th>Date / Time</th>
              <th>Cashier</th>
              <th>Customer</th>
              <th>Subtotal</th>
              <th>Discount</th>
              <th>Total</th>
              <th>Payment</th>
              <th>Paid</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>${rows || `<tr><td colspan="11" style="text-align:center;padding:2rem">No sales records found.</td></tr>`}</tbody>
        </table>
      </div>
    </div>
  `;
}

async function openInvoiceItemsModal(saleId, invNo) {
  const res = await fetch(`/api/sales/invoice/${saleId}`);
  const data = await res.json();
  const rows = (data.items || [])
    .map(
      (it) => `
      <tr>
        <td>${escapeHtml(it.sku)}</td>
        <td><strong>${escapeHtml(it.name)}</strong></td>
        <td>${it.quantity}</td>
        <td>${STATE.currency}${it.unit_price.toFixed(2)}</td>
        <td><strong>${STATE.currency}${it.line_total.toFixed(2)}</strong></td>
      </tr>
    `
    )
    .join("");

  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800;margin-bottom:0.85rem">Invoice Breakdown — ${escapeHtml(invNo)}</h3>
    <div class="table-card">
      <table class="data-table">
        <thead><tr><th>SKU</th><th>Product</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div style="display:flex;justify-content:flex-end;margin-top:1rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Close</button>
    </div>
  `);
}

/* ───────────────────────────────────────────────────────────────────────────
   8. SCREEN 4: USER ACCOUNTS & SECURITY AUDIT TRAIL (Matches screens/users.py)
   ─────────────────────────────────────────────────────────────────────────── */
async function renderUsersScreen(fetchFresh = true) {
  const container = document.getElementById("screen-container");
  container.innerHTML = `
    <div class="screen-top-bar">
      <h1 class="screen-title">👥 User Accounts &amp; Security Audit Trail</h1>
      <div class="tab-pills-bar">
        <button type="button" class="tab-pill-btn ${STATE.usersTab === "users" ? "active" : ""}" onclick="switchUsersTab('users')">User Account Management</button>
        <button type="button" class="tab-pill-btn ${STATE.usersTab === "audit" ? "active" : ""}" onclick="switchUsersTab('audit')">Security Audit Logs</button>
      </div>
    </div>
    <div id="users-tab-body"></div>
  `;

  if (STATE.usersTab === "users") await renderUsersDirectoryTab();
  else await renderAuditLogsTab();
}

function switchUsersTab(tab) {
  STATE.usersTab = tab;
  renderUsersScreen(false);
}

async function renderUsersDirectoryTab() {
  const body = document.getElementById("users-tab-body");
  if (!body) return;
  const res = await fetch("/api/users");
  const data = await res.json();
  STATE.usersList = data.users || [];
  if (!STATE.selectedUserId && STATE.usersList.length) {
    STATE.selectedUserId = STATE.usersList[0].id;
  }

  const rows = STATE.usersList
    .map(
      (u) => `
      <tr onclick="selectUserRow(${u.id})" style="cursor:pointer;${STATE.selectedUserId === u.id ? "background:var(--surface-alt)" : ""}">
        <td>${u.id}</td>
        <td><strong>${escapeHtml(u.username)}</strong></td>
        <td>${escapeHtml(u.full_name)}</td>
        <td><span class="cat-badge">${escapeHtml(u.role_display)}</span></td>
        <td>${escapeHtml(u.email)}</td>
        <td>
          <span class="status-pill ${u.status === "Active" ? "status-ok" : "status-low"}">${escapeHtml(u.status)}</span>
        </td>
        <td>${u.failed_attempts}</td>
        <td>${escapeHtml(u.last_login)}</td>
        <td>${escapeHtml(u.created_at)}</td>
      </tr>
    `
    )
    .join("");

  body.innerHTML = `
    <div class="filter-toolbar">
      <div class="action-btns-row">
        <button type="button" class="btn-teal" onclick="openAddUserModal()">+ Add New User</button>
        <button type="button" class="btn-surface" onclick="openEditUserModal()">✎ Edit User</button>
        <button type="button" class="btn-surface" onclick="openResetPasswordModal()">🔑 Reset Password</button>
        <button type="button" class="btn-surface" onclick="handleUnlockSelectedUser()">🔓 Unlock Account</button>
      </div>
      <button type="button" class="btn-danger" onclick="handleToggleSelectedUserActive()">Toggle Active / Inactive</button>
    </div>

    <div class="table-card">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Full Name</th>
              <th>Assigned Role</th>
              <th>Email</th>
              <th>Account Status</th>
              <th>Failed Logins</th>
              <th>Last Login</th>
              <th>Registered</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function selectUserRow(uid) {
  STATE.selectedUserId = uid;
  renderUsersDirectoryTab();
}

function openAddUserModal() {
  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800;margin-bottom:1rem">Create New User</h3>
    <div class="form-row"><label>Username *</label><input id="u-username" /></div>
    <div class="form-row"><label>Full Name *</label><input id="u-fullname" /></div>
    <div class="form-row"><label>Email Address</label><input id="u-email" /></div>
    <div class="form-row"><label>Initial Password *</label><input id="u-password" type="password" /></div>
    <div class="form-row">
      <label>Role Assignment *</label>
      <select id="u-role">
        <option value="admin">Administrator</option>
        <option value="inventory_clerk">Inventory Clerk</option>
        <option value="sales_personnel">Sales Personnel</option>
        <option value="instructor">Academic Instructor</option>
      </select>
    </div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-teal" onclick="submitCreateUser()">Save User</button>
    </div>
  `);
}

async function submitCreateUser() {
  const res = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("u-username").value,
      full_name: document.getElementById("u-fullname").value,
      email: document.getElementById("u-email").value,
      password: document.getElementById("u-password").value,
      role: document.getElementById("u-role").value,
    }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  closeModal();
  showToast(data.message);
  await renderUsersDirectoryTab();
}

function openEditUserModal() {
  const u = STATE.usersList.find((x) => x.id === STATE.selectedUserId);
  if (!u) return alert("Please select a user to edit.");
  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800;margin-bottom:1rem">Edit User: ${escapeHtml(u.username)}</h3>
    <div class="form-row"><label>Full Name *</label><input id="eu-fullname" value="${escapeHtml(u.full_name)}" /></div>
    <div class="form-row"><label>Email Address</label><input id="eu-email" value="${escapeHtml(u.email === "-" ? "" : u.email)}" /></div>
    <div class="form-row">
      <label>Role Assignment *</label>
      <select id="eu-role">
        <option value="admin" ${u.role === "admin" ? "selected" : ""}>Administrator</option>
        <option value="inventory_clerk" ${u.role === "inventory_clerk" ? "selected" : ""}>Inventory Clerk</option>
        <option value="sales_personnel" ${u.role === "sales_personnel" ? "selected" : ""}>Sales Personnel</option>
        <option value="instructor" ${u.role === "instructor" ? "selected" : ""}>Academic Instructor</option>
      </select>
    </div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-teal" onclick="submitEditUser(${u.id})">Save Changes</button>
    </div>
  `);
}

async function submitEditUser(uid) {
  const res = await fetch(`/api/users/${uid}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: document.getElementById("eu-fullname").value,
      email: document.getElementById("eu-email").value,
      role: document.getElementById("eu-role").value,
    }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  closeModal();
  showToast(data.message);
  await renderUsersDirectoryTab();
}

function openResetPasswordModal() {
  const u = STATE.usersList.find((x) => x.id === STATE.selectedUserId);
  if (!u) return alert("Please select a user.");
  showModal(`
    <h3 style="font-size:1.15rem;font-weight:800;margin-bottom:1rem">Reset Password — ${escapeHtml(u.username)}</h3>
    <div class="form-row"><label>New Password</label><input id="rp-p1" type="password" /></div>
    <div class="form-row"><label>Confirm Password</label><input id="rp-p2" type="password" /></div>
    <div style="display:flex;justify-content:flex-end;gap:0.6rem;margin-top:1.2rem">
      <button type="button" class="btn-surface" onclick="closeModal()">Cancel</button>
      <button type="button" class="btn-teal" onclick="submitResetPassword(${u.id})">Change Password</button>
    </div>
  `);
}

async function submitResetPassword(uid) {
  const res = await fetch(`/api/users/${uid}/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      password: document.getElementById("rp-p1").value,
      confirm_password: document.getElementById("rp-p2").value,
    }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  closeModal();
  showToast(data.message);
}

async function handleUnlockSelectedUser() {
  if (!STATE.selectedUserId) return;
  const res = await fetch(`/api/users/${STATE.selectedUserId}/unlock`, { method: "POST" });
  const data = await res.json();
  showToast(data.message);
  await renderUsersDirectoryTab();
}

async function handleToggleSelectedUserActive() {
  if (!STATE.selectedUserId) return;
  const res = await fetch(`/api/users/${STATE.selectedUserId}/toggle-active`, { method: "POST" });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  showToast(data.message);
  await renderUsersDirectoryTab();
}

async function renderAuditLogsTab() {
  const body = document.getElementById("users-tab-body");
  if (!body) return;
  const res = await fetch(`/api/audit-logs?action=${encodeURIComponent(STATE.auditActionFilter)}`);
  const data = await res.json();
  STATE.auditLogs = data.logs || [];

  const actions = [
    "All Actions",
    "LOGIN_SUCCESS",
    "FAILED_LOGIN",
    "ACCOUNT_LOCKED",
    "SALE_COMPLETE",
    "STOCK_MOVEMENT",
    "PRODUCT_CREATE",
    "PRODUCT_UPDATE",
    "USER_CREATE",
  ];

  const rows = STATE.auditLogs
    .map(
      (l) => `
      <tr>
        <td>${l.id}</td>
        <td>${escapeHtml(l.time)}</td>
        <td><strong>${escapeHtml(l.username)}</strong></td>
        <td><span class="cat-badge">${escapeHtml(l.action)}</span></td>
        <td>${escapeHtml(l.details)}</td>
        <td>${escapeHtml(l.ip)}</td>
      </tr>
    `
    )
    .join("");

  body.innerHTML = `
    <div class="filter-toolbar">
      <div style="display:flex;align-items:center;gap:0.6rem">
        <strong>Filter Action:</strong>
        <select class="pop-select" style="width:200px" onchange="setAuditFilter(this.value)">
          ${actions.map((a) => `<option value="${a}" ${STATE.auditActionFilter === a ? "selected" : ""}>${a}</option>`).join("")}
        </select>
      </div>
      <button type="button" class="btn-surface" onclick="renderAuditLogsTab()">↻ Refresh Log</button>
    </div>
    <div class="table-card">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Username / Actor</th>
              <th>Action Performed</th>
              <th>Event Details</th>
              <th>IP Origin</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function setAuditFilter(act) {
  STATE.auditActionFilter = act;
  renderAuditLogsTab();
}

/* ───────────────────────────────────────────────────────────────────────────
   9. SCREEN 5: KNOWLEDGE ANALYSIS STUDIO (Matches screens/analysis.py)
   ─────────────────────────────────────────────────────────────────────────── */
async function renderAnalysisScreen(fetchFresh = true) {
  const container = document.getElementById("screen-container");
  const isInstructor = STATE.user?.role === "instructor";

  if (fetchFresh || !STATE.analysisData || STATE.analysisData.task_name !== STATE.analysisTask) {
    const res = await fetch(`/api/analysis/task/${STATE.analysisTask}`);
    STATE.analysisData = await res.json();
    STATE.lastPredictionResult = null;
  }

  const tasks = [
    { key: "product_demand", label: "1. Product Demand Prediction" },
    { key: "sales_revenue", label: "2. Sales Revenue Prediction" },
    { key: "slow_moving", label: "3. Slow-Moving Product Prediction" },
    { key: "best_selling", label: "4. Best-Selling Product Prediction" },
  ];

  container.innerHTML = `
    <div class="screen-top-bar">
      <h1 class="screen-title">${isInstructor ? "🧠 Knowledge Analysis Studio (Instructor Mode)" : "🧠 Knowledge Analysis &amp; Demand Prediction"}</h1>
      <div style="display:flex;align-items:center;gap:0.65rem">
        <strong>Select Analysis Task:</strong>
        <select class="pop-select" style="width:265px" onchange="onAnalysisTaskChange(this.value)">
          ${tasks.map((tk) => `<option value="${tk.key}" ${STATE.analysisTask === tk.key ? "selected" : ""}>${tk.label}</option>`).join("")}
        </select>
        ${isInstructor ? `<button type="button" class="btn-teal" onclick="handleRetrainModels()">⚡ Retrain Models</button>` : ""}
      </div>
    </div>

    ${
      isInstructor
        ? `<div class="tab-pills-bar" style="margin-bottom:1rem">
             <button type="button" class="tab-pill-btn ${STATE.analysisTab === "prediction" ? "active" : ""}" onclick="switchAnalysisTab('prediction')">Interactive Prediction</button>
             <button type="button" class="tab-pill-btn ${STATE.analysisTab === "metrics" ? "active" : ""}" onclick="switchAnalysisTab('metrics')">Model Evaluation &amp; Plain-Language Metrics</button>
             <button type="button" class="tab-pill-btn ${STATE.analysisTab === "compare" ? "active" : ""}" onclick="switchAnalysisTab('compare')">Linear vs Random Forest Diagnostics</button>
             <button type="button" class="tab-pill-btn ${STATE.analysisTab === "dataset" ? "active" : ""}" onclick="switchAnalysisTab('dataset')">Training Dataset Preview</button>
           </div>`
        : ""
    }

    <div id="analysis-tab-body"></div>
  `;

  if (!isInstructor || STATE.analysisTab === "prediction") renderAnalysisPredictionTab();
  else if (STATE.analysisTab === "metrics") renderAnalysisMetricsTab();
  else if (STATE.analysisTab === "compare") renderAnalysisCompareTab();
  else if (STATE.analysisTab === "dataset") renderAnalysisDatasetTab();
}

function onAnalysisTaskChange(taskKey) {
  STATE.analysisTask = taskKey;
  renderAnalysisScreen(true);
}

function switchAnalysisTab(tab) {
  STATE.analysisTab = tab;
  renderAnalysisScreen(false);
}

function renderAnalysisPredictionTab() {
  const body = document.getElementById("analysis-tab-body");
  if (!body) return;
  const cats = [
    "Analgesics & Antipyretics",
    "Antibiotics & Antivirals",
    "Antihistamines & Allergy",
    "Cardiovascular & Hypertension",
    "Vitamins & Supplements",
    "Gastrointestinal & Digestive",
    "Respiratory & Cough Care",
    "Topical & First Aid",
  ];
  const catOptions = (defIdx = 0) =>
    cats.map((c, i) => `<option value="${escapeHtml(c)}" ${i === defIdx ? "selected" : ""}>${escapeHtml(c)}</option>`).join("");
  const yesNo = (defVal = 1) =>
    `<option value="1" ${defVal === 1 ? "selected" : ""}>Yes (1)</option><option value="0" ${defVal === 0 ? "selected" : ""}>No (0)</option>`;

  let fieldsHtml = "";
  if (STATE.analysisTask === "product_demand") {
    fieldsHtml = `
      <div class="form-row"><label>Category:</label><select id="ml-category">${catOptions(0)}</select></div>
      <div class="form-row"><label>Unit Price ($):</label><input id="ml-unit_price" type="number" step="0.01" value="12.50" /></div>
      <div class="form-row"><label>Cost Price ($):</label><input id="ml-cost_price" type="number" step="0.01" value="5.00" /></div>
      <div class="form-row"><label>Month (1-12):</label><input id="ml-month" type="number" value="11" /></div>
      <div class="form-row"><label>Day of Week (0-6):</label><input id="ml-day_of_week" type="number" value="5" /></div>
      <div class="form-row"><label>Flu Season?:</label><select id="ml-is_flu_season">${yesNo(1)}</select></div>
      <div class="form-row"><label>Rainy Season?:</label><select id="ml-is_rainy_season">${yesNo(0)}</select></div>
      <div class="form-row"><label>Promotional Sale?:</label><select id="ml-is_promotion">${yesNo(1)}</select></div>
      <div class="form-row"><label>Discount %:</label><input id="ml-discount_percent" type="number" value="15" /></div>
      <div class="form-row"><label>Current Stock Qty:</label><input id="ml-stock_level" type="number" value="150" /></div>
    `;
  } else if (STATE.analysisTask === "sales_revenue") {
    fieldsHtml = `
      <div class="form-row"><label>Month (1-12):</label><input id="ml-month" type="number" value="12" /></div>
      <div class="form-row"><label>Day of Week (0-6):</label><input id="ml-day_of_week" type="number" value="6" /></div>
      <div class="form-row"><label>Weekend?:</label><select id="ml-is_weekend">${yesNo(1)}</select></div>
      <div class="form-row"><label>Holiday?:</label><select id="ml-is_holiday">${yesNo(1)}</select></div>
      <div class="form-row"><label>Flu Season?:</label><select id="ml-is_flu_season">${yesNo(1)}</select></div>
      <div class="form-row"><label>Rainy Season?:</label><select id="ml-is_rainy_season">${yesNo(0)}</select></div>
      <div class="form-row"><label>Promo Active?:</label><select id="ml-promo_active">${yesNo(1)}</select></div>
      <div class="form-row"><label>Est. Foot Traffic:</label><input id="ml-foot_traffic" type="number" value="230" /></div>
      <div class="form-row"><label>Prescriptions Filled:</label><input id="ml-prescriptions_filled" type="number" value="75" /></div>
      <div class="form-row"><label>Avg Basket Size ($):</label><input id="ml-avg_basket_size" type="number" step="0.01" value="38.50" /></div>
    `;
  } else if (STATE.analysisTask === "slow_moving") {
    fieldsHtml = `
      <div class="form-row"><label>Category:</label><select id="ml-category">${catOptions(3)}</select></div>
      <div class="form-row"><label>Unit Price ($):</label><input id="ml-unit_price" type="number" step="0.01" value="45.00" /></div>
      <div class="form-row"><label>Current Stock Qty:</label><input id="ml-stock_qty" type="number" value="280" /></div>
      <div class="form-row"><label>Shelf Life (days):</label><input id="ml-shelf_life_days" type="number" value="365" /></div>
      <div class="form-row"><label>Days Since Last Sale:</label><input id="ml-days_since_last_sale" type="number" value="48" /></div>
      <div class="form-row"><label>Monthly Sales Velocity:</label><input id="ml-monthly_sales_velocity" type="number" step="0.1" value="6.5" /></div>
      <div class="form-row"><label>Seasonal Product?:</label><select id="ml-is_seasonal">${yesNo(0)}</select></div>
      <div class="form-row"><label>Discount Applied %:</label><input id="ml-discount_applied" type="number" value="0" /></div>
    `;
  } else {
    fieldsHtml = `
      <div class="form-row"><label>Category:</label><select id="ml-category">${catOptions(6)}</select></div>
      <div class="form-row"><label>Unit Price ($):</label><input id="ml-unit_price" type="number" step="0.01" value="8.50" /></div>
      <div class="form-row"><label>Hist. Monthly Demand:</label><input id="ml-historical_monthly_demand" type="number" value="320" /></div>
      <div class="form-row"><label>Customer Rating (1-5):</label><input id="ml-customer_rating" type="number" step="0.1" value="4.8" /></div>
      <div class="form-row"><label>Target Month (1-12):</label><input id="ml-month" type="number" value="12" /></div>
      <div class="form-row"><label>Flu Season?:</label><select id="ml-is_flu_season">${yesNo(1)}</select></div>
      <div class="form-row"><label>Rainy Season?:</label><select id="ml-is_rainy_season">${yesNo(0)}</select></div>
      <div class="form-row"><label>Promotional Boost?:</label><select id="ml-promo_active">${yesNo(1)}</select></div>
      <div class="form-row"><label>Stock Availability %:</label><input id="ml-stock_availability" type="number" step="0.1" value="98.0" /></div>
    `;
  }

  body.innerHTML = `
    <div class="analysis-split">
      <div class="analysis-card">
        <h3 style="font-size:1.05rem;font-weight:800;margin-bottom:0.9rem">⚙ Prediction Parameters</h3>
        ${fieldsHtml}
        <div class="form-row" style="margin-top:0.85rem">
          <label>Machine Learning Model:</label>
          <select id="ml-model-type">
            <option value="rf">Random Forest (Recommended)</option>
            <option value="linear">Simple Linear Regression</option>
          </select>
        </div>
        <button type="button" class="btn-teal" style="width:100%;padding:0.75rem;margin-top:0.85rem;font-size:0.92rem" onclick="executeAnalysisPrediction()">
          🚀 Calculate Prediction
        </button>
      </div>

      <div class="analysis-card" style="display:flex;flex-direction:column">
        <h3 style="font-size:1.05rem;font-weight:800;margin-bottom:0.9rem">📊 Prediction Results &amp; Output Visualizer</h3>
        <div class="output-banner">
          <div id="ml-out-primary" class="output-primary" style="color:var(--text-muted);font-size:0.95rem">
            Enter parameters on the left and click 'Calculate Prediction'
          </div>
          <div id="ml-out-sub" class="output-sub"></div>
        </div>
        <div style="flex:1;min-height:280px;position:relative">
          <canvas id="ml-pred-canvas" style="width:100%;height:280px;display:block"></canvas>
        </div>
      </div>
    </div>
  `;

  if (STATE.lastPredictionResult) {
    applyPredictionOutput(STATE.lastPredictionResult);
  }
}

async function executeAnalysisPrediction() {
  const params = {};
  document.querySelectorAll("[id^='ml-']").forEach((el) => {
    const key = el.id.replace("ml-", "");
    if (key !== "model-type" && key !== "out-primary" && key !== "out-sub" && key !== "pred-canvas") {
      params[key] = el.value;
    }
  });
  const modelType = document.getElementById("ml-model-type")?.value || "rf";

  const res = await fetch("/api/analysis/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_name: STATE.analysisTask, model_type: modelType, params }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  STATE.lastPredictionResult = data;
  applyPredictionOutput(data);
}

function applyPredictionOutput(data) {
  const pEl = document.getElementById("ml-out-primary");
  const sEl = document.getElementById("ml-out-sub");
  if (pEl) {
    pEl.textContent = data.primary_text;
    pEl.style.fontSize = "1.35rem";
    pEl.style.color = data.is_danger ? "var(--danger)" : "var(--secondary)";
  }
  if (sEl) sEl.textContent = data.sub_text;
  drawPredictionCanvasChart(data.chart);
}

function drawPredictionCanvasChart(chart) {
  const canvas = document.getElementById("ml-pred-canvas");
  if (!canvas || !chart) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 540;
  const h = 280;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const isDark = STATE.prefs.theme === "dark";
  const textCol = isDark ? "#f8fafc" : "#0f172a";
  const mutedCol = isDark ? "#94a3b8" : "#64748b";
  const gridCol = isDark ? "#1e2c44" : "#e2e8f0";

  ctx.font = `bold 13px ${getComputedStyle(document.documentElement).getPropertyValue("--font-family")}`;
  ctx.fillStyle = textCol;
  ctx.textAlign = "center";
  ctx.fillText(chart.title, w / 2, 22);

  if (chart.type === "bar") {
    const padL = 56, padR = 24, padT = 44, padB = 40;
    const plotW = w - padL - padR;
    const plotH = h - padT - padB;
    const maxV = Math.max(10, ...chart.values) * 1.18;

    ctx.strokeStyle = gridCol;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padT + (i / 4) * plotH;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();
    }

    const colMap = {
      accent: "#2563eb",
      teal: "#0d9488",
      lime: "#a3e635",
      muted: "#64748b",
    };

    const bw = Math.min(78, (plotW / chart.values.length) * 0.52);
    chart.values.forEach((v, i) => {
      const cx = padL + ((i + 0.5) / chart.values.length) * plotW;
      const bh = (v / maxV) * plotH;
      const x = cx - bw / 2;
      const y = padT + plotH - bh;

      ctx.fillStyle = colMap[chart.colors?.[i]] || "#0d9488";
      ctx.beginPath();
      ctx.roundRect(x, y, bw, bh, [5, 5, 0, 0]);
      ctx.fill();

      ctx.font = `bold 11px ${getComputedStyle(document.documentElement).getPropertyValue("--font-family")}`;
      ctx.fillStyle = textCol;
      ctx.textAlign = "center";
      const valLbl = chart.currency ? `${STATE.currency}${Math.round(v)}` : String(v);
      ctx.fillText(valLbl, cx, y - 7);

      ctx.font = `11px ${getComputedStyle(document.documentElement).getPropertyValue("--font-family")}`;
      ctx.fillStyle = mutedCol;
      ctx.fillText(chart.labels[i], cx, padT + plotH + 18);
    });
  } else if (chart.type === "threshold_hbar") {
    const padL = 60, padR = 30, padT = 80, padB = 50;
    const plotW = w - padL - padR;
    const maxX = Math.max(60, chart.value + 15);
    const barW = (chart.value / maxX) * plotW;
    const threshX = padL + (chart.threshold / maxX) * plotW;

    ctx.fillStyle = gridCol;
    ctx.beginPath();
    ctx.roundRect(padL, padT, plotW, 38, 8);
    ctx.fill();

    ctx.fillStyle = chart.is_danger ? "#ef4444" : "#10b981";
    ctx.beginPath();
    ctx.roundRect(padL, padT, Math.max(8, barW), 38, 8);
    ctx.fill();

    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 2.5;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(threshX, padT - 18);
    ctx.lineTo(threshX, padT + 56);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.font = `bold 11px ${getComputedStyle(document.documentElement).getPropertyValue("--font-family")}`;
    ctx.fillStyle = "#f59e0b";
    ctx.textAlign = "center";
    ctx.fillText(`Critical Slow-Moving Threshold (${chart.threshold}%)`, threshX, padT - 24);
  }
}

function renderAnalysisMetricsTab() {
  const body = document.getElementById("analysis-tab-body");
  if (!body) return;
  const meta = STATE.analysisData?.metadata || {};
  const rfM = meta.rf_metrics || {};
  const lrM = meta.lr_metrics || {};
  const classEval = meta.classification_eval;

  const cards = Object.keys(rfM)
    .map((k) => {
      const m = rfM[k];
      const lrVal = lrM[k]?.value ?? 0;
      return `
        <div class="metric-card">
          <div class="metric-top">
            <strong style="font-size:1rem">${escapeHtml(m.title)}</strong>
            <span class="metric-badge">Random Forest: ${m.value.toFixed(4)}  |  Linear Regression: ${lrVal.toFixed(4)}</span>
          </div>
          <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.3rem">Concept Definition: ${escapeHtml(m.description)}</p>
          <p style="font-size:0.86rem;font-weight:700;color:var(--secondary)">Practical Interpretation: ${escapeHtml(m.interpretation)}</p>
        </div>
      `;
    })
    .join("");

  let classHtml = "";
  if (classEval) {
    const cKeys = ["Accuracy", "Precision", "Recall", "F1"];
    classHtml =
      `<h3 style="margin:1.25rem 0 0.75rem;font-size:1.15rem">Classification Metrics (Slow-Moving Risk Detection)</h3>` +
      cKeys
        .filter((k) => classEval[k])
        .map((k) => {
          const c = classEval[k];
          return `
            <div class="metric-card">
              <div class="metric-top">
                <strong style="font-size:1rem">${escapeHtml(c.title)}</strong>
                <span class="metric-badge">Score: ${c.value.toFixed(4)}</span>
              </div>
              <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.3rem">Concept: ${escapeHtml(c.description)}</p>
              <p style="font-size:0.86rem;font-weight:700;color:var(--secondary)">Interpretation: ${escapeHtml(c.interpretation)}</p>
            </div>
          `;
        })
        .join("");
  }

  body.innerHTML = `
    <h3 style="margin-bottom:0.9rem;font-size:1.15rem">Detailed Model Evaluation Metrics &amp; Plain-Language Interpretations</h3>
    ${cards}
    ${classHtml}
  `;
}

function renderAnalysisCompareTab() {
  const body = document.getElementById("analysis-tab-body");
  if (!body) return;
  const meta = STATE.analysisData?.metadata || {};
  const comp = meta.comparison || {};
  const rfM = meta.rf_metrics || {};
  const lrM = meta.lr_metrics || {};

  const rows = [
    ["R² (Variance Explained)", "R2", true],
    ["Root Mean Squared Error (RMSE)", "RMSE", false],
    ["Mean Absolute Error (MAE)", "MAE", false],
    ["Mean Squared Error (MSE)", "MSE", false],
    ["5-Fold CV Score (R²)", "CV_Score", true],
  ]
    .map(([title, key, higherBetter]) => {
      const vLr = lrM[key]?.value ?? 0;
      const vRf = rfM[key]?.value ?? 0;
      const diff = vRf - vLr;
      const adv = higherBetter
        ? diff > 0
          ? `RF (+${diff.toFixed(4)})`
          : `LR (+${(-diff).toFixed(4)})`
        : diff < 0
        ? `RF (${diff.toFixed(2)} lower)`
        : `LR (${(-diff).toFixed(2)} lower)`;
      return `
        <tr>
          <td><strong>${escapeHtml(title)}</strong></td>
          <td>${vLr.toFixed(4)}</td>
          <td><strong>${vRf.toFixed(4)}</strong></td>
          <td><span class="status-pill status-ok">${escapeHtml(adv)}</span></td>
        </tr>
      `;
    })
    .join("");

  const topFeats = (meta.top_features || [])
    .map((f) => {
      const pct = Math.min(100, Math.round(f.importance * 100));
      return `
        <div class="bar-row">
          <div class="bar-label" style="width:190px">${escapeHtml(f.feature)}</div>
          <div class="pill-track"><div class="pill-fill" style="width:${pct}%;background:var(--secondary)"></div></div>
          <div class="bar-qty" style="width:48px">${f.importance.toFixed(2)}</div>
        </div>
      `;
    })
    .join("");

  body.innerHTML = `
    <div class="metric-card" style="margin-bottom:1rem">
      <h3 style="color:var(--secondary);font-size:1.18rem;margin-bottom:0.4rem">🏆 Winning Algorithm: ${escapeHtml(comp.winner || "Random Forest Regression")}</h3>
      <p style="font-size:0.88rem">${escapeHtml(comp.reason || "")}</p>
    </div>

    <div class="table-card" style="margin-bottom:1rem;padding:1rem">
      <h4 style="margin-bottom:0.75rem">Side-by-Side Algorithmic Performance Comparison</h4>
      <table class="data-table">
        <thead>
          <tr>
            <th>Evaluation Metric</th>
            <th>Simple Linear Regression</th>
            <th>Random Forest Regression (Tuned)</th>
            <th>Variance / Advantage</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
      <div class="analysis-card">
        <h4 style="margin-bottom:0.75rem">Actual vs Predicted Values (Holdout Set)</h4>
        <canvas id="cmp-scatter-canvas" style="width:100%;height:240px;display:block"></canvas>
      </div>
      <div class="analysis-card">
        <h4 style="margin-bottom:0.75rem">Top Feature Importances (Random Forest)</h4>
        <div class="bar-list">${topFeats}</div>
      </div>
    </div>
  `;

  drawScatterDiagnosticChart(meta.sample_scatter || {});
}

function drawScatterDiagnosticChart(scatter) {
  const canvas = document.getElementById("cmp-scatter-canvas");
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 460;
  const h = 240;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const acts = scatter.actual || [];
  const preds = scatter.predicted || [];
  if (!acts.length) return;

  const pad = 32;
  const plotW = w - pad * 2;
  const plotH = h - pad * 2;
  const minV = Math.min(...acts, ...preds);
  const maxV = Math.max(...acts, ...preds) || 1;

  // y = x reference line
  ctx.strokeStyle = "#ef4444";
  ctx.lineWidth = 1.6;
  ctx.setLineDash([5, 4]);
  ctx.beginPath();
  ctx.moveTo(pad, h - pad);
  ctx.lineTo(w - pad, pad);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "rgba(37, 99, 235, 0.72)";
  for (let i = 0; i < acts.length; i++) {
    const x = pad + ((acts[i] - minV) / (maxV - minV || 1)) * plotW;
    const y = h - pad - ((preds[i] - minV) / (maxV - minV || 1)) * plotH;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  }
}

function renderAnalysisDatasetTab() {
  const body = document.getElementById("analysis-tab-body");
  if (!body) return;
  const ds = STATE.analysisData?.dataset || { filename: "", total_rows: 0, total_cols: 0, columns: [], rows: [] };

  const headers = ds.columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("");
  const rows = ds.rows
    .map((r) => `<tr>${ds.columns.map((c) => `<td>${escapeHtml(String(r[c] ?? ""))}</td>`).join("")}</tr>`)
    .join("");

  body.innerHTML = `
    <div class="filter-toolbar">
      <strong>Dataset File: ${escapeHtml(ds.filename)}  |  Total Records: ${ds.total_rows.toLocaleString()} rows, ${ds.total_cols} columns</strong>
    </div>
    <div class="table-card">
      <div class="table-scroll">
        <table class="data-table">
          <thead><tr>${headers}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

async function handleRetrainModels() {
  if (!confirm(`Trigger full retraining and hyperparameter tuning for task '${STATE.analysisTask}'?`)) return;
  showToast("Retraining models and calculating 5-Fold Cross-Validation…");
  const res = await fetch("/api/analysis/retrain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_name: STATE.analysisTask }),
  });
  const data = await res.json();
  if (!data.ok) return alert(data.message);
  showToast(data.message);
  await renderAnalysisScreen(true);
}

/* ───────────────────────────────────────────────────────────────────────────
   10. SCREEN 6: MY PROFILE (Matches ProfileScreen in main.py)
   ─────────────────────────────────────────────────────────────────────────── */
function renderProfileScreen() {
  const container = document.getElementById("screen-container");
  const u = STATE.user || {
    full_name: "System Administrator",
    username: "admin",
    email: "admin@restinpills.local",
    role_display: "Administrator",
    last_login: "2026-11-23 · 18:00",
  };

  container.innerHTML = `
    <h1 class="screen-title" style="margin-bottom:1.15rem">My Profile</h1>

    <div class="profile-hero">
      <div class="profile-avatar-big">${escapeHtml(getInitials(u.full_name))}</div>
      <div>
        <div style="font-size:1.35rem;font-weight:800;color:#ffffff">${escapeHtml(u.full_name)}</div>
        <div style="font-size:0.88rem;color:#94a3b8;margin:0.15rem 0 0.65rem">${escapeHtml(u.email)}</div>
        <div style="display:flex;gap:0.5rem">
          <span style="background:#b4e633;color:#0c1b2e;font-size:0.76rem;font-weight:800;padding:0.22rem 0.75rem;border-radius:999px">
            ${escapeHtml(u.role_display)}
          </span>
          <span style="background:#132338;color:#e2e8f0;border:1px solid #2a3f5a;font-size:0.76rem;font-weight:700;padding:0.22rem 0.75rem;border-radius:999px">
            Session active
          </span>
        </div>
      </div>
    </div>

    <div class="profile-cards-grid">
      <div class="profile-detail-card">
        <h3 style="font-size:1.05rem;font-weight:800;margin-bottom:0.9rem">Account details</h3>
        <div class="profile-fields-grid">
          <div class="profile-field-cell">
            <div class="profile-field-label">FULL NAME</div>
            <div class="profile-field-val">${escapeHtml(u.full_name)}</div>
          </div>
          <div class="profile-field-cell">
            <div class="profile-field-label">USERNAME</div>
            <div class="profile-field-val">${escapeHtml(u.username)}</div>
          </div>
          <div class="profile-field-cell">
            <div class="profile-field-label">EMAIL ADDRESS</div>
            <div class="profile-field-val">${escapeHtml(u.email)}</div>
          </div>
          <div class="profile-field-cell">
            <div class="profile-field-label">ASSIGNED ROLE</div>
            <div class="profile-field-val">${escapeHtml(u.role_display)}</div>
          </div>
        </div>
      </div>

      <div class="profile-detail-card">
        <h3 style="font-size:1.05rem;font-weight:800;margin-bottom:0.9rem">Current session</h3>
        <div style="display:flex;flex-direction:column;gap:0.95rem">
          <div class="profile-field-cell">
            <div class="profile-field-label">STARTED</div>
            <div class="profile-field-val">${escapeHtml(u.last_login)}</div>
          </div>
          <div class="profile-field-cell">
            <div class="profile-field-label">STATUS</div>
            <div class="profile-field-val">Active</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

/* ───────────────────────────────────────────────────────────────────────────
   11. MODAL & TOAST HELPERS + INITIALIZATION
   ─────────────────────────────────────────────────────────────────────────── */
function showModal(html) {
  const overlay = document.getElementById("modal-overlay");
  const card = document.getElementById("modal-card");
  if (!overlay || !card) return;
  card.innerHTML = html;
  overlay.classList.remove("hidden");
}

function closeModal() {
  const overlay = document.getElementById("modal-overlay");
  if (overlay) overlay.classList.add("hidden");
}

function handleOverlayClick(e) {
  if (e.target.id === "modal-overlay") closeModal();
}

function showToast(msg) {
  const wrap = document.getElementById("toast-container");
  if (!wrap) return;
  const el = document.createElement("div");
  el.className = "toast-item";
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 3400);
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function initApp() {
  try {
    const res = await fetch("/api/bootstrap");
    const data = await res.json();
    STATE.currency = data.currency || "$";
    STATE.dbName = data.db_name || "pharmacy";
    STATE.expiryWarnDays = data.expiry_warn_days || 90;
    if (data.prefs) {
      STATE.prefs = { ...STATE.prefs, ...data.prefs };
    }
    applyPrefsToDOM();
    if (data.user) {
      STATE.user = data.user;
      enterAppShell();
    } else {
      startLoginAnimation();
    }
  } catch (e) {
    applyPrefsToDOM();
    startLoginAnimation();
  }
}

window.addEventListener("DOMContentLoaded", initApp);
window.addEventListener("resize", () => {
  if (STATE.user && STATE.activeScreen === "dashboard" && STATE.dashboardData) {
    drawDashboardTrendChart(STATE.dashboardData.trend_14d || []);
  }
});
