# PostgreSQL Query Guide for Docker

## Quick Reference

### Check if Docker Container is Running
```bash
docker ps | findstr postgres-dq
```

### Connect to PostgreSQL Database
```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test
```

### Query Data (from Windows Command Prompt)
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT * FROM customer_data;"
```

### Query Data (from PowerShell)
```powershell
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT * FROM customer_data;"
```

## Common Queries

### Count Total Records
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT COUNT(*) FROM customer_data;"
```

### View First 5 Records
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT * FROM customer_data LIMIT 5;"
```

### View Good Records (Clean Data)
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT * FROM customer_data WHERE customer_id IN (1001.0, 1005.0, 1006.0, 1011.0, 1012.0);"
```

### View Bad Records (Data with Issues)
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT * FROM customer_data WHERE customer_id NOT IN (1001.0, 1005.0, 1006.0, 1011.0, 1012.0) OR customer_id IS NULL;"
```

### Check for NULL Values
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT customer_id, customer_name, email FROM customer_data WHERE customer_name IS NULL OR email IS NULL;"
```

### Check for Duplicates
```bash
docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT customer_id, COUNT(*) FROM customer_data WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(*) > 1;"
```

## Interactive Mode

To enter interactive PostgreSQL shell:

```bash
docker exec -it postgres-dq psql -U dq_user -d dq_test
```

Once inside, you can run queries directly:
```sql
SELECT * FROM customer_data;
\q  -- to quit
```

## Current Database Status

- **Container Name**: postgres-dq
- **Database**: dq_test
- **User**: dq_user
- **Password**: postgres123
- **Port**: 5432
- **Table**: customer_data
- **Total Records**: 14
  - Good Records: 5
  - Bad Records: 9

## Troubleshooting

### If you can't see data:

1. **Check if container is running:**
   ```bash
   docker ps
   ```

2. **Check if you're in the right database:**
   ```bash
   docker exec postgres-dq psql -U dq_user -d dq_test -c "\dt"
   ```

3. **Verify table exists:**
   ```bash
   docker exec postgres-dq psql -U dq_user -d dq_test -c "\d customer_data"
   ```

4. **Count records:**
   ```bash
   docker exec postgres-dq psql -U dq_user -d dq_test -c "SELECT COUNT(*) FROM customer_data;"
   ```

### If container is not running:

```bash
docker start postgres-dq
```

### To restart container:

```bash
docker restart postgres-dq
```

## Connection String for Python/DQ Analysis

```
postgresql://dq_user:postgres123@localhost:5432/dq_test
```

## Notes

- The DQ analysis script successfully reads from this database
- All 14 records are present and accessible
- The quality score calculation is working correctly (35.71%)
- Good records are properly identified and exported