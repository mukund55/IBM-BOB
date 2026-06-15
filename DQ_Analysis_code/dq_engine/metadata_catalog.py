"""
Metadata Catalog Module
=======================

Manages data quality metadata and generates data dictionaries.

Features:
- Automatic metadata extraction
- Data dictionary generation
- Column metadata tracking
- Business metadata management
- Profiling summary catalog

Author: Bob
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class MetadataCatalog:
    """
    Metadata catalog engine that manages and tracks data quality metadata.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Metadata Catalog.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.catalog_dir = Path(self.config.get('catalog_dir', 'dq_metadata'))
        self.catalog_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_data_dictionary(self, df: pd.DataFrame,
                                 column_profiles: List[Dict[str, Any]],
                                 business_metadata: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Generate comprehensive data dictionary.
        
        Args:
            df: Input DataFrame
            column_profiles: List of column profile dictionaries
            business_metadata: Optional business metadata
            
        Returns:
            DataFrame containing data dictionary
        """
        self.logger.info("Generating data dictionary...")
        
        business_metadata = business_metadata or {}
        
        records = []
        for profile in column_profiles:
            column_name = profile['column_name']
            
            # Get business metadata for this column
            col_business_meta = business_metadata.get(column_name, {})
            
            record = {
                'Column Name': column_name,
                'Data Type': profile.get('data_type', ''),
                'Inferred Type': profile.get('inferred_type', ''),
                'Description': col_business_meta.get('description', ''),
                'Business Owner': col_business_meta.get('owner', ''),
                'Is Mandatory': col_business_meta.get('is_mandatory', False),
                'Is PII': col_business_meta.get('is_pii', False),
                'Record Count': profile.get('record_count', 0),
                'Null Count': profile.get('null_count', 0),
                'Null %': profile.get('null_percentage', 0),
                'Distinct Count': profile.get('distinct_count', 0),
                'Distinct %': profile.get('distinct_percentage', 0),
                'Completeness %': profile.get('completeness_percentage', 0),
                'Quality Score': profile.get('quality_score', 0),
                'Sample Values': ', '.join([str(v['value']) for v in profile.get('top_values', [])[:3]]),
                'Quality Issues': '; '.join(profile.get('quality_issues', []))
            }
            
            # Add numeric-specific fields
            if 'min_value' in profile:
                record['Min Value'] = profile['min_value']
                record['Max Value'] = profile['max_value']
                record['Mean'] = profile.get('mean', '')
                record['Median'] = profile.get('median', '')
            
            records.append(record)
        
        data_dict = pd.DataFrame(records)
        
        self.logger.info(f"Data dictionary generated for {len(records)} columns")
        
        return data_dict
    
    def generate_column_metadata(self, column_profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Generate detailed column metadata catalog.
        
        Args:
            column_profiles: List of column profile dictionaries
            
        Returns:
            Dictionary mapping column names to metadata
        """
        self.logger.info("Generating column metadata catalog...")
        
        metadata = {}
        
        for profile in column_profiles:
            column_name = profile['column_name']
            
            metadata[column_name] = {
                'technical_metadata': {
                    'data_type': profile.get('data_type', ''),
                    'inferred_type': profile.get('inferred_type', ''),
                    'nullable': profile.get('null_count', 0) > 0,
                    'unique': profile.get('is_unique', False),
                    'cardinality': profile.get('cardinality', '')
                },
                'quality_metadata': {
                    'completeness_percentage': profile.get('completeness_percentage', 0),
                    'quality_score': profile.get('quality_score', 0),
                    'quality_issues': profile.get('quality_issues', []),
                    'null_percentage': profile.get('null_percentage', 0),
                    'blank_percentage': profile.get('blank_percentage', 0),
                    'duplicate_percentage': profile.get('duplicate_percentage', 0)
                },
                'statistical_metadata': {
                    'record_count': profile.get('record_count', 0),
                    'distinct_count': profile.get('distinct_count', 0),
                    'min_value': profile.get('min_value'),
                    'max_value': profile.get('max_value'),
                    'mean': profile.get('mean'),
                    'median': profile.get('median'),
                    'std_dev': profile.get('std_dev')
                },
                'pattern_metadata': {
                    'patterns': profile.get('patterns', {}),
                    'top_values': profile.get('top_values', [])
                },
                'last_profiled': datetime.now().isoformat()
            }
        
        self.logger.info(f"Column metadata generated for {len(metadata)} columns")
        
        return metadata
    
    def generate_business_metadata_template(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate template for business metadata collection.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame template for business metadata
        """
        self.logger.info("Generating business metadata template...")
        
        records = []
        for column in df.columns:
            records.append({
                'Column Name': column,
                'Business Name': '',
                'Description': '',
                'Business Owner': '',
                'Data Steward': '',
                'Is Mandatory': '',
                'Is PII': '',
                'Is Sensitive': '',
                'Business Rules': '',
                'Valid Values': '',
                'Source System': '',
                'Transformation Logic': '',
                'Notes': ''
            })
        
        template = pd.DataFrame(records)
        
        self.logger.info(f"Business metadata template generated for {len(records)} columns")
        
        return template
    
    def generate_profiling_summary(self, dataset_profile: Dict[str, Any],
                                   column_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive profiling summary for catalog.
        
        Args:
            dataset_profile: Dataset-level profile
            column_profiles: List of column profiles
            
        Returns:
            Dictionary containing profiling summary
        """
        self.logger.info("Generating profiling summary...")
        
        # Calculate aggregate statistics
        total_quality_score = sum(p.get('quality_score', 0) for p in column_profiles)
        avg_quality_score = total_quality_score / len(column_profiles) if column_profiles else 0
        
        columns_with_issues = sum(1 for p in column_profiles if p.get('quality_issues', []))
        
        summary = {
            'profiling_metadata': {
                'profiling_timestamp': dataset_profile.get('profiling_timestamp', ''),
                'dataset_name': dataset_profile.get('dataset_name', ''),
                'total_rows': dataset_profile.get('total_rows', 0),
                'total_columns': dataset_profile.get('total_columns', 0),
                'total_cells': dataset_profile.get('total_cells', 0),
                'memory_usage_mb': dataset_profile.get('memory_usage_mb', 0)
            },
            'quality_summary': {
                'overall_completeness': dataset_profile.get('completeness_percentage', 0),
                'average_column_quality_score': round(avg_quality_score, 2),
                'columns_with_quality_issues': columns_with_issues,
                'duplicate_rows': dataset_profile.get('duplicate_rows', 0),
                'duplicate_row_percentage': dataset_profile.get('duplicate_row_percentage', 0)
            },
            'column_summary': {
                'total_columns': len(column_profiles),
                'numeric_columns': sum(1 for p in column_profiles if 'mean' in p),
                'text_columns': sum(1 for p in column_profiles if 'avg_length' in p),
                'date_columns': sum(1 for p in column_profiles if 'date_range_days' in p),
                'columns_with_nulls': sum(1 for p in column_profiles if p.get('null_count', 0) > 0),
                'columns_with_blanks': sum(1 for p in column_profiles if p.get('blank_count', 0) > 0),
                'unique_columns': sum(1 for p in column_profiles if p.get('is_unique', False))
            },
            'data_types': {},
            'inferred_types': {}
        }
        
        # Count data types
        for profile in column_profiles:
            dtype = profile.get('data_type', 'unknown')
            summary['data_types'][dtype] = summary['data_types'].get(dtype, 0) + 1
            
            inferred = profile.get('inferred_type', 'unknown')
            summary['inferred_types'][inferred] = summary['inferred_types'].get(inferred, 0) + 1
        
        self.logger.info("Profiling summary generated")
        
        return summary
    
    def export_catalog_to_json(self, catalog_data: Dict[str, Any], output_path: str) -> None:
        """Export metadata catalog to JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, indent=2, default=str)
            self.logger.info(f"Metadata catalog exported to JSON: {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting catalog to JSON: {str(e)}")
    
    def export_catalog_to_excel(self, data_dictionary: pd.DataFrame,
                               column_metadata: Dict[str, Dict[str, Any]],
                               profiling_summary: Dict[str, Any],
                               output_path: str) -> None:
        """Export complete metadata catalog to Excel"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Data Dictionary sheet
                data_dictionary.to_excel(writer, sheet_name='Data Dictionary', index=False)
                
                # Profiling Summary sheet
                summary_records = []
                for category, metrics in profiling_summary.items():
                    if isinstance(metrics, dict):
                        for metric, value in metrics.items():
                            summary_records.append({
                                'Category': category.replace('_', ' ').title(),
                                'Metric': metric.replace('_', ' ').title(),
                                'Value': value
                            })
                
                pd.DataFrame(summary_records).to_excel(writer, sheet_name='Profiling Summary', index=False)
                
                # Column Metadata sheet (flattened)
                metadata_records = []
                for col_name, metadata in column_metadata.items():
                    record = {'Column Name': col_name}
                    
                    # Flatten nested metadata
                    for category, values in metadata.items():
                        if isinstance(values, dict):
                            for key, value in values.items():
                                record[f"{category}_{key}"] = value
                        else:
                            record[category] = values
                    
                    metadata_records.append(record)
                
                pd.DataFrame(metadata_records).to_excel(writer, sheet_name='Column Metadata', index=False)
            
            self.logger.info(f"Metadata catalog exported to Excel: {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting catalog to Excel: {str(e)}")
    
    def generate_catalog_report(self, profiling_summary: Dict[str, Any]) -> str:
        """Generate human-readable catalog report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DATA QUALITY METADATA CATALOG")
        lines.append("=" * 80)
        lines.append("")
        
        # Profiling Metadata
        if 'profiling_metadata' in profiling_summary:
            meta = profiling_summary['profiling_metadata']
            lines.append("PROFILING METADATA")
            lines.append("-" * 80)
            lines.append(f"Dataset: {meta.get('dataset_name', 'Unknown')}")
            lines.append(f"Profiled: {meta.get('profiling_timestamp', '')}")
            lines.append(f"Total Rows: {meta.get('total_rows', 0):,}")
            lines.append(f"Total Columns: {meta.get('total_columns', 0)}")
            lines.append(f"Memory Usage: {meta.get('memory_usage_mb', 0):.2f} MB")
            lines.append("")
        
        # Quality Summary
        if 'quality_summary' in profiling_summary:
            quality = profiling_summary['quality_summary']
            lines.append("QUALITY SUMMARY")
            lines.append("-" * 80)
            lines.append(f"Overall Completeness: {quality.get('overall_completeness', 0):.2f}%")
            lines.append(f"Average Column Quality Score: {quality.get('average_column_quality_score', 0):.2f}")
            lines.append(f"Columns with Issues: {quality.get('columns_with_quality_issues', 0)}")
            lines.append(f"Duplicate Rows: {quality.get('duplicate_rows', 0)} ({quality.get('duplicate_row_percentage', 0):.2f}%)")
            lines.append("")
        
        # Column Summary
        if 'column_summary' in profiling_summary:
            cols = profiling_summary['column_summary']
            lines.append("COLUMN SUMMARY")
            lines.append("-" * 80)
            lines.append(f"Total Columns: {cols.get('total_columns', 0)}")
            lines.append(f"  Numeric: {cols.get('numeric_columns', 0)}")
            lines.append(f"  Text: {cols.get('text_columns', 0)}")
            lines.append(f"  Date: {cols.get('date_columns', 0)}")
            lines.append(f"Columns with Nulls: {cols.get('columns_with_nulls', 0)}")
            lines.append(f"Columns with Blanks: {cols.get('columns_with_blanks', 0)}")
            lines.append(f"Unique Columns: {cols.get('unique_columns', 0)}")
            lines.append("")
        
        # Data Types
        if 'data_types' in profiling_summary:
            lines.append("DATA TYPE DISTRIBUTION")
            lines.append("-" * 80)
            for dtype, count in profiling_summary['data_types'].items():
                lines.append(f"  {dtype}: {count}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return '\n'.join(lines)

# Made with Bob
