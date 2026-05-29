-- ============================================================================
-- Oracle Database Sample Data for DQ Analysis Testing
-- ============================================================================
-- 
-- This script creates a comprehensive test dataset with both good and bad data
-- to demonstrate all DQ analysis capabilities.
--
-- Usage:
--   sqlplus dq_test/dq_test123@localhost:1521/XE @setup_oracle_dq_sample_data.sql
--
-- Or via Docker:
--   docker cp setup_oracle_dq_sample_data.sql oracle-xe:/tmp/
--   docker exec -it oracle-xe sqlplus dq_test/dq_test123@XE @/tmp/setup_oracle_dq_sample_data.sql
--
-- ============================================================================

SET ECHO ON
SET FEEDBACK ON
SET SERVEROUTPUT ON
SET LINESIZE 200

PROMPT ============================================================================
PROMPT Creating Sample Table: CUSTOMER_DATA
PROMPT ============================================================================

-- Drop table if exists
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE customer_data CASCADE CONSTRAINTS';
    DBMS_OUTPUT.PUT_LINE('Existing table dropped');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN -- Table does not exist
            RAISE;
        END IF;
        DBMS_OUTPUT.PUT_LINE('Table does not exist, creating new');
END;
/

-- Create comprehensive customer data table
CREATE TABLE customer_data (
    customer_id NUMBER(10) PRIMARY KEY,
    customer_name VARCHAR2(100),
    email VARCHAR2(100),
    phone VARCHAR2(20),
    country VARCHAR2(50),
    state VARCHAR2(50),
    city VARCHAR2(50),
    postal_code VARCHAR2(10),
    registration_date DATE,
    last_purchase_date DATE,
    purchase_amount NUMBER(10,2),
    total_orders NUMBER(5),
    credit_score NUMBER(3),
    account_status VARCHAR2(20),
    is_active NUMBER(1),
    customer_segment VARCHAR2(20),
    created_date DATE DEFAULT SYSDATE,
    updated_date DATE DEFAULT SYSDATE
);

PROMPT Table 'customer_data' created successfully

PROMPT ============================================================================
PROMPT Inserting Sample Data (Good + Bad Quality)
PROMPT ============================================================================

-- ============================================================================
-- GOOD QUALITY DATA (Records 1-20)
-- ============================================================================

PROMPT Inserting GOOD quality records (1-20)...

