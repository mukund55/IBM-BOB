# Database Integration Guide for Data Quality Analysis

## Overview

The DQ Analysis script supports multiple databases through SQLAlchemy. This guide covers setup and configuration for:
- **Oracle** (Best for enterprise, already configured)
- **Snowflake** (Best for cloud data warehouse)
- **Amazon Redshift** (Best for AWS ecosystem)
- **MS SQL Server** (Best for Microsoft ecosystem)
- **PostgreSQL** (Best for open-source)
- **MySQL** (Best for web applications)

## Database Comparison

| Database | Setup Complexity | Cost | Performance | Best For | Open Source |
|----------|-----------------|------|-------------|----------|-------------|
| **PostgreSQL** | ⭐ Easy | Free | ⭐⭐⭐⭐ | Testing, Development | ✅ Yes |
| **MySQL** | ⭐ Easy | Free | ⭐⭐⭐ | Web Apps | ✅ Yes |
| **Oracle** | ⭐⭐⭐ Complex | $$$ | ⭐⭐⭐⭐⭐ | Enterprise | ❌ No |
| **MS SQL Server** | ⭐⭐ Medium | $$ | ⭐⭐⭐⭐ | Microsoft Stack | ❌ No |
| **Snowflake** | ⭐⭐ Medium | $$$ | ⭐⭐⭐⭐⭐ | Cloud DW | ❌ No |
| **Redshift** | ⭐⭐ Medium | $$ | ⭐⭐⭐⭐ | AWS Ecosystem | ❌ No |

## Recommendation

**For Testing & Learning: PostgreSQL** ✅
- Free and open-source
- Easy to set up with Docker
- Full SQL support
- Great for validating DQ analysis before production

---

## 1. PostgreSQL (Recommended for Testing)

### Why PostgreSQL?
- ✅ **Free & Open Source**
- ✅ **Easy Docker Setup** (5 minutes)
- ✅ **Full SQL Support**
- ✅ **Great for Testing** before production databases
- ✅ **No License Costs**

### Quick Setup with Docker

```bash
# Pull PostgreSQL image
docker pull postgres:15

# Run PostgreSQL container
docker run -d \
  --name postgres-dq \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_USER=dq_user \
  -e POSTGRES_DB=dq_test \
  -p 5432:5432 \
  postgres:15

# Wait 10 seconds for startup
docker logs postgres-dq
```

### Install Python Driver

```bash
pip install psycopg2-binary
```

### Create Test Data

```sql
-- Connect to database
docker exec -it postgres-dq psql -U dq_user -d dq_test

-- Create sample table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    registration_date DATE,
    purchase_amount DECIMAL(10,2),
    is_active INTEGER,
    country_code VARCHAR(2)
);

-- Insert test data with quality issues
INSERT INTO customers VALUES
(1, 'John Doe', 'john@example.com', '555-0001', '2024-01-15', 1500.00, 1, 'US'),
(2, 'Jane Smith', 'jane@example.com', '555-0002', '2024-02-20', 2500.50, 1, 'UK'),
(3, 'Bob Johnson', NULL, '555-0003', '2024-03-10', -100.00, 1, 'CA'),  -- NULL email, negative amount
(4, 'Alice Brown', 'invalid-email', NULL, '2024-04-05', 3500.00, 2, 'AU'),  -- Invalid email, NULL phone
(5, 'Charlie Wilson', 'charlie@test.com', '555-0005', NULL, 999999.99, 1, 'IN'),  -- NULL date, outlier amount
(1, 'Duplicate John', 'john2@example.com', '555-0006', '2024-05-01', 1200.00, 1, 'US');  -- Duplicate ID

-- Exit
\q
```

### Configuration File: `dq_config_postgres.json`

```json
{
  "general": {
    "output_dir": "dq_output_postgres",
    "log_file": "dq_run.log",
    "normalize_column_names": true,
    "trim_whitespace": true
  },
  "database": {
    "enabled": true,
    "type": "postgresql",
    "connection_string": "postgresql://dq_user:postgres123@localhost:5432/dq_test",
    "query": "SELECT * FROM customers"
  },
  "rules": {
    "mandatory_columns": ["customer_id", "customer_name", "email"],
    "email_columns": ["email"],
    "primary_keys": ["customer_id"],
    "dtype_rules": {
      "customer_id": "numeric",
      "purchase_amount": "numeric",
      "registration_date": "date"
    },
    "negative_not_allowed_columns": ["purchase_amount"],
    "range_rules": {
      "purchase_amount": {"min": 0, "max": 100000}
    },
    "allowed_values": {
      "is_active": [0, 1],
      "country_code": ["US", "UK", "CA", "AU", "IN"]
    }
  },
  "anomaly_detection": {
    "check_nulls": true,
    "check_duplicates": true,
    "check_outliers": true,
    "check_invalid_emails": true,
    "outlier_method": "iqr",
    "outlier_threshold": 1.5
  }
}
```

### Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_postgres.json \
  --generate-dashboard \
  --cleanse-data
```

---

## 2. Snowflake (Cloud Data Warehouse)

### Install Driver

```bash
pip install snowflake-connector-python snowflake-sqlalchemy
```

### Configuration: `dq_config_snowflake.json`

```json
{
  "general": {
    "output_dir": "dq_output_snowflake"
  },
  "database": {
    "enabled": true,
    "type": "snowflake",
    "connection_string": "snowflake://username:password@account.region.snowflakecomputing.com/database/schema?warehouse=warehouse_name&role=role_name",
    "query": "SELECT * FROM your_table"
  },
  "rules": {
    "mandatory_columns": ["id", "name", "email"],
    "email_columns": ["email"],
    "primary_keys": ["id"]
  }
}
```

### Alternative Connection String Format

```python
# Using individual parameters
connection_string = (
    "snowflake://{user}:{password}@{account}/{database}/{schema}"
    "?warehouse={warehouse}&role={role}"
).format(
    user="your_username",
    password="your_password",
    account="xy12345.us-east-1",
    database="DQ_DATABASE",
    schema="PUBLIC",
    warehouse="COMPUTE_WH",
    role="ACCOUNTADMIN"
)
```

### Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_snowflake.json \
  --generate-dashboard
```

---

## 3. Amazon Redshift (AWS Data Warehouse)

### Install Driver

```bash
pip install redshift-connector sqlalchemy-redshift
```

### Configuration: `dq_config_redshift.json`

```json
{
  "general": {
    "output_dir": "dq_output_redshift"
  },
  "database": {
    "enabled": true,
    "type": "redshift",
    "connection_string": "redshift+psycopg2://username:password@cluster-name.region.redshift.amazonaws.com:5439/database",
    "query": "SELECT * FROM your_schema.your_table"
  },
  "rules": {
    "mandatory_columns": ["id", "name"],
    "primary_keys": ["id"]
  }
}
```

### Using IAM Authentication

```python
# For IAM-based authentication
connection_string = (
    "redshift+redshift_connector://"
    "?iam=True"
    "&cluster_identifier=my-cluster"
    "&region=us-east-1"
    "&db_user=iam_user"
    "&database=dev"
)
```

### Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_redshift.json \
  --generate-dashboard
```

---

## 4. MS SQL Server (Microsoft)

### Install Driver

```bash
pip install pyodbc
```

### Configuration: `dq_config_mssql.json`

```json
{
  "general": {
    "output_dir": "dq_output_mssql"
  },
  "database": {
    "enabled": true,
    "type": "sqlserver",
    "connection_string": "mssql+pyodbc://username:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server",
    "query": "SELECT * FROM dbo.your_table"
  },
  "rules": {
    "mandatory_columns": ["id", "name"],
    "primary_keys": ["id"]
  }
}
```

### Windows Authentication

```json
{
  "database": {
    "connection_string": "mssql+pyodbc://server/database?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
  }
}
```

### Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_mssql.json \
  --generate-dashboard
```

---

## 5. Oracle (Enterprise)

### Install Driver

```bash
pip install cx_Oracle
```

### Download Oracle Instant Client
- Windows: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
- Linux: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html

### Configuration: `dq_config_oracle.json`

```json
{
  "general": {
    "output_dir": "dq_output_oracle"
  },
  "database": {
    "enabled": true,
    "type": "oracle",
    "connection_string": "oracle+cx_oracle://username:password@localhost:1521/?service_name=XE",
    "query": "SELECT * FROM customers"
  },
  "rules": {
    "mandatory_columns": ["customer_id", "customer_name"],
    "primary_keys": ["customer_id"]
  }
}
```

### Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_oracle.json \
  --generate-dashboard
```

---

## 6. MySQL (Web Applications)

### Install Driver

```bash
pip install pymysql
```

### Configuration: `dq_config_mysql.json`

```json
{
  "general": {
    "output_dir": "dq_output_mysql"
  },
  "database": {
    "enabled": true,
    "type": "mysql",
    "connection_string": "mysql+pymysql://username:password@localhost:3306/database",
    "query": "SELECT * FROM your_table"
  },
  "rules": {
    "mandatory_columns": ["id", "name"],
    "primary_keys": ["id"]
  }
}
```

### Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_mysql.json \
  --generate-dashboard
```

---

## Advanced Features

### 1. Query with Filters

```json
{
  "database": {
    "query": "SELECT * FROM customers WHERE registration_date >= '2024-01-01' AND is_active = 1"
  }
}
```

### 2. Join Multiple Tables

```json
{
  "database": {
    "query": "SELECT c.*, o.order_total FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id"
  }
}
```

### 3. Sample Large Tables

