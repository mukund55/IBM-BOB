# Oracle Database Connection Guide for DQ Analysis

This guide explains how to set up and use a separate Oracle database connection for testing your Data Quality (DQ) analysis script.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Configuration Files](#configuration-files)
5. [Testing the Connection](#testing-the-connection)
6. [Running DQ Analysis](#running-dq-analysis)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## 🎯 Overview

This setup provides a dedicated Oracle database connection for testing the DQ analysis script with Oracle databases. It includes:

- **Separate configuration file** (`oracle_connection_config.json`)
- **Connection test script** (`test_oracle_dq_connection.py`)
- **Automated run scripts** (`.bat` and `.ps1`)
- **Isolated output directory** (`dq_output_oracle_test`)

---

## ✅ Prerequisites

### 1. Oracle Database

You need an Oracle database instance. Options:

**Option A: Docker Container (Recommended)**
```bash
# Pull and run Oracle XE
docker run -d --name oracle-xe \
  -p 1521:1521 \
  -e ORACLE_PASSWORD=Oracle123 \
  gvenzl/oracle-xe:latest

# Wait for database to be ready (2-3 minutes)
docker logs -f oracle-xe
```

**Option B: Local Oracle Installation**
- Oracle Database 11g or higher
- Ensure listener is running on port 1521

### 2. Python Dependencies

Install required packages:

```bash
pip install cx_Oracle sqlalchemy pandas numpy
```

### 3. Oracle Instant Client

Download and install Oracle Instant Client:
- **Windows**: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
- **Linux**: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html
- **macOS**: https://www.oracle.com/database/technologies/instant-client/macos-intel-x86-downloads.html

Add to PATH or set environment variables:
```bash
# Windows
set PATH=%PATH%;C:\oracle\instantclient_21_3

# Linux/macOS
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_3:$LD_LIBRARY_PATH
```

### 4. Database Setup

Run the setup script to create test user and sample data:

```bash
# Copy SQL script to container
docker cp DQ_Analysis_code/setup_oracle_db.sql oracle-xe:/tmp/

# Execute setup
docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql
```

Or use the automated setup:
```bash
DQ_Analysis_code\setup_oracle_complete.bat
```

---

## 🚀 Quick Start

### Step 1: Verify Configuration

Check that `oracle_connection_config.json` exists with correct settings:

```json
{
  "database": {
    "type": "oracle",
    "host": "localhost",
    "port": 1521,
    "service_name": "XE",
    "username": "dq_test",
    "password": "dq_test123",
    "query": "SELECT * FROM customers"
  }
}
```

### Step 2: Test Connection

Run the connection test:

```bash
# Using Python directly
python DQ_Analysis_code/test_oracle_dq_connection.py

# Or with custom config
python DQ_Analysis_code/test_oracle_dq_connection.py --config path/to/config.json
```

Expected output:
```
✓ cx_Oracle is installed
✓ SQLAlchemy is installed
✓ Configuration file is valid
✓ Connection successful!
✓ All tests passed!
```

### Step 3: Run DQ Analysis

Use the automated scripts:

**Windows (Command Prompt):**
```bash
DQ_Analysis_code\run_oracle_dq_analysis.bat
```

**Windows (PowerShell):**
```powershell
.\DQ_Analysis_code\run_oracle_dq_analysis.ps1
```

**Manual execution:**
```bash
python DQ_Analysis_code/data_quality_analysis.py \
  --use-database \
  --config-file DQ_Analysis_code/oracle_connection_config.json \
  --generate-dashboard
```

### Step 4: View Results

Results are saved in `dq_output_oracle_test/`:

- **dq_executive_dashboard.html** - Interactive dashboard (opens automatically)
- **dq_executive_summary.txt** - Quick text summary
- **dq_summary.csv** - Detailed metrics
- **good_records.csv** - Clean data records
- **dq_all_bad_records.csv** - Records with issues
- **dq_oracle_run.log** - Execution log

---

## 📝 Configuration Files

### oracle_connection_config.json

Complete configuration structure:

```json
{
  "general": {
    "output_dir": "dq_output_oracle_test",
    "log_file": "dq_oracle_run.log",
    "log_level": "INFO"
  },
  "database": {
    "type": "oracle",
    "host": "localhost",
    "port": 1521,
    "service_name": "XE",
    "username": "dq_test",
    "password": "dq_test123",
    "query": "SELECT * FROM customers",
    "connection_timeout": 30,
    "fetch_size": 1000
  },
  "rules": {
    "mandatory_columns": ["customer_id", "customer_name", "email"],
    "email_columns": ["email"],
    "primary_key": ["customer_id"],
    "numeric_columns": ["customer_id", "purchase_amount"],
    "date_columns": {
      "registration_date": {"format": "%Y-%m-%d"}
    },
    "pattern_rules": {
      "phone": "^\\d{10}$"
    },
    "range_rules": {
      "purchase_amount": {"min": 0, "max": 100000}
    }
  },
  "anomaly_detection": {
    "outlier_method": "iqr",
    "iqr_multiplier": 1.5,
    "outlier_columns": ["purchase_amount"]
  },
  "output": {
    "generate_dashboard": true,
    "export_good_records": true,
    "export_bad_records": true
  }
}
```

### Connection String Format

The script uses SQLAlchemy connection strings:

```
oracle+cx_oracle://username:password@host:port/?service_name=service_name
```

For TNS names:
```
oracle+cx_oracle://username:password@tnsname
```

---

## 🧪 Testing the Connection

### Basic Test

```bash
python DQ_Analysis_code/test_oracle_dq_connection.py
```

### Test Steps Performed

1. **cx_Oracle Installation** - Verifies cx_Oracle is installed
2. **SQLAlchemy Installation** - Verifies SQLAlchemy is available
3. **Configuration Loading** - Validates config file
4. **Direct Connection** - Tests cx_Oracle connection
5. **SQLAlchemy Connection** - Tests SQLAlchemy engine
6. **Query Execution** - Runs sample queries

### Interpreting Results

**All tests passed:**
```
✓ All tests passed!
Run DQ analysis:
  python DQ_Analysis_code/data_quality_analysis.py --use-database --config-file ...
```

**Connection failed:**
```
✗ Connection failed: ORA-12541: TNS:no listener
Troubleshooting:
  1. Check Oracle container: docker ps | findstr oracle-xe
  2. Verify connection details in config
```

---

## 🔧 Running DQ Analysis

### Method 1: Automated Scripts

**Windows Batch:**
```bash
DQ_Analysis_code\run_oracle_dq_analysis.bat
```

**PowerShell:**
```powershell
.\DQ_Analysis_code\run_oracle_dq_analysis.ps1
```

These scripts:
1. Verify Python installation
2. Check configuration file
3. Test Oracle connection
4. Run DQ analysis
5. Open dashboard in browser

### Method 2: Manual Execution

**Basic analysis:**
```bash
python DQ_Analysis_code/data_quality_analysis.py \
  --use-database \
  --config-file DQ_Analysis_code/oracle_connection_config.json
```

**With dashboard:**
```bash
python DQ_Analysis_code/data_quality_analysis.py \
  --use-database \
  --config-file DQ_Analysis_code/oracle_connection_config.json \
  --generate-dashboard
```

**Custom output directory:**
```bash
python DQ_Analysis_code/data_quality_analysis.py \
  --use-database \
  --config-file DQ_Analysis_code/oracle_connection_config.json \
  --output-dir my_custom_output
```

### Method 3: Python Script

```python
import subprocess

result = subprocess.run([
    'python', 'DQ_Analysis_code/data_quality_analysis.py',
    '--use-database',
    '--config-file', 'DQ_Analysis_code/oracle_connection_config.json',
    '--generate-dashboard'
], capture_output=True, text=True)

print(result.stdout)
```

---

## 🔍 Troubleshooting

### Issue 1: cx_Oracle Not Found

**Error:**
```
ModuleNotFoundError: No module named 'cx_Oracle'
```

**Solution:**
```bash
pip install cx_Oracle
```

### Issue 2: Oracle Instant Client Not Found

**Error:**
```
DPI-1047: Cannot locate a 64-bit Oracle Client library
```

**Solution:**
1. Download Oracle Instant Client
2. Extract to a directory (e.g., `C:\oracle\instantclient_21_3`)
3. Add to PATH:
   ```bash
   set PATH=%PATH%;C:\oracle\instantclient_21_3
   ```

### Issue 3: Connection Refused

**Error:**
```
ORA-12541: TNS:no listener
```

**Solution:**
1. Check if Oracle is running:
   ```bash
   docker ps | findstr oracle-xe
   ```
2. Start if stopped:
   ```bash
   docker start oracle-xe
   ```
3. Wait for database to be ready:
   ```bash
   docker logs -f oracle-xe
   ```

### Issue 4: Invalid Username/Password

**Error:**
```
ORA-01017: invalid username/password; logon denied
```

**Solution:**
1. Verify credentials in config file
2. Reset password if needed:
   ```sql
   ALTER USER dq_test IDENTIFIED BY new_password;
   ```

### Issue 5: Table Not Found

**Error:**
```
ORA-00942: table or view does not exist
```

**Solution:**
Run the setup script:
```bash
docker exec -it oracle-xe sqlplus dq_test/dq_test123@XE @/tmp/setup_oracle_db.sql
```

### Issue 6: Port Already in Use

**Error:**
```
Error starting container: port 1521 is already allocated
```

**Solution:**
1. Stop conflicting service
2. Or use different port:
   ```bash
   docker run -p 1522:1521 ...
   ```
   Update config: `"port": 1522`

---

## ⚙️ Advanced Configuration

### Custom Query

Modify the query in config:

```json
{
  "database": {
    "query": "SELECT * FROM customers WHERE country = 'USA' AND registration_date > SYSDATE - 365"
  }
}
```

### Multiple Tables

For joins:

```json
{
  "database": {
    "query": "SELECT c.*, o.order_count FROM customers c LEFT JOIN (SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id) o ON c.customer_id = o.customer_id"
  }
}
```

### Connection Pooling

For better performance:

```json
{
  "database": {
    "connection_timeout": 60,
    "fetch_size": 5000,
    "pool_size": 5,
    "max_overflow": 10
  }
}
```

### Custom Rules

Add specific validation rules:

```json
{
  "rules": {
    "business_rules": {
      "valid_status": {
        "column": "is_active",
        "allowed_values": [0, 1]
      },
      "positive_amount": {
        "column": "purchase_amount",
        "condition": "> 0"
      }
    }
  }
}
```

### Environment Variables

Use environment variables for sensitive data:

```json
{
  "database": {
    "username": "${ORACLE_USER}",
    "password": "${ORACLE_PASSWORD}"
  }
}
```

Set in environment:
```bash
set ORACLE_USER=dq_test
set ORACLE_PASSWORD=dq_test123
```

---

## 📊 Output Files

### Executive Dashboard (HTML)

Interactive dashboard with:
- Overall DQ score
- Issue breakdown by category
- Column-level metrics
- Trend charts
- Recommendations

### Summary Files

- **dq_summary.csv** - Overall metrics
- **dq_score_breakdown.csv** - Detailed scoring
- **dq_column_metrics.csv** - Per-column statistics
- **dq_recommendations.csv** - Improvement suggestions

### Data Files

- **good_records.csv** - Records passing all checks
- **dq_all_bad_records.csv** - All records with issues
- **bad_records_*.csv** - Issues by category

### Log Files

- **dq_oracle_run.log** - Execution log with timestamps

---

## 🔗 Related Files

- `oracle_connection_config.json` - Main configuration
- `test_oracle_dq_connection.py` - Connection test script
- `run_oracle_dq_analysis.bat` - Windows batch runner
- `run_oracle_dq_analysis.ps1` - PowerShell runner
- `setup_oracle_db.sql` - Database setup script
- `data_quality_analysis.py` - Main DQ analysis script

---

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review log files in `dq_output_oracle_test/`
3. Test connection with `test_oracle_dq_connection.py`
4. Verify Oracle database is running: `docker ps`

---

## 📝 Notes

- Default output directory: `dq_output_oracle_test`
- Default log file: `dq_oracle_run.log`
- Connection timeout: 30 seconds
- Fetch size: 1000 rows per batch
- Dashboard auto-opens after successful run

---

**Created with Bob** 🤖