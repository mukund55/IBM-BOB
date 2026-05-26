#!/usr/bin/env python3
"""
Transform DAT file according to DML specification
Reads DML file to understand format and transforms DAT file accordingly
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
from datetime import datetime


def parse_dml_file(dml_path: str) -> List[Dict[str, str]]:
    """
    Parse DML file and extract field definitions
    Returns list of field specifications with name, type, delimiter, and format
    """
    fields = []
    
    with open(dml_path, 'r') as f:
        content = f.read()
    
    # Extract field definitions between record and end
    record_match = re.search(r'record\s+(.*?)\s+end;', content, re.DOTALL)
    if not record_match:
        raise ValueError("Invalid DML format: 'record...end;' block not found")
    
    record_content = record_match.group(1)
    
    # Parse each field line
    # Format: type("delimiter") field_name(size);
    field_pattern = r'(\w+)\("([^"]*)"\)\s+(\w+)(?:\(([^)]+)\))?;'
    
    for match in re.finditer(field_pattern, record_content):
        field_type = match.group(1)  # string, decimal, date, etc.
        delimiter = match.group(2)   # delimiter after this field
        field_name = match.group(3)  # field name
        field_format = match.group(4) if match.group(4) else None  # size or date format
        
        # Unescape special characters in delimiter
        delimiter = delimiter.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
        
        fields.append({
            'name': field_name,
            'type': field_type,
            'delimiter': delimiter,
            'format': field_format
        })
    
    return fields


def analyze_dat_field(values: list, field_name: str) -> Dict[str, str]:
    """
    Analyze actual data in DAT file to determine field characteristics
    Returns dict with detected type, format, etc.
    """
    analysis = {
        'name': field_name,
        'sample_values': values[:5],
        'detected_type': 'string',
        'is_numeric': False,
        'is_date': False,
        'date_format': None
    }
    
    # Check if numeric
    numeric_count = 0
    for val in values:
        try:
            float(val)
            numeric_count += 1
        except:
            pass
    
    if numeric_count / len(values) > 0.8:  # 80% numeric
        analysis['is_numeric'] = True
        analysis['detected_type'] = 'decimal'
    
    # Check if date
    date_count = 0
    detected_format = None
    for val in values:
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                datetime.strptime(val, fmt)
                date_count += 1
                detected_format = fmt
                break
            except:
                pass
    
    if date_count / len(values) > 0.8:  # 80% dates
        analysis['is_date'] = True
        analysis['detected_type'] = 'date'
        analysis['date_format'] = detected_format
    
    return analysis


def convert_value(value: str, field_spec: Dict[str, str]) -> str:
    """
    Convert value according to field specification
    The DML spec is the TARGET format, so we convert TO what DML specifies
    """
    field_type = field_spec['type']
    field_format = field_spec.get('format')
    
    try:
        if field_type == 'string':
            # Keep as string, optionally truncate to size
            if field_format and field_format.isdigit():
                max_len = int(field_format)
                return value[:max_len]
            return value
        
        elif field_type == 'decimal':
            # Convert to decimal/numeric
            # Remove non-numeric characters except decimal point and minus
            cleaned = re.sub(r'[^\d.-]', '', value)
            if cleaned:
                return str(float(cleaned))
            return '0'
        
        elif field_type == 'date':
            # Convert date format
            # Try to parse existing date and convert to target format
            if field_format:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        dt = datetime.strptime(value, fmt)
                        # Convert DML format to Python format
                        target_fmt = field_format.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
                        return dt.strftime(target_fmt)
                    except ValueError:
                        continue
            return value
        
        else:
            # Unknown type, keep as is
            return value
    
    except Exception as e:
        print(f"Warning: Error converting value '{value}' for field {field_spec['name']}: {e}")
        return value


def transform_dat_file(dat_path: str, dml_path: str, output_path: str = None) -> Dict[str, Any]:
    """
    Transform DAT file according to DML specification
    """
    # Parse DML
    print(f"Parsing DML file: {dml_path}")
    field_specs = parse_dml_file(dml_path)
    
    print(f"\nDML Field Specifications:")
    for i, spec in enumerate(field_specs, 1):
        print(f"  {i}. {spec['name']}: {spec['type']}", end='')
        if spec['format']:
            print(f"({spec['format']})", end='')
        delim_repr = repr(spec['delimiter']).strip("'")
        print(f" -> delimiter: {delim_repr}")
    
    # Read DAT file
    print(f"\nReading DAT file: {dat_path}")
    with open(dat_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        print("Error: DAT file is empty")
        return {'success': False, 'error': 'DAT file is empty'}
    
    # Detect current delimiter
    header = lines[0].strip()
    current_delimiter = None
    for delim in ['|', ',', '\t', ';']:
        if delim in header:
            current_delimiter = delim
            break
    
    if not current_delimiter:
        print("Error: Could not detect delimiter in DAT file")
        return {'success': False, 'error': 'Could not detect delimiter in DAT file'}
    
    print(f"Detected current delimiter: '{current_delimiter}'")
    
    # Parse header
    header_fields = [f.strip() for f in header.split(current_delimiter)]
    print(f"Header fields: {header_fields}")
    
    # Verify field count matches
    if len(header_fields) != len(field_specs):
        print(f"Warning: Field count mismatch - DAT has {len(header_fields)} fields, DML has {len(field_specs)} fields")
    
    # Determine output path
    if not output_path:
        dat_file = Path(dat_path)
        output_path = dat_file.parent / f"{dat_file.stem}_transformed{dat_file.suffix}"
    
    print(f"\nTransforming data...")
    print(f"Output file: {output_path}")
    
    # Transform data
    transformed_lines = []
    
    # Write header (field names from DML)
    header_line = ""
    for i, spec in enumerate(field_specs):
        header_line += spec['name']
        if i < len(field_specs) - 1:
            header_line += spec['delimiter']
    transformed_lines.append(header_line)
    
    # Transform data rows
    for line_num, line in enumerate(lines[1:], 2):
        line = line.strip()
        if not line:
            continue
        
        # Split by current delimiter
        values = [v.strip() for v in line.split(current_delimiter)]
        
        # Convert each value according to DML spec
        transformed_line = ""
        for i, (value, spec) in enumerate(zip(values, field_specs)):
            converted_value = convert_value(value, spec)
            transformed_line += converted_value
            if i < len(field_specs) - 1:
                transformed_line += spec['delimiter']
        
        transformed_lines.append(transformed_line)
    
    # Write output file
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        for line in transformed_lines:
            f.write(line + '\n')
    
    print(f"\n[SUCCESS] Transformation complete!")
    print(f"  Input records: {len(lines) - 1}")
    print(f"  Output records: {len(transformed_lines) - 1}")
    print(f"  Output file: {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python transform_dat_by_dml.py <dat_file> <dml_file> [output_file]")
        print("\nExample:")
        print("  python transform_dat_by_dml.py sample_employee_data.dat unsupported_format_employee.dml")
        print("  python transform_dat_by_dml.py sample_employee_data.dat unsupported_format_employee.dml output.dat")
        sys.exit(1)
    
    dat_file = sys.argv[1]
    dml_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Verify files exist
    if not Path(dat_file).exists():
        print(f"Error: DAT file not found: {dat_file}")
        sys.exit(1)
    
    if not Path(dml_file).exists():
        print(f"Error: DML file not found: {dml_file}")
        sys.exit(1)
    
    try:
        transform_dat_file(dat_file, dml_file, output_file)
    except Exception as e:
        print(f"\nError during transformation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
