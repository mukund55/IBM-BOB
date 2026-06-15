"""
Alert Management Module
=======================

Manages data quality alerts based on thresholds and severity levels.

Features:
- Threshold-based alerting
- Severity classification (Critical, High, Medium, Low)
- Alert history tracking
- Email notification support (configurable)
- Alert dashboard data generation

Author: Bob
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class AlertManager:
    """
    Alert management engine that generates and tracks data quality alerts.
    """
    
    # Default alert thresholds
    DEFAULT_THRESHOLDS = {
        'overall_score': {'critical': 60, 'high': 75, 'medium': 85},
        'null_percentage': {'critical': 20, 'high': 10, 'medium': 5},
        'duplicate_percentage': {'critical': 10, 'high': 5, 'medium': 2},
        'invalid_email_percentage': {'critical': 15, 'high': 8, 'medium': 3},
        'pattern_violation_percentage': {'critical': 15, 'high': 8, 'medium': 3}
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Alert Manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Get thresholds from config or use defaults
        self.thresholds = self.config.get('alert_thresholds', self.DEFAULT_THRESHOLDS)
        
        # Alert history
        self.alert_history_file = self.config.get('alert_history_file', 'alert_history.json')
        self.alert_dir = Path(self.config.get('alert_dir', 'dq_alerts'))
        self.alert_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate_alerts(self, metrics: Dict[str, Any],
                       anomaly_summary: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evaluate metrics against thresholds and generate alerts.
        
        Args:
            metrics: Dictionary containing DQ metrics
            anomaly_summary: Optional anomaly summary data
            
        Returns:
            List of generated alerts
        """
        self.logger.info("Evaluating data quality alerts...")
        
        alerts = []
        
        # Check overall score
        if 'overall_score' in metrics:
            alert = self._check_threshold(
                'overall_score',
                metrics['overall_score'],
                'Overall DQ Score',
                lower_is_worse=True
            )
            if alert:
                alerts.append(alert)
        
        # Check dimension scores
        if 'dimensions' in metrics:
            for dim_name, dim_data in metrics['dimensions'].items():
                if 'score' in dim_data:
                    alert = self._check_threshold(
                        f'{dim_name}_score',
                        dim_data['score'],
                        f'{dim_name.title()} Score',
                        lower_is_worse=True
                    )
                    if alert:
                        alerts.append(alert)
        
        # Check anomaly percentages
        if anomaly_summary:
            for issue_type, issue_data in anomaly_summary.items():
                if isinstance(issue_data, dict) and 'percentage' in issue_data:
                    percentage = issue_data['percentage']
                    
                    # Map issue types to threshold keys
                    threshold_key = f'{issue_type}_percentage'
                    
                    alert = self._check_threshold(
                        threshold_key,
                        percentage,
                        f'{issue_type.replace("_", " ").title()} Percentage',
                        lower_is_worse=False
                    )
                    if alert:
                        alert['issue_count'] = issue_data.get('count', 0)
                        alerts.append(alert)
        
        # Store alerts in history
        if alerts:
            self._store_alerts(alerts)
        
        self.logger.info(f"Generated {len(alerts)} alerts")
        
        return alerts
    
    def _check_threshold(self, metric_key: str, value: float,
                        metric_display_name: str,
                        lower_is_worse: bool = True) -> Optional[Dict[str, Any]]:
        """
        Check if a metric value exceeds thresholds.
        
        Args:
            metric_key: Key to look up thresholds
            value: Metric value
            metric_display_name: Display name for the metric
            lower_is_worse: True if lower values are worse (e.g., scores)
            
        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        # Get thresholds for this metric
        metric_thresholds = self.thresholds.get(metric_key)
        
        if not metric_thresholds:
            # Try generic thresholds
            if lower_is_worse:
                metric_thresholds = self.thresholds.get('overall_score')
            else:
                metric_thresholds = self.thresholds.get('null_percentage')
        
        if not metric_thresholds:
            return None
        
        # Determine severity
        severity = None
        threshold_value = None
        
        if lower_is_worse:
            # Lower values are worse (e.g., scores)
            if value < metric_thresholds.get('critical', 0):
                severity = 'Critical'
                threshold_value = metric_thresholds['critical']
            elif value < metric_thresholds.get('high', 0):
                severity = 'High'
                threshold_value = metric_thresholds['high']
            elif value < metric_thresholds.get('medium', 0):
                severity = 'Medium'
                threshold_value = metric_thresholds['medium']
        else:
            # Higher values are worse (e.g., error percentages)
            if value > metric_thresholds.get('critical', 100):
                severity = 'Critical'
                threshold_value = metric_thresholds['critical']
            elif value > metric_thresholds.get('high', 100):
                severity = 'High'
                threshold_value = metric_thresholds['high']
            elif value > metric_thresholds.get('medium', 100):
                severity = 'Medium'
                threshold_value = metric_thresholds['medium']
        
        if severity:
            return {
                'timestamp': datetime.now().isoformat(),
                'metric': metric_display_name,
                'metric_key': metric_key,
                'value': round(value, 2),
                'threshold': threshold_value,
                'severity': severity,
                'message': self._generate_alert_message(
                    metric_display_name, value, threshold_value, severity, lower_is_worse
                )
            }
        
        return None
    
    def _generate_alert_message(self, metric_name: str, value: float,
                               threshold: float, severity: str,
                               lower_is_worse: bool) -> str:
        """Generate human-readable alert message"""
        if lower_is_worse:
            return (f"{severity} Alert: {metric_name} is {value:.2f}, "
                   f"below threshold of {threshold:.2f}")
        else:
            return (f"{severity} Alert: {metric_name} is {value:.2f}%, "
                   f"exceeding threshold of {threshold:.2f}%")
    
    def _store_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Store alerts in history file"""
        history_path = self.alert_dir / self.alert_history_file
        
        # Load existing history
        history = []
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading alert history: {str(e)}")
        
        # Append new alerts
        history.extend(alerts)
        
        # Keep only last 1000 alerts
        if len(history) > 1000:
            history = history[-1000:]
        
        # Save updated history
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving alert history: {str(e)}")
    
    def get_alert_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert summary statistics"""
        if not alerts:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0
            }
        
        by_severity = {}
        for alert in alerts:
            severity = alert['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_alerts': len(alerts),
            'by_severity': by_severity,
            'critical_count': by_severity.get('Critical', 0),
            'high_count': by_severity.get('High', 0),
            'medium_count': by_severity.get('Medium', 0),
            'low_count': by_severity.get('Low', 0),
            'most_severe': alerts[0]['severity'] if alerts else 'None'
        }
    
    def export_alerts_to_dataframe(self, alerts: List[Dict[str, Any]]) -> pd.DataFrame:
        """Export alerts to DataFrame"""
        if not alerts:
            return pd.DataFrame()
        
        records = []
        for alert in alerts:
            records.append({
                'Timestamp': alert['timestamp'],
                'Severity': alert['severity'],
                'Metric': alert['metric'],
                'Value': alert['value'],
                'Threshold': alert['threshold'],
                'Message': alert['message'],
                'Issue Count': alert.get('issue_count', '')
            })
        
        return pd.DataFrame(records)
    
    def generate_alert_report(self, alerts: List[Dict[str, Any]]) -> str:
        """Generate human-readable alert report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DATA QUALITY ALERTS")
        lines.append("=" * 80)
        lines.append("")
        
        if not alerts:
            lines.append("No alerts generated. All metrics within acceptable thresholds.")
            return '\n'.join(lines)
        
        summary = self.get_alert_summary(alerts)
        lines.append(f"Total Alerts: {summary['total_alerts']}")
        lines.append(f"  Critical: {summary['critical_count']}")
        lines.append(f"  High: {summary['high_count']}")
        lines.append(f"  Medium: {summary['medium_count']}")
        lines.append(f"  Low: {summary['low_count']}")
        lines.append("")
        
        # Group by severity
        by_severity = {}
        for alert in alerts:
            severity = alert['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(alert)
        
        for severity in ['Critical', 'High', 'Medium', 'Low']:
            if severity in by_severity:
                lines.append(f"\n{severity.upper()} ALERTS")
                lines.append("-" * 80)
                
                for alert in by_severity[severity]:
                    lines.append(f"\n{alert['message']}")
                    if alert.get('issue_count'):
                        lines.append(f"  Affected Records: {alert['issue_count']}")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)
    
    def send_email_alerts(self, alerts: List[Dict[str, Any]],
                         recipients: List[str]) -> bool:
        """
        Send email notifications for alerts (placeholder for email integration).
        
        Args:
            alerts: List of alerts to send
            recipients: List of email addresses
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Email alert functionality called for {len(alerts)} alerts")
        self.logger.info(f"Recipients: {', '.join(recipients)}")
        
        # This is a placeholder. In production, integrate with:
        # - SMTP server
        # - SendGrid API
        # - AWS SES
        # - Other email service
        
        self.logger.warning("Email sending not implemented. Configure email service in production.")
        
        return False

# Made with Bob
