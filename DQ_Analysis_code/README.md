# Data Quality Analysis Tool

## Overview
Production-ready Data Quality Analysis script for CSV datasets with comprehensive profiling, anomaly detection, and reporting capabilities.

## Installation

### Required Dependencies
Install the core dependencies:
```bash
pip install pandas numpy openpyxl xlsxwriter
```

### Optional Dependencies

#### For Visualization Features
```bash
pip install matplotlib seaborn plotly
```

#### For Database Connectivity
```bash
# For all databases
pip install sqlalchemy

# For specific databases (install as needed)
pip install cx-Oracle      # Oracle
pip install pyodbc          # SQL Server
pip install pymysql         # MySQL
pip install psycopg2-binary # PostgreSQL
```

### Install All Dependencies
To install all dependencies at once:
```bash
pip install -r requirements.txt
```

## Resolving Import Warnings

The script uses optional imports wrapped in try-except blocks. This means:
- **Core functionality** works with just pandas and numpy
- **Visualization features** require matplotlib, seaborn, and plotly
- **Database features** require sqlalchemy and database-specific drivers

### Type Checking Warnings
If you see basedpyright/pyright warnings about missing imports, these are expected for optional dependencies. The script handles missing imports gracefully:

1. **Missing visualization libraries**: The script will log a warning and skip visualization features
2. **Missing database libraries**: The script will log a warning and skip database connectivity features

### To Suppress Type Checking Warnings
Add a `pyrightconfig.json` or `pyproject.toml` in your project root:

**pyrightconfig.json:**
```json
{
  "reportMissingImports": "none",
  "reportMissingModuleSource": "none"
}
```

**pyproject.toml:**
```toml
[tool.pyright]
reportMissingImports = "none"
reportMissingModuleSource = "none"
```

## Usage

### Basic Usage
```bash
python data_quality_analysis.py input.csv
```

### With Configuration File
```bash
python data_quality_analysis.py input.csv --config dq_config.json
```

### With Output Directory
```bash
python data_quality_analysis.py input.csv --output-dir ./results
```

## Features

- **Data Profiling**: Column-level statistics and metadata
- **Anomaly Detection**: Null values, duplicates, outliers, pattern violations
- **Rule Validation**: Business rules, referential integrity, data types
- **Quality Scoring**: Overall data quality score with breakdown
- **Reporting**: Excel, CSV, HTML, and interactive dashboards
- **Data Cleansing**: Optional data cleaning with detailed logs
- **Database Support**: Load data directly from databases

## Configuration

Create a JSON configuration file to customize validation rules:

```json
{
  "columns": {
    "email": {
      "data_type": "string",
      "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
      "mandatory": true
    },
    "age": {
      "data_type": "integer",
      "min_value": 0,
      "max_value": 120
    }
  },
  "keys": {
    "primary_keys": ["id"],
    "unique_keys": ["email"]
  }
}
```

## Troubleshooting

### Import Errors
If you encounter import errors:
1. Check which features you need
2. Install only the required dependencies
3. The script will work with partial dependencies installed

### Type Checking Issues
The type checking warnings are informational and don't affect runtime behavior. The script uses defensive programming with try-except blocks and availability flags.

## License
MIT License