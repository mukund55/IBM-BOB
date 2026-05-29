#!/usr/bin/env python3
"""
Ab Initio Analysis Dashboard Generator
Creates interactive HTML dashboards for plan and MP file analysis results
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ab Initio Code Analysis Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        }
        
        .card-title {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .card-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        
        .card-subtitle {
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }
        
        .score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .score-card .card-title,
        .score-card .card-subtitle {
            color: rgba(255,255,255,0.9);
        }
        
        .score-card .card-value {
            color: white;
            font-size: 3em;
        }
        
        .score-gauge {
            width: 100%;
            height: 20px;
            background: rgba(255,255,255,0.3);
            border-radius: 10px;
            margin-top: 15px;
            overflow: hidden;
        }
        
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%);
            border-radius: 10px;
            transition: width 1s ease-out;
        }
        
        .content {
            padding: 30px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        .components-grid {
            display: grid;
            gap: 20px;
        }
        
        .component-card {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 20px;
        }
        
        .component-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .component-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .component-type {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .component-params {
            display: grid;
            gap: 10px;
        }
        
        .param-row {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 15px;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }
        
        .param-key {
            font-weight: 600;
            color: #666;
        }
        
        .param-value {
            color: #333;
            word-break: break-word;
        }
        
        .issues-container {
            display: grid;
            gap: 15px;
        }
        
        .issue-card {
            border-radius: 8px;
            padding: 20px;
            border-left: 5px solid;
        }
        
        .issue-critical {
            background: #fee;
            border-color: #dc2626;
        }
        
        .issue-high {
            background: #fef3c7;
            border-color: #f59e0b;
        }
        
        .issue-medium {
            background: #dbeafe;
            border-color: #3b82f6;
        }
        
        .issue-low {
            background: #f0fdf4;
            border-color: #10b981;
        }
        
        .issue-info {
            background: #f3f4f6;
            border-color: #6b7280;
        }
        
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .issue-severity {
            font-weight: bold;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            text-transform: uppercase;
        }
        
        .severity-critical {
            background: #dc2626;
            color: white;
        }
        
        .severity-high {
            background: #f59e0b;
            color: white;
        }
        
        .severity-medium {
            background: #3b82f6;
            color: white;
        }
        
        .severity-low {
            background: #10b981;
            color: white;
        }
        
        .severity-info {
            background: #6b7280;
            color: white;
        }
        
        .issue-component {
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
        }
        
        .issue-category {
            display: inline-block;
            background: rgba(0,0,0,0.1);
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.85em;
            margin-left: 10px;
        }
        
        .issue-message {
            margin: 15px 0;
            color: #333;
            line-height: 1.6;
        }
        
        .issue-suggestion {
            background: rgba(255,255,255,0.7);
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            border-left: 3px solid #10b981;
        }
        
        .suggestion-title {
            font-weight: 600;
            color: #10b981;
            margin-bottom: 8px;
        }
        
        .suggestion-text {
            color: #555;
            line-height: 1.6;
            white-space: pre-line;
        }
        
        .insights-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-top: 30px;
        }
        
        .insights-title {
            font-size: 1.5em;
            margin-bottom: 20px;
        }
        
        .insights-list {
            list-style: none;
        }
        
        .insights-list li {
            padding: 10px 0;
            padding-left: 25px;
            position: relative;
        }
        
        .insights-list li:before {
            content: "→";
            position: absolute;
            left: 0;
            font-weight: bold;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e5e7eb;
        }
        
        .timestamp {
            font-size: 0.9em;
            color: #999;
        }
        
        @media (max-width: 768px) {
            .summary-cards {
                grid-template-columns: 1fr;
            }
            
            .param-row {
                grid-template-columns: 1fr;
            }
            
            .issue-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .filter-btn:hover {
            background: #667eea;
            color: white;
        }
        
        .filter-btn.active {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Ab Initio Code Analysis Dashboard</h1>
            <p>Comprehensive Analysis & Optimization Recommendations</p>
        </div>
        
        <div class="summary-cards">
            <div class="card score-card">
                <div class="card-title">Optimization Score</div>
                <div class="card-value">{optimization_score}/100</div>
                <div class="score-gauge">
                    <div class="score-fill" style="width: {optimization_score}%"></div>
                </div>
                <div class="card-subtitle">{score_rating}</div>
            </div>
            
            <div class="card">
                <div class="card-title">Graph Name</div>
                <div class="card-value" style="font-size: 1.5em;">{graph_name}</div>
                <div class="card-subtitle">{file_type} File</div>
            </div>
            
            <div class="card">
                <div class="card-title">Components</div>
                <div class="card-value">{total_components}</div>
                <div class="card-subtitle">Analyzed</div>
            </div>
            
            <div class="card">
                <div class="card-title">Total Issues</div>
                <div class="card-value">{total_issues}</div>
                <div class="card-subtitle">{critical_count} Critical, {high_count} High</div>
            </div>
        </div>
        
        <div class="content">
            {components_section}
            
            <div class="section">
                <h2 class="section-title">📊 Issues by Severity</h2>
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterIssues('all')">All Issues</button>
                    <button class="filter-btn" onclick="filterIssues('CRITICAL')">Critical ({critical_count})</button>
                    <button class="filter-btn" onclick="filterIssues('HIGH')">High ({high_count})</button>
                    <button class="filter-btn" onclick="filterIssues('MEDIUM')">Medium ({medium_count})</button>
                    <button class="filter-btn" onclick="filterIssues('LOW')">Low ({low_count})</button>
                    <button class="filter-btn" onclick="filterIssues('INFO')">Info ({info_count})</button>
                </div>
                
                <div class="issues-container">
                    {issues_html}
                </div>
            </div>
            
            {insights_section}
        </div>
        
        <div class="footer">
            <p><strong>Generated by Ab Initio Code Analyzer</strong></p>
            <p class="timestamp">Analysis Date: {timestamp}</p>
            <p class="timestamp">File: {file_path}</p>
        </div>
    </div>
    
    <script>
        function filterIssues(severity) {
            const issues = document.querySelectorAll('.issue-card');
            const buttons = document.querySelectorAll('.filter-btn');
            
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            issues.forEach(issue => {
                if (severity === 'all' || issue.dataset.severity === severity) {
                    issue.style.display = 'block';
                } else {
                    issue.style.display = 'none';
                }
            });
        }
        
        // Animate score gauge on load
        window.addEventListener('load', () => {
            const fill = document.querySelector('.score-fill');
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 100);
        });
    </script>
</body>
</html>
"""


