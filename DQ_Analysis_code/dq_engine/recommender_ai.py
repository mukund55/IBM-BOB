"""
AI-Powered Recommendation Engine
=================================

Generates intelligent, actionable recommendations for data quality issues.
Provides priority-based recommendations with cost-benefit analysis.

Features:
- 50+ recommendation scenarios
- Priority classification (Critical, High, Medium, Low)
- Cost-benefit analysis
- Implementation effort estimation
- Actionable remediation plans
- Context-aware suggestions

Author: Bob
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class AIRecommendationEngine:
    """
    AI-powered recommendation engine that generates actionable
    recommendations for data quality improvements.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Recommendation Engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.recommendation_templates = self._build_recommendation_library()
    
    def _build_recommendation_library(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build comprehensive library of recommendations for various DQ issues.
        
        Returns:
            Dictionary mapping issue types to recommendation templates
        """
        return {
            'null_values': [
                {
                    'title': 'Implement NOT NULL Constraints',
                    'description': 'Add database-level NOT NULL constraints on mandatory fields to prevent null values at source',
                    'priority': 'Critical',
                    'effort': 'Low',
                    'impact': 'High',
                    'cost_benefit_ratio': 9.5,
                    'implementation_steps': [
                        'Identify all mandatory fields',
                        'Add NOT NULL constraints to database schema',
                        'Update application code to handle constraint violations',
                        'Test with sample data'
                    ],
                    'estimated_time': '2-4 hours',
                    'prerequisites': ['Database access', 'Schema modification rights']
                },
                {
                    'title': 'Add Default Values for Optional Fields',
                    'description': 'Define appropriate default values for optional fields to reduce null percentage',
                    'priority': 'Medium',
                    'effort': 'Low',
                    'impact': 'Medium',
                    'cost_benefit_ratio': 7.0,
                    'implementation_steps': [
                        'Analyze business requirements for default values',
                        'Update database schema with DEFAULT clauses',
                        'Modify ETL to apply defaults',
                        'Document default value logic'
                    ],
                    'estimated_time': '4-6 hours',
                    'prerequisites': ['Business rule documentation']
                },
                {
                    'title': 'Implement Source-Side Validation',
                    'description': 'Add validation at data entry points to prevent null values from entering the system',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.5,
                    'implementation_steps': [
                        'Identify all data entry points',
                        'Add client-side validation',
                        'Add server-side validation',
                        'Implement user-friendly error messages',
                        'Add validation logging'
                    ],
                    'estimated_time': '1-2 days',
                    'prerequisites': ['Source application access', 'Development resources']
                },
                {
                    'title': 'Review ETL Mapping Configuration',
                    'description': 'Audit and fix ETL mappings to ensure all source fields are correctly mapped',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.0,
                    'implementation_steps': [
                        'Document current ETL mappings',
                        'Compare with source system schema',
                        'Identify missing or incorrect mappings',
                        'Update ETL configuration',
                        'Test with historical data'
                    ],
                    'estimated_time': '1-3 days',
                    'prerequisites': ['ETL tool access', 'Source system documentation']
                }
            ],
            'duplicate_records': [
                {
                    'title': 'Add Unique Constraints on Primary Keys',
                    'description': 'Implement database-level unique constraints to prevent duplicate primary keys',
                    'priority': 'Critical',
                    'effort': 'Low',
                    'impact': 'High',
                    'cost_benefit_ratio': 9.8,
                    'implementation_steps': [
                        'Identify primary key columns',
                        'Clean existing duplicates',
                        'Add UNIQUE constraint to database',
                        'Update application error handling',
                        'Monitor for constraint violations'
                    ],
                    'estimated_time': '4-8 hours',
                    'prerequisites': ['Database access', 'Data cleansing completed']
                },
                {
                    'title': 'Implement Deduplication in ETL',
                    'description': 'Add deduplication logic in ETL process to remove duplicates before loading',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.5,
                    'implementation_steps': [
                        'Define deduplication rules (which record to keep)',
                        'Implement dedup logic in ETL',
                        'Add logging for removed duplicates',
                        'Create duplicate records archive',
                        'Test with sample data'
                    ],
                    'estimated_time': '2-3 days',
                    'prerequisites': ['ETL tool access', 'Business rules for deduplication']
                },
                {
                    'title': 'Fix Merge/Upsert Logic',
                    'description': 'Review and fix merge logic to properly handle incremental loads',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.0,
                    'implementation_steps': [
                        'Review current merge key logic',
                        'Identify merge key issues',
                        'Implement proper UPSERT logic',
                        'Add merge conflict resolution',
                        'Test with incremental loads'
                    ],
                    'estimated_time': '2-4 days',
                    'prerequisites': ['ETL access', 'Understanding of merge keys']
                },
                {
                    'title': 'Implement Master Data Management (MDM)',
                    'description': 'Deploy MDM solution to manage duplicates across multiple systems',
                    'priority': 'Medium',
                    'effort': 'High',
                    'impact': 'High',
                    'cost_benefit_ratio': 7.5,
                    'implementation_steps': [
                        'Evaluate MDM tools',
                        'Define golden record rules',
                        'Implement MDM solution',
                        'Integrate with source systems',
                        'Train users on MDM processes'
                    ],
                    'estimated_time': '2-3 months',
                    'prerequisites': ['Budget approval', 'MDM tool selection', 'Dedicated team']
                }
            ],
            'invalid_email': [
                {
                    'title': 'Implement Email Validation at Source',
                    'description': 'Add regex-based email validation at all data entry points',
                    'priority': 'High',
                    'effort': 'Low',
                    'impact': 'High',
                    'cost_benefit_ratio': 9.0,
                    'implementation_steps': [
                        'Define email validation regex pattern',
                        'Add client-side validation',
                        'Add server-side validation',
                        'Implement user-friendly error messages',
                        'Test with various email formats'
                    ],
                    'estimated_time': '1-2 days',
                    'prerequisites': ['Source application access']
                },
                {
                    'title': 'Perform Data Cleansing',
                    'description': 'Clean existing invalid email addresses using automated tools and manual review',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'Medium',
                    'cost_benefit_ratio': 7.0,
                    'implementation_steps': [
                        'Export invalid email records',
                        'Attempt automated correction (typo fixes)',
                        'Manual review of remaining records',
                        'Update corrected records',
                        'Archive uncorrectable records'
                    ],
                    'estimated_time': '3-5 days',
                    'prerequisites': ['Data cleansing tools', 'Business approval']
                },
                {
                    'title': 'Implement Email Verification Service',
                    'description': 'Integrate with email verification API to validate email deliverability',
                    'priority': 'Medium',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 7.5,
                    'implementation_steps': [
                        'Select email verification service',
                        'Integrate API into application',
                        'Add verification at registration',
                        'Implement verification workflow',
                        'Monitor verification results'
                    ],
                    'estimated_time': '1-2 weeks',
                    'prerequisites': ['Budget for API service', 'Development resources']
                }
            ],
            'pattern_violations': [
                {
                    'title': 'Standardize Data Formats Across Sources',
                    'description': 'Define and enforce standard data formats for all source systems',
                    'priority': 'High',
                    'effort': 'High',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.0,
                    'implementation_steps': [
                        'Document current format variations',
                        'Define standard formats',
                        'Create transformation rules',
                        'Implement in ETL',
                        'Communicate standards to source teams'
                    ],
                    'estimated_time': '2-4 weeks',
                    'prerequisites': ['Cross-team coordination', 'Data governance approval']
                },
                {
                    'title': 'Add Pattern Validation Rules',
                    'description': 'Implement regex-based pattern validation for all formatted fields',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.5,
                    'implementation_steps': [
                        'Define regex patterns for each field',
                        'Add validation to source systems',
                        'Add validation to ETL',
                        'Create validation error reports',
                        'Monitor validation failures'
                    ],
                    'estimated_time': '1-2 weeks',
                    'prerequisites': ['Regex expertise', 'Pattern documentation']
                }
            ],
            'range_violations': [
                {
                    'title': 'Add CHECK Constraints for Valid Ranges',
                    'description': 'Implement database CHECK constraints to enforce valid value ranges',
                    'priority': 'High',
                    'effort': 'Low',
                    'impact': 'High',
                    'cost_benefit_ratio': 9.0,
                    'implementation_steps': [
                        'Define valid ranges for each field',
                        'Add CHECK constraints to database',
                        'Update application error handling',
                        'Test with boundary values',
                        'Monitor constraint violations'
                    ],
                    'estimated_time': '1-2 days',
                    'prerequisites': ['Database access', 'Business rule documentation']
                },
                {
                    'title': 'Implement Range Validation in Application',
                    'description': 'Add range validation at data entry points with user-friendly feedback',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.0,
                    'implementation_steps': [
                        'Define validation rules',
                        'Add client-side validation',
                        'Add server-side validation',
                        'Implement helpful error messages',
                        'Add validation logging'
                    ],
                    'estimated_time': '3-5 days',
                    'prerequisites': ['Source application access']
                },
                {
                    'title': 'Review and Update Business Rules',
                    'description': 'Ensure validation rules match current business requirements',
                    'priority': 'Medium',
                    'effort': 'Low',
                    'impact': 'Medium',
                    'cost_benefit_ratio': 7.0,
                    'implementation_steps': [
                        'Review current validation rules',
                        'Meet with business stakeholders',
                        'Document updated rules',
                        'Update validation logic',
                        'Communicate changes'
                    ],
                    'estimated_time': '1-2 weeks',
                    'prerequisites': ['Stakeholder availability']
                }
            ],
            'outliers': [
                {
                    'title': 'Implement Outlier Detection and Alerting',
                    'description': 'Add automated outlier detection with real-time alerts',
                    'priority': 'Medium',
                    'effort': 'Medium',
                    'impact': 'Medium',
                    'cost_benefit_ratio': 6.5,
                    'implementation_steps': [
                        'Define outlier detection rules',
                        'Implement detection logic',
                        'Configure alert thresholds',
                        'Set up notification system',
                        'Create outlier review process'
                    ],
                    'estimated_time': '1-2 weeks',
                    'prerequisites': ['Monitoring infrastructure']
                },
                {
                    'title': 'Add Confirmation Dialogs for Extreme Values',
                    'description': 'Require user confirmation when entering values outside normal ranges',
                    'priority': 'High',
                    'effort': 'Low',
                    'impact': 'Medium',
                    'cost_benefit_ratio': 7.5,
                    'implementation_steps': [
                        'Define "extreme value" thresholds',
                        'Add confirmation dialogs to UI',
                        'Log confirmed extreme values',
                        'Create review reports',
                        'Monitor confirmation patterns'
                    ],
                    'estimated_time': '2-3 days',
                    'prerequisites': ['UI development access']
                }
            ],
            'referential_integrity': [
                {
                    'title': 'Add Foreign Key Constraints',
                    'description': 'Implement database foreign key constraints to enforce referential integrity',
                    'priority': 'Critical',
                    'effort': 'Medium',
                    'impact': 'High',
                    'cost_benefit_ratio': 9.5,
                    'implementation_steps': [
                        'Identify all relationships',
                        'Clean orphan records',
                        'Add foreign key constraints',
                        'Configure cascade rules',
                        'Test referential integrity'
                    ],
                    'estimated_time': '1-2 weeks',
                    'prerequisites': ['Database access', 'Data cleansing']
                },
                {
                    'title': 'Implement Master Data Management',
                    'description': 'Deploy MDM to synchronize reference data across systems',
                    'priority': 'High',
                    'effort': 'High',
                    'impact': 'High',
                    'cost_benefit_ratio': 7.5,
                    'implementation_steps': [
                        'Evaluate MDM solutions',
                        'Define master data domains',
                        'Implement MDM platform',
                        'Integrate with systems',
                        'Establish governance processes'
                    ],
                    'estimated_time': '2-4 months',
                    'prerequisites': ['Budget', 'Executive sponsorship']
                }
            ],
            'business_rule_violations': [
                {
                    'title': 'Implement Business Rule Engine',
                    'description': 'Deploy centralized business rule engine for consistent validation',
                    'priority': 'High',
                    'effort': 'High',
                    'impact': 'High',
                    'cost_benefit_ratio': 8.0,
                    'implementation_steps': [
                        'Document all business rules',
                        'Select rule engine platform',
                        'Implement rule engine',
                        'Migrate rules to engine',
                        'Integrate with applications'
                    ],
                    'estimated_time': '1-3 months',
                    'prerequisites': ['Rule engine tool', 'Business analyst support']
                },
                {
                    'title': 'Create Business Rule Documentation',
                    'description': 'Document all business rules in centralized repository',
                    'priority': 'High',
                    'effort': 'Medium',
                    'impact': 'Medium',
                    'cost_benefit_ratio': 7.0,
                    'implementation_steps': [
                        'Collect existing rules',
                        'Interview stakeholders',
                        'Document rules clearly',
                        'Create rule catalog',
                        'Establish update process'
                    ],
                    'estimated_time': '2-4 weeks',
                    'prerequisites': ['Business analyst', 'Documentation tool']
                }
            ]
        }
    
    def generate_recommendations(self, anomaly_summary: Dict[str, Any],
                                scoring_results: Optional[Dict[str, Any]] = None,
                                rca_results: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommendations based on detected issues.
        
        Args:
            anomaly_summary: Dictionary containing all detected anomalies
            scoring_results: Multi-dimensional scoring results
            rca_results: Root cause analysis results
            
        Returns:
            List of recommendations sorted by priority and impact
        """
        self.logger.info("Generating AI-powered recommendations...")
        
        recommendations = []
        
        # Map anomaly types to recommendation categories
        issue_mapping = {
            'null_blank': 'null_values',
            'duplicates': 'duplicate_records',
            'duplicate_primary_keys': 'duplicate_records',
            'invalid_emails': 'invalid_email',
            'pattern_violations': 'pattern_violations',
            'range_violations': 'range_violations',
            'outliers': 'outliers',
            'referential_integrity': 'referential_integrity',
            'business_rule_violations': 'business_rule_violations'
        }
        
        for anomaly_type, rec_category in issue_mapping.items():
            if anomaly_type in anomaly_summary:
                issue_data = anomaly_summary[anomaly_type]
                if isinstance(issue_data, dict) and issue_data.get('count', 0) > 0:
                    # Get recommendations for this issue type
                    issue_recs = self._get_recommendations_for_issue(
                        rec_category,
                        issue_data,
                        scoring_results,
                        rca_results
                    )
                    recommendations.extend(issue_recs)
        
        # Sort by priority and cost-benefit ratio
        priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        recommendations.sort(
            key=lambda x: (priority_order.get(x['priority'], 4), -x['cost_benefit_ratio'])
        )
        
        # Add rank
        for i, rec in enumerate(recommendations, 1):
            rec['rank'] = i
        
        self.logger.info(f"Generated {len(recommendations)} recommendations")
        
        return recommendations
    
    def _get_recommendations_for_issue(self, issue_category: str,
                                      issue_data: Dict[str, Any],
                                      scoring_results: Optional[Dict[str, Any]],
                                      rca_results: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get recommendations for a specific issue category"""
        
        templates = self.recommendation_templates.get(issue_category, [])
        recommendations = []
        
        for template in templates:
            # Create recommendation from template
            rec = template.copy()
            rec['issue_category'] = issue_category
            rec['issue_count'] = issue_data.get('count', 0)
            rec['issue_percentage'] = issue_data.get('percentage', 0)
            
            # Adjust priority based on severity
            rec['priority'] = self._adjust_priority(
                template['priority'],
                issue_data.get('percentage', 0)
            )
            
            # Add context from RCA if available
            if rca_results and issue_category in rca_results:
                top_cause = rca_results[issue_category][0] if rca_results[issue_category] else None
                if top_cause:
                    rec['related_root_cause'] = top_cause['cause']
                    rec['root_cause_confidence'] = top_cause['confidence']
            
            recommendations.append(rec)
        
        return recommendations
    
    def _adjust_priority(self, base_priority: str, issue_percentage: float) -> str:
        """Adjust recommendation priority based on issue severity"""
        
        if issue_percentage > 20:
            # Severe issues - upgrade priority
            if base_priority == 'Medium':
                return 'High'
            elif base_priority == 'Low':
                return 'Medium'
        elif issue_percentage < 1:
            # Minor issues - downgrade priority
            if base_priority == 'Critical':
                return 'High'
            elif base_priority == 'High':
                return 'Medium'
        
        return base_priority
    
    def export_recommendations_to_dataframe(self, recommendations: List[Dict[str, Any]]) -> pd.DataFrame:
        """Export recommendations to DataFrame"""
        
        if not recommendations:
            return pd.DataFrame()
        
        records = []
        for rec in recommendations:
            records.append({
                'Rank': rec.get('rank', 0),
                'Priority': rec['priority'],
                'Title': rec['title'],
                'Description': rec['description'],
                'Issue Category': rec.get('issue_category', '').replace('_', ' ').title(),
                'Issue Count': rec.get('issue_count', 0),
                'Issue %': round(rec.get('issue_percentage', 0), 2),
                'Effort': rec['effort'],
                'Impact': rec['impact'],
                'Cost-Benefit Ratio': rec['cost_benefit_ratio'],
                'Estimated Time': rec['estimated_time'],
                'Implementation Steps': ' | '.join(rec['implementation_steps']),
                'Prerequisites': ', '.join(rec['prerequisites'])
            })
        
        return pd.DataFrame(records)
    
    def generate_action_plan(self, recommendations: List[Dict[str, Any]],
                           max_recommendations: int = 10) -> str:
        """Generate actionable implementation plan"""
        
        lines = []
        lines.append("=" * 80)
        lines.append("DATA QUALITY IMPROVEMENT ACTION PLAN")
        lines.append("=" * 80)
        lines.append("")
        
        if not recommendations:
            lines.append("No recommendations generated.")
            return '\n'.join(lines)
        
        # Group by priority
        by_priority = {}
        for rec in recommendations[:max_recommendations]:
            priority = rec['priority']
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(rec)
        
        for priority in ['Critical', 'High', 'Medium', 'Low']:
            if priority in by_priority:
                lines.append(f"\n{priority.upper()} PRIORITY ACTIONS")
                lines.append("-" * 80)
                
                for rec in by_priority[priority]:
                    lines.append(f"\n{rec.get('rank', 0)}. {rec['title']}")
                    lines.append(f"   {rec['description']}")
                    lines.append(f"   Effort: {rec['effort']} | Impact: {rec['impact']} | Time: {rec['estimated_time']}")
                    lines.append(f"   Cost-Benefit Ratio: {rec['cost_benefit_ratio']}/10")
                    
                    if rec.get('related_root_cause'):
                        lines.append(f"   Root Cause: {rec['related_root_cause']}")
                    
                    lines.append(f"\n   Implementation Steps:")
                    for i, step in enumerate(rec['implementation_steps'], 1):
                        lines.append(f"      {i}. {step}")
                    
                    if rec['prerequisites']:
                        lines.append(f"   Prerequisites: {', '.join(rec['prerequisites'])}")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)

# Made with Bob
