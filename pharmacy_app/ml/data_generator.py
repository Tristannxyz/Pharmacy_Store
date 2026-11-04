import random
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Ensure config path is accessible
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import config

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

CATEGORIES = [
    "Analgesics & Antipyretics",
    "Antibiotics & Antivirals",
    "Antihistamines & Allergy",
    "Cardiovascular & Hypertension",
    "Vitamins & Supplements",
    "Gastrointestinal & Digestive",
    "Respiratory & Cough Care",
    "Topical & First Aid"
]

def generate_product_demand_dataset(n_samples=1500, save_path=None):
    """
    Task 1 Dataset: Product Demand Prediction.
    Features include price, cost, month, day of week, seasonal flu/rainy flags,
    promotions, stock availability, and historical baseline demand.
    """
    rows = []
    for i in range(n_samples):
        cat = random.choice(CATEGORIES)
        month = random.randint(1, 12)
        day_of_week = random.randint(0, 6) # 0=Mon, 6=Sun
        is_flu_season = 1 if month in [11, 12, 1, 2] else (1 if (month == 10 and random.random() < 0.4) else 0)
        is_rainy_season = 1 if month in [6, 7, 8, 9] else 0

        # Baseline price based on category
        if cat in ["Cardiovascular & Hypertension", "Antibiotics & Antivirals"]:
            price = round(random.uniform(5.0, 35.0), 2)
        elif cat in ["Topical & First Aid", "Respiratory & Cough Care"]:
            price = round(random.uniform(3.0, 18.0), 2)
        else:
            price = round(random.uniform(1.0, 12.0), 2)

        cost = round(price * random.uniform(0.35, 0.65), 2)
        is_promotion = 1 if random.random() < 0.25 else 0
        discount_pct = random.choice([5, 10, 15, 20]) if is_promotion else 0
        stock_level = random.randint(10, 500)
        competitor_price_ratio = round(random.uniform(0.85, 1.25), 2)

        # Baseline demand calculation
        base_demand = random.uniform(25, 120)

        # Seasonality effects
        season_boost = 0.0
        if is_flu_season and cat in ["Respiratory & Cough Care", "Analgesics & Antipyretics", "Vitamins & Supplements"]:
            season_boost += random.uniform(35, 80)
        if is_rainy_season and cat in ["Antihistamines & Allergy", "Analgesics & Antipyretics", "Gastrointestinal & Digestive"]:
            season_boost += random.uniform(20, 50)

        # Price elasticity effect (higher price -> lower demand)
        price_elasticity = -1.2 * price + 30.0

        # Promotion effect
        promo_boost = random.uniform(15, 45) if is_promotion else 0.0

        # Day of week effect (Saturdays & Sundays busier)
        weekend_boost = random.uniform(10, 25) if day_of_week in [5, 6] else 0.0

        # Combine with noise
        noise = np.random.normal(0, 8)
        demand = base_demand + season_boost + promo_boost + weekend_boost + price_elasticity + noise
        demand = max(5, int(round(demand)))

        rows.append({
            "record_id": i + 1,
            "category": cat,
            "unit_price": price,
            "cost_price": cost,
            "month": month,
            "day_of_week": day_of_week,
            "is_flu_season": is_flu_season,
            "is_rainy_season": is_rainy_season,
            "is_promotion": is_promotion,
            "discount_percent": discount_pct,
            "stock_level": stock_level,
            "competitor_price_ratio": competitor_price_ratio,
            "quantity_demanded": demand
        })

    df = pd.DataFrame(rows)
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"[Generated] Product Demand: {len(df)} records -> {save_path}")
    return df

def generate_sales_revenue_dataset(n_samples=1500, save_path=None):
    """
    Task 2 Dataset: Sales Revenue Prediction.
    Features include foot traffic, prescriptions filled, average basket size,
    holidays, weekends, flu & rainy seasons, promotional campaigns.
    Target is total_daily_revenue.
    """
    rows = []
    for i in range(n_samples):
        month = random.randint(1, 12)
        day_of_week = random.randint(0, 6)
        is_weekend = 1 if day_of_week in [5, 6] else 0
        is_holiday = 1 if random.random() < 0.08 else 0
        is_flu_season = 1 if month in [11, 12, 1, 2] else 0
        is_rainy_season = 1 if month in [6, 7, 8, 9] else 0
        promo_active = 1 if random.random() < 0.30 else 0

        # Foot traffic (customers entering store per day)
        base_traffic = random.uniform(80, 250)
        if is_weekend:
            base_traffic += random.uniform(40, 90)
        if is_holiday:
            base_traffic += random.uniform(50, 110)
        if promo_active:
            base_traffic += random.uniform(30, 70)
        if is_flu_season:
            base_traffic += random.uniform(25, 60)
        foot_traffic = int(round(base_traffic))

        # Prescriptions filled
        rx_filled = int(round(foot_traffic * random.uniform(0.20, 0.45)))

        # Average basket size ($ per transaction)
        avg_basket = round(random.uniform(15.0, 48.0) + (8.0 if promo_active else 0.0), 2)

        # Revenue formula + noise
        revenue = (foot_traffic * avg_basket * random.uniform(0.85, 1.15)) + (rx_filled * 14.5)
        revenue = round(max(300.0, float(revenue)), 2)

        rows.append({
            "record_id": i + 1,
            "month": month,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "is_flu_season": is_flu_season,
            "is_rainy_season": is_rainy_season,
            "promo_campaign_active": promo_active,
            "foot_traffic": foot_traffic,
            "prescriptions_filled": rx_filled,
            "avg_basket_size": avg_basket,
            "total_daily_revenue": revenue
        })

    df = pd.DataFrame(rows)
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"[Generated] Sales Revenue: {len(df)} records -> {save_path}")
    return df

