import pandas as pd
import sys
sys.path.insert(0, '.')
from data_quality_analysis import cleanse_data, run_all_checks
import json

# Load data
df = pd.read_csv('sample data/customer_data_diff_with_header.dat', delimiter='|')
print("Original DataFrame:")
print(f"Indices: {df.index.tolist()}")
print(f"IDs: {df['CUSTOMER_ID'].tolist()}")
print()

# Load config
with open('dq_config_dat_customer.json', 'r') as f:
    config = json.load(f)

# Cleanse data
cleansed_df, cleansing_log_df = cleanse_data(df, config)
print("Cleansed DataFrame:")
print(f"Indices: {cleansed_df.index.tolist()}")
print(f"IDs: {cleansed_df['CUSTOMER_ID'].tolist()}")
print()

# Run checks
results = run_all_checks(cleansed_df, config)
combined_issues_df = results["combined_issues_df"]
good_records_df = results["good_records_df"]

print("Combined Issues DataFrame:")
print(f"Shape: {combined_issues_df.shape}")
print(f"Indices: {combined_issues_df.index.tolist()}")
print(f"Unique indices: {combined_issues_df.index.unique().tolist()}")
if not combined_issues_df.empty:
    print(f"IDs in issues: {combined_issues_df['CUSTOMER_ID'].tolist()}")
print()

print("Good Records DataFrame:")
print(f"Shape: {good_records_df.shape}")
print(f"Indices: {good_records_df.index.tolist()}")
if not good_records_df.empty:
    print(f"IDs in good records: {good_records_df['CUSTOMER_ID'].tolist()}")

# Made with Bob
