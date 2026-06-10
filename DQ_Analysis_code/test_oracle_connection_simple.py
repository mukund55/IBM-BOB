#!/usr/bin/env python3
"""
Simple Oracle Database Connection Test
Tests connection to Oracle XE in Docker and displays sample data
"""

import oracledb
import sys

def test_oracle_connection():
    """Test Oracle database connection and display sample data"""
    
    print("=" * 80)
    print("Oracle Database Connection Test")
    print("=" * 80)
    print()
    
    # Connection parameters
    username = "dq_test"
    password = "dq_test123"
    host = "localhost"
    port = 1521
    service_name = "XEPDB1"  # Important: Use XEPDB1, not XE!
    
    print(f"Connection Details:")
    print(f"  Username: {username}")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Service: {service_name}")
    print()
    
    try:
        # Create connection string
        dsn = f"{host}:{port}/{service_name}"
        
        print(f"Connecting to Oracle database...")
        print(f"DSN: {dsn}")
        print()
        
        # Connect to Oracle
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        
        print("[OK] Connection successful!")
        print()
        
        # Get database version
        cursor = connection.cursor()
        cursor.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
        version = cursor.fetchone()
        if version:
            print(f"Database Version: {version[0]}")
            print()
        
        # Test customers table
        print("-" * 80)
        print("Testing 'customers' table:")
        print("-" * 80)
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        print(f"[OK] Total customers: {count}")
        print()
        
        # Display sample data
        print("Sample customer records:")
        print()
        cursor.execute("""
            SELECT customer_id, customer_name, email, phone, country, purchase_amount
            FROM customers
            WHERE ROWNUM <= 5
            ORDER BY customer_id
        """)
        
        print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Phone':<15} {'Country':<15} {'Amount':<10}")
        print("-" * 100)
        
        for row in cursor:
            cid, name, email, phone, country, amount = row
            name = name or "NULL"
            email = email or "NULL"
            phone = phone or "NULL"
            country = country or "NULL"
            amount = amount or 0
            print(f"{cid:<5} {name:<20} {email:<30} {phone:<15} {country:<15} {amount:<10.2f}")
        
        print()
        
        # Test orders table
        print("-" * 80)
        print("Testing 'orders' table:")
        print("-" * 80)
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        print(f"[OK] Total orders: {count}")
        print()
        
        # Check for data quality issues
        print("-" * 80)
        print("Data Quality Check:")
        print("-" * 80)
        
        # Check for NULL emails
        cursor.execute("SELECT COUNT(*) FROM customers WHERE email IS NULL")
        null_emails = cursor.fetchone()[0]
        print(f"  Records with NULL email: {null_emails}")
        
        # Check for NULL names
        cursor.execute("SELECT COUNT(*) FROM customers WHERE customer_name IS NULL")
        null_names = cursor.fetchone()[0]
        print(f"  Records with NULL name: {null_names}")
        
        # Check for invalid emails
        cursor.execute("SELECT COUNT(*) FROM customers WHERE email NOT LIKE '%@%'")
        invalid_emails = cursor.fetchone()[0]
        print(f"  Records with invalid email format: {invalid_emails}")
        
        # Check for negative amounts
        cursor.execute("SELECT COUNT(*) FROM customers WHERE purchase_amount < 0")
        negative_amounts = cursor.fetchone()[0]
        print(f"  Records with negative purchase amount: {negative_amounts}")
        
        print()
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        print("=" * 80)
        print("[SUCCESS] All tests passed successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Create Oracle DQ configuration file")
        print("2. Run DQ analysis: python data_quality_analysis.py --use-database --config-file dq_config_oracle.json")
        print()
        
        return True
        
    except oracledb.Error as error:
        print(f"[ERROR] Connection failed!")
        print(f"Error: {error}")
        print()
        print("Troubleshooting:")
        print("1. Ensure Oracle container is running: docker ps | findstr oracle-xe")
        print("2. Check if database is ready: docker logs oracle-xe | findstr 'DATABASE IS READY'")
        print("3. Verify service name is XEPDB1 (not XE)")
        print("4. Check if user exists: docker exec oracle-xe sqlplus sys/Oracle123@XEPDB1 as sysdba")
        print()
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_oracle_connection()
    sys.exit(0 if success else 1)

# Made with Bob