def get_score_rating(score: float) -> str:
    """Get rating based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Needs Improvement"
    else:
        return "Critical Issues"


def generate_components_html(components: List[Dict]) -> str:
    """Generate HTML for components section"""
    if not components:
        return ""
    
    html = '<div class="section"><h2 class="section-title">🔧 Components</h2><div class="components-grid">'
    
    for comp in components:
        html += f'''
        <div class="component-card">
            <div class="component-header">
                <div class="component-name">{comp['name']}</div>
                <div class="component-type">{comp['type']}</div>
            </div>
            <div class="component-params">
        '''
        
        for key, value in comp.get('parameters', {}).items():
            # Truncate long values
            display_value = str(value)
            if len(display_value) > 100:
                display_value = display_value[:97] + "..."
            
            html += f'''
                <div class="param-row">
                    <div class="param-key">{key}</div>
                    <div class="param-value">{display_value}</div>
                </div>
            '''
        
        html += '</div></div>'
    
    html += '</div></div>'
    return html


def generate_issues_html(issues: List[Dict]) -> str:
    """Generate HTML for issues"""
    if not issues:
        return '<p style="text-align: center; color: #10b981; font-size: 1.2em; padding: 40px;">✓ No issues found! Code follows best practices.</p>'
    
    html = ""
    
    for issue in issues:
        severity = issue['severity']
        severity_class = severity.lower()
        
        html += f'''
        <div class="issue-card issue-{severity_class}" data-severity="{severity}">
            <div class="issue-header">
                <div>
                    <span class="issue-component">{issue['component']}</span>
                    <span class="issue-category">{issue['category']}</span>
                </div>
                <span class="issue-severity severity-{severity_class}">{severity}</span>
            </div>
            <div class="issue-message">{issue['message']}</div>
        '''
        
        if issue.get('suggestion'):
            html += f'''
            <div class="issue-suggestion">
                <div class="suggestion-title">💡 Recommendation:</div>
                <div class="suggestion-text">{issue['suggestion']}</div>
            </div>
            '''
        
        html += '</div>'
    
    return html


def generate_insights_html(file_type: str) -> str:
    """Generate insights section"""
    if file_type == "MP":
        insights = [
            "In-memory rollup is optimized for small to medium datasets",
            "Adjust max-core parameter based on actual data volume",
            "Monitor memory usage to prevent disk spilling",
            "Use parameterized paths for environment flexibility",
            "Implement reject ports for robust error handling",
            "Consider sorted rollup for very large datasets (>10M records)"
        ]
    else:
        insights = [
            "Enable parallel processing with appropriate partitioning",
            "Use broadcast joins for small reference data",
            "Replace hardcoded paths with parameters",
            "Implement reject ports for error handling",
            "Consolidate multiple reformat operations",
            "Ensure inputs are sorted before joins"
        ]
    
    html = '''
    <div class="insights-box">
        <h3 class="insights-title">💡 Key Optimization Insights</h3>
        <ul class="insights-list">
    '''
    
    for insight in insights:
        html += f'<li>{insight}</li>'
    
    html += '</ul></div>'
    return html


def generate_dashboard(json_file: Path, output_file: Path) -> None:
    """Generate HTML dashboard from JSON analysis results"""
    
    # Read JSON data with encoding detection
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # Try UTF-16 encoding
        with open(json_file, 'r', encoding='utf-16') as f:
            data = json.load(f)
    
    # Determine file type
    file_type = "MP" if "inmemory" in str(json_file).lower() or ".mp" in data.get('file_path', '') else "Plan"
    
    # Extract data
    graph_name = data.get('graph_name', 'Unknown')
    optimization_score = data.get('optimization_score', 0)
    components = data.get('components', [])
    issues = data.get('issues', [])
    summary = data.get('summary', {})
    file_path = data.get('file_path', 'Unknown')
    
    # Calculate totals
    total_components = len(components) if components else data.get('total_components', 0)
    total_issues = sum(summary.values())
    
    # Generate HTML sections
    components_html = generate_components_html(components) if components else ""
    issues_html = generate_issues_html(issues)
    insights_html = generate_insights_html(file_type)
    
    # Fill template using replace instead of format to avoid CSS brace issues
    html_content = HTML_TEMPLATE
    replacements = {
        '{graph_name}': graph_name,
        '{file_type}': file_type,
        '{optimization_score}': f"{optimization_score:.1f}",
        '{score_rating}': get_score_rating(optimization_score),
        '{total_components}': str(total_components),
        '{total_issues}': str(total_issues),
        '{critical_count}': str(summary.get('CRITICAL', 0)),
        '{high_count}': str(summary.get('HIGH', 0)),
        '{medium_count}': str(summary.get('MEDIUM', 0)),
        '{low_count}': str(summary.get('LOW', 0)),
        '{info_count}': str(summary.get('INFO', 0)),
        '{components_section}': components_html,
        '{issues_html}': issues_html,
        '{insights_section}': insights_html,
        '{timestamp}': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        '{file_path}': file_path
    }
    
    for placeholder, value in replacements.items():
        html_content = html_content.replace(placeholder, value)
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[SUCCESS] Dashboard generated successfully: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate HTML dashboard from Ab Initio analysis JSON")
    parser.add_argument("json_file", help="Path to JSON analysis results file")
    parser.add_argument("-o", "--output", help="Output HTML file path", default=None)
    
    args = parser.parse_args()
    
    json_file = Path(args.json_file)
    
    if not json_file.exists():
        print(f"Error: JSON file not found: {json_file}")
        return 1
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = json_file.with_suffix('.html')
    
    try:
        generate_dashboard(json_file, output_file)
        return 0
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

# Made with Bob
