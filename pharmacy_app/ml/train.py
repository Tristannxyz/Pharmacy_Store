import os
import sys
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, KFold, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# Ensure root paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
import db
from ml.data_generator import generate_all_datasets
from ml.evaluate import calculate_regression_metrics, calculate_classification_metrics, compare_models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TASKS = ["product_demand", "sales_revenue", "slow_moving", "best_selling"]

def handle_outliers(df, numeric_cols):
    """Outlier Handling: Clips extreme values using Interquartile Range (IQR)."""
    df_clean = df.copy()
    for col in numeric_cols:
        if col in df_clean.columns:
            q1 = df_clean[col].quantile(0.01)
            q3 = df_clean[col].quantile(0.99)
            df_clean[col] = df_clean[col].clip(q1, q3)
    return df_clean

def load_combined_data(task_name):
    """
    Loads dataset from CSV in datasets/ and augments with real MySQL sales data if available.
    """
    csv_file = config.DATASETS_DIR / f"{task_name}.csv"
    if not csv_file.exists():
        logger.info(f"Dataset {csv_file} not found. Generating datasets now...")
        generate_all_datasets()

    df = pd.read_csv(csv_file)
    logger.info(f"Loaded {len(df)} records from {csv_file.name}")

    # Combine with real MySQL sales data if available
    try:
        if task_name == "sales_revenue":
            real_sales = db.execute_query("""
                SELECT 
                    MONTH(created_at) as month,
                    DAYOFWEEK(created_at) - 1 as day_of_week,
                    CASE WHEN DAYOFWEEK(created_at) IN (1, 7) THEN 1 ELSE 0 END as is_weekend,
                    0 as is_holiday,
                    CASE WHEN MONTH(created_at) IN (11, 12, 1, 2) THEN 1 ELSE 0 END as is_flu_season,
                    CASE WHEN MONTH(created_at) IN (6, 7, 8, 9) THEN 1 ELSE 0 END as is_rainy_season,
                    0 as promo_campaign_active,
                    COUNT(DISTINCT invoice_no) * 8 as foot_traffic,
                    COUNT(DISTINCT invoice_no) as prescriptions_filled,
                    AVG(total_amount) as avg_basket_size,
                    SUM(total_amount) as total_daily_revenue
                FROM sales
                GROUP BY DATE(created_at), month, day_of_week, is_weekend, is_flu_season, is_rainy_season
                HAVING total_daily_revenue > 0
            """, fetchall=True)

            if real_sales and len(real_sales) > 0:
                real_df = pd.DataFrame(real_sales)
                real_df["record_id"] = range(len(df) + 1, len(df) + 1 + len(real_df))
                for col in df.columns:
                    if col in real_df.columns:
                        real_df[col] = pd.to_numeric(real_df[col], errors="coerce").fillna(0)
                df = pd.concat([df, real_df], ignore_index=True)
                logger.info(f"Augmented with {len(real_df)} real daily sales records from MySQL database.")

        elif task_name == "product_demand":
            real_items = db.execute_query("""
                SELECT 
                    c.name as category,
                    p.selling_price as unit_price,
                    p.cost_price as cost_price,
                    MONTH(s.created_at) as month,
                    DAYOFWEEK(s.created_at) - 1 as day_of_week,
                    CASE WHEN MONTH(s.created_at) IN (11, 12, 1, 2) THEN 1 ELSE 0 END as is_flu_season,
                    CASE WHEN MONTH(s.created_at) IN (6, 7, 8, 9) THEN 1 ELSE 0 END as is_rainy_season,
                    0 as is_promotion,
                    0 as discount_percent,
                    p.stock_qty as stock_level,
                    1.0 as competitor_price_ratio,
                    SUM(si.quantity) as quantity_demanded
                FROM sales_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                GROUP BY si.product_id, c.name, p.selling_price, p.cost_price, month, day_of_week, is_flu_season, is_rainy_season, p.stock_qty
            """, fetchall=True)

            if real_items and len(real_items) > 0:
                real_df = pd.DataFrame(real_items)
                real_df["record_id"] = range(len(df) + 1, len(df) + 1 + len(real_df))
                for col in ["unit_price", "cost_price", "month", "day_of_week", "is_flu_season", "is_rainy_season", "is_promotion", "discount_percent", "stock_level", "competitor_price_ratio", "quantity_demanded"]:
                    if col in real_df.columns:
                        real_df[col] = pd.to_numeric(real_df[col], errors="coerce").fillna(0)
                df = pd.concat([df, real_df], ignore_index=True)
                logger.info(f"Augmented with {len(real_df)} real product sales aggregations from MySQL database.")
    except Exception as e:
        logger.warning(f"Could not fetch real data for augmentation: {e}. Using CSV data.")

    return df

