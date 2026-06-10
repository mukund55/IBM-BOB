# PostgreSQL Docker Commands - Step by Step

## Step 1: Start PostgreSQL Container

```powershell
docker run -d `
  --name postgres_dq_test `
  -e POSTGRES_USER=dquser `
  -e POSTGRES_PASSWORD=dqpass123 `
  -e POSTGRES_DB=dq_database `
  -p 5432:5432 `
  postgres:15-alpine
```

## Step 2: Wait for PostgreSQL to Start (10 seconds)

```powershell
Start-Sleep -Seconds 10
```

## Step 3: Copy SQL Script to Container

```powershell
docker cp setup_postgres_dq_test.sql postgres_dq_test:/tmp/setup.sql
```

## Step 4: Execute SQL Script

```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database -f /tmp/setup.sql
```

## Step 5: Verify Data - Connect to PostgreSQL

```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database
```

Once connected, run these SQL commands:

### Count Total Records
```sql
SELECT COUNT(*) FROM customer_data;
```

### View All Records
```sql
SELECT * FROM customer_data ORDER BY customer_id NULLS LAST;
```

### Check for Duplicates
```sql
SELECT customer_id, COUNT(*) AS duplicate_count
FROM customer_data
WHERE customer_id IS NOT NULL
GROUP BY customer_id
HAVING COUNT(*) > 1;
```

### Count NULL Values by Column
```sql
SELECT 
    'customer_id' AS column_name, COUNT(*) AS null_count FROM customer_data WHERE customer_id IS NULL
UNION ALL
SELECT 'customer_name', COUNT(*) FROM customer_data WHERE customer_name IS NULL
UNION ALL
SELECT 'email', COUNT(*) FROM customer_data WHERE email IS NULL
UNION ALL
SELECT 'age', COUNT(*) FROM customer_data WHERE age IS NULL
UNION ALL
SELECT 'salary', COUNT(*) FROM customer_data WHERE salary IS NULL
UNION ALL
SELECT 'join_date', COUNT(*) FROM customer_data WHERE join_date IS NULL
UNION ALL
SELECT 'country_code', COUNT(*) FROM customer_data WHERE country_code IS NULL
UNION ALL
SELECT 'status', COUNT(*) FROM customer_data WHERE status IS NULL;
```

### Exit psql
```sql
\q
```

## Step 6: Export Data to CSV

```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database -c "\copy customer_data TO '/tmp/customer_data_export.csv' WITH CSV HEADER"
docker cp postgres_dq_test:/tmp/customer_data_export.csv ./customer_data_export.csv
```

## Step 7: Run DQ Analysis

```powershell
python data_quality_analysis.py --input-file customer_data_export.csv --output-dir dq_output_postgres
```

---

## Alternative: Run All SQL Commands Directly (Without Entering psql)

### View all records
```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database -c "SELECT * FROM customer_data ORDER BY customer_id NULLS LAST;"
```

### Count records
```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database -c "SELECT COUNT(*) FROM customer_data;"
```

### Check duplicates
```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database -c "SELECT customer_id, COUNT(*) FROM customer_data WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(*) > 1;"
```

---

## Useful Management Commands

### Stop Container
```powershell
docker stop postgres_dq_test
```

### Start Container
```powershell
docker start postgres_dq_test
```

### Remove Container
```powershell
docker stop postgres_dq_test
docker rm postgres_dq_test
```

### View Container Logs
```powershell
docker logs postgres_dq_test
```

### Check Container Status
```powershell
docker ps -a | Select-String "postgres_dq_test"
```

---

## Complete One-Line Setup (All Steps Combined)

```powershell
docker run -d --name postgres_dq_test -e POSTGRES_USER=dquser -e POSTGRES_PASSWORD=dqpass123 -e POSTGRES_DB=dq_database -p 5432:5432 postgres:15-alpine; Start-Sleep -Seconds 10; docker cp setup_postgres_dq_test.sql postgres_dq_test:/tmp/setup.sql; docker exec -it postgres_dq_test psql -U dquser -d dq_database -f /tmp/setup.sql