-- ============================================================================
-- Oracle Database Setup Script for Data Quality Analysis (Fixed for PDB)
-- ============================================================================
-- 
-- This script creates a test user and sample data for testing the
-- data quality analysis tool with Oracle database.
--
-- Usage:
--   sqlplus sys/Oracle123@XEPDB1 as sysdba @setup_oracle_db_fixed.sql
--
-- ============================================================================

SET ECHO ON
SET FEEDBACK ON
SET SERVEROUTPUT ON

PROMPT ============================================================================
PROMPT Creating Test User: dq_test in XEPDB1
PROMPT ============================================================================

-- Drop user if exists (for clean setup)
BEGIN
    EXECUTE IMMEDIATE 'DROP USER dq_test CASCADE';
    DBMS_OUTPUT.PUT_LINE('Existing user dropped');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -1918 THEN -- User does not exist
            RAISE;
        END IF;
        DBMS_OUTPUT.PUT_LINE('User does not exist, creating new');
END;
/

-- Create user
CREATE USER dq_test IDENTIFIED BY dq_test123
    DEFAULT TABLESPACE users
    TEMPORARY TABLESPACE temp
    QUOTA UNLIMITED ON users;

-- Grant privileges
GRANT CONNECT TO dq_test;
GRANT RESOURCE TO dq_test;
GRANT CREATE SESSION TO dq_test;
GRANT CREATE TABLE TO dq_test;
GRANT CREATE VIEW TO dq_test;
GRANT CREATE SEQUENCE TO dq_test;

PROMPT User 'dq_test' created successfully with password 'dq_test123'

-- Connect as the new user
CONNECT dq_test/dq_test123@XEPDB1

PROMPT ============================================================================
PROMPT Creating Sample Tables
PROMPT ============================================================================

-- Create customers table
CREATE TABLE customers (
    customer_id NUMBER(10) PRIMARY KEY,
    customer_name VARCHAR2(100),
    email VARCHAR2(100),
    phone VARCHAR2(20),
    country VARCHAR2(50),
    registration_date DATE,
    purchase_amount NUMBER(10,2),
    is_active NUMBER(1),
    created_date DATE DEFAULT SYSDATE,
    updated_date DATE DEFAULT SYSDATE
);

PROMPT Table 'customers' created

-- Create orders table (for referential integrity testing)
CREATE TABLE orders (
    order_id NUMBER(10) PRIMARY KEY,
    customer_id NUMBER(10),
    order_date DATE,
    order_amount NUMBER(10,2),
    order_status VARCHAR2(20),
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

PROMPT Table 'orders' created

PROMPT ============================================================================
PROMPT Inserting Sample Data
PROMPT ============================================================================

-- Insert good quality data
INSERT INTO customers VALUES (1, 'John Doe', 'john.doe@example.com', '1234567890', 'USA', SYSDATE-365, 1500.50, 1, SYSDATE, SYSDATE);
INSERT INTO customers VALUES (2, 'Jane Smith', 'jane.smith@example.com', '0987654321', 'UK', SYSDATE-300, 2000.00, 1, SYSDATE, SYSDATE);
INSERT INTO customers VALUES (3, 'Bob Johnson', 'bob.johnson@example.com', '5555555555', 'Canada', SYSDATE-250, 500.00, 1, SYSDATE, SYSDATE);

-- Insert data with quality issues
INSERT INTO customers VALUES (4, 'Alice Williams', NULL, '4444444444', 'Australia', SYSDATE-200, 3000.00, 1, SYSDATE, SYSDATE); -- Missing email
INSERT INTO customers VALUES (5, 'Charlie Brown', 'charlie@invalid', NULL, 'USA', SYSDATE-150, -100.00, 1, SYSDATE, SYSDATE); -- Invalid email, missing phone, negative amount
INSERT INTO customers VALUES (6, NULL, 'test@example.com', '3333333333', 'Germany', SYSDATE-100, 750.00, 0, SYSDATE, SYSDATE); -- Missing name
INSERT INTO customers VALUES (7, 'David Lee', 'david.lee@example.com', '2222222222', NULL, SYSDATE-50, 1200.00, 1, SYSDATE, SYSDATE); -- Missing country
INSERT INTO customers VALUES (8, 'Eve Martinez', 'eve.martinez@example.com', '1111111111', 'Spain', NULL, 850.00, 1, SYSDATE, SYSDATE); -- Missing registration date
INSERT INTO customers VALUES (9, 'Frank Wilson', 'frank@test', '9999999999', 'France', SYSDATE-25, 0.00, 2, SYSDATE, SYSDATE); -- Invalid email, invalid is_active
INSERT INTO customers VALUES (10, 'Grace Taylor', 'grace.taylor@example.com', '8888888888', 'Italy', SYSDATE-10, 999999.99, 1, SYSDATE, SYSDATE); -- Outlier amount

-- Insert duplicate records (for duplicate detection)
INSERT INTO customers VALUES (11, 'John Doe', 'john.doe@example.com', '1234567890', 'USA', SYSDATE-365, 1500.50, 1, SYSDATE, SYSDATE); -- Duplicate of ID 1
INSERT INTO customers VALUES (12, 'Jane Smith', 'jane.smith@example.com', '0987654321', 'UK', SYSDATE-300, 2000.00, 1, SYSDATE, SYSDATE); -- Duplicate of ID 2

-- Insert orders
INSERT INTO orders VALUES (1, 1, SYSDATE-30, 150.00, 'COMPLETED');
INSERT INTO orders VALUES (2, 2, SYSDATE-25, 200.00, 'COMPLETED');
INSERT INTO orders VALUES (3, 3, SYSDATE-20, 50.00, 'PENDING');
INSERT INTO orders VALUES (4, 999, SYSDATE-15, 100.00, 'COMPLETED'); -- Referential integrity violation

COMMIT;

PROMPT Sample data inserted successfully

PROMPT ============================================================================
PROMPT Creating Indexes
PROMPT ============================================================================

CREATE INDEX idx_customer_email ON customers(email);
CREATE INDEX idx_customer_country ON customers(country);
CREATE INDEX idx_order_customer ON orders(customer_id);

PROMPT Indexes created

PROMPT ============================================================================
PROMPT Gathering Statistics
PROMPT ============================================================================

BEGIN
    DBMS_STATS.GATHER_TABLE_STATS(USER, 'CUSTOMERS');
    DBMS_STATS.GATHER_TABLE_STATS(USER, 'ORDERS');
END;
/

PROMPT Statistics gathered

PROMPT ============================================================================
PROMPT Verification
PROMPT ============================================================================

SELECT 'Total customers: ' || COUNT(*) AS info FROM customers;
SELECT 'Total orders: ' || COUNT(*) AS info FROM orders;

PROMPT
PROMPT ============================================================================
PROMPT Setup Complete!
PROMPT ============================================================================
PROMPT
PROMPT Connection Details:
PROMPT   Username: dq_test
PROMPT   Password: dq_test123
PROMPT   Host: localhost
PROMPT   Port: 1521
PROMPT   Service: XEPDB1 (NOT XE!)
PROMPT
PROMPT Test the connection:
PROMPT   python test_oracle_connection.py
PROMPT
PROMPT Run data quality analysis:
PROMPT   python data_quality_analysis.py --use-database --config-file dq_config_oracle.json
PROMPT
PROMPT ============================================================================

-- Display sample data
SELECT * FROM customers WHERE ROWNUM <= 5;

EXIT;

-- Made with Bob
