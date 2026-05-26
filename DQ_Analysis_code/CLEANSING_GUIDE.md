# Data Quality Analysis - Cleansing Guide

## Overview
The `data_quality_analysis.py` script now includes comprehensive data cleansing capabilities that automatically fix common data quality issues.

## Features

### Automatic Cleansing Operations

1. **Whitespace Trimming**
   - Removes leading/trailing whitespace from all string columns
   - Automatically applied to all text fields

2. **Email Normalization**
   - Converts emails to lowercase
   - Removes invalid entries (nan, none, empty strings)
   - Standardizes email format

3. **Data Type Conversion**
   - Converts columns to correct data types (numeric, date)
   - Invalid values are set to NaN/NaT
   - Preserves valid data while marking invalid entries

4. **Negative Value Fixes**
   - Converts negative values to absolute values in specified columns
   - Useful for fields like age, salary, quantity where negatives are invalid

5. **Allowed Values Enforcement**
   - Validates values against allowed lists
   - Sets invalid values to NaN
   - Case-insensitive matching

6. **Range Constraints**
   - Clips values to specified min/max ranges
   - Ensures data stays within business rules
   - Example: Age between 0-120, Salary between 0-1000000

7. **Duplicate Removal**
   - Removes duplicate records (keeps first occurrence)
   - Removes duplicate primary keys
   - Maintains data integrity

## Usage

### Basic Usage with Cleansing

```bash
python data_quality_analysis.py \
    --input-file your_data.csv \
    --output-dir output_folder \
    --generate-dashboard \
    --cleanse-data
```

### With Configuration File

```bash
python data_quality_analysis.py \
    --input-file your_data.json \
    --config-file dq_config.json \
    --output-dir output_folder \
    --generate-dashboard \
    --cleanse-data
```

### Specify Cleansed Output File

```bash
python data_quality_analysis.py \
    --input-file your_data.csv \
    --output-dir output_folder \
    --cleanse-data \
    --cleanse-output cleaned_data.csv
```

## Output Files

When cleansing is enabled, the following files are generated:

1. **cleansed_data.csv** - The cleaned dataset with all fixes applied
2. **dq_cleansing_log.csv** - Detailed log of all cleansing operations
3. **dq_executive_dashboard.html** - Dashboard with cleansing status section
4. **good_records.csv** - Records that passed all quality checks
5. **bad_records_*.csv** - Categorized bad records for review

## Dashboard Cleansing Section

The executive dashboard includes a dedicated "Data Cleansing Status" section showing:

- **Cleansing Operations**: Number of operations performed
- **Records Affected**: Total records modified
- **Quality Improvement**: Percentage improvement in quality score
- **Detailed Table**: Column-by-column breakdown of all operations

### When Cleansing is NOT Performed

If you run without `--cleanse-data`, the dashboard shows:
```
🔧 Data Cleansing Status
No data cleansing was performed.
Run with --cleanse-data flag to enable automatic data cleansing.
```

### When Cleansing IS Performed

The dashboard displays:
- Summary metrics (operations, records affected, improvement)
- Detailed table with:
  - Column name
  - Operation type
  - Records affected
  - Description of the fix

## Configuration

Configure cleansing rules in your JSON config file:

```json
{
  "general": {
    "trim_whitespace": true
  },
  "rules": {
    "email_columns": ["EMAIL", "CONTACT_EMAIL"],
    "dtype_rules": {
      "SALARY": "numeric",
      "JOIN_DATE": "date"
    },
    "negative_not_allowed_columns": ["AGE", "SALARY", "QUANTITY"],
    "allowed_values": {
      "STATUS": ["ACTIVE", "INACTIVE"],
      "COUNTRY_CODE": ["IN", "US", "UK"]
    },
    "range_rules": {
      "AGE": {"min": 0, "max": 120},
      "SALARY": {"min": 0, "max": 1000000}
    }
  },
  "keys": {
    "primary_keys": ["CUSTOMER_ID"]
  }
}
```

## Examples

### Example 1: Customer Data Cleansing

```bash
cd DQ_Analysis_code
python data_quality_analysis.py \
    --input-file sample_customer_data.csv \
    --output-dir dq_output_customer_cleansed \
    --generate-dashboard \
    --cleanse-data
```

**Result:**
- 10 cleansing operations performed
- 31 records affected
- Quality improved from 0% to 5%
- Cleansed data saved to `cleansed_data.csv`

### Example 2: Electricity Board Data

```bash
cd DQ_Analysis_code
python data_quality_analysis.py \
    --input-file electricity_board_anomalies.json \
    --output-dir dq_output_electricity_cleansed \
    --generate-dashboard \
    --cleanse-data
```

**Result:**
- No automatic fixes applied (data has nulls, outliers, invalid emails)
- Dashboard shows "No data cleansing was performed"
- Manual intervention required for these issue types

## Cleansing Log Format

The `dq_cleansing_log.csv` contains:

| Column | Operation | Records Affected | Description |
|--------|-----------|------------------|-------------|
| EMAIL | normalize_email | 2 | Converted to lowercase and removed invalid entries |
| SALARY | convert_to_numeric | 21 | Converted to numeric type, invalid values set to NaN |
| AGE | fix_negative_values | 1 | Converted negative values to absolute values |

## Best Practices

1. **Always Review Cleansing Log**: Check what was changed before using cleansed data
2. **Backup Original Data**: Keep a copy of original data before cleansing
3. **Validate Business Rules**: Ensure cleansing rules match your business requirements
4. **Test on Sample Data**: Test cleansing on a small dataset first
5. **Review Bad Records**: Check bad_records_*.csv files to understand issues
6. **Monitor Quality Improvement**: Track quality score changes over time

## Limitations

### Issues That Cannot Be Auto-Fixed

1. **Null/Blank Values**: Requires business logic to fill
2. **Outliers**: Need domain expertise to determine if valid
3. **Invalid Emails**: Cannot guess correct email addresses
4. **Pattern Violations**: Cannot infer correct format
5. **Referential Integrity**: Requires lookup in reference data

These issues are flagged in bad records files for manual review.

## Quality Score Calculation

- **Before Cleansing**: Based on original data
- **After Cleansing**: Based on cleansed data
- **Improvement**: Difference between before and after
- **Formula**: `Quality Score = (Clean Records / Total Records) × 100`

## Support

For issues or questions:
1. Check the log file: `dq_output/dq_run.log`
2. Review the cleansing log: `dq_output/dq_cleansing_log.csv`
3. Examine bad records files for patterns
4. Adjust configuration rules as needed

## Version History

- **v2.0**: Added comprehensive cleansing capabilities
- **v2.1**: Added cleansing status to dashboard
- **v2.2**: Enhanced cleansing log with detailed descriptions