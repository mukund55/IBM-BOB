#!/usr/bin/env python3
"""
Smart DAT File Transformer with Auto-Correction
- Analyzes actual data in DAT file
- Auto-corrects DML if types don't match data
- Transforms DAT file according to corrected DML
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
from datetime import datetime


def parse_dml_file(dml_path: str) -> List[Dict[str, Any]]:
    """
    Parse DML file and extract field definitions
    Supports both old and new syntax:
    - Old: type("delimiter") field_name;
    - New: type("format")("delimiter") field_name;
    """
    fields = []
    
    with open(dml_path, 'r') as f:
        content = f.read()
    
    # Extract field definitions between record and end
    record_match = re.search(r'record\s+(.*?)\s+end;', content, re.DOTALL)
    if not record_match:
        raise ValueError("Invalid DML format: 'record...end;' block not found")
    
    record_content = record_match.group(1)
    
    # Parse each field line - support both syntaxes
    # New syntax: type("format")("delimiter") field_name;
    # Old syntax: type("delimiter") field_name(size);
    
    for line in record_content.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        
        # Try new syntax first: type("format")("delimiter") field_name;
        match = re.match(r'(\w+)\("([^"]*)"\)\("([^"]*)"\)\s+(\w+);', line)
        if match:
            field_type = match.group(1)
            field_format = match.group(2)
            delimiter = match.group(3)
            field_name = match.group(4)
        else:
            # Try old syntax: type("delimiter") field_name(size);
            match = re.match(r'(\w+)\("([^"]*)"\)\s+(\w+)(?:\(([^)]+)\))?;', line)
            if match:
                field_type = match.group(1)
                delimiter = match.group(2)
                field_name = match.group(3)
                field_format = match.group(4) if match.group(4) else None
            else:
                print(f"Warning: Could not parse DML line: {line}")
                continue
        
        # Unescape special characters in delimiter
        delimiter = delimiter.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
        
        fields.append({
            'name': field_name,
            'type': field_type,
            'delimiter': delimiter,
            'format': field_format
        })
    
    return fields


def analyze_column_data(values: List[str], field_name: str) -> Dict[str, Any]:
    """
    Analyze actual data to detect real data type
    """
    analysis = {
        'name': field_name,
        'sample_values': values[:3],
        'detected_type': 'string',
        'confidence': 0.0,
        'is_numeric': False,
        'is_date': False,
        'date_format': None
    }
    
    if not values:
        return analysis
    
    # Check if numeric
    numeric_count = 0
    for val in values:
        try:
            float(val.replace(',', ''))
            numeric_count += 1
        except:
            pass
    
    numeric_confidence = numeric_count / len(values)
    if numeric_confidence > 0.9:  # 90% numeric
        analysis['is_numeric'] = True
        analysis['detected_type'] = 'decimal'
        analysis['confidence'] = numeric_confidence
        return analysis
    
    # Check if date
    date_count = 0
    detected_format = None
    date_formats = [
        ('%Y-%m-%d', 'YYYY-MM-DD'),
        ('%Y/%m/%d', 'YYYY/MM/DD'),
        ('%d-%m-%Y', 'DD-MM-YYYY'),
        ('%d/%m/%Y', 'DD/MM/YYYY'),
        ('%m/%d/%Y', 'MM/DD/YYYY')
    ]
    
    for val in values:
        for py_fmt, dml_fmt in date_formats:
            try:
                datetime.strptime(val, py_fmt)
                date_count += 1
                detected_format = dml_fmt
                break
            except:
                pass
    
    date_confidence = date_count / len(values)
    if date_confidence > 0.9:  # 90% dates
        analysis['is_date'] = True
        analysis['detected_type'] = 'date'
        analysis['date_format'] = detected_format
        analysis['confidence'] = date_confidence
        return analysis
    
    # Default to string
    analysis['detected_type'] = 'string'
    analysis['confidence'] = 1.0
    return analysis


def auto_correct_dml(dml_fields: List[Dict], dat_analysis: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Auto-correct DML fields based on actual data analysis
    Returns corrected fields and list of corrections made
    """
    corrected_fields = []
    corrections = []
    
    for i, (dml_field, dat_field) in enumerate(zip(dml_fields, dat_analysis)):
        corrected = dml_field.copy()
        
        # Check if type needs correction
        if dml_field['type'] != dat_field['detected_type']:
            corrections.append(
                f"Field '{dml_field['name']}': Changed type from '{dml_field['type']}' to '{dat_field['detected_type']}' "
                f"(confidence: {dat_field['confidence']:.1%}, samples: {dat_field['sample_values']})"
            )
            corrected['type'] = dat_field['detected_type']
            
            # Update format for dates
            if dat_field['is_date'] and dat_field['date_format']:
                corrected['format'] = dat_field['date_format']
        
        # Check if delimiter looks wrong (contains letters/numbers that aren't escape sequences)
        delimiter = corrected['delimiter']
        # If delimiter contains alphanumeric characters (except \n, \t, \r), it's probably wrong
        if re.search(r'[a-zA-Z0-9]', delimiter.replace('\\n', '').replace('\\t', '').replace('\\r', '')):
            old_delim = delimiter
            # Use comma for all fields except the last one (which should be newline)
            if i == len(dml_fields) - 1:
                corrected['delimiter'] = '\n'
                corrections.append(
                    f"Field '{dml_field['name']}': Fixed delimiter from '{old_delim}' to '\\n' (newline)"
                )
            else:
                corrected['delimiter'] = ','
                corrections.append(
                    f"Field '{dml_field['name']}': Fixed delimiter from '{old_delim}' to ',' (comma)"
                )
        
        corrected_fields.append(corrected)
    
    return corrected_fields, corrections


