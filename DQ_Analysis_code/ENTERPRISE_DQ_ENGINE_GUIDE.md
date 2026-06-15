# Enterprise Data Quality Engine - Complete Guide

## Overview

The Enterprise Data Quality Engine is a comprehensive, production-ready framework that extends the existing `data_quality_analysis.py` script with advanced AI-powered capabilities.

**Version:** 2.0.0  
**Author:** Bob  
**Date:** June 2026

---

## 🎯 Key Features

### 1. **Advanced Data Profiling** (15+ Metrics per Column)
- Data type inference (email, phone, URL, date, numeric, text)
- Statistical measures (min, max, mean, median, std, quartiles, IQR)
- Null/blank analysis with percentages
- Uniqueness and cardinality metrics
- Pattern detection and frequency analysis
- Top N values with distribution
- Column-level quality scores

### 2. **Multi-Dimensional Quality Scoring** (5 Dimensions)
- **Completeness** (25%): Null values, blanks, mandatory fields
- **Validity** (25%): Pattern violations, range violations, datatype violations
- **Consistency** (20%): Mixed types, special characters, standardization
- **Accuracy** (15%): Referential integrity, business rules, outliers
- **Uniqueness** (15%): Duplicates, primary key violations

**Overall Score:** 0-100 with classification (Excellent 90-100, Moderate 75-89, Poor <75)

### 3. **Root Cause Analysis Engine**
- AI-powered cause inference with confidence scores (0-100)
- 100+ root cause templates across 10 issue categories
- Context-aware analysis
- Multi-factor pattern matching
- Actionable remediation guidance

### 4. **AI Recommendation Engine** (50+ Scenarios)
- Priority-based recommendations (Critical, High, Medium, Low)
- Cost-benefit analysis (0-10 scale)
- Implementation effort estimation
- Step-by-step implementation plans
- Prerequisites and time estimates

### 5. **ETL Reconciliation Module**
- Record count comparison
- Sum validation for numeric columns
- Hash total validation
- Missing records detection
- Additional records detection
- Data mismatch detection with tolerance

### 6. **Historical Trend Analysis**
- DQ score tracking over time
- Trend detection (improving, degrading, stable)
- Trend strength calculation (strong, moderate, weak)
- Volatility analysis (low, medium, high)
- Anomaly detection on trends

### 7. **Alert Management Framework**
- Threshold-based alerting
- Severity classification (Critical, High, Medium, Low)
- Alert history tracking
- Email notification support (configurable)
- Alert dashboard generation

### 8. **Metadata Catalog**
- Automatic data dictionary generation
- Column metadata tracking (technical, quality, statistical, pattern)
- Business metadata templates
- Profiling summary catalog
- JSON and Excel exports

### 9. **Enhanced Reporting**
- **Excel Reports**: Multi-sheet comprehensive reports
- **PDF Reports**: Executive summaries with visualizations
- **JSON Reports**: API-ready structured data
- **HTML Dashboards**: Interactive visualizations

---

## 📦 Installation

### Prerequisites
```bash
Python 3.8+
pip (Python package manager)
```

### Install Dependencies
```bash
cd DQ_Analysis_code
pip install -r requirements.txt
```

### Optional Dependencies
```bash
# For PDF generation
pip install reportlab

# For database connectivity
pip install cx-Oracle  # Oracle
pip install psycopg2-binary  # PostgreSQL
pip install pyodbc  # SQL Server
pip install pymysql  # MySQL
```

---

## 🚀 Quick Start

### Basic Usage

```bash
# Analyze a CSV file
python dq_engine_enhanced.py --input customer_data.csv --output-dir dq_results

# With custom configuration
python dq_engine_enhanced.py --input customer_data.csv --config dq_config.json --output-dir dq_results

# With dataset name
python dq_engine_enhanced.py --input customer_data.csv --dataset-name "Customer Master Data" --output-dir dq_results
```

### ETL Reconciliation

```bash
# Reconcile source and target
python dq_engine_enhanced.py \
  --input source_data.csv \
  --reconcile-target target_data.csv \
  --key-columns "customer_id,order_id" \
  --output-dir reconciliation_results
```

### Python API Usage

```python
from dq_engine_enhanced import EnterpriseDataQualityEngine
import pandas as pd

# Load configuration
config = {
    'general': {'output_dir': 'dq_output'},
    'rules': {'mandatory_fields': ['customer_id', 'email']}
}

# Initialize engine
engine = EnterpriseDataQualityEngine(config)

# Load data
df = pd.read_csv('customer_data.csv')

# Perform analysis
results = engine.analyze_dataset(df, dataset_name='Customer Data')

# Generate reports
reports = engine.generate_reports(results, 'dq_output', 'customer_dq_report')

# Print summary
engine.print_executive_summary(results)
```

