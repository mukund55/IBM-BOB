#!/usr/bin/env python3
"""
Production-ready Data Quality Analysis script for CSV datasets.

Features:
- Data profiling
- Anomaly detection
- Rule validation
- Data quality scoring
- Summary and bad-record exports
- Optional JSON configuration override
- Logging and exception handling

Libraries:
- pandas
- numpy
- re
- argparse
- json
- logging
- pathlib
- datetime
- typing
- traceback
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Enhanced imports for new features
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("Visualization libraries not available. Install matplotlib and seaborn for dashboard features.")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Database connectivity imports
try:
    import sqlalchemy
    from sqlalchemy import create_engine, text
    DB_SUPPORT = True
except ImportError:
    DB_SUPPORT = False
    logging.warning("SQLAlchemy not available. Install sqlalchemy for database connectivity.")

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

try:
    import pyodbc
    ODBC_AVAILABLE = True
except ImportError:
    ODBC_AVAILABLE = False

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# ============================================================================
# Ab Initio DML Parser Functions
# ============================================================================

def parse_dml_file(dml_path: str) -> Dict[str, Any]:
    """
    Parse Ab Initio DML file to extract field definitions and delimiters.
    
    Supports:
    - Field types with sizes: decimal(8), string(50), decimal(10.2)
    - Nullable fields: = NULL, = NULL("default")
    - Nested records
    - Field delimiters
    
    DML Format Examples:
        Simple:
            record
            string (",") field1;
            decimal (",") field2;
            string ("\r\n") field3;
            end
        
        Advanced:
            record
            decimal(8) customer_id;
            string(50) customer_name = NULL;
            decimal(10.2) amount = NULL("-1");
            end
    
    Args:
        dml_path: Path to the DML file
        
    Returns:
        Dictionary containing:
        - fields: List of field definitions with metadata
        - field_delimiter: Field delimiter character
        - record_delimiter: Record delimiter character
        - column_names: List of column names
        - nullable_fields: Dict of nullable field info
    """
    logging.info(f"Parsing DML file: {dml_path}")
    
    with open(dml_path, 'r', encoding='utf-8') as f:
        dml_content = f.read()
    
    # Initialize result
    result = {
        'fields': [],
        'field_delimiter': ',',
        'record_delimiter': '\n',
        'column_names': [],
        'nullable_fields': {},
        'mandatory_fields': []
    }
    
    # Remove comments and normalize whitespace
    dml_content = re.sub(r'//.*$', '', dml_content, flags=re.MULTILINE)
    dml_content = re.sub(r'/\*.*?\*/', '', dml_content, flags=re.DOTALL)
    
    # Parse field definitions - Enhanced pattern to handle multiple formats
    # Pattern 1: type(size) ("delimiter") fieldname = NULL("default");
    # Pattern 2: type(size) fieldname = NULL("default");
    # Pattern 3: type ("delimiter") fieldname;
    # Pattern 4: type fieldname;
    
    field_patterns = [
        # With delimiter and nullable with default: decimal(10.2) (",") amount = NULL("-1");
        r'(\w+)(?:\(([^)]+)\))?\s*\("([^"]+)"\)\s*(\w+)\s*=\s*NULL\s*\("([^"]*)"\)\s*;',
        # With delimiter and nullable: string(50) (",") name = NULL;
        r'(\w+)(?:\(([^)]+)\))?\s*\("([^"]+)"\)\s*(\w+)\s*=\s*NULL\s*;',
        # With delimiter only: string(50) (",") name;
        r'(\w+)(?:\(([^)]+)\))?\s*\("([^"]+)"\)\s*(\w+)\s*;',
        # No delimiter, nullable with default: decimal(10.2) amount = NULL("-1");
        r'(\w+)(?:\(([^)]+)\))?\s+(\w+)\s*=\s*NULL\s*\("([^"]*)"\)\s*;',
        # No delimiter, nullable: string(50) name = NULL;
        r'(\w+)(?:\(([^)]+)\))?\s+(\w+)\s*=\s*NULL\s*;',
        # No delimiter, no nullable: decimal(8) customer_id;
        r'(\w+)(?:\(([^)]+)\))?\s+(\w+)\s*;',
    ]
    
    all_fields = []
    for pattern_idx, pattern in enumerate(field_patterns):
        matches = re.findall(pattern, dml_content)
        for match in matches:
            all_fields.append((pattern_idx, match))
    
    if not all_fields:
        raise ValueError(f"No field definitions found in DML file: {dml_path}")
    
    # Sort by position in file
    lines = dml_content.split('\n')
    field_positions = []
    for pattern_idx, match in all_fields:
        # Find which line this field is on
        if pattern_idx == 0:  # With delimiter, nullable with default
            field_type, size, delimiter, field_name, null_default = match
            search_str = field_name
        elif pattern_idx == 1:  # With delimiter, nullable
            field_type, size, delimiter, field_name = match
            null_default = None
            search_str = field_name
        elif pattern_idx == 2:  # With delimiter only
            field_type, size, delimiter, field_name = match
            null_default = None
            search_str = field_name
        elif pattern_idx == 3:  # No delimiter, nullable with default
            field_type, size, field_name, null_default = match
            delimiter = None
            search_str = field_name
        elif pattern_idx == 4:  # No delimiter, nullable
            field_type, size, field_name = match
            delimiter = None
            null_default = None
            search_str = field_name
        else:  # No delimiter, no nullable
            field_type, size, field_name = match
            delimiter = None
            null_default = None
            search_str = field_name
        
        # Find line number
        line_num = 0
        for i, line in enumerate(lines):
            if search_str in line and field_type in line:
                line_num = i
                break
        
        field_positions.append((line_num, pattern_idx, match))
    
    # Sort by line number
    field_positions.sort(key=lambda x: x[0])
    
    # Process fields in order
    for i, (line_num, pattern_idx, match) in enumerate(field_positions):
        if pattern_idx == 0:  # With delimiter, nullable with default
            field_type, size, delimiter, field_name, null_default = match
            nullable = True
        elif pattern_idx == 1:  # With delimiter, nullable
            field_type, size, delimiter, field_name = match
            null_default = None
            nullable = True
        elif pattern_idx == 2:  # With delimiter only
            field_type, size, delimiter, field_name = match
            null_default = None
            nullable = False
        elif pattern_idx == 3:  # No delimiter, nullable with default
            field_type, size, field_name, null_default = match
            delimiter = None
            nullable = True
        elif pattern_idx == 4:  # No delimiter, nullable
            field_type, size, field_name = match
            delimiter = None
            null_default = None
            nullable = True
        else:  # No delimiter, no nullable
            field_type, size, field_name = match
            delimiter = None
            null_default = None
            nullable = False
        
        field_info = {
            'name': field_name,
            'type': field_type,
            'size': size if size else None,
            'delimiter': delimiter,
            'position': i,
            'nullable': nullable,
            'null_default': null_default if null_default else None
        }
        
        result['fields'].append(field_info)
        result['column_names'].append(field_name)
        
        if nullable:
            result['nullable_fields'][field_name] = {
                'default': null_default,
                'type': field_type
            }
        else:
            result['mandatory_fields'].append(field_name)
        
        # Determine delimiters
        if delimiter:
            if i == len(field_positions) - 1:
                result['record_delimiter'] = delimiter
            else:
                result['field_delimiter'] = delimiter
    
    # Convert escape sequences
    result['field_delimiter'] = result['field_delimiter'].encode().decode('unicode_escape')
    result['record_delimiter'] = result['record_delimiter'].encode().decode('unicode_escape')
    
    logging.info(f"DML parsed successfully:")
    logging.info(f"  Fields: {len(result['fields'])}")
    logging.info(f"  Field delimiter: {repr(result['field_delimiter'])}")
    logging.info(f"  Record delimiter: {repr(result['record_delimiter'])}")
    logging.info(f"  Columns: {result['column_names']}")
    logging.info(f"  Nullable fields: {len(result['nullable_fields'])}")
    logging.info(f"  Mandatory fields: {len(result['mandatory_fields'])}")
    
    return result


def load_dat_file_with_dml(dat_path: str, dml_info: Dict[str, Any], 
                           auto_fix_newlines: bool = True) -> pd.DataFrame:
    """
    Load Ab Initio DAT file using DML specifications.
    
    Args:
        dat_path: Path to the DAT file
        dml_info: DML information from parse_dml_file()
        auto_fix_newlines: Automatically fix newline mismatches
        
    Returns:
        pandas DataFrame with the data
    """
    logging.info(f"Loading DAT file: {dat_path}")
    
    # Check if file has correct newline characters
    with open(dat_path, 'rb') as f:
        content = f.read()
    
    expected_newline = dml_info['record_delimiter']
    
    # Count different newline types
    crlf_count = content.count(b'\r\n')
    lf_count = content.count(b'\n') - crlf_count
    cr_count = content.count(b'\r') - crlf_count
    
    # Determine actual newline in file
    if crlf_count > lf_count and crlf_count > cr_count:
        actual_newline = '\r\n'
    elif lf_count > crlf_count and lf_count > cr_count:
        actual_newline = '\n'
    elif cr_count > 0:
        actual_newline = '\r'
    else:
        actual_newline = '\n'
    
    # Check for mismatch
    newline_mismatch = (actual_newline != expected_newline)
    
    if newline_mismatch:
        logging.warning(f"Newline mismatch detected!")
        logging.warning(f"  DML expects: {repr(expected_newline)}")
        logging.warning(f"  DAT file has: {repr(actual_newline)}")
        logging.warning(f"  CRLF: {crlf_count}, LF: {lf_count}, CR: {cr_count}")
        
        if auto_fix_newlines:
            logging.info("Auto-fixing newlines to match DML specification...")
            # Create temporary fixed file
            fixed_path = dat_path + '.fixed_temp'
            fix_result = fix_newline_characters(dat_path, fixed_path, expected_newline)
            
            if fix_result['success']:
                logging.info(f"Newlines fixed successfully. Using fixed file for loading.")
                dat_path = fixed_path
            else:
                logging.error(f"Failed to fix newlines: {fix_result.get('error')}")
                raise ValueError(f"Newline mismatch and auto-fix failed")
    
    # Load the DAT file
    try:
        # Determine line terminator for pandas
        if expected_newline == '\r\n':
            line_terminator = None  # pandas default
        elif expected_newline == '\n':
            line_terminator = '\n'
        elif expected_newline == '\r':
            line_terminator = '\r'
        else:
            line_terminator = None
        
        df = pd.read_csv(
            dat_path,
            sep=dml_info['field_delimiter'],
            names=dml_info['column_names'],
            lineterminator=line_terminator,
            encoding='utf-8',
            on_bad_lines='warn'
        )
        
        logging.info(f"DAT file loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Clean up temporary fixed file if created
        if auto_fix_newlines and newline_mismatch:
            try:
                Path(dat_path).unlink()
                logging.info("Temporary fixed file cleaned up")
            except Exception as e:
                logging.warning(f"Could not delete temporary file: {e}")
        
        return df
        
    except Exception as e:
        logging.error(f"Error loading DAT file: {e}")
        raise



DEFAULT_CONFIG: Dict[str, Any] = {
    "general": {
        "output_dir": "dq_output",
        "log_file": "dq_run.log",
        "encoding": "utf-8",
        "delimiter": ",",
        "normalize_column_names": True,
        "treat_blank_as_null": True,
        "trim_whitespace": True,
        "top_n_frequent_values": 5,
        "excel_output": True,
        "bad_records_prefix": "bad_records",
        "generate_dashboard": False,
    },
    "input": {
        "xml": {
            "record_tag": "",
            "flatten_attributes": True,
            "include_root_text": False
        },
        "excel": {
            "sheet_name": 0
        },
        "json": {
            "orient": "records"
        }
    },
    "database": {
        "enabled": False,
        "type": "oracle",
        "connection_string": "",
        "query": "",
        "host": "",
        "port": "",
        "database": "",
        "username": "",
        "password": ""
    },
    "keys": {
        "primary_keys": ["CUSTOMER_ID"]
    },
    "rules": {
        "mandatory_columns": [],
        "mandatory_fields": [],
        "dtype_rules": {
            "CUSTOMER_ID": "numeric",
            "EMAIL": "string",
            "AGE": "numeric",
            "SALARY": "numeric",
            "JOIN_DATE": "date",
            "COUNTRY_CODE": "string",
            "STATUS": "string",
        },
        "range_rules": {
            "AGE": {"min": 0, "max": 120},
            "SALARY": {"min": 0, "max": 1000000},
        },
        "regex_rules": {
            "EMAIL": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            "COUNTRY_CODE": r"^[A-Z]{2,3}$",
            "STATUS": r"^[A-Z_]+$",
        },
        "allowed_values": {
            "STATUS": ["ACTIVE", "INACTIVE"],
            "COUNTRY_CODE": ["IN", "US", "UK"],
        },
        "date_columns": {
            "JOIN_DATE": {"format": "%Y-%m-%d"}
        },
        "email_columns": ["EMAIL"],
        "email_rules": {
            "EMAIL": {
                "pattern": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
                "allow_blank": True,
                "normalize_case": True
            }
        },
        "negative_not_allowed_columns": ["AGE", "SALARY"],
        "special_character_rules": {
            "CUSTOMER_NAME": r"^[A-Za-z\s.'-]*$"
        },
        "mixed_type_check_columns": ["CUSTOMER_ID", "AGE", "SALARY", "JOIN_DATE"],
        "mixed_type_rules": {
            "CUSTOMER_ID": {"expected_type": "numeric"},
            "AGE": {"expected_type": "numeric"},
            "SALARY": {"expected_type": "numeric"},
            "JOIN_DATE": {"expected_type": "date", "format": "%Y-%m-%d"}
        },
    },
    "anomaly_detection": {
        "outlier_method": "iqr",
        "iqr_multiplier": 1.5,
        "zscore_threshold": 3.0,
        "max_unique_ratio_for_categorical_consistency": 0.95,
        "outlier_min_sample_size": 5,
        "outlier_columns": [],
        "outlier_column_overrides": {},
    },
    "scoring": {
        "weights": {
            "null_blank": 15,
            "duplicates": 10,
            "duplicate_primary_keys": 15,
            "outliers": 10,
            "mixed_types": 10,
            "invalid_dates": 10,
            "invalid_emails": 10,
            "negative_values": 10,
            "special_characters": 5,
            "datatype_violations": 10,
            "range_violations": 10,
            "pattern_violations": 10,
            "allowed_value_violations": 10,
            "missing_mandatory_columns": 20,
            "mandatory_field_violations": 15,
            "referential_integrity": 10,
            "business_rule_violations": 10,
        }
    },
    "reference_integrity": {
        "enabled": False,
        "reference_file": "",
        "source_column": "",
        "reference_column": "",
        "reference_delimiter": ",",
        "reference_encoding": "utf-8",
    },
    "business_rules": [
        {
            "name": "active_customer_should_have_join_date",
            "type": "conditional_required",
            "if": {"column": "STATUS", "operator": "equals", "value": "ACTIVE"},
            "then": {"required_column": "JOIN_DATE"},
        }
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run data quality analysis with enhanced features: DB connectivity, multiple file formats, dashboards, data cleansing."
    )
    parser.add_argument(
        "--input-file",
        required=False,
        help="Path to input file (CSV, XML, Excel, JSON, Parquet, DAT). Not required if using database.",
    )
    parser.add_argument(
        "--dml-file",
        default=None,
        help="Path to Ab Initio DML file (required for .dat files). Defines field structure and delimiters.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Overrides config value.",
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help="Optional JSON configuration file path.",
    )
    parser.add_argument(
        "--reference-file",
        default=None,
        help="Optional reference file path for referential integrity validation.",
    )
    parser.add_argument(
        "--sheet-name",
        default="DQ_Report",
        help="Excel sheet name for summary workbook output.",
    )
    parser.add_argument(
        "--generate-dashboard",
        action="store_true",
        help="Generate interactive HTML dashboard with charts (requires plotly).",
    )
    parser.add_argument(
        "--use-database",
        action="store_true",
        help="Load data from database (requires database config in config file).",
    )
    parser.add_argument(
        "--cleanse-data",
        action="store_true",
        help="Apply automatic data cleansing to fix common data quality issues.",
    )
    parser.add_argument(
        "--cleanse-output",
        default=None,
        help="Output file path for cleansed data (default: <output_dir>/cleansed_data.csv).",
    )
    parser.add_argument(
        "--check-newlines",
        action="store_true",
        help="Check for mixed newline characters in input file (useful for Ab Initio .dat files).",
    )
    parser.add_argument(
        "--fix-newlines",
        action="store_true",
        help="Fix mixed newline characters by standardizing them.",
    )
    parser.add_argument(
        "--target-newline",
        choices=['LF', 'CRLF', 'CR'],
        default='LF',
        help="Target newline type when fixing (LF=\\n, CRLF=\\r\\n, CR=\\r). Default: LF",
    )
    parser.add_argument(
        "--fixed-file-output",
        default=None,
        help="Output path for file with fixed newlines (default: <input_file>_fixed.dat).",
    )
    parser.add_argument(
        "--transform-dat",
        action="store_true",
        help="Transform DAT file according to DML specification (requires --dml-file).",
    )
    parser.add_argument(
        "--transform-output",
        default=None,
        help="Output path for transformed DAT file (default: <input_file>_transformed.dat).",
    )
    return parser.parse_args()


def setup_logging(output_dir: Path, log_file: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / log_file
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_file: Optional[str], cli_output_dir: Optional[str], reference_file: Optional[str]) -> Dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)

    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as file_obj:
            override = json.load(file_obj)
        config = deep_merge(config, override)

    if cli_output_dir:
        config["general"]["output_dir"] = cli_output_dir

    if reference_file:
        config["reference_integrity"]["enabled"] = True
        config["reference_integrity"]["reference_file"] = reference_file

    return config


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(col).strip().upper().replace(" ", "_") for col in normalized.columns]
    return normalized


def preprocess_dataframe(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    processed = df.copy()

    if config["general"].get("trim_whitespace", True):
        object_cols = processed.select_dtypes(include=["object", "string"]).columns
        for col in object_cols:
            processed[col] = processed[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )

    if config["general"].get("treat_blank_as_null", True):
        processed = processed.replace(r"^\s*$", np.nan, regex=True)

    return processed


def load_csv(file_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(
        path,
        sep=config["general"].get("delimiter", ","),
        encoding=config["general"].get("encoding", "utf-8"),
        dtype=str,
        keep_default_na=True,
        na_values=["", "NA", "N/A", "NULL", "null", "None"],
    )

    if config["general"].get("normalize_column_names", True):
        df = normalize_columns(df)

    df = preprocess_dataframe(df, config)
    return df


def flatten_xml_element(
    element: ET.Element,
    parent_path: str = "",
    flatten_attributes: bool = True,
    include_root_text: bool = False,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {}
    current_path = f"{parent_path}_{element.tag}" if parent_path else element.tag

    if flatten_attributes:
        for attr_name, attr_value in element.attrib.items():
            row[f"{current_path}_ATTR_{attr_name}"] = attr_value

    children = list(element)
    text_value = (element.text or "").strip()

    if not children:
        row[current_path] = text_value if text_value != "" else None
        return row

    if include_root_text and text_value:
        row[current_path] = text_value

    child_tag_counts: Dict[str, int] = {}
    for child in children:
        child_tag_counts[child.tag] = child_tag_counts.get(child.tag, 0) + 1

    repeated_child_tags = {tag for tag, count in child_tag_counts.items() if count > 1}

    for child in children:
        if child.tag in repeated_child_tags:
            child_text = (child.text or "").strip()
            key = f"{current_path}_{child.tag}"
            existing = row.get(key)
            if existing is None:
                row[key] = child_text if child_text != "" else None
            else:
                existing_text = "" if existing is None else str(existing)
                new_text = child_text if child_text != "" else ""
                row[key] = "|".join([part for part in [existing_text, new_text] if part != ""]) or None

            if flatten_attributes and child.attrib:
                for attr_name, attr_value in child.attrib.items():
                    attr_key = f"{key}_ATTR_{attr_name}"
                    existing_attr = row.get(attr_key)
                    if existing_attr is None:
                        row[attr_key] = attr_value
                    else:
                        row[attr_key] = f"{existing_attr}|{attr_value}"
        else:
            row.update(
                flatten_xml_element(
                    child,
                    parent_path=current_path,
                    flatten_attributes=flatten_attributes,
                    include_root_text=include_root_text,
                )
            )

    return row

# ============================================================================
# ENHANCED FEATURES: Database Connectivity & Multiple File Format Support
# ============================================================================

def load_excel(file_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    """Load data from Excel file (.xlsx, .xls)"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    sheet_name = config.get("input", {}).get("excel", {}).get("sheet_name", 0)
    
    df = pd.read_excel(
        path,
        sheet_name=sheet_name,
        dtype=str,
        keep_default_na=True,
        na_values=["", "NA", "N/A", "NULL", "null", "None"],
    )
    
    if config["general"].get("normalize_column_names", True):
        df = normalize_columns(df)
    
    df = preprocess_dataframe(df, config)
    return df


