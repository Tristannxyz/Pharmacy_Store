import os
import sys
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from ml import train

logger = logging.getLogger(__name__)

class ModelPredictor:
    """Loads saved models from ml/models/ and performs robust validated predictions."""

    @classmethod
    def get_models(cls, task_name):
        """Loads or auto-trains models for the specified task."""
        lr_path = config.MODELS_DIR / f"{task_name}_linear.joblib"
        rf_path = config.MODELS_DIR / f"{task_name}_rf.joblib"
        meta_path = config.MODELS_DIR / f"{task_name}_meta.joblib"

        if not lr_path.exists() or not rf_path.exists() or not meta_path.exists():
            logger.info(f"Models for {task_name} not found. Running training pipeline...")
            train.train_and_evaluate_task(task_name)

        lr_model = joblib.load(lr_path)
        rf_model = joblib.load(rf_path)
        meta = joblib.load(meta_path)
        return lr_model, rf_model, meta

    @classmethod
    def predict_product_demand(cls, category, unit_price, cost_price, month, day_of_week, is_flu_season, is_rainy_season, is_promotion, discount_percent, stock_level, competitor_ratio=1.0, model_type="rf"):
        """Task 1: Predict Product Demand Volume."""
        # Input Validation
        if unit_price <= 0 or cost_price < 0:
            raise ValueError("Unit price and cost price must be positive numbers.")
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")
        if day_of_week < 0 or day_of_week > 6:
            raise ValueError("Day of week must be between 0 (Mon) and 6 (Sun).")
        if stock_level < 0:
            raise ValueError("Stock level cannot be negative.")

        lr_model, rf_model, meta = cls.get_models("product_demand")
        model = rf_model if model_type == "rf" else lr_model

        # Feature Engineering matching train.py
        profit_margin = (unit_price - cost_price) / max(0.01, unit_price)
        flu_resp_interaction = is_flu_season * (1 if "Respiratory" in str(category) or "Analgesic" in str(category) else 0)

        input_data = pd.DataFrame([{
            "category": category,
            "unit_price": float(unit_price),
            "cost_price": float(cost_price),
            "profit_margin": float(profit_margin),
            "month": int(month),
            "day_of_week": int(day_of_week),
            "is_flu_season": int(is_flu_season),
            "is_rainy_season": int(is_rainy_season),
            "is_promotion": int(is_promotion),
            "discount_percent": float(discount_percent),
            "stock_level": int(stock_level),
            "competitor_price_ratio": float(competitor_ratio),
            "flu_resp_interaction": float(flu_resp_interaction)
        }])

        pred_val = float(model.predict(input_data)[0])
        pred_val = max(1.0, round(pred_val, 1))

        # Prediction Confidence & Error Range based on RMSE
        rmse = meta["rf_metrics"]["RMSE"]["value"] if model_type == "rf" else meta["lr_metrics"]["RMSE"]["value"]
        lower_bound = max(0, round(pred_val - rmse, 1))
        upper_bound = round(pred_val + rmse, 1)

        return {
            "predicted_demand": pred_val,
            "unit": "units",
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_interval": f"{lower_bound} - {upper_bound} units (±{rmse:.1f} RMSE margin)",
            "model_used": "Random Forest Regressor" if model_type == "rf" else "Linear Regression",
            "r2_score": meta["rf_metrics"]["R2"]["value"] if model_type == "rf" else meta["lr_metrics"]["R2"]["value"]
        }

    @classmethod
    def predict_sales_revenue(cls, month, day_of_week, is_weekend, is_holiday, is_flu_season, is_rainy_season, promo_active, foot_traffic, prescriptions_filled, avg_basket_size, model_type="rf"):
        """Task 2: Predict Sales Revenue."""
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")
        if foot_traffic < 0 or avg_basket_size <= 0:
            raise ValueError("Foot traffic and average basket size must be positive numbers.")

        lr_model, rf_model, meta = cls.get_models("sales_revenue")
        model = rf_model if model_type == "rf" else lr_model

        # Feature Engineering matching train.py
        traffic_basket_interaction = foot_traffic * avg_basket_size
        weekend_traffic = is_weekend * foot_traffic

        input_data = pd.DataFrame([{
            "month": int(month),
            "day_of_week": int(day_of_week),
            "is_weekend": int(is_weekend),
            "is_holiday": int(is_holiday),
            "is_flu_season": int(is_flu_season),
            "is_rainy_season": int(is_rainy_season),
            "promo_campaign_active": int(promo_active),
            "foot_traffic": int(foot_traffic),
            "prescriptions_filled": int(prescriptions_filled),
            "avg_basket_size": float(avg_basket_size),
            "traffic_basket_interaction": float(traffic_basket_interaction),
            "weekend_traffic": float(weekend_traffic)
        }])

        pred_rev = float(model.predict(input_data)[0])
        pred_rev = max(50.0, round(pred_rev, 2))

        rmse = meta["rf_metrics"]["RMSE"]["value"] if model_type == "rf" else meta["lr_metrics"]["RMSE"]["value"]
        lower_bound = max(0.0, round(pred_rev - rmse, 2))
        upper_bound = round(pred_rev + rmse, 2)

        return {
            "predicted_revenue": pred_rev,
            "unit": "$",
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_interval": f"{config.CURRENCY}{lower_bound:,.2f} - {config.CURRENCY}{upper_bound:,.2f} (±{config.CURRENCY}{rmse:.2f} RMSE margin)",
            "model_used": "Random Forest Regressor" if model_type == "rf" else "Linear Regression",
            "r2_score": meta["rf_metrics"]["R2"]["value"] if model_type == "rf" else meta["lr_metrics"]["R2"]["value"]
        }

    @classmethod
    def predict_slow_moving(cls, category, unit_price, stock_qty, shelf_life_days, days_since_last_sale, monthly_sales_velocity, is_seasonal, discount_applied=0, model_type="rf"):
        """Task 3: Identify Slow-Moving Product."""
        if unit_price <= 0 or stock_qty < 0:
            raise ValueError("Unit price and stock quantity must be valid non-negative values.")

        lr_model, rf_model, meta = cls.get_models("slow_moving")
        model = rf_model if model_type == "rf" else lr_model

        # Feature Engineering matching train.py
        turnover_velocity_ratio = monthly_sales_velocity / max(1, stock_qty)
        dormancy_risk = days_since_last_sale * unit_price

        input_data = pd.DataFrame([{
            "category": category,
            "unit_price": float(unit_price),
            "stock_qty": int(stock_qty),
            "shelf_life_days": int(shelf_life_days),
            "days_since_last_sale": int(days_since_last_sale),
            "monthly_sales_velocity": float(monthly_sales_velocity),
            "is_seasonal": int(is_seasonal),
            "discount_applied": float(discount_applied),
            "turnover_velocity_ratio": float(turnover_velocity_ratio),
            "dormancy_risk": float(dormancy_risk)
        }])

        predicted_turnover = float(model.predict(input_data)[0])
        predicted_turnover = max(0.1, round(predicted_turnover, 2))

        # Risk threshold: turnover ratio < 15% indicates slow-moving inventory risk
        is_slow = predicted_turnover < 15.0 or days_since_last_sale > 40
        status_label = "SLOW-MOVING (High Overstock Risk)" if is_slow else "HEALTHY TURNOVER"
        recommendation = (
            "Recommended Action: Apply promotional markdown (10-15%), halt reordering, or bundle with fast-movers."
            if is_slow else
            "Recommended Action: Maintain regular replenishment schedule. Inventory flow is stable."
        )

        return {
            "predicted_turnover_ratio": predicted_turnover,
            "is_slow_moving": is_slow,
            "status_label": status_label,
            "recommendation": recommendation,
            "model_used": "Random Forest Regressor" if model_type == "rf" else "Linear Regression",
            "r2_score": meta["rf_metrics"]["R2"]["value"] if model_type == "rf" else meta["lr_metrics"]["R2"]["value"]
        }

    @classmethod
    def predict_best_selling(cls, category, unit_price, historical_monthly_demand, customer_rating, month, is_flu_season, is_rainy_season, promo_active, stock_availability=95.0, brand_tier=2, model_type="rf"):
        """Task 4: Rank Best-Selling Product Demand."""
        if unit_price <= 0 or customer_rating < 1 or customer_rating > 5:
            raise ValueError("Customer rating must be between 1.0 and 5.0.")

        lr_model, rf_model, meta = cls.get_models("best_selling")
        model = rf_model if model_type == "rf" else lr_model

        # Feature Engineering matching train.py
        value_demand_score = customer_rating * historical_monthly_demand
        brand_promo_interaction = brand_tier * (1 + 0.3 * promo_active)

        input_data = pd.DataFrame([{
            "category": category,
            "unit_price": float(unit_price),
            "historical_monthly_demand": float(historical_monthly_demand),
            "customer_rating": float(customer_rating),
            "month": int(month),
            "is_flu_season": int(is_flu_season),
            "is_rainy_season": int(is_rainy_season),
            "promo_active": int(promo_active),
            "stock_availability_pct": float(stock_availability),
            "brand_tier": int(brand_tier),
            "value_demand_score": float(value_demand_score),
            "brand_promo_interaction": float(brand_promo_interaction)
        }])

        pred_units = float(model.predict(input_data)[0])
        pred_units = max(5, int(round(pred_units)))

        tier = "Tier 1: Top Seller / Blockbuster" if pred_units >= 250 else ("Tier 2: Steady Core Seller" if pred_units >= 120 else "Tier 3: Moderate Volume")
        return {
            "projected_units": pred_units,
            "tier_classification": tier,
            "model_used": "Random Forest Regressor" if model_type == "rf" else "Linear Regression",
            "r2_score": meta["rf_metrics"]["R2"]["value"] if model_type == "rf" else meta["lr_metrics"]["R2"]["value"]
        }

