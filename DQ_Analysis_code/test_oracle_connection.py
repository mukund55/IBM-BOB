#!/usr/bin/env python3
"""
Test Oracle Database Connection Script

This script tests the connection to Oracle database and verifies
that the data quality analysis script can access the data.

Usage:
    python test_oracle_connection.py
"""

import sys

def test_cx_oracle_import():
    """Test if cx_Oracle is installed"""
    print("=" * 80)
    print("STEP 1: Testing cx_Oracle Installation")
    print("=" * 80)
    try:
        import cx_Oracle
        print(f"✓ cx_Oracle is installed (version: {cx_Oracle.version})")
        return True
    except ImportError as e:
        print(f"✗ cx_Oracle is NOT installed")
        print(f"  Error: {e}")
        print("\nTo install cx_Oracle:")
        print("  pip install cx_Oracle")
        print("\nYou also need Oracle Instant Client:")
        print("  Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html")
        return False


def test_oracle_connection(host="localhost", port=1521, service_name="XE", 
                          username="dq_test", password="dq_test123"):
    """Test connection to Oracle database"""
    print("\n" + "=" * 80)
    print("STEP 2: Testing Oracle Database Connection")
    print("=" * 80)
    
    try:
        import cx_Oracle
        
        # Build connection string
        dsn = f"{host}:{port}/{service_name}"
        print(f"Connecting to: {username}@{dsn}")
        
        # Attempt connection
        connection = cx_Oracle.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        
        print(f"✓ Connection successful!")
        print(f"  Database version: {connection.version}")
        
        return connection
        
    except cx_Oracle.Error as error:
        print(f"✗ Connection failed!")
        print(f"  Error: {error}")
        print("\nTroubleshooting:")
        print("  1. Check if Oracle database is running")
        print("  2. Verify host, port, and service name")
        print("  3. Verify username and password")
        print("  4. Check if Oracle listener is running: lsnrctl status")
        return None


def test_query_execution(connection):
    """Test executing a query"""
    print("\n" + "=" * 80)
    print("STEP 3: Testing Query Execution")
    print("=" * 80)
    
    try:
        cursor = connection.cursor()
        
        # Test 1: Check if customers table exists
        print("\nTest 1: Checking if 'customers' table exists...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM user_tables 
            WHERE table_name = 'CUSTOMERS'
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✓ 'customers' table exists")
        else:
            print("✗ 'customers' table does NOT exist")
            print("\nTo create the table, run:")
            print("  sqlplus dq_test/dq_test123@localhost:1521/XE")
            print("  Then execute the CREATE TABLE statement from ORACLE_SETUP_GUIDE.md")
            cursor.close()
            return False
        
        # Test 2: Count records
        print("\nTest 2: Counting records in 'customers' table...")
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        print(f"✓ Found {count} records in 'customers' table")
        
        # Test 3: Fetch sample data
        print("\nTest 3: Fetching sample data...")
        cursor.execute("SELECT * FROM customers WHERE ROWNUM <= 3")
        columns = [desc[0] for desc in cursor.description]
        print(f"✓ Columns: {', '.join(columns)}")
        
        rows = cursor.fetchall()
        print(f"✓ Sample records:")
        for i, row in enumerate(rows, 1):
            print(f"  Record {i}: {dict(zip(columns, row))}")
        
        cursor.close()
        return True
        
    except Exception as error:
        print(f"✗ Query execution failed!")
        print(f"  Error: {error}")
        return False


def test_data_quality_config():
    """Test if data quality config file exists"""
    print("\n" + "=" * 80)
    print("STEP 4: Testing Data Quality Configuration")
    print("=" * 80)
    
    import json
    from pathlib import Path
    
    config_file = Path("dq_config_oracle.json")
    
    if not config_file.exists():
        print(f"✗ Configuration file not found: {config_file}")
        print("\nCreate the file with Oracle database settings.")
        return False
    
    print(f"✓ Configuration file exists: {config_file}")
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print("✓ Configuration file is valid JSON")
        
        # Check database section
        if 'database' in config:
            db_config = config['database']
            print(f"✓ Database configuration found:")
            print(f"  - Type: {db_config.get('type')}")
            print(f"  - Host: {db_config.get('host')}")
            print(f"  - Port: {db_config.get('port')}")
            print(f"  - Service: {db_config.get('service_name')}")
            print(f"  - Username: {db_config.get('username')}")
            print(f"  - Query: {db_config.get('query')}")
        else:
            print("✗ No 'database' section in configuration")
            return False
        
        return True
        
    except json.JSONDecodeError as error:
        print(f"✗ Configuration file has invalid JSON")
        print(f"  Error: {error}")
        return False


def main():
    """Main test function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ORACLE DATABASE CONNECTION TEST" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Test 1: cx_Oracle installation
    if not test_cx_oracle_import():
        print("\n" + "!" * 80)
        print("FAILED: cx_Oracle is not installed. Please install it first.")
        print("!" * 80)
        return 1
    
    # Test 2: Oracle connection
    connection = test_oracle_connection()
    if not connection:
        print("\n" + "!" * 80)
        print("FAILED: Could not connect to Oracle database.")
        print("!" * 80)
        return 1
    
    # Test 3: Query execution
    if not test_query_execution(connection):
        connection.close()
        print("\n" + "!" * 80)
        print("FAILED: Could not execute queries on the database.")
        print("!" * 80)
        return 1
    
    connection.close()
    
    # Test 4: Configuration file
    if not test_data_quality_config():
        print("\n" + "!" * 80)
        print("WARNING: Configuration file issues detected.")
        print("!" * 80)
    
    # Success summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✓ All tests passed successfully!")
    print("\nYou can now run data quality analysis:")
    print("  python data_quality_analysis.py --use-database --config-file dq_config_oracle.json")
    print("\nOr with dashboard:")
    print("  python data_quality_analysis.py --use-database --config-file dq_config_oracle.json --generate-dashboard")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
