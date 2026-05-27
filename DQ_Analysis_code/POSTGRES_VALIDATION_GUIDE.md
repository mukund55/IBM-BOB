# PostgreSQL Database Validation Guide

## Quick Validation Commands

### 1. Check if Docker Container is Running
```bash
docker ps
```
**Expected Output:** You should see `postgres-dq` container with status "Up"

### 2. Check Container Logs
```bash
docker logs postgres-dq
```
**Look for:** "database system is ready to accept connections"

### 3. Connect to PostgreSQL Database
```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test
```

### 4. View Data in Database (from psql prompt)
```sql
-- List all tables
\dt

-- View table structure
\d customers

-- Count records
SELECT COUNT(*) FROM customers;

-- View all data
SELECT * FROM customers;

-- View data with quality issues
SELECT 
    customer_id,
    customer_name,
    email,
    CASE 
        WHEN email IS NULL THEN 'NULL email'
        WHEN email NOT LIKE '%@%' THEN 'Invalid email'
        ELSE 'Valid'
    END as email_status,
    purchase_amount,
    CASE 
        WHEN purchase_amount < 0 THEN 'Negative amount'
        WHEN purchase_amount > 100000 THEN 'Outlier'
        ELSE 'Normal'
    END as amount_status
FROM customers;

-- Exit psql
\q
```

## Validation Checklist

### ✅ Step 1: Verify Docker Container
```bash
docker ps -a | findstr postgres-dq
```
**Status should be:** "Up X minutes"

### ✅ Step 2: Test Database Connection
```bash
cd DQ_Analysis_code
python test_database_integration.py
```
**Expected:** `[OK] Connected successfully!`

### ✅ Step 3: Verify Test Data
```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test -c "SELECT COUNT(*) FROM customers;"
```
**Expected:** `6` (or the number of test records)

### ✅ Step 4: View Sample Data
```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test -c "SELECT customer_id, customer_name, email, purchase_amount FROM customers LIMIT 3;"
```

### ✅ Step 5: Run DQ Analysis
```bash
python data_quality_analysis.py --use-database --config-file dq_config_postgres.json --generate-dashboard
```
**Expected:** Dashboard created in `dq_output_postgres/`

## Common Issues and Solutions

### Issue 1: Container Not Running
```bash
docker start postgres-dq
```

### Issue 2: Connection Refused
**Wait 10-15 seconds** after starting container, then retry.

### Issue 3: No Data in Table
**Re-insert data:**
```bash
docker exec -i postgres-dq psql -U dq_user -d dq_test -f /tmp/setup_postgres_data.sql
```

### Issue 4: Duplicate Key Error
**Clear and re-insert:**
```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test -c "TRUNCATE TABLE customers;"
docker exec -i postgres-dq psql -U dq_user -d dq_test -f /tmp/setup_postgres_data.sql
```

## Manual Data Insertion (if needed)

```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test
```

Then run:
```sql
-- Clear existing data
TRUNCATE TABLE customers;

-- Insert test data
INSERT INTO customers (customer_id, customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) VALUES
(1, 'John Doe', 'john@example.com', '555-0001', '2024-01-15', 1500.00, 1, 'US'),
(2, 'Jane Smith', 'jane@example.com', '555-0002', '2024-02-20', 2500.50, 1, 'UK'),
(3, 'Bob Johnson', NULL, '555-0003', '2024-03-10', -100.00, 1, 'CA'),
(4, 'Alice Brown', 'invalid-email', NULL, '2024-04-05', 3500.00, 2, 'AU'),
(5, 'Charlie Wilson', 'charlie@test.com', '555-0005', NULL, 999999.99, 1, 'IN'),
(6, 'Duplicate John', 'john2@example.com', '555-0006', '2024-05-01', 1200.00, 1, 'US');

-- Verify
SELECT COUNT(*) FROM customers;
SELECT * FROM customers;
```

## Python Script Validation

### Test 1: Database Connection
```python
from sqlalchemy import create_engine
import pandas as pd

# Create connection
engine = create_engine('postgresql://dq_user:postgres123@localhost:5432/dq_test')

# Test query
df = pd.read_sql("SELECT * FROM customers", engine)
print(f"Records loaded: {len(df)}")
print(df.head())
```

### Test 2: Run DQ Analysis
```bash
python data_quality_analysis.py --use-database --config-file dq_config_postgres.json --generate-dashboard --cleanse-data
```

### Test 3: Check Output Files
```bash
dir dq_output_postgres
```
**Expected files:**
- `dq_executive_dashboard.html`
- `cleansed_data.csv`
- `dq_summary.csv`
- `dq_all_bad_records.csv`

## View Dashboard
```bash
start dq_output_postgres\dq_executive_dashboard.html
```

## Stop/Start PostgreSQL

### Stop Container
```bash
docker stop postgres-dq
```

### Start Container
```bash
docker start postgres-dq
```

### Remove Container (to start fresh)
```bash
docker stop postgres-dq
docker rm postgres-dq
```

Then run `setup_postgres_test.bat` again.

## Database Credentials

- **Host:** localhost
- **Port:** 5432
- **Database:** dq_test
- **Username:** dq_user
- **Password:** postgres123

## Connection String
```
postgresql://dq_user:postgres123@localhost:5432/dq_test