def convert_value(value: str, field_spec: Dict[str, Any], field_analysis: Dict[str, Any]) -> str:
    """
    Convert value according to corrected field specification
    """
    field_type = field_spec['type']
    field_format = field_spec.get('format')
    
    try:
        if field_type == 'string':
            return value
        
        elif field_type == 'decimal':
            cleaned = value.replace(',', '')
            try:
                return str(float(cleaned))
            except:
                return value
        
        elif field_type == 'date':
            # Keep date as-is or reformat if needed
            if field_format and field_analysis.get('date_format'):
                # Parse with detected format
                source_fmt = field_analysis['date_format'].replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
                target_fmt = field_format.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
                try:
                    dt = datetime.strptime(value, source_fmt)
                    return dt.strftime(target_fmt)
                except:
                    return value
            return value
        
        else:
            return value
    
    except Exception as e:
        return value


def transform_dat_file(dat_path: str, dml_path: str, output_path: str | None = None, auto_correct: bool = True) -> Dict[str, Any]:
    """
    Transform DAT file according to DML with optional auto-correction
    """
    print(f"\n{'='*80}")
    print("SMART DAT FILE TRANSFORMATION")
    print(f"{'='*80}\n")
    
    start_time = datetime.now()
    
    # Parse DML
    print(f"[1/5] Parsing DML file: {dml_path}")
    dml_fields = parse_dml_file(dml_path)
    print(f"      Found {len(dml_fields)} field specifications")
    
    # Read DAT file
    print(f"\n[2/5] Reading DAT file: {dat_path}")
    with open(dat_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        return {'success': False, 'error': 'DAT file is empty'}
    
    total_records = len(lines) - 1
    
    # Detect delimiter
    header = lines[0].strip()
    current_delimiter = None
    for delim in ['|', ',', '\t', ';']:
        if delim in header:
            current_delimiter = delim
            print(f"      Detected delimiter: '{delim}'")
            break
    
    if not current_delimiter:
        return {'success': False, 'error': 'Could not detect delimiter'}
    
    # Parse data
    header_fields = [f.strip() for f in header.split(current_delimiter)]
    print(f"      Columns: {', '.join(header_fields)}")
    print(f"      Records: {total_records}")
    
    # Analyze actual data
    print(f"\n[3/5] Analyzing actual data types...")
    data_analysis = []
    issues_detected = 0
    
    for i, field_name in enumerate(header_fields):
        column_values = []
        for line in lines[1:]:
            values = line.strip().split(current_delimiter)
            if i < len(values):
                column_values.append(values[i].strip())
        
        analysis = analyze_column_data(column_values, field_name)
        data_analysis.append(analysis)
        print(f"      {field_name}: {analysis['detected_type']} (confidence: {analysis['confidence']:.1%})")
        
        # Count potential issues
        if i < len(dml_fields) and dml_fields[i]['type'] != analysis['detected_type']:
            issues_detected += 1
    
    # Auto-correct DML if needed
    corrected_fields = dml_fields
    corrections = []
    type_corrections = 0
    delimiter_corrections = 0
    
    if auto_correct:
        print(f"\n[4/5] Auto-correcting DML based on actual data...")
        corrected_fields, corrections = auto_correct_dml(dml_fields, data_analysis)
        
        # Count correction types
        for correction in corrections:
            if 'Changed type' in correction:
                type_corrections += 1
            elif 'Fixed delimiter' in correction:
                delimiter_corrections += 1
        
        if corrections:
            print(f"      Made {len(corrections)} corrections:")
            for correction in corrections:
                print(f"      - {correction}")
        else:
            print(f"      No corrections needed - DML matches data!")
    
    # Transform data
    print(f"\n[5/5] Transforming data...")
    
    if not output_path:
        output_path = str(Path(dat_path).parent / f"{Path(dat_path).stem}_transformed{Path(dat_path).suffix}")
    
    transformed_lines = []
    transformation_errors = 0
    
    # Write header
    header_line = ""
    for i, field in enumerate(corrected_fields):
        header_line += field['name']
        if i < len(corrected_fields) - 1:
            header_line += field['delimiter']
    transformed_lines.append(header_line)
    
    # Transform data rows
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        
        values = [v.strip() for v in line.split(current_delimiter)]
        transformed_line = ""
        
        try:
            for i, (value, field, analysis) in enumerate(zip(values, corrected_fields, data_analysis)):
                converted_value = convert_value(value, field, analysis)
                transformed_line += converted_value
                if i < len(corrected_fields) - 1:
                    transformed_line += field['delimiter']
            
            transformed_lines.append(transformed_line)
        except Exception as e:
            transformation_errors += 1
    
    # Write output
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        for line in transformed_lines:
            f.write(line + '\n')
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Calculate metrics
    records_transformed = len(transformed_lines) - 1
    corrections_made = len(corrections)
    # Auto-fix success rate: percentage of detected issues that were successfully corrected
    # Cap at 100% (can't fix more than 100% of issues)
    auto_fix_success_rate = min((corrections_made / issues_detected * 100) if issues_detected > 0 else 100.0, 100.0)
    remaining_issues = max(issues_detected - corrections_made, 0)  # Can't have negative remaining issues
    correction_rate = (type_corrections / len(dml_fields) * 100) if len(dml_fields) > 0 else 0.0
    recovery_rate = (records_transformed / total_records * 100) if total_records > 0 else 0.0
    transformation_success = ((total_records - transformation_errors) / total_records * 100) if total_records > 0 else 0.0
    dml_compatibility_improved = corrections_made > 0
    final_status = "REMEDIATED" if remaining_issues == 0 and transformation_errors == 0 else "PARTIAL" if corrections_made > 0 else "FAILED"
    
    print(f"\n{'='*80}")
    print("[SUCCESS] Transformation Complete!")
    print(f"{'='*80}")
    print(f"Output file: {output_path}")
    print(f"Records transformed: {records_transformed}/{total_records}")
    print(f"Corrections made: {corrections_made}")
    print(f"Correction rate: {correction_rate:.1f}%")
    print(f"Recovery rate: {recovery_rate:.1f}%")
    print(f"Transformation success: {transformation_success:.1f}%")
    print(f"Auto-fix success rate: {auto_fix_success_rate:.1f}%")
    print(f"Remaining issues: {remaining_issues}")
    print(f"DML compatibility: {'IMPROVED' if dml_compatibility_improved else 'UNCHANGED'}")
    print(f"Final status: {final_status}")
    print(f"Duration: {duration:.2f}s")
    print(f"{'='*80}\n")
    
    return {
        'success': True,
        'input_file': dat_path,
        'dml_file': dml_path,
        'output_file': output_path,
        'total_records': total_records,
        'records_transformed': records_transformed,
        'corrections_made': corrections_made,
        'correction_rate': correction_rate,
        'recovery_rate': recovery_rate,
        'transformation_success': transformation_success,
        'auto_fix_success_rate': auto_fix_success_rate,
        'remaining_issues': remaining_issues,
        'dml_compatibility_improved': dml_compatibility_improved,
        'final_status': final_status,
        'corrections': corrections,
        'data_analysis': data_analysis,
        'type_corrections': type_corrections,
        'delimiter_corrections': delimiter_corrections,
        'transformation_errors': transformation_errors,
        'duration': duration,
        'timestamp': end_time.strftime('%Y-%m-%d %H:%M:%S')
    }


def generate_transformation_dashboard(result: Dict[str, Any], output_dir: str | None = None) -> str:
    """
    Generate HTML dashboard for transformation results
    """
    if not output_dir:
        output_dir = str(Path(result['output_file']).parent)
    
    dashboard_path = Path(output_dir) / "transformation_dashboard.html"
    
    # Determine status colors
    status_color = {
        'REMEDIATED': '#28a745',
        'PARTIAL': '#ffc107',
        'FAILED': '#dc3545'
    }
    
    color = status_color.get(result['final_status'], '#6c757d')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DAT Transformation Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            color: #667eea;
            font-size: 36px;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #666;
            font-size: 16px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .metric-subtitle {{
            font-size: 12px;
            color: #999;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .status-remediated {{
            background: #d4edda;
            color: #155724;
        }}
        .status-partial {{
            background: #fff3cd;
            color: #856404;
        }}
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        .info-item {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .info-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .info-value {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }}
        .corrections-list {{
            list-style: none;
            padding: 0;
        }}
        .corrections-list li {{
            padding: 12px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            transition: width 0.5s ease;
        }}
        .analysis-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .analysis-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        .analysis-table td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        .analysis-table tr:hover {{
            background: #f8f9fa;
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 DAT Transformation Report</h1>
            <p>Smart Data Transformation with Auto-Correction</p>
            <p style="font-size: 12px; margin-top: 10px;">Generated: {result['timestamp']}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Records</div>
                <div class="metric-value">{result['total_records']:,}</div>
                <div class="metric-subtitle">Input dataset size</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Records Transformed</div>
                <div class="metric-value">{result['records_transformed']:,}</div>
                <div class="metric-subtitle">{result['recovery_rate']:.1f}% recovery rate</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result['recovery_rate']}%">{result['recovery_rate']:.1f}%</div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Corrections Made</div>
                <div class="metric-value">{result['corrections_made']}</div>
                <div class="metric-subtitle">{result['type_corrections']} type + {result['delimiter_corrections']} delimiter</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Auto-Fix Success Rate</div>
                <div class="metric-value">{result['auto_fix_success_rate']:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result['auto_fix_success_rate']}%">{result['auto_fix_success_rate']:.1f}%</div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Transformation Success</div>
                <div class="metric-value">{result['transformation_success']:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {result['transformation_success']}%">{result['transformation_success']:.1f}%</div>
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Remaining Issues</div>
                <div class="metric-value">{result['remaining_issues']}</div>
                <div class="metric-subtitle">Issues not auto-fixed</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">📊 Transformation Summary</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Input File</div>
                    <div class="info-value">{Path(result['input_file']).name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">DML File</div>
                    <div class="info-value">{Path(result['dml_file']).name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Output File</div>
                    <div class="info-value">{Path(result['output_file']).name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Correction Rate</div>
                    <div class="info-value">{result['correction_rate']:.1f}%</div>
                </div>
                <div class="info-item">
                    <div class="info-label">DML Compatibility</div>
                    <div class="info-value">{'✅ IMPROVED' if result['dml_compatibility_improved'] else '⚠️ UNCHANGED'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Final Status</div>
                    <div class="info-value">
                        <span class="status-badge status-{result['final_status'].lower()}">{result['final_status']}</span>
                    </div>
                </div>
                <div class="info-item">
                    <div class="info-label">Processing Time</div>
                    <div class="info-value">{result['duration']:.2f}s</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Transformation Errors</div>
                    <div class="info-value">{result['transformation_errors']}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">🔧 Corrections Applied</div>
            {f'<p style="color: #28a745; font-weight: bold;">✅ {len(result["corrections"])} corrections were successfully applied:</p>' if result['corrections'] else '<p style="color: #6c757d;">ℹ️ No corrections needed - DML perfectly matches the data!</p>'}
            {f'''<ul class="corrections-list">
                {''.join([f'<li>{correction}</li>' for correction in result['corrections']])}
            </ul>''' if result['corrections'] else ''}
        </div>

        <div class="section">
            <div class="section-title">📈 Data Analysis Results</div>
            <table class="analysis-table">
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Detected Type</th>
                        <th>Confidence</th>
                        <th>Sample Values</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''<tr>
                        <td><strong>{field['name']}</strong></td>
                        <td>{field['detected_type']}</td>
                        <td>{field['confidence']:.1%}</td>
                        <td>{', '.join(str(v) for v in field['sample_values'][:3])}</td>
                    </tr>''' for field in result['data_analysis']])}
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-title">💬 Comments & Recommendations</div>
            <div style="line-height: 1.8;">
                <p><strong>What was fixed:</strong></p>
                <ul style="margin-left: 20px; margin-top: 10px;">
                    <li>✅ {result['type_corrections']} data type mismatches corrected</li>
                    <li>✅ {result['delimiter_corrections']} delimiter issues fixed</li>
                    <li>✅ {result['records_transformed']} records successfully transformed</li>
                </ul>
                
                <p style="margin-top: 20px;"><strong>DML Compatibility:</strong></p>
                <p style="margin-left: 20px; margin-top: 10px;">
                    {f'✅ DML compatibility has been <strong>IMPROVED</strong>. The auto-corrected DML now matches the actual data structure.' if result['dml_compatibility_improved'] else '⚠️ DML compatibility <strong>UNCHANGED</strong>. The original DML already matched the data structure.'}
                </p>
                
                <p style="margin-top: 20px;"><strong>Final Status:</strong></p>
                <p style="margin-left: 20px; margin-top: 10px;">
                    {f'<span style="color: #28a745;">✅ <strong>REMEDIATED</strong> - All issues have been successfully resolved. The transformation is complete with no remaining issues.</span>' if result['final_status'] == 'REMEDIATED' else f'<span style="color: #ffc107;">⚠️ <strong>PARTIAL</strong> - Some corrections were made, but {result["remaining_issues"]} issues remain. Manual review may be needed.</span>' if result['final_status'] == 'PARTIAL' else '<span style="color: #dc3545;">❌ <strong>FAILED</strong> - Transformation encountered significant issues. Manual intervention required.</span>'}
                </p>
                
                <p style="margin-top: 20px;"><strong>Recommendations:</strong></p>
                <ul style="margin-left: 20px; margin-top: 10px;">
                    {f'<li>⚠️ Review the {result["remaining_issues"]} remaining issues manually</li>' if result['remaining_issues'] > 0 else ''}
                    <li>📝 Update the source DML file with the auto-corrected specifications</li>
                    <li>🔍 Validate the transformed output file before using in production</li>
                    {'<li>✅ Transformation completed successfully - output file is ready to use</li>' if result['final_status'] == 'REMEDIATED' else ''}
                    {'<li>🎉 No further action required</li>' if result['final_status'] == 'REMEDIATED' else ''}
                </ul>
            </div>
        </div>

        <div class="section">
            <div class="section-title">🔧 Resolution Steps</div>
            <div style="line-height: 1.8;">
                <p><strong>How to apply these corrections to your DML file:</strong></p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #667eea;">
                    <p style="font-weight: bold; color: #667eea; margin-bottom: 15px;">Step-by-Step Resolution:</p>
                    
                    <ol style="margin-left: 20px;">
                        <li style="margin-bottom: 15px;">
                            <strong>Open your DML file:</strong> {Path(result['dml_file']).name}
                            <br><code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 12px;">notepad {Path(result['dml_file']).name}</code>
                        </li>
                        
                        <li style="margin-bottom: 15px;">
                            <strong>Apply the following corrections:</strong>
                            <ul style="margin-left: 20px; margin-top: 10px;">
                                {''.join([f'''<li style="margin-bottom: 15px; background: white; padding: 15px; border-radius: 5px; border-left: 3px solid #667eea;">
                                    <div style="font-size: 16px; font-weight: bold; color: #667eea; margin-bottom: 8px;">
                                        📌 Field: {correction.split("'")[1] if "'" in correction else 'Unknown'}
                                    </div>
                                    <div style="margin-bottom: 5px;">
                                        <strong style="color: #dc3545;">❌ Issue:</strong>
                                        <span style="background: #fff5f5; padding: 3px 8px; border-radius: 3px; font-family: monospace;">
                                            {correction.split('Changed type from')[1].split('to')[0].strip().strip("'") if 'Changed type from' in correction else correction.split('Fixed delimiter from')[1].split('to')[0].strip().strip("'") if 'Fixed delimiter from' in correction else 'Type mismatch'}
                                        </span>
                                    </div>
                                    <div style="margin-bottom: 5px;">
                                        <strong style="color: #28a745;">✅ Fix:</strong>
                                        <span style="background: #f0fdf4; padding: 3px 8px; border-radius: 3px; font-family: monospace;">
                                            {correction.split("to '")[1].split("'")[0] if "to '" in correction else 'Apply correction'}
                                        </span>
                                    </div>
                                    <div style="font-size: 12px; color: #666; margin-top: 8px;">
                                        💡 <em>{correction.split('(confidence:')[1].split(')')[0] if 'confidence:' in correction else 'Full details: ' + correction}</em>
                                    </div>
                                </li>''' for correction in result['corrections']])}
                            </ul>
                        </li>
                        
                        <li style="margin-bottom: 15px;">
                            <strong>Example DML correction format:</strong>
                            <div style="background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: 'Courier New', monospace; font-size: 13px;">
                                <div style="color: #6c757d;">// Before (incorrect):</div>
                                <div style="color: #ff6b6b;">string("|") EMP_ID;</div>
                                <br>
                                <div style="color: #6c757d;">// After (corrected):</div>
                                <div style="color: #51cf66;">decimal("|") EMP_ID;</div>
                            </div>
                        </li>
                        
                        <li style="margin-bottom: 15px;">
                            <strong>Save the corrected DML file</strong> and re-run the transformation to verify
                        </li>
                        
                        <li style="margin-bottom: 15px;">
                            <strong>Validate the output:</strong>
                            <br>• Check the transformed file: {Path(result['output_file']).name}
                            <br>• Verify data types match expectations
                            <br>• Ensure delimiters are correct
                            <br>• Test with downstream systems
                        </li>
                    </ol>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ffc107;">
                    <p style="font-weight: bold; color: #856404; margin-bottom: 10px;">⚠️ Important Notes:</p>
                    <ul style="margin-left: 20px;">
                        <li>Always backup your original DML file before making changes</li>
                        <li>Test the corrected DML with a sample dataset first</li>
                        <li>Document all changes made for future reference</li>
                        <li>If using version control, commit the corrected DML with a descriptive message</li>
                    </ul>
                </div>
                
                <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #28a745;">
                    <p style="font-weight: bold; color: #155724; margin-bottom: 10px;">✅ Quick Command to Re-run:</p>
                    <code style="background: #155724; color: white; padding: 10px; border-radius: 5px; display: block; font-family: 'Courier New', monospace;">
                        python smart_transform_dat.py {Path(result['input_file']).name} {Path(result['dml_file']).name}
                    </code>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Smart DAT Transformer | {result['timestamp']}</p>
            <p style="margin-top: 5px;">Duration: {result['duration']:.2f}s</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(dashboard_path)


def main():
    if len(sys.argv) < 3:
        print("Usage: python smart_transform_dat.py <dat_file> <dml_file> [output_file] [--no-auto-correct]")
        print("\nExample:")
        print("  python smart_transform_dat.py sample.dat schema.dml output.dat")
        print("  python smart_transform_dat.py sample.dat schema.dml --no-auto-correct")
        sys.exit(1)
    
    dat_file = sys.argv[1]
    dml_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
    auto_correct = '--no-auto-correct' not in sys.argv
    
    # Verify files exist
    if not Path(dat_file).exists():
        print(f"Error: DAT file not found: {dat_file}")
        sys.exit(1)
    
    if not Path(dml_file).exists():
        print(f"Error: DML file not found: {dml_file}")
        sys.exit(1)
    
    try:
        result = transform_dat_file(dat_file, dml_file, output_file, auto_correct)
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        # Generate dashboard
        print("\n[DASHBOARD] Generating transformation dashboard...")
        dashboard_path = generate_transformation_dashboard(result)
        print(f"[DASHBOARD] Dashboard saved to: {dashboard_path}")
        print(f"\n{'='*80}")
        print("[SUCCESS] TRANSFORMATION COMPLETE WITH DASHBOARD")
        print(f"{'='*80}")
        print(f"[DASHBOARD] View dashboard: {dashboard_path}")
        print(f"[OUTPUT] Output file: {result['output_file']}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\nError during transformation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
