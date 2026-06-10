# Oracle Sample Data for DQ Analysis Testing

## 📊 Overview

This document describes the sample data created for testing the Data Quality (DQ) analysis tool with Oracle database. The dataset is specifically designed to demonstrate all DQ analysis capabilities by including both good and bad quality data.

---

## 📋 Table Structure

**Table Name:** `customer_data`

### Columns

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| customer_id | NUMBER(10) | Primary key, unique customer identifier |
| customer_name | VARCHAR2(100) | Customer full name |
| email | VARCHAR2(100) | Customer email address |
| phone | VARCHAR2(20) | Customer phone number |
| country | VARCHAR2(50) | Customer country |
| state | VARCHAR2(50) | Customer state/province |
| city | VARCHAR2(50) | Customer city |
| postal_code | VARCHAR2(10) | Postal/ZIP code |
| registration_date | DATE | Date customer registered |
| last_purchase_date | DATE | Date of last purchase |
| purchase_amount | NUMBER(10,2) | Total purchase amount |
| total_orders | NUMBER(5) | Total number of orders |
| credit_score | NUMBER(3) | Customer credit score (300-850) |
| account_status | VARCHAR2(20) | Account status (ACTIVE, INACTIVE, SUSPENDED) |
| is_active | NUMBER(1) | Active flag (0 or 1) |
| customer_segment | VARCHAR2(20) | Customer segment (PREMIUM, STANDARD) |
| created_date | DATE | Record creation date |
| updated_date | DATE | Record last update date |

---

## 📈 Data Distribution

**Total Records:** 55

### Quality Breakdown

| Category | Count | Percentage | Record IDs |
|----------|-------|------------|------------|
| ✅ **Good Quality** | 20 | 36% | 1-20 |
| ❌ **NULL/Missing Values** | 10 | 18% | 21-30 |
| ❌ **Invalid Formats** | 10 | 18% | 31-40 |
| ❌ **Outliers & Anomalies** | 10 | 18% | 41-50 |
| ❌ **Duplicates** | 5 | 9% | 51-55 |

---

## ✅ Good Quality Data (Records 1-20)

These records have:
- All mandatory fields populated
- Valid email formats
- Valid phone numbers (10 digits)
- Valid country names
- Reasonable purchase amounts ($500-$3000)
- Valid credit scores (680-820)
- Proper date ranges
- Valid account status (ACTIVE)
- Valid customer segments (PREMIUM, STANDARD)

**Example:**
```sql
customer_id: 1
customer_name: John Smith
email: john.smith@example.com
phone: 5551234567
country: USA
purchase_amount: 1500.50
credit_score: 750
```

---

## ❌ Bad Quality Data

### 1. NULL/Missing Values (Records 21-30)

Each record has one or more NULL values in critical fields:

| Record ID | Missing Field | Impact |
|-----------|--------------|--------|
| 21 | customer_name | Mandatory field violation |
| 22 | email | Mandatory field violation |
| 23 | phone | Contact information missing |
| 24 | country, state, city, postal_code | Location data missing |
| 25 | registration_date | Temporal data missing |
| 26 | last_purchase_date | Activity tracking incomplete |
| 27 | purchase_amount | Financial data missing |
| 28 | total_orders | Order history incomplete |
| 29 | credit_score | Risk assessment data missing |
| 30 | account_status | Status information missing |

### 2. Invalid Formats (Records 31-40)

Records with format violations:

| Record ID | Issue | Example |
|-----------|-------|---------|
| 31 | Invalid email format | "invalid-email" (no @ or domain) |
| 32 | Invalid email domain | "carol@invalid" (incomplete domain) |
| 33 | Phone too short | "123" (should be 10 digits) |
| 34 | Phone with letters | "ABCDEFGHIJ" (should be numeric) |
| 35 | Invalid country | "123" (numeric country code) |
| 36 | Invalid postal code | "INVALID" (wrong format) |
| 37 | Invalid account status | "INVALID_STATUS" (not in allowed values) |
| 38 | Invalid is_active | 5 (should be 0 or 1) |
| 39 | Invalid customer segment | "INVALID_SEGMENT" (not in allowed values) |
| 40 | Malformed email | "karen@page@example.com" (double @) |

### 3. Outliers & Anomalies (Records 41-50)

Records with statistical outliers or logical anomalies:

| Record ID | Issue | Value | Expected Range |
|-----------|-------|-------|----------------|
| 41 | Negative purchase amount | -$500.00 | > $0 |
| 42 | Extremely high purchase | $999,999.99 | $0-$100,000 |
| 43 | Negative order count | -5 | >= 0 |
| 44 | Unrealistic order count | 10,000 | 0-1000 |
| 45 | Credit score too high | 1000 | 300-850 |
| 46 | Credit score too low | 200 | 300-850 |
| 47 | Registration date too old | 1900-01-01 | Recent dates |
| 48 | Future registration date | 2030-12-31 | <= Today |
| 49 | Future last purchase | 2025-12-31 | <= Today |
| 50 | Purchase before registration | Last purchase: 2020-01-01, Registration: 2024-05-25 | Logical inconsistency |

### 4. Duplicates (Records 51-55)

Duplicate records to test deduplication:

| Record ID | Type | Duplicate Of |
|-----------|------|--------------|
| 51 | Exact duplicate | Record 1 (John Smith) |
| 52 | Exact duplicate | Record 2 (Jane Doe) |
| 53 | Exact duplicate | Record 3 (Bob Johnson) |
| 54 | Partial duplicate (same email) | Record 1 (john.smith@example.com) |
| 55 | Partial duplicate (same email) | Record 2 (jane.doe@example.com) |

---

## 🔧 Loading the Sample Data