def load_json(file_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    """Load data from JSON file"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    json_orient = config.get("input", {}).get("json", {}).get("orient", "records")
    
    df = pd.read_json(
        path,
        orient=json_orient,
        dtype=str,
        convert_dates=False,
    )
    
    if config["general"].get("normalize_column_names", True):
        df = normalize_columns(df)
    
    df = preprocess_dataframe(df, config)
    return df


def load_parquet(file_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    """Load data from Parquet file"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    df = pd.read_parquet(path)
    
    # Convert all columns to string for consistent processing
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    if config["general"].get("normalize_column_names", True):
        df = normalize_columns(df)
    
    df = preprocess_dataframe(df, config)
    return df


def load_from_database(config: Dict[str, Any]) -> pd.DataFrame:
    """Load data from database using connection string and query"""
    if not DB_SUPPORT:
        raise ImportError("SQLAlchemy is required for database connectivity. Install: pip install sqlalchemy")
    
    db_config = config.get("database", {})
    connection_string = db_config.get("connection_string")
    query = db_config.get("query")
    db_type = db_config.get("type", "").lower()
    
    if not connection_string:
        raise ValueError("Database connection_string is required in config")
    if not query:
        raise ValueError("Database query is required in config")
    
    # Check for specific database driver availability
    if db_type == "oracle" and not ORACLE_AVAILABLE:
        raise ImportError("cx_Oracle is required for Oracle connectivity. Install: pip install cx_Oracle")
    elif db_type == "sqlserver" and not ODBC_AVAILABLE:
        raise ImportError("pyodbc is required for SQL Server connectivity. Install: pip install pyodbc")
    elif db_type == "mysql" and not MYSQL_AVAILABLE:
        raise ImportError("pymysql is required for MySQL connectivity. Install: pip install pymysql")
    elif db_type == "postgresql" and not POSTGRES_AVAILABLE:
        raise ImportError("psycopg2 is required for PostgreSQL connectivity. Install: pip install psycopg2-binary")
    
    logging.info(f"Connecting to {db_type} database...")
    
    try:
        engine = create_engine(connection_string)
        
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        
        logging.info(f"Successfully loaded {len(df)} rows from database")
        
        # Convert all columns to string for consistent processing
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        if config["general"].get("normalize_column_names", True):
            df = normalize_columns(df)
        
        df = preprocess_dataframe(df, config)
        return df
        
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise


def load_input_data_enhanced(file_path: Optional[str], config: Dict[str, Any]) -> pd.DataFrame:
    """
    Enhanced data loader supporting multiple sources:
    - CSV, XML, Excel, JSON, Parquet files
    - Database connections (Oracle, SQL Server, MySQL, PostgreSQL)
    """
    # Check if loading from database
    if config.get("database", {}).get("enabled", False):
        return load_from_database(config)
    
    # File-based loading
    if not file_path:
        raise ValueError("Either file_path or database configuration is required")
    
    file_suffix = Path(file_path).suffix.lower()
    
    if file_suffix == ".csv":
        return load_csv(file_path, config)
    elif file_suffix == ".dat":
        # Treat .dat files as delimited text files (like CSV)
        logging.info(f"Loading .dat file as delimited text: {file_path}")
        
        # For .dat files, always auto-detect delimiter (don't use default comma)
        delimiter = None
        
        # Try common delimiters: pipe, comma, tab, semicolon
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            for delim in ['|', ',', '\t', ';']:
                if delim in first_line:
                    delimiter = delim
                    logging.info(f"Auto-detected delimiter: '{delim}'")
                    break
            if not delimiter:
                delimiter = ','  # Default to comma
                logging.warning("Could not detect delimiter, defaulting to comma")
        
        # Update config with detected delimiter at the correct level
        if "general" not in config:
            config["general"] = {}
        config["general"]["delimiter"] = delimiter
        return load_csv(file_path, config)
    elif file_suffix == ".xml":
        return load_xml(file_path, config)
    elif file_suffix in [".xlsx", ".xls"]:
        return load_excel(file_path, config)
    elif file_suffix == ".json":
        return load_json(file_path, config)
    elif file_suffix == ".parquet":
        return load_parquet(file_path, config)
    else:
        raise ValueError(
            f"Unsupported input file type: {file_suffix}. "
            f"Supported types are: .csv, .dat, .xml, .xlsx, .xls, .json, .parquet"
        )


# ============================================================================
# ENHANCED FEATURES: Dashboard & Visualization
# ============================================================================

def generate_quality_dashboard(
    output_dir: Path,
    quality_score: float,
    anomaly_summary_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    column_metrics_df: pd.DataFrame,
    total_rows: int,
) -> None:
    """Generate interactive HTML dashboard with charts and visualizations"""
    
    if not PLOTLY_AVAILABLE:
        logging.warning("Plotly not available. Skipping dashboard generation. Install: pip install plotly")
        return
    
    logging.info("Generating quality dashboard...")
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Overall Quality Score',
            'Issues by Category',
            'Top 10 Columns with Issues',
            'Issue Severity Distribution',
            'Data Completeness',
            'Quality Trend'
        ),
        specs=[
            [{"type": "indicator"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )
    
    # 1. Quality Score Gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=quality_score,
            title={'text': "Quality Score"},
            delta={'reference': 90},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 60], 'color': "red"},
                    {'range': [60, 80], 'color': "orange"},
                    {'range': [80, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=1, col=1
    )
    
    # 2. Issues by Category
    if not anomaly_summary_df.empty and 'category' in anomaly_summary_df.columns:
        category_counts = anomaly_summary_df.groupby('category')['count'].sum().sort_values(ascending=True)
        fig.add_trace(
            go.Bar(
                y=category_counts.index,
                x=category_counts.values,
                orientation='h',
                marker_color='indianred'
            ),
            row=1, col=2
        )
    
    # 3. Top 10 Columns with Issues
    if not column_metrics_df.empty and 'column' in column_metrics_df.columns:
        top_columns = column_metrics_df.nlargest(10, 'issue_count')
        fig.add_trace(
            go.Bar(
                x=top_columns['column'],
                y=top_columns['issue_count'],
                marker_color='lightcoral'
            ),
            row=2, col=1
        )
    
    # 4. Severity Distribution (mock data for now)
    severity_data = {
        'Critical': len(anomaly_summary_df[anomaly_summary_df['count'] > total_rows * 0.1]) if not anomaly_summary_df.empty else 0,
        'High': len(anomaly_summary_df[(anomaly_summary_df['count'] > total_rows * 0.05) & (anomaly_summary_df['count'] <= total_rows * 0.1)]) if not anomaly_summary_df.empty else 0,
        'Medium': len(anomaly_summary_df[(anomaly_summary_df['count'] > total_rows * 0.01) & (anomaly_summary_df['count'] <= total_rows * 0.05)]) if not anomaly_summary_df.empty else 0,
        'Low': len(anomaly_summary_df[anomaly_summary_df['count'] <= total_rows * 0.01]) if not anomaly_summary_df.empty else 0,
    }
    fig.add_trace(
        go.Pie(
            labels=list(severity_data.keys()),
            values=list(severity_data.values()),
            marker_colors=['red', 'orange', 'yellow', 'lightgreen']
        ),
        row=2, col=2
    )
    
    # 5. Data Completeness by Column
    if not profile_df.empty and 'column' in profile_df.columns:
        completeness = profile_df.copy()
        if 'null_count' in completeness.columns:
            completeness['completeness'] = ((total_rows - completeness['null_count']) / total_rows * 100)
            top_incomplete = completeness.nsmallest(10, 'completeness')
            fig.add_trace(
                go.Bar(
                    x=top_incomplete['column'],
                    y=top_incomplete['completeness'],
                    marker_color='lightblue'
                ),
                row=3, col=1
            )
    
    # 6. Quality Trend (placeholder)
    fig.add_trace(
        go.Scatter(
            x=['Run 1', 'Run 2', 'Run 3', 'Current'],
            y=[75, 80, 85, quality_score],
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=10)
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="Data Quality Dashboard",
        showlegend=False,
        height=1200,
        template="plotly_white"
    )
    
    # Save dashboard
    dashboard_path = output_dir / "dq_dashboard.html"
    fig.write_html(str(dashboard_path))
    logging.info(f"Dashboard saved to: {dashboard_path}")
    
    # Also generate static charts if matplotlib is available
    if VISUALIZATION_AVAILABLE:
        generate_static_charts(output_dir, quality_score, anomaly_summary_df, profile_df, total_rows)


def generate_static_charts(
    output_dir: Path,
    quality_score: float,
    anomaly_summary_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    total_rows: int,
) -> None:
    """Generate static PNG charts using matplotlib"""
    
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    
    # Set style
    sns.set_style("whitegrid")
    
    # 1. Quality Score Chart
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['red' if quality_score < 60 else 'orange' if quality_score < 80 else 'yellow' if quality_score < 90 else 'green']
    ax.barh(['Quality Score'], [quality_score], color=colors)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score')
    ax.set_title('Overall Data Quality Score')
    for i, v in enumerate([quality_score]):
        ax.text(v + 2, i, f'{v:.1f}%', va='center')
    plt.tight_layout()
    plt.savefig(charts_dir / 'quality_score.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Issues by Category
    if not anomaly_summary_df.empty and 'category' in anomaly_summary_df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        category_counts = anomaly_summary_df.groupby('category')['count'].sum().sort_values()
        category_counts.plot(kind='barh', ax=ax, color='coral')
        ax.set_xlabel('Number of Issues')
        ax.set_title('Issues by Category')
        plt.tight_layout()
        plt.savefig(charts_dir / 'issues_by_category.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # 3. Data Completeness
    if not profile_df.empty and 'column' in profile_df.columns and 'null_count' in profile_df.columns:
        fig, ax = plt.subplots(figsize=(12, 6))
        completeness = profile_df.copy()
        completeness['completeness'] = ((total_rows - completeness['null_count']) / total_rows * 100)
        top_incomplete = completeness.nsmallest(15, 'completeness')
        top_incomplete.plot(x='column', y='completeness', kind='bar', ax=ax, color='skyblue', legend=False)
        ax.set_ylabel('Completeness %')
        ax.set_xlabel('Column')
        ax.set_title('Data Completeness by Column (Top 15 Incomplete)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(charts_dir / 'data_completeness.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    logging.info(f"Static charts saved to: {charts_dir}")


# ============================================================================
# ENHANCED FEATURES: Data Aggregation
# ============================================================================

def aggregate_quality_metrics(
    df: pd.DataFrame,
    anomaly_summary_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Aggregate quality metrics for reporting and analysis
    Provides summary statistics grouped by various dimensions
    """
    aggregations = []
    
    # Overall aggregation
    total_records = len(df)
    total_columns = len(df.columns)
    total_issues = anomaly_summary_df['count'].sum() if not anomaly_summary_df.empty else 0
    
    aggregations.append({
        'dimension': 'Overall',
        'group': 'All Data',
        'total_records': total_records,
        'total_columns': total_columns,
        'total_issues': int(total_issues),
        'issue_rate': (total_issues / total_records * 100) if total_records > 0 else 0,
    })
    
    # By category aggregation
    if not anomaly_summary_df.empty and 'category' in anomaly_summary_df.columns:
        category_agg = anomaly_summary_df.groupby('category').agg({
            'count': 'sum'
        }).reset_index()
        
        for _, row in category_agg.iterrows():
            aggregations.append({
                'dimension': 'Category',
                'group': row['category'],
                'total_records': total_records,
                'total_columns': total_columns,
                'total_issues': int(row['count']),
                'issue_rate': (row['count'] / total_records * 100) if total_records > 0 else 0,
            })
    
    # By column aggregation
    if not profile_df.empty and 'column' in profile_df.columns:
        for _, row in profile_df.iterrows():
            null_count = row.get('null_count', 0)
            aggregations.append({
                'dimension': 'Column',
                'group': row['column'],
                'total_records': total_records,
                'total_columns': 1,
                'total_issues': int(null_count),
                'issue_rate': (null_count / total_records * 100) if total_records > 0 else 0,
            })
    
    agg_df = pd.DataFrame(aggregations)
    return agg_df



def load_xml(file_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    xml_cfg = config.get("input", {}).get("xml", {})
    record_tag = str(xml_cfg.get("record_tag", "")).strip()
    flatten_attributes = bool(xml_cfg.get("flatten_attributes", True))
    include_root_text = bool(xml_cfg.get("include_root_text", False))

    tree = ET.parse(path)
    root = tree.getroot()

    if record_tag:
        record_elements = root.findall(f".//{record_tag}")
        if not record_elements and root.tag == record_tag:
            record_elements = [root]
    else:
        candidate_records = list(root)
        if candidate_records:
            record_elements = candidate_records
        else:
            record_elements = [root]

    rows: List[Dict[str, Any]] = []
    for element in record_elements:
        row = flatten_xml_element(
            element,
            parent_path="",
            flatten_attributes=flatten_attributes,
            include_root_text=include_root_text,
        )
        rows.append(row)

    df = pd.DataFrame(rows)
    if config["general"].get("normalize_column_names", True):
        df = normalize_columns(df)

    df = preprocess_dataframe(df, config)
    return df


def load_input_data(file_path: str, config: Dict[str, Any]) -> pd.DataFrame:
    file_suffix = Path(file_path).suffix.lower()

    if file_suffix == ".csv":
        return load_csv(file_path, config)
    if file_suffix == ".xml":
        return load_xml(file_path, config)

    raise ValueError(f"Unsupported input file type: {file_suffix}. Supported types are .csv and .xml")


def get_series(df: pd.DataFrame, column_name: str) -> pd.Series:
    value = df.loc[:, column_name]
    if isinstance(value, pd.Series):
        return value
    if isinstance(value, pd.DataFrame):
        return value.iloc[:, 0]
    raise TypeError(f"Column '{column_name}' did not resolve to a pandas Series")


def ensure_series(value: Any, index: pd.Index) -> pd.Series:
    if isinstance(value, pd.Series):
        return value
    if isinstance(value, pd.DataFrame):
        return value.iloc[:, 0]
    if isinstance(value, np.ndarray):
        return pd.Series(value, index=index)
    return pd.Series(value, index=index)


def safe_numeric(series: pd.Series) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    return ensure_series(converted, series.index)


def safe_datetime(series: pd.Series, date_format: Optional[str] = None) -> pd.Series:
    converted = pd.to_datetime(series, format=date_format, errors="coerce")
    return ensure_series(converted, series.index)


def scalar_str(value: Any) -> str:
    if isinstance(value, pd.Series):
        return str(value.iloc[0]) if not value.empty else ""
    if isinstance(value, np.ndarray):
        return str(value[0]) if value.size else ""
    return str(value)


def scalar_int(value: Any) -> int:
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else 0
    elif isinstance(value, np.ndarray):
        value = value[0] if value.size else 0
    return int(value)


def scalar_float(value: Any) -> float:
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else 0.0
    elif isinstance(value, np.ndarray):
        value = value[0] if value.size else 0.0
    return float(value)


def ensure_dataframe(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, pd.Series):
        return value.to_frame()
    if value is None:
        return pd.DataFrame()
    return pd.DataFrame(value)


def dataframe_records(df: Any) -> List[Dict[str, Any]]:
    safe_df = ensure_dataframe(df)
    records: List[Dict[str, Any]] = []
    for row_idx in range(len(safe_df.index)):
        row_dict: Dict[str, Any] = {}
        for col_idx, col in enumerate(safe_df.columns):
            row_dict[str(col)] = safe_df.iat[row_idx, col_idx]
        records.append(row_dict)
    return records


def profile_data(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    row_count, column_count = df.shape
    summary_rows: List[Dict[str, Any]] = [
        {"metric": "row_count", "value": row_count},
        {"metric": "column_count", "value": column_count},
        {"metric": "generated_at", "value": datetime.now(UTC).isoformat()},
    ]

    top_n = config["general"].get("top_n_frequent_values", 5)
    profile_rows: List[Dict[str, Any]] = []

    for col in df.columns:
        series = get_series(df, col)
        non_null = series.notna().sum()
        null_count = series.isna().sum()
        distinct_count = series.nunique(dropna=True)
        inferred_dtype = pd.api.types.infer_dtype(series.dropna(), skipna=True)
        has_non_null = bool(series.notna().any())
        blanks_count = int(series.astype(str).str.strip().eq("").sum()) if has_non_null else 0
        value_counts = series.dropna().astype(str).value_counts().head(top_n).to_dict()

        profile_rows.append(
            {
                "column_name": col,
                "inferred_dtype": inferred_dtype,
                "row_count": row_count,
                "non_null_count": int(non_null),
                "null_count": int(null_count),
                "blank_count": int(blanks_count),
                "null_percentage": round((null_count / row_count) * 100, 2) if row_count else 0.0,
                "distinct_count": int(distinct_count),
                "distinct_ratio": round((distinct_count / row_count), 4) if row_count else 0.0,
                "top_values": json.dumps(value_counts, ensure_ascii=False),
            }
        )

    profile_df = pd.DataFrame(profile_rows)

    numeric_stats_frames: List[pd.DataFrame] = []
    for col in df.columns:
        numeric_series = safe_numeric(get_series(df, col))
        if numeric_series.notna().sum() > 0:
            stats = numeric_series.describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
            stats["column_name"] = col
            numeric_stats_frames.append(pd.DataFrame([stats]))

    numeric_stats_df = (
        pd.concat(numeric_stats_frames, ignore_index=True)
        if numeric_stats_frames
        else pd.DataFrame(columns=["column_name", "count", "mean", "std", "min", "25%", "50%", "75%", "max"])
    )

    summary_df = pd.DataFrame(summary_rows)
    return summary_df, profile_df, numeric_stats_df


def build_issue_records(
    df: pd.DataFrame,
    mask: pd.Series,
    issue_type: str,
    issue_detail: str,
    columns_involved: Optional[List[str]] = None,
) -> pd.DataFrame:
    if mask is None or mask.sum() == 0:
        return pd.DataFrame()

    issue_df = df.loc[mask].copy()
    issue_df.insert(0, "issue_type", issue_type)
    issue_df.insert(1, "issue_detail", issue_detail)
    issue_df.insert(
        2,
        "columns_involved",
        ",".join(columns_involved) if columns_involved else "",
    )
    return issue_df


def detect_null_and_blank_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col in df.columns:
        null_mask = df[col].isna()
        blank_mask = df[col].astype(str).str.strip().eq("") & df[col].notna()

        if null_mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    ensure_series(null_mask, df.index),
                    "null_blank",
                    f"Null values detected in column {col}",
                    [col],
                )
            )
        if blank_mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    ensure_series(blank_mask, df.index),
                    "null_blank",
                    f"Blank values detected in column {col}",
                    [col],
                )
            )

        summary_rows.append(
            {
                "category": "null_blank",
                "column_name": col,
                "count": int(null_mask.sum() + blank_mask.sum()),
            }
        )

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def detect_duplicate_records(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    duplicate_mask = df.duplicated(keep=False)
    issues_df = build_issue_records(
        df,
        duplicate_mask,
        "duplicates",
        "Exact duplicate rows detected across all columns",
        list(df.columns),
    )
    summary = {
        "category": "duplicates",
        "column_name": "ALL_COLUMNS",
        "count": int(duplicate_mask.sum()),
    }
    return issues_df, summary


def detect_duplicate_primary_keys(df: pd.DataFrame, primary_keys: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    valid_keys = [col for col in primary_keys if col in df.columns]
    if not valid_keys:
        return pd.DataFrame(), {
            "category": "duplicate_primary_keys",
            "column_name": ",".join(primary_keys),
            "count": 0,
        }

    subset = df[valid_keys].copy()
    non_null_key_mask = subset.notna().all(axis=1)
    duplicate_key_subset = subset.loc[non_null_key_mask, :]
    duplicate_key_mask = duplicate_key_subset.duplicated(keep=False)
    full_mask = pd.Series(False, index=df.index, dtype=bool)
    full_mask.loc[duplicate_key_subset.index] = duplicate_key_mask.to_numpy()

    issues_df = build_issue_records(
        df,
        full_mask,
        "duplicate_primary_keys",
        f"Duplicate business key values detected for {valid_keys}; rows may differ in non-key columns",
        valid_keys,
    )
    summary = {
        "category": "duplicate_primary_keys",
        "column_name": ",".join(valid_keys),
        "count": int(full_mask.sum()),
    }
    return issues_df, summary


def detect_outliers(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    anomaly_cfg = config["anomaly_detection"]
    default_method = anomaly_cfg.get("outlier_method", "iqr").lower()
    default_iqr_multiplier = float(anomaly_cfg.get("iqr_multiplier", 1.5))
    default_zscore_threshold = float(anomaly_cfg.get("zscore_threshold", 3.0))
    min_sample_size = int(anomaly_cfg.get("outlier_min_sample_size", 5))
    target_columns = anomaly_cfg.get("outlier_columns", []) or list(df.columns)
    column_overrides = anomaly_cfg.get("outlier_column_overrides", {})

    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col in target_columns:
        if col not in df.columns:
            summary_rows.append({"category": "outliers", "column_name": col, "count": 0})
            continue

        numeric_series = safe_numeric(get_series(df, col))
        valid = numeric_series.dropna()
        if valid.shape[0] < min_sample_size:
            summary_rows.append({"category": "outliers", "column_name": col, "count": 0})
            continue

        col_cfg = column_overrides.get(col, {})
        method = str(col_cfg.get("method", default_method)).lower()
        iqr_multiplier = float(col_cfg.get("iqr_multiplier", default_iqr_multiplier))
        zscore_threshold = float(col_cfg.get("zscore_threshold", default_zscore_threshold))

        if method == "zscore":
            std_dev = valid.std(ddof=0)
            if bool(pd.isna(std_dev)) or std_dev == 0:
                mask = pd.Series(False, index=df.index)
                threshold_detail = f"Z-score threshold={zscore_threshold}"
            else:
                mean_val = valid.mean()
                zscores = (numeric_series - mean_val) / std_dev
                mask = zscores.abs() > zscore_threshold
                threshold_detail = f"Z-score threshold={zscore_threshold}"
        else:
            q1 = valid.quantile(0.25)
            q3 = valid.quantile(0.75)
            iqr = q3 - q1
            if pd.isna(iqr) or iqr == 0:
                mask = pd.Series(False, index=df.index)
                threshold_detail = f"IQR multiplier={iqr_multiplier}"
            else:
                lower = q1 - (iqr_multiplier * iqr)
                upper = q3 + (iqr_multiplier * iqr)
                mask = (numeric_series < lower) | (numeric_series > upper)
                threshold_detail = f"IQR multiplier={iqr_multiplier}, lower={round(lower, 4)}, upper={round(upper, 4)}"

        mask = mask.fillna(False)
        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "outliers",
                    f"Outliers detected in numeric column {col} using {method.upper()} method ({threshold_detail})",
                    [col],
                )
            )

        summary_rows.append({"category": "outliers", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def detect_mixed_datatypes(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    columns = config["rules"].get("mixed_type_check_columns", list(df.columns))
    mixed_type_rules = config["rules"].get("mixed_type_rules", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col in columns:
        if col not in df.columns:
            continue

        rule = mixed_type_rules.get(col, {})
        expected_type = str(rule.get("expected_type", "")).lower()
        date_format = rule.get("format")
        non_null_mask = df[col].notna()

        if not bool(non_null_mask.any()):
            summary_rows.append({"category": "mixed_types", "column_name": col, "count": 0})
            continue

        if expected_type == "numeric":
            converted = safe_numeric(get_series(df, col))
            invalid_mask = non_null_mask & converted.isna()
            detail = f"Non-numeric values detected in column {col} expected to be numeric"
        elif expected_type == "date":
            converted = safe_datetime(get_series(df, col), date_format)
            invalid_mask = non_null_mask & converted.isna()
            detail = f"Non-date values detected in column {col} expected to follow date format"
        elif expected_type == "string":
            numeric_like_mask = df[col].astype("string").fillna("").str.fullmatch(r"[-+]?\d*\.?\d+", na=False)
            date_like_mask = df[col].astype("string").fillna("").str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
            invalid_mask = non_null_mask & (numeric_like_mask | date_like_mask)
            detail = f"Unexpected numeric/date-like values detected in string column {col}"
        else:
            summary_rows.append({"category": "mixed_types", "column_name": col, "count": 0})
            continue

        invalid_mask = invalid_mask.fillna(False)
        if invalid_mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    invalid_mask,
                    "mixed_types",
                    detail,
                    [col],
                )
            )

        summary_rows.append({"category": "mixed_types", "column_name": col, "count": int(invalid_mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def detect_invalid_dates(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    date_columns = config["rules"].get("date_columns", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col, settings in date_columns.items():
        if col not in df.columns:
            summary_rows.append({"category": "invalid_dates", "column_name": col, "count": 0})
            continue

        date_format = settings.get("format")
        source_series = get_series(df, col)
        converted = safe_datetime(source_series, date_format)
        mask = source_series.notna() & converted.isna()

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "invalid_dates",
                    f"Invalid date format detected in column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "invalid_dates", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def detect_invalid_emails(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    email_columns = config["rules"].get("email_columns", [])
    email_rules = config["rules"].get("email_rules", {})
    fallback_pattern = config["rules"].get("regex_rules", {}).get("EMAIL", r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col in email_columns:
        if col not in df.columns:
            summary_rows.append({"category": "invalid_emails", "column_name": col, "count": 0})
            continue

        col_rule = email_rules.get(col, {})
        pattern_text = col_rule.get("pattern", fallback_pattern)
        allow_blank = bool(col_rule.get("allow_blank", True))
        normalize_case = bool(col_rule.get("normalize_case", True))
        pattern = re.compile(pattern_text)

        series = df[col].astype("string")
        comparable = series.fillna("")
        if normalize_case:
            comparable = comparable.str.lower().str.strip()
        else:
            comparable = comparable.str.strip()

        populated_mask = comparable.ne("") & series.notna()
        if allow_blank:
            mask = populated_mask & ~comparable.apply(lambda x: bool(pattern.fullmatch(str(x))))
            detail = f"Malformed email syntax detected in column {col}"
        else:
            mask = ~comparable.apply(lambda x: bool(pattern.fullmatch(str(x))))
            detail = f"Missing or malformed email values detected in column {col}"

        mask = mask.fillna(False)

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "invalid_emails",
                    detail,
                    [col],
                )
            )

        summary_rows.append({"category": "invalid_emails", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def detect_negative_values(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    target_columns = config["rules"].get("negative_not_allowed_columns", [])
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col in target_columns:
        if col not in df.columns:
            summary_rows.append({"category": "negative_values", "column_name": col, "count": 0})
            continue

        numeric_series = safe_numeric(get_series(df, col))
        mask = numeric_series < 0

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask.fillna(False),
                    "negative_values",
                    f"Negative values detected in business-sensitive column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "negative_values", "column_name": col, "count": int(mask.fillna(False).sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def detect_special_characters(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    rules = config["rules"].get("special_character_rules", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col, pattern_text in rules.items():
        if col not in df.columns:
            summary_rows.append({"category": "special_characters", "column_name": col, "count": 0})
            continue

        pattern = re.compile(pattern_text)
        mask = df[col].notna() & ~df[col].astype("string").fillna("").apply(lambda x: bool(pattern.fullmatch(str(x))))

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "special_characters",
                    f"Unexpected special characters detected in column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "special_characters", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def validate_mandatory_columns(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    mandatory_columns = config["rules"].get("mandatory_columns", [])
    missing_columns = [col for col in mandatory_columns if col not in df.columns]

    if not missing_columns:
        return pd.DataFrame(), {
            "category": "missing_mandatory_columns",
            "column_name": "STRUCTURE",
            "count": 0,
        }

    issue_df = pd.DataFrame(
        {
            "issue_type": ["missing_mandatory_columns"] * len(missing_columns),
            "issue_detail": ["Mandatory column missing"] * len(missing_columns),
            "columns_involved": missing_columns,
        }
    )

    return issue_df, {
        "category": "missing_mandatory_columns",
        "column_name": "STRUCTURE",
        "count": len(missing_columns),
    }


def validate_mandatory_fields(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    mandatory_fields = config["rules"].get("mandatory_fields", [])
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col in mandatory_fields:
        if col not in df.columns:
            summary_rows.append({"category": "mandatory_field_violations", "column_name": col, "count": 0})
            continue

        mask = df[col].isna() | df[col].astype(str).str.strip().eq("")
        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "mandatory_field_violations",
                    f"Mandatory field violations detected in column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "mandatory_field_violations", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def validate_datatype_rules(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    dtype_rules = config["rules"].get("dtype_rules", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col, expected_type in dtype_rules.items():
        if col not in df.columns:
            summary_rows.append({"category": "datatype_violations", "column_name": col, "count": 0})
            continue

        expected_type = str(expected_type).lower()
        if expected_type == "numeric":
            converted = safe_numeric(get_series(df, col))
            mask = df[col].notna() & converted.isna()
        elif expected_type == "date":
            date_format = config["rules"].get("date_columns", {}).get(col, {}).get("format")
            converted = safe_datetime(get_series(df, col), date_format)
            mask = df[col].notna() & converted.isna()
        elif expected_type == "string":
            mask = pd.Series(False, index=df.index)
        else:
            mask = pd.Series(False, index=df.index)

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "datatype_violations",
                    f"Datatype validation failed for column {col}; expected {expected_type}",
                    [col],
                )
            )

        summary_rows.append({"category": "datatype_violations", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def validate_range_rules(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    range_rules = config["rules"].get("range_rules", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col, rule in range_rules.items():
        if col not in df.columns:
            summary_rows.append({"category": "range_violations", "column_name": col, "count": 0})
            continue

        numeric_series = safe_numeric(get_series(df, col))
        min_val = rule.get("min")
        max_val = rule.get("max")

        mask = pd.Series(False, index=df.index)
        if min_val is not None:
            mask = mask | (numeric_series < min_val)
        if max_val is not None:
            mask = mask | (numeric_series > max_val)

        mask = mask.fillna(False)

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "range_violations",
                    f"Range validation failed for column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "range_violations", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def validate_pattern_rules(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    regex_rules = config["rules"].get("regex_rules", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col, pattern_text in regex_rules.items():
        if col not in df.columns:
            summary_rows.append({"category": "pattern_violations", "column_name": col, "count": 0})
            continue

        pattern = re.compile(pattern_text)
        mask = df[col].notna() & ~df[col].astype("string").fillna("").apply(lambda x: bool(pattern.fullmatch(str(x))))

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "pattern_violations",
                    f"Regex pattern validation failed for column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "pattern_violations", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def validate_allowed_values(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    allowed_values = config["rules"].get("allowed_values", {})
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for col, allowed in allowed_values.items():
        if col not in df.columns:
            summary_rows.append({"category": "allowed_value_violations", "column_name": col, "count": 0})
            continue

        allowed_list = [str(x) for x in allowed]
        source_series = get_series(df, col)
        mask = source_series.notna() & ~source_series.astype(str).isin(allowed_list)

        if mask.sum() > 0:
            issue_frames.append(
                build_issue_records(
                    df,
                    mask,
                    "allowed_value_violations",
                    f"Unexpected values detected in column {col}",
                    [col],
                )
            )

        summary_rows.append({"category": "allowed_value_violations", "column_name": col, "count": int(mask.sum())})

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def validate_referential_integrity(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    ref_cfg = config.get("reference_integrity", {})
    if not ref_cfg.get("enabled", False):
        return pd.DataFrame(), {
            "category": "referential_integrity",
            "column_name": "REFERENCE",
            "count": 0,
        }

    reference_file = ref_cfg.get("reference_file")
    source_column = ref_cfg.get("source_column")
    reference_column = ref_cfg.get("reference_column")

    if not reference_file or not source_column or not reference_column:
        return pd.DataFrame(), {
            "category": "referential_integrity",
            "column_name": source_column or "REFERENCE",
            "count": 0,
        }

    if source_column not in df.columns:
        return pd.DataFrame(), {
            "category": "referential_integrity",
            "column_name": source_column,
            "count": 0,
        }

    reference_df = pd.read_csv(
        reference_file,
        sep=ref_cfg.get("reference_delimiter", ","),
        encoding=ref_cfg.get("reference_encoding", "utf-8"),
        dtype=str,
    )
    reference_df = normalize_columns(reference_df)

    if reference_column not in reference_df.columns:
        return pd.DataFrame(), {
            "category": "referential_integrity",
            "column_name": source_column,
            "count": 0,
        }

    reference_values = reference_df[reference_column].dropna().astype(str).unique().tolist()
    source_series = get_series(df, source_column)
    mask = source_series.notna() & ~source_series.astype(str).isin(reference_values)

    issues_df = build_issue_records(
        df,
        mask,
        "referential_integrity",
        f"Referential integrity failed for source column {source_column}",
        [source_column, reference_column],
    )
    summary = {
        "category": "referential_integrity",
        "column_name": source_column,
        "count": int(mask.sum()),
    }
    return issues_df, summary


def evaluate_condition(series: pd.Series, operator: str, value: Any) -> pd.Series:
    operator = operator.lower()
    compare_series = series.astype(str)

    if operator == "equals":
        return compare_series == str(value)
    if operator == "not_equals":
        return compare_series != str(value)
    if operator == "in":
        valid_set = {str(v) for v in value}
        return compare_series.isin(valid_set)
    if operator == "not_in":
        invalid_set = {str(v) for v in value}
        return ~compare_series.isin(invalid_set)

    numeric_series = safe_numeric(series)
    if operator == "gt":
        return numeric_series > float(value)
    if operator == "gte":
        return numeric_series >= float(value)
    if operator == "lt":
        return numeric_series < float(value)
    if operator == "lte":
        return numeric_series <= float(value)

    return pd.Series(False, index=series.index)


def validate_business_rules(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    business_rules = config.get("business_rules", [])
    issue_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, Any]] = []

    for rule in business_rules:
        name = rule.get("name", "unnamed_business_rule")
        rule_type = rule.get("type")
        count = 0

        if rule_type == "conditional_required":
            if_cfg = rule.get("if", {})
            then_cfg = rule.get("then", {})

            source_col = if_cfg.get("column")
            operator = if_cfg.get("operator", "equals")
            source_val = if_cfg.get("value")
            required_col = then_cfg.get("required_column")

            if source_col in df.columns and required_col in df.columns:
                source_series = get_series(df, source_col)
                required_series = get_series(df, required_col)
                condition_mask = evaluate_condition(source_series, operator, source_val)
                violation_mask = condition_mask & (required_series.isna() | required_series.astype(str).str.strip().eq(""))
                count = int(violation_mask.sum())

                if count > 0:
                    issue_frames.append(
                        build_issue_records(
                            df,
                            violation_mask,
                            "business_rule_violations",
                            f"Business rule '{name}' failed",
                            [source_col, required_col],
                        )
                    )

        summary_rows.append(
            {
                "category": "business_rule_violations",
                "column_name": name,
                "count": count,
            }
        )

    issues_df = pd.concat(issue_frames, ignore_index=True) if issue_frames else pd.DataFrame()
    return issues_df, summary_rows


def compute_quality_score(anomaly_summary_df: pd.DataFrame, config: Dict[str, Any], total_rows: int, bad_records_count: int = 0) -> Tuple[float, pd.DataFrame]:
    """
    Compute quality score based on percentage of clean records.
    
    The quality score directly reflects the percentage of records that are completely clean (no issues).
    This provides a more intuitive and accurate measure of data quality.
    
    Args:
        anomaly_summary_df: DataFrame with anomaly counts by category
        config: Configuration dictionary with scoring weights
        total_rows: Total number of records
        bad_records_count: Number of records with at least one issue
    
    Returns:
        Tuple of (quality_score, score_breakdown_df)
    """
    weights = config["scoring"].get("weights", {})
    if anomaly_summary_df.empty or total_rows <= 0:
        return 100.0, pd.DataFrame(columns=["category", "weighted_penalty"])

    # Calculate quality score based on clean records percentage
    # This is the most intuitive measure: % of records with NO issues
    clean_records_count = total_rows - bad_records_count
    quality_score_clean_records = (clean_records_count / total_rows * 100) if total_rows > 0 else 100.0
    
    # Also calculate weighted penalty score for detailed breakdown
    category_counts = anomaly_summary_df.groupby("category", as_index=False)["count"].sum()
    weighted_rows: List[Dict[str, Any]] = []
    penalty_score = 0.0

    category_records = dataframe_records(category_counts)
    for row in category_records:
        category = scalar_str(row.get("category", ""))
        count = scalar_float(row.get("count", 0))
        weight = float(weights.get(category, 5))
        ratio = min(count / total_rows, 1.0)
        weighted_penalty = ratio * weight
        penalty_score += weighted_penalty
        weighted_rows.append(
            {
                "category": category,
                "count": count,
                "weight": weight,
                "weighted_penalty": round(weighted_penalty, 4),
            }
        )

    # Use clean records percentage as the primary quality score
    # This is more intuitive: if 76% of records are bad, quality score should be 24%
    final_score = max(0.0, round(quality_score_clean_records, 2))
    
    return final_score, pd.DataFrame(weighted_rows)


def build_column_quality_metrics(
    profile_df: pd.DataFrame,
    anomaly_summary_df: pd.DataFrame,
    total_rows: int,
) -> pd.DataFrame:
    if profile_df.empty:
        return pd.DataFrame()

    category_pivot = (
        anomaly_summary_df.pivot_table(
            index="column_name",
            columns="category",
            values="count",
            aggfunc="sum",
            fill_value=0,
        )
        if not anomaly_summary_df.empty
        else pd.DataFrame()
    )

    merged = profile_df.merge(
        category_pivot,
        how="left",
        left_on="column_name",
        right_index=True,
    )

    merged = merged.fillna(0)

    anomaly_cols = [
        col for col in merged.columns
        if col not in {
            "column_name",
            "inferred_dtype",
            "row_count",
            "non_null_count",
            "null_count",
            "blank_count",
            "null_percentage",
            "distinct_count",
            "distinct_ratio",
            "top_values",
        }
    ]

    if anomaly_cols and total_rows > 0:
        merged["total_anomaly_count"] = merged[anomaly_cols].sum(axis=1)
        merged["column_quality_score"] = (
            100 - ((merged["total_anomaly_count"] / total_rows) * 100)
        ).clip(lower=0).round(2)
    else:
        merged["total_anomaly_count"] = 0
        merged["column_quality_score"] = 100.0

    return merged


def generate_recommendations(anomaly_summary_df: pd.DataFrame) -> pd.DataFrame:
    recommendations_map = {
        "null_blank": "Impute, backfill, or enforce non-null source validations.",
        "duplicates": "Apply deduplication logic and enforce unique row checks in ETL.",
        "duplicate_primary_keys": "Enforce primary key uniqueness before load.",
        "outliers": "Review business thresholds and validate source extraction anomalies.",
        "mixed_types": "Cast columns explicitly and add type validation in ingestion stage.",
        "invalid_dates": "Standardize date formats and reject malformed date strings.",
        "invalid_emails": "Validate email patterns at capture time and quarantine invalid rows.",
        "negative_values": "Apply non-negative constraints for sensitive business metrics.",
        "special_characters": "Sanitize text inputs and apply regex cleansing rules.",
        "datatype_violations": "Introduce schema enforcement and pre-load casting tests.",
        "range_violations": "Add min/max validation gates in ETL pipeline.",
        "pattern_violations": "Use regex-based checks in source forms and ETL transformations.",
        "allowed_value_violations": "Use lookup/reference validation for domain-controlled fields.",
        "missing_mandatory_columns": "Validate input schema before processing starts.",
        "mandatory_field_violations": "Block records with nulls in critical fields or route to quarantine.",
        "referential_integrity": "Validate foreign keys against master/reference dataset before load.",
        "business_rule_violations": "Encode business rules in ETL tests and monitor failures over time.",
    }

    preventive_controls = {
        "null_blank": "Add source mandatory-field controls and upstream completeness dashboards.",
        "duplicates": "Implement dedupe keys and idempotent load design.",
        "duplicate_primary_keys": "Use unique key constraints in staging and target layers.",
        "outliers": "Add statistical threshold alerts and anomaly monitoring.",
        "mixed_types": "Define contract-first schemas and ingestion validators.",
        "invalid_dates": "Force ISO date ingestion and date parser validation.",
        "invalid_emails": "Use field-level regex validation in UI/API layers.",
        "negative_values": "Apply business constraints and reject invalid transactions early.",
        "special_characters": "Introduce input sanitization and approved character policies.",
        "datatype_violations": "Automate schema checks in CI/CD for ETL pipelines.",
        "range_violations": "Establish rule catalog for valid numeric boundaries.",
        "pattern_violations": "Centralize regex standards and re-use across pipelines.",
        "allowed_value_violations": "Use governed master data and lookup-controlled values.",
        "missing_mandatory_columns": "Implement schema registry and contract validation.",
        "mandatory_field_violations": "Add source completeness SLAs and null-prevention checks.",
        "referential_integrity": "Maintain authoritative reference datasets and key synchronization.",
        "business_rule_violations": "Version-control business rules and test them automatically.",
    }

    testing_suggestions = {
        "null_blank": "Add row-level completeness tests for mandatory fields.",
        "duplicates": "Add duplicate row detection tests after transformation and before load.",
        "duplicate_primary_keys": "Add uniqueness tests for primary key columns in ETL.",
        "outliers": "Add threshold-based anomaly tests on sensitive numeric columns.",
        "mixed_types": "Add schema conformance tests on typed columns.",
        "invalid_dates": "Add strict date parsing tests for date fields.",
        "invalid_emails": "Add regex validation tests for email fields.",
        "negative_values": "Add non-negative assertions for financial and demographic metrics.",
        "special_characters": "Add regex sanitation tests for text fields.",
        "datatype_violations": "Add datatype contract tests between stages.",
        "range_violations": "Add min/max validation tests for numeric fields.",
        "pattern_violations": "Add regex rule tests for domain-formatted columns.",
        "allowed_value_violations": "Add accepted-values tests for categorical columns.",
        "missing_mandatory_columns": "Add schema-presence tests before ETL execution.",
        "mandatory_field_violations": "Add non-null tests for required fields.",
        "referential_integrity": "Add foreign-key validation tests against reference data.",
        "business_rule_violations": "Add custom rule-based assertions for cross-column logic.",
    }

    rows: List[Dict[str, Any]] = []
    if anomaly_summary_df.empty:
        return pd.DataFrame(
            [
                {
                    "category": "none",
                    "count": 0,
                    "recommendation": "No anomalies detected.",
                    "testing_suggestion": "Maintain current validation coverage.",
                    "preventive_control": "Continue monitoring.",
                }
            ]
        )

    grouped = anomaly_summary_df.groupby("category", as_index=False)["count"].sum()

    grouped_records = dataframe_records(grouped)
    for row in grouped_records:
        category = scalar_str(row.get("category", ""))
        rows.append(
            {
                "category": category,
                "count": scalar_int(row.get("count", 0)),
                "recommendation": recommendations_map.get(category, "Review and remediate source/system issues."),
                "testing_suggestion": testing_suggestions.get(category, "Add automated ETL validation for this issue type."),
                "preventive_control": preventive_controls.get(category, "Introduce monitoring and source controls."),
            }
        )

    return pd.DataFrame(rows)


def export_dataframe(df: pd.DataFrame, file_path: Path, skip_if_empty: bool = False) -> None:
    """
    Export dataframe to CSV file.
    
    Args:
        df: DataFrame to export
        file_path: Path to save the CSV file
        skip_if_empty: If True, skip file creation when dataframe is empty
    """
    if df is None or df.empty:
        if skip_if_empty:
            logging.info(f"Skipping empty file: {file_path.name}")
            return
        pd.DataFrame().to_csv(file_path, index=False)
    else:
        df.to_csv(file_path, index=False)


def export_excel_report(
    output_path: Path,
    summary_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    numeric_stats_df: pd.DataFrame,
    anomaly_summary_df: pd.DataFrame,
    score_df: pd.DataFrame,
    column_metrics_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
) -> None:
    try:
        with pd.ExcelWriter(output_path) as writer:
            summary_df.to_excel(writer, sheet_name="summary", index=False)
            profile_df.to_excel(writer, sheet_name="profile", index=False)
            numeric_stats_df.to_excel(writer, sheet_name="numeric_stats", index=False)
            anomaly_summary_df.to_excel(writer, sheet_name="anomaly_summary", index=False)
            score_df.to_excel(writer, sheet_name="score_breakdown", index=False)
            column_metrics_df.to_excel(writer, sheet_name="column_metrics", index=False)
            recommendations_df.to_excel(writer, sheet_name="recommendations", index=False)
    except Exception as exc:
        logging.warning("Excel export skipped or failed: %s", exc)



def detect_mixed_newline_characters(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect mixed newline characters in a file (common issue with Ab Initio .dat files).
    
    Detects:
    - \\r\\n (Windows/CRLF)
    - \\n (Unix/LF)
    - \\r (Mac/CR)
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Tuple of (issue_df, summary_dict)
    """
    try:
        # Read file in binary mode to detect actual line endings
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Count different line ending types
        crlf_count = content.count(b'\r\n')
        lf_only_count = content.count(b'\n') - crlf_count  # Subtract CRLF occurrences
        cr_only_count = content.count(b'\r') - crlf_count  # Subtract CRLF occurrences
        
        total_lines = crlf_count + lf_only_count + cr_only_count
        
        # Determine if there are mixed line endings
        line_ending_types = sum([
            1 if crlf_count > 0 else 0,
            1 if lf_only_count > 0 else 0,
            1 if cr_only_count > 0 else 0
        ])
        
        has_mixed = line_ending_types > 1
        
        # Determine predominant line ending
        if crlf_count >= lf_only_count and crlf_count >= cr_only_count:
            predominant = "CRLF (\\r\\n)"
            predominant_code = "\\r\\n"
        elif lf_only_count >= cr_only_count:
            predominant = "LF (\\n)"
            predominant_code = "\\n"
        else:
            predominant = "CR (\\r)"
            predominant_code = "\\r"
        
        issue_records = []
        if has_mixed:
            issue_records.append({
                'file': file_path,
                'issue': 'Mixed newline characters detected',
                'crlf_count': crlf_count,
                'lf_count': lf_only_count,
                'cr_count': cr_only_count,
                'total_lines': total_lines,
                'predominant_type': predominant,
                'recommendation': f'Standardize to {predominant}'
            })
        
        issue_df = pd.DataFrame(issue_records)
        
        summary = {
            'category': 'mixed_newline_characters',
            'count': 1 if has_mixed else 0,
            'severity': 'HIGH' if has_mixed else 'NONE',
            'details': {
                'crlf': crlf_count,
                'lf': lf_only_count,
                'cr': cr_only_count,
                'mixed': has_mixed,
                'predominant': predominant_code
            }
        }
        
        if has_mixed:
            logging.warning(f"Mixed newline characters detected in {file_path}")
            logging.warning(f"  CRLF (\\r\\n): {crlf_count}, LF (\\n): {lf_only_count}, CR (\\r): {cr_only_count}")
            logging.warning(f"  Recommendation: Standardize to {predominant}")
        
        return issue_df, summary
        
    except Exception as e:
        logging.error(f"Error detecting newline characters: {e}")
        return pd.DataFrame(), {'category': 'mixed_newline_characters', 'count': 0}


def fix_newline_characters(input_file: str, output_file: str, target_newline: str = '\n') -> Dict[str, Any]:
    """
    Fix mixed newline characters in a file by standardizing to a single type.
    
    Args:
        input_file: Path to input file
        output_file: Path to output file
        target_newline: Target newline character ('\\n', '\\r\\n', or '\\r')
        
    Returns:
        Dictionary with fix statistics
    """
    try:
        # Read file in binary mode
        with open(input_file, 'rb') as f:
            content = f.read()
        
        # Count original line endings
        original_crlf = content.count(b'\r\n')
        original_lf = content.count(b'\n') - original_crlf
        original_cr = content.count(b'\r') - original_crlf
        
        # Convert to string and normalize
        text = content.decode('utf-8', errors='replace')
        
        # Replace all line endings with a temporary marker
        text = text.replace('\r\n', '\n')  # Convert CRLF to LF
        text = text.replace('\r', '\n')    # Convert CR to LF
        
        # Now convert to target line ending
        if target_newline == '\r\n':
            text = text.replace('\n', '\r\n')
            target_name = 'CRLF'
        elif target_newline == '\r':
            text = text.replace('\n', '\r')
            target_name = 'CR'
        else:  # '\n'
            target_name = 'LF'
            # Already in LF format
        
        # Write fixed content
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        
        # Count new line endings
        with open(output_file, 'rb') as f:
            new_content = f.read()
        
        new_crlf = new_content.count(b'\r\n')
        new_lf = new_content.count(b'\n') - new_crlf
        new_cr = new_content.count(b'\r') - new_crlf
        
        result = {
            'success': True,
            'input_file': input_file,
            'output_file': output_file,
            'target_newline': target_name,
            'original': {
                'crlf': original_crlf,
                'lf': original_lf,
                'cr': original_cr
            },
            'fixed': {
                'crlf': new_crlf,
                'lf': new_lf,
                'cr': new_cr
            },
            'lines_fixed': original_crlf + original_lf + original_cr
        }
        
        logging.info(f"Fixed newline characters in {input_file}")
        logging.info(f"  Original: CRLF={original_crlf}, LF={original_lf}, CR={original_cr}")
        logging.info(f"  Fixed to {target_name}: CRLF={new_crlf}, LF={new_lf}, CR={new_cr}")
        logging.info(f"  Output saved to: {output_file}")
        
        return result
        
    except Exception as e:
        logging.error(f"Error fixing newline characters: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def cleanse_data(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply automatic data cleansing to fix common data quality issues.
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        Tuple of (cleansed_df, cleansing_log_df)
    """
    cleansed_df = df.copy()
    cleansing_log = []
    
    logging.info("Starting data cleansing process...")
    
    # 1. Trim whitespace from string columns
    if config["general"].get("trim_whitespace", True):
        for col in cleansed_df.columns:
            if cleansed_df[col].dtype == 'object':
                original_values = cleansed_df[col].copy()
                cleansed_df[col] = cleansed_df[col].astype(str).str.strip()
                changed_count = (original_values != cleansed_df[col]).sum()
                if changed_count > 0:
                    cleansing_log.append({
                        'column': col,
                        'operation': 'trim_whitespace',
                        'records_affected': changed_count,
                        'description': 'Removed leading/trailing whitespace'
                    })
                    logging.info(f"Trimmed whitespace in {col}: {changed_count} records")
    
    # 2. Normalize email addresses
    email_columns = config.get("rules", {}).get("email_columns", [])
    for col in email_columns:
        if col in cleansed_df.columns:
            original_values = cleansed_df[col].copy()
            # Convert to lowercase and strip
            cleansed_df[col] = cleansed_df[col].astype(str).str.lower().str.strip()
            # Replace 'nan' string with actual NaN
            cleansed_df[col] = cleansed_df[col].replace(['nan', 'none', ''], np.nan)
            changed_count = (original_values != cleansed_df[col]).sum()
            if changed_count > 0:
                cleansing_log.append({
                    'column': col,
                    'operation': 'normalize_email',
                    'records_affected': changed_count,
                    'description': 'Converted to lowercase and removed invalid entries'
                })
                logging.info(f"Normalized emails in {col}: {changed_count} records")
    
    # 3. Fix data types
    dtype_rules = config.get("rules", {}).get("dtype_rules", {})
    for col, expected_type in dtype_rules.items():
        if col not in cleansed_df.columns:
            continue
            
        original_values = cleansed_df[col].copy()
        
        if expected_type == "numeric":
            # Convert to numeric, coercing errors to NaN
            cleansed_df[col] = pd.to_numeric(cleansed_df[col], errors='coerce')
            changed_count = (original_values.astype(str) != cleansed_df[col].astype(str)).sum()
            if changed_count > 0:
                cleansing_log.append({
                    'column': col,
                    'operation': 'convert_to_numeric',
                    'records_affected': changed_count,
                    'description': 'Converted to numeric type, invalid values set to NaN'
                })
                logging.info(f"Converted {col} to numeric: {changed_count} records affected")
        
        elif expected_type == "date":
            # Convert to datetime
            date_format = config.get("rules", {}).get("date_columns", {}).get(col, {}).get("format", None)
            try:
                if date_format:
                    cleansed_df[col] = pd.to_datetime(cleansed_df[col], format=date_format, errors='coerce')
                else:
                    cleansed_df[col] = pd.to_datetime(cleansed_df[col], errors='coerce')
                changed_count = pd.isna(cleansed_df[col]).sum() - pd.isna(original_values).sum()
                if changed_count > 0:
                    cleansing_log.append({
                        'column': col,
                        'operation': 'convert_to_date',
                        'records_affected': changed_count,
                        'description': f'Converted to date type (format: {date_format}), invalid dates set to NaT'
                    })
                    logging.info(f"Converted {col} to date: {changed_count} invalid dates found")
            except Exception as e:
                logging.warning(f"Could not convert {col} to date: {e}")
    
    # 4. Fix negative values in columns where they're not allowed
    negative_not_allowed = config.get("rules", {}).get("negative_not_allowed_columns", [])
    for col in negative_not_allowed:
        if col in cleansed_df.columns and pd.api.types.is_numeric_dtype(cleansed_df[col]):
            negative_mask = cleansed_df[col] < 0
            negative_count = negative_mask.sum()
            if negative_count > 0:
                # Replace negative values with absolute value
                cleansed_df.loc[negative_mask, col] = cleansed_df.loc[negative_mask, col].abs()
                cleansing_log.append({
                    'column': col,
                    'operation': 'fix_negative_values',
                    'records_affected': negative_count,
                    'description': 'Converted negative values to absolute values'
                })
                logging.info(f"Fixed negative values in {col}: {negative_count} records")
    
    # 5. Standardize allowed values (case normalization)
    allowed_values_rules = config.get("rules", {}).get("allowed_values", {})
    for col, allowed_vals in allowed_values_rules.items():
        if col not in cleansed_df.columns:
            continue
        
        original_values = cleansed_df[col].copy()
        # Create a mapping of lowercase to proper case
        value_map = {str(v).lower(): v for v in allowed_vals}
        
        # Apply case-insensitive mapping
        cleansed_df[col] = cleansed_df[col].astype(str).str.upper()
        
        # Replace values not in allowed list with NaN
        mask = ~cleansed_df[col].isin(allowed_vals)
        invalid_count = mask.sum()
        if invalid_count > 0:
            cleansed_df.loc[mask, col] = np.nan
            cleansing_log.append({
                'column': col,
                'operation': 'enforce_allowed_values',
                'records_affected': invalid_count,
                'description': f'Set invalid values to NaN (allowed: {allowed_vals})'
            })
            logging.info(f"Enforced allowed values in {col}: {invalid_count} invalid values set to NaN")
    
    # 6. Apply range constraints
    range_rules = config.get("rules", {}).get("range_rules", {})
    for col, range_spec in range_rules.items():
        if col not in cleansed_df.columns or not pd.api.types.is_numeric_dtype(cleansed_df[col]):
            continue
        
        min_val = range_spec.get("min")
        max_val = range_spec.get("max")
        
        out_of_range_mask = pd.Series([False] * len(cleansed_df), index=cleansed_df.index)
        
        if min_val is not None:
            out_of_range_mask |= cleansed_df[col] < min_val
        if max_val is not None:
            out_of_range_mask |= cleansed_df[col] > max_val
        
        out_of_range_count = out_of_range_mask.sum()
        if out_of_range_count > 0:
            # Clip values to range
            if min_val is not None and max_val is not None:
                cleansed_df[col] = cleansed_df[col].clip(lower=min_val, upper=max_val)
                cleansing_log.append({
                    'column': col,
                    'operation': 'apply_range_constraints',
                    'records_affected': out_of_range_count,
                    'description': f'Clipped values to range [{min_val}, {max_val}]'
                })
                logging.info(f"Applied range constraints to {col}: {out_of_range_count} records clipped")
    
    # 7. Remove duplicate records (keep first occurrence)
    duplicate_mask = cleansed_df.duplicated(keep='first')
    duplicate_count = duplicate_mask.sum()
    if duplicate_count > 0:
        cleansed_df = cleansed_df[~duplicate_mask].reset_index(drop=True)
        cleansing_log.append({
            'column': 'ALL',
            'operation': 'remove_duplicates',
            'records_affected': duplicate_count,
            'description': 'Removed duplicate records (kept first occurrence)'
        })
        logging.info(f"Removed {duplicate_count} duplicate records")
    
    # 8. Handle duplicate primary keys (keep first, mark others)
    primary_keys = config.get("keys", {}).get("primary_keys", [])
    if primary_keys and all(pk in cleansed_df.columns for pk in primary_keys):
        pk_duplicate_mask = cleansed_df.duplicated(subset=primary_keys, keep='first')
        pk_duplicate_count = pk_duplicate_mask.sum()
        if pk_duplicate_count > 0:
            cleansed_df = cleansed_df[~pk_duplicate_mask].reset_index(drop=True)
            cleansing_log.append({
                'column': ', '.join(primary_keys),
                'operation': 'remove_duplicate_primary_keys',
                'records_affected': pk_duplicate_count,
                'description': f'Removed records with duplicate primary keys (kept first occurrence)'
            })
            logging.info(f"Removed {pk_duplicate_count} records with duplicate primary keys")
    
    # Create cleansing log DataFrame
    cleansing_log_df = pd.DataFrame(cleansing_log)
    
    total_operations = len(cleansing_log)
    total_records_affected = cleansing_log_df['records_affected'].sum() if not cleansing_log_df.empty else 0
    
    logging.info(f"Data cleansing completed: {total_operations} operations, {total_records_affected} total records affected")
    logging.info(f"Original records: {len(df)}, Cleansed records: {len(cleansed_df)}")
    
    return cleansed_df, cleansing_log_df

def run_all_checks(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    all_issue_frames: Dict[str, pd.DataFrame] = {}
    anomaly_summary_rows: List[Dict[str, Any]] = []

    null_blank_df, null_blank_summary = detect_null_and_blank_values(df)
    all_issue_frames["null_blank"] = null_blank_df
    anomaly_summary_rows.extend(null_blank_summary)

    duplicates_df, duplicates_summary = detect_duplicate_records(df)
    all_issue_frames["duplicates"] = duplicates_df
    anomaly_summary_rows.append(duplicates_summary)

    primary_keys = config.get("keys", {}).get("primary_keys", [])
    duplicate_pk_df, duplicate_pk_summary = detect_duplicate_primary_keys(df, primary_keys)
    all_issue_frames["duplicate_primary_keys"] = duplicate_pk_df
    anomaly_summary_rows.append(duplicate_pk_summary)

    outliers_df, outliers_summary = detect_outliers(df, config)
    all_issue_frames["outliers"] = outliers_df
    anomaly_summary_rows.extend(outliers_summary)

    mixed_types_df, mixed_types_summary = detect_mixed_datatypes(df, config)
    all_issue_frames["mixed_types"] = mixed_types_df
    anomaly_summary_rows.extend(mixed_types_summary)

    invalid_dates_df, invalid_dates_summary = detect_invalid_dates(df, config)
    all_issue_frames["invalid_dates"] = invalid_dates_df
    anomaly_summary_rows.extend(invalid_dates_summary)

    invalid_emails_df, invalid_emails_summary = detect_invalid_emails(df, config)
    all_issue_frames["invalid_emails"] = invalid_emails_df
    anomaly_summary_rows.extend(invalid_emails_summary)

    negative_values_df, negative_values_summary = detect_negative_values(df, config)
    all_issue_frames["negative_values"] = negative_values_df
    anomaly_summary_rows.extend(negative_values_summary)

    special_chars_df, special_chars_summary = detect_special_characters(df, config)
    all_issue_frames["special_characters"] = special_chars_df
    anomaly_summary_rows.extend(special_chars_summary)

    missing_columns_df, missing_columns_summary = validate_mandatory_columns(df, config)
    all_issue_frames["missing_mandatory_columns"] = missing_columns_df
    anomaly_summary_rows.append(missing_columns_summary)

    mandatory_fields_df, mandatory_fields_summary = validate_mandatory_fields(df, config)
    all_issue_frames["mandatory_field_violations"] = mandatory_fields_df
    anomaly_summary_rows.extend(mandatory_fields_summary)

    datatype_df, datatype_summary = validate_datatype_rules(df, config)
    all_issue_frames["datatype_violations"] = datatype_df
    anomaly_summary_rows.extend(datatype_summary)

    range_df, range_summary = validate_range_rules(df, config)
    all_issue_frames["range_violations"] = range_df
    anomaly_summary_rows.extend(range_summary)

    pattern_df, pattern_summary = validate_pattern_rules(df, config)
    all_issue_frames["pattern_violations"] = pattern_df
    anomaly_summary_rows.extend(pattern_summary)

    allowed_values_df, allowed_values_summary = validate_allowed_values(df, config)
    all_issue_frames["allowed_value_violations"] = allowed_values_df
    anomaly_summary_rows.extend(allowed_values_summary)

    referential_df, referential_summary = validate_referential_integrity(df, config)
    all_issue_frames["referential_integrity"] = referential_df
    anomaly_summary_rows.append(referential_summary)

    business_rule_df, business_rule_summary = validate_business_rules(df, config)
    all_issue_frames["business_rule_violations"] = business_rule_df
    anomaly_summary_rows.extend(business_rule_summary)

    anomaly_summary_df = pd.DataFrame(anomaly_summary_rows)
    if "count" not in anomaly_summary_df.columns:
        anomaly_summary_df["count"] = 0
    count_series = pd.Series(pd.to_numeric(anomaly_summary_df["count"], errors="coerce"), index=anomaly_summary_df.index)
    anomaly_summary_df["count"] = count_series.fillna(0).astype(int)

    combined_issues_df = pd.concat(
        [issue_df for issue_df in all_issue_frames.values() if issue_df is not None and not issue_df.empty],
        ignore_index=True,
    ) if any(not df_part.empty for df_part in all_issue_frames.values()) else pd.DataFrame()

    # Identify good records (records without any issues)
    good_records_df = df.copy()
    if not combined_issues_df.empty:
        # Get unique indices of bad records
        bad_indices = combined_issues_df.index.unique() if 'index' not in combined_issues_df.columns else combined_issues_df['index'].unique()
        # Filter out bad records to get good records
        good_records_df = df[~df.index.isin(bad_indices)]
        logging.info(f"Good records: {len(good_records_df)}, Bad records: {len(bad_indices)}")
    else:
        logging.info(f"All {len(good_records_df)} records are clean (no issues found)")

    return {
        "issue_frames": all_issue_frames,
        "anomaly_summary_df": anomaly_summary_df,
        "combined_issues_df": combined_issues_df,
        "good_records_df": good_records_df,
    }


def save_outputs(
    output_dir: Path,
    summary_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    numeric_stats_df: pd.DataFrame,
    anomaly_summary_df: pd.DataFrame,
    score_df: pd.DataFrame,
    column_metrics_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
    issue_frames: Dict[str, pd.DataFrame],
    combined_issues_df: pd.DataFrame,
    good_records_df: pd.DataFrame,
    cleansing_log_df: Optional[pd.DataFrame],
    config: Dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Always export summary and analysis files
    export_dataframe(summary_df, output_dir / "dq_summary.csv")
    export_dataframe(profile_df, output_dir / "dq_profile.csv")
    export_dataframe(numeric_stats_df, output_dir / "dq_numeric_stats.csv")
    export_dataframe(anomaly_summary_df, output_dir / "dq_anomaly_summary.csv")
    export_dataframe(score_df, output_dir / "dq_score_breakdown.csv")
    export_dataframe(column_metrics_df, output_dir / "dq_column_metrics.csv")
    export_dataframe(recommendations_df, output_dir / "dq_recommendations.csv")
    
    # Export good records (clean data without any issues)
    good_prefix = config["general"].get("good_records_prefix", "good_records")
    export_dataframe(good_records_df, output_dir / f"{good_prefix}.csv", skip_if_empty=True)
    if not good_records_df.empty:
        logging.info(f"Good records file created: {len(good_records_df)} clean records")
    
    # Only export combined bad records if there are issues
    export_dataframe(combined_issues_df, output_dir / "dq_all_bad_records.csv", skip_if_empty=True)

    # Only export individual bad record files if they contain data
    bad_prefix = config["general"].get("bad_records_prefix", "bad_records")
    files_created = 0
    files_skipped = 0
    for category, issue_df in issue_frames.items():
        if issue_df is not None and not issue_df.empty:
            export_dataframe(issue_df, output_dir / f"{bad_prefix}_{category}.csv", skip_if_empty=False)
            files_created += 1
        else:
            files_skipped += 1
            logging.info(f"Skipping empty bad records file for category: {category}")
    
    logging.info(f"Bad record files: {files_created} created, {files_skipped} skipped (no issues found)")

    # Export cleansing log if available
    if cleansing_log_df is not None and not cleansing_log_df.empty:
        export_dataframe(cleansing_log_df, output_dir / "dq_cleansing_log.csv")
        logging.info(f"Cleansing log saved: {len(cleansing_log_df)} operations logged")
    
    if config["general"].get("excel_output", True):
        export_excel_report(
            output_dir / "dq_report.xlsx",
            summary_df,
            profile_df,
            numeric_stats_df,
            anomaly_summary_df,
            score_df,
            column_metrics_df,
            recommendations_df,
        )


def print_console_summary(
    input_file: str,
    total_rows: int,
    total_columns: int,
    quality_score: float,
    anomaly_summary_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Print summary to console."""
    print("\n=== DATA QUALITY ANALYSIS SUMMARY ===")
    print(f"Input file          : {input_file}")
    print(f"Output directory    : {output_dir}")
    print(f"Total rows          : {total_rows}")
    print(f"Total columns       : {total_columns}")
    print(f"Data quality score  : {quality_score:.2f}")
    print("\nAnomaly counts by category:")
    
    if not anomaly_summary_df.empty:
        category_counts = anomaly_summary_df.groupby('category')['count'].sum()
        for category, count in category_counts.items():
            print(f" - {category}: {count}")


def generate_executive_summary(
    output_dir: Path,
    original_df: pd.DataFrame,
    cleansed_df: Optional[pd.DataFrame],
    anomaly_summary_df: pd.DataFrame,
    quality_score: float,
    cleansing_log_df: Optional[pd.DataFrame],
    good_records_count: int,
    bad_records_count: int,
) -> pd.DataFrame:
    """
    Generate comprehensive executive summary report with all key metrics.
    
    Returns:
        DataFrame containing the executive summary
    
    Args:
        output_dir: Output directory
        original_df: Original dataset
        cleansed_df: Cleansed dataset (if cleansing was performed)
        anomaly_summary_df: Anomaly summary
        quality_score: Overall quality score
        cleansing_log_df: Cleansing operations log
        good_records_count: Number of clean records
        bad_records_count: Number of bad records
    """
    summary_data = []
    
    # === PROCESSING METRICS ===
    total_records_processed = len(original_df)
    total_columns = len(original_df.columns)
    
    summary_data.append({
        'Category': 'PROCESSING METRICS',
        'Metric': 'Total Records Processed',
        'Value': total_records_processed,
        'Percentage': '100.00%',
        'Status': 'INFO'
    })
    
    summary_data.append({
        'Category': 'PROCESSING METRICS',
        'Metric': 'Total Columns',
        'Value': total_columns,
        'Percentage': '-',
        'Status': 'INFO'
    })
    
    # === DATA QUALITY METRICS ===
    bad_data_percentage = (bad_records_count / total_records_processed * 100) if total_records_processed > 0 else 0
    clean_data_percentage = (good_records_count / total_records_processed * 100) if total_records_processed > 0 else 0
    
    summary_data.append({
        'Category': 'DATA QUALITY',
        'Metric': 'Total Bad Data Detected',
        'Value': bad_records_count,
        'Percentage': f'{bad_data_percentage:.2f}%',
        'Status': 'CRITICAL' if bad_data_percentage > 20 else 'WARNING' if bad_data_percentage > 10 else 'OK'
    })
    
    summary_data.append({
        'Category': 'DATA QUALITY',
        'Metric': 'Bad Data Percentage',
        'Value': f'{bad_data_percentage:.2f}%',
        'Percentage': '-',
        'Status': 'CRITICAL' if bad_data_percentage > 20 else 'WARNING' if bad_data_percentage > 10 else 'OK'
    })
    
    summary_data.append({
        'Category': 'DATA QUALITY',
        'Metric': 'Total Clean Records',
        'Value': good_records_count,
        'Percentage': f'{clean_data_percentage:.2f}%',
        'Status': 'GOOD' if clean_data_percentage > 80 else 'WARNING' if clean_data_percentage > 60 else 'CRITICAL'
    })
    
    summary_data.append({
        'Category': 'DATA QUALITY',
        'Metric': 'Data Quality Score',
        'Value': f'{quality_score:.2f}',
        'Percentage': f'{quality_score:.2f}%',
        'Status': 'EXCELLENT' if quality_score >= 90 else 'GOOD' if quality_score >= 75 else 'WARNING' if quality_score >= 60 else 'CRITICAL'
    })
    
    # === ANOMALY ANALYSIS ===
    if not anomaly_summary_df.empty:
        # Group by category and sum counts
        category_summary = anomaly_summary_df.groupby('category')['count'].sum().to_dict()
        
        for category, count in sorted(category_summary.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                category_percentage = (count / total_records_processed * 100) if total_records_processed > 0 else 0
                summary_data.append({
                    'Category': 'ANOMALY ANALYSIS',
                    'Metric': category.replace('_', ' ').title(),
                    'Value': count,
                    'Percentage': f'{category_percentage:.2f}%',
                    'Status': 'HIGH' if count > total_records_processed * 0.1 else 'MEDIUM' if count > total_records_processed * 0.05 else 'LOW'
                })
    
    # === CLEANSING METRICS ===
    if cleansed_df is not None and cleansing_log_df is not None and not cleansing_log_df.empty:
        records_before = len(original_df)
        records_after = len(cleansed_df)
        records_removed = records_before - records_after
        
        total_operations = len(cleansing_log_df)
        total_records_affected = cleansing_log_df['records_affected'].sum()
        
        # Calculate cleansing success rate
        # Success = records that were fixed and are now clean
        cleansing_success_rate = (good_records_count / bad_records_count * 100) if bad_records_count > 0 else 100
        
        summary_data.append({
            'Category': 'CLEANSING METRICS',
            'Metric': 'Cleansing Operations Performed',
            'Value': total_operations,
            'Percentage': '-',
            'Status': 'INFO'
        })
        
        summary_data.append({
            'Category': 'CLEANSING METRICS',
            'Metric': 'Total Records Affected by Cleansing',
            'Value': total_records_affected,
            'Percentage': f'{(total_records_affected/records_before*100):.2f}%',
            'Status': 'INFO'
        })
        
        summary_data.append({
            'Category': 'CLEANSING METRICS',
            'Metric': 'Records Removed (Duplicates)',
            'Value': records_removed,
            'Percentage': f'{(records_removed/records_before*100):.2f}%',
            'Status': 'INFO'
        })
        
        summary_data.append({
            'Category': 'CLEANSING METRICS',
            'Metric': 'Cleansing Success Rate',
            'Value': f'{cleansing_success_rate:.2f}%',
            'Percentage': '-',
            'Status': 'EXCELLENT' if cleansing_success_rate >= 80 else 'GOOD' if cleansing_success_rate >= 60 else 'WARNING'
        })
        
        summary_data.append({
            'Category': 'CLEANSING METRICS',
            'Metric': 'Records After Cleansing',
            'Value': records_after,
            'Percentage': f'{(records_after/records_before*100):.2f}%',
            'Status': 'INFO'
        })
    else:
        summary_data.append({
            'Category': 'CLEANSING METRICS',
            'Metric': 'Cleansing Status',
            'Value': 'Not Performed',
            'Percentage': '-',
            'Status': 'INFO'
        })
    
    # Create DataFrame and save
    summary_df = pd.DataFrame(summary_data)
    export_dataframe(summary_df, output_dir / "dq_executive_summary.csv")
    
    # Generate formatted text report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("DATA QUALITY EXECUTIVE SUMMARY REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    current_category = None
    for _, row in summary_df.iterrows():
        if row['Category'] != current_category:
            current_category = row['Category']
            report_lines.append("")
            report_lines.append("-" * 80)
            report_lines.append(f"{current_category}")
            report_lines.append("-" * 80)
        
        status_symbol = {
            'EXCELLENT': '[++]',
            'GOOD': '[+]',
            'OK': '[o]',
            'INFO': '[i]',
            'WARNING': '[!]',
            'CRITICAL': '[X]',
            'HIGH': '[H]',
            'MEDIUM': '[M]',
            'LOW': '[L]'
        }.get(row['Status'], '[*]')
        
        metric_line = f"  {status_symbol} {row['Metric']:<45} : {str(row['Value']):>12}"
        if row['Percentage'] != '-':
            metric_line += f"  ({row['Percentage']})"
        report_lines.append(metric_line)
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Save text report
    report_text = "\n".join(report_lines)
    with open(output_dir / "dq_executive_summary.txt", 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # Print to console
    print("\n" + report_text)
    
    logging.info("Executive summary report generated")
    
    return summary_df

def generate_executive_dashboard(
    output_dir: Path,
    executive_summary_df: pd.DataFrame,
    quality_score: float,
    anomaly_summary_df: pd.DataFrame,
    cleansing_log_df: Optional[pd.DataFrame],
    total_rows: int,
    good_records_count: int,
    bad_records_count: int,
    quality_score_before: Optional[float] = None,
    quality_score_after: Optional[float] = None,
    quality_improvement_pct: Optional[float] = None,
) -> None:
    """
    Generate comprehensive executive dashboard with all key metrics.
    Includes before/after cleansing comparison if cleansing was performed.
    """
    if not PLOTLY_AVAILABLE:
        logging.warning("Plotly not available. Install plotly for dashboard: pip install plotly")
        return
    
    logging.info("Generating executive dashboard...")
    
    # Create HTML dashboard
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Quality Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        .metric-card.critical {{
            border-left-color: #e74c3c;
        }}
        .metric-card.warning {{
            border-left-color: #f39c12;
        }}
        .metric-card.good {{
            border-left-color: #27ae60;
        }}
        .metric-card.excellent {{
            border-left-color: #2ecc71;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .metric-subtitle {{
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .status-excellent {{ background: #d4edda; color: #155724; }}
        .status-good {{ background: #d1ecf1; color: #0c5460; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .status-critical {{ background: #f8d7da; color: #721c24; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Data Quality Analysis Report</h1>
        <p>Comprehensive Data Quality Analysis & Recommendations</p>
        <p style="font-size: 14px; margin-top: 10px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
    
    # Add Key Metrics Cards
    bad_data_pct = (bad_records_count / total_rows * 100) if total_rows > 0 else 0
    clean_data_pct = (good_records_count / total_rows * 100) if total_rows > 0 else 0
    
    quality_status = "excellent" if quality_score >= 90 else "good" if quality_score >= 75 else "warning" if quality_score >= 60 else "critical"
    bad_data_status = "critical" if bad_data_pct > 20 else "warning" if bad_data_pct > 10 else "good"
    
    html_content += f"""
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Records Processed</div>
            <div class="metric-value">{total_rows:,}</div>
            <div class="metric-subtitle">Input dataset size</div>
        </div>
        
        <div class="metric-card {quality_status}">
            <div class="metric-label">Data Quality Score</div>
            <div class="metric-value">{quality_score:.1f}%</div>
            <span class="status-badge status-{quality_status}">{quality_status.upper()}</span>
        </div>
        
        <div class="metric-card {bad_data_status}">
            <div class="metric-label">Bad Data Detected</div>
            <div class="metric-value">{bad_records_count:,}</div>
            <div class="metric-subtitle">{bad_data_pct:.1f}% of total records</div>
        </div>
        
        <div class="metric-card good">
            <div class="metric-label">Clean Records</div>
            <div class="metric-value">{good_records_count:,}</div>
            <div class="metric-subtitle">{clean_data_pct:.1f}% of total records</div>
        </div>
    </div>
"""
    
    # Add Cleansing Status Section (if cleansing was performed)
    if cleansing_log_df is not None and not cleansing_log_df.empty:
        total_operations = len(cleansing_log_df)
        total_records_affected = cleansing_log_df['records_affected'].sum()
        
        html_content += f"""
    <div class="chart-container">
        <div class="chart-title">🔧 Data Cleansing Status</div>
        <div style="padding: 15px;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50;">
                    <div style="font-size: 14px; color: #666;">Cleansing Operations</div>
                    <div style="font-size: 28px; font-weight: bold; color: #2e7d32;">{total_operations}</div>
                </div>
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;">
                    <div style="font-size: 14px; color: #666;">Records Affected</div>
                    <div style="font-size: 28px; font-weight: bold; color: #1565c0;">{total_records_affected:,}</div>
                </div>
                <div style="background: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;">
                    <div style="font-size: 14px; color: #666;">Quality Improvement</div>
                    <div style="font-size: 28px; font-weight: bold; color: #e65100;">{quality_improvement_pct:.2f}%</div>
                </div>
            </div>
            <table style="width: 100%; margin-top: 10px;">
                <thead>
                    <tr>
                        <th>Column</th>
                        <th>Operation</th>
                        <th>Records Affected</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for _, row in cleansing_log_df.iterrows():
            html_content += f"""
                    <tr>
                        <td><strong>{row['column']}</strong></td>
                        <td>{row['operation'].replace('_', ' ').title()}</td>
                        <td>{row['records_affected']:,}</td>
                        <td>{row['description']}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
    </div>
"""
    else:
        # Show "No Cleansing Performed" message
        html_content += """
    <div class="chart-container">
        <div class="chart-title">🔧 Data Cleansing Status</div>
        <div style="padding: 20px; text-align: center; color: #666;">
            <p style="font-size: 16px; margin: 0;">No data cleansing was performed.</p>
            <p style="font-size: 14px; margin-top: 10px;">Run with <code>--cleanse-data</code> flag to enable automatic data cleansing.</p>
        </div>
    </div>
"""
    
    # Create chart containers
    html_content += """
    <div class="chart-container">
        <div class="chart-title">📈 Quality Score Gauge</div>
        <div id="gauge-chart"></div>
    </div>
    
    <div class="chart-container">
        <div class="chart-title">📊 Issues by Category</div>
        <div id="category-chart"></div>
    </div>
    
    <div class="chart-container">
        <div class="chart-title">📋 Detailed Metrics Table</div>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Percentage</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add executive summary table rows
    
    for _, row in executive_summary_df.iterrows():
        status_class = f"status-{row['Status'].lower()}" if row['Status'].lower() in ['excellent', 'good', 'warning', 'critical'] else ""
        html_content += f"""
        <tr>
            <td><strong>{row['Category']}</strong></td>
            <td>{row['Metric']}</td>
            <td>{row['Value']}</td>
            <td>{row['Percentage']}</td>
            <td><span class="status-badge {status_class}">{row['Status']}</span></td>
        </tr>
"""
    
    html_content += """
            </tbody>
        </table>
    </div>
"""
    
    # Add JavaScript for Plotly charts
    html_content += """
    <script>
        // Quality Score Gauge
        var gaugeData = [{
            type: "indicator",
            mode: "gauge+number+delta",
            value: """ + str(quality_score) + """,
            title: { text: "Quality Score", font: { size: 24 } },
            delta: { reference: 90, increasing: { color: "green" } },
            gauge: {
                axis: { range: [null, 100], tickwidth: 1, tickcolor: "darkblue" },
                bar: { color: "darkblue" },
                bgcolor: "white",
                borderwidth: 2,
                bordercolor: "gray",
                steps: [
                    { range: [0, 60], color: "#ffcccc" },
                    { range: [60, 80], color: "#ffffcc" },
                    { range: [80, 90], color: "#ccffcc" },
                    { range: [90, 100], color: "#99ff99" }
                ],
                threshold: {
                    line: { color: "red", width: 4 },
                    thickness: 0.75,
                    value: 90
                }
            }
        }];
        
        var gaugeLayout = {
            width: 500,
            height: 400,
            margin: { t: 25, r: 25, l: 25, b: 25 },
            paper_bgcolor: "white",
            font: { color: "darkblue", family: "Arial" }
        };
        
        Plotly.newPlot('gauge-chart', gaugeData, gaugeLayout);
"""
    
    # Add category chart data
    if not anomaly_summary_df.empty:
        category_data = anomaly_summary_df.groupby('category')['count'].sum().sort_values(ascending=False)
        categories = category_data.index.tolist()
        counts = category_data.values.tolist()
        
        html_content += f"""
        // Issues by Category
        var categoryData = [{{
            x: {counts},
            y: {[cat.replace('_', ' ').title() for cat in categories]},
            type: 'bar',
            orientation: 'h',
            marker: {{
                color: {counts},
                colorscale: 'Reds',
                showscale: true
            }},
            text: {counts},
            textposition: 'auto',
        }}];
        
        var categoryLayout = {{
            title: 'Issue Distribution',
            xaxis: {{ title: 'Number of Issues' }},
            yaxis: {{ title: 'Category' }},
            height: 500,
            margin: {{ l: 200 }}
        }};
        
        Plotly.newPlot('category-chart', categoryData, categoryLayout);
"""
    
    html_content += """
    </script>
</body>
</html>
"""
    
    # Save dashboard
    dashboard_path = output_dir / "dq_executive_dashboard.html"
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logging.info(f"Executive dashboard saved to: {dashboard_path}")


# ============================================================================
# DAT FILE TRANSFORMATION BASED ON DML
# ============================================================================

def transform_dat_by_dml(dat_path: str, dml_path: str, output_path: str) -> Dict[str, Any]:
    """
    Transform DAT file according to DML specification
    Returns transformation result dictionary
    """
    from datetime import datetime
    
    # Parse DML to get field specifications
    dml_data = parse_dml_file(dml_path)
    field_specs = dml_data['fields']
    
    logging.info(f"Parsing DML file: {dml_path}")
    logging.info(f"Found {len(field_specs)} field specifications")
    
    # Read DAT file
    logging.info(f"Reading DAT file: {dat_path}")
    with open(dat_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        raise ValueError("DAT file is empty")
    
    # Detect current delimiter
    header = lines[0].strip()
    current_delimiter = None
    for delim in ['|', ',', '\t', ';']:
        if delim in header:
            current_delimiter = delim
            logging.info(f"Detected current delimiter: '{delim}'")
            break
    
    if not current_delimiter:
        raise ValueError("Could not detect delimiter in DAT file")
    
    # Parse header
    header_fields = [f.strip() for f in header.split(current_delimiter)]
    
    # Verify field count matches
    if len(header_fields) != len(field_specs):
        logging.warning(f"Field count mismatch - DAT has {len(header_fields)} fields, DML has {len(field_specs)} fields")
    
    logging.info(f"Transforming data according to DML specification...")
    
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
    conversion_warnings = []
    for line_num, line in enumerate(lines[1:], 2):
        line = line.strip()
        if not line:
            continue
        
        # Split by current delimiter
        values = [v.strip() for v in line.split(current_delimiter)]
        
        # Convert each value according to DML spec
        transformed_line = ""
        for i, (value, spec) in enumerate(zip(values, field_specs)):
            try:
                converted_value = convert_value_by_type(value, spec)
                transformed_line += converted_value
            except Exception as e:
                conversion_warnings.append(f"Line {line_num}, Field {spec['name']}: {str(e)}")
                transformed_line += value  # Keep original on error
            
            if i < len(field_specs) - 1:
                transformed_line += spec['delimiter']
        
        transformed_lines.append(transformed_line)
    
    # Write output file
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        for line in transformed_lines:
            f.write(line + '\n')
    
    result = {
        'success': True,
        'input_file': dat_path,
        'dml_file': dml_path,
        'output_file': output_path,
        'input_records': len(lines) - 1,
        'output_records': len(transformed_lines) - 1,
        'field_count': len(field_specs),
        'conversion_warnings': conversion_warnings,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    logging.info(f"Transformation complete: {len(transformed_lines) - 1} records transformed")
    if conversion_warnings:
        logging.warning(f"{len(conversion_warnings)} conversion warnings occurred")
    
    return result


def convert_value_by_type(value: str, field_spec: Dict[str, str]) -> str:
    """Convert value according to field specification"""
    field_type = field_spec['type']
    field_format = field_spec.get('format')
    
    if field_type == 'string':
        # Keep as string, optionally truncate to size
        if field_format and field_format.isdigit():
            max_len = int(field_format)
            return value[:max_len]
        return value
    
    elif field_type == 'decimal':
        # Convert to decimal/numeric
        cleaned = re.sub(r'[^\d.-]', '', value)
        if cleaned:
            return str(float(cleaned))
        return '0'
    
    elif field_type == 'date':
        # Convert date format
        if field_format:
            # Try to parse existing date and convert to target format
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    from datetime import datetime
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


def main() -> int:
    """Main entry point for data quality analysis"""
    args = parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config_file, args.output_dir, args.reference_file)
        
        # Enable database mode if requested
        if args.use_database:
            config["database"]["enabled"] = True
        
        # Setup output directory
        output_dir = Path(config["general"]["output_dir"])
        setup_logging(output_dir, config["general"]["log_file"])
        
        logging.info("Starting ENHANCED data quality analysis")
        logging.info("Features: DB connectivity, Multi-format support, Dashboard, Aggregation, Newline fixing")
        
        # Handle DAT transformation if requested
        if args.transform_dat:
            if not args.dml_file:
                logging.error("--transform-dat requires --dml-file to be specified")
                print("ERROR: --transform-dat requires --dml-file", file=sys.stderr)
                return 1
            
            if not args.input_file:
                logging.error("--transform-dat requires --input-file to be specified")
                print("ERROR: --transform-dat requires --input-file", file=sys.stderr)
                return 1
            
            # Determine output path
            transform_output = args.transform_output
            if not transform_output:
                input_path = Path(args.input_file)
                transform_output = str(input_path.parent / f"{input_path.stem}_transformed{input_path.suffix}")
            
            logging.info(f"Transforming DAT file according to DML specification...")
            transform_result = transform_dat_by_dml(args.input_file, args.dml_file, transform_output)
            
            if transform_result['success']:
                print("\n[SUCCESS] DAT FILE TRANSFORMATION COMPLETE!")
                print("=" * 80)
                print(f"Input file: {transform_result['input_file']}")
                print(f"DML file: {transform_result['dml_file']}")
                print(f"Output file: {transform_result['output_file']}")
                print(f"\nRecords transformed: {transform_result['output_records']}")
                print(f"Fields: {transform_result['field_count']}")
                
                if transform_result['conversion_warnings']:
                    print(f"\nConversion warnings: {len(transform_result['conversion_warnings'])}")
                    for warning in transform_result['conversion_warnings'][:10]:  # Show first 10
                        print(f"  - {warning}")
                    if len(transform_result['conversion_warnings']) > 10:
                        print(f"  ... and {len(transform_result['conversion_warnings']) - 10} more")
                
                print("=" * 80)
                
                # Save transformation report
                transform_report = pd.DataFrame([transform_result])
                transform_report_path = output_dir / "dat_transformation_report.csv"
                export_dataframe(transform_report, transform_report_path)
                logging.info(f"Transformation report saved to: {transform_report_path}")
                
                print(f"\n[TIP] Use the transformed file for analysis: {transform_output}")
                logging.info("DAT transformation completed successfully")
                return 0
            else:
                logging.error("DAT transformation failed")
                return 1
        
        # Check for mixed newline characters if requested
        if args.check_newlines and args.input_file:
            logging.info("Checking for mixed newline characters...")
            newline_issues_df, newline_summary = detect_mixed_newline_characters(args.input_file)
            
            if newline_summary['count'] > 0:
                print("\n[WARNING] MIXED NEWLINE CHARACTERS DETECTED!")
                print("=" * 80)
                for _, row in newline_issues_df.iterrows():
                    print(f"File: {row['file']}")
                    print(f"Issue: {row['issue']}")
                    print(f"  - CRLF (\\r\\n): {row['crlf_count']}")
                    print(f"  - LF (\\n): {row['lf_count']}")
                    print(f"  - CR (\\r): {row['cr_count']}")
                    print(f"  - Total lines: {row['total_lines']}")
                    print(f"  - Predominant type: {row['predominant_type']}")
                    print(f"  - Recommendation: {row['recommendation']}")
                print("=" * 80)
                
                # Save newline issues report
                newline_report_path = output_dir / "newline_issues_report.csv"
                export_dataframe(newline_issues_df, newline_report_path)
                logging.info(f"Newline issues report saved to: {newline_report_path}")
                
                if args.fix_newlines:
                    print("\n[FIX] Fixing newline characters...")
                else:
                    print("\n[TIP] Use --fix-newlines to automatically fix these issues")
                    # If only checking newlines (not fixing), exit here
                    if not args.cleanse_data:
                        logging.info("Newline check completed. Exiting.")
                        return 0
            else:
                print("\n[OK] No mixed newline characters detected. File is clean!")
                # If only checking newlines and file is clean, exit here
                if not args.fix_newlines and not args.cleanse_data:
                    logging.info("Newline check completed. File is clean. Exiting.")
                    return 0
        
        # Fix newline characters if requested
        if args.fix_newlines and args.input_file:
            # Determine output file path
            if args.fixed_file_output:
                fixed_output = args.fixed_file_output
            else:
                input_path = Path(args.input_file)
                fixed_output = str(input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}")
            
            # Map target newline choice to actual character
            newline_map = {
                'LF': '\n',
                'CRLF': '\r\n',
                'CR': '\r'
            }
            target_nl = newline_map[args.target_newline]
            
            logging.info(f"Fixing newline characters to {args.target_newline}...")
            fix_result = fix_newline_characters(args.input_file, fixed_output, target_nl)
            
            if fix_result['success']:
                print("\n[SUCCESS] NEWLINE CHARACTERS FIXED SUCCESSFULLY!")
                print("=" * 80)
                print(f"Input file: {fix_result['input_file']}")
                print(f"Output file: {fix_result['output_file']}")
                print(f"Target format: {fix_result['target_newline']}")
                print(f"\nOriginal line endings:")
                print(f"  - CRLF (\\r\\n): {fix_result['original']['crlf']}")
                print(f"  - LF (\\n): {fix_result['original']['lf']}")
                print(f"  - CR (\\r): {fix_result['original']['cr']}")
                print(f"\nFixed line endings:")
                print(f"  - CRLF (\\r\\n): {fix_result['fixed']['crlf']}")
                print(f"  - LF (\\n): {fix_result['fixed']['lf']}")
                print(f"  - CR (\\r): {fix_result['fixed']['cr']}")
                print(f"\nTotal lines processed: {fix_result['lines_fixed']}")
                print("=" * 80)
                
                # Save fix report
                fix_report = pd.DataFrame([{
                    'input_file': fix_result['input_file'],
                    'output_file': fix_result['output_file'],
                    'target_format': fix_result['target_newline'],
                    'original_crlf': fix_result['original']['crlf'],
                    'original_lf': fix_result['original']['lf'],
                    'original_cr': fix_result['original']['cr'],
                    'fixed_crlf': fix_result['fixed']['crlf'],
                    'fixed_lf': fix_result['fixed']['lf'],
                    'fixed_cr': fix_result['fixed']['cr'],
                    'lines_processed': fix_result['lines_fixed'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }])
                fix_report_path = output_dir / "newline_fix_report.csv"
                export_dataframe(fix_report, fix_report_path)
                logging.info(f"Fix report saved to: {fix_report_path}")
                
                # Ask if user wants to use the fixed file for analysis
                print(f"\n[TIP] Use the fixed file for analysis: {fixed_output}")
                print("   You can now run the analysis on the fixed file!")
                
                # If only fixing newlines, exit here
                if not args.cleanse_data:
                    logging.info("Newline fixing completed. Exiting.")
                    return 0
            else:
                logging.error(f"Failed to fix newline characters: {fix_result.get('error', 'Unknown error')}")
                print(f"\n[ERROR] Error fixing newlines: {fix_result.get('error', 'Unknown error')}")
                return 1
        
        # Load data using enhanced loader
        if args.use_database:
            logging.info("Loading data from database...")
            df = load_input_data_enhanced(None, config)
        else:
            if not args.input_file:
                raise ValueError("Either --input-file or --use-database must be specified")
            
            # Check if this is an Ab Initio DAT file with DML
            input_path = Path(args.input_file)
            if input_path.suffix.lower() == '.dat' and args.dml_file:
                # If DML file is provided, use it for parsing
                logging.info("Loading Ab Initio DAT file with DML...")
                logging.info(f"  DAT file: {args.input_file}")
                logging.info(f"  DML file: {args.dml_file}")
                
                # Parse DML file
                dml_info = parse_dml_file(args.dml_file)
                
                # Load DAT file using DML specifications
                df = load_dat_file_with_dml(args.input_file, dml_info, auto_fix_newlines=True)
                
                logging.info("Ab Initio DAT file loaded successfully")
            else:
                # Load as regular delimited file (CSV-like)
                logging.info("Loading input file: %s", args.input_file)
                df = load_input_data_enhanced(args.input_file, config)
        
        total_rows, total_columns = df.shape
        logging.info("Loaded dataset with %s rows and %s columns", total_rows, total_columns)

        # Calculate quality score BEFORE cleansing (baseline)
        logging.info("Calculating baseline quality score on original data...")
        original_results = run_all_checks(df, config)
        original_anomaly_summary_df = original_results["anomaly_summary_df"]
        original_bad_records_count = len(original_results["combined_issues_df"]) if not original_results["combined_issues_df"].empty else 0
        quality_score_before, _ = compute_quality_score(original_anomaly_summary_df, config, total_rows, original_bad_records_count)
        logging.info(f"Baseline quality score: {quality_score_before:.2f}%")
        
        # Apply data cleansing if requested
        cleansing_log_df = None
        cleansed_df = df
        quality_score_after = None
        quality_improvement_pct = None
        
        if args.cleanse_data:
            logging.info("Applying data cleansing...")
            cleansed_df, cleansing_log_df = cleanse_data(df, config)
            logging.info(f"Data cleansing completed. Records: {len(df)} -> {len(cleansed_df)}")
            
            # Save cleansed data
            cleanse_output_path = args.cleanse_output if args.cleanse_output else output_dir / "cleansed_data.csv"
            export_dataframe(cleansed_df, Path(cleanse_output_path))
            logging.info(f"Cleansed data saved to: {cleanse_output_path}")
            
            # Calculate quality score AFTER cleansing
            logging.info("Calculating quality score on cleansed data...")
            cleansed_results = run_all_checks(cleansed_df, config)
            cleansed_anomaly_summary_df = cleansed_results["anomaly_summary_df"]
            cleansed_bad_records_count = len(cleansed_results["combined_issues_df"]) if not cleansed_results["combined_issues_df"].empty else 0
            quality_score_after, _ = compute_quality_score(cleansed_anomaly_summary_df, config, len(cleansed_df), cleansed_bad_records_count)
            
            # Calculate improvement
            quality_improvement_pct = quality_score_after - quality_score_before
            logging.info(f"Quality score after cleansing: {quality_score_after:.2f}%")
            logging.info(f"Quality improvement: {quality_improvement_pct:+.2f}%")
        
        # Run data profiling and quality checks on the appropriate dataset
        analysis_df = cleansed_df if args.cleanse_data else df
        summary_df, profile_df, numeric_stats_df = profile_data(analysis_df, config)
        results = run_all_checks(analysis_df, config)

        anomaly_summary_df = results["anomaly_summary_df"]
        combined_issues_df = results["combined_issues_df"]
        issue_frames = results["issue_frames"]
        good_records_df = results["good_records_df"]

        # Calculate quality metrics (use after-cleansing score if available, otherwise before)
        quality_score = quality_score_after if quality_score_after is not None else quality_score_before
        bad_records_count = len(combined_issues_df) if not combined_issues_df.empty else 0
        _, score_df = compute_quality_score(anomaly_summary_df, config, total_rows if not args.cleanse_data else len(cleansed_df), bad_records_count)
        column_metrics_df = build_column_quality_metrics(profile_df, anomaly_summary_df, total_rows if not args.cleanse_data else len(cleansed_df))
        recommendations_df = generate_recommendations(anomaly_summary_df)
        
        # Generate aggregated metrics
        aggregated_metrics_df = aggregate_quality_metrics(analysis_df, anomaly_summary_df, profile_df, config)

        trend_row = pd.DataFrame(
            [
                {
                    "metric": "quality_score",
                    "value": quality_score,
                },
                {
                    "metric": "total_anomaly_records",
                    "value": 0 if combined_issues_df.empty else combined_issues_df.shape[0],
                },
                {
                    "metric": "trend_summary",
                    "value": "Use persisted dq_summary.csv files from prior runs to compare trends over time.",
                },
            ]
        )
        summary_df = pd.concat([summary_df, trend_row], ignore_index=True)

        # Save all outputs
        save_outputs(
            output_dir=output_dir,
            summary_df=summary_df,
            profile_df=profile_df,
            numeric_stats_df=numeric_stats_df,
            anomaly_summary_df=anomaly_summary_df,
            score_df=score_df,
            column_metrics_df=column_metrics_df,
            recommendations_df=recommendations_df,
            issue_frames=issue_frames,
            combined_issues_df=combined_issues_df,
            good_records_df=good_records_df,
            cleansing_log_df=cleansing_log_df,
            config=config,
        )
        
        # Save aggregated metrics
        export_dataframe(aggregated_metrics_df, output_dir / "dq_aggregated_metrics.csv")
        logging.info("Aggregated metrics saved")
        
        # Generate dashboard if requested
        if args.generate_dashboard or config.get("general", {}).get("generate_dashboard", False):
            generate_quality_dashboard(
                output_dir=output_dir,
                quality_score=quality_score,
                anomaly_summary_df=anomaly_summary_df,
                profile_df=profile_df,
                column_metrics_df=column_metrics_df,
                total_rows=total_rows,
            )

        # Generate Executive Summary Report
        executive_summary_df = generate_executive_summary(
            output_dir=output_dir,
            original_df=df,
            cleansed_df=cleansed_df if args.cleanse_data else None,
            anomaly_summary_df=anomaly_summary_df,
            quality_score=quality_score,
            cleansing_log_df=cleansing_log_df,
            good_records_count=len(good_records_df),
            bad_records_count=len(combined_issues_df) if not combined_issues_df.empty else 0,
        )
        
        # Generate Executive Dashboard (always generate)
        generate_executive_dashboard(
            output_dir=output_dir,
            executive_summary_df=executive_summary_df,
            quality_score=quality_score,
            anomaly_summary_df=anomaly_summary_df,
            cleansing_log_df=cleansing_log_df,
            total_rows=total_rows,
            good_records_count=len(good_records_df),
            bad_records_count=len(combined_issues_df) if not combined_issues_df.empty else 0,
            quality_score_before=quality_score_before,
            quality_score_after=quality_score_after,
            quality_improvement_pct=quality_improvement_pct,
        )

        print_console_summary(
            input_file=args.input_file,
            total_rows=total_rows,
            total_columns=total_columns,
            quality_score=quality_score,
            anomaly_summary_df=anomaly_summary_df,
            output_dir=output_dir,
        )

        logging.info("Data quality analysis completed successfully")
        return 0

    except Exception as exc:
        logging.error("Data quality analysis failed: %s", exc)
        logging.error(traceback.format_exc())
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
