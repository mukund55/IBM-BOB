# Installing Docker Desktop on Windows

## Error: 'docker' is not recognized

This error means Docker is not installed on your system. Follow these steps to install it.

## Option 1: Install Docker Desktop (Recommended)

### Step 1: Download Docker Desktop
1. Visit: https://www.docker.com/products/docker-desktop
2. Click "Download for Windows"
3. File size: ~500 MB
4. Save the installer: `Docker Desktop Installer.exe`

### Step 2: System Requirements
**Minimum Requirements:**
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
- OR Windows 11 64-bit
- 4GB RAM minimum (8GB recommended)
- BIOS-level hardware virtualization support must be enabled

**Check Windows Version:**
```powershell
winver
```

**Enable Virtualization:**
1. Restart computer
2. Enter BIOS/UEFI (usually F2, F10, or Del key during boot)
3. Find "Virtualization Technology" or "Intel VT-x" or "AMD-V"
4. Enable it
5. Save and exit

### Step 3: Install Docker Desktop
1. Run `Docker Desktop Installer.exe` as Administrator
2. Follow installation wizard:
   - ✓ Use WSL 2 instead of Hyper-V (recommended)
   - ✓ Add shortcut to desktop
3. Click "Install"
4. Wait for installation (5-10 minutes)
5. Click "Close and restart"

### Step 4: Start Docker Desktop
1. After restart, Docker Desktop should start automatically
2. If not, search for "Docker Desktop" in Start menu and run it
3. Accept the service agreement
4. Wait for Docker to start (green icon in system tray)

### Step 5: Verify Installation
Open PowerShell or Command Prompt:
```powershell
docker --version
docker ps
```

Expected output:
```
Docker version 24.0.x, build xxxxx
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

### Step 6: Configure Docker (Optional)
1. Right-click Docker icon in system tray
2. Click "Settings"
3. Resources → Memory: Set to 4GB or more
4. Resources → Disk: Ensure enough space (20GB+)
5. Click "Apply & Restart"

## Option 2: Install Oracle Database Directly (No Docker)

If you cannot install Docker, you can install Oracle Database XE directly:

### Step 1: Download Oracle XE
1. Visit: https://www.oracle.com/database/technologies/xe-downloads.html
2. Download "Oracle Database 21c Express Edition for Windows x64"
3. File: `OracleXE213_Win64.zip` (~2.5 GB)
4. You'll need an Oracle account (free to create)

### Step 2: Extract and Install
1. Extract the ZIP file
2. Run `setup.exe` as Administrator
3. Follow installation wizard:
   - Accept license agreement
   - Choose installation location (default: `C:\app\username\product\21c\dbhomeXE`)
   - Set password for SYS and SYSTEM users (remember this!)
   - Default port: 1521
   - Service name: XE
4. Wait for installation (15-30 minutes)

### Step 3: Verify Installation
Open Command Prompt:
```cmd
sqlplus sys/your_password@localhost:1521/XE as sysdba
```

If successful, you'll see:
```
SQL*Plus: Release 21.0.0.0.0 - Production
Connected to:
Oracle Database 21c Express Edition Release 21.0.0.0.0 - Production
```

### Step 4: Setup Database
```cmd
cd C:\Users\YourUsername\.bob\IBM-BOB\DQ_Analysis_code
sqlplus sys/your_password@localhost:1521/XE as sysdba @setup_oracle_db.sql
```

### Step 5: Update Configuration
Edit `dq_config_oracle.json`:
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

## Troubleshooting

### Docker Installation Issues

**Issue: "WSL 2 installation is incomplete"**
Solution:
1. Open PowerShell as Administrator
2. Run: `wsl --install`
3. Restart computer
4. Run Docker Desktop again

**Issue: "Hardware assisted virtualization is not enabled"**
Solution:
1. Restart computer
2. Enter BIOS (F2, F10, or Del during boot)
3. Enable "Intel VT-x" or "AMD-V"
4. Save and restart

**Issue: "Docker Desktop requires Windows 10 Pro/Enterprise"**
Solution:
- Upgrade to Windows 10 Pro, OR
- Use Oracle Database direct installation (Option 2)

### Oracle Direct Installation Issues

**Issue: "ORA-12541: TNS:no listener"**
Solution:
1. Open Services (services.msc)
2. Find "OracleServiceXE"
3. Right-click → Start
4. Find "OracleOraDB21Home1TNSListener"
5. Right-click → Start

**Issue: "Insufficient disk space"**
Solution:
- Free up at least 10GB on C: drive
- Or choose different installation location

## Next Steps

### After Docker Installation:
```powershell
# Pull Oracle image
docker pull container-registry.oracle.com/database/express:21.3.0-xe

# Run container
docker run -d --name oracle-xe -p 1521:1521 -e ORACLE_PWD=Oracle123 container-registry.oracle.com/database/express:21.3.0-xe

# Wait for database (2-3 minutes)
docker logs -f oracle-xe

# Setup database
docker cp setup_oracle_db.sql oracle-xe:/tmp/
docker exec -it oracle-xe sqlplus sys/Oracle123@XE as sysdba @/tmp/setup_oracle_db.sql

# Test connection
python test_oracle_connection.py

# Run analysis
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json
```

### After Direct Oracle Installation:
```cmd
# Setup database
sqlplus sys/your_password@localhost:1521/XE as sysdba @setup_oracle_db.sql

# Install Python dependency
pip install cx_Oracle

# Download Oracle Instant Client (if not already installed)
# Visit: https://www.oracle.com/database/technologies/instant-client/downloads.html

# Test connection
python test_oracle_connection.py

# Run analysis
python data_quality_analysis.py --use-database --config-file dq_config_oracle.json
```

## Alternative: Use SQLite (No Installation Required)

If both Docker and Oracle installation are not feasible, you can use SQLite:

### Create SQLite Database:
```python
import sqlite3
import pandas as pd

# Read CSV
df = pd.read_csv('sample_customer_data.csv')

# Create SQLite database
conn = sqlite3.connect('customers.db')
df.to_sql('customers', conn, if_exists='replace', index=False)
conn.close()
```

### Update Config:
```json
{
  "database": {
    "type": "sqlite",
    "database": "customers.db",
    "query": "SELECT * FROM customers"
  }
}
```

## Support Resources

- **Docker Desktop**: https://docs.docker.com/desktop/install/windows-install/
- **Oracle XE**: https://docs.oracle.com/en/database/oracle/oracle-database/21/xeinw/
- **WSL 2**: https://docs.microsoft.com/en-us/windows/wsl/install
- **Virtualization**: https://support.microsoft.com/en-us/windows/enable-virtualization-on-windows-11-pcs-c5578302-6e43-4b4b-a449-8ced115f58e1

## Quick Decision Guide

**Choose Docker if:**
- ✓ You have Windows 10 Pro/Enterprise or Windows 11
- ✓ You have 8GB+ RAM
- ✓ You want easy setup and cleanup
- ✓ You want to test multiple databases

**Choose Direct Install if:**
- ✓ You have Windows 10 Home
- ✓ You cannot enable virtualization
- ✓ You want permanent installation
- ✓ You need better performance

**Choose SQLite if:**
- ✓ You just want to test the data quality script
- ✓ You don't need Oracle-specific features
- ✓ You want zero installation
- ✓ You're working with small datasets