---

## 📊 Output Files

### Generated Reports

| File | Format | Description |
|------|--------|-------------|
| `dq_comprehensive_report.xlsx` | Excel | Multi-sheet report with all analysis results |
| `dq_comprehensive_report.json` | JSON | API-ready structured data |
| `dq_comprehensive_report.pdf` | PDF | Executive summary with visualizations |
| `reconciliation_report.xlsx` | Excel | ETL reconciliation results (if applicable) |

### Excel Report Sheets

1. **Executive Summary**: Key metrics and scores
2. **Dataset Profile**: Dataset-level statistics
3. **Column Profiles**: Detailed column-level metrics
4. **DQ Scorecard**: 5-dimension scoring breakdown
5. **Root Cause Analysis**: AI-generated root causes
6. **Recommendations**: Prioritized action items
7. **Alerts**: Data quality alerts
8. **Trend Analysis**: Historical trends
9. **Data Dictionary**: Complete data catalog
10. **Anomaly Summary**: Issue breakdown

---

## ⚙️ Configuration

### Sample Configuration File

```json
{
  "general": {
    "output_dir": "dq_output_enhanced",
    "log_level": "INFO",
    "top_n_frequent_values": 10
  },
  "rules": {
    "mandatory_columns": ["customer_id", "email"],
    "mandatory_fields": ["customer_id", "email", "name"],
    "primary_keys": ["customer_id"],
    "regex_rules": {
      "email": "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$",
      "phone": "^[0-9]{10}$"
    },
    "range_rules": {
      "age": {"min": 18, "max": 100},
      "salary": {"min": 20000, "max": 500000}
    }
  },
  "dimension_weights": {
    "completeness": 25,
    "validity": 25,
    "consistency": 20,
    "accuracy": 15,
    "uniqueness": 15
  },
  "alert_thresholds": {
    "overall_score": {"critical": 60, "high": 75, "medium": 85},
    "null_percentage": {"critical": 20, "high": 10, "medium": 5},
    "duplicate_percentage": {"critical": 10, "high": 5, "medium": 2}
  }
}
```

---

## 📈 Use Cases

### 1. Data Migration Validation
```bash
# Validate migrated data
python dq_engine_enhanced.py \
  --input legacy_data.csv \
  --reconcile-target new_system_data.csv \
  --key-columns "customer_id" \
  --dataset-name "Customer Migration"
```

### 2. Daily Data Quality Monitoring
```bash
# Schedule daily DQ checks
python dq_engine_enhanced.py \
  --input daily_feed.csv \
  --config production_dq_config.json \
  --output-dir dq_monitoring/$(date +%Y%m%d)
```

### 3. Data Profiling for New Datasets
```python
# Profile unknown dataset
engine = EnterpriseDataQualityEngine({})
df = pd.read_csv('unknown_data.csv')
results = engine.analyze_dataset(df)

# Export data dictionary
data_dict = results['data_dictionary']
data_dict.to_excel('data_dictionary.xlsx', index=False)
```

### 4. Trend Analysis
```python
# Analyze quality trends over time
trend_analyzer = TrendAnalyzer({'history_dir': 'dq_history'})
trends = trend_analyzer.analyze_all_metrics(lookback_periods=30)
trend_report = trend_analyzer.generate_trend_report(trends)
print(trend_report)
```

---

## 🔧 Module Reference

### 1. AdvancedDataProfiler
```python
from dq_engine.profiler_advanced import AdvancedDataProfiler

profiler = AdvancedDataProfiler(config)
dataset_profile, column_profiles = profiler.profile_dataframe(df)

# Export profiles
profiler.export_profile_to_json(dataset_profile, column_profiles, 'profile.json')
profiler.export_profile_to_excel(dataset_profile, column_profiles, 'profile.xlsx')
```

### 2. MultiDimensionalScorer
```python
from dq_engine.scorer_multidimensional import MultiDimensionalScorer

scorer = MultiDimensionalScorer(config)
scoring_results = scorer.score_data_quality(df, anomaly_summary)

# Export scorecard
scorecard_df = scorer.export_scorecard_to_dataframe(scoring_results)
```

### 3. RootCauseAnalyzer
```python
from dq_engine.root_cause_analyzer import RootCauseAnalyzer

rca = RootCauseAnalyzer(config)
rca_results = rca.analyze_all_issues(anomaly_summary, context)

# Export RCA
rca_df = rca.export_rca_to_dataframe(rca_results)
rca_summary = rca.generate_rca_summary(rca_results)
```

