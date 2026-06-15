"""
ETL Reconciliation Module
=========================

Performs source-target validation and reconciliation for ETL processes.

Features:
- Record count comparison
- Sum validation (numeric columns)
- Hash total validation
- Missing records detection
- Additional records detection
- Data mismatch detection
- Reconciliation reports

Author: Bob
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class ETLReconciler:
    """
    ETL reconciliation engine that validates data consistency
    between source and target systems.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ETL Reconciler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.tolerance = self.config.get('numeric_tolerance', 0.01)
    
    def reconcile_record_count(self, source_df: pd.DataFrame,
                               target_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare record counts between source and target.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            
        Returns:
            Dictionary containing reconciliation results
        """
        self.logger.info("Performing record count reconciliation...")
        
        source_count = len(source_df)
        target_count = len(target_df)
        difference = target_count - source_count
        match_percentage = (min(source_count, target_count) / max(source_count, target_count) * 100) if max(source_count, target_count) > 0 else 100
        
        result = {
            'check_type': 'Record Count',
            'source_count': source_count,
            'target_count': target_count,
            'difference': difference,
            'match_percentage': round(match_percentage, 2),
            'status': 'PASS' if difference == 0 else 'FAIL',
            'severity': self._determine_severity(abs(difference), source_count)
        }
        
        self.logger.info(f"Record count: Source={source_count}, Target={target_count}, Diff={difference}")
        
        return result
    
    def reconcile_sum_validation(self, source_df: pd.DataFrame,
                                 target_df: pd.DataFrame,
                                 numeric_columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Compare sums of numeric columns between source and target.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            numeric_columns: List of numeric columns to validate (None = all numeric)
            
        Returns:
            List of validation results for each column
        """
        self.logger.info("Performing sum validation...")
        
        results = []
        
        # Identify numeric columns
        if numeric_columns is None:
            numeric_columns = source_df.select_dtypes(include=['number']).columns.tolist()
        
        # Filter to columns present in both dataframes
        common_columns = [col for col in numeric_columns if col in source_df.columns and col in target_df.columns]
        
        for column in common_columns:
            source_sum = source_df[column].sum()
            target_sum = target_df[column].sum()
            difference = target_sum - source_sum
            
            # Check if within tolerance
            if abs(source_sum) > 0:
                diff_percentage = abs(difference / source_sum * 100)
            else:
                diff_percentage = 0 if difference == 0 else 100
            
            status = 'PASS' if diff_percentage <= self.tolerance else 'FAIL'
            
            result = {
                'check_type': 'Sum Validation',
                'column': column,
                'source_sum': float(source_sum),
                'target_sum': float(target_sum),
                'difference': float(difference),
                'difference_percentage': round(diff_percentage, 4),
                'status': status,
                'severity': self._determine_severity_percentage(diff_percentage)
            }
            
            results.append(result)
            self.logger.debug(f"Sum validation for {column}: {status}")
        
        return results
    
    def reconcile_hash_totals(self, source_df: pd.DataFrame,
                             target_df: pd.DataFrame,
                             key_columns: List[str]) -> Dict[str, Any]:
        """
        Compare hash totals to detect data changes.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            key_columns: Columns to include in hash calculation
            
        Returns:
            Dictionary containing hash validation results
        """
        self.logger.info("Performing hash total validation...")
        
        # Calculate hash for source
        source_hash = self._calculate_dataframe_hash(source_df, key_columns)
        
        # Calculate hash for target
        target_hash = self._calculate_dataframe_hash(target_df, key_columns)
        
        result = {
            'check_type': 'Hash Total',
            'source_hash': source_hash,
            'target_hash': target_hash,
            'status': 'PASS' if source_hash == target_hash else 'FAIL',
            'severity': 'Critical' if source_hash != target_hash else 'None'
        }
        
        self.logger.info(f"Hash validation: {result['status']}")
        
        return result
    
    def find_missing_records(self, source_df: pd.DataFrame,
                            target_df: pd.DataFrame,
                            key_columns: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Find records present in source but missing in target.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            key_columns: Primary key columns
            
        Returns:
            Tuple of (missing_records_df, summary_dict)
        """
        self.logger.info("Finding missing records...")
        
        # Create composite key
        source_keys = source_df[key_columns].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        target_keys = target_df[key_columns].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        
        # Find missing keys
        missing_keys = set(source_keys) - set(target_keys)
        
        # Get missing records
        missing_mask = source_keys.isin(missing_keys)
        missing_records = source_df[missing_mask].copy()
        
        summary = {
            'check_type': 'Missing Records',
            'missing_count': len(missing_records),
            'missing_percentage': round(len(missing_records) / len(source_df) * 100, 2) if len(source_df) > 0 else 0,
            'status': 'PASS' if len(missing_records) == 0 else 'FAIL',
            'severity': self._determine_severity(len(missing_records), len(source_df))
        }
        
        self.logger.info(f"Missing records: {len(missing_records)}")
        
        return missing_records, summary
    
    def find_additional_records(self, source_df: pd.DataFrame,
                               target_df: pd.DataFrame,
                               key_columns: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Find records present in target but not in source.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            key_columns: Primary key columns
            
        Returns:
            Tuple of (additional_records_df, summary_dict)
        """
        self.logger.info("Finding additional records...")
        
        # Create composite key
        source_keys = source_df[key_columns].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        target_keys = target_df[key_columns].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        
        # Find additional keys
        additional_keys = set(target_keys) - set(source_keys)
        
        # Get additional records
        additional_mask = target_keys.isin(additional_keys)
        additional_records = target_df[additional_mask].copy()
        
        summary = {
            'check_type': 'Additional Records',
            'additional_count': len(additional_records),
            'additional_percentage': round(len(additional_records) / len(target_df) * 100, 2) if len(target_df) > 0 else 0,
            'status': 'PASS' if len(additional_records) == 0 else 'FAIL',
            'severity': self._determine_severity(len(additional_records), len(target_df))
        }
        
        self.logger.info(f"Additional records: {len(additional_records)}")
        
        return additional_records, summary
    
    def find_data_mismatches(self, source_df: pd.DataFrame,
                            target_df: pd.DataFrame,
                            key_columns: List[str],
                            compare_columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Find records with data mismatches between source and target.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            key_columns: Primary key columns
            compare_columns: Columns to compare (None = all common columns)
            
        Returns:
            Tuple of (mismatch_records_df, summary_dict)
        """
        self.logger.info("Finding data mismatches...")
        
        # Merge on key columns
        merged = source_df.merge(
            target_df,
            on=key_columns,
            how='inner',
            suffixes=('_source', '_target')
        )
        
        if len(merged) == 0:
            return pd.DataFrame(), {
                'check_type': 'Data Mismatches',
                'mismatch_count': 0,
                'mismatch_percentage': 0,
                'status': 'PASS',
                'severity': 'None'
            }
        
        # Determine columns to compare
        if compare_columns is None:
            # Get all common columns except keys
            source_cols = set(source_df.columns) - set(key_columns)
            target_cols = set(target_df.columns) - set(key_columns)
            compare_columns = list(source_cols & target_cols)
        
        # Find mismatches
        mismatch_mask = pd.Series([False] * len(merged))
        mismatch_details = []
        
        for col in compare_columns:
            source_col = f"{col}_source"
            target_col = f"{col}_target"
            
            if source_col in merged.columns and target_col in merged.columns:
                # Handle numeric comparison with tolerance
                if pd.api.types.is_numeric_dtype(merged[source_col]):
                    col_mismatch = ~pd.isna(merged[source_col]) & ~pd.isna(merged[target_col]) & \
                                  (abs(merged[source_col] - merged[target_col]) > self.tolerance)
                else:
                    col_mismatch = (merged[source_col].astype(str) != merged[target_col].astype(str))
                
                mismatch_mask |= col_mismatch
                
                if col_mismatch.any():
                    mismatch_details.append({
                        'column': col,
                        'mismatch_count': int(col_mismatch.sum())
                    })
        
        mismatch_records = merged[mismatch_mask].copy()
        
        summary = {
            'check_type': 'Data Mismatches',
            'mismatch_count': len(mismatch_records),
            'mismatch_percentage': round(len(mismatch_records) / len(merged) * 100, 2) if len(merged) > 0 else 0,
            'columns_with_mismatches': len(mismatch_details),
            'mismatch_details': mismatch_details,
            'status': 'PASS' if len(mismatch_records) == 0 else 'FAIL',
            'severity': self._determine_severity(len(mismatch_records), len(merged))
        }
        
        self.logger.info(f"Data mismatches: {len(mismatch_records)}")
        
        return mismatch_records, summary
    
    def perform_full_reconciliation(self, source_df: pd.DataFrame,
                                   target_df: pd.DataFrame,
                                   key_columns: List[str],
                                   numeric_columns: Optional[List[str]] = None,
                                   compare_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform complete reconciliation with all checks.
        
        Args:
            source_df: Source DataFrame
            target_df: Target DataFrame
            key_columns: Primary key columns
            numeric_columns: Numeric columns for sum validation
            compare_columns: Columns for data comparison
            
        Returns:
            Dictionary containing all reconciliation results
        """
        self.logger.info("Starting full ETL reconciliation...")
        
        results = {
            'reconciliation_timestamp': pd.Timestamp.now().isoformat(),
            'source_info': {
                'record_count': len(source_df),
                'column_count': len(source_df.columns)
            },
            'target_info': {
                'record_count': len(target_df),
                'column_count': len(target_df.columns)
            },
            'checks': []
        }
        
        # Record count check
        count_result = self.reconcile_record_count(source_df, target_df)
        results['checks'].append(count_result)
        
        # Sum validation
        sum_results = self.reconcile_sum_validation(source_df, target_df, numeric_columns)
        results['checks'].extend(sum_results)
        
        # Hash validation
        hash_result = self.reconcile_hash_totals(source_df, target_df, key_columns)
        results['checks'].append(hash_result)
        
        # Missing records
        missing_records, missing_summary = self.find_missing_records(source_df, target_df, key_columns)
        results['checks'].append(missing_summary)
        results['missing_records'] = missing_records
        
        # Additional records
        additional_records, additional_summary = self.find_additional_records(source_df, target_df, key_columns)
        results['checks'].append(additional_summary)
        results['additional_records'] = additional_records
        
        # Data mismatches
        mismatch_records, mismatch_summary = self.find_data_mismatches(
            source_df, target_df, key_columns, compare_columns
        )
        results['checks'].append(mismatch_summary)
        results['mismatch_records'] = mismatch_records
        
        # Overall status
        failed_checks = [c for c in results['checks'] if c['status'] == 'FAIL']
        results['overall_status'] = 'PASS' if len(failed_checks) == 0 else 'FAIL'
        results['total_checks'] = len(results['checks'])
        results['passed_checks'] = len(results['checks']) - len(failed_checks)
        results['failed_checks'] = len(failed_checks)
        
        self.logger.info(f"Reconciliation complete: {results['overall_status']} ({results['passed_checks']}/{results['total_checks']} checks passed)")
        
        return results
    
    def _calculate_dataframe_hash(self, df: pd.DataFrame, columns: List[str]) -> str:
        """Calculate hash for DataFrame"""
        # Sort by columns and convert to string
        sorted_df = df[columns].sort_values(by=columns).astype(str)
        
        # Create hash
        hash_obj = hashlib.md5()
        for _, row in sorted_df.iterrows():
            hash_obj.update('|'.join(row.values).encode())
        
        return hash_obj.hexdigest()
    
    def _determine_severity(self, count: int, total: int) -> str:
        """Determine severity based on count and total"""
        if total == 0:
            return 'None'
        
        percentage = count / total * 100
        
        if percentage > 10:
            return 'Critical'
        elif percentage > 5:
            return 'High'
        elif percentage > 1:
            return 'Medium'
        elif percentage > 0:
            return 'Low'
        else:
            return 'None'
    
    def _determine_severity_percentage(self, percentage: float) -> str:
        """Determine severity based on percentage"""
        if percentage > 10:
            return 'Critical'
        elif percentage > 5:
            return 'High'
        elif percentage > 1:
            return 'Medium'
        elif percentage > 0:
            return 'Low'
        else:
            return 'None'
    
    def export_reconciliation_report(self, results: Dict[str, Any], output_path: str) -> None:
        """Export reconciliation results to Excel"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Overall Status', 'Total Checks', 'Passed Checks', 'Failed Checks',
                          'Source Records', 'Target Records'],
                'Value': [results['overall_status'], results['total_checks'], results['passed_checks'],
                         results['failed_checks'], results['source_info']['record_count'],
                         results['target_info']['record_count']]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Checks sheet
            checks_df = pd.DataFrame(results['checks'])
            checks_df.to_excel(writer, sheet_name='All Checks', index=False)
            
            # Missing records
            if 'missing_records' in results and len(results['missing_records']) > 0:
                results['missing_records'].to_excel(writer, sheet_name='Missing Records', index=False)
            
            # Additional records
            if 'additional_records' in results and len(results['additional_records']) > 0:
                results['additional_records'].to_excel(writer, sheet_name='Additional Records', index=False)
            
            # Mismatch records
            if 'mismatch_records' in results and len(results['mismatch_records']) > 0:
                results['mismatch_records'].to_excel(writer, sheet_name='Data Mismatches', index=False)
        
        self.logger.info(f"Reconciliation report exported to: {output_path}")

# Made with Bob
