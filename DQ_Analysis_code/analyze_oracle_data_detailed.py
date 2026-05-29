#!/usr/bin/env python3
"""
Detailed Oracle Data Analysis
Analyzes the customers table and provides accurate DQ metrics
"""

import oracledb
import pandas as pd

def analyze_oracle_data():
    """Perform detailed analysis of Oracle customers table"""
    
    print("=" * 80)
    print("DETAILED ORACLE DATA QUALITY ANALYSIS")
    print("=" * 80)
    print()
    
    # Connect to Oracle
    connection = oracledb.connect(
        user="dq_test",
        password="dq_test123",
        dsn="localhost:1521/XEPDB1"
    )
    
    # Load data
    df = pd.read_sql("SELECT * FROM customers ORDER BY customer_id", connection)
    connection.close()
    
    print(f"Total Records: {len(df)}")
    print(f"Total Columns: {len(df.columns)}")
    print()
    
    # Initialize counters
    issues = {
        'null_blank': 0,
        'missing_mandatory_columns': 0,
        'invalid_emails': 0,
        'duplicates': 0,
        'negative_values': 0,
        'outliers': 0,
        'pattern_violations': 0,
        'allowed_value_violations': 0
    }
    
    issue_details = []
    
    # Check each record
    for idx, row in df.iterrows():
        record_issues = []
        
        # 1. Check NULL/Blank values
        null_cols = []
        if pd.isna(row['CUSTOMER_NAME']) or str(row['CUSTOMER_NAME']).strip() == '':
            null_cols.append('CUSTOMER_NAME')
        if pd.isna(row['EMAIL']) or str(row['EMAIL']).strip() == '':
            null_cols.append('EMAIL')
        if pd.isna(row['PHONE']) or str(row['PHONE']).strip() == '':
            null_cols.append('PHONE')
        if pd.isna(row['COUNTRY']) or str(row['COUNTRY']).strip() == '':
            null_cols.append('COUNTRY')
        if pd.isna(row['REGISTRATION_DATE']):
            null_cols.append('REGISTRATION_DATE')
            
        if null_cols:
            issues['null_blank'] += 1
            record_issues.append(f"NULL/Blank in: {', '.join(null_cols)}")
        
        # 2. Check mandatory columns
        mandatory_missing = []
        if pd.isna(row['CUSTOMER_ID']):
            mandatory_missing.append('CUSTOMER_ID')
        if pd.isna(row['CUSTOMER_NAME']) or str(row['CUSTOMER_NAME']).strip() == '':
            mandatory_missing.append('CUSTOMER_NAME')
        if pd.isna(row['EMAIL']) or str(row['EMAIL']).strip() == '':
            mandatory_missing.append('EMAIL')
            
        if mandatory_missing:
            issues['missing_mandatory_columns'] += 1
            record_issues.append(f"Missing mandatory: {', '.join(mandatory_missing)}")
        
        # 3. Check invalid emails
        email = str(row['EMAIL']) if not pd.isna(row['EMAIL']) else ''
        if email and '@' in email:
            # Check if it has proper domain
            if '.' not in email.split('@')[1] if len(email.split('@')) > 1 else True:
                issues['invalid_emails'] += 1
                issues['pattern_violations'] += 1
                record_issues.append(f"Invalid email: {email}")
        elif email and email != 'nan':
            issues['invalid_emails'] += 1
            issues['pattern_violations'] += 1
            record_issues.append(f"Invalid email: {email}")
        
        # 4. Check negative values
        if not pd.isna(row['PURCHASE_AMOUNT']) and float(row['PURCHASE_AMOUNT']) < 0:
            issues['negative_values'] += 1
            record_issues.append(f"Negative amount: {row['PURCHASE_AMOUNT']}")
        
        # 5. Check outliers (amount > 100000)
        if not pd.isna(row['PURCHASE_AMOUNT']) and float(row['PURCHASE_AMOUNT']) > 100000:
            issues['outliers'] += 1
            record_issues.append(f"Outlier amount: {row['PURCHASE_AMOUNT']}")
        
        # 6. Check allowed values for is_active
        if not pd.isna(row['IS_ACTIVE']) and int(row['IS_ACTIVE']) not in [0, 1]:
            issues['allowed_value_violations'] += 1
            record_issues.append(f"Invalid is_active: {row['IS_ACTIVE']}")
        
        if record_issues:
            issue_details.append({
                'customer_id': row['CUSTOMER_ID'],
                'customer_name': row['CUSTOMER_NAME'],
                'issues': record_issues
            })
    
    # 7. Check for duplicates
    duplicate_cols = ['CUSTOMER_NAME', 'EMAIL', 'PHONE']
    duplicates_df = df[df.duplicated(subset=duplicate_cols, keep=False)]
    issues['duplicates'] = len(duplicates_df)
    
    # Print summary
    print("=" * 80)
    print("ISSUE SUMMARY")
    print("=" * 80)
    print()
    
    total_issues = sum(issues.values())
    for issue_type, count in sorted(issues.items()):
        if count > 0:
            print(f"  {issue_type:.<40} {count:>3} records")
    
    print()
    print(f"Total Issue Instances: {total_issues}")
    print()
    
    # Print detailed issues
    print("=" * 80)
    print("DETAILED ISSUES BY RECORD")
    print("=" * 80)
    print()
    
    for detail in issue_details:
        print(f"Customer ID {detail['customer_id']}: {detail['customer_name']}")
        for issue in detail['issues']:
            print(f"  - {issue}")
        print()
    
    # Print duplicates
    if len(duplicates_df) > 0:
        print("=" * 80)
        print(f"DUPLICATE RECORDS ({len(duplicates_df)} records)")
        print("=" * 80)
        print()
        for idx, row in duplicates_df.iterrows():
            print(f"  ID {row['CUSTOMER_ID']}: {row['CUSTOMER_NAME']} - {row['EMAIL']}")
        print()
    
    # Calculate quality score
    bad_records = len(issue_details)
    good_records = len(df) - bad_records
    quality_score = (good_records / len(df)) * 100 if len(df) > 0 else 0
    
    print("=" * 80)
    print("DATA QUALITY SCORE")
    print("=" * 80)
    print()
    print(f"  Total Records: {len(df)}")
    print(f"  Good Records: {good_records} ({good_records/len(df)*100:.2f}%)")
    print(f"  Bad Records: {bad_records} ({bad_records/len(df)*100:.2f}%)")
    print(f"  Quality Score: {quality_score:.2f}%")
    print()
    
    # Print expected vs actual
    print("=" * 80)
    print("EXPECTED VS ACTUAL COUNTS")
    print("=" * 80)
    print()
    print("Expected counts (based on data):")
    print("  allowed_value_violations: 1 (is_active=2)")
    print("  duplicates: 2 (John Doe, Jane Smith)")
    print("  invalid_emails: 2 (charlie@invalid, frank@test)")
    print("  missing_mandatory_columns: 3")
    print("  negative_values: 1 (purchase_amount=-100)")
    print("  null_blank: 3-5 (various NULL fields)")
    print("  outliers: 1 (purchase_amount=999999.99)")
    print("  pattern_violations: 2 (same as invalid_emails)")
    print()
    print("Actual counts from analysis:")
    for issue_type, count in sorted(issues.items()):
        print(f"  {issue_type}: {count}")
    print()

if __name__ == "__main__":
    try:
        analyze_oracle_data()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Made with Bob
