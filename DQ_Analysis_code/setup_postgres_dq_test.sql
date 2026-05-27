-- =====================================================
-- PostgreSQL Database Setup for Data Quality Testing
-- =====================================================
-- This script creates a customer_data table and inserts
-- both good and bad records for DQ analysis testing
-- =====================================================

-- Drop table if exists (for clean setup)
DROP TABLE IF EXISTS customer_data CASCADE;

-- Create customer_data table
CREATE TABLE customer_data (
    customer_id NUMERIC(10,1),
    customer_name VARCHAR(100),
    email VARCHAR(100),
    age INTEGER,
    salary NUMERIC(12,2),
    join_date DATE,
    country_code VARCHAR(10),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comments to table and columns
COMMENT ON TABLE customer_data IS 'Customer data table for DQ analysis testing';
COMMENT ON COLUMN customer_data.customer_id IS 'Unique customer identifier';
COMMENT ON COLUMN customer_data.customer_name IS 'Full name of the customer';
COMMENT ON COLUMN customer_data.email IS 'Customer email address';
COMMENT ON COLUMN customer_data.age IS 'Customer age in years';
COMMENT ON COLUMN customer_data.salary IS 'Annual salary in USD';
COMMENT ON COLUMN customer_data.join_date IS 'Date when customer joined';
COMMENT ON COLUMN customer_data.country_code IS 'ISO country code (2-3 chars)';
COMMENT ON COLUMN customer_data.status IS 'Customer status (ACTIVE/INACTIVE)';

-- =====================================================
-- INSERT GOOD RECORDS (Clean data for baseline)
-- =====================================================

INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1001.0, 'John Doe', 'john.doe@test.com', 29, 55000, '2024-01-10', 'IN', 'ACTIVE'),
(1005.0, 'Emma Wilson', 'emma.wilson@test.com', 35, 68000, '2023-08-15', 'US', 'ACTIVE'),
(1006.0, 'Robert Brown', 'robert.brown@test.com', 42, 75000, '2022-03-20', 'UK', 'INACTIVE'),
(1011.0, 'Lisa Anderson', 'lisa.anderson@test.com', 31, 62000, '2024-02-01', 'IN', 'ACTIVE'),
(1012.0, 'James Taylor', 'james.taylor@test.com', 38, 71000, '2023-11-10', 'US', 'ACTIVE');

-- =====================================================
-- INSERT BAD RECORDS (Data quality issues)
-- =====================================================

-- Record with invalid email format and negative age
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1002.0, 'Sara Khan', 'sara@test', -5, 62000, '2024-01-01', 'US', 'ACTIVE');

-- Record with multiple NULL/missing values
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1003.0, NULL, NULL, 35, NULL, NULL, 'IN', 'INACTIVE');

-- Record with age out of range and negative salary (duplicate ID - first instance)
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1004.0, 'Mike Ross', 'mike.ross@test.com', 200, -1000, '2023-05-20', 'UK', 'UNKNOWN');

-- Record with duplicate customer_id (second instance)
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1004.0, 'Mike Ross', 'mike.ross@test.com', 41, 72000, '2023-05-20', 'UK', 'ACTIVE');

-- Record with NULL customer_id and invalid country code
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(NULL, 'David Lee', 'david@test.com', NULL, 81000, NULL, 'INDIA', NULL);

-- Record with missing name and invalid email
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1007.0, NULL, 'anna.com', 28, 0, '2025-02-15', 'IN', 'ACTIVE');

-- Record with missing email and salary outlier
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1008.0, 'Anna', NULL, 32, 9500000, '2022-11-30', NULL, 'INACTIVE');

-- Record with invalid data types (stored as strings in VARCHAR columns)
-- Note: In PostgreSQL, we need to handle type mismatches differently
-- This record has invalid country code and status
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1009.0, 'Chris', 'chris@test.com', NULL, 67000, NULL, '123', '123');

-- Record with NULL salary and missing join_date
INSERT INTO customer_data (customer_id, customer_name, email, age, salary, join_date, country_code, status) VALUES
(1010.0, 'Tom', 'tom@test.com', 45, NULL, NULL, 'IN', NULL);

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Count total records
SELECT 'Total Records' AS metric, COUNT(*) AS count FROM customer_data;

-- Count good vs bad records (approximate)
SELECT 
    'Good Records' AS category, 
    COUNT(*) AS count 
FROM customer_data 
WHERE customer_id IN (1001.0, 1005.0, 1006.0, 1011.0, 1012.0)
UNION ALL
SELECT 
    'Bad Records' AS category, 
    COUNT(*) AS count 
FROM customer_data 
WHERE customer_id NOT IN (1001.0, 1005.0, 1006.0, 1011.0, 1012.0) 
   OR customer_id IS NULL;

-- Show all records
SELECT * FROM customer_data ORDER BY customer_id NULLS LAST;

-- Identify duplicate customer_ids
SELECT 
    customer_id, 
    COUNT(*) AS duplicate_count
FROM customer_data
WHERE customer_id IS NOT NULL
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- Identify NULL values by column
SELECT 
    'customer_id' AS column_name, COUNT(*) AS null_count FROM customer_data WHERE customer_id IS NULL
UNION ALL
SELECT 'customer_name', COUNT(*) FROM customer_data WHERE customer_name IS NULL
UNION ALL
SELECT 'email', COUNT(*) FROM customer_data WHERE email IS NULL
UNION ALL
SELECT 'age', COUNT(*) FROM customer_data WHERE age IS NULL
UNION ALL
SELECT 'salary', COUNT(*) FROM customer_data WHERE salary IS NULL
UNION ALL
SELECT 'join_date', COUNT(*) FROM customer_data WHERE join_date IS NULL
UNION ALL
SELECT 'country_code', COUNT(*) FROM customer_data WHERE country_code IS NULL
UNION ALL
SELECT 'status', COUNT(*) FROM customer_data WHERE status IS NULL;

-- =====================================================
-- EXPORT DATA FOR DQ ANALYSIS
-- =====================================================
-- To export data to CSV for Python DQ analysis:
-- \copy customer_data TO '/tmp/customer_data_export.csv' WITH CSV HEADER;

-- Made with Bob
