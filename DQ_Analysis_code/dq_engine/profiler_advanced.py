"""
Advanced Data Profiler Module
==============================

Provides comprehensive data profiling with 15+ metrics per column:
- Data type inference and validation
- Statistical measures (min, max, mean, median, std, quartiles)
- Null/blank analysis
- Uniqueness and cardinality
- Pattern detection and frequency analysis
- Top N values with distribution
- Data quality indicators

Author: Bob
"""

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class AdvancedDataProfiler:
    """
    Advanced data profiling engine that generates comprehensive
    column-level and dataset-level metrics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Advanced Data Profiler.
        
        Args:
            config: Configuration dictionary with profiling parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.top_n_values = self.config.get('top_n_frequent_values', 10)
        self.pattern_sample_size = self.config.get('pattern_sample_size', 1000)
        
    def profile_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive dataset-level profile.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary containing dataset-level metrics
        """
        self.logger.info("Generating dataset-level profile...")
        
        profile = {
            'dataset_name': self.config.get('dataset_name', 'Unknown'),
            'profiling_timestamp': datetime.now().isoformat(),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'total_cells': len(df) * len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'duplicate_rows': df.duplicated().sum(),
            'duplicate_row_percentage': (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0,
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict(),
        }
        
        # Calculate overall null statistics
        total_nulls = df.isnull().sum().sum()
        profile['total_null_cells'] = int(total_nulls)
        profile['null_cell_percentage'] = (total_nulls / profile['total_cells'] * 100) if profile['total_cells'] > 0 else 0
        
        # Calculate completeness
        profile['completeness_percentage'] = 100 - profile['null_cell_percentage']
        
        self.logger.info(f"Dataset profile complete: {profile['total_rows']} rows, {profile['total_columns']} columns")
        
        return profile
    
    def profile_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """
        Generate comprehensive column-level profile with 15+ metrics.
        
        Args:
            series: Pandas Series to profile
            column_name: Name of the column
            
        Returns:
            Dictionary containing all column metrics
        """
        self.logger.debug(f"Profiling column: {column_name}")
        
        profile = {
            'column_name': column_name,
            'data_type': str(series.dtype),
            'inferred_type': self._infer_semantic_type(series),
        }
        
        # Basic counts
        total_count = len(series)
        profile['record_count'] = total_count
        profile['null_count'] = int(series.isnull().sum())
        profile['null_percentage'] = (profile['null_count'] / total_count * 100) if total_count > 0 else 0
        
        # Non-null series for further analysis
        non_null_series = series.dropna()
        non_null_count = len(non_null_series)
        profile['non_null_count'] = non_null_count
        
        # Blank/empty string detection
        if series.dtype == 'object':
            blank_count = (non_null_series.astype(str).str.strip() == '').sum()
            profile['blank_count'] = int(blank_count)
            profile['blank_percentage'] = (blank_count / total_count * 100) if total_count > 0 else 0
        else:
            profile['blank_count'] = 0
            profile['blank_percentage'] = 0.0
        
        # Completeness
        profile['completeness_percentage'] = 100 - profile['null_percentage'] - profile['blank_percentage']
        
        # Uniqueness metrics
        profile['distinct_count'] = int(series.nunique())
        profile['distinct_percentage'] = (profile['distinct_count'] / total_count * 100) if total_count > 0 else 0
        profile['duplicate_count'] = total_count - profile['distinct_count']
        profile['duplicate_percentage'] = (profile['duplicate_count'] / total_count * 100) if total_count > 0 else 0
        profile['is_unique'] = profile['distinct_count'] == non_null_count
        profile['cardinality'] = 'High' if profile['distinct_percentage'] > 95 else 'Medium' if profile['distinct_percentage'] > 50 else 'Low'
        
        # Statistical measures (for numeric columns)
        if pd.api.types.is_numeric_dtype(series):
            profile.update(self._profile_numeric_column(non_null_series))
        elif pd.api.types.is_datetime64_any_dtype(series):
            profile.update(self._profile_datetime_column(non_null_series))
        else:
            profile.update(self._profile_text_column(non_null_series))
        
        # Top N frequent values
        profile['top_values'] = self._get_top_n_values(series, self.top_n_values)
        
        # Pattern analysis
        profile['patterns'] = self._analyze_patterns(non_null_series)
        
        # Data quality indicators
        profile['quality_score'] = self._calculate_column_quality_score(profile)
        profile['quality_issues'] = self._identify_column_issues(profile)
        
        return profile
    
    def _infer_semantic_type(self, series: pd.Series) -> str:
        """Infer semantic data type (email, phone, date, numeric, text, etc.)"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 'empty'
        
        # Sample for performance
        sample = non_null.head(min(100, len(non_null)))
        sample_str = sample.astype(str)
        
        # Email pattern
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        if sample_str.str.match(email_pattern).sum() / len(sample) > 0.8:
            return 'email'
        
        # Phone pattern (various formats)
        phone_pattern = r'^[\d\s\-\(\)\+]{10,}$'
        if sample_str.str.match(phone_pattern).sum() / len(sample) > 0.8:
            return 'phone'
        
        # URL pattern
        url_pattern = r'^https?://'
        if sample_str.str.match(url_pattern).sum() / len(sample) > 0.8:
            return 'url'
        
        # Numeric
        if pd.api.types.is_numeric_dtype(series):
            if series.dtype in ['int64', 'int32', 'int16', 'int8']:
                return 'integer'
            return 'decimal'
        
        # Date/Time
        if pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        
        # Try to parse as date
        try:
            pd.to_datetime(sample, errors='coerce')
            if pd.to_datetime(sample, errors='coerce').notna().sum() / len(sample) > 0.8:
                return 'date_string'
        except:
            pass
        
        # Boolean
        unique_values = set(sample_str.str.lower().unique())
        if unique_values.issubset({'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n'}):
            return 'boolean'
        
        # Default to text
        return 'text'
    
    def _profile_numeric_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile numeric column with statistical measures"""
        profile = {}
        
        if len(series) == 0:
            return {
                'min_value': None, 'max_value': None, 'mean': None,
                'median': None, 'std_dev': None, 'variance': None,
                'q1': None, 'q3': None, 'iqr': None,
                'sum': None, 'range': None,
                'coefficient_of_variation': None,
                'skewness': None, 'kurtosis': None
            }
        
        profile['min_value'] = float(series.min())
        profile['max_value'] = float(series.max())
        profile['mean'] = float(series.mean())
        profile['median'] = float(series.median())
        profile['std_dev'] = float(series.std())
        profile['variance'] = float(series.var())
        
        # Quartiles
        profile['q1'] = float(series.quantile(0.25))
        profile['q3'] = float(series.quantile(0.75))
        profile['iqr'] = profile['q3'] - profile['q1']
        
        # Additional metrics
        profile['sum'] = float(series.sum())
        profile['range'] = profile['max_value'] - profile['min_value']
        
        # Coefficient of variation
        if profile['mean'] != 0:
            profile['coefficient_of_variation'] = (profile['std_dev'] / abs(profile['mean'])) * 100
        else:
            profile['coefficient_of_variation'] = None
        
        # Skewness and Kurtosis
        try:
            profile['skewness'] = float(series.skew())
            profile['kurtosis'] = float(series.kurtosis())
        except:
            profile['skewness'] = None
            profile['kurtosis'] = None
        
        # Negative value detection
        profile['negative_count'] = int((series < 0).sum())
        profile['negative_percentage'] = (profile['negative_count'] / len(series) * 100) if len(series) > 0 else 0
        
        # Zero value detection
        profile['zero_count'] = int((series == 0).sum())
        profile['zero_percentage'] = (profile['zero_count'] / len(series) * 100) if len(series) > 0 else 0
        
        return profile
    
    def _profile_datetime_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile datetime column"""
        profile = {}
        
        if len(series) == 0:
            return {
                'min_date': None, 'max_date': None,
                'date_range_days': None, 'most_common_date': None
            }
        
        profile['min_date'] = str(series.min())
        profile['max_date'] = str(series.max())
        
        # Date range
        date_range = series.max() - series.min()
        profile['date_range_days'] = date_range.days if hasattr(date_range, 'days') else None
        
        # Most common date
        most_common = series.mode()
        profile['most_common_date'] = str(most_common.iloc[0]) if len(most_common) > 0 else None
        
        return profile
    
    def _profile_text_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile text column"""
        profile = {}
        
        if len(series) == 0:
            return {
                'min_length': None, 'max_length': None,
                'avg_length': None, 'most_common_value': None
            }
        
        # Convert to string
        str_series = series.astype(str)
        lengths = str_series.str.len()
        
        profile['min_length'] = int(lengths.min())
        profile['max_length'] = int(lengths.max())
        profile['avg_length'] = float(lengths.mean())
        
        # Most common value
        most_common = series.mode()
        profile['most_common_value'] = str(most_common.iloc[0]) if len(most_common) > 0 else None
        
        return profile
    
    def _get_top_n_values(self, series: pd.Series, n: int) -> List[Dict[str, Any]]:
        """Get top N most frequent values with counts and percentages"""
        value_counts = series.value_counts().head(n)
        total = len(series)
        
        top_values = []
        for value, count in value_counts.items():
            top_values.append({
                'value': str(value) if not pd.isna(value) else 'NULL',
                'count': int(count),
                'percentage': round((count / total * 100), 2) if total > 0 else 0
            })
        
        return top_values
    
    def _analyze_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze data patterns in the column"""
        if len(series) == 0:
            return {'pattern_count': 0, 'patterns': []}
        
        # Sample for performance
        sample = series.head(min(self.pattern_sample_size, len(series)))
        str_sample = sample.astype(str)
        
        # Generate patterns by replacing digits and letters
        patterns = str_sample.apply(lambda x: re.sub(r'\d', '9', re.sub(r'[A-Za-z]', 'A', x)))
        pattern_counts = patterns.value_counts().head(10)
        
        pattern_list = []
        for pattern, count in pattern_counts.items():
            pattern_list.append({
                'pattern': pattern,
                'count': int(count),
                'percentage': round((count / len(sample) * 100), 2),
                'example': str(sample[patterns == pattern].iloc[0]) if len(sample[patterns == pattern]) > 0 else None
            })
        
        return {
            'pattern_count': len(pattern_counts),
            'patterns': pattern_list
        }
    
    def _calculate_column_quality_score(self, profile: Dict[str, Any]) -> float:
        """Calculate quality score for a column (0-100)"""
        score = 100.0
        
        # Deduct for nulls
        score -= profile['null_percentage'] * 0.5
        
        # Deduct for blanks
        score -= profile['blank_percentage'] * 0.5
        
        # Bonus for high uniqueness (if appropriate)
        if profile['distinct_percentage'] > 90:
            score += 5
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))
    
    def _identify_column_issues(self, profile: Dict[str, Any]) -> List[str]:
        """Identify potential quality issues in a column"""
        issues = []
        
        if profile['null_percentage'] > 10:
            issues.append(f"High null percentage: {profile['null_percentage']:.2f}%")
        
        if profile['blank_percentage'] > 10:
            issues.append(f"High blank percentage: {profile['blank_percentage']:.2f}%")
        
        if profile['duplicate_percentage'] > 50 and profile['distinct_count'] > 1:
            issues.append(f"High duplicate percentage: {profile['duplicate_percentage']:.2f}%")
        
        if profile.get('negative_percentage', 0) > 0:
            issues.append(f"Contains negative values: {profile['negative_percentage']:.2f}%")
        
        if profile['completeness_percentage'] < 80:
            issues.append(f"Low completeness: {profile['completeness_percentage']:.2f}%")
        
        return issues
    
    def profile_dataframe(self, df: pd.DataFrame) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate complete profile for entire DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (dataset_profile, column_profiles_list)
        """
        self.logger.info(f"Starting comprehensive profiling of DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Dataset-level profile
        dataset_profile = self.profile_dataset(df)
        
        # Column-level profiles
        column_profiles = []
        for column in df.columns:
            try:
                col_profile = self.profile_column(df[column], column)
                column_profiles.append(col_profile)
            except Exception as e:
                self.logger.error(f"Error profiling column {column}: {str(e)}")
                column_profiles.append({
                    'column_name': column,
                    'error': str(e),
                    'quality_score': 0
                })
        
        self.logger.info(f"Profiling complete: {len(column_profiles)} columns profiled")
        
        return dataset_profile, column_profiles
    
    def export_profile_to_json(self, dataset_profile: Dict[str, Any], 
                               column_profiles: List[Dict[str, Any]], 
                               output_path: str) -> None:
        """Export profile to JSON file"""
        import json
        
        output = {
            'dataset_profile': dataset_profile,
            'column_profiles': column_profiles
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, default=str)
        
        self.logger.info(f"Profile exported to JSON: {output_path}")
    
    def export_profile_to_excel(self, dataset_profile: Dict[str, Any],
                                column_profiles: List[Dict[str, Any]],
                                output_path: str) -> None:
        """Export profile to Excel file with multiple sheets"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Dataset summary sheet
            dataset_df = pd.DataFrame([dataset_profile])
            dataset_df.to_excel(writer, sheet_name='Dataset Summary', index=False)
            
            # Column profiles sheet
            columns_df = pd.DataFrame(column_profiles)
            columns_df.to_excel(writer, sheet_name='Column Profiles', index=False)
            
            # Top values sheet (if available)
            top_values_data = []
            for col_profile in column_profiles:
                if 'top_values' in col_profile:
                    for tv in col_profile['top_values']:
                        top_values_data.append({
                            'column_name': col_profile['column_name'],
                            'value': tv['value'],
                            'count': tv['count'],
                            'percentage': tv['percentage']
                        })
            
            if top_values_data:
                top_values_df = pd.DataFrame(top_values_data)
                top_values_df.to_excel(writer, sheet_name='Top Values', index=False)
        
        self.logger.info(f"Profile exported to Excel: {output_path}")

# Made with Bob
