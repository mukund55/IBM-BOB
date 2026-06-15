"""
Multi-Dimensional Data Quality Scorer
======================================

Implements 5-dimension data quality scoring framework:
1. Completeness - Measures presence of data (nulls, blanks)
2. Validity - Measures conformance to rules (patterns, ranges, types)
3. Consistency - Measures uniformity and standardization
4. Accuracy - Measures correctness against reference data
5. Uniqueness - Measures duplicate detection

Overall DQ Score: Weighted average of all dimensions (0-100)
Classification: Excellent (90-100), Moderate (75-89), Poor (<75)

Author: Bob
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class MultiDimensionalScorer:
    """
    Multi-dimensional data quality scoring engine that calculates
    quality scores across 5 key dimensions.
    """
    
    # Default dimension weights (must sum to 100)
    DEFAULT_WEIGHTS = {
        'completeness': 25,
        'validity': 25,
        'consistency': 20,
        'accuracy': 15,
        'uniqueness': 15
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Multi-Dimensional Scorer.
        
        Args:
            config: Configuration dictionary with scoring parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Get dimension weights from config or use defaults
        self.weights = self.config.get('dimension_weights', self.DEFAULT_WEIGHTS)
        
        # Validate weights sum to 100
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 100) > 0.01:
            self.logger.warning(f"Dimension weights sum to {weight_sum}, normalizing to 100")
            factor = 100 / weight_sum
            self.weights = {k: v * factor for k, v in self.weights.items()}
    
    def calculate_completeness_score(self, df: pd.DataFrame, 
                                    anomaly_summary: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Completeness Score (0-100).
        
        Measures:
        - Null values
        - Blank values
        - Missing mandatory fields
        - Missing mandatory columns
        
        Args:
            df: Input DataFrame
            anomaly_summary: Dictionary containing anomaly detection results
            
        Returns:
            Tuple of (score, details_dict)
        """
        self.logger.debug("Calculating Completeness Score...")
        
        total_cells = len(df) * len(df.columns)
        total_rows = len(df)
        
        # Count null cells
        null_cells = df.isnull().sum().sum()
        null_percentage = (null_cells / total_cells * 100) if total_cells > 0 else 0
        
        # Count blank cells (for string columns)
        blank_cells = 0
        for col in df.select_dtypes(include=['object']).columns:
            blank_cells += (df[col].astype(str).str.strip() == '').sum()
        blank_percentage = (blank_cells / total_cells * 100) if total_cells > 0 else 0
        
        # Get mandatory field violations from anomaly summary
        mandatory_violations = anomaly_summary.get('mandatory_field_violations', {}).get('count', 0)
        mandatory_percentage = (mandatory_violations / total_rows * 100) if total_rows > 0 else 0
        
        # Get missing mandatory columns
        missing_columns = anomaly_summary.get('missing_mandatory_columns', {}).get('count', 0)
        missing_col_penalty = missing_columns * 10  # 10 points per missing column
        
        # Calculate score (start at 100, deduct for issues)
        score = 100.0
        score -= null_percentage * 0.5  # 0.5 points per 1% nulls
        score -= blank_percentage * 0.5  # 0.5 points per 1% blanks
        score -= mandatory_percentage * 0.8  # 0.8 points per 1% mandatory violations
        score -= missing_col_penalty
        
        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))
        
        details = {
            'dimension': 'Completeness',
            'score': round(score, 2),
            'null_percentage': round(null_percentage, 2),
            'blank_percentage': round(blank_percentage, 2),
            'mandatory_violations_percentage': round(mandatory_percentage, 2),
            'missing_mandatory_columns': missing_columns,
            'total_cells': total_cells,
            'null_cells': int(null_cells),
            'blank_cells': int(blank_cells),
            'issues': []
        }
        
        if null_percentage > 5:
            details['issues'].append(f"High null percentage: {null_percentage:.2f}%")
        if blank_percentage > 5:
            details['issues'].append(f"High blank percentage: {blank_percentage:.2f}%")
        if mandatory_percentage > 1:
            details['issues'].append(f"Mandatory field violations: {mandatory_percentage:.2f}%")
        if missing_columns > 0:
            details['issues'].append(f"Missing {missing_columns} mandatory column(s)")
        
        self.logger.debug(f"Completeness Score: {score:.2f}")
        return score, details
    
    def calculate_validity_score(self, df: pd.DataFrame,
                                 anomaly_summary: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Validity Score (0-100).
        
        Measures:
        - Pattern violations (regex, email, phone)
        - Range violations
        - Datatype violations
        - Invalid dates
        - Allowed value violations
        
        Args:
            df: Input DataFrame
            anomaly_summary: Dictionary containing anomaly detection results
            
        Returns:
            Tuple of (score, details_dict)
        """
        self.logger.debug("Calculating Validity Score...")
        
        total_rows = len(df)
        
        # Collect validity violations
        pattern_violations = anomaly_summary.get('pattern_violations', {}).get('count', 0)
        range_violations = anomaly_summary.get('range_violations', {}).get('count', 0)
        datatype_violations = anomaly_summary.get('datatype_violations', {}).get('count', 0)
        invalid_dates = anomaly_summary.get('invalid_dates', {}).get('count', 0)
        invalid_emails = anomaly_summary.get('invalid_emails', {}).get('count', 0)
        allowed_value_violations = anomaly_summary.get('allowed_value_violations', {}).get('count', 0)
        
        total_violations = (pattern_violations + range_violations + datatype_violations +
                          invalid_dates + invalid_emails + allowed_value_violations)
        
        violation_percentage = (total_violations / total_rows * 100) if total_rows > 0 else 0
        
        # Calculate score
        score = 100.0
        score -= violation_percentage * 0.8  # 0.8 points per 1% violations
        
        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))
        
        details = {
            'dimension': 'Validity',
            'score': round(score, 2),
            'total_violations': int(total_violations),
            'violation_percentage': round(violation_percentage, 2),
            'pattern_violations': int(pattern_violations),
            'range_violations': int(range_violations),
            'datatype_violations': int(datatype_violations),
            'invalid_dates': int(invalid_dates),
            'invalid_emails': int(invalid_emails),
            'allowed_value_violations': int(allowed_value_violations),
            'issues': []
        }
        
        if pattern_violations > 0:
            details['issues'].append(f"Pattern violations: {pattern_violations}")
        if range_violations > 0:
            details['issues'].append(f"Range violations: {range_violations}")
        if datatype_violations > 0:
            details['issues'].append(f"Datatype violations: {datatype_violations}")
        if invalid_emails > 0:
            details['issues'].append(f"Invalid emails: {invalid_emails}")
        
        self.logger.debug(f"Validity Score: {score:.2f}")
        return score, details
    
    def calculate_consistency_score(self, df: pd.DataFrame,
                                    anomaly_summary: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Consistency Score (0-100).
        
        Measures:
        - Mixed datatypes in columns
        - Special character violations
        - Standardization issues
        - Format consistency
        
        Args:
            df: Input DataFrame
            anomaly_summary: Dictionary containing anomaly detection results
            
        Returns:
            Tuple of (score, details_dict)
        """
        self.logger.debug("Calculating Consistency Score...")
        
        total_rows = len(df)
        
        # Collect consistency violations
        mixed_types = anomaly_summary.get('mixed_types', {}).get('count', 0)
        special_char_violations = anomaly_summary.get('special_characters', {}).get('count', 0)
        
        total_violations = mixed_types + special_char_violations
        violation_percentage = (total_violations / total_rows * 100) if total_rows > 0 else 0
        
        # Check for case inconsistency in string columns
        case_inconsistency_count = 0
        for col in df.select_dtypes(include=['object']).columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                # Check if values have mixed case
                str_values = non_null.astype(str)
                has_upper = str_values.str.isupper().any()
                has_lower = str_values.str.islower().any()
                has_mixed = (~str_values.str.isupper() & ~str_values.str.islower()).any()
                
                if (has_upper and has_lower) or has_mixed:
                    case_inconsistency_count += 1
        
        # Calculate score
        score = 100.0
        score -= violation_percentage * 0.7  # 0.7 points per 1% violations
        score -= case_inconsistency_count * 2  # 2 points per inconsistent column
        
        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))
        
        details = {
            'dimension': 'Consistency',
            'score': round(score, 2),
            'total_violations': int(total_violations),
            'violation_percentage': round(violation_percentage, 2),
            'mixed_type_violations': int(mixed_types),
            'special_char_violations': int(special_char_violations),
            'case_inconsistent_columns': case_inconsistency_count,
            'issues': []
        }
        
        if mixed_types > 0:
            details['issues'].append(f"Mixed datatype violations: {mixed_types}")
        if special_char_violations > 0:
            details['issues'].append(f"Special character violations: {special_char_violations}")
        if case_inconsistency_count > 0:
            details['issues'].append(f"Case inconsistency in {case_inconsistency_count} column(s)")
        
        self.logger.debug(f"Consistency Score: {score:.2f}")
        return score, details
    
    def calculate_accuracy_score(self, df: pd.DataFrame,
                                 anomaly_summary: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Accuracy Score (0-100).
        
        Measures:
        - Referential integrity violations
        - Business rule violations
        - Outliers (potential data errors)
        - Negative values where not allowed
        
        Args:
            df: Input DataFrame
            anomaly_summary: Dictionary containing anomaly detection results
            
        Returns:
            Tuple of (score, details_dict)
        """
        self.logger.debug("Calculating Accuracy Score...")
        
        total_rows = len(df)
        
        # Collect accuracy violations
        referential_violations = anomaly_summary.get('referential_integrity', {}).get('count', 0)
        business_rule_violations = anomaly_summary.get('business_rule_violations', {}).get('count', 0)
        outliers = anomaly_summary.get('outliers', {}).get('count', 0)
        negative_values = anomaly_summary.get('negative_values', {}).get('count', 0)
        
        total_violations = (referential_violations + business_rule_violations +
                          outliers + negative_values)
        
        violation_percentage = (total_violations / total_rows * 100) if total_rows > 0 else 0
        
        # Calculate score
        score = 100.0
        score -= violation_percentage * 0.6  # 0.6 points per 1% violations
        
        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))
        
        details = {
            'dimension': 'Accuracy',
            'score': round(score, 2),
            'total_violations': int(total_violations),
            'violation_percentage': round(violation_percentage, 2),
            'referential_violations': int(referential_violations),
            'business_rule_violations': int(business_rule_violations),
            'outliers': int(outliers),
            'negative_values': int(negative_values),
            'issues': []
        }
        
        if referential_violations > 0:
            details['issues'].append(f"Referential integrity violations: {referential_violations}")
        if business_rule_violations > 0:
            details['issues'].append(f"Business rule violations: {business_rule_violations}")
        if outliers > 0:
            details['issues'].append(f"Outliers detected: {outliers}")
        if negative_values > 0:
            details['issues'].append(f"Invalid negative values: {negative_values}")
        
        self.logger.debug(f"Accuracy Score: {score:.2f}")
        return score, details
    
    def calculate_uniqueness_score(self, df: pd.DataFrame,
                                   anomaly_summary: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Uniqueness Score (0-100).
        
        Measures:
        - Duplicate records
        - Duplicate primary keys
        - Overall data uniqueness
        
        Args:
            df: Input DataFrame
            anomaly_summary: Dictionary containing anomaly detection results
            
        Returns:
            Tuple of (score, details_dict)
        """
        self.logger.debug("Calculating Uniqueness Score...")
        
        total_rows = len(df)
        
        # Collect uniqueness violations
        duplicate_records = anomaly_summary.get('duplicates', {}).get('count', 0)
        duplicate_pks = anomaly_summary.get('duplicate_primary_keys', {}).get('count', 0)
        
        duplicate_percentage = (duplicate_records / total_rows * 100) if total_rows > 0 else 0
        pk_duplicate_percentage = (duplicate_pks / total_rows * 100) if total_rows > 0 else 0
        
        # Calculate score
        score = 100.0
        score -= duplicate_percentage * 0.5  # 0.5 points per 1% duplicates
        score -= pk_duplicate_percentage * 1.0  # 1.0 points per 1% PK duplicates (more severe)
        
        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))
        
        details = {
            'dimension': 'Uniqueness',
            'score': round(score, 2),
            'duplicate_records': int(duplicate_records),
            'duplicate_percentage': round(duplicate_percentage, 2),
            'duplicate_primary_keys': int(duplicate_pks),
            'pk_duplicate_percentage': round(pk_duplicate_percentage, 2),
            'issues': []
        }
        
        if duplicate_records > 0:
            details['issues'].append(f"Duplicate records: {duplicate_records} ({duplicate_percentage:.2f}%)")
        if duplicate_pks > 0:
            details['issues'].append(f"Duplicate primary keys: {duplicate_pks} ({pk_duplicate_percentage:.2f}%)")
        
        self.logger.debug(f"Uniqueness Score: {score:.2f}")
        return score, details
    
    def calculate_overall_score(self, dimension_scores: Dict[str, float]) -> Tuple[float, str, Dict[str, Any]]:
        """
        Calculate overall DQ score as weighted average of dimension scores.
        
        Args:
            dimension_scores: Dictionary of dimension names to scores
            
        Returns:
            Tuple of (overall_score, classification, breakdown_dict)
        """
        self.logger.info("Calculating Overall Data Quality Score...")
        
        # Calculate weighted average
        overall_score = 0.0
        for dimension, score in dimension_scores.items():
            weight = self.weights.get(dimension, 0) / 100
            overall_score += score * weight
        
        # Classify score
        if overall_score >= 90:
            classification = "Excellent"
            color = "green"
        elif overall_score >= 75:
            classification = "Moderate"
            color = "yellow"
        else:
            classification = "Poor"
            color = "red"
        
        breakdown = {
            'overall_score': round(overall_score, 2),
            'classification': classification,
            'color': color,
            'dimension_scores': {k: round(v, 2) for k, v in dimension_scores.items()},
            'dimension_weights': self.weights,
            'weighted_contributions': {
                k: round(v * self.weights.get(k, 0) / 100, 2)
                for k, v in dimension_scores.items()
            }
        }
        
        self.logger.info(f"Overall DQ Score: {overall_score:.2f} ({classification})")
        
        return overall_score, classification, breakdown
    
    def score_data_quality(self, df: pd.DataFrame,
                          anomaly_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform complete multi-dimensional data quality scoring.
        
        Args:
            df: Input DataFrame
            anomaly_summary: Dictionary containing all anomaly detection results
            
        Returns:
            Dictionary containing all scoring results
        """
        self.logger.info("Starting Multi-Dimensional Data Quality Scoring...")
        
        # Calculate each dimension score
        completeness_score, completeness_details = self.calculate_completeness_score(df, anomaly_summary)
        validity_score, validity_details = self.calculate_validity_score(df, anomaly_summary)
        consistency_score, consistency_details = self.calculate_consistency_score(df, anomaly_summary)
        accuracy_score, accuracy_details = self.calculate_accuracy_score(df, anomaly_summary)
        uniqueness_score, uniqueness_details = self.calculate_uniqueness_score(df, anomaly_summary)
        
        # Collect dimension scores
        dimension_scores = {
            'completeness': completeness_score,
            'validity': validity_score,
            'consistency': consistency_score,
            'accuracy': accuracy_score,
            'uniqueness': uniqueness_score
        }
        
        # Calculate overall score
        overall_score, classification, breakdown = self.calculate_overall_score(dimension_scores)
        
        # Compile results
        results = {
            'overall_score': overall_score,
            'classification': classification,
            'breakdown': breakdown,
            'dimensions': {
                'completeness': completeness_details,
                'validity': validity_details,
                'consistency': consistency_details,
                'accuracy': accuracy_details,
                'uniqueness': uniqueness_details
            },
            'summary': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'scoring_timestamp': pd.Timestamp.now().isoformat()
            }
        }
        
        self.logger.info("Multi-Dimensional Scoring Complete")
        
        return results
    
    def export_scorecard_to_dataframe(self, scoring_results: Dict[str, Any]) -> pd.DataFrame:
        """Export scoring results to a DataFrame for reporting"""
        records = []
        
        for dim_name, dim_details in scoring_results['dimensions'].items():
            record = {
                'Dimension': dim_details['dimension'],
                'Score': dim_details['score'],
                'Weight (%)': self.weights.get(dim_name, 0),
                'Weighted Score': scoring_results['breakdown']['weighted_contributions'].get(dim_name, 0),
                'Issues': '; '.join(dim_details.get('issues', []))
            }
            records.append(record)
        
        # Add overall row
        records.append({
            'Dimension': 'OVERALL',
            'Score': scoring_results['overall_score'],
            'Weight (%)': 100,
            'Weighted Score': scoring_results['overall_score'],
            'Issues': f"Classification: {scoring_results['classification']}"
        })
        
        return pd.DataFrame(records)

# Made with Bob
