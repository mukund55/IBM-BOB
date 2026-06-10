# PostgreSQL Docker Setup for Data Quality Testing

This guide will help you set up a PostgreSQL database in Docker with sample data for DQ analysis.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Start PostgreSQL Container

Open PowerShell or Command Prompt in the `DQ_Analysis_code` directory and run:

```powershell
docker-compose -f docker-compose-postgres.yml up -d
```

This will:
- Pull PostgreSQL 15 Alpine image
- Create a container named `postgres_dq_test`
- Create database `dq_database` with user `dquser`
- Automatically execute `setup_postgres_dq_test.sql` to create table and insert data
- Expose PostgreSQL on port 5432

### 2. Verify Container is Running

```powershell
docker ps
```

You should see `postgres_dq_test` container running.

### 3. Check Container Logs

```powershell
docker logs postgres_dq_test
```

Look for messages indicating successful database initialization.

## Database Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: dq_database
- **Username**: dquser
- **Password**: dqpass123

## Connecting to PostgreSQL

### Option 1: Using psql (Command Line)

```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database
```

### Option 2: Using pgAdmin or DBeaver

Create a new connection with the details above.

### Option 3: Using Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="dq_database",
    user="dquser",
    password="dqpass123"
)
```

## Verify Data

Once connected, run these queries:

```sql
-- Count total records
SELECT COUNT(*) FROM customer_data;

-- View all records
SELECT * FROM customer_data ORDER BY customer_id NULLS LAST;

-- Check for duplicates
SELECT customer_id, COUNT(*) 
FROM customer_data 
WHERE customer_id IS NOT NULL
GROUP BY customer_id 
HAVING COUNT(*) > 1;
```

## Data Summary

The `customer_data` table contains:
- **5 good records** (clean data)
- **9 bad records** (various data quality issues)

### Good Records
- 1001.0 - John Doe
- 1005.0 - Emma Wilson
- 1006.0 - Robert Brown
- 1011.0 - Lisa Anderson
- 1012.0 - James Taylor

### Bad Records with Issues
- **1002.0** - Invalid email, negative age
- **1003.0** - Multiple NULL values
- **1004.0** - Duplicate ID (2 records), age out of range, negative salary
- **NULL** - Missing customer_id, invalid country code
- **1007.0** - Missing name, invalid email
- **1008.0** - Missing email, salary outlier (9.5M)
- **1009.0** - Invalid country code, invalid status
- **1010.0** - NULL salary, missing join_date

## Export Data to CSV for DQ Analysis

### Method 1: Using psql

```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database -c "\copy customer_data TO '/tmp/customer_data_export.csv' WITH CSV HEADER"
docker cp postgres_dq_test:/tmp/customer_data_export.csv ./customer_data_export.csv
```

### Method 2: Using Python Script

Create a file `export_postgres_data.py`:

```python
import psycopg2
import csv

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="dq_database",
    user="dquser",
    password="dqpass123"
)

# Export to CSV
with conn.cursor() as cur:
    cur.execute("SELECT * FROM customer_data ORDER BY customer_id NULLS LAST")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    
    with open('customer_data_export.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

conn.close()
print("Data exported to customer_data_export.csv")
```

Run it:
```powershell
python export_postgres_data.py
```

## Run DQ Analysis on Exported Data

After exporting the data:

```powershell
python data_quality_analysis.py --input-file customer_data_export.csv --output-dir dq_output_postgres
```

## Useful Docker Commands

### Stop the container
```powershell
docker-compose -f docker-compose-postgres.yml stop
```

### Start the container
```powershell
docker-compose -f docker-compose-postgres.yml start
```

### Remove the container and data
```powershell
docker-compose -f docker-compose-postgres.yml down -v
```

### View container logs
```powershell
docker logs postgres_dq_test
```

### Access PostgreSQL shell
```powershell
docker exec -it postgres_dq_test psql -U dquser -d dq_database
```

## Troubleshooting

### Port 5432 already in use
If you have another PostgreSQL instance running, either:
1. Stop the other instance
2. Change the port in `docker-compose-postgres.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Use port 5433 instead
   ```

### Container won't start
Check logs:
```powershell
docker logs postgres_dq_test
```

### Reset everything
```powershell
docker-compose -f docker-compose-postgres.yml down -v
docker-compose -f docker-compose-postgres.yml up -d
```

## SQL Script Details

The `setup_postgres_dq_test.sql` script includes:
1. **Table Creation**: Creates `customer_data` table with appropriate data types
2. **Good Records**: Inserts 5 clean records for baseline
3. **Bad Records**: Inserts 9 records with various DQ issues:
   - NULL/missing values
   - Invalid email formats
   - Negative values
   - Out-of-range values
   - Duplicate primary keys
   - Invalid country codes
   - Invalid status values
   - Outliers
4. **Verification Queries**: Queries to validate the data setup

## Next Steps

1. Start the PostgreSQL container
2. Verify data is loaded correctly
3. Export data to CSV
4. Run DQ analysis using `data_quality_analysis.py`
5. Review the DQ reports generated