### Method 1: Automated Script (Recommended)

```bash
DQ_Analysis_code\load_oracle_sample_data.bat
```

This script will:
1. Check if Oracle container is running
2. Copy SQL script to container
3. Execute the script
4. Display summary

### Method 2: Manual Execution

**Step 1:** Copy SQL script to container
```bash
docker cp DQ_Analysis_code\setup_oracle_dq_sample_data.sql oracle-xe:/tmp/
```

**Step 2:** Execute the script
```bash
docker exec -it oracle-xe sqlplus dq_test/dq_test123@XE @/tmp/setup_oracle_dq_sample_data.sql
```

### Method 3: Direct SQL*Plus

```bash
docker exec -it oracle-xe sqlplus dq_test/dq_test123@XE
```

Then paste the contents of `setup_oracle_dq_sample_data.sql`

---

## 🧪 Testing DQ Analysis

### Step 1: Verify Data Loaded

```sql
SELECT COUNT(*) FROM customer_data;
-- Should return: 55

SELECT 
    CASE 
        WHEN customer_id BETWEEN 1 AND 20 THEN 'Good Quality'
        WHEN customer_id BETWEEN 21 AND 30 THEN 'NULL/Missing'
        WHEN customer_id BETWEEN 31 AND 40 THEN 'Invalid Format'
        WHEN customer_id BETWEEN 41 AND 50 THEN 'Outliers'
        WHEN customer_id BETWEEN 51 AND 55 THEN 'Duplicates'
    END AS category,
    COUNT(*) as count
FROM customer_data
GROUP BY 
    CASE 
        WHEN customer_id BETWEEN 1 AND 20 THEN 'Good Quality'
        WHEN customer_id BETWEEN 21 AND 30 THEN 'NULL/Missing'
        WHEN customer_id BETWEEN 31 AND 40 THEN 'Invalid Format'
        WHEN customer_id BETWEEN 41 AND 50 THEN 'Outliers'
        WHEN customer_id BETWEEN 51 AND 55 THEN 'Duplicates'
    END
ORDER BY 1;
```

### Step 2: Test Connection

```bash
python DQ_Analysis_code\test_oracle_dq_connection.py
```

### Step 3: Run DQ Analysis

```bash
DQ_Analysis_code\run_oracle_dq_analysis.bat
```

Or manually:
```bash
python DQ_Analysis_code\data_quality_analysis.py ^
    --use-database ^
    --config-file DQ_Analysis_code\oracle_connection_config.json ^
    --generate-dashboard
```

---

## 📊 Expected DQ Analysis Results

When you run the DQ analysis on this dataset, you should see:

### Overall Quality Score
- **Expected:** ~36-40% (20 good records out of 55)

### Issues Detected

1. **NULL/Missing Values:** 10+ issues
   - Missing customer names
   - Missing emails
   - Missing phone numbers
   - Missing location data
   - Missing dates

2. **Invalid Formats:** 10+ issues
   - Invalid email formats
   - Invalid phone numbers
   - Invalid country codes
   - Invalid postal codes
   - Invalid status values

3. **Outliers:** 10+ issues
   - Negative amounts
   - Extreme values
   - Out-of-range credit scores

4. **Date Anomalies:** 3+ issues
   - Future dates
   - Historical dates
   - Logical inconsistencies

5. **Duplicates:** 5 duplicate records
   - 3 exact duplicates
   - 2 partial duplicates (same email)

### Dashboard Metrics

The executive dashboard should show:
- **Completeness:** ~82% (45/55 records have all mandatory fields)
- **Validity:** ~64% (35/55 records have valid formats)
- **Accuracy:** ~82% (45/55 records have reasonable values)
- **Consistency:** ~91% (50/55 records are unique)

---

## 🔍 Sample Queries for Verification

### Check NULL Values
```sql
SELECT 
    COUNT(*) FILTER (WHERE customer_name IS NULL) as missing_name,
    COUNT(*) FILTER (WHERE email IS NULL) as missing_email,
    COUNT(*) FILTER (WHERE phone IS NULL) as missing_phone,
    COUNT(*) FILTER (WHERE country IS NULL) as missing_country
FROM customer_data;
```

### Check Invalid Emails
```sql
SELECT customer_id, customer_name, email
FROM customer_data
WHERE email NOT LIKE '%@%.%'
   OR email LIKE '%@@%'
ORDER BY customer_id;
```

### Check Outliers
```sql
SELECT customer_id, customer_name, purchase_amount, credit_score
FROM customer_data
WHERE purchase_amount < 0 
   OR purchase_amount > 100000
   OR credit_score < 300
   OR credit_score > 850
ORDER BY customer_id;
```

### Check Duplicates
```sql
SELECT email, COUNT(*) as count
FROM customer_data
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY count DESC;
```

---

## 🗑️ Cleanup

To remove the sample data:

```sql
DROP TABLE customer_data CASCADE CONSTRAINTS;
```

Or via Docker:
```bash
docker exec -it oracle-xe sqlplus dq_test/dq_test123@XE
DROP TABLE customer_data CASCADE CONSTRAINTS;
```

---

## 📝 Notes

- All dates use Oracle DATE format
- Phone numbers are 10-digit US format
- Credit scores follow FICO range (300-850)
- Purchase amounts are in USD
- The data is designed to trigger all DQ checks in the analysis tool

---

## 🔗 Related Files

- `setup_oracle_dq_sample_data.sql` - SQL script to create and populate table
- `load_oracle_sample_data.bat` - Automated loader script
- `oracle_connection_config.json` - DQ analysis configuration
- `test_oracle_dq_connection.py` - Connection test script
- `run_oracle_dq_analysis.bat` - DQ analysis runner

---

**Created with Bob** 🤖