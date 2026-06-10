#!/usr/bin/env python3
"""
Generate Oracle DQ Dashboard with Accurate Metrics
Creates an interactive HTML dashboard with charts and detailed metrics
"""

import oracledb
import pandas as pd
from datetime import datetime
import json

def generate_dashboard():
    """Generate comprehensive DQ dashboard"""
    
    print("Connecting to Oracle database...")
    connection = oracledb.connect(
        user="dq_test",
        password="dq_test123",
        dsn="localhost:1521/XEPDB1"
    )
    
    # Load data
    df = pd.read_sql("SELECT * FROM customers ORDER BY customer_id", connection)
    connection.close()
    
    print(f"Loaded {len(df)} records")
    
    # Analyze data
    issues = {
        'allowed_value_violations': 0,
        'business_rule_violations': 0,
        'datatype_violations': 0,
        'duplicate_primary_keys': 0,
        'duplicates': 0,
        'invalid_dates': 0,
        'invalid_emails': 0,
        'missing_mandatory_columns': 0,
        'mixed_types': 0,
        'negative_values': 0,
        'null_blank': 0,
        'outliers': 0,
        'pattern_violations': 0,
        'range_violations': 0,
        'referential_integrity': 0,
        'special_characters': 0
    }
    
    bad_records = []
    
    # Analyze each record
    for idx, row in df.iterrows():
        has_issue = False
        record_issues = []
        
        # Check NULL/Blank
        if pd.isna(row['CUSTOMER_NAME']) or pd.isna(row['EMAIL']) or pd.isna(row['PHONE']) or pd.isna(row['COUNTRY']) or pd.isna(row['REGISTRATION_DATE']):
            issues['null_blank'] += 1
            has_issue = True
            record_issues.append('null_blank')
        
        # Check mandatory columns
        if pd.isna(row['CUSTOMER_NAME']) or pd.isna(row['EMAIL']):
            issues['missing_mandatory_columns'] += 1
            has_issue = True
            record_issues.append('missing_mandatory_columns')
        
        # Check invalid emails
        email = str(row['EMAIL']) if not pd.isna(row['EMAIL']) else ''
        if email and email != 'nan':
            if '@' not in email or ('.' not in email.split('@')[1] if len(email.split('@')) > 1 else True):
                issues['invalid_emails'] += 1
                issues['pattern_violations'] += 1
                has_issue = True
                record_issues.append('invalid_emails')
        
        # Check negative values
        if not pd.isna(row['PURCHASE_AMOUNT']) and float(row['PURCHASE_AMOUNT']) < 0:
            issues['negative_values'] += 1
            has_issue = True
            record_issues.append('negative_values')
        
        # Check outliers
        if not pd.isna(row['PURCHASE_AMOUNT']) and float(row['PURCHASE_AMOUNT']) > 100000:
            issues['outliers'] += 1
            has_issue = True
            record_issues.append('outliers')
        
        # Check allowed values
        if not pd.isna(row['IS_ACTIVE']) and int(row['IS_ACTIVE']) not in [0, 1]:
            issues['allowed_value_violations'] += 1
            has_issue = True
            record_issues.append('allowed_value_violations')
        
        if has_issue:
            bad_records.append({
                'customer_id': row['CUSTOMER_ID'],
                'customer_name': row['CUSTOMER_NAME'],
                'issues': ', '.join(record_issues)
            })
    
    # Check duplicates
    duplicate_cols = ['CUSTOMER_NAME', 'EMAIL', 'PHONE']
    duplicates_df = df[df.duplicated(subset=duplicate_cols, keep=False)]
    issues['duplicates'] = len(duplicates_df)
    
    # Calculate metrics
    total_records = len(df)
    bad_record_count = len(bad_records)
    good_record_count = total_records - bad_record_count
    quality_score = (good_record_count / total_records * 100) if total_records > 0 else 0
    
    # Generate HTML
    # Get current timestamp
    report_date = datetime.now().strftime('%Y-%m-%d')
    report_time = datetime.now().strftime('%H:%M:%S')
    report_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oracle DQ Dashboard - CUSTOMERS Table</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header .table-name {{ font-size: 24px; font-weight: bold; margin: 15px 0; padding: 10px 20px; background: rgba(255,255,255,0.2); border-radius: 5px; display: inline-block; }}
        .header .report-info {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3); }}
        .header .report-info p {{ opacity: 0.9; font-size: 14px; margin: 5px 0; }}
        .header .timestamp {{ font-size: 16px; font-weight: bold; margin-top: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }}
        .metric-card .value {{ font-size: 36px; font-weight: bold; color: #333; }}
        .metric-card .subtext {{ color: #999; font-size: 12px; margin-top: 5px; }}
        .score-good {{ color: #10b981; }}
        .score-medium {{ color: #f59e0b; }}
        .score-bad {{ color: #ef4444; }}
        .section {{ background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; margin-bottom: 20px; font-size: 24px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #666; }}
        tr:hover {{ background: #f8f9fa; }}
        .issue-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin: 2px; }}
        .badge-high {{ background: #fee2e2; color: #991b1b; }}
        .badge-medium {{ background: #fef3c7; color: #92400e; }}
        .badge-low {{ background: #dbeafe; color: #1e40af; }}
        .chart-container {{ margin: 20px 0; }}
        .bar {{ background: #667eea; height: 30px; border-radius: 4px; margin: 10px 0; position: relative; }}
        .bar-label {{ position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: white; font-weight: bold; font-size: 12px; }}
        .bar-value {{ position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: white; font-size: 12px; }}
        .timestamp {{ color: #999; font-size: 12px; text-align: center; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Oracle Data Quality Dashboard</h1>
            <div class="table-name">📊 Table: CUSTOMERS</div>
            <div class="report-info">
                <p><strong>Database:</strong> XEPDB1 (Oracle 21c Express Edition)</p>
                <p><strong>Schema:</strong> dq_test</p>
                <div class="timestamp">
                    📅 Report Generated: {report_date} at {report_time}
                </div>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total Records</h3>
                <div class="value">{total_records}</div>
                <div class="subtext">All customer records</div>
            </div>
            <div class="metric-card">
                <h3>Data Quality Score</h3>
                <div class="value {'score-good' if quality_score >= 70 else 'score-medium' if quality_score >= 40 else 'score-bad'}">{quality_score:.2f}%</div>
                <div class="subtext">{good_record_count} good / {bad_record_count} bad records</div>
            </div>
            <div class="metric-card">
                <h3>Total Issues</h3>
                <div class="value score-bad">{sum(issues.values())}</div>
                <div class="subtext">Across all categories</div>
            </div>
            <div class="metric-card">
                <h3>Issue Categories</h3>
                <div class="value">{sum(1 for v in issues.values() if v > 0)}</div>
                <div class="subtext">Out of {len(issues)} categories</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Issues by Category</h2>
            <div class="chart-container">
"""
    
    # Add bars for each issue type
    max_count = max(issues.values()) if issues.values() else 1
    for issue_type, count in sorted(issues.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            width = (count / max_count * 100) if max_count > 0 else 0
            html += f"""
                <div style="margin: 15px 0;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{issue_type.replace('_', ' ').title()}</div>
                    <div class="bar" style="width: {width}%;">
                        <span class="bar-label">{count} records</span>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Detailed Issue Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>Issue Category</th>
                        <th>Count</th>
                        <th>Percentage</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for issue_type, count in sorted(issues.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / total_records * 100) if total_records > 0 else 0
            severity = 'HIGH' if count >= 3 else 'MEDIUM' if count >= 2 else 'LOW'
            badge_class = 'badge-high' if severity == 'HIGH' else 'badge-medium' if severity == 'MEDIUM' else 'badge-low'
            html += f"""
                    <tr>
                        <td>{issue_type.replace('_', ' ').title()}</td>
                        <td><strong>{count}</strong></td>
                        <td>{percentage:.1f}%</td>
                        <td><span class="issue-badge {badge_class}">{severity}</span></td>
                    </tr>
"""
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🔍 Bad Records Detail</h2>
            <p style="color: #666; margin-bottom: 20px;">Records with data quality issues ({len(bad_records)} total)</p>
            <table>
                <thead>
                    <tr>
                        <th>Customer ID</th>
                        <th>Customer Name</th>
                        <th>Issues</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for record in bad_records:
        html += f"""
                    <tr>
                        <td>{record['customer_id']}</td>
                        <td>{record['customer_name'] if not pd.isna(record['customer_name']) else '<em>NULL</em>'}</td>
                        <td>{record['issues']}</td>
                    </tr>
"""
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📈 Summary Statistics</h2>
            <table>
                <tr>
                    <td><strong>Total Records Analyzed</strong></td>
                    <td>{total_records}</td>
                </tr>
                <tr>
                    <td><strong>Good Records</strong></td>
                    <td style="color: #10b981;">{good_record_count} ({good_record_count/total_records*100:.1f}%)</td>
                </tr>
                <tr>
                    <td><strong>Bad Records</strong></td>
                    <td style="color: #ef4444;">{bad_record_count} ({bad_record_count/total_records*100:.1f}%)</td>
                </tr>
                <tr>
                    <td><strong>Data Quality Score</strong></td>
                    <td><strong>{quality_score:.2f}%</strong></td>
                </tr>
                <tr>
                    <td><strong>Total Issue Instances</strong></td>
                    <td>{sum(issues.values())}</td>
                </tr>
                <tr>
                    <td><strong>Duplicate Records</strong></td>
                    <td>{issues['duplicates']}</td>
                </tr>
            </table>
        </div>
        
        <div class="timestamp">
            <strong>Report Details:</strong> Table: CUSTOMERS | Generated: {report_datetime} |
            Database: Oracle 21c Express Edition (XEPDB1) | Schema: dq_test
        </div>
    </div>
</body>
</html>
"""
    
    # Save dashboard
    output_file = "dq_output_oracle/oracle_dq_dashboard_accurate.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n[OK] Dashboard generated: {output_file}")
    print(f"\nSummary:")
    print(f"  Total Records: {total_records}")
    print(f"  Quality Score: {quality_score:.2f}%")
    print(f"  Good Records: {good_record_count}")
    print(f"  Bad Records: {bad_record_count}")
    print(f"  Total Issues: {sum(issues.values())}")
    print(f"\nOpen the dashboard: start {output_file}")

if __name__ == "__main__":
    try:
        generate_dashboard()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Made with Bob
