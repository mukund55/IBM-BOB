# Data Quality Analysis Tool

A production-ready Python script for comprehensive data quality analysis of CSV datasets.

## Features

- **Data Profiling**: Statistical analysis of all columns
- **Anomaly Detection**: Identifies outliers, null values, duplicates, and data inconsistencies
- **Rule Validation**: Validates data against configurable business rules
- **Quality Scoring**: Calculates overall data quality score with weighted metrics
- **Detailed Reports**: Generates CSV and Excel reports with bad records
- **Referential Integrity**: Validates foreign key relationships
- **Business Rules**: Supports conditional validation rules

## Prerequisites

Install required Python packages:

```bash
pip install pandas numpy openpyxl
```

## Project Structure

```
DQ_Analysis_code/
├── data_quality_analysis.py      # Main script
├── dq_config.json                # Configuration file (optional)
├── sample_customer_data.csv      # Sample input data
├── reference_countries.csv       # Sample reference data
├── dq_output/                    # Output directory (auto-created)
└── README.md                     # This file
```

## Quick Start

### Option 1: Using the Runner Scripts (Easiest)

**Windows Batch Script:**
```bash
cd DQ_Analysis_code
run_dq_analysis.bat
```

**PowerShell Script:**
```powershell
cd DQ_Analysis_code
.\run_dq_analysis.ps1
```

### Option 2: Manual Command Line

**IMPORTANT:** You must run the commands from within the DQ_Analysis_code directory:

```bash
cd DQ_Analysis_code
python data_quality_analysis.py --input-file sample_customer_data.csv
```

### Basic Usage (with default configuration)

```bash
cd DQ_Analysis_code
python data_quality_analysis.py --input-file sample_customer_data.csv
```

### With Custom Configuration

```bash
cd DQ_Analysis_code
python data_quality_analysis.py --input-file sample_customer_data.csv --config-file dq_config.json
```

### With Custom Output Directory

```bash
cd DQ_Analysis_code
python data_quality_analysis.py --input-file sample_customer_data.csv --output-dir my_output
```

### With Referential Integrity Check

```bash
cd DQ_Analysis_code
python data_quality_analysis.py --input-file sample_customer_data.csv --reference-file reference_countries.csv
```

### Complete Example

```bash
cd DQ_Analysis_code
python data_quality_analysis.py --input-file sample_customer_data.csv --config-file dq_config.json --output-dir dq_output --reference-file reference_countries.csv --sheet-name "Quality_Report"
```

## Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--input-file` | Yes | Path to input CSV file |
| `--output-dir` | No | Output directory (default: dq_output) |
| `--config-file` | No | JSON configuration file path |
| `--reference-file` | No | Reference CSV for referential integrity |
| `--sheet-name` | No | Excel sheet name (default: DQ_Report) |

## Configuration File

The `dq_config.json` file allows you to customize:

### General Settings
- Output directory and log file names
- File encoding and delimiter
- Column name normalization
- Excel output options

### Data Rules
- **Primary Keys**: Define unique identifier columns
- **Mandatory Columns**: Columns that must exist
- **Mandatory Fields**: Fields that cannot be null/blank
- **Data Type Rules**: Expected data types per column
- **Range Rules**: Min/max values for numeric columns
- **Pattern Rules**: Regex patterns for validation
- **Allowed Values**: Enumerated valid values
- **Date Formats**: Expected date formats
- **Email Validation**: Email pattern rules

### Anomaly Detection
- **Outlier Method**: IQR or Z-score
- **Thresholds**: Configurable sensitivity
- **Column-specific**: Override settings per column

### Quality Scoring
- **Weights**: Customize importance of each check
- Configurable penalty weights for different violation types

### Business Rules
- Conditional validation rules
- Cross-column dependencies

## Output Files

The script generates the following files in the output directory:

### CSV Files
1. **dq_summary.csv** - Overall statistics and quality score
2. **dq_profile.csv** - Column-level profiling data
3. **dq_numeric_stats.csv** - Statistical measures for numeric columns
4. **dq_anomaly_summary.csv** - Summary of all detected anomalies
5. **dq_quality_score.csv** - Detailed quality score breakdown
6. **dq_column_metrics.csv** - Per-column quality metrics
7. **dq_recommendations.csv** - Actionable recommendations
8. **bad_records_*.csv** - Separate files for each anomaly type

### Excel Report
- **dq_report.xlsx** - Consolidated workbook with all sheets

### Log File
- **dq_run.log** - Detailed execution log

## Sample Data

### sample_customer_data.csv
Contains intentional data quality issues for testing:
- Null/blank values
- Duplicate records
- Invalid emails
- Out-of-range values
- Invalid dates
- Negative values
- Special characters
- Mixed data types

### reference_countries.csv
Reference data for validating country codes.

## Data Quality Checks

The script performs the following checks:

1. **Null and Blank Values** - Identifies missing data
2. **Duplicate Records** - Finds exact duplicate rows
3. **Duplicate Primary Keys** - Detects duplicate IDs
4. **Outliers** - Statistical outlier detection (IQR/Z-score)
5. **Mixed Data Types** - Inconsistent types in columns
6. **Invalid Dates** - Date format violations
7. **Invalid Emails** - Email pattern validation
8. **Negative Values** - Unexpected negative numbers
9. **Special Characters** - Invalid character patterns
10. **Data Type Violations** - Type mismatch with rules
11. **Range Violations** - Values outside allowed ranges
12. **Pattern Violations** - Regex pattern mismatches
13. **Allowed Value Violations** - Values not in whitelist
14. **Missing Mandatory Columns** - Required columns absent
15. **Mandatory Field Violations** - Required fields empty
16. **Referential Integrity** - Foreign key validation
17. **Business Rule Violations** - Custom rule failures

## Quality Score

The quality score (0-100) is calculated based on:
- Weighted penalties for each violation type
- Total number of records
- Severity of issues

**Score Interpretation:**
- 90-100: Excellent
- 80-89: Good
- 70-79: Fair
- 60-69: Poor
- Below 60: Critical

## Customization

### Adding Custom Rules

Edit `dq_config.json` to add:

```json
{
  "rules": {
    "regex_rules": {
      "PHONE": "^\\d{10}$"
    },
    "allowed_values": {
      "DEPARTMENT": ["IT", "HR", "Finance"]
    }
  }
}
```

### Adding Business Rules

```json
{
  "business_rules": [
    {
      "name": "active_must_have_email",
      "type": "conditional_required",
      "if": {"column": "STATUS", "operator": "equals", "value": "ACTIVE"},
      "then": {"required_column": "EMAIL"}
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Module not found**: Install required packages
   ```bash
   pip install pandas numpy openpyxl
   ```

2. **File encoding errors**: Specify encoding in config
   ```json
   {"general": {"encoding": "utf-8"}}
   ```

3. **Memory issues with large files**: Process in chunks or increase system memory

4. **Permission errors**: Ensure write access to output directory

## Best Practices

1. **Start with defaults**: Run with default config first
2. **Review logs**: Check dq_run.log for detailed information
3. **Iterative refinement**: Adjust rules based on initial results
4. **Version control**: Keep config files in version control
5. **Regular monitoring**: Run periodically on production data
6. **Trend analysis**: Compare quality scores over time

## Support

For issues or questions:
1. Check the log file (dq_run.log)
2. Review the console output
3. Verify input file format matches expectations
4. Validate configuration JSON syntax

## License

This script is provided as-is for data quality analysis purposes.

## Version History

- v1.0 - Initial production release with comprehensive DQ checks