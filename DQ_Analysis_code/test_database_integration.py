#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify database integration for DQ Analysis.
Tests connection and basic query execution for different databases.
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

def test_imports():
    """Test if required libraries are installed"""
    print("=" * 80)
    print("TESTING IMPORTS")
    print("=" * 80)
    
    results = {}
    
    # Test SQLAlchemy
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text
        results['sqlalchemy'] = f"[OK] SQLAlchemy {sqlalchemy.__version__}"
    except ImportError as e:
        results['sqlalchemy'] = f"[FAIL] SQLAlchemy not installed: {e}"
    
    # Test PostgreSQL
    try:
        import psycopg2
        results['postgresql'] = f"[OK] psycopg2 installed"
    except ImportError:
        results['postgresql'] = "[FAIL] psycopg2 not installed (pip install psycopg2-binary)"
    
    # Test Oracle
    try:
        import cx_Oracle
        results['oracle'] = f"[OK] cx_Oracle installed"
    except ImportError:
        results['oracle'] = "[FAIL] cx_Oracle not installed (pip install cx_Oracle)"
    
    # Test SQL Server
    try:
        import pyodbc
        results['sqlserver'] = f"[OK] pyodbc installed"
    except ImportError:
        results['sqlserver'] = "[FAIL] pyodbc not installed (pip install pyodbc)"
    
    # Test MySQL
    try:
        import pymysql
        results['mysql'] = f"[OK] pymysql {pymysql.__version__}"
    except ImportError:
        results['mysql'] = "[FAIL] pymysql not installed (pip install pymysql)"
    
    # Test Snowflake
    try:
        import snowflake.connector
        results['snowflake'] = f"[OK] snowflake-connector installed"
    except ImportError:
        results['snowflake'] = "[FAIL] snowflake-connector not installed (pip install snowflake-connector-python)"
    
    # Test Pandas
    try:
        import pandas as pd
        results['pandas'] = f"[OK] pandas {pd.__version__}"
    except ImportError:
        results['pandas'] = "[FAIL] pandas not installed (pip install pandas)"
    
    for lib, status in results.items():
        print(f"{lib:20s}: {status}")
    
    print()
    return all('[OK]' in v for v in results.values() if 'sqlalchemy' in v or 'pandas' in v)


def test_postgresql_connection():
    """Test PostgreSQL connection"""
    print("=" * 80)
    print("TESTING POSTGRESQL CONNECTION")
    print("=" * 80)
    
    try:
        from sqlalchemy import create_engine, text
        
        # Test connection string
        connection_string = "postgresql://dq_user:postgres123@localhost:5432/dq_test"
        print(f"Connection string: {connection_string}")
        
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] Connected successfully!")
            print(f"  PostgreSQL version: {version[:50]}...")
            
            # Test query
            result = conn.execute(text("SELECT 1 as test"))
            test_val = result.fetchone()[0]
            print(f"[OK] Query execution successful (test value: {test_val})")
            
            # Check if customers table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'customers')"
            ))
            table_exists = result.fetchone()[0]
            
            if table_exists:
                print("[OK] 'customers' table exists")
                result = conn.execute(text("SELECT COUNT(*) FROM customers"))
                count = result.fetchone()[0]
                print(f"  Records in customers table: {count}")
            else:
                print("[WARN] 'customers' table does not exist")
                print("  Run the setup SQL from DATABASE_INTEGRATION_GUIDE.md")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] PostgreSQL connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running:")
        print("   docker ps | grep postgres")
        print("2. Start PostgreSQL if not running:")
        print("   docker start postgres-dq")
        print("3. Or create new container:")
        print("   docker run -d --name postgres-dq -e POSTGRES_PASSWORD=postgres123 -p 5432:5432 postgres:15")
        return False


def test_oracle_connection():
    """Test Oracle connection"""
    print("\n" + "=" * 80)
    print("TESTING ORACLE CONNECTION")
    print("=" * 80)
    
    try:
        from sqlalchemy import create_engine, text
        
        connection_string = "oracle+cx_oracle://dq_test:dq_test123@localhost:1521/?service_name=XE"
        print(f"Connection string: {connection_string}")
        
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM v$version WHERE ROWNUM = 1"))
            version = result.fetchone()[0]
            print(f"[OK] Connected successfully!")
            print(f"  Oracle version: {version}")
            
            # Check if customers table exists
            result = conn.execute(text(
                "SELECT COUNT(*) FROM user_tables WHERE table_name = 'CUSTOMERS'"
            ))
            table_exists = result.fetchone()[0] > 0
            
            if table_exists:
                print("[OK] 'CUSTOMERS' table exists")
                result = conn.execute(text("SELECT COUNT(*) FROM customers"))
                count = result.fetchone()[0]
                print(f"  Records in customers table: {count}")
            else:
                print("[WARN] 'CUSTOMERS' table does not exist")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Oracle connection failed: {e}")
        print("\nNote: Oracle setup is more complex. See ORACLE_SETUP_GUIDE.md")
        return False


def test_config_files():
    """Test if configuration files exist"""
    print("\n" + "=" * 80)
    print("TESTING CONFIGURATION FILES")
    print("=" * 80)
    
    config_files = [
        'dq_config_postgres.json',
        'dq_config_oracle.json',
        'dq_config_snowflake.json',
        'dq_config_redshift.json',
        'dq_config_mssql.json'
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"[OK] {config_file} exists")
        else:
            print(f"[FAIL] {config_file} not found")
    
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("DATABASE INTEGRATION TEST SUITE")
    print("=" * 80)
    print()
    
    # Test imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n[WARN] Some required libraries are missing")
        print("Install them with: pip install sqlalchemy psycopg2-binary pandas")
        print()
    
    # Test configuration files
    test_config_files()
    
    # Test PostgreSQL (recommended for testing)
    pg_ok = test_postgresql_connection()
    
    # Test Oracle (optional)
    oracle_ok = test_oracle_connection()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Imports:     {'[PASS]' if imports_ok else '[FAIL]'}")
    print(f"PostgreSQL:  {'[PASS]' if pg_ok else '[FAIL] (optional)'}")
    print(f"Oracle:      {'[PASS]' if oracle_ok else '[FAIL] (optional)'}")
    print()
    
    if pg_ok:
        print("[OK] You can now run DQ analysis on PostgreSQL:")
        print("  python data_quality_analysis.py --use-database --config-file dq_config_postgres.json --generate-dashboard")
    else:
        print("[WARN] Set up PostgreSQL first:")
        print("  See DATABASE_INTEGRATION_GUIDE.md for instructions")
    
    print("=" * 80)
    print()
    
    return 0 if (imports_ok and pg_ok) else 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
