SET PAGESIZE 50
SET LINESIZE 200
COLUMN customer_id FORMAT 999
COLUMN customer_name FORMAT A20
COLUMN email FORMAT A30
COLUMN phone FORMAT A15
COLUMN country FORMAT A15
COLUMN purchase_amount FORMAT 9999999.99

PROMPT ================================================================================
PROMPT All Customers Data
PROMPT ================================================================================

SELECT customer_id, customer_name, email, phone, country, purchase_amount, is_active
FROM customers 
ORDER BY customer_id;

PROMPT
PROMPT ================================================================================
PROMPT Summary Statistics
PROMPT ================================================================================

SELECT 
    COUNT(*) as total_records,
    COUNT(email) as records_with_email,
    COUNT(*) - COUNT(email) as records_without_email,
    COUNT(customer_name) as records_with_name,
    MIN(purchase_amount) as min_amount,
    MAX(purchase_amount) as max_amount,
    AVG(purchase_amount) as avg_amount
FROM customers;

EXIT;

-- Made with Bob