def train_and_evaluate_task(task_name):
    """
    Trains both Simple Linear Regression and Random Forest Regression for a given task.
    Includes:
    - Feature Engineering
    - Outlier Handling
    - Imputation & One-Hot Encoding
    - StandardScaler
    - 5-Fold Cross Validation
    - Hyperparameter Tuning with GridSearchCV
    - Evaluation & Model Comparison
    - Joblib Persistence
    """
    logger.info(f"\n{'='*20} Training Models for Task: {task_name.upper()} {'='*20}")
    df = load_combined_data(task_name)

    # 1. Feature Engineering & Column Separation
    if task_name == "product_demand":
        # Feature Engineering: Price margin ratio & flu interaction
        df["profit_margin"] = (df["unit_price"] - df["cost_price"]) / df["unit_price"].replace(0, 1)
        df["flu_resp_interaction"] = df["is_flu_season"] * df["category"].apply(lambda c: 1 if "Respiratory" in str(c) or "Analgesic" in str(c) else 0)

        target_col = "quantity_demanded"
        cat_features = ["category"]
        num_features = ["unit_price", "cost_price", "profit_margin", "month", "day_of_week", "is_flu_season", "is_rainy_season", "is_promotion", "discount_percent", "stock_level", "competitor_price_ratio", "flu_resp_interaction"]
        unit = "units"

    elif task_name == "sales_revenue":
        # Feature Engineering: Traffic per basket ratio & holiday interaction
        df["traffic_basket_interaction"] = df["foot_traffic"] * df["avg_basket_size"]
        df["weekend_traffic"] = df["is_weekend"] * df["foot_traffic"]

        target_col = "total_daily_revenue"
        cat_features = []
        num_features = ["month", "day_of_week", "is_weekend", "is_holiday", "is_flu_season", "is_rainy_season", "promo_campaign_active", "foot_traffic", "prescriptions_filled", "avg_basket_size", "traffic_basket_interaction", "weekend_traffic"]
        unit = "$"

    elif task_name == "slow_moving":
        # Feature Engineering: Days per turnover velocity
        df["turnover_velocity_ratio"] = df["monthly_sales_velocity"] / df["stock_qty"].replace(0, 1)
        df["dormancy_risk"] = df["days_since_last_sale"] * df["unit_price"]

        target_col = "turnover_ratio"
        cat_features = ["category"]
        num_features = ["unit_price", "stock_qty", "shelf_life_days", "days_since_last_sale", "monthly_sales_velocity", "is_seasonal", "discount_applied", "turnover_velocity_ratio", "dormancy_risk"]
        unit = "% turnover"

    elif task_name == "best_selling":
        # Feature Engineering: Rating to price value score
        df["value_demand_score"] = df["customer_rating"] * df["historical_monthly_demand"]
        df["brand_promo_interaction"] = df["brand_tier"] * (1 + 0.3 * df["promo_active"])

        target_col = "projected_monthly_units"
        cat_features = ["category"]
        num_features = ["unit_price", "historical_monthly_demand", "customer_rating", "month", "is_flu_season", "is_rainy_season", "promo_active", "stock_availability_pct", "brand_tier", "value_demand_score", "brand_promo_interaction"]
        unit = "units"

    # Outlier handling on numeric columns
    df = handle_outliers(df, num_features)

    X = df[cat_features + num_features]
    y = df[target_col]

    # Preprocessing Pipeline: Impute + Scale Numerics, Impute + OneHot Encode Categoricals
    num_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    transformers = [("num", num_transformer, num_features)]
    if cat_features:
        cat_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])
        transformers.append(("cat", cat_transformer, cat_features))

    preprocessor = ColumnTransformer(transformers=transformers)

    # 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    # 2. Fit Simple / Multiple Linear Regression
    lr_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression())
    ])

    # 5-Fold Cross Validation for Linear Regression
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)
    lr_cv_scores = cross_val_score(lr_pipeline, X_train, y_train, cv=kfold, scoring="r2")
    lr_pipeline.fit(X_train, y_train)
    y_pred_lr = lr_pipeline.predict(X_test)
    lr_metrics = calculate_regression_metrics(y_test, y_pred_lr, cv_scores=lr_cv_scores, unit=unit)

    # 3. Hyperparameter Tuning for Random Forest
    rf_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(random_state=42, n_jobs=-1))
    ])

    param_grid = {
        "regressor__n_estimators": [60, 100],
        "regressor__max_depth": [8, 14, None],
        "regressor__min_samples_split": [2, 5]
    }

    grid_search = GridSearchCV(rf_pipeline, param_grid, cv=3, scoring="r2", n_jobs=-1)
    grid_search.fit(X_train, y_train)
    best_rf_pipeline = grid_search.best_estimator_

    rf_cv_scores = cross_val_score(best_rf_pipeline, X_train, y_train, cv=kfold, scoring="r2")
    y_pred_rf = best_rf_pipeline.predict(X_test)
    rf_metrics = calculate_regression_metrics(y_test, y_pred_rf, cv_scores=rf_cv_scores, unit=unit)

    # Classification Metrics for Slow-Moving (if applicable)
    classification_eval = None
    if task_name == "slow_moving":
        # Binary target: 1 if slow moving (turnover < 15), 0 otherwise
        y_test_binary = (y_test < 15.0).astype(int)
        y_pred_binary = (y_pred_rf < 15.0).astype(int)
        classification_eval = calculate_classification_metrics(y_test_binary, y_pred_binary)

    # Feature Importance Extraction from Random Forest
    rf_regressor = best_rf_pipeline.named_steps["regressor"]
    fitted_preprocessor = best_rf_pipeline.named_steps["preprocessor"]

    feature_names = list(num_features)
    if cat_features and "cat" in fitted_preprocessor.named_transformers_:
        cat_onehot = fitted_preprocessor.named_transformers_["cat"].named_steps["onehot"]
        encoded_cats = cat_onehot.get_feature_names_out(cat_features).tolist()
        feature_names.extend(encoded_cats)

    importances = rf_regressor.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    top_features = [{"feature": feature_names[i], "importance": float(importances[i])} for i in sorted_idx[:8]]

    # Compare models
    comparison = compare_models(lr_metrics, rf_metrics)

    # Residuals & Sample Scatter Data for visualization
    sample_size = min(60, len(y_test))
    y_test_sample = np.array(y_test)[:sample_size].tolist()
    y_pred_sample = np.array(y_pred_rf)[:sample_size].tolist()
    residuals_sample = (np.array(y_test_sample) - np.array(y_pred_sample)).tolist()

    # Save to disk with joblib
    models_dir = config.MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)

    lr_path = models_dir / f"{task_name}_linear.joblib"
    rf_path = models_dir / f"{task_name}_rf.joblib"
    meta_path = models_dir / f"{task_name}_meta.joblib"

    joblib.dump(lr_pipeline, lr_path)
    joblib.dump(best_rf_pipeline, rf_path)

    metadata = {
        "task_name": task_name,
        "unit": unit,
        "target_col": target_col,
        "num_features": num_features,
        "cat_features": cat_features,
        "lr_metrics": lr_metrics,
        "rf_metrics": rf_metrics,
        "classification_eval": classification_eval,
        "comparison": comparison,
        "top_features": top_features,
        "best_params": grid_search.best_params_,
        "sample_scatter": {
            "actual": y_test_sample,
            "predicted": y_pred_sample,
            "residuals": residuals_sample
        }
    }
    joblib.dump(metadata, meta_path)

    logger.info(f"Saved models for {task_name}:")
    logger.info(f"  - Linear: {lr_path.name} (R² = {lr_metrics['R2']['value']:.4f})")
    logger.info(f"  - Random Forest: {rf_path.name} (R² = {rf_metrics['R2']['value']:.4f})")
    logger.info(f"  - Comparison: {comparison['winner']} won! ({comparison['reason'][:75]}...)")

    return metadata

def train_all_tasks():
    """Trains all 4 required prediction tasks."""
    results = {}
    for task in TASKS:
        meta = train_and_evaluate_task(task)
        results[task] = meta
    return results

if __name__ == "__main__":
    train_all_tasks()

