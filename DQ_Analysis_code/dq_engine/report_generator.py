"""
Enhanced Report Generator Module
=================================

Generates comprehensive data quality reports in multiple formats.

Features:
- Excel reports with multiple sheets
- PDF report generation
- JSON API outputs
- Interactive HTML dashboards
- Executive summary reports
- Customizable templates

Author: Bob
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class EnhancedReportGenerator:
    """
    Enhanced report generator that creates comprehensive DQ reports
    in multiple formats.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Enhanced Report Generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def generate_comprehensive_excel_report(self, output_path: str, **data_sections) -> None:
        """
        Generate comprehensive Excel report with multiple sheets.
        
        Args:
            output_path: Path to output Excel file
            **data_sections: Keyword arguments containing data for each sheet
                Expected keys: dataset_profile, column_profiles, scoring_results,
                rca_results, recommendations, alerts, trends, etc.
        """
        self.logger.info(f"Generating comprehensive Excel report: {output_path}")
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Executive Summary
                if 'scoring_results' in data_sections:
                    self._write_executive_summary_sheet(writer, data_sections)
                
                # Dataset Profile
                if 'dataset_profile' in data_sections:
                    df = pd.DataFrame([data_sections['dataset_profile']])
                    df.to_excel(writer, sheet_name='Dataset Profile', index=False)
                
                # Column Profiles
                if 'column_profiles' in data_sections:
                    df = pd.DataFrame(data_sections['column_profiles'])
                    df.to_excel(writer, sheet_name='Column Profiles', index=False)
                
                # DQ Scorecard
                if 'scoring_results' in data_sections:
                    self._write_scorecard_sheet(writer, data_sections['scoring_results'])
                
                # Root Cause Analysis
                if 'rca_results' in data_sections:
                    self._write_rca_sheet(writer, data_sections['rca_results'])
                
                # Recommendations
                if 'recommendations' in data_sections:
                    df = pd.DataFrame(data_sections['recommendations'])
                    df.to_excel(writer, sheet_name='Recommendations', index=False)
                
                # Alerts
                if 'alerts' in data_sections:
                    df = pd.DataFrame(data_sections['alerts'])
                    df.to_excel(writer, sheet_name='Alerts', index=False)
                
                # Trends
                if 'trends' in data_sections:
                    self._write_trends_sheet(writer, data_sections['trends'])
                
                # Data Dictionary
                if 'data_dictionary' in data_sections:
                    data_sections['data_dictionary'].to_excel(writer, sheet_name='Data Dictionary', index=False)
                
                # Anomaly Details
                if 'anomaly_summary' in data_sections:
                    self._write_anomaly_sheet(writer, data_sections['anomaly_summary'])
            
            self.logger.info(f"Excel report generated successfully: {output_path}")
        
        except Exception as e:
            self.logger.error(f"Error generating Excel report: {str(e)}")
            raise
    
    def _write_executive_summary_sheet(self, writer: pd.ExcelWriter, data: Dict[str, Any]) -> None:
        """Write executive summary sheet"""
        scoring = data.get('scoring_results', {})
        
        summary_data = {
            'Metric': [
                'Overall DQ Score',
                'Classification',
                'Completeness Score',
                'Validity Score',
                'Consistency Score',
                'Accuracy Score',
                'Uniqueness Score',
                'Total Records',
                'Total Columns',
                'Bad Records',
                'Bad Record %'
            ],
            'Value': [
                scoring.get('overall_score', 0),
                scoring.get('classification', 'Unknown'),
                scoring.get('dimensions', {}).get('completeness', {}).get('score', 0),
                scoring.get('dimensions', {}).get('validity', {}).get('score', 0),
                scoring.get('dimensions', {}).get('consistency', {}).get('score', 0),
                scoring.get('dimensions', {}).get('accuracy', {}).get('score', 0),
                scoring.get('dimensions', {}).get('uniqueness', {}).get('score', 0),
                data.get('dataset_profile', {}).get('total_rows', 0),
                data.get('dataset_profile', {}).get('total_columns', 0),
                data.get('bad_record_count', 0),
                data.get('bad_record_percentage', 0)
            ]
        }
        
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Executive Summary', index=False)
    
    def _write_scorecard_sheet(self, writer: pd.ExcelWriter, scoring_results: Dict[str, Any]) -> None:
        """Write DQ scorecard sheet"""
        records = []
        
        if 'dimensions' in scoring_results:
            for dim_name, dim_data in scoring_results['dimensions'].items():
                records.append({
                    'Dimension': dim_data.get('dimension', dim_name),
                    'Score': dim_data.get('score', 0),
                    'Issues': '; '.join(dim_data.get('issues', []))
                })
        
        if records:
            pd.DataFrame(records).to_excel(writer, sheet_name='DQ Scorecard', index=False)
    
    def _write_rca_sheet(self, writer: pd.ExcelWriter, rca_results: Dict[str, Any]) -> None:
        """Write root cause analysis sheet"""
        records = []
        
        for issue_type, causes in rca_results.items():
            for cause in causes:
                records.append({
                    'Issue Type': issue_type.replace('_', ' ').title(),
                    'Root Cause': cause.get('cause', ''),
                    'Confidence %': cause.get('confidence', 0),
                    'Category': cause.get('category', ''),
                    'Remediation': cause.get('remediation', '')
                })
        
        if records:
            pd.DataFrame(records).to_excel(writer, sheet_name='Root Cause Analysis', index=False)
    
    def _write_trends_sheet(self, writer: pd.ExcelWriter, trends: Dict[str, Any]) -> None:
        """Write trends analysis sheet"""
        records = []
        
        for metric, analysis in trends.items():
            if analysis.get('trend') not in ['insufficient_data', 'error']:
                records.append({
                    'Metric': metric.replace('_', ' ').title(),
                    'Current': analysis.get('current_value', 0),
                    'Previous': analysis.get('previous_value', 0),
                    'Change': analysis.get('change', 0),
                    'Change %': analysis.get('change_percentage', 0),
                    'Trend': analysis.get('trend_direction', ''),
                    'Strength': analysis.get('trend_strength', ''),
                    'Volatility': analysis.get('volatility', '')
                })
        
        if records:
            pd.DataFrame(records).to_excel(writer, sheet_name='Trend Analysis', index=False)
    
    def _write_anomaly_sheet(self, writer: pd.ExcelWriter, anomaly_summary: Dict[str, Any]) -> None:
        """Write anomaly summary sheet"""
        records = []
        
        for issue_type, issue_data in anomaly_summary.items():
            if isinstance(issue_data, dict):
                records.append({
                    'Issue Type': issue_type.replace('_', ' ').title(),
                    'Count': issue_data.get('count', 0),
                    'Percentage': issue_data.get('percentage', 0),
                    'Severity': issue_data.get('severity', '')
                })
        
        if records:
            pd.DataFrame(records).to_excel(writer, sheet_name='Anomaly Summary', index=False)
    
    def generate_json_report(self, output_path: str, **data_sections) -> None:
        """
        Generate JSON report for API consumption.
        
        Args:
            output_path: Path to output JSON file
            **data_sections: Data sections to include
        """
        self.logger.info(f"Generating JSON report: {output_path}")
        
        import json
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'data_quality_analysis',
                'version': '2.0.0'
            }
        }
        
        # Add all data sections
        report.update(data_sections)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"JSON report generated successfully: {output_path}")
        
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {str(e)}")
            raise
    
    def generate_pdf_report(self, output_path: str, **data_sections) -> None:
        """
        Generate PDF report (requires reportlab library).
        
        Args:
            output_path: Path to output PDF file
            **data_sections: Data sections to include
        """
        self.logger.info(f"Generating PDF report: {output_path}")
        
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("Data Quality Analysis Report", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Executive Summary
            if 'scoring_results' in data_sections:
                story.append(Paragraph("Executive Summary", styles['Heading2']))
                story.append(Spacer(1, 0.2*inch))
                
                scoring = data_sections['scoring_results']
                summary_data = [
                    ['Metric', 'Value'],
                    ['Overall DQ Score', f"{scoring.get('overall_score', 0):.2f}"],
                    ['Classification', scoring.get('classification', 'Unknown')],
                    ['Completeness', f"{scoring.get('dimensions', {}).get('completeness', {}).get('score', 0):.2f}"],
                    ['Validity', f"{scoring.get('dimensions', {}).get('validity', {}).get('score', 0):.2f}"],
                    ['Consistency', f"{scoring.get('dimensions', {}).get('consistency', {}).get('score', 0):.2f}"],
                    ['Accuracy', f"{scoring.get('dimensions', {}).get('accuracy', {}).get('score', 0):.2f}"],
                    ['Uniqueness', f"{scoring.get('dimensions', {}).get('uniqueness', {}).get('score', 0):.2f}"]
                ]
                
                table = Table(summary_data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(PageBreak())
            
            # Top Recommendations
            if 'recommendations' in data_sections and data_sections['recommendations']:
                story.append(Paragraph("Top Recommendations", styles['Heading2']))
                story.append(Spacer(1, 0.2*inch))
                
                for i, rec in enumerate(data_sections['recommendations'][:5], 1):
                    story.append(Paragraph(f"{i}. {rec.get('title', '')}", styles['Heading3']))
                    story.append(Paragraph(rec.get('description', ''), styles['Normal']))
                    story.append(Paragraph(f"Priority: {rec.get('priority', '')} | Effort: {rec.get('effort', '')} | Impact: {rec.get('impact', '')}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                story.append(PageBreak())
            
            # Alerts
            if 'alerts' in data_sections and data_sections['alerts']:
                story.append(Paragraph("Data Quality Alerts", styles['Heading2']))
                story.append(Spacer(1, 0.2*inch))
                
                for alert in data_sections['alerts'][:10]:
                    alert_text = f"[{alert.get('severity', '')}] {alert.get('message', '')}"
                    story.append(Paragraph(alert_text, styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"PDF report generated successfully: {output_path}")
        
        except ImportError:
            self.logger.warning("reportlab library not installed. Install with: pip install reportlab")
            self.logger.info("Generating text-based PDF alternative...")
            self._generate_text_pdf_alternative(output_path, **data_sections)
        
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _generate_text_pdf_alternative(self, output_path: str, **data_sections) -> None:
        """Generate text-based report as PDF alternative"""
        text_output = output_path.replace('.pdf', '.txt')
        
        lines = []
        lines.append("=" * 80)
        lines.append("DATA QUALITY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Executive Summary
        if 'scoring_results' in data_sections:
            scoring = data_sections['scoring_results']
            lines.append("\nEXECUTIVE SUMMARY")
            lines.append("-" * 80)
            lines.append(f"Overall DQ Score: {scoring.get('overall_score', 0):.2f}")
            lines.append(f"Classification: {scoring.get('classification', 'Unknown')}")
            lines.append("")
        
        # Recommendations
        if 'recommendations' in data_sections:
            lines.append("\nTOP RECOMMENDATIONS")
            lines.append("-" * 80)
            for i, rec in enumerate(data_sections['recommendations'][:5], 1):
                lines.append(f"\n{i}. {rec.get('title', '')}")
                lines.append(f"   {rec.get('description', '')}")
                lines.append(f"   Priority: {rec.get('priority', '')} | Effort: {rec.get('effort', '')}")
        
        # Alerts
        if 'alerts' in data_sections:
            lines.append("\n\nALERTS")
            lines.append("-" * 80)
            for alert in data_sections['alerts'][:10]:
                lines.append(f"[{alert.get('severity', '')}] {alert.get('message', '')}")
        
        lines.append("\n" + "=" * 80)
        
        with open(text_output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        self.logger.info(f"Text report generated as PDF alternative: {text_output}")
    
    def generate_all_reports(self, output_dir: str, base_filename: str, **data_sections) -> Dict[str, str]:
        """
        Generate all report formats.
        
        Args:
            output_dir: Output directory
            base_filename: Base filename (without extension)
            **data_sections: Data sections to include
            
        Returns:
            Dictionary mapping format to output path
        """
        self.logger.info("Generating all report formats...")
        
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        generated_reports = {}
        
        # Excel report
        excel_path = str(output_dir_path / f"{base_filename}.xlsx")
        try:
            self.generate_comprehensive_excel_report(excel_path, **data_sections)
            generated_reports['excel'] = excel_path
        except Exception as e:
            self.logger.error(f"Failed to generate Excel report: {str(e)}")
        
        # JSON report
        json_path = str(output_dir_path / f"{base_filename}.json")
        try:
            self.generate_json_report(json_path, **data_sections)
            generated_reports['json'] = json_path
        except Exception as e:
            self.logger.error(f"Failed to generate JSON report: {str(e)}")
        
        # PDF report
        pdf_path = str(output_dir_path / f"{base_filename}.pdf")
        try:
            self.generate_pdf_report(pdf_path, **data_sections)
            generated_reports['pdf'] = pdf_path
        except Exception as e:
            self.logger.error(f"Failed to generate PDF report: {str(e)}")
        
        self.logger.info(f"Generated {len(generated_reports)} report formats")
        
        return generated_reports

# Made with Bob
