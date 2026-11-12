import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import config
import db
import auth
from ml.predict import ModelPredictor
from ml import train

class AnalysisScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=config.COLORS["background"])
        self.parent = parent
        self.controller = controller
        self.user = auth.SessionManager.get_user() or {}
        self.role = self.user.get("role", config.ROLE_ADMIN)
        self.is_instructor = (self.role == config.ROLE_INSTRUCTOR)

        self.current_task = "product_demand"
        self.metadata = {}
        self._mpl_charts = []
        self.load_current_metadata()

        self.setup_ui()

    def load_current_metadata(self):
        try:
            meta_path = config.MODELS_DIR / f"{self.current_task}_meta.joblib"
            if meta_path.exists():
                self.metadata = joblib.load(meta_path)
            else:
                self.metadata = train.train_and_evaluate_task(self.current_task)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            self.metadata = {}

    def setup_ui(self):
        # Header Bar
        header = tk.Frame(self, bg=config.COLORS["surface"], padx=30, pady=16, highlightbackground=config.COLORS["border"], highlightthickness=1)
        header.pack(fill="x", side="top")

        title_text = "🧠 Knowledge Analysis Studio (Instructor Mode)" if self.is_instructor else "🧠 Knowledge Analysis & Demand Prediction"
        lbl_title = tk.Label(header, text=title_text, font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"])
        lbl_title.pack(side="left")

        # Task Selector Dropdown
        task_f = tk.Frame(header, bg=config.COLORS["surface"])
        task_f.pack(side="right")

        tk.Label(task_f, text="Select Analysis Task:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(side="left", padx=(0, 8))
        self.task_options = [
            ("product_demand", "1. Product Demand Prediction"),
            ("sales_revenue", "2. Sales Revenue Prediction"),
            ("slow_moving", "3. Slow-Moving Product Prediction"),
            ("best_selling", "4. Best-Selling Product Prediction")
        ]
        self.combo_task = ttk.Combobox(task_f, values=[desc for _, desc in self.task_options], state="readonly", width=34)
        self.combo_task.current(0)
        self.combo_task.pack(side="left", padx=(0, 10))
        self.combo_task.bind("<<ComboboxSelected>>", self.on_task_changed)

        if self.is_instructor:
            btn_retrain = tk.Button(task_f, text="⚡ Retrain Models", font=config.FONTS["small"], bg=config.COLORS["secondary"], fg="white", relief="flat", cursor="hand2", padx=10, pady=4, command=self.handle_retrain)
            btn_retrain.pack(side="left")

        # Main Layout: If Instructor, Notebook with Prediction Tab + Instructor Tabs. If Admin, single Prediction View.
        if self.is_instructor:
            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill="both", expand=True, padx=25, pady=15)

            # Tab 1: Prediction Playground
            self.tab_prediction = tk.Frame(self.notebook, bg=config.COLORS["background"])
            self.notebook.add(self.tab_prediction, text="  Interactive Prediction  ")
            self.build_prediction_view(self.tab_prediction)

            # Tab 2: Evaluation Metrics & Explanations
            self.tab_metrics = tk.Frame(self.notebook, bg=config.COLORS["background"])
            self.notebook.add(self.tab_metrics, text="  Model Evaluation & Plain-Language Metrics  ")
            self.build_metrics_view(self.tab_metrics)

            # Tab 3: Model Comparison & Diagnostics
            self.tab_compare = tk.Frame(self.notebook, bg=config.COLORS["background"])
            self.notebook.add(self.tab_compare, text="  Linear vs Random Forest Diagnostics  ")
            self.build_comparison_view(self.tab_compare)

            # Tab 4: Dataset Preview (1000+ rows)
            self.tab_dataset = tk.Frame(self.notebook, bg=config.COLORS["background"])
            self.notebook.add(self.tab_dataset, text="  Training Dataset Preview  ")
            self.build_dataset_view(self.tab_dataset)

        else: # Admin Mode (Inputs + Outputs + Result Chart only)
            admin_container = tk.Frame(self, bg=config.COLORS["background"], padx=25, pady=15)
            admin_container.pack(fill="both", expand=True)
            self.build_prediction_view(admin_container)

    def on_task_changed(self, event=None):
        idx = self.combo_task.current()
        self.current_task = self.task_options[idx][0]
        self.load_current_metadata()
        
        # Clear and rebuild UI
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()

    def build_prediction_view(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal", bg=config.COLORS["background"], sashwidth=6)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT: Input Form
        left_card = tk.Frame(paned, bg=config.COLORS["surface"], padx=20, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        paned.add(left_card, width=460)

        tk.Label(left_card, text="⚙ Prediction Parameters", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 10))

        # Form fields container with scroll
        form_scroll = tk.Frame(left_card, bg=config.COLORS["surface"])
        form_scroll.pack(fill="both", expand=True)

        self.input_entries = {}
        self.render_task_form_inputs(form_scroll)

        # Algorithm Choice
        row_algo = tk.Frame(left_card, bg=config.COLORS["surface"], pady=8)
        row_algo.pack(fill="x")
        tk.Label(row_algo, text="Machine Learning Model:", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left")
        self.combo_algo = ttk.Combobox(row_algo, values=["Random Forest (Recommended)", "Simple Linear Regression"], state="readonly", width=25)
        self.combo_algo.current(0)
        self.combo_algo.pack(side="right")

        btn_run = tk.Button(
            left_card,
            text="🚀 Calculate Prediction",
            font=config.FONTS["body_bold"],
            bg=config.COLORS["secondary"],
            fg="white",
            relief="flat",
            cursor="hand2",
            pady=10,
            command=self.execute_prediction
        )
        btn_run.pack(fill="x", pady=(10, 0))

        # RIGHT: Output Results Card & Result Chart
        right_card = tk.Frame(paned, bg=config.COLORS["surface"], padx=20, pady=20, highlightbackground=config.COLORS["border"], highlightthickness=1)
        paned.add(right_card, width=620)

        tk.Label(right_card, text="📊 Prediction Results & Output Visualizer", font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 10))

        self.output_banner = tk.Frame(right_card, bg=config.COLORS["surface_alt"], padx=18, pady=14, highlightbackground=config.COLORS["border"], highlightthickness=1)
        self.output_banner.pack(fill="x", pady=(0, 15))

        self.lbl_out_primary = tk.Label(self.output_banner, text="Enter parameters on the left and click 'Calculate Prediction'", font=config.FONTS["body"], bg=config.COLORS["surface_alt"], fg=config.COLORS["text_muted"])
        self.lbl_out_primary.pack(anchor="w")

        self.lbl_out_sub = tk.Label(self.output_banner, text="", font=config.FONTS["small"], bg=config.COLORS["surface_alt"], fg=config.COLORS["text_dark"])
        self.lbl_out_sub.pack(anchor="w", pady=(4, 0))

        # Output Chart Container
        self.chart_container = tk.Frame(right_card, bg=config.COLORS["surface"])
        self.chart_container.pack(fill="both", expand=True)

        self.show_default_result_chart()

    def render_task_form_inputs(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        def add_input(row, label, key, default_val, is_combo=False, vals=None):
            f = tk.Frame(container, bg=config.COLORS["surface"], pady=3)
            f.pack(fill="x")
            tk.Label(f, text=label, font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"], width=20, anchor="w").pack(side="left")
            if is_combo:
                w = ttk.Combobox(f, values=vals or [], state="readonly", width=22)
                if default_val in vals:
                    w.set(default_val)
                elif vals:
                    w.current(0)
            else:
                w = ttk.Entry(f, font=config.FONTS["body"], width=24)
                w.insert(0, str(default_val))
            w.pack(side="right", fill="x", expand=True)
            self.input_entries[key] = w

        cats = [
            "Analgesics & Antipyretics", "Antibiotics & Antivirals", "Antihistamines & Allergy",
            "Cardiovascular & Hypertension", "Vitamins & Supplements", "Gastrointestinal & Digestive",
            "Respiratory & Cough Care", "Topical & First Aid"
        ]

        if self.current_task == "product_demand":
            add_input(0, "Category:", "category", cats[0], is_combo=True, vals=cats)
            add_input(1, "Unit Price ($):", "unit_price", "12.50")
            add_input(2, "Cost Price ($):", "cost_price", "5.00")
            add_input(3, "Month (1-12):", "month", "11")
            add_input(4, "Day of Week (0-6):", "day_of_week", "5")
            add_input(5, "Flu Season?:", "is_flu_season", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(6, "Rainy Season?:", "is_rainy_season", "No (0)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(7, "Promotional Sale?:", "is_promotion", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(8, "Discount %:", "discount_percent", "15")
            add_input(9, "Current Stock Qty:", "stock_level", "150")

        elif self.current_task == "sales_revenue":
            add_input(0, "Month (1-12):", "month", "12")
            add_input(1, "Day of Week (0-6):", "day_of_week", "6")
            add_input(2, "Weekend?:", "is_weekend", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(3, "Holiday?:", "is_holiday", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(4, "Flu Season?:", "is_flu_season", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(5, "Rainy Season?:", "is_rainy_season", "No (0)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(6, "Promo Active?:", "promo_active", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(7, "Est. Foot Traffic:", "foot_traffic", "230")
            add_input(8, "Prescriptions Filled:", "prescriptions_filled", "75")
            add_input(9, "Avg Basket Size ($):", "avg_basket_size", "38.50")

        elif self.current_task == "slow_moving":
            add_input(0, "Category:", "category", cats[3], is_combo=True, vals=cats)
            add_input(1, "Unit Price ($):", "unit_price", "45.00")
            add_input(2, "Current Stock Qty:", "stock_qty", "280")
            add_input(3, "Shelf Life (days):", "shelf_life_days", "365")
            add_input(4, "Days Since Last Sale:", "days_since_last_sale", "48")
            add_input(5, "Monthly Sales Velocity:", "monthly_sales_velocity", "6.5")
            add_input(6, "Seasonal Product?:", "is_seasonal", "No (0)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(7, "Discount Applied %:", "discount_applied", "0")

        elif self.current_task == "best_selling":
            add_input(0, "Category:", "category", cats[6], is_combo=True, vals=cats)
            add_input(1, "Unit Price ($):", "unit_price", "8.50")
            add_input(2, "Hist. Monthly Demand:", "historical_monthly_demand", "320")
            add_input(3, "Customer Rating (1-5):", "customer_rating", "4.8")
            add_input(4, "Target Month (1-12):", "month", "12")
            add_input(5, "Flu Season?:", "is_flu_season", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(6, "Rainy Season?:", "is_rainy_season", "No (0)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(7, "Promotional Boost?:", "promo_active", "Yes (1)", is_combo=True, vals=["Yes (1)", "No (0)"])
            add_input(8, "Stock Availability %:", "stock_availability", "98.0")

    def execute_prediction(self):
        algo_choice = "rf" if "Random Forest" in self.combo_algo.get() else "linear"
        try:
            if self.current_task == "product_demand":
                res = ModelPredictor.predict_product_demand(
                    category=self.input_entries["category"].get(),
                    unit_price=float(self.input_entries["unit_price"].get()),
                    cost_price=float(self.input_entries["cost_price"].get()),
                    month=int(self.input_entries["month"].get()),
                    day_of_week=int(self.input_entries["day_of_week"].get()),
                    is_flu_season=1 if "Yes" in self.input_entries["is_flu_season"].get() else 0,
                    is_rainy_season=1 if "Yes" in self.input_entries["is_rainy_season"].get() else 0,
                    is_promotion=1 if "Yes" in self.input_entries["is_promotion"].get() else 0,
                    discount_percent=float(self.input_entries["discount_percent"].get()),
                    stock_level=int(self.input_entries["stock_level"].get()),
                    model_type=algo_choice
                )
                self.lbl_out_primary.config(
                    text=f"Predicted Demand: {res['predicted_demand']:.0f} units",
                    font=config.FONTS["h1"],
                    fg=config.COLORS["secondary_dark"]
                )
                self.lbl_out_sub.config(
                    text=f"Confidence Interval: {res['confidence_interval']} | Algorithm: {res['model_used']} (R²: {res['r2_score']:.3f})"
                )
                self.render_result_chart_demand(res)

            elif self.current_task == "sales_revenue":
                res = ModelPredictor.predict_sales_revenue(
                    month=int(self.input_entries["month"].get()),
                    day_of_week=int(self.input_entries["day_of_week"].get()),
                    is_weekend=1 if "Yes" in self.input_entries["is_weekend"].get() else 0,
                    is_holiday=1 if "Yes" in self.input_entries["is_holiday"].get() else 0,
                    is_flu_season=1 if "Yes" in self.input_entries["is_flu_season"].get() else 0,
                    is_rainy_season=1 if "Yes" in self.input_entries["is_rainy_season"].get() else 0,
                    promo_active=1 if "Yes" in self.input_entries["promo_active"].get() else 0,
                    foot_traffic=int(self.input_entries["foot_traffic"].get()),
                    prescriptions_filled=int(self.input_entries["prescriptions_filled"].get()),
                    avg_basket_size=float(self.input_entries["avg_basket_size"].get()),
                    model_type=algo_choice
                )
                self.lbl_out_primary.config(
                    text=f"Projected Daily Revenue: {config.CURRENCY}{res['predicted_revenue']:,.2f}",
                    font=config.FONTS["h1"],
                    fg=config.COLORS["secondary_dark"]
                )
                self.lbl_out_sub.config(
                    text=f"Confidence Interval: {res['confidence_interval']} | Algorithm: {res['model_used']} (R²: {res['r2_score']:.3f})"
                )
                self.render_result_chart_revenue(res)

            elif self.current_task == "slow_moving":
                res = ModelPredictor.predict_slow_moving(
                    category=self.input_entries["category"].get(),
                    unit_price=float(self.input_entries["unit_price"].get()),
                    stock_qty=int(self.input_entries["stock_qty"].get()),
                    shelf_life_days=int(self.input_entries["shelf_life_days"].get()),
                    days_since_last_sale=int(self.input_entries["days_since_last_sale"].get()),
                    monthly_sales_velocity=float(self.input_entries["monthly_sales_velocity"].get()),
                    is_seasonal=1 if "Yes" in self.input_entries["is_seasonal"].get() else 0,
                    discount_applied=float(self.input_entries["discount_applied"].get()),
                    model_type=algo_choice
                )
                color = config.COLORS["danger"] if res["is_slow_moving"] else config.COLORS["success"]
                self.lbl_out_primary.config(
                    text=f"Turnover Ratio: {res['predicted_turnover_ratio']:.1f}% ({res['status_label']})",
                    font=config.FONTS["h2"],
                    fg=color
                )
                self.lbl_out_sub.config(
                    text=f"{res['recommendation']} | Algorithm: {res['model_used']} (R²: {res['r2_score']:.3f})"
                )
                self.render_result_chart_slow_moving(res)

            elif self.current_task == "best_selling":
                res = ModelPredictor.predict_best_selling(
                    category=self.input_entries["category"].get(),
                    unit_price=float(self.input_entries["unit_price"].get()),
                    historical_monthly_demand=float(self.input_entries["historical_monthly_demand"].get()),
                    customer_rating=float(self.input_entries["customer_rating"].get()),
                    month=int(self.input_entries["month"].get()),
                    is_flu_season=1 if "Yes" in self.input_entries["is_flu_season"].get() else 0,
                    is_rainy_season=1 if "Yes" in self.input_entries["is_rainy_season"].get() else 0,
                    promo_active=1 if "Yes" in self.input_entries["promo_active"].get() else 0,
                    stock_availability=float(self.input_entries["stock_availability"].get()),
                    model_type=algo_choice
                )
                self.lbl_out_primary.config(
                    text=f"Projected Monthly Volume: {res['projected_units']:,} units ({res['tier_classification']})",
                    font=config.FONTS["h2"],
                    fg=config.COLORS["secondary_dark"]
                )
                self.lbl_out_sub.config(
                    text=f"Algorithm: {res['model_used']} (Model R²: {res['r2_score']:.3f})"
                )
                self.render_result_chart_best_selling(res)

        except ValueError as ve:
            messagebox.showerror("Input Validation Error", f"Invalid parameter entered:\n\n{ve}")
        except Exception as ex:
            messagebox.showerror("Prediction Error", f"An error occurred while generating prediction:\n\n{ex}")

    def show_default_result_chart(self):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5.5, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(config.COLORS["surface"])
        ax.text(0.5, 0.5, "Prediction visualization will appear here after calculation.", ha="center", va="center", color=config.COLORS["text_muted"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig, ax, canvas))

    def render_result_chart_demand(self, res):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5.5, 3.4), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(config.COLORS["surface"])

        categories = ["Lower Error Bound", "Predicted Demand", "Upper Error Bound"]
        values = [res["lower_bound"], res["predicted_demand"], res["upper_bound"]]
        colors = [config.COLORS["accent"], config.COLORS["secondary"], config.COLORS["accent"]]

        bars = ax.bar(categories, values, color=colors, width=0.45)
        ax.bar_label(bars, padding=4, color=config.COLORS["text_dark"], fontsize=9, fontweight="bold")
        ax.set_title("Predicted Demand with ±RMSE Confidence Interval", color=config.COLORS["text_dark"], fontsize=11, fontweight="bold")
        ax.set_ylabel("Quantity Demanded (Units)", color=config.COLORS["text_muted"], fontsize=9)
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig, ax, canvas))

    def render_result_chart_revenue(self, res):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5.5, 3.4), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(config.COLORS["surface"])

        categories = ["Min Bound", "Projected Revenue", "Max Bound"]
        values = [res["lower_bound"], res["predicted_revenue"], res["upper_bound"]]
        colors = [config.COLORS["accent"], config.COLORS["secondary_dark"], config.COLORS["accent"]]

        bars = ax.bar(categories, values, color=colors, width=0.45)
        ax.bar_label(bars, fmt=f"{config.CURRENCY}%0.0f", padding=4, color=config.COLORS["text_dark"], fontsize=9, fontweight="bold")
        ax.set_title("Projected Revenue Envelope", color=config.COLORS["text_dark"], fontsize=11, fontweight="bold")
        ax.set_ylabel("Daily Revenue ($)", color=config.COLORS["text_muted"], fontsize=9)
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig, ax, canvas))

    def render_result_chart_slow_moving(self, res):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5.5, 3.4), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(config.COLORS["surface"])

        turnover = res["predicted_turnover_ratio"]
        bar_color = config.COLORS["danger"] if res["is_slow_moving"] else config.COLORS["success"]

        ax.barh(["Inventory Turnover"], [turnover], color=bar_color, height=0.35)
        ax.axvline(15.0, color=config.COLORS["warning"], linestyle="--", linewidth=2, label="Critical Slow-Moving Threshold (15%)")

        ax.set_xlim(0, max(60, turnover + 15))
        ax.set_title("Product Turnover Ratio vs Risk Threshold", color=config.COLORS["text_dark"], fontsize=11, fontweight="bold")
        ax.set_xlabel("Turnover Ratio (%)", color=config.COLORS["text_muted"], fontsize=9)
        ax.legend(loc="upper right", fontsize=8)
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, axis="x", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig, ax, canvas))

    def render_result_chart_best_selling(self, res):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(5.5, 3.4), dpi=100, facecolor=config.COLORS["surface"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(config.COLORS["surface"])

        tiers = ["Tier 3: Moderate", "Tier 2: Steady Core", "Tier 1: Top Seller", "Projected"]
        volumes = [60, 160, 320, res["projected_units"]]
        colors = [config.COLORS["border"], config.COLORS["accent"], config.COLORS["secondary"], config.COLORS["secondary_dark"]]

        bars = ax.bar(tiers, volumes, color=colors, width=0.45)
        ax.bar_label(bars, padding=4, color=config.COLORS["text_dark"], fontsize=9, fontweight="bold")
        ax.set_title("Benchmarked Sales Tier Classification", color=config.COLORS["text_dark"], fontsize=11, fontweight="bold")
        ax.set_ylabel("Monthly Units", color=config.COLORS["text_muted"], fontsize=9)
        ax.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax.spines.values():
            spine.set_color(config.COLORS["border"])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig, ax, canvas))

    def build_metrics_view(self, parent):
        scroll_c = tk.Canvas(parent, bg=config.COLORS["background"], highlightthickness=0)
        sbar = ttk.Scrollbar(parent, orient="vertical", command=scroll_c.yview)
        inner = tk.Frame(scroll_c, bg=config.COLORS["background"], padx=20, pady=20)
        inner.bind("<Configure>", lambda e: scroll_c.configure(scrollregion=scroll_c.bbox("all")))
        scroll_c.create_window((0, 0), window=inner, anchor="nw")
        scroll_c.configure(yscrollcommand=sbar.set)
        scroll_c.pack(side="left", fill="both", expand=True)
        sbar.pack(side="right", fill="y")

        tk.Label(inner, text="Detailed Model Evaluation Metrics & Plain-Language Interpretations", font=config.FONTS["h2"], bg=config.COLORS["background"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(0, 15))

        rf_metrics = self.metadata.get("rf_metrics", {})
        lr_metrics = self.metadata.get("lr_metrics", {})

        for m_key, m_info in rf_metrics.items():
            card = tk.Frame(inner, bg=config.COLORS["surface"], padx=20, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
            card.pack(fill="x", pady=6)

            val_rf = m_info["value"]
            val_lr = lr_metrics.get(m_key, {}).get("value", 0.0)

            top_row = tk.Frame(card, bg=config.COLORS["surface"])
            top_row.pack(fill="x")

            tk.Label(top_row, text=m_info["title"], font=config.FONTS["h3"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"]).pack(side="left")
            
            badge_text = f"Random Forest: {val_rf:.4f}  |  Linear Regression: {val_lr:.4f}"
            tk.Label(top_row, text=badge_text, font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"], fg=config.COLORS["secondary_dark"], padx=10, pady=3).pack(side="right")

            tk.Label(card, text=f"Concept Definition: {m_info['description']}", font=config.FONTS["body"], bg=config.COLORS["surface"], fg=config.COLORS["text_muted"], wraplength=900, justify="left").pack(anchor="w", pady=(6, 2))
            tk.Label(card, text=f"Practical Interpretation: {m_info['interpretation']}", font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["secondary"], wraplength=900, justify="left").pack(anchor="w", pady=(2, 0))

        # Classification Metrics if slow_moving
        class_eval = self.metadata.get("classification_eval")
        if class_eval:
            tk.Label(inner, text="Classification Metrics (Slow-Moving Risk Detection)", font=config.FONTS["h2"], bg=config.COLORS["background"], fg=config.COLORS["text_dark"]).pack(anchor="w", pady=(20, 10))
            for c_key in ["Accuracy", "Precision", "Recall", "F1"]:
                c_info = class_eval.get(c_key)
                if c_info:
                    card = tk.Frame(inner, bg=config.COLORS["surface"], padx=20, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
                    card.pack(fill="x", pady=6)
                    top_row = tk.Frame(card, bg=config.COLORS["surface"])
                    top_row.pack(fill="x")
                    tk.Label(top_row, text=c_info["title"], font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(side="left")
                    tk.Label(top_row, text=f"Score: {c_info['value']:.4f}", font=config.FONTS["body_bold"], bg=config.COLORS["surface_alt"], fg=config.COLORS["accent"], padx=10, pady=3).pack(side="right")
                    tk.Label(card, text=f"Concept: {c_info['description']}", font=config.FONTS["body"], bg=config.COLORS["surface"], fg=config.COLORS["text_muted"]).pack(anchor="w", pady=(4, 2))
                    tk.Label(card, text=f"Interpretation: {c_info['interpretation']}", font=config.FONTS["body_bold"], bg=config.COLORS["surface"], fg=config.COLORS["secondary"]).pack(anchor="w")

    def build_comparison_view(self, parent):
        scroll_c = tk.Canvas(parent, bg=config.COLORS["background"], highlightthickness=0)
        sbar = ttk.Scrollbar(parent, orient="vertical", command=scroll_c.yview)
        inner = tk.Frame(scroll_c, bg=config.COLORS["background"], padx=20, pady=20)
        inner.bind("<Configure>", lambda e: scroll_c.configure(scrollregion=scroll_c.bbox("all")))
        scroll_c.create_window((0, 0), window=inner, anchor="nw")
        scroll_c.configure(yscrollcommand=sbar.set)
        scroll_c.pack(side="left", fill="both", expand=True)
        sbar.pack(side="right", fill="y")

        # Winner Summary Banner
        comp = self.metadata.get("comparison", {})
        winner_card = tk.Frame(inner, bg=config.COLORS["surface"], padx=20, pady=18, highlightbackground=config.COLORS["border"], highlightthickness=1)
        winner_card.pack(fill="x", pady=(0, 20))

        tk.Label(winner_card, text=f"🏆 Winning Algorithm: {comp.get('winner', 'N/A')}", font=config.FONTS["h2"], bg=config.COLORS["surface"], fg=config.COLORS["secondary_dark"]).pack(anchor="w")
        tk.Label(winner_card, text=comp.get("reason", ""), font=config.FONTS["body"], bg=config.COLORS["surface"], fg=config.COLORS["text_dark"], wraplength=950, justify="left").pack(anchor="w", pady=(8, 0))

        # Side-by-Side Table
        table_card = tk.Frame(inner, bg=config.COLORS["surface"], padx=20, pady=18, highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_card.pack(fill="x", pady=(0, 20))

        tk.Label(table_card, text="Side-by-Side Algorithmic Performance Comparison", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 10))

        cols = ("metric", "linear_reg", "random_forest", "delta")
        cmp_tree = ttk.Treeview(table_card, columns=cols, show="headings", height=6)
        cmp_tree.heading("metric", text="Evaluation Metric")
        cmp_tree.heading("linear_reg", text="Simple Linear Regression")
        cmp_tree.heading("random_forest", text="Random Forest Regression (Tuned)")
        cmp_tree.heading("delta", text="Variance / Advantage")

        cmp_tree.column("metric", width=220, anchor="w")
        cmp_tree.column("linear_reg", width=200, anchor="center")
        cmp_tree.column("random_forest", width=220, anchor="center")
        cmp_tree.column("delta", width=200, anchor="center")

        rf_m = self.metadata.get("rf_metrics", {})
        lr_m = self.metadata.get("lr_metrics", {})

        metrics_list = [
            ("R² (Variance Explained)", "R2", True),
            ("Root Mean Squared Error (RMSE)", "RMSE", False),
            ("Mean Absolute Error (MAE)", "MAE", False),
            ("Mean Squared Error (MSE)", "MSE", False),
            ("5-Fold CV Score (R²)", "CV_Score", True)
        ]

        for m_title, m_key, higher_better in metrics_list:
            v_lr = lr_m.get(m_key, {}).get("value", 0.0)
            v_rf = rf_m.get(m_key, {}).get("value", 0.0)
            diff = v_rf - v_lr
            if higher_better:
                adv = f"RF (+{diff:.4f})" if diff > 0 else f"LR (+{-diff:.4f})"
            else:
                adv = f"RF ({diff:.2f} lower)" if diff < 0 else f"LR ({-diff:.2f} lower)"

            cmp_tree.insert("", "end", values=(m_title, f"{v_lr:.4f}", f"{v_rf:.4f}", adv))

        cmp_tree.pack(fill="x")

        # Diagnostic Charts: Actual vs Predicted & Feature Importance
        charts_row = tk.Frame(inner, bg=config.COLORS["background"])
        charts_row.pack(fill="x", pady=(0, 20))

        # Chart 1: Actual vs Predicted
        c1_frame = tk.Frame(charts_row, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        c1_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(c1_frame, text="Actual vs Predicted Values (Holdout Set)", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 8))
        fig1 = Figure(figsize=(4.8, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax1 = fig1.add_subplot(111)
        ax1.set_facecolor(config.COLORS["surface"])

        scatter_data = self.metadata.get("sample_scatter", {})
        acts = scatter_data.get("actual", [])
        preds = scatter_data.get("predicted", [])
        if acts and preds:
            ax1.scatter(acts, preds, color=config.COLORS["accent"], alpha=0.7, edgecolors="none")
            min_v = min(min(acts), min(preds))
            max_v = max(max(acts), max(preds))
            ax1.plot([min_v, max_v], [min_v, max_v], color=config.COLORS["danger"], linestyle="--", linewidth=1.5, label="Perfect Fit (y=x)")
            ax1.legend(fontsize=8)
        ax1.set_xlabel("Actual Values", fontsize=8, color=config.COLORS["text_muted"])
        ax1.set_ylabel("Predicted Values", fontsize=8, color=config.COLORS["text_muted"])
        ax1.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax1.grid(True, linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax1.spines.values():
            spine.set_color(config.COLORS["border"])
        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=c1_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig1, ax1, canvas1))

        # Chart 2: Feature Importance
        c2_frame = tk.Frame(charts_row, bg=config.COLORS["surface"], padx=15, pady=15, highlightbackground=config.COLORS["border"], highlightthickness=1)
        c2_frame.pack(side="right", fill="both", expand=True)

        tk.Label(c2_frame, text="Top Feature Importances (Random Forest)", font=config.FONTS["h3"], bg=config.COLORS["surface"]).pack(anchor="w", pady=(0, 8))
        fig2 = Figure(figsize=(4.8, 3.2), dpi=100, facecolor=config.COLORS["surface"])
        ax2 = fig2.add_subplot(111)
        ax2.set_facecolor(config.COLORS["surface"])

        top_feats = self.metadata.get("top_features", [])
        if top_feats:
            f_names = [f["feature"][:16] for f in reversed(top_feats)]
            f_vals = [f["importance"] for f in reversed(top_feats)]
            bars = ax2.barh(f_names, f_vals, color=config.COLORS["secondary"], height=0.55)
            ax2.bar_label(bars, fmt="%0.2f", padding=3, color=config.COLORS["text_dark"], fontsize=8)

        ax2.set_xlabel("Importance Weight", fontsize=8, color=config.COLORS["text_muted"])
        ax2.tick_params(colors=config.COLORS["text_muted"], labelsize=8)
        ax2.grid(True, axis="x", linestyle="--", alpha=0.5, color=config.COLORS["border"])
        for spine in ax2.spines.values():
            spine.set_color(config.COLORS["border"])
        fig2.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=c2_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True)
        self._mpl_charts.append((fig2, ax2, canvas2))

    def build_dataset_view(self, parent):
        top_bar = tk.Frame(parent, bg=config.COLORS["surface"], padx=15, pady=12, highlightbackground=config.COLORS["border"], highlightthickness=1)
        top_bar.pack(fill="x", pady=(0, 10))

        csv_file = config.DATASETS_DIR / f"{self.current_task}.csv"
        df = pd.read_csv(csv_file) if csv_file.exists() else pd.DataFrame()

        tk.Label(top_bar, text=f"Dataset File: {csv_file.name}  |  Total Records: {len(df):,} rows, {len(df.columns)} columns", font=config.FONTS["body_bold"], bg=config.COLORS["surface"]).pack(side="left")

        table_frame = tk.Frame(parent, bg=config.COLORS["surface"], highlightbackground=config.COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        if not df.empty:
            cols = list(df.columns)
            tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=110, anchor="center")

            scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

            tree.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")

            # Insert preview rows (first 300 rows for smooth UI rendering)
            for _, row in df.head(300).iterrows():
                tree.insert("", "end", values=list(row))

    def apply_theme(self):
        """Updates active Matplotlib figures in place when toggling Light/Dark theme."""
        c = config.COLORS
        alive = []
        for fig, ax, canvas in self._mpl_charts:
            try:
                if not canvas.get_tk_widget().winfo_exists():
                    continue
            except Exception:
                continue
            alive.append((fig, ax, canvas))
            fig.set_facecolor(c["surface"])
            ax.set_facecolor(c["surface"])
            ax.title.set_color(c["text_dark"])
            ax.xaxis.label.set_color(c["text_muted"])
            ax.yaxis.label.set_color(c["text_muted"])
            ax.tick_params(colors=c["text_muted"], labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(c["border"])
            for txt in ax.texts:
                txt.set_color(c["text_dark"])
            ax.grid(True, linestyle="--", alpha=0.5, color=c["border"])
            canvas.draw_idle()
        self._mpl_charts = alive

    def handle_retrain(self):
        if messagebox.askyesno("Confirm Retraining", f"Trigger full retraining and hyperparameter tuning for task '{self.current_task}'?\n\nThis will re-fit models, calculate CV scores, and update saved .joblib files."):
            try:
                self.metadata = train.train_and_evaluate_task(self.current_task)
                messagebox.showinfo("Retraining Complete", f"Models for task '{self.current_task}' have been retrained and persisted successfully!")
                self.on_task_changed()
            except Exception as e:
                messagebox.showerror("Retraining Failed", f"Error retraining models: {e}")

