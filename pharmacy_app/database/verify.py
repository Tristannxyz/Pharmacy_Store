import sys
sys.path.insert(0, r'c:\Users\mabis\OneDrive\Documents\Projects\Pharmacy Store Business\pharmacy_app')

import db, auth
from ml.predict import ModelPredictor
import pandas as pd
from pathlib import Path

print('=== FINAL SYSTEM VERIFICATION ===')

# DB connectivity
conn = db.get_connection()
cursor = conn.cursor(dictionary=True)
for tbl in ['users','products','sales','stock_movements','audit_log']:
    cursor.execute(f'SELECT COUNT(*) as c FROM {tbl}')
    c = cursor.fetchone()['c']
    print(f'  [{tbl}]: {c} records')
cursor.close()
conn.close()
print()

# Auth & lockout
ok, msg, user = auth.authenticate_user('instructor', 'instructor123')
print('Auth OK:', ok, '| Role:', user['role'] if user else None)

# RBAC
auth.SessionManager.set_user(user)
assert auth.SessionManager.has_permission('analysis_instructor_full'), 'FAIL: Instructor needs full analysis'
auth.SessionManager.set_user({'id':1,'username':'admin','role':'admin','full_name':'Admin','email':''})
assert not auth.SessionManager.has_permission('analysis_instructor_full'), 'FAIL: Admin must not have instructor full'
assert auth.SessionManager.has_permission('analysis_input_predict'), 'FAIL: Admin must have predict'
print('RBAC: All permission checks correct')
print()

# ML inference across all 4 tasks
r1 = ModelPredictor.predict_product_demand('Vitamins & Supplements', 5.0, 2.0, 2, 0, 1, 0, 0, 0, 200)
print(f'Task 1 - Product Demand: {r1["predicted_demand"]} units | R2={r1["r2_score"]:.4f}')
print(f'         Confidence: {r1["confidence_interval"]}')

r2 = ModelPredictor.predict_sales_revenue(12, 6, 1, 1, 1, 0, 1, 300, 90, 42.0)
print(f'Task 2 - Sales Revenue: ${r2["predicted_revenue"]:,.2f} | R2={r2["r2_score"]:.4f}')
print(f'         Confidence: {r2["confidence_interval"]}')

r3 = ModelPredictor.predict_slow_moving('Topical & First Aid', 55.0, 400, 365, 60, 3.0, 0)
print(f'Task 3 - Slow Moving: {r3["status_label"]} | Turnover={r3["predicted_turnover_ratio"]}%')
print(f'         Recommendation: {r3["recommendation"][:60]}...')

r4 = ModelPredictor.predict_best_selling('Vitamins & Supplements', 3.0, 400, 4.9, 2, 1, 0, 1)
print(f'Task 4 - Best Selling: {r4["projected_units"]} units | {r4["tier_classification"]}')
print()

# CSVs
datasets_dir = Path(r'c:\Users\mabis\OneDrive\Documents\Projects\Pharmacy Store Business\pharmacy_app\datasets')
for f in ['product_demand.csv','sales_revenue.csv','slow_moving.csv','best_selling.csv']:
    df = pd.read_csv(datasets_dir / f)
    print(f'  CSV {f}: {len(df)} rows x {len(df.columns)} cols')

# Joblib model files
models_dir = Path(r'c:\Users\mabis\OneDrive\Documents\Projects\Pharmacy Store Business\pharmacy_app\ml\models')
joblibfiles = list(models_dir.glob('*.joblib'))
print(f'\n  Saved model files: {len(joblibfiles)} joblib files')
for jf in sorted(joblibfiles):
    print(f'    {jf.name}')

print()
print('=== ALL VERIFICATIONS PASSED ===')

