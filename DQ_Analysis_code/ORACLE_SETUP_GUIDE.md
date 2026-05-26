# Oracle Database Setup Guide for Data Quality Analysis

## Overview
This guide will help you set up Oracle Database and integrate it with the data quality analysis script.

## Option 1: Oracle Database Express Edition (XE) - Recommended for Testing

### Step 1: Download Oracle XE
1. Visit: https://www.oracle.com/database/technologies/xe-downloads.html
2. Download Oracle Database 21c Express Edition for Windows
3. File size: ~2.5 GB

### Step 2: Install Oracle XE
1. Run the installer (OracleXE213_Win64.zip)
2. Extract and run `setup.exe`
3. Follow installation wizard:
   - Accept license agreement
   - Choose installation location (default: C:\app\username\product\21c\dbhomeXE)
   - Set SYS and SYSTEM password (remember this!)
   - Default port: 1521
   - Service name: XE

### Step 3: Verify Installation
```cmd
# Open Command Prompt as Administrator
sqlplus sys/your_password@localhost:1521/XE as sysdba
```

If successful, you'll see:
```
SQL*Plus: Release 21.0.0.0.0 - Production
Connected to:
Oracle Database 21c Express Edition Release 21.0.0.0.0 - Production
```

## Option 2: Oracle Database in Docker (Easier Alternative)

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop
2. Install and restart your computer

### Step 2: Pull Oracle XE Image
```bash
docker pull container-registry.oracle.com/database/express:21.3.0-xe
```

### Step 3: Run Oracle Container
```bash
docker run -d \
  --name oracle-xe \
  -p 1521:1521 \
  -p 5500:5500 \
  -e ORACLE_PWD=YourPassword123 \
  container-registry.oracle.com/database/express:21.3.0-xe
```

### Step 4: Wait for Database to Start (2-3 minutes)
```bash
docker logs -f oracle-xe
```

Wait for: "DATABASE IS READY TO USE!"

## Step 5: Install Python Oracle Client

### Install cx_Oracle
```bash
pip install cx_Oracle
```

### Download Oracle Instant Client
1. Visit: https://www.oracle.com/database/technologies/instant-client/downloads.html
2. Download "Basic Package" for Windows x64
3. Extract to: C:\oracle\instantclient_21_9
4. Add to PATH:
   - Open System Properties > Environment Variables
   - Edit PATH variable
   - Add: C:\oracle\instantclient_21_9

### Verify Installation
```python
import cx_Oracle
print(cx_Oracle.version)
```

## Step 6: Create Test Database and User

### Connect as SYSDBA
```sql
sqlplus sys/YourPassword123@localhost:1521/XE as sysdba
```

### Create Test User
```sql
-- Create user
CREATE USER dq_test IDENTIFIED BY dq_test123;

-- Grant privileges
GRANT CONNECT, RESOURCE TO dq_test;
GRANT CREATE SESSION TO dq_test;
GRANT CREATE TABLE TO dq_test;
GRANT UNLIMITED TABLESPACE TO dq_test;

-- Verify
SELECT username FROM dba_users WHERE username = 'DQ_TEST';
```

### Create Sample Table
```sql
-- Connect as test user
CONNECT dq_test/dq_test123@localhost:1521/XE

-- Create sample customer table
CREATE TABLE customers (
    customer_id NUMBER(10) PRIMARY KEY,
    customer_name VARCHAR2(100),
    email VARCHAR2(100),
    phone VARCHAR2(20),
    country VARCHAR2(50),
    registration_date DATE,
    purchase_amount NUMBER(10,2),
    is_active NUMBER(1)
);

-- Insert sample data
INSERT INTO customers VALUES (1, 'John Doe', 'john@example.com', '1234567890', 'USA', SYSDATE, 1500.50, 1);
INSERT INTO customers VALUES (2, 'Jane Smith', 'jane@example.com', '0987654321', 'UK', SYSDATE-30, 2000.00, 1);
INSERT INTO customers VALUES (3, 'Bob Johnson', 'bob@example.com', '5555555555', 'Canada', SYSDATE-60, 500.00, 0);
INSERT INTO customers VALUES (4, 'Alice Williams', NULL, '4444444444', 'Australia', SYSDATE-90, 3000.00, 1);
INSERT INTO customers VALUES (5, 'Charlie Brown', 'charlie@invalid', NULL, 'USA', SYSDATE-120, -100.00, 1);

COMMIT;

-- Verify data
SELECT * FROM customers;
```

