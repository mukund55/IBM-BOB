"""
Historical Trend Analysis Module
=================================

Tracks and analyzes data quality trends over time.

Features:
- Historical DQ score tracking
- Trend detection (improving, degrading, stable)
- Anomaly detection on trends
- Trend visualization data
- Predictive insights

Author: Bob
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class TrendAnalyzer:
    """
    Trend analysis engine that tracks data quality metrics over time
    and identifies patterns and anomalies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Trend Analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.history_file = self.config.get('history_file', 'dq_history.json')
        self.history_dir = Path(self.config.get('history_dir', 'dq_history'))
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def store_execution(self, execution_data: Dict[str, Any]) -> None:
        """
        Store current execution results for historical tracking.
        
        Args:
            execution_data: Dictionary containing execution results
        """
        self.logger.info("Storing execution data for trend analysis...")
        
        # Add timestamp
        execution_data['timestamp'] = datetime.now().isoformat()
        
        # Load existing history
        history = self._load_history()
        
        # Append new execution
        history.append(execution_data)
        
        # Save updated history
        self._save_history(history)
        
        self.logger.info(f"Execution data stored. Total executions: {len(history)}")
    
    def analyze_trends(self, metric_name: str = 'overall_score',
                      lookback_periods: int = 10) -> Dict[str, Any]:
        """
        Analyze trends for a specific metric.
        
        Args:
            metric_name: Name of metric to analyze
            lookback_periods: Number of historical periods to analyze
            
        Returns:
            Dictionary containing trend analysis results
        """
        self.logger.info(f"Analyzing trends for metric: {metric_name}")
        
        history = self._load_history()
        
        if len(history) < 2:
            return {
                'metric': metric_name,
                'trend': 'insufficient_data',
                'message': 'Need at least 2 historical executions for trend analysis'
            }
        
        # Extract metric values
        recent_history = history[-lookback_periods:]
        values = []
        timestamps = []
        
        for execution in recent_history:
            value = self._extract_metric_value(execution, metric_name)
            if value is not None:
                values.append(value)
                timestamps.append(execution.get('timestamp', ''))
        
        if len(values) < 2:
            return {
                'metric': metric_name,
                'trend': 'insufficient_data',
                'message': f'Metric {metric_name} not found in history'
            }
        
        # Calculate trend
        trend_direction = self._calculate_trend_direction(values)
        trend_strength = self._calculate_trend_strength(values)
        volatility = self._calculate_volatility(values)
        
        # Detect anomalies
        anomalies = self._detect_trend_anomalies(values, timestamps)
        
        result = {
            'metric': metric_name,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'current_value': values[-1],
            'previous_value': values[-2],
            'change': values[-1] - values[-2],
            'change_percentage': ((values[-1] - values[-2]) / values[-2] * 100) if values[-2] != 0 else 0,
            'min_value': min(values),
            'max_value': max(values),
            'avg_value': sum(values) / len(values),
            'data_points': len(values),
            'anomalies': anomalies,
            'timestamps': timestamps,
            'values': values
        }
        
        self.logger.info(f"Trend analysis complete: {trend_direction} ({trend_strength})")
        
        return result
    
    def analyze_all_metrics(self, lookback_periods: int = 10) -> Dict[str, Dict[str, Any]]:
        """
        Analyze trends for all available metrics.
        
        Args:
            lookback_periods: Number of historical periods to analyze
            
        Returns:
            Dictionary mapping metric names to trend analysis results
        """
        self.logger.info("Analyzing trends for all metrics...")
        
        # Key metrics to track
        metrics = [
            'overall_score',
            'completeness_score',
            'validity_score',
            'consistency_score',
            'accuracy_score',
            'uniqueness_score',
            'null_percentage',
            'duplicate_percentage',
            'bad_record_percentage'
        ]
        
        results = {}
        for metric in metrics:
            try:
                results[metric] = self.analyze_trends(metric, lookback_periods)
            except Exception as e:
                self.logger.error(f"Error analyzing trend for {metric}: {str(e)}")
                results[metric] = {
                    'metric': metric,
                    'trend': 'error',
                    'message': str(e)
                }
        
        return results
    
    def generate_trend_report(self, trend_results: Dict[str, Dict[str, Any]]) -> str:
        """Generate human-readable trend report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DATA QUALITY TREND ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        for metric, analysis in trend_results.items():
            if analysis.get('trend') in ['insufficient_data', 'error']:
                continue
            
            lines.append(f"\n{metric.replace('_', ' ').upper()}")
            lines.append("-" * 80)
            lines.append(f"Current Value: {analysis['current_value']:.2f}")
            lines.append(f"Previous Value: {analysis['previous_value']:.2f}")
            lines.append(f"Change: {analysis['change']:+.2f} ({analysis['change_percentage']:+.2f}%)")
            lines.append(f"Trend: {analysis['trend_direction']} ({analysis['trend_strength']})")
            lines.append(f"Volatility: {analysis['volatility']}")
            lines.append(f"Range: {analysis['min_value']:.2f} - {analysis['max_value']:.2f}")
            lines.append(f"Average: {analysis['avg_value']:.2f}")
            
            if analysis['anomalies']:
                lines.append(f"Anomalies Detected: {len(analysis['anomalies'])}")
                for anomaly in analysis['anomalies']:
                    lines.append(f"  - {anomaly['timestamp']}: {anomaly['value']:.2f} ({anomaly['type']})")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)
    
    def export_trends_to_dataframe(self, trend_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Export trend analysis to DataFrame"""
        records = []
        
        for metric, analysis in trend_results.items():
            if analysis.get('trend') in ['insufficient_data', 'error']:
                continue
            
            records.append({
                'Metric': metric.replace('_', ' ').title(),
                'Current Value': round(analysis['current_value'], 2),
                'Previous Value': round(analysis['previous_value'], 2),
                'Change': round(analysis['change'], 2),
                'Change %': round(analysis['change_percentage'], 2),
                'Trend Direction': analysis['trend_direction'],
                'Trend Strength': analysis['trend_strength'],
                'Volatility': analysis['volatility'],
                'Min': round(analysis['min_value'], 2),
                'Max': round(analysis['max_value'], 2),
                'Avg': round(analysis['avg_value'], 2),
                'Anomalies': len(analysis['anomalies'])
            })
        
        return pd.DataFrame(records)
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load execution history from file"""
        history_path = self.history_dir / self.history_file
        
        if not history_path.exists():
            return []
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading history: {str(e)}")
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save execution history to file"""
        history_path = self.history_dir / self.history_file
        
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving history: {str(e)}")
    
    def _extract_metric_value(self, execution: Dict[str, Any], metric_name: str) -> Optional[float]:
        """Extract metric value from execution data"""
        # Try direct access
        if metric_name in execution:
            return float(execution[metric_name])
        
        # Try nested access
        if 'scoring_results' in execution:
            scoring = execution['scoring_results']
            if metric_name in scoring:
                return float(scoring[metric_name])
            
            # Try dimension scores
            if 'dimensions' in scoring:
                for dim_name, dim_data in scoring['dimensions'].items():
                    if metric_name == f"{dim_name}_score" and 'score' in dim_data:
                        return float(dim_data['score'])
        
        # Try anomaly summary
        if 'anomaly_summary' in execution:
            for issue_type, issue_data in execution['anomaly_summary'].items():
                if isinstance(issue_data, dict):
                    if metric_name == f"{issue_type}_percentage" and 'percentage' in issue_data:
                        return float(issue_data['percentage'])
        
        return None
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        if slope > 0.5:
            return 'improving'
        elif slope < -0.5:
            return 'degrading'
        else:
            return 'stable'
    
    def _calculate_trend_strength(self, values: List[float]) -> str:
        """Calculate trend strength"""
        if len(values) < 2:
            return 'weak'
        
        # Calculate coefficient of variation
        mean = sum(values) / len(values)
        if mean == 0:
            return 'weak'
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        cv = (std_dev / abs(mean)) * 100
        
        if cv < 5:
            return 'strong'
        elif cv < 15:
            return 'moderate'
        else:
            return 'weak'
    
    def _calculate_volatility(self, values: List[float]) -> str:
        """Calculate volatility"""
        if len(values) < 2:
            return 'low'
        
        # Calculate standard deviation
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Normalize by mean
        if mean != 0:
            normalized_std = (std_dev / abs(mean)) * 100
        else:
            normalized_std = std_dev
        
        if normalized_std < 5:
            return 'low'
        elif normalized_std < 15:
            return 'medium'
        else:
            return 'high'
    
    def _detect_trend_anomalies(self, values: List[float],
                                timestamps: List[str]) -> List[Dict[str, Any]]:
        """Detect anomalies in trend data"""
        if len(values) < 3:
            return []
        
        anomalies = []
        
        # Calculate mean and standard deviation
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Detect outliers (values beyond 2 standard deviations)
        for i, value in enumerate(values):
            if abs(value - mean) > 2 * std_dev:
                anomalies.append({
                    'index': i,
                    'timestamp': timestamps[i] if i < len(timestamps) else '',
                    'value': value,
                    'type': 'outlier',
                    'deviation': abs(value - mean) / std_dev if std_dev > 0 else 0
                })
        
        # Detect sudden changes
        for i in range(1, len(values)):
            change = abs(values[i] - values[i-1])
            if change > std_dev * 1.5:
                anomalies.append({
                    'index': i,
                    'timestamp': timestamps[i] if i < len(timestamps) else '',
                    'value': values[i],
                    'type': 'sudden_change',
                    'change': values[i] - values[i-1]
                })
        
        return anomalies

# Made with Bob