def generate_slow_moving_dataset(n_samples=1400, save_path=None):
    """
    Task 3 Dataset: Slow-Moving Product Prediction.
    Identifies products with low turnover ratio relative to current inventory stock.
    Target: turnover_ratio (continuous demand-to-stock ratio) and is_slow_moving (1 if slow, 0 if healthy).
    """
    rows = []
    for i in range(n_samples):
        cat = random.choice(CATEGORIES)
        price = round(random.uniform(2.0, 60.0), 2)
        stock_qty = random.randint(20, 600)
        shelf_life_days = random.choice([180, 365, 540, 730, 900])
        days_since_last_sale = random.randint(0, 95)
        monthly_sales_velocity = random.uniform(2.0, 150.0)
        is_seasonal = 1 if cat in ["Antihistamines & Allergy", "Respiratory & Cough Care"] else 0
        discount_applied = random.choice([0, 5, 10, 15, 20])

        # High price, high stock, and high days_since_last_sale correlate strongly with slow movement
        turnover_score = (monthly_sales_velocity / max(1, stock_qty)) * 100.0
        # Deductions
        if days_since_last_sale > 30:
            turnover_score -= (days_since_last_sale * 0.4)
        if price > 30.0:
            turnover_score -= 8.0

        turnover_ratio = round(max(0.5, float(turnover_score + np.random.normal(0, 3))), 2)
        # Slow moving if monthly turnover is below 15% of stock
        is_slow = 1 if turnover_ratio < 15.0 or days_since_last_sale > 40 else 0

        rows.append({
            "record_id": i + 1,
            "category": cat,
            "unit_price": price,
            "stock_qty": stock_qty,
            "shelf_life_days": shelf_life_days,
            "days_since_last_sale": days_since_last_sale,
            "monthly_sales_velocity": round(monthly_sales_velocity, 1),
            "is_seasonal": is_seasonal,
            "discount_applied": discount_applied,
            "turnover_ratio": turnover_ratio,
            "is_slow_moving": is_slow
        })

    df = pd.DataFrame(rows)
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"[Generated] Slow Moving: {len(df)} records -> {save_path}")
    return df

def generate_best_selling_dataset(n_samples=1400, save_path=None):
    """
    Task 4 Dataset: Best-Selling Product Prediction.
    Ranks products by predicted demand volume and velocity to highlight top performers.
    Target: projected_monthly_units (continuous) and is_top_seller (1 if in top tier).
    """
    rows = []
    for i in range(n_samples):
        cat = random.choice(CATEGORIES)
        unit_price = round(random.uniform(0.50, 40.0), 2)
        historical_monthly_demand = random.uniform(20, 500)
        customer_rating = round(random.uniform(3.0, 5.0), 1)
        month = random.randint(1, 12)
        is_flu_season = 1 if month in [11, 12, 1, 2] else 0
        is_rainy_season = 1 if month in [6, 7, 8, 9] else 0
        promo_active = 1 if random.random() < 0.28 else 0
        stock_availability_pct = round(random.uniform(70.0, 100.0), 1)
        brand_tier = random.choice([1, 2, 3]) # 1=Generic, 2=Popular, 3=Leading Global

        # Projected demand
        projected = historical_monthly_demand * (customer_rating / 4.0) * (stock_availability_pct / 100.0)
        if brand_tier == 3:
            projected *= 1.35
        elif brand_tier == 2:
            projected *= 1.15
        if promo_active:
            projected *= 1.25
        if is_flu_season and cat in ["Respiratory & Cough Care", "Analgesics & Antipyretics", "Vitamins & Supplements"]:
            projected *= 1.40

        projected += np.random.normal(0, 15)
        projected_units = max(10, int(round(projected)))
        is_top_seller = 1 if projected_units >= 250 else 0

        rows.append({
            "record_id": i + 1,
            "category": cat,
            "unit_price": unit_price,
            "historical_monthly_demand": round(historical_monthly_demand, 1),
            "customer_rating": customer_rating,
            "month": month,
            "is_flu_season": is_flu_season,
            "is_rainy_season": is_rainy_season,
            "promo_active": promo_active,
            "stock_availability_pct": stock_availability_pct,
            "brand_tier": brand_tier,
            "projected_monthly_units": projected_units,
            "is_top_seller": is_top_seller
        })

    df = pd.DataFrame(rows)
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"[Generated] Best Selling: {len(df)} records -> {save_path}")
    return df

def generate_all_datasets():
    """Generates all 4 synthetic CSV datasets into the configured datasets directory."""
    print("=" * 60)
    print("  GENERATING SYNTHETIC PHARMACY MACHINE LEARNING DATASETS")
    print("=" * 60)
    config.DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    p1 = config.DATASETS_DIR / "product_demand.csv"
    p2 = config.DATASETS_DIR / "sales_revenue.csv"
    p3 = config.DATASETS_DIR / "slow_moving.csv"
    p4 = config.DATASETS_DIR / "best_selling.csv"

    df1 = generate_product_demand_dataset(1500, p1)
    df2 = generate_sales_revenue_dataset(1500, p2)
    df3 = generate_slow_moving_dataset(1400, p3)
    df4 = generate_best_selling_dataset(1400, p4)

    print("=" * 60)
    print(f"All datasets generated with fixed random seed {RANDOM_SEED} (1400-1500 records each).")
    return df1, df2, df3, df4

if __name__ == "__main__":
    generate_all_datasets()