## Step 7: Configure Data Quality Analysis Script

### Create Oracle Configuration File
Create `dq_config_oracle.json`:

```json
{
  "general": {
    "output_dir": "dq_output_oracle",
    "log_file": "dq_run.log"
  },
  "database": {
    "type": "oracle",
    "host": "localhost",
    "port": 1521,
    "service_name": "XE",
    "username": "dq_test",
    "password": "dq_test123",
    "query": "SELECT * FROM customers"
  },
  "rules": {
    "mandatory_columns": ["customer_id", "customer_name", "email"],
    "email_columns": ["email"],
    "primary_key": ["customer_id"]
  }
}
```

## Step 8: Run Data Quality Analysis

### Basic Analysis
```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_oracle.json \
  --output-dir dq_output_oracle
```

### With Dashboard
```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_oracle.json \
  --generate-dashboard \
  --output-dir dq_output_oracle
```

### With Data Cleansing
```bash
python data_quality_analysis.py \
  --use-database \
  --config-file dq_config_oracle.json \
  --cleanse-data \
  --output-dir dq_output_oracle
```

## Connection String Formats

### Format 1: Service Name (Recommended)
```python
connection_string = "dq_test/dq_test123@localhost:1521/XE"
```

### Format 2: SID
```python
connection_string = "dq_test/dq_test123@localhost:1521/ORCL"
```

### Format 3: TNS Name
```python
connection_string = "dq_test/dq_test123@MYDB"
```

## Troubleshooting

### Error: "DPI-1047: Cannot locate a 64-bit Oracle Client library"
**Solution**: Install Oracle Instant Client and add to PATH

### Error: "ORA-12541: TNS:no listener"
**Solution**: 
1. Check if Oracle service is running
2. Verify port 1521 is not blocked
3. Check listener status: `lsnrctl status`

### Error: "ORA-01017: invalid username/password"
**Solution**: 
1. Verify credentials
2. Check if user exists: `SELECT username FROM dba_users;`
3. Reset password: `ALTER USER dq_test IDENTIFIED BY new_password;`

### Error: "ORA-12154: TNS:could not resolve the connect identifier"
**Solution**: Use full connection string with host:port/service_name

## Testing Connection

### Python Test Script
```python
import cx_Oracle

try:
    # Connect to Oracle
    connection = cx_Oracle.connect(
        user="dq_test",
        password="dq_test123",
        dsn="localhost:1521/XE"
    )
    
    print("✓ Connection successful!")
    
    # Test query
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    print(f"✓ Found {count} records in customers table")
    
    cursor.close()
    connection.close()
    
except cx_Oracle.Error as error:
    print(f"✗ Connection failed: {error}")
```

## Quick Start Commands

```bash
# 1. Install dependencies
pip install cx_Oracle

# 2. Start Oracle (if using Docker)
docker start oracle-xe

# 3. Create config file
# (Use the JSON example above)

# 4. Run analysis
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json

# 5. View results
# Open: dq_output_oracle/dq_executive_dashboard.html
```

## Additional Resources

- Oracle XE Documentation: https://docs.oracle.com/en/database/oracle/oracle-database/21/xeinw/
- cx_Oracle Documentation: https://cx-oracle.readthedocs.io/
- Oracle Instant Client: https://www.oracle.com/database/technologies/instant-client.html
- Docker Oracle Images: https://container-registry.oracle.com/

## Support

For issues with:
- **Oracle Installation**: Check Oracle documentation
- **Python Integration**: Check cx_Oracle documentation  
- **Data Quality Script**: Check script logs in dq_output/dq_run.log