-- Perfect records
INSERT INTO customer_data VALUES (1, 'John Smith', 'john.smith@example.com', '5551234567', 'USA', 'California', 'Los Angeles', '90001', DATE '2023-01-15', DATE '2024-05-20', 1500.50, 25, 750, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (2, 'Jane Doe', 'jane.doe@example.com', '5552345678', 'USA', 'New York', 'New York', '10001', DATE '2023-02-20', DATE '2024-05-18', 2000.00, 30, 800, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (3, 'Bob Johnson', 'bob.johnson@example.com', '5553456789', 'Canada', 'Ontario', 'Toronto', 'M5H2N2', DATE '2023-03-10', DATE '2024-05-15', 500.00, 10, 680, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (4, 'Alice Williams', 'alice.williams@example.com', '5554567890', 'UK', 'England', 'London', 'SW1A1AA', DATE '2023-04-05', DATE '2024-05-10', 3000.00, 45, 820, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (5, 'Charlie Brown', 'charlie.brown@example.com', '5555678901', 'Australia', 'NSW', 'Sydney', '2000', DATE '2023-05-12', DATE '2024-05-05', 750.00, 15, 700, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (6, 'Diana Prince', 'diana.prince@example.com', '5556789012', 'USA', 'Texas', 'Houston', '77001', DATE '2023-06-18', DATE '2024-04-30', 1200.00, 20, 760, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (7, 'Edward Norton', 'edward.norton@example.com', '5557890123', 'Germany', 'Bavaria', 'Munich', '80331', DATE '2023-07-22', DATE '2024-04-25', 1800.00, 28, 790, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (8, 'Fiona Green', 'fiona.green@example.com', '5558901234', 'France', 'Ile-de-France', 'Paris', '75001', DATE '2023-08-30', DATE '2024-04-20', 950.00, 18, 720, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (9, 'George Miller', 'george.miller@example.com', '5559012345', 'USA', 'Florida', 'Miami', '33101', DATE '2023-09-14', DATE '2024-04-15', 2200.00, 35, 810, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (10, 'Helen Clark', 'helen.clark@example.com', '5550123456', 'New Zealand', 'Auckland', 'Auckland', '1010', DATE '2023-10-08', DATE '2024-04-10', 600.00, 12, 690, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);

-- More good records
INSERT INTO customer_data VALUES (11, 'Ivan Petrov', 'ivan.petrov@example.com', '5551234560', 'Russia', 'Moscow', 'Moscow', '101000', DATE '2023-11-20', DATE '2024-04-05', 1100.00, 22, 740, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (12, 'Julia Santos', 'julia.santos@example.com', '5552345670', 'Brazil', 'Sao Paulo', 'Sao Paulo', '01000', DATE '2023-12-15', DATE '2024-03-30', 850.00, 16, 710, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (13, 'Kevin Lee', 'kevin.lee@example.com', '5553456780', 'South Korea', 'Seoul', 'Seoul', '04524', DATE '2024-01-10', DATE '2024-03-25', 1400.00, 24, 770, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (14, 'Laura Martinez', 'laura.martinez@example.com', '5554567891', 'Spain', 'Madrid', 'Madrid', '28001', DATE '2024-02-05', DATE '2024-03-20', 1650.00, 27, 780, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (15, 'Michael Chen', 'michael.chen@example.com', '5555678902', 'China', 'Shanghai', 'Shanghai', '200000', DATE '2024-03-01', DATE '2024-03-15', 900.00, 17, 730, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (16, 'Nancy White', 'nancy.white@example.com', '5556789023', 'USA', 'Illinois', 'Chicago', '60601', DATE '2024-03-15', DATE '2024-03-10', 1300.00, 23, 750, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (17, 'Oliver Taylor', 'oliver.taylor@example.com', '5557890134', 'UK', 'Scotland', 'Edinburgh', 'EH11AA', DATE '2024-04-01', DATE '2024-03-05', 1750.00, 29, 795, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (18, 'Patricia Moore', 'patricia.moore@example.com', '5558901245', 'Canada', 'Quebec', 'Montreal', 'H2X1Y9', DATE '2024-04-10', DATE '2024-02-28', 650.00, 13, 695, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (19, 'Quinn Anderson', 'quinn.anderson@example.com', '5559012356', 'USA', 'Washington', 'Seattle', '98101', DATE '2024-04-20', DATE '2024-02-25', 2100.00, 33, 805, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE);
INSERT INTO customer_data VALUES (20, 'Rachel Kim', 'rachel.kim@example.com', '5550123467', 'Japan', 'Tokyo', 'Tokyo', '100-0001', DATE '2024-05-01', DATE '2024-02-20', 1050.00, 19, 725, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE);

-- ============================================================================
-- BAD QUALITY DATA - NULL/MISSING VALUES (Records 21-30)
-- ============================================================================

PROMPT Inserting BAD quality records - NULL/MISSING values (21-30)...

INSERT INTO customer_data VALUES (21, NULL, 'missing.name@example.com', '5551111111', 'USA', 'California', 'San Diego', '92101', DATE '2024-01-15', DATE '2024-02-15', 800.00, 14, 715, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing name
INSERT INTO customer_data VALUES (22, 'Sarah Connor', NULL, '5552222222', 'USA', 'Arizona', 'Phoenix', '85001', DATE '2024-01-20', DATE '2024-02-10', 950.00, 16, 735, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing email
INSERT INTO customer_data VALUES (23, 'Tom Hardy', 'tom.hardy@example.com', NULL, 'UK', 'England', 'Manchester', 'M11AA', DATE '2024-01-25', DATE '2024-02-05', 1100.00, 18, 745, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing phone
INSERT INTO customer_data VALUES (24, 'Uma Thurman', 'uma.thurman@example.com', '5554444444', NULL, NULL, NULL, NULL, DATE '2024-02-01', DATE '2024-01-30', 700.00, 12, 705, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing location
INSERT INTO customer_data VALUES (25, 'Victor Stone', 'victor.stone@example.com', '5555555555', 'USA', 'Nevada', 'Las Vegas', '89101', NULL, DATE '2024-01-25', 1250.00, 21, 755, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing registration date
INSERT INTO customer_data VALUES (26, 'Wendy Davis', 'wendy.davis@example.com', '5556666666', 'Canada', 'Alberta', 'Calgary', 'T2P0A8', DATE '2024-02-10', NULL, 850.00, 15, 720, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing last purchase
INSERT INTO customer_data VALUES (27, 'Xavier Woods', 'xavier.woods@example.com', '5557777777', 'USA', 'Oregon', 'Portland', '97201', DATE '2024-02-15', DATE '2024-01-20', NULL, 0, 680, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing purchase amount
INSERT INTO customer_data VALUES (28, 'Yolanda Martinez', 'yolanda.martinez@example.com', '5558888888', 'Mexico', 'Mexico City', 'Mexico City', '01000', DATE '2024-02-20', DATE '2024-01-15', 600.00, NULL, 690, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing total orders
INSERT INTO customer_data VALUES (29, 'Zachary Taylor', 'zachary.taylor@example.com', '5559999999', 'USA', 'Colorado', 'Denver', '80201', DATE '2024-02-25', DATE '2024-01-10', 1400.00, 23, NULL, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing credit score
INSERT INTO customer_data VALUES (30, 'Amy Adams', 'amy.adams@example.com', '5550000000', 'USA', 'Massachusetts', 'Boston', '02101', DATE '2024-03-01', DATE '2024-01-05', 950.00, 17, 725, NULL, 1, 'STANDARD', SYSDATE, SYSDATE); -- Missing account status

-- ============================================================================
-- BAD QUALITY DATA - INVALID FORMATS (Records 31-40)
-- ============================================================================

PROMPT Inserting BAD quality records - INVALID formats (31-40)...

INSERT INTO customer_data VALUES (31, 'Ben Parker', 'invalid-email', '5551231234', 'USA', 'Georgia', 'Atlanta', '30301', DATE '2024-03-05', DATE '2023-12-30', 800.00, 14, 710, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid email format
INSERT INTO customer_data VALUES (32, 'Carol Danvers', 'carol@invalid', '5552342345', 'USA', 'Michigan', 'Detroit', '48201', DATE '2024-03-10', DATE '2023-12-25', 1100.00, 19, 740, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid email domain
INSERT INTO customer_data VALUES (33, 'David Banner', 'david.banner@example.com', '123', 'USA', 'Ohio', 'Cleveland', '44101', DATE '2024-03-15', DATE '2023-12-20', 650.00, 11, 695, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid phone (too short)
INSERT INTO customer_data VALUES (34, 'Emma Frost', 'emma.frost@example.com', 'ABCDEFGHIJ', 'USA', 'Pennsylvania', 'Philadelphia', '19101', DATE '2024-03-20', DATE '2023-12-15', 1300.00, 22, 760, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid phone (letters)
INSERT INTO customer_data VALUES (35, 'Frank Castle', 'frank.castle@example.com', '5555555555', '123', 'Unknown', 'Unknown', '00000', DATE '2024-03-25', DATE '2023-12-10', 900.00, 16, 720, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid country
INSERT INTO customer_data VALUES (36, 'Gwen Stacy', 'gwen.stacy@example.com', '5556786789', 'USA', 'Virginia', 'Richmond', 'INVALID', DATE '2024-03-30', DATE '2023-12-05', 1050.00, 18, 735, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid postal code
INSERT INTO customer_data VALUES (37, 'Hank Pym', 'hank.pym@example.com', '5557897890', 'USA', 'Tennessee', 'Nashville', '37201', DATE '2024-04-05', DATE '2023-11-30', 750.00, 13, 705, 'INVALID_STATUS', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid account status
INSERT INTO customer_data VALUES (38, 'Iris West', 'iris.west@example.com', '5558908901', 'USA', 'Missouri', 'Kansas City', '64101', DATE '2024-04-10', DATE '2023-11-25', 1200.00, 20, 750, 'ACTIVE', 5, 'STANDARD', SYSDATE, SYSDATE); -- Invalid is_active (should be 0 or 1)
INSERT INTO customer_data VALUES (39, 'James Rhodes', 'james.rhodes@example.com', '5559019012', 'USA', 'Wisconsin', 'Milwaukee', '53201', DATE '2024-04-15', DATE '2023-11-20', 850.00, 15, 715, 'ACTIVE', 1, 'INVALID_SEGMENT', SYSDATE, SYSDATE); -- Invalid customer segment
INSERT INTO customer_data VALUES (40, 'Karen Page', 'karen@page@example.com', '5550120123', 'USA', 'Minnesota', 'Minneapolis', '55401', DATE '2024-04-20', DATE '2023-11-15', 1400.00, 24, 770, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Invalid email (double @)

-- ============================================================================
-- BAD QUALITY DATA - OUTLIERS & ANOMALIES (Records 41-50)
-- ============================================================================

PROMPT Inserting BAD quality records - OUTLIERS & ANOMALIES (41-50)...

INSERT INTO customer_data VALUES (41, 'Leo Fitz', 'leo.fitz@example.com', '5551231235', 'USA', 'Indiana', 'Indianapolis', '46201', DATE '2024-04-25', DATE '2023-11-10', -500.00, 10, 720, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Negative purchase amount
INSERT INTO customer_data VALUES (42, 'May Parker', 'may.parker@example.com', '5552342346', 'USA', 'Kentucky', 'Louisville', '40201', DATE '2024-04-30', DATE '2023-11-05', 999999.99, 5, 730, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Extremely high purchase amount
INSERT INTO customer_data VALUES (43, 'Nick Fury', 'nick.fury@example.com', '5553453457', 'USA', 'Louisiana', 'New Orleans', '70112', DATE '2024-05-05', DATE '2023-10-30', 1000.00, -5, 740, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Negative orders
INSERT INTO customer_data VALUES (44, 'Ororo Munroe', 'ororo.munroe@example.com', '5554564568', 'USA', 'Oklahoma', 'Oklahoma City', '73101', DATE '2024-05-10', DATE '2023-10-25', 800.00, 10000, 750, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Unrealistic order count
INSERT INTO customer_data VALUES (45, 'Peter Quill', 'peter.quill@example.com', '5555675679', 'USA', 'Connecticut', 'Hartford', '06101', DATE '2024-05-15', DATE '2023-10-20', 1200.00, 20, 1000, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Credit score too high (max 850)
INSERT INTO customer_data VALUES (46, 'Quentin Beck', 'quentin.beck@example.com', '5556786780', 'USA', 'Iowa', 'Des Moines', '50301', DATE '2024-05-20', DATE '2023-10-15', 900.00, 15, 200, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Credit score too low
INSERT INTO customer_data VALUES (47, 'Raven Darkholme', 'raven.darkholme@example.com', '5557897891', 'USA', 'Arkansas', 'Little Rock', '72201', DATE '1900-01-01', DATE '2023-10-10', 1100.00, 18, 720, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Registration date too old
INSERT INTO customer_data VALUES (48, 'Scott Summers', 'scott.summers@example.com', '5558908902', 'USA', 'Mississippi', 'Jackson', '39201', DATE '2030-12-31', DATE '2023-10-05', 850.00, 14, 710, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Future registration date
INSERT INTO customer_data VALUES (49, 'Tony Stark', 'tony.stark@example.com', '5559019013', 'USA', 'Kansas', 'Wichita', '67201', DATE '2024-01-01', DATE '2025-12-31', 2000.00, 30, 800, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE); -- Future last purchase date
INSERT INTO customer_data VALUES (50, 'Ultron Prime', 'ultron@example.com', '5550120124', 'USA', 'Nebraska', 'Omaha', '68101', DATE '2024-05-25', DATE '2020-01-01', 750.00, 12, 690, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Last purchase before registration

-- ============================================================================
-- BAD QUALITY DATA - DUPLICATES (Records 51-55)
-- ============================================================================

PROMPT Inserting BAD quality records - DUPLICATES (51-55)...

-- Exact duplicates of good records
INSERT INTO customer_data VALUES (51, 'John Smith', 'john.smith@example.com', '5551234567', 'USA', 'California', 'Los Angeles', '90001', DATE '2023-01-15', DATE '2024-05-20', 1500.50, 25, 750, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE); -- Duplicate of ID 1
INSERT INTO customer_data VALUES (52, 'Jane Doe', 'jane.doe@example.com', '5552345678', 'USA', 'New York', 'New York', '10001', DATE '2023-02-20', DATE '2024-05-18', 2000.00, 30, 800, 'ACTIVE', 1, 'PREMIUM', SYSDATE, SYSDATE); -- Duplicate of ID 2
INSERT INTO customer_data VALUES (53, 'Bob Johnson', 'bob.johnson@example.com', '5553456789', 'Canada', 'Ontario', 'Toronto', 'M5H2N2', DATE '2023-03-10', DATE '2024-05-15', 500.00, 10, 680, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Duplicate of ID 3

-- Partial duplicates (same email, different data)
INSERT INTO customer_data VALUES (54, 'John Smith Jr', 'john.smith@example.com', '5559999998', 'USA', 'California', 'San Francisco', '94101', DATE '2024-01-01', DATE '2024-03-01', 1000.00, 15, 730, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Duplicate email
INSERT INTO customer_data VALUES (55, 'Jane Doe Smith', 'jane.doe@example.com', '5559999997', 'USA', 'New York', 'Buffalo', '14201', DATE '2024-02-01', DATE '2024-03-15', 1200.00, 18, 745, 'ACTIVE', 1, 'STANDARD', SYSDATE, SYSDATE); -- Duplicate email

COMMIT;

PROMPT ============================================================================
PROMPT Creating Indexes for Performance
PROMPT ============================================================================

CREATE INDEX idx_customer_email ON customer_data(email);
CREATE INDEX idx_customer_country ON customer_data(country);
CREATE INDEX idx_customer_status ON customer_data(account_status);
CREATE INDEX idx_customer_segment ON customer_data(customer_segment);

PROMPT Indexes created successfully

PROMPT ============================================================================
PROMPT Gathering Statistics
PROMPT ============================================================================

BEGIN
    DBMS_STATS.GATHER_TABLE_STATS(USER, 'CUSTOMER_DATA');
END;
/

PROMPT Statistics gathered

PROMPT ============================================================================
PROMPT Data Summary
PROMPT ============================================================================

SELECT 'Total Records: ' || COUNT(*) AS summary FROM customer_data;
SELECT 'Good Quality Records: 20' AS summary FROM DUAL;
SELECT 'Records with NULL values: 10' AS summary FROM DUAL;
SELECT 'Records with Invalid Formats: 10' AS summary FROM DUAL;
SELECT 'Records with Outliers: 10' AS summary FROM DUAL;
SELECT 'Duplicate Records: 5' AS summary FROM DUAL;

PROMPT
PROMPT ============================================================================
PROMPT Sample Data Preview
PROMPT ============================================================================

SELECT customer_id, customer_name, email, country, purchase_amount, account_status
FROM customer_data
WHERE ROWNUM <= 10
ORDER BY customer_id;

PROMPT
PROMPT ============================================================================
PROMPT Setup Complete!
PROMPT ============================================================================
PROMPT
PROMPT Table: customer_data
PROMPT Total Records: 55
PROMPT   - Good Quality: 20 records (IDs 1-20)
PROMPT   - NULL/Missing: 10 records (IDs 21-30)
PROMPT   - Invalid Formats: 10 records (IDs 31-40)
PROMPT   - Outliers: 10 records (IDs 41-50)
PROMPT   - Duplicates: 5 records (IDs 51-55)
PROMPT
PROMPT Next Steps:
PROMPT 1. Test connection:
PROMPT    python DQ_Analysis_code/test_oracle_dq_connection.py
PROMPT
PROMPT 2. Run DQ Analysis:
PROMPT    python DQ_Analysis_code/data_quality_analysis.py --use-database --config-file DQ_Analysis_code/oracle_connection_config.json --generate-dashboard
PROMPT
PROMPT 3. Or use the automated script:
PROMPT    DQ_Analysis_code\run_oracle_dq_analysis.bat
PROMPT
PROMPT ============================================================================

-- Made with Bob