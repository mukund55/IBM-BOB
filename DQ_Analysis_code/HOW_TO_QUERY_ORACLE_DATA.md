# How to Check Data from Customers Table in Docker

This guide shows you multiple ways to query and view data from the Oracle database running in Docker.

---

## Method 1: Using SQL Script (Recommended)

### Step 1: Copy the SQL file to container
```bash
docker cp DQ_Analysis_code/query_customers.sql oracle-xe:/tmp/
```

### Step 2: Execute the SQL script
```bash
docker exec oracle-xe bash -c "sqlplus -S dq_test/dq_test123@XEPDB1 @/tmp/query_customers.sql"
```

**Output:** Shows all 12 customer records with summary statistics

---

## Method 2: Interactive SQL*Plus Session

### Connect to SQL*Plus interactively
```bash
docker exec -it oracle-xe sqlplus dq_test/dq_test123@XEPDB1
```

### Once connected, run queries:
```sql
-- View all customers
SELECT * FROM customers ORDER BY customer_id;

-- Count records
SELECT COUNT(*) FROM customers;

-- Find records with issues
SELECT * FROM customers WHERE email IS NULL;
SELECT * FROM customers WHERE customer_name IS NULL;
SELECT * FROM customers WHERE purchase_amount < 0;

-- Exit SQL*Plus
EXIT;
```

---

## Method 3: Single Query from Command Line

### View all customers
```bash
docker exec oracle-xe bash -c "echo 'SELECT * FROM customers;' | sqlplus -S dq_test/dq_test123@XEPDB1"
```

### Count records
```bash
docker exec oracle-xe bash -c "echo 'SELECT COUNT(*) FROM customers;' | sqlplus -S dq_test/dq_test123@XEPDB1"
```

### Find NULL emails
```bash
docker exec oracle-xe bash -c "echo 'SELECT customer_id, customer_name, email FROM customers WHERE email IS NULL;' | sqlplus -S dq_test/dq_test123@XEPDB1"
```

---

## Method 4: Using Python Script

### Create a Python query script
```python
import oracledb

connection = oracledb.connect(
    user="dq_test",
    password="dq_test123",
    dsn="localhost:1521/XEPDB1"
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM customers ORDER BY customer_id")

print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Phone':<15} {'Country':<15}")
print("-" * 90)

for row in cursor:
    print(f"{row[0]:<5} {row[1] or 'NULL':<20} {row[2] or 'NULL':<30} {row[3] or 'NULL':<15} {row[4] or 'NULL':<15}")

cursor.close()
connection.close()
```

### Run the script
```bash
python your_query_script.py
```

---

## Method 5: Using Batch File (Windows)

### Create `query_oracle.bat`:
```batch
@echo off
docker exec oracle-xe bash -c "sqlplus -S dq_test/dq_test123@XEPDB1 @/tmp/query_customers.sql"
pause
```

### Run it:
```bash
query_oracle.bat
```

---

## Common Queries

### 1. View All Customers
```sql
SELECT customer_id, customer_name, email, phone, country, purchase_amount 
FROM customers 
ORDER BY customer_id;
```

### 2. Find Data Quality Issues

**NULL Emails:**
```sql
SELECT customer_id, customer_name, email 
FROM customers 
WHERE email IS NULL;
```

**NULL Names:**
```sql
SELECT customer_id, customer_name, email 
FROM customers 
WHERE customer_name IS NULL;
```

**Invalid Emails (no @ symbol):**
```sql
SELECT customer_id, customer_name, email 
FROM customers 
WHERE email NOT LIKE '%@%';
```

**Negative Purchase Amounts:**
```sql
SELECT customer_id, customer_name, purchase_amount 
FROM customers 
WHERE purchase_amount < 0;
```

**Outliers (very high amounts):**
```sql
SELECT customer_id, customer_name, purchase_amount 
FROM customers 
WHERE purchase_amount > 100000;
```