```json
{
  "database": {
    "query": "SELECT * FROM large_table TABLESAMPLE SYSTEM (10)"
  }
}
```

### 4. Get Table Metadata (DDL)

```python
# Add this to your script to extract DDL
from sqlalchemy import inspect, MetaData

def get_table_ddl(connection_string, table_name):
    engine = create_engine(connection_string)
    inspector = inspect(engine)
    
    # Get columns
    columns = inspector.get_columns(table_name)
    print(f"\nTable: {table_name}")
    print("Columns:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")
    
    # Get primary keys
    pk = inspector.get_pk_constraint(table_name)
    print(f"\nPrimary Keys: {pk['constrained_columns']}")
    
    # Get foreign keys
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        print(f"\nForeign Key: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Get indexes
    indexes = inspector.get_indexes(table_name)
    for idx in indexes:
        print(f"\nIndex: {idx['name']} on {idx['column_names']}")
```

### 5. Database-Level Analysis

```json
{
  "database": {
    "query": "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public'"
  }
}
```

---

## Complete Workflow Example

### Step 1: Setup PostgreSQL (Recommended for Testing)

```bash
# Start PostgreSQL
docker run -d --name postgres-dq -e POSTGRES_PASSWORD=postgres123 -p 5432:5432 postgres:15

# Create test data
docker exec -it postgres-dq psql -U postgres -c "
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    amount DECIMAL(10,2)
);
INSERT INTO customers VALUES 
(1, 'John', 'john@test.com', 100.00),
(2, 'Jane', NULL, -50.00),
(3, 'Bob', 'invalid', 999999.99);
"
```

### Step 2: Install Dependencies

```bash
pip install psycopg2-binary sqlalchemy pandas numpy plotly
```

### Step 3: Create Config

Create `dq_config_postgres.json`:
```json
{
  "general": {"output_dir": "dq_output_postgres"},
  "database": {
    "enabled": true,
    "type": "postgresql",
    "connection_string": "postgresql://postgres:postgres123@localhost:5432/postgres",
    "query": "SELECT * FROM customers"
  },
  "rules": {
    "mandatory_columns": ["id", "name", "email"],
    "email_columns": ["email"],
    "negative_not_allowed_columns": ["amount"]
  }
}
```

### Step 4: Run Analysis

```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_postgres.json \
  --generate-dashboard \
  --cleanse-data
```

### Step 5: View Results

- Dashboard: `dq_output_postgres/dq_executive_dashboard.html`
- Bad Records: `dq_output_postgres/bad_records_*.csv`
- Cleansed Data: `dq_output_postgres/cleansed_data.csv`

---

## Troubleshooting

### Connection Errors

```bash
# Test connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@localhost:5432/db')
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Connection successful!')
"
```

### Driver Issues

```bash
# PostgreSQL
pip install psycopg2-binary

# Oracle
pip install cx_Oracle
# Download Instant Client from Oracle

# SQL Server
pip install pyodbc
# Install ODBC Driver 17 for SQL Server

# Snowflake
pip install snowflake-connector-python snowflake-sqlalchemy

# Redshift
pip install redshift-connector sqlalchemy-redshift
```

### Permission Issues

```sql
-- Grant SELECT permission
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dq_user;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO dq_user;
```

---

## Best Practices

1. **Start with PostgreSQL** for testing and validation
2. **Use read-only accounts** for production databases
3. **Limit query scope** with WHERE clauses
4. **Sample large tables** to avoid performance issues
5. **Schedule analysis** during off-peak hours
6. **Monitor query performance** with EXPLAIN
7. **Use connection pooling** for multiple analyses
8. **Encrypt connection strings** in production
9. **Log all database operations** for audit trails
10. **Test on dev/staging** before production

---

## Summary

| Database | Best For | Setup Time | Cost |
|----------|----------|------------|------|
| **PostgreSQL** | Testing, Learning | 5 min | Free |
| **MySQL** | Web Apps | 5 min | Free |
| **Oracle** | Enterprise | 30 min | $$$ |
| **SQL Server** | Microsoft Stack | 15 min | $$ |
| **Snowflake** | Cloud DW | 10 min | $$$ |
| **Redshift** | AWS Ecosystem | 15 min | $$ |

**Recommendation**: Start with **PostgreSQL** for testing, then move to your production database once validated.

---

## Next Steps

1. ✅ Choose your database (PostgreSQL recommended for testing)
2. ✅ Install required drivers
3. ✅ Create configuration file
4. ✅ Test connection
5. ✅ Run DQ analysis
6. ✅ Review dashboard and results
7. ✅ Configure cleansing rules
8. ✅ Schedule regular analysis

For more help, see:
- `README.md` - General usage
- `CLEANSING_GUIDE.md` - Data cleansing features
- `ORACLE_SETUP_GUIDE.md` - Oracle-specific setup