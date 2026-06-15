"""
Enterprise Data Quality Engine
==============================

A comprehensive, production-ready data quality framework with:
- Advanced data profiling (15+ metrics per column)
- Multi-dimensional quality scoring
- Root cause analysis
- AI-powered recommendations
- ETL reconciliation
- Historical trend analysis
- Alert management
- Metadata cataloging

Author: Bob (Enterprise DQ Team)
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "Bob"

from .profiler_advanced import AdvancedDataProfiler
from .scorer_multidimensional import MultiDimensionalScorer
from .root_cause_analyzer import RootCauseAnalyzer
from .recommender_ai import AIRecommendationEngine
from .reconciler import ETLReconciler
from .trend_analyzer import TrendAnalyzer
from .alert_manager import AlertManager
from .metadata_catalog import MetadataCatalog
from .report_generator import EnhancedReportGenerator

__all__ = [
    'AdvancedDataProfiler',
    'MultiDimensionalScorer',
    'RootCauseAnalyzer',
    'AIRecommendationEngine',
    'ETLReconciler',
    'TrendAnalyzer',
    'AlertManager',
    'MetadataCatalog',
    'EnhancedReportGenerator'
]

# Made with Bob
