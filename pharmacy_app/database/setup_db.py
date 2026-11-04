import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import db
import config

def main():
    print("=" * 60)
    print("  PHARMACY STORE BUSINESS MANAGEMENT SYSTEM")
    print("  Database Auto-Setup & Seeding Script")
    print("=" * 60)
    try:
        db.init_database()
        print(f"\n[SUCCESS] Database '{config.DB_NAME}' setup completed successfully!")
        
        # Verify counts
        users = db.execute_query("SELECT username, role FROM users", fetchall=True)
        print("\nRegistered Accounts:")
        for u in users:
            print(f"  - Username: {u['username']:<18} Role: {u['role']}")

        prod_count = db.execute_query("SELECT COUNT(*) AS c FROM products", fetchone=True)["c"]
        cat_count = db.execute_query("SELECT COUNT(*) AS c FROM categories", fetchone=True)["c"]
        sup_count = db.execute_query("SELECT COUNT(*) AS c FROM suppliers", fetchone=True)["c"]
        sales_count = db.execute_query("SELECT COUNT(*) AS c FROM sales", fetchone=True)["c"]

        print(f"\nInventory & Setup Statistics:")
        print(f"  - Categories: {cat_count}")
        print(f"  - Suppliers:  {sup_count}")
        print(f"  - Products:   {prod_count} (Target: >= 50)")
        print(f"  - Sample Sales: {sales_count}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