### 4. AIRecommendationEngine
```python
from dq_engine.recommender_ai import AIRecommendationEngine

recommender = AIRecommendationEngine(config)
recommendations = recommender.generate_recommendations(anomaly_summary, scoring_results, rca_results)

# Export recommendations
rec_df = recommender.export_recommendations_to_dataframe(recommendations)
action_plan = recommender.generate_action_plan(recommendations, max_recommendations=10)
```

### 5. ETLReconciler
```python
from dq_engine.reconciler import ETLReconciler

reconciler = ETLReconciler(config)
recon_results = reconciler.perform_full_reconciliation(
    source_df, target_df, key_columns=['id']
)

# Export reconciliation report
reconciler.export_reconciliation_report(recon_results, 'reconciliation.xlsx')
```

### 6. TrendAnalyzer
```python
from dq_engine.trend_analyzer import TrendAnalyzer

trend_analyzer = TrendAnalyzer(config)

# Store execution
trend_analyzer.store_execution(execution_data)

# Analyze trends
trends = trend_analyzer.analyze_all_metrics(lookback_periods=10)
trend_df = trend_analyzer.export_trends_to_dataframe(trends)
```

### 7. AlertManager
```python
from dq_engine.alert_manager import AlertManager

alert_manager = AlertManager(config)
alerts = alert_manager.evaluate_alerts(metrics, anomaly_summary)

# Export alerts
alert_df = alert_manager.export_alerts_to_dataframe(alerts)
alert_report = alert_manager.generate_alert_report(alerts)
```

### 8. MetadataCatalog
```python
from dq_engine.metadata_catalog import MetadataCatalog

catalog = MetadataCatalog(config)

# Generate data dictionary
data_dict = catalog.generate_data_dictionary(df, column_profiles, business_metadata)

# Generate metadata
column_metadata = catalog.generate_column_metadata(column_profiles)
profiling_summary = catalog.generate_profiling_summary(dataset_profile, column_profiles)

# Export catalog
catalog.export_catalog_to_excel(data_dict, column_metadata, profiling_summary, 'catalog.xlsx')
```

### 9. EnhancedReportGenerator
```python
from dq_engine.report_generator import EnhancedReportGenerator

report_gen = EnhancedReportGenerator(config)

# Generate all reports
reports = report_gen.generate_all_reports(
    output_dir='reports',
    base_filename='dq_report',
    dataset_profile=dataset_profile,
    column_profiles=column_profiles,
    scoring_results=scoring_results,
    recommendations=recommendations
)
```

---

## 🎓 Best Practices

### 1. Configuration Management
- Store configurations in version control
- Use environment-specific configs (dev, test, prod)
- Document all custom rules and thresholds

### 2. Scheduling and Automation
- Schedule regular DQ checks (daily/weekly)
- Integrate with CI/CD pipelines
- Set up automated alerting

### 3. Trend Monitoring
- Track DQ scores over time
- Set up alerts for degrading trends
- Review trends monthly

### 4. Action on Recommendations
- Prioritize Critical and High recommendations
- Track implementation progress
- Measure improvement after fixes

### 5. Documentation
- Maintain data dictionaries
- Document business rules
- Keep metadata up-to-date

---

## 🐛 Troubleshooting

### Common Issues

**Issue:** Module import errors
```bash
# Solution: Ensure dq_engine package is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/DQ_Analysis_code"
```

**Issue:** PDF generation fails
```bash
# Solution: Install reportlab
pip install reportlab
```

**Issue:** Database connection errors
```bash
# Solution: Install appropriate database driver
pip install cx-Oracle  # For Oracle
pip install psycopg2-binary  # For PostgreSQL
```

**Issue:** Memory errors with large datasets
```python
# Solution: Process in chunks
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    results = engine.analyze_dataset(chunk)
```

---

## 📞 Support

For issues, questions, or contributions:
- Review existing documentation
- Check troubleshooting section
- Contact: Bob (Enterprise DQ Team)

---

## 📝 License

Enterprise Data Quality Engine v2.0.0  
Copyright © 2026 Bob

---

## 🔄 Version History

### Version 2.0.0 (June 2026)
- ✅ Advanced data profiling (15+ metrics)
- ✅ Multi-dimensional scoring (5 dimensions)
- ✅ Root cause analysis engine
- ✅ AI recommendation engine (50+ scenarios)
- ✅ ETL reconciliation module
- ✅ Historical trend analysis
- ✅ Alert management framework
- ✅ Metadata catalog
- ✅ Enhanced reporting (Excel, PDF, JSON)

### Version 1.0.0 (Original)
- Basic data profiling
- Anomaly detection
- Rule validation
- Simple scoring
- CSV/Excel exports

---

**End of Guide**