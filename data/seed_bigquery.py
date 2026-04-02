"""
Run this ONCE to seed your BigQuery dataset.
Usage: python data/seed_bigquery.py --project YOUR_GCP_PROJECT_ID
"""
import argparse
from google.cloud import bigquery

parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
args = parser.parse_args()

client = bigquery.Client(project=args.project)
dataset_id = f"{args.project}.inventory_db"

# Create dataset
client.create_dataset(bigquery.Dataset(dataset_id), exists_ok=True)
print(f"✅ Dataset {dataset_id} ready")

# ── raw_materials ──────────────────────────────────────────────────────────────
client.query(f"""
CREATE OR REPLACE TABLE `{dataset_id}.raw_materials` AS
SELECT * FROM UNNEST([
  STRUCT('RM001' AS material_id, 'Steel Sheets'       AS name, 'Metals'     AS category, 'kg'   AS unit, 1200.0 AS current_stock, 500.0  AS reorder_level, 3000.0 AS max_stock, 85.50  AS unit_cost, 'SUP001' AS supplier_id, 'Warehouse A' AS warehouse),
  STRUCT('RM002',                'Aluminium Rods',              'Metals',                 'kg',           340.0,                   400.0,                2000.0,               120.00,              'SUP002',              'Warehouse A'),
  STRUCT('RM003',                'Copper Wire',                 'Metals',                 'kg',           890.0,                   300.0,                1500.0,               450.00,              'SUP002',              'Warehouse B'),
  STRUCT('RM004',                'PVC Granules',                'Polymers',               'kg',           150.0,                   500.0,                2500.0,               35.00,               'SUP003',              'Warehouse B'),
  STRUCT('RM005',                'Rubber Compound',             'Polymers',               'kg',           60.0,                    200.0,                1000.0,               78.00,               'SUP003',              'Warehouse C'),
  STRUCT('RM006',                'Hydraulic Oil',               'Fluids',                 'litre',        2200.0,                  1000.0,               5000.0,               42.00,               'SUP004',              'Warehouse C'),
  STRUCT('RM007',                'Welding Electrodes',          'Consumables',            'box',          45.0,                    100.0,                500.0,                320.00,              'SUP005',              'Warehouse A'),
  STRUCT('RM008',                'Epoxy Resin',                 'Chemicals',              'kg',           30.0,                    150.0,                600.0,                890.00,              'SUP005',              'Warehouse B'),
  STRUCT('RM009',                'Carbon Fibre',                'Composites',             'kg',           500.0,                   200.0,                1200.0,               2100.00,             'SUP006',              'Warehouse A'),
  STRUCT('RM010',                'Titanium Bolts',              'Fasteners',              'pcs',          12000.0,                 5000.0,               50000.0,              8.50,                'SUP006',              'Warehouse C')
])
""").result()
print("✅ raw_materials seeded")

# ── suppliers ──────────────────────────────────────────────────────────────────
client.query(f"""
CREATE OR REPLACE TABLE `{dataset_id}.suppliers` AS
SELECT * FROM UNNEST([
  STRUCT('SUP001' AS supplier_id, 'Tata Steel Ltd'          AS name, 'Mumbai'    AS city, 4.8 AS rating, 7  AS avg_lead_days, TRUE  AS is_active),
  STRUCT('SUP002',                'Hindalco Industries',              'Pune',              4.5,            10,                 TRUE),
  STRUCT('SUP003',                'Reliance Polymers',                'Surat',             4.2,            14,                 TRUE),
  STRUCT('SUP004',                'Castrol India',                    'Bengaluru',         4.7,            5,                  TRUE),
  STRUCT('SUP005',                'Lincoln Electric India',           'Chennai',           3.9,            21,                 TRUE),
  STRUCT('SUP006',                'Toray Composites India',           'Hyderabad',         4.6,            30,                 FALSE)
])
""").result()
print("✅ suppliers seeded")

# ── purchase_orders ────────────────────────────────────────────────────────────
client.query(f"""
CREATE OR REPLACE TABLE `{dataset_id}.purchase_orders` AS
SELECT * FROM UNNEST([
  STRUCT('PO-2026-001' AS po_id, 'RM002' AS material_id, 'SUP002' AS supplier_id, DATE '2026-03-15' AS order_date, DATE '2026-03-25' AS expected_date, DATE '2026-03-28' AS actual_delivery, 500.0 AS qty_ordered, 500.0 AS qty_received, 'Delivered' AS status),
  STRUCT('PO-2026-002',          'RM004',                'SUP003',                DATE '2026-03-20',               DATE '2026-04-03',                NULL,                              800.0,               0.0,               'Pending'),
  STRUCT('PO-2026-003',          'RM005',                'SUP003',                DATE '2026-03-22',               DATE '2026-04-05',                NULL,                              400.0,               0.0,               'In Transit'),
  STRUCT('PO-2026-004',          'RM007',                'SUP005',                DATE '2026-03-10',               DATE '2026-03-31',                DATE '2026-04-10',                 200.0,               200.0,             'Delayed'),
  STRUCT('PO-2026-005',          'RM008',                'SUP005',                DATE '2026-03-28',               DATE '2026-04-18',                NULL,                              100.0,               0.0,               'Pending'),
  STRUCT('PO-2026-006',          'RM001',                'SUP001',                DATE '2026-04-01',               DATE '2026-04-08',                NULL,                              2000.0,              0.0,               'Pending')
])
""").result()
print("✅ purchase_orders seeded")

# ── consumption_log ────────────────────────────────────────────────────────────
client.query(f"""
CREATE OR REPLACE TABLE `{dataset_id}.consumption_log` AS
SELECT * FROM UNNEST([
  STRUCT(DATE '2026-03-25' AS log_date, 'RM001' AS material_id, 'Production Line A' AS department, 120.0 AS qty_consumed),
  STRUCT(DATE '2026-03-26', 'RM001', 'Production Line B', 95.0),
  STRUCT(DATE '2026-03-27', 'RM001', 'Production Line A', 110.0),
  STRUCT(DATE '2026-03-28', 'RM003', 'Production Line A', 45.0),
  STRUCT(DATE '2026-03-29', 'RM003', 'Production Line C', 60.0),
  STRUCT(DATE '2026-03-30', 'RM006', 'Maintenance',        180.0),
  STRUCT(DATE '2026-03-31', 'RM006', 'Production Line B',  220.0),
  STRUCT(DATE '2026-04-01', 'RM002', 'Production Line A',  80.0),
  STRUCT(DATE '2026-04-01', 'RM007', 'Welding Shop',       12.0),
  STRUCT(DATE '2026-04-01', 'RM009', 'Production Line C',  25.0)
])
""").result()
print("✅ consumption_log seeded")

print("\n🎉 All tables seeded! Your BigQuery dataset is ready.")
print(f"   Project : {args.project}")
print(f"   Dataset : inventory_db")
print(f"   Tables  : raw_materials, suppliers, purchase_orders, consumption_log")
