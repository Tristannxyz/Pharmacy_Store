import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import db

def dump_table(table_name):
    rows = db.execute_query(f"SELECT * FROM `{table_name}`", fetchall=True)
    if not rows:
        return ""
    cols = list(rows[0].keys())
    col_str = ", ".join([f"`{c}`" for c in cols])
    lines = [f"-- Data for table `{table_name}`", f"INSERT INTO `{table_name}` ({col_str}) VALUES"]
    val_lines = []
    for r in rows:
        vals = []
        for c in cols:
            v = r[c]
            if v is None:
                vals.append("NULL")
            elif isinstance(v, (int, float)):
                vals.append(str(v))
            else:
                s = str(v).replace("\\", "\\\\").replace("'", "''")
                vals.append(f"'{s}'")
        val_lines.append("  (" + ", ".join(vals) + ")")
    lines.append(",\n".join(val_lines) + ";")
    return "\n".join(lines) + "\n\n"

def main():
    schema_path = PROJECT_ROOT / "database" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    full_sql = (
        "-- ====================================================================\n"
        "-- PHARMACARE — COMPLETE DATABASE DUMP (STRUCTURE + DATA)\n"
        "-- For School Project Presentation & Professor Evaluation\n"
        "-- Database Name: pharmacy\n"
        "-- Compatible with MySQL 8.x / MariaDB / WAMP phpMyAdmin\n"
        "-- ====================================================================\n\n"
        + schema_sql +
        "\n\n-- ====================================================================\n"
        "-- SEED DATA: Categories, Suppliers, Users, 57 Products & Sample Sales\n"
        "-- ====================================================================\n\n"
    )

    for tbl in ["categories", "suppliers", "users", "products", "sales", "sales_items", "audit_log"]:
        full_sql += dump_table(tbl)

    out_path = PROJECT_ROOT / "database" / "pharmacy_complete.sql"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_sql)

    print(f"Generated complete SQL file at: {out_path}")
    print(f"File size: {len(full_sql):,} bytes")

if __name__ == "__main__":
    main()

