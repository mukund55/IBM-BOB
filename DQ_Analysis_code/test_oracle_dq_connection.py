#!/usr/bin/env python3
"""
Oracle Database Connection Test for DQ Analysis
================================================

This script tests the Oracle database connection specifically for the
Data Quality Analysis script. It verifies:
1. cx_Oracle installation
2. Oracle database connectivity
3. Table access and data retrieval
4. Configuration file validity
5. SQLAlchemy integration (used by DQ script)

Usage:
    python test_oracle_dq_connection.py
    python test_oracle_dq_connection.py --config oracle_connection_config.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


def print_header(title: str, char: str = "=") -> None:
    """Print a formatted header"""
    print("\n" + char * 80)
    print(title)
    print(char * 80)


def print_success(message: str) -> None:
    """Print success message"""
    print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print error message"""
    print(f"✗ {message}")


def print_warning(message: str) -> None:
    """Print warning message"""
    print(f"⚠ {message}")


def test_cx_oracle_import() -> bool:
    """Test if cx_Oracle is installed"""
    print_header("STEP 1: Testing cx_Oracle Installation")
    
    try:
        import cx_Oracle
        print_success(f"cx_Oracle is installed (version: {cx_Oracle.version})")
        
        try:
            client_version = cx_Oracle.clientversion()
            print_success(f"Oracle Instant Client: {'.'.join(map(str, client_version))}")
        except Exception as e:
            print_warning(f"Could not detect Oracle Instant Client: {e}")
        
        return True
    except ImportError as e:
        print_error("cx_Oracle is NOT installed")
        print(f"  Error: {e}")
        print("\nInstall: pip install cx_Oracle")
        return False


def test_sqlalchemy_import() -> bool:
    """Test if SQLAlchemy is installed"""
    print_header("STEP 2: Testing SQLAlchemy Installation")
    
    try:
        import sqlalchemy
        print_success(f"SQLAlchemy is installed (version: {sqlalchemy.__version__})")
        return True
    except ImportError as e:
        print_error("SQLAlchemy is NOT installed")
        print("\nInstall: pip install sqlalchemy")
        return False


def load_config(config_file: str) -> Optional[Dict[str, Any]]:
    """Load and validate configuration file"""
    print_header("STEP 3: Loading Configuration File")
    
    config_path = Path(config_file)
    
    if not config_path.exists():
        print_error(f"Configuration file not found: {config_file}")
        return None
    
    print_success(f"Configuration file exists: {config_file}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print_success("Configuration file is valid JSON")
        
        if 'database' not in config:
            print_error("No 'database' section in configuration")
            return None
        
        db_config = config['database']
        required = ['type', 'host', 'port', 'service_name', 'username', 'password', 'query']
        
        missing = [f for f in required if f not in db_config]
        if missing:
            print_error(f"Missing fields: {', '.join(missing)}")
            return None
        
        print_success("Database configuration is valid:")
        print(f"  - Type: {db_config.get('type')}")
        print(f"  - Host: {db_config.get('host')}")
        print(f"  - Port: {db_config.get('port')}")
        print(f"  - Service: {db_config.get('service_name')}")
        print(f"  - Username: {db_config.get('username')}")
        print(f"  - Query: {db_config.get('query')}")
        
        return config
        
    except json.JSONDecodeError as error:
        print_error(f"Invalid JSON: {error}")
        return None
    except Exception as error:
        print_error(f"Error reading config: {error}")
        return None


def test_cx_oracle_connection(config: Dict[str, Any]) -> Optional[Any]:
    """Test direct cx_Oracle connection"""
    print_header("STEP 4: Testing Direct cx_Oracle Connection")
    
    try:
        import cx_Oracle
        
        db = config['database']
        dsn = f"{db['host']}:{db['port']}/{db['service_name']}"
        print(f"Connecting to: {db['username']}@{dsn}")
        
        connection = cx_Oracle.connect(
            user=db['username'],
            password=db['password'],
            dsn=dsn
        )
        
        print_success("Connection successful!")
        print(f"  Database version: {connection.version}")
        
        return connection
        
    except Exception as error:
        print_error(f"Connection failed: {error}")
        print("\nTroubleshooting:")
        print("  1. Check Oracle container: docker ps | findstr oracle-xe")
        print("  2. Verify connection details in config")
        print("  3. Check logs: docker logs oracle-xe")
        return None


def test_sqlalchemy_connection(config: Dict[str, Any]) -> Optional[Any]:
    """Test SQLAlchemy connection"""
    print_header("STEP 5: Testing SQLAlchemy Connection")
    
    try:
        from sqlalchemy import create_engine, text
        
        db = config['database']
        conn_str = f"oracle+cx_oracle://{db['username']}:{db['password']}@{db['host']}:{db['port']}/?service_name={db['service_name']}"
        
        engine = create_engine(conn_str)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM DUAL"))
            result.fetchone()
        
        print_success("SQLAlchemy connection successful!")
        
        return engine
        
    except Exception as error:
        print_error(f"SQLAlchemy connection failed: {error}")
        return None


def test_query_execution(connection: Any, config: Dict[str, Any]) -> bool:
    """Test executing queries"""
    print_header("STEP 6: Testing Query Execution")
    
    try:
        cursor = connection.cursor()
        
        print("\nTest 1: Checking 'customers' table...")
        cursor.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'CUSTOMERS'")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print_success("'customers' table exists")
        else:
            print_error("'customers' table does NOT exist")
            print("\nRun setup_oracle_db.sql to create it")
            cursor.close()
            return False
        
        print("\nTest 2: Counting records...")
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        print_success(f"Found {count} records")
        
        if count == 0:
            print_warning("Table is empty")
        
        print("\nTest 3: Fetching sample data...")
        cursor.execute("SELECT * FROM customers WHERE ROWNUM <= 3")
        columns = [desc[0] for desc in cursor.description]
        print_success(f"Columns: {', '.join(columns)}")
        
        rows = cursor.fetchall()
        if rows:
            print_success(f"Sample records ({len(rows)}):")
            for i, row in enumerate(rows, 1):
                print(f"  Record {i}: {dict(zip(columns, row))}")
        
        print("\nTest 4: Testing configured query...")
        query = config['database'].get('query', 'SELECT * FROM customers')
        cursor.execute(query)
        result_count = len(cursor.fetchall())
        print_success(f"Query returned {result_count} rows")
        
        cursor.close()
        return True
        
    except Exception as error:
        print_error(f"Query execution failed: {error}")
        return False


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test Oracle connection for DQ Analysis')
    parser.add_argument('--config', default='DQ_Analysis_code/oracle_connection_config.json',
                       help='Path to configuration file')
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("ORACLE DATABASE CONNECTION TEST FOR DQ ANALYSIS")
    print("=" * 80)
    
    if not test_cx_oracle_import():
        return 1
    
    if not test_sqlalchemy_import():
        return 1
    
    config = load_config(args.config)
    if not config:
        return 1
    
    connection = test_cx_oracle_connection(config)
    if not connection:
        return 1
    
    engine = test_sqlalchemy_connection(config)
    if not engine:
        connection.close()
        return 1
    
    if not test_query_execution(connection, config):
        connection.close()
        return 1
    
    connection.close()
    
    print_header("SUMMARY")
    print_success("All tests passed!")
    print("\nRun DQ analysis:")
    print(f"  python DQ_Analysis_code/data_quality_analysis.py --use-database --config-file {args.config}")
    print("\nWith dashboard:")
    print(f"  python DQ_Analysis_code/data_quality_analysis.py --use-database --config-file {args.config} --generate-dashboard")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
