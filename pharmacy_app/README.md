# ⚕ PharmaCare — Pharmacy Store Business Management System with Knowledge Analysis

> **Group School Project** | Python + Tkinter + MySQL + Scikit-Learn  
> Full-stack desktop application with role-based access control, POS sales, inventory management, and ML-powered demand prediction.

---

## 📁 Project Structure

```
pharmacy_app/
├── main.py                  # Application entry point & fullscreen window manager
├── config.py                # DB settings, roles, colors, fonts — edit here first
├── db.py                    # DB connection, parameterized queries, auto-setup & seeding
├── auth.py                  # bcrypt authentication, session, lockout, audit logging
├── requirements.txt         # Python package dependencies
├── database/
│   ├── schema.sql           # All CREATE TABLE statements with FK constraints
│   └── setup_db.py          # Standalone DB setup script (run once)
├── screens/
│   ├── login.py             # Full-screen login with role-based redirect
│   ├── dashboard.py         # KPI cards + 4 Matplotlib charts (role-filtered)
│   ├── inventory.py         # Product CRUD, stock in/out, expiry alerts, suppliers/categories
│   ├── sales.py             # POS terminal, cart, receipt dialog, sales history
│   ├── users.py             # User CRUD, password reset, unlock, audit log viewer
│   └── analysis.py          # Knowledge Analysis (Admin: predict only; Instructor: full studio)
├── ml/
│   ├── data_generator.py    # Synthetic dataset generation (1,400–1,500 rows, seed=42)
│   ├── train.py             # Full training pipeline: preprocessing, CV, GridSearchCV, joblib save
│   ├── predict.py           # ModelPredictor: loads saved models, validates inputs, confidence intervals
│   ├── evaluate.py          # Metrics (MAE, MSE, RMSE, R², CV, Accuracy, Precision, Recall, F1)
│   └── models/              # Pre-trained .joblib files (auto-created on first run)
├── datasets/                # CSV datasets (auto-created by data_generator.py, seed=42)
│   ├── product_demand.csv   # 1,500 rows — Task 1
│   ├── sales_revenue.csv    # 1,500 rows — Task 2
│   ├── slow_moving.csv      # 1,400 rows — Task 3
│   └── best_selling.csv     # 1,400 rows — Task 4
└── README.md
```

---

## ⚙️ Prerequisites & WAMP Setup

