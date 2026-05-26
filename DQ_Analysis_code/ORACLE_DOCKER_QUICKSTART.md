# Oracle Database Docker Quick Start Guide

## Prerequisites
- Docker Desktop installed and running
- Python 3.7+ installed
- At least 4GB RAM available for Docker

## Step-by-Step Setup

### 1. Pull Oracle XE Image
```bash
docker pull container-registry.oracle.com/database/express:21.3.0-xe
```

**Note**: This is a ~2.5GB download and may take 5-15 minutes depending on your internet speed.

### 2. Start Oracle Container
```bash
docker run -d \
  --name oracle-xe \
  -p 1521:1521 \
  -p 5500:5500 \
  -e ORACLE_PWD=Oracle123 \
  container-registry.oracle.com/database/express:21.3.0-xe
```

**Windows Command Prompt:**
```cmd
docker run -d --name oracle-xe -p 1521:1521 -p 5500:5500 -e ORACLE_PWD=Oracle123 container-registry.oracle.com/database/express:21.3.0-xe
```

### 3. Wait for Database to Start (2-3 minutes)
```bash
docker logs -f oracle-xe
```

Wait for the message: **"DATABASE IS READY TO USE!"**

Press `Ctrl+C` to exit the logs.

### 4. Verify Container is Running
```bash
docker ps
```

You should see `oracle-xe` in the list with status "Up".

### 5. Install Python Dependencies
```bash
pip install cx_Oracle
```

### 6. Download Oracle Instant Client

**Windows:**
1. Visit: https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
2. Download "Basic Package" (instantclient-basic-windows.x64-21.9.0.0.0dbru.zip)
3. Extract to: `C:\oracle\instantclient_21_9`
4. Add to PATH:
   - Open System Properties → Environment Variables
   - Edit PATH variable
   - Add: `C:\oracle\instantclient_21_9`
5. Restart your terminal/IDE

**Verify Installation:**
```bash
python -c "import cx_Oracle; print(cx_Oracle.version)"
```

### 7. Setup Database Schema

**Option A - Copy SQL file into container:**
```bash
docker cp setup_oracle_db.sql oracle-xe:/tmp/
docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql
```

**Option B - Connect from host (requires Oracle Client):**
```bash
sqlplus sys/Oracle123@localhost:1521/XE as sysdba @setup_oracle_db.sql
```

### 8. Test Connection
```bash
python test_oracle_connection.py
```

Expected output:
```
✓ cx_Oracle is installed
✓ Connection successful!
✓ 'customers' table exists
✓ Found 12 records in 'customers' table
```

### 9. Run Data Quality Analysis

**Basic Analysis:**
```bash
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json
```

**With Dashboard:**
```bash
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json --generate-dashboard
```

**With Data Cleansing:**
```bash
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json --cleanse-data
```

### 10. View Results
Open the dashboard in your browser:
```
dq_output_oracle/dq_executive_dashboard.html
```

## Connection Details

| Parameter | Value |
|-----------|-------|
| Host | localhost |
| Port | 1521 |
| Service Name | XE |
| SYS Password | Oracle123 |
| Test User | dq_test |
| Test Password | dq_test123 |

## Container Management

### Start Container
```bash
docker start oracle-xe
```

### Stop Container
```bash
docker stop oracle-xe
```

### View Logs
```bash
docker logs -f oracle-xe
```

### Access SQL*Plus
```bash
docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba
```

### Remove Container
```bash
docker stop oracle-xe
docker rm oracle-xe
```

### Remove Image (to free space)
```bash
docker rmi container-registry.oracle.com/database/express:21.3.0-xe
```

## Troubleshooting

### Issue: "Cannot connect to Docker daemon"
**Solution**: Start Docker Desktop

### Issue: "Port 1521 is already in use"
**Solution**: 
```bash
# Find what's using the port
netstat -ano | findstr :1521

# Stop the process or use a different port
docker run -d --name oracle-xe -p 1522:1521 -e ORACLE_PWD=Oracle123 container-registry.oracle.com/database/express:21.3.0-xe
```

### Issue: "DPI-1047: Cannot locate a 64-bit Oracle Client library"
**Solution**: Install Oracle Instant Client and add to PATH (see Step 6)

### Issue: Container keeps restarting
**Solution**: 
```bash
# Check logs for errors
docker logs oracle-xe

# Ensure you have enough memory (4GB minimum)
# Check Docker Desktop → Settings → Resources
```

### Issue: "ORA-12514: TNS:listener does not currently know of service"
**Solution**: Wait longer for database to initialize (can take 3-5 minutes on first start)

## Quick Commands Reference

```bash
# Setup (one-time)
docker pull container-registry.oracle.com/database/express:21.3.0-xe
docker run -d --name oracle-xe -p 1521:1521 -e ORACLE_PWD=Oracle123 container-registry.oracle.com/database/express:21.3.0-xe
docker logs -f oracle-xe  # Wait for "DATABASE IS READY"
docker cp setup_oracle_db.sql oracle-xe:/tmp/
docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql

# Daily use
docker start oracle-xe
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json --generate-dashboard

# Cleanup
docker stop oracle-xe
```

## Automated Setup

**Windows:**
```cmd
setup_oracle_docker.bat
```

This script will:
1. Check Docker installation
2. Pull Oracle XE image
3. Start container
4. Wait for database to be ready
5. Install Python dependencies
6. Provide next steps

## Enterprise Manager (Optional)

Access Oracle Enterprise Manager at:
```
http://localhost:5500/em
```

Login:
- Username: `sys`
- Password: `Oracle123`
- Container Name: `XE`
- Connect as: `SYSDBA`

## Performance Tips

1. **Allocate more memory to Docker**: Docker Desktop → Settings → Resources → Memory (4GB minimum, 8GB recommended)

2. **Persist data with volumes**:
```bash
docker run -d \
  --name oracle-xe \
  -p 1521:1521 \
  -e ORACLE_PWD=Oracle123 \
  -v oracle-data:/opt/oracle/oradata \
  container-registry.oracle.com/database/express:21.3.0-xe
```

3. **Auto-start container**:
```bash
docker update --restart unless-stopped oracle-xe
```

## Next Steps

1. ✅ Setup Oracle in Docker
2. ✅ Install cx_Oracle and Instant Client
3. ✅ Create test database and user
4. ✅ Test connection
5. ✅ Run data quality analysis
6. 📊 Explore the dashboard
7. 🔧 Customize rules in `dq_config_oracle.json`
8. 🚀 Connect to your production database

## Support

- **Docker Issues**: https://docs.docker.com/desktop/troubleshoot/overview/
- **Oracle XE**: https://docs.oracle.com/en/database/oracle/oracle-database/21/xeinw/
- **cx_Oracle**: https://cx-oracle.readthedocs.io/
- **Data Quality Script**: Check `dq_output_oracle/dq_run.log`