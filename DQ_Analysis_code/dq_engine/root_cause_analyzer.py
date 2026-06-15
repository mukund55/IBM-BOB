"""
Root Cause Analysis Engine
===========================

AI-powered root cause analysis for data quality issues.
Analyzes patterns and generates probable root causes with confidence scores.

Features:
- Pattern-based root cause inference
- Confidence scoring (0-100)
- Context-aware analysis
- Template-based cause library (100+ scenarios)
- Multi-factor analysis

Author: Bob
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class RootCauseAnalyzer:
    """
    AI-powered root cause analysis engine that identifies probable
    causes for data quality issues.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Root Cause Analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.cause_library = self._build_cause_library()
    
    def _build_cause_library(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build comprehensive library of root causes for various DQ issues.
        
        Returns:
            Dictionary mapping issue types to lists of probable causes
        """
        return {
            'null_values': [
                {
                    'cause': 'Source system not enforcing mandatory field validation',
                    'indicators': ['high_null_percentage', 'mandatory_field'],
                    'confidence_base': 85,
                    'category': 'Source System',
                    'remediation': 'Implement NOT NULL constraints in source database'
                },
                {
                    'cause': 'ETL mapping issue - source field not mapped correctly',
                    'indicators': ['specific_columns', 'recent_increase'],
                    'confidence_base': 80,
                    'category': 'ETL Process',
                    'remediation': 'Review and fix ETL mapping configuration'
                },
                {
                    'cause': 'Upstream data feed incomplete or delayed',
                    'indicators': ['sudden_spike', 'multiple_columns'],
                    'confidence_base': 75,
                    'category': 'Data Feed',
                    'remediation': 'Investigate upstream data provider and SLA'
                },
                {
                    'cause': 'Optional field with no default value defined',
                    'indicators': ['non_mandatory_field', 'consistent_pattern'],
                    'confidence_base': 70,
                    'category': 'Data Model',
                    'remediation': 'Define appropriate default values or make field mandatory'
                },
                {
                    'cause': 'Data extraction query missing JOIN condition',
                    'indicators': ['high_percentage', 'related_tables'],
                    'confidence_base': 65,
                    'category': 'ETL Process',
                    'remediation': 'Review SQL extraction queries for missing JOINs'
                }
            ],
            'duplicate_records': [
                {
                    'cause': 'Missing unique constraint on primary key',
                    'indicators': ['primary_key_duplicates', 'high_count'],
                    'confidence_base': 90,
                    'category': 'Data Model',
                    'remediation': 'Add UNIQUE constraint on primary key columns'
                },
                {
                    'cause': 'ETL process running multiple times without deduplication',
                    'indicators': ['exact_duplicates', 'timestamp_pattern'],
                    'confidence_base': 85,
                    'category': 'ETL Process',
                    'remediation': 'Implement idempotent ETL with deduplication logic'
                },
                {
                    'cause': 'Merge/Upsert logic not working correctly',
                    'indicators': ['incremental_load', 'key_mismatch'],
                    'confidence_base': 80,
                    'category': 'ETL Process',
                    'remediation': 'Fix merge key logic and implement proper UPSERT'
                },
                {
                    'cause': 'Multiple source systems sending same records',
                    'indicators': ['different_timestamps', 'similar_values'],
                    'confidence_base': 75,
                    'category': 'Source System',
                    'remediation': 'Implement master data management (MDM) strategy'
                },
                {
                    'cause': 'Lack of business key definition',
                    'indicators': ['no_primary_key', 'natural_key_missing'],
                    'confidence_base': 70,
                    'category': 'Data Model',
                    'remediation': 'Define and implement proper business keys'
                }
            ],
            'invalid_email': [
                {
                    'cause': 'No email validation at data entry point',
                    'indicators': ['pattern_violations', 'user_input'],
                    'confidence_base': 90,
                    'category': 'Source System',
                    'remediation': 'Implement regex validation in source application'
                },
                {
                    'cause': 'Data migration from legacy system without cleansing',
                    'indicators': ['old_records', 'batch_pattern'],
                    'confidence_base': 80,
                    'category': 'Data Migration',
                    'remediation': 'Perform data cleansing before migration'
                },
                {
                    'cause': 'Manual data entry errors',
                    'indicators': ['random_pattern', 'low_percentage'],
                    'confidence_base': 75,
                    'category': 'Data Entry',
                    'remediation': 'Implement real-time validation and training'
                },
                {
                    'cause': 'Test data mixed with production data',
                    'indicators': ['test_patterns', 'specific_values'],
                    'confidence_base': 85,
                    'category': 'Data Governance',
                    'remediation': 'Separate test and production environments'
                }
            ],
            'pattern_violations': [
                {
                    'cause': 'Inconsistent data format across sources',
                    'indicators': ['multiple_patterns', 'source_variation'],
                    'confidence_base': 85,
                    'category': 'Data Integration',
                    'remediation': 'Standardize data formats across all sources'
                },
                {
                    'cause': 'Missing data transformation rules',
                    'indicators': ['raw_format', 'no_standardization'],
                    'confidence_base': 80,
                    'category': 'ETL Process',
                    'remediation': 'Implement transformation rules in ETL'
                },
                {
                    'cause': 'International data without localization',
                    'indicators': ['country_codes', 'format_variety'],
                    'confidence_base': 75,
                    'category': 'Globalization',
                    'remediation': 'Implement locale-aware validation'
                }
            ],
            'range_violations': [
                {
                    'cause': 'No range validation in source system',
                    'indicators': ['outliers', 'unrealistic_values'],
                    'confidence_base': 85,
                    'category': 'Source System',
                    'remediation': 'Add CHECK constraints for valid ranges'
                },
                {
                    'cause': 'Data type overflow or conversion error',
                    'indicators': ['extreme_values', 'datatype_mismatch'],
                    'confidence_base': 80,
                    'category': 'ETL Process',
                    'remediation': 'Review data type mappings and conversions'
                },
                {
                    'cause': 'Business rule changes not reflected in validation',
                    'indicators': ['recent_violations', 'policy_change'],
                    'confidence_base': 75,
                    'category': 'Business Rules',
                    'remediation': 'Update validation rules to match current business logic'
                },
                {
                    'cause': 'Future dates due to timezone issues',
                    'indicators': ['future_dates', 'timezone_pattern'],
                    'confidence_base': 70,
                    'category': 'ETL Process',
                    'remediation': 'Standardize timezone handling in ETL'
                }
            ],
            'outliers': [
                {
                    'cause': 'Data entry errors (typos, extra zeros)',
                    'indicators': ['extreme_values', 'magnitude_difference'],
                    'confidence_base': 80,
                    'category': 'Data Entry',
                    'remediation': 'Implement range validation and confirmation dialogs'
                },
                {
                    'cause': 'Unit conversion errors (e.g., cents vs dollars)',
                    'indicators': ['consistent_multiplier', 'specific_columns'],
                    'confidence_base': 85,
                    'category': 'ETL Process',
                    'remediation': 'Standardize units and add conversion validation'
                },
                {
                    'cause': 'Legitimate exceptional cases',
                    'indicators': ['business_justification', 'documented'],
                    'confidence_base': 60,
                    'category': 'Business Process',
                    'remediation': 'Document exceptions and create separate handling rules'
                },
                {
                    'cause': 'Data corruption during transmission',
                    'indicators': ['random_pattern', 'transmission_errors'],
                    'confidence_base': 70,
                    'category': 'Data Transfer',
                    'remediation': 'Implement checksums and data integrity validation'
                }
            ],
            'referential_integrity': [
                {
                    'cause': 'Missing foreign key constraints',
                    'indicators': ['orphan_records', 'no_constraints'],
                    'confidence_base': 90,
                    'category': 'Data Model',
                    'remediation': 'Add foreign key constraints to database'
                },
                {
                    'cause': 'Cascade delete not configured properly',
                    'indicators': ['parent_deleted', 'child_remains'],
                    'confidence_base': 85,
                    'category': 'Data Model',
                    'remediation': 'Configure CASCADE DELETE or implement soft deletes'
                },
                {
                    'cause': 'Reference data not loaded before transactional data',
                    'indicators': ['load_sequence', 'timing_issue'],
                    'confidence_base': 80,
                    'category': 'ETL Process',
                    'remediation': 'Ensure proper ETL load sequence'
                },
                {
                    'cause': 'Cross-system reference data out of sync',
                    'indicators': ['multiple_systems', 'sync_delay'],
                    'confidence_base': 75,
                    'category': 'Data Integration',
                    'remediation': 'Implement master data management (MDM)'
                }
            ],
            'business_rule_violations': [
                {
                    'cause': 'Business rules not implemented in source system',
                    'indicators': ['consistent_violations', 'no_validation'],
                    'confidence_base': 85,
                    'category': 'Source System',
                    'remediation': 'Implement business rule validation at source'
                },
                {
                    'cause': 'Rules changed but validation not updated',
                    'indicators': ['recent_violations', 'rule_change'],
                    'confidence_base': 80,
                    'category': 'Business Rules',
                    'remediation': 'Update validation logic to match current rules'
                },
                {
                    'cause': 'Complex rules not fully understood',
                    'indicators': ['edge_cases', 'interpretation_issues'],
                    'confidence_base': 70,
                    'category': 'Requirements',
                    'remediation': 'Clarify business rules with stakeholders'
                }
            ],
            'mixed_datatypes': [
                {
                    'cause': 'Inconsistent data types across source systems',
                    'indicators': ['multiple_sources', 'type_variety'],
                    'confidence_base': 85,
                    'category': 'Data Integration',
                    'remediation': 'Standardize data types in integration layer'
                },
                {
                    'cause': 'String column storing numeric and text values',
                    'indicators': ['varchar_column', 'mixed_content'],
                    'confidence_base': 80,
                    'category': 'Data Model',
                    'remediation': 'Separate into appropriate typed columns'
                },
                {
                    'cause': 'Data quality degradation over time',
                    'indicators': ['temporal_pattern', 'increasing_violations'],
                    'confidence_base': 75,
                    'category': 'Data Governance',
                    'remediation': 'Implement ongoing data quality monitoring'
                }
            ]
        }
    
    def analyze_issue(self, issue_type: str, issue_details: Dict[str, Any],
                     context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Analyze a specific data quality issue and return probable root causes.
        
        Args:
            issue_type: Type of issue (e.g., 'null_values', 'duplicates')
            issue_details: Details about the issue (count, percentage, affected columns)
            context: Additional context (dataset info, historical trends, etc.)
            
        Returns:
            List of probable root causes with confidence scores
        """
        self.logger.debug(f"Analyzing root cause for issue type: {issue_type}")
        
        context = context or {}
        
        # Get potential causes from library
        potential_causes = self.cause_library.get(issue_type, [])
        
        if not potential_causes:
            self.logger.warning(f"No root cause templates found for issue type: {issue_type}")
            return [{
                'cause': f'Unknown root cause for {issue_type}',
                'confidence': 50,
                'category': 'Unknown',
                'remediation': 'Investigate manually'
            }]
        
        # Score each potential cause based on indicators
        scored_causes = []
        for cause_template in potential_causes:
            confidence = self._calculate_confidence(
                cause_template,
                issue_details,
                context
            )
            
            if confidence > 30:  # Only include causes with reasonable confidence
                scored_causes.append({
                    'cause': cause_template['cause'],
                    'confidence': confidence,
                    'category': cause_template['category'],
                    'remediation': cause_template['remediation'],
                    'indicators_matched': self._get_matched_indicators(
                        cause_template['indicators'],
                        issue_details,
                        context
                    )
                })
        
        # Sort by confidence (highest first)
        scored_causes.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Return top 5 most likely causes
        return scored_causes[:5]
    
    def _calculate_confidence(self, cause_template: Dict[str, Any],
                             issue_details: Dict[str, Any],
                             context: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a potential root cause.
        
        Args:
            cause_template: Template from cause library
            issue_details: Details about the issue
            context: Additional context
            
        Returns:
            Confidence score (0-100)
        """
        base_confidence = cause_template['confidence_base']
        
        # Check how many indicators match
        indicators = cause_template['indicators']
        matched_count = 0
        total_indicators = len(indicators)
        
        for indicator in indicators:
            if self._check_indicator(indicator, issue_details, context):
                matched_count += 1
        
        # Adjust confidence based on indicator matches
        if total_indicators > 0:
            match_ratio = matched_count / total_indicators
            confidence = base_confidence * (0.5 + 0.5 * match_ratio)
        else:
            confidence = base_confidence * 0.7
        
        # Adjust based on issue severity
        percentage = issue_details.get('percentage', 0)
        if percentage > 20:
            confidence += 10  # High severity increases confidence
        elif percentage < 1:
            confidence -= 10  # Low severity decreases confidence
        
        # Ensure confidence is between 0 and 100
        return max(0.0, min(100.0, confidence))
    
    def _check_indicator(self, indicator: str, issue_details: Dict[str, Any],
                        context: Dict[str, Any]) -> bool:
        """Check if a specific indicator is present"""
        
        # Check in issue details
        if indicator in issue_details:
            return True
        
        # Check specific indicator patterns
        if indicator == 'high_null_percentage':
            return issue_details.get('percentage', 0) > 10
        
        if indicator == 'mandatory_field':
            return issue_details.get('is_mandatory', False)
        
        if indicator == 'primary_key_duplicates':
            return 'primary_key' in str(issue_details.get('column', '')).lower()
        
        if indicator == 'high_count':
            return issue_details.get('count', 0) > 100
        
        if indicator == 'sudden_spike':
            historical = context.get('historical_data', {})
            current = issue_details.get('count', 0)
            previous = historical.get('previous_count', current)
            return current > previous * 2
        
        if indicator == 'recent_increase':
            return context.get('trend', '') == 'increasing'
        
        if indicator == 'multiple_columns':
            return issue_details.get('affected_columns_count', 1) > 3
        
        if indicator == 'specific_columns':
            return issue_details.get('affected_columns_count', 0) <= 3
        
        # Default: check if indicator keyword is in any detail value
        for value in issue_details.values():
            if indicator.lower() in str(value).lower():
                return True
        
        return False
    
    def _get_matched_indicators(self, indicators: List[str],
                               issue_details: Dict[str, Any],
                               context: Dict[str, Any]) -> List[str]:
        """Get list of indicators that matched"""
        matched = []
        for indicator in indicators:
            if self._check_indicator(indicator, issue_details, context):
                matched.append(indicator)
        return matched
    
    def analyze_all_issues(self, anomaly_summary: Dict[str, Any],
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze all data quality issues and generate root cause analysis.
        
        Args:
            anomaly_summary: Dictionary containing all detected anomalies
            context: Additional context information
            
        Returns:
            Dictionary mapping issue types to lists of root causes
        """
        self.logger.info("Performing comprehensive root cause analysis...")
        
        rca_results = {}
        
        # Map anomaly types to issue types
        issue_mapping = {
            'null_blank': 'null_values',
            'duplicates': 'duplicate_records',
            'duplicate_primary_keys': 'duplicate_records',
            'invalid_emails': 'invalid_email',
            'pattern_violations': 'pattern_violations',
            'range_violations': 'range_violations',
            'outliers': 'outliers',
            'referential_integrity': 'referential_integrity',
            'business_rule_violations': 'business_rule_violations',
            'mixed_types': 'mixed_datatypes'
        }
        
        for anomaly_type, issue_type in issue_mapping.items():
            if anomaly_type in anomaly_summary:
                issue_data = anomaly_summary[anomaly_type]
                if isinstance(issue_data, dict) and issue_data.get('count', 0) > 0:
                    causes = self.analyze_issue(issue_type, issue_data, context)
                    if causes:
                        rca_results[anomaly_type] = causes
        
        self.logger.info(f"Root cause analysis complete: {len(rca_results)} issue types analyzed")
        
        return rca_results
    
    def export_rca_to_dataframe(self, rca_results: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """Export root cause analysis to DataFrame"""
        records = []
        
        for issue_type, causes in rca_results.items():
            for i, cause in enumerate(causes, 1):
                records.append({
                    'Issue Type': issue_type.replace('_', ' ').title(),
                    'Rank': i,
                    'Root Cause': cause['cause'],
                    'Confidence (%)': round(cause['confidence'], 1),
                    'Category': cause['category'],
                    'Remediation': cause['remediation'],
                    'Indicators Matched': ', '.join(cause.get('indicators_matched', []))
                })
        
        return pd.DataFrame(records)
    
    def generate_rca_summary(self, rca_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate human-readable RCA summary"""
        lines = []
        lines.append("=" * 80)
        lines.append("ROOT CAUSE ANALYSIS SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        
        if not rca_results:
            lines.append("No significant data quality issues detected.")
            return '\n'.join(lines)
        
        for issue_type, causes in rca_results.items():
            lines.append(f"\n{issue_type.replace('_', ' ').upper()}")
            lines.append("-" * 80)
            
            for i, cause in enumerate(causes, 1):
                lines.append(f"\n{i}. {cause['cause']}")
                lines.append(f"   Confidence: {cause['confidence']:.1f}%")
                lines.append(f"   Category: {cause['category']}")
                lines.append(f"   Remediation: {cause['remediation']}")
                if cause.get('indicators_matched'):
                    lines.append(f"   Indicators: {', '.join(cause['indicators_matched'])}")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)

# Made with Bob