### 3. Summary Statistics
```sql
SELECT 
    COUNT(*) as total_records,
    COUNT(email) as records_with_email,
    COUNT(*) - COUNT(email) as records_without_email,
    COUNT(customer_name) as records_with_name,
    MIN(purchase_amount) as min_amount,
    MAX(purchase_amount) as max_amount,
    ROUND(AVG(purchase_amount), 2) as avg_amount
FROM customers;
```

### 4. Find Duplicates
```sql
SELECT customer_name, email, COUNT(*) as count
FROM customers
GROUP BY customer_name, email
HAVING COUNT(*) > 1;
```

### 5. Join with Orders
```sql
SELECT c.customer_id, c.customer_name, c.email, o.order_id, o.order_amount
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
ORDER BY c.customer_id;
```

---

## Current Data Overview

Based on the query results, here's what's in the database:

### Total Records: 12 customers

**Good Quality Records (5):**
1. John Doe - Complete data
2. Jane Smith - Complete data  
3. Bob Johnson - Complete data
4. David Lee - Missing country
5. Eve Martinez - Missing registration date

**Bad Quality Records (7):**
6. Alice Williams - Missing email
7. Charlie Brown - Invalid email, missing phone, negative amount (-100)
8. NULL name - Missing customer name
9. Frank Wilson - Invalid email, invalid is_active (2)
10. Grace Taylor - Outlier amount (999,999.99)
11. John Doe (duplicate)
12. Jane Smith (duplicate)

### Summary Statistics:
- Total Records: 12
- Records with Email: 11
- Records without Email: 1
- Records with Name: 11
- Min Amount: -100
- Max Amount: 999,999.99
- Avg Amount: 84,433.42

---

## Quick Reference Commands

### Check if container is running
```bash
docker ps | findstr oracle-xe
```

### View container logs
```bash
docker logs oracle-xe --tail 50
```

### Start/Stop container
```bash
docker start oracle-xe
docker stop oracle-xe
```

### Access container shell
```bash
docker exec -it oracle-xe bash
```

### Connect to SQL*Plus as SYSDBA
```bash
docker exec -it oracle-xe sqlplus sys/Oracle123@XEPDB1 as sysdba
```

---

## Troubleshooting

### Issue: "ORA-01017: invalid username/password"
**Solution:** Verify credentials:
- Username: dq_test
- Password: dq_test123
- Service: XEPDB1 (not XE!)

### Issue: "ORA-12154: TNS:could not resolve"
**Solution:** Use XEPDB1 as service name, not XE

### Issue: Container not responding
**Solution:** 
```bash
docker restart oracle-xe
# Wait 2-3 minutes for database to initialize
docker logs -f oracle-xe
```

### Issue: PowerShell syntax errors
**Solution:** Use bash inside container:
```bash
docker exec oracle-xe bash -c "your-command-here"
```

---

## Export Data to CSV

### Using SQL*Plus
```bash
docker exec oracle-xe bash -c "sqlplus -S dq_test/dq_test123@XEPDB1 << EOF
SET COLSEP ','
SET PAGESIZE 0
SET TRIMSPOOL ON
SET HEADSEP OFF
SET LINESIZE 1000
SPOOL /tmp/customers_export.csv
SELECT customer_id, customer_name, email, phone, country, purchase_amount FROM customers;
SPOOL OFF
EXIT;
EOF"

# Copy exported file from container
docker cp oracle-xe:/tmp/customers_export.csv ./customers_export.csv
```

### Using Python
```python
import oracledb
import pandas as pd

connection = oracledb.connect(
    user="dq_test",
    password="dq_test123",
    dsn="localhost:1521/XEPDB1"
)

df = pd.read_sql("SELECT * FROM customers", connection)
df.to_csv("customers_export.csv", index=False)
connection.close()
```

---

## Next Steps

1. **Explore the data** using the queries above
2. **Modify test data** to test different scenarios
3. **Run DQ analysis** after making changes
4. **Compare results** in the dashboard

---

*Last Updated: 2026-05-28*
*Oracle Container: oracle-xe*
*Database: XEPDB1*