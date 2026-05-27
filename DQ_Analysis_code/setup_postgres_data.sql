-- PostgreSQL Test Data Setup Script
-- Creates customers table with intentional data quality issues

-- Drop table if exists
DROP TABLE IF EXISTS customers;

-- Create customers table
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
-- Record 1: Good record
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('John Doe', 'john@example.com', '555-0001', '2024-01-15', 1500.00, 1, 'US');

-- Record 2: Good record
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Jane Smith', 'jane@example.com', '555-0002', '2024-02-20', 2500.50, 1, 'UK');

-- Record 3: NULL email, negative amount (2 issues)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Bob Johnson', NULL, '555-0003', '2024-03-10', -100.00, 1, 'CA');

-- Record 4: Invalid email format, NULL phone (2 issues)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Alice Brown', 'invalid-email', NULL, '2024-04-05', 3500.00, 2, 'AU');

-- Record 5: NULL date, outlier amount (2 issues)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Charlie Wilson', 'charlie@test.com', '555-0005', NULL, 999999.99, 1, 'IN');

-- Record 6: Duplicate name (potential duplicate)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('John Doe', 'john2@example.com', '555-0006', '2024-05-01', 1200.00, 1, 'US');

-- Show record count
SELECT COUNT(*) as total_records FROM customers;

-- Show all records
SELECT * FROM customers;

-- Made with Bob