### 1. Install WAMP Server
- Download from [wampserver.com](https://www.wampserver.com/en/)
- Install and **start WAMP** (all services green in the taskbar icon)
- Default MySQL settings:
  - **Host:** `localhost`
  - **Port:** `3306`
  - **User:** `root`
  - **Password:** *(empty)*

### 2. Install Python 3.10+
- Download from [python.org](https://www.python.org/downloads/)
- Ensure Python is on your system PATH

### 3. Install Python Dependencies
```powershell
cd "pharmacy_app"
pip install -r requirements.txt
```
> **Or using pip directly:**
```powershell
pip install mysql-connector-python bcrypt pandas numpy scikit-learn joblib matplotlib
```

---

## 🗄️ Database Setup

### Option A — Auto-Setup Script (Recommended)
With WAMP running, execute:
```powershell
python database/setup_db.py
```
This will automatically:
1. Create database `pharmacy_db`
2. Run all `schema.sql` table definitions
3. Seed 4 user accounts with bcrypt-hashed passwords
4. Seed 8 product categories, 6 suppliers, 57 realistic pharmacy products
5. Generate 67 sample sales transactions across the past 14 days (for dashboard charts)

### Option B — phpMyAdmin Manual Import
1. Open **phpMyAdmin** at `http://localhost/phpmyadmin`
2. Click **New** → create database `pharmacy_db` with charset `utf8mb4_unicode_ci`
3. Select `pharmacy_db` → **Import** → choose `database/schema.sql` → **Go**
4. Then run: `python database/setup_db.py` (for seed data only)

---

## 🚀 Running the Application

```powershell
cd "c:\Users\mabis\OneDrive\Documents\Projects\Pharmacy Store Business\pharmacy_app"
python main.py
```

> The application opens in **full-screen mode** automatically.  
> Press `Esc` for a safeguard dialog to toggle windowed mode.

---

## 🔐 Default Login Credentials

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Administrator** | `admin` | `admin123` | Dashboard + Users + Inventory (view) + Sales History + Knowledge Analysis (Predict only) |
| **Academic Instructor** | `instructor` | `instructor123` | **Full access** — all modules + ML Studio (metrics, retrain, dataset preview) |
| **Inventory Clerk** | `inventory_clerk` | `clerk123` | Inventory Management + Stock In/Out + Suppliers + Categories |
| **Sales Personnel** | `sales_personnel` | `sales123` | POS Terminal + Sales History |

> **Quick-Login shortcut:** The login screen shows clickable usernames — click any to auto-fill the credentials.

---

## 🧠 Knowledge Analysis & Machine Learning

### Tasks Implemented

| # | Task | Target Variable | Models |
|---|------|----------------|--------|
| 1 | **Product Demand Prediction** | `quantity_demanded` | Linear Regression + Random Forest |
| 2 | **Sales Revenue Prediction** | `total_daily_revenue` | Linear Regression + Random Forest |
| 3 | **Slow-Moving Product Detection** | `turnover_ratio` + `is_slow_moving` | Linear Regression + Random Forest + Classification Metrics |
| 4 | **Best-Selling Product Ranking** | `projected_monthly_units` | Linear Regression + Random Forest |

### Datasets
Synthetic datasets generated with a fixed seed (`RANDOM_SEED = 42`) for full reproducibility. Features include:
- **Seasonality**: Flu season (Nov–Feb), Rainy season (Jun–Sep)
- **Promotions**: Discount %, active campaign flags
- **Calendar**: Month, day-of-week, weekends, holidays
- **Product attributes**: Price, cost, stock level, category, brand tier, customer rating
- **Real MySQL data augmentation**: When DB is available, real sales data is appended automatically

### ML Model Improvements Applied
1. **Outlier Handling** — IQR clipping (1st–99th percentile) on all numeric features
2. **Missing Value Imputation** — Median for numerics, Most-Frequent for categoricals (`SimpleImputer`)
3. **Categorical Encoding** — `OneHotEncoder` with `handle_unknown='ignore'`
4. **Feature Scaling** — `StandardScaler` on all numeric inputs (within `Pipeline`)
5. **Feature Engineering** — Interaction terms (e.g., `flu_resp_interaction`, `traffic_basket_interaction`, `value_demand_score`)
6. **80/20 Train/Test Split** — Stratified evaluation on holdout set
7. **5-Fold Cross-Validation** — `KFold(n_splits=5)` — R² scores averaged for stability
8. **Hyperparameter Tuning** — `GridSearchCV` for Random Forest (`n_estimators`, `max_depth`, `min_samples_split`)
9. **Feature Importance** — Top-8 features ranked by `feature_importances_` from Random Forest
10. **Prediction Confidence Intervals** — Lower/upper bounds computed using ±RMSE

### Retraining Models
Via the **Instructor** Knowledge Analysis Studio:
1. Select a task from the dropdown
2. Click **⚡ Retrain Models**
3. A dialog confirms — models retrain with fresh GridSearchCV and saved to `ml/models/`

Or via command line:
```powershell
python ml/train.py
```

---

## 📊 Evaluation Metrics — Plain-Language Reference

| Metric | Full Name | What It Means |
|--------|-----------|---------------|
| **MAE** | Mean Absolute Error | Average prediction error in the same units as the target. Lower = better. |
| **MSE** | Mean Squared Error | Squared average error — penalizes large mistakes more heavily. Lower = better. |
| **RMSE** | Root Mean Squared Error | Square root of MSE, back in original units. Most interpretable error metric. Lower = better. |
| **R²** | Coefficient of Determination | Fraction of variance the model explains. 1.0 = perfect, 0.0 = no better than mean. Higher = better. |
| **CV Score** | 5-Fold Cross-Validation R² | Average R² across 5 holdout folds — proves the model generalizes, not just memorizes. |
| **Accuracy** | Classification Accuracy | % of inventory items correctly classified as slow-moving or normal. |
| **Precision** | Precision Score | Of items flagged as slow-moving, how many actually are? Avoids false alarms. |
| **Recall** | Recall / Sensitivity | Of all genuinely slow-moving items, how many did the model catch? Avoids missed risk. |
| **F1-Score** | Harmonic Mean of Precision & Recall | Balanced trade-off when both false alarms and missed detections matter. |
| **Confusion Matrix** | TP/FP/TN/FN grid | Visual breakdown of correct vs incorrect classifications (shown in Instructor view). |

---

## 🔒 Security Features

| Feature | Implementation |
|---------|---------------|
| Password Hashing | `bcrypt` with 12 rounds (salt auto-generated per user) |
| SQL Injection Protection | All queries use parameterized `%s` placeholders — zero string interpolation |
| Login Lockout | 5 failed attempts → 15-minute lockout (configurable in `config.py`) |
| Role-Based Access Control | Enforced at both UI (sidebar items) and server-side (screen constructor check) |
| Audit Trail | All key actions logged to `audit_log` table with timestamp, user, and details |
| Confirmation Dialogs | All destructive actions (delete, deactivate) require `messagebox.askyesno()` confirmation |
| Input Validation | All form fields validated before DB writes (type checks, range checks, date format) |
| Session Management | `SessionManager` singleton — cleared on logout/app exit |

---

## 📐 Configuration — `config.py`

Edit `config.py` to change database settings without touching any other file:

```python
DB_HOST = "localhost"    # MySQL host
DB_USER = "root"         # MySQL username  
DB_PASSWORD = ""         # MySQL password (empty for WAMP default)
DB_NAME = "pharmacy_db"  # Database name
DB_PORT = 3306           # MySQL port

LOW_STOCK_THRESHOLD = 15     # Alert if stock <= this
EXPIRY_WARN_DAYS = 90        # Alert if expiry within this many days
MAX_LOGIN_ATTEMPTS = 5       # Lockout trigger
LOCKOUT_MINUTES = 15         # Lockout duration
```

You can also set these via environment variables:
```powershell
$env:PHARMACY_DB_PASSWORD = "mysecretpass"
python main.py
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Can't connect to MySQL" | Ensure WAMP is running (green icon) and MySQL is started |
| "Database offline" message on dashboard | Start WAMP, then click ↻ Refresh |
| `bcrypt` import error | Run: `pip install bcrypt` |
| `mysql.connector` error | Run: `pip install mysql-connector-python` |
| Matplotlib cache warning | Normal on Windows restricted environments — app works fine |
| Models not found | Run `python ml/train.py` once to generate all model files |
| Account locked | Login as admin → User Management → select user → 🔓 Unlock Account |

---

## 📋 Module Summary

### Login Screen
- Full-screen centered card with animated quick-login buttons for each test account
- Input validation, attempt counter display, role-based redirect after success

### Dashboard
- **Admin/Instructor**: 6 KPI cards + 4 charts (sales trend, top products, category pie, stock health)
- **Inventory Clerk**: Inventory-focused cards + stock health + category chart
- **Sales Personnel**: Sales-focused cards + 14-day trend + top products chart

### Inventory Management *(Inventory Clerk & Instructor)*
- Full product CRUD with SKU, category, supplier, cost/price, stock, reorder level, expiry
- Highlighted row tags: Low Stock (red), Near Expiry (amber), Expired (crimson background)
- Stock In / Out / Adjustment dialog with reference notes and audit trail
- Suppliers and Categories management tabs

### Point of Sale (POS) *(Sales Personnel & Instructor)*
- Real-time product search, double-click or qty spinner to add to cart
- Discount %, payment method, auto-change calculation
- One-click checkout creates invoice, deducts stock, logs stock OUT movement
- Official receipt dialog (printable format)
- Sales & Invoice History with line-item drill-down

### User Management *(Admin & Instructor)*
- Add/Edit user accounts with role assignment
- Reset password (bcrypt rehash), unlock locked accounts, toggle active/inactive
- Security Audit Log viewer with action-type filter (300 most recent records)

### Knowledge Analysis Studio
- **Admin view**: Task selector + input form + result output + result visualization chart
- **Instructor view**: All admin features + Model Metrics tab (all metrics with plain-language descriptions) + Diagnostics tab (actual vs predicted scatter, feature importance bar chart, side-by-side model comparison table) + Dataset Preview tab (scrollable table, row count, all 1,400–1,500 records)

---

*Generated for: Pharmacy Store Business Management Group School Project*  
*Stack: Python 3.10+ · Tkinter/ttk · MySQL 8.x · scikit-learn 1.9 · Matplotlib · pandas · bcrypt · joblib*

