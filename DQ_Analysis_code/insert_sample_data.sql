-- ============================================================================
-- Sample Data for Data Quality Analysis
-- Mix of GOOD and BAD data to demonstrate DQ scoring
-- ============================================================================

-- Clear existing data
TRUNCATE TABLE customers;

-- ============================================================================
-- GOOD RECORDS (10 records - 50% of total)
-- ============================================================================

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('John Doe', 'john.doe@example.com', '555-0001', '2024-01-15', 1500.00, 1, 'US');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Jane Smith', 'jane.smith@example.com', '555-0002', '2024-02-20', 2500.50, 1, 'UK');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Michael Johnson', 'michael.j@company.com', '555-0003', '2024-03-10', 3200.00, 1, 'CA');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Sarah Williams', 'sarah.w@business.org', '555-0004', '2024-04-05', 1800.75, 1, 'AU');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('David Brown', 'david.brown@email.com', '555-0005', '2024-05-12', 2100.00, 1, 'IN');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Emily Davis', 'emily.davis@mail.com', '555-0006', '2024-06-18', 1950.25, 1, 'US');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Robert Miller', 'robert.m@domain.com', '555-0007', '2024-07-22', 2800.00, 1, 'UK');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Lisa Anderson', 'lisa.anderson@web.com', '555-0008', '2024-08-30', 1650.50, 1, 'CA');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('James Wilson', 'james.wilson@site.com', '555-0009', '2024-09-14', 2250.00, 1, 'AU');

INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Maria Garcia', 'maria.garcia@email.net', '555-0010', '2024-10-08', 1750.75, 1, 'IN');

-- ============================================================================
-- BAD RECORDS (10 records - 50% of total)
-- Demonstrating various data quality issues
-- ============================================================================

-- Record 11: NULL email (Missing mandatory field)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Bob Johnson', NULL, '555-0011', '2024-03-10', 1200.00, 1, 'CA');

-- Record 12: Invalid email format (Pattern violation)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Alice Brown', 'invalid-email-no-at', '555-0012', '2024-04-05', 3500.00, 2, 'AU');

-- Record 13: NULL phone (Missing data)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Charlie Wilson', 'charlie@test.com', NULL, '2024-05-20', 2200.00, 1, 'IN');

-- Record 14: NULL registration date (Missing mandatory field)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Diana Prince', 'diana.prince@email.com', '555-0014', NULL, 1900.00, 1, 'US');

-- Record 15: Negative purchase amount (Business rule violation)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Edward Norton', 'edward.n@mail.com', '555-0015', '2024-06-15', -500.00, 1, 'UK');

-- Record 16: Outlier - Very high purchase amount (Statistical outlier)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Fiona Apple', 'fiona.apple@email.com', '555-0016', '2024-07-20', 999999.99, 1, 'CA');

-- Record 17: Invalid email format (No domain)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('George Martin', 'george@', '555-0017', '2024-08-25', 1800.00, 1, 'AU');

-- Record 18: Multiple issues - NULL email AND negative amount
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Helen Troy', NULL, '555-0018', '2024-09-10', -250.00, 1, 'IN');

-- Record 19: Invalid email (Missing @ symbol)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('Ivan Petrov', 'ivanpetrov.com', '555-0019', '2024-10-15', 2100.00, 1, 'US');

-- Record 20: Duplicate name (Potential duplicate record)
INSERT INTO customers (customer_name, email, phone, registration_date, purchase_amount, is_active, country_code) 
VALUES ('John Doe', 'john.doe2@example.com', '555-0020', '2024-11-01', 1600.00, 1, 'US');

-- ============================================================================
-- Summary Statistics
-- ============================================================================

-- Show total record count
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN email IS NOT NULL AND email LIKE '%@%.%' THEN 1 END) as valid_emails,
    COUNT(CASE WHEN email IS NULL OR email NOT LIKE '%@%.%' THEN 1 END) as invalid_emails,
    COUNT(CASE WHEN purchase_amount < 0 THEN 1 END) as negative_amounts,
    COUNT(CASE WHEN purchase_amount > 100000 THEN 1 END) as outlier_amounts,
    COUNT(CASE WHEN registration_date IS NULL THEN 1 END) as missing_dates
FROM customers;

-- Show all records
SELECT 
    customer_id,
    customer_name,
    email,
    phone,
    registration_date,
    purchase_amount,
    is_active,
    country_code,
    CASE 
        WHEN email IS NULL THEN 'NULL Email'
        WHEN email NOT LIKE '%@%' THEN 'Invalid Email'
        WHEN purchase_amount < 0 THEN 'Negative Amount'
        WHEN purchase_amount > 100000 THEN 'Outlier Amount'
        WHEN registration_date IS NULL THEN 'Missing Date'
        WHEN phone IS NULL THEN 'Missing Phone'
        ELSE 'Good Record'
    END as data_quality_status
FROM customers
ORDER BY customer_id;

-- ============================================================================
-- Expected Data Quality Score: ~50%
-- Good Records: 10 out of 20 = 50%
-- Bad Records: 10 out of 20 = 50%
-- ============================================================================

-- Made with Bob
