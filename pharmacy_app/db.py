import logging
import mysql.connector
from mysql.connector import errorcode
import bcrypt
from datetime import datetime, date, timedelta
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT, DATABASE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def get_connection(use_database=True):
    """Establishes and returns a connection to MySQL."""
    kwargs = {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT,
        "autocommit": False
    }
    if use_database:
        kwargs["database"] = DB_NAME

    try:
        conn = mysql.connector.connect(**kwargs)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"MySQL Connection Error: {err}")
        raise err

def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Executes a parameterized SQL query safely.
    Returns:
        - dict / None for fetchone
        - list of dicts for fetchall
        - lastrowid for INSERT with commit
        - rowcount for UPDATE/DELETE with commit
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if commit:
            conn.commit()
            return cursor.lastrowid or cursor.rowcount

        if fetchone:
            return cursor.fetchone()

        if fetchall:
            return cursor.fetchall()

        return None
    except mysql.connector.Error as err:
        if conn and commit:
            conn.rollback()
        logger.error(f"SQL Execution Error: {err} | Query: {query} | Params: {params}")
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_many(query, seq_of_params, commit=True):
    """Executes a query for multiple parameter sets."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, seq_of_params)
        if commit:
            conn.commit()
            return cursor.rowcount
        return None
    except mysql.connector.Error as err:
        if conn and commit:
            conn.rollback()
        logger.error(f"SQL Batch Execution Error: {err}")
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def init_database():
    """Initializes the database schema and seeds initial data if missing."""
    logger.info("Initializing database...")
    # Step 1: Ensure database exists
    conn_root = get_connection(use_database=False)
    cursor_root = conn_root.cursor()
    cursor_root.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor_root.close()
    conn_root.close()

    # Step 2: Read and execute schema.sql
    schema_path = DATABASE_DIR / "schema.sql"
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        conn = get_connection(use_database=True)
        cursor = conn.cursor()
        # Execute each statement separated by semicolon
        for statement in sql_script.split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Schema tables confirmed/created successfully.")

    # Step 3: Seed initial data
    seed_users()
    seed_categories()
    seed_suppliers()
    seed_products()
    seed_sample_sales()
    logger.info("Database initialization and seed verification complete.")

def hash_pw(plain_text):
    return bcrypt.hashpw(plain_text.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def seed_users():
    """Seeds default accounts if users table is empty."""
    user_count = execute_query("SELECT COUNT(*) AS cnt FROM users", fetchone=True)["cnt"]
    if user_count > 0:
        return

    logger.info("Seeding default user accounts...")
    default_users = [
        ("admin", hash_pw("admin123"), "System Administrator", "admin@pharmacare.local", "admin"),
        ("inventory_clerk", hash_pw("clerk123"), "Lebron James", "clerk@pharmacare.local", "inventory_clerk"),
        ("sales_personnel", hash_pw("sales123"), "Steph Curry", "sales@pharmacare.local", "sales_personnel"),
        ("instructor", hash_pw("instructor123"), "Prof. Norris Alexis Amora", "instructor@pharmacare.local", "instructor")
    ]
    query = """
        INSERT INTO users (username, password_hash, full_name, email, role)
        VALUES (%s, %s, %s, %s, %s)
    """
    execute_many(query, default_users)
    logger.info("Default user accounts seeded successfully.")

def seed_categories():
    cat_count = execute_query("SELECT COUNT(*) AS cnt FROM categories", fetchone=True)["cnt"]
    if cat_count > 0:
        return

    logger.info("Seeding categories...")
    categories = [
        ("Analgesics & Antipyretics", "Pain relief and fever reducers"),
        ("Antibiotics & Antivirals", "Prescription antibacterial and antimicrobial agents"),
        ("Antihistamines & Allergy", "Allergy relief and sinus decongestants"),
        ("Cardiovascular & Hypertension", "Heart, blood pressure and lipid regulators"),
        ("Vitamins & Supplements", "Dietary supplements, multivitamins and minerals"),
        ("Gastrointestinal & Digestive", "Antacids, proton-pump inhibitors, and laxatives"),
        ("Respiratory & Cough Care", "Bronchodilators, expectorants, and cough syrups"),
        ("Topical & First Aid", "Antiseptics, wound ointments, and skin treatments")
    ]
    query = "INSERT INTO categories (name, description) VALUES (%s, %s)"
    execute_many(query, categories)

def seed_suppliers():
    sup_count = execute_query("SELECT COUNT(*) AS cnt FROM suppliers", fetchone=True)["cnt"]
    if sup_count > 0:
        return

    logger.info("Seeding suppliers...")
    suppliers = [
        ("Pfizer Direct Logistics", "Mark Sterling", "+1-800-555-0199", "orders@pfizerlogistics.com", "45 Pharma Parkway, New York, NY"),
        ("Novartis Wholesale Distribution", "Elena Rostova", "+1-800-555-0210", "dist@novartis-supply.com", "88 Health Ave, Cambridge, MA"),
        ("Sanofi Healthcare Supply", "Carlos Mendez", "+1-800-555-0322", "supply@sanofi-care.com", "12 Bio Way, Bridgewater, NJ"),
        ("GSK Global Therapeutics", "Sarah Jenkins", "+1-800-555-0455", "commercial@gsk-supply.com", "200 Discovery Blvd, Philadelphia, PA"),
        ("Astra BioMed Supply Co.", "David Lee", "+1-800-555-0567", "orders@astrabio.com", "10 Science Rd, Gaithersburg, MD"),
        ("Metro Local Pharma Warehouse", "Liza Reyes", "+1-800-555-0789", "sales@metrolocalmed.com", "300 Industrial Loop, Chicago, IL")
    ]
    query = "INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES (%s, %s, %s, %s, %s)"
    execute_many(query, suppliers)

def seed_products():
    prod_count = execute_query("SELECT COUNT(*) AS cnt FROM products", fetchone=True)["cnt"]
    if prod_count > 0:
        return

    logger.info("Seeding 55 realistic pharmacy products...")
    # Fetch category & supplier IDs
    cats = {c["name"]: c["id"] for c in execute_query("SELECT id, name FROM categories", fetchall=True)}
    sups = {s["name"]: s["id"] for s in execute_query("SELECT id, name FROM suppliers", fetchall=True)}

    c_analgesic = cats.get("Analgesics & Antipyretics", 1)
    c_antibiotic = cats.get("Antibiotics & Antivirals", 2)
    c_allergy = cats.get("Antihistamines & Allergy", 3)
    c_cardio = cats.get("Cardiovascular & Hypertension", 4)
    c_vitamins = cats.get("Vitamins & Supplements", 5)
    c_gastro = cats.get("Gastrointestinal & Digestive", 6)
    c_resp = cats.get("Respiratory & Cough Care", 7)
    c_topical = cats.get("Topical & First Aid", 8)

    s_pfizer = sups.get("Pfizer Direct Logistics", 1)
    s_novartis = sups.get("Novartis Wholesale Distribution", 2)
    s_sanofi = sups.get("Sanofi Healthcare Supply", 3)
    s_gsk = sups.get("GSK Global Therapeutics", 4)
    s_astra = sups.get("Astra BioMed Supply Co.", 5)
    s_metro = sups.get("Metro Local Pharma Warehouse", 6)

    today = date.today()

    # 55 Realistic pharmacy products with varied stock and expiry
    products_data = [
        # Analgesics
        ("SKU-1001", "Paracetamol 500mg Tablet", c_analgesic, s_metro, 0.15, 0.50, 450, 50, today + timedelta(days=500), "strip"),
        ("SKU-1002", "Paracetamol 120mg/5ml Syrup 60ml", c_analgesic, s_metro, 1.20, 3.25, 65, 15, today + timedelta(days=400), "bottle"),
        ("SKU-1003", "Ibuprofen 400mg Softgel", c_analgesic, s_pfizer, 0.35, 1.10, 220, 30, today + timedelta(days=620), "box"),
        ("SKU-1004", "Ibuprofen 200mg Tablet", c_analgesic, s_pfizer, 0.20, 0.75, 180, 25, today + timedelta(days=360), "strip"),
        ("SKU-1005", "Aspirin 81mg Low Dose", c_analgesic, s_novartis, 0.18, 0.65, 310, 40, today + timedelta(days=450), "bottle"),
        ("SKU-1006", "Mefenamic Acid 500mg Capsule", c_analgesic, s_gsk, 0.40, 1.25, 95, 20, today + timedelta(days=520), "strip"),
        ("SKU-1007", "Tramadol 50mg Capsule (Rx)", c_analgesic, s_sanofi, 0.85, 2.75, 8, 15, today + timedelta(days=320), "box"), # low stock
        ("SKU-1008", "Naproxen Sodium 550mg Tablet", c_analgesic, s_astra, 0.50, 1.60, 140, 25, today + timedelta(days=600), "strip"),

        # Antibiotics & Antivirals
        ("SKU-2001", "Amoxicillin 500mg Capsule", c_antibiotic, s_gsk, 0.30, 0.95, 380, 40, today + timedelta(days=480), "box"),
        ("SKU-2002", "Amoxicillin + Clavulanate 625mg", c_antibiotic, s_gsk, 1.20, 3.50, 85, 20, today + timedelta(days=420), "box"),
        ("SKU-2003", "Azithromycin 500mg Tablet", c_antibiotic, s_pfizer, 1.80, 5.00, 60, 15, today + timedelta(days=300), "box"),
        ("SKU-2004", "Ciprofloxacin 500mg Tablet", c_antibiotic, s_novartis, 0.70, 2.10, 110, 20, today + timedelta(days=540), "strip"),
        ("SKU-2005", "Cephalexin 500mg Capsule", c_antibiotic, s_sanofi, 0.45, 1.40, 90, 20, today + timedelta(days=390), "box"),
        ("SKU-2006", "Doxycycline 100mg Capsule", c_antibiotic, s_astra, 0.55, 1.75, 75, 15, today + timedelta(days=450), "strip"),
        ("SKU-2007", "Acyclovir 400mg Tablet", c_antibiotic, s_gsk, 0.90, 2.80, 12, 15, today + timedelta(days=70), "box"), # near expiry & low stock
        ("SKU-2008", "Levofloxacin 500mg Tablet", c_antibiotic, s_sanofi, 1.50, 4.25, 45, 10, today + timedelta(days=410), "strip"),

        # Antihistamines & Allergy
        ("SKU-3001", "Cetirizine 10mg Tablet", c_allergy, s_metro, 0.15, 0.60, 500, 50, today + timedelta(days=650), "strip"),
        ("SKU-3002", "Loratadine 10mg Tablet", c_allergy, s_metro, 0.20, 0.70, 320, 40, today + timedelta(days=580), "strip"),
        ("SKU-3003", "Fexofenadine 180mg Tablet", c_allergy, s_sanofi, 1.10, 3.20, 80, 15, today + timedelta(days=500), "box"),
        ("SKU-3004", "Diphenhydramine 25mg Capsule", c_allergy, s_pfizer, 0.25, 0.85, 190, 30, today + timedelta(days=350), "bottle"),
        ("SKU-3005", "Chlorpheniramine Maleate 4mg", c_allergy, s_metro, 0.08, 0.35, 420, 50, today + timedelta(days=720), "strip"),
        ("SKU-3006", "Fluticasone Nasal Spray 50mcg", c_allergy, s_gsk, 5.50, 14.50, 40, 10, today + timedelta(days=480), "bottle"),

        # Cardiovascular & Hypertension
        ("SKU-4001", "Amlodipine 5mg Tablet", c_cardio, s_pfizer, 0.22, 0.75, 400, 50, today + timedelta(days=590), "strip"),
        ("SKU-4002", "Amlodipine 10mg Tablet", c_cardio, s_pfizer, 0.35, 1.15, 250, 35, today + timedelta(days=540), "strip"),
        ("SKU-4003", "Losartan Potassium 50mg", c_cardio, s_novartis, 0.30, 0.95, 380, 40, today + timedelta(days=600), "strip"),
        ("SKU-4004", "Losartan + HCTZ 50mg/12.5mg", c_cardio, s_novartis, 0.55, 1.65, 160, 25, today + timedelta(days=480), "strip"),
        ("SKU-4005", "Atorvastatin 20mg Tablet", c_cardio, s_pfizer, 0.60, 1.90, 290, 35, today + timedelta(days=530), "box"),
        ("SKU-4006", "Atorvastatin 40mg Tablet", c_cardio, s_pfizer, 0.95, 2.85, 130, 20, today + timedelta(days=490), "box"),
        ("SKU-4007", "Rosuvastatin 10mg Tablet", c_cardio, s_astra, 0.75, 2.30, 175, 25, today + timedelta(days=510), "strip"),
        ("SKU-4008", "Metoprolol Tartrate 50mg", c_cardio, s_novartis, 0.28, 0.85, 210, 30, today + timedelta(days=440), "strip"),
        ("SKU-4009", "Clopidogrel 75mg Tablet", c_cardio, s_sanofi, 0.80, 2.45, 140, 20, today + timedelta(days=460), "box"),

        # Vitamins & Supplements
        ("SKU-5001", "Vitamin C 500mg Ascorbic Acid", c_vitamins, s_metro, 0.12, 0.45, 600, 60, today + timedelta(days=680), "bottle"),
        ("SKU-5002", "Vitamin C + Zinc Non-Acidic Capsule", c_vitamins, s_metro, 0.28, 0.90, 450, 50, today + timedelta(days=560), "box"),
        ("SKU-5003", "Vitamin D3 1000 IU Softgel", c_vitamins, s_novartis, 0.30, 0.95, 310, 40, today + timedelta(days=610), "bottle"),
        ("SKU-5004", "Vitamin B-Complex Tablet", c_vitamins, s_metro, 0.18, 0.60, 390, 45, today + timedelta(days=630), "bottle"),
        ("SKU-5005", "Multivitamins with Iron Capsule", c_vitamins, s_gsk, 0.25, 0.80, 280, 35, today + timedelta(days=540), "box"),
        ("SKU-5006", "Calcium Carbonate + Vit D3", c_vitamins, s_gsk, 0.32, 1.05, 190, 25, today + timedelta(days=580), "bottle"),
        ("SKU-5007", "Fish Oil Omega-3 1000mg Softgel", c_vitamins, s_pfizer, 0.45, 1.50, 160, 20, today + timedelta(days=520), "bottle"),
        ("SKU-5008", "Zinc Gluconate 50mg Tablet", c_vitamins, s_metro, 0.16, 0.55, 240, 30, today + timedelta(days=600), "bottle"),

        # Gastrointestinal & Digestive
        ("SKU-6001", "Omeprazole 20mg Capsule", c_gastro, s_astra, 0.35, 1.15, 350, 40, today + timedelta(days=510), "strip"),
        ("SKU-6002", "Esomeprazole 40mg Tablet", c_gastro, s_astra, 1.10, 3.40, 95, 15, today + timedelta(days=460), "box"),
        ("SKU-6003", "Antacid Chewable Tablet", c_gastro, s_metro, 0.15, 0.50, 280, 30, today + timedelta(days=580), "strip"),
        ("SKU-6004", "Loperamide 2mg Capsule", c_gastro, s_sanofi, 0.18, 0.65, 330, 35, today + timedelta(days=620), "strip"),
        ("SKU-6005", "Oral Rehydration Salts (ORS) Sachet", c_gastro, s_metro, 0.20, 0.75, 410, 50, today + timedelta(days=700), "sachet"),
        ("SKU-6006", "Bisacodyl 5mg Laxative Tablet", c_gastro, s_sanofi, 0.22, 0.70, 110, 15, today + timedelta(days=480), "strip"),
        ("SKU-6007", "Hyoscine-N-Butylbromide 10mg", c_gastro, s_sanofi, 0.40, 1.30, 9, 15, today + timedelta(days=55), "strip"), # near expiry & low stock

        # Respiratory & Cough Care
        ("SKU-7001", "Salbutamol 2mg Tablet", c_resp, s_gsk, 0.14, 0.50, 270, 30, today + timedelta(days=570), "strip"),
        ("SKU-7002", "Salbutamol Inhaler 100mcg", c_resp, s_gsk, 4.20, 11.50, 55, 15, today + timedelta(days=630), "canister"),
        ("SKU-7003", "Dextromethorphan HBr Syrup 60ml", c_resp, s_metro, 1.40, 3.80, 85, 20, today + timedelta(days=430), "bottle"),
        ("SKU-7004", "Guaifenesin 100mg/5ml Expectorant", c_resp, s_metro, 1.30, 3.60, 90, 20, today + timedelta(days=440), "bottle"),
        ("SKU-7005", "Carbocisteine 500mg Capsule", c_resp, s_metro, 0.32, 0.95, 340, 40, today + timedelta(days=530), "box"),
        ("SKU-7006", "Montelukast 10mg Tablet", c_resp, s_novartis, 0.85, 2.65, 120, 20, today + timedelta(days=490), "box"),

        # Topical & First Aid
        ("SKU-8001", "Povidone Iodine 10% Solution 60ml", c_topical, s_metro, 1.60, 4.25, 75, 15, today + timedelta(days=590), "bottle"),
        ("SKU-8002", "Hydrocortisone 1% Cream 15g", c_topical, s_pfizer, 2.10, 5.80, 60, 15, today + timedelta(days=450), "tube"),
        ("SKU-8003", "Silver Sulfadiazine 1% Burn Cream 20g", c_topical, s_novartis, 2.80, 7.50, 7, 10, today + timedelta(days=40), "tube"), # low stock & near expiry
        ("SKU-8004", "Alcohol 70% Isopropyl 500ml", c_topical, s_metro, 0.90, 2.50, 180, 25, today + timedelta(days=800), "bottle"),
        ("SKU-8005", "Sterile Gauze Pad 4x4 (Pack of 10)", c_topical, s_metro, 0.70, 2.00, 150, 20, today + timedelta(days=900), "pack")
    ]

    query = """
        INSERT INTO products 
        (sku, name, category_id, supplier_id, cost_price, selling_price, stock_qty, reorder_level, expiry_date, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_many(query, products_data)
    logger.info("55 pharmacy products seeded successfully.")

def seed_sample_sales():
    """Seeds a small set of historical sales so dashboard charts and KPIs display immediately."""
    sale_count = execute_query("SELECT COUNT(*) AS cnt FROM sales", fetchone=True)["cnt"]
    if sale_count > 0:
        return

    logger.info("Seeding initial sales records for dashboard visualizations...")
    admin_user = execute_query("SELECT id FROM users WHERE username='admin'", fetchone=True)
    if not admin_user:
        return
    user_id = admin_user["id"]

    prods = execute_query("SELECT id, cost_price, selling_price FROM products LIMIT 10", fetchall=True)
    if not prods:
        return

    import random
    random.seed(42)

    today = datetime.now()
    sales_created = 0

    for day_offset in range(14, -1, -1):
        sale_date = today - timedelta(days=day_offset, hours=random.randint(1, 8))
        num_sales_today = random.randint(3, 7)
        for s_idx in range(num_sales_today):
            invoice_no = f"INV-{sale_date.strftime('%Y%m%d')}-{sales_created+1:04d}"
            # Pick 1-3 products
            chosen = random.sample(prods, k=random.randint(1, 3))
            subtotal = 0.0
            items_to_add = []
            for p in chosen:
                qty = random.randint(1, 4)
                line_total = float(p["selling_price"]) * qty
                subtotal += line_total
                items_to_add.append((p["id"], qty, p["selling_price"], p["cost_price"], line_total))

            total = round(subtotal, 2)
            paid = round(total + random.choice([0, 5, 10, 20]), 2)
            change = round(paid - total, 2)

            sale_id = execute_query("""
                INSERT INTO sales (invoice_no, user_id, subtotal, total_amount, payment_method, amount_paid, change_amount, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (invoice_no, user_id, total, total, "CASH", paid, change, sale_date), commit=True)

            for item in items_to_add:
                execute_query("""
                    INSERT INTO sales_items (sale_id, product_id, quantity, unit_price, unit_cost, line_total)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (sale_id, item[0], item[1], item[2], item[3], item[4]), commit=True)

            sales_created += 1

    logger.info(f"Seeded {sales_created} realistic sales across 14 days.")

