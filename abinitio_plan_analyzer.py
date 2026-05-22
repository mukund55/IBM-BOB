#!/usr/bin/env python3
"""
Ab Initio Plan File Analyzer
Analyzes .plan files for standard practices and optimization opportunities
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Issue:
    """Represents a code quality or optimization issue"""
    severity: Severity
    category: str
    component: str
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    file_path: str
    graph_name: str
    version: str
    total_components: int
    issues: List[Issue]
    optimization_score: float
    summary: Dict[str, int]


class AbInitioPlanAnalyzer:
    """Analyzer for Ab Initio .plan files"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self._read_file()
        self.lines = self.content.splitlines()
        self.graph_name = ""
        self.version = ""
        self.components: Dict[str, Dict] = {}
        self.flows: List[str] = []
        self.partitions: Dict[str, int] = {}
        self.issues: List[Issue] = []
        
    def _read_file(self) -> str:
        """Read the plan file"""
        try:
            return self.file_path.read_text(encoding='utf-8')
        except Exception as e:
            raise ValueError(f"Error reading file {self.file_path}: {e}")
    
    def parse(self) -> None:
        """Parse the plan file structure"""
        self._extract_metadata()
        self._parse_components()
        self._parse_flows()
        self._parse_partitions()
    
    def _extract_metadata(self) -> None:
        """Extract graph metadata"""
        version_match = re.search(r'VERSION\s+"([^"]+)"', self.content)
        self.version = version_match.group(1) if version_match else "Unknown"
        
        graph_match = re.search(r'GRAPH\s+(\w+)', self.content)
        self.graph_name = graph_match.group(1) if graph_match else "Unknown"
    
    def _parse_components(self) -> None:
        """Parse all PROCESS components"""
        pattern = r'PROCESS\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(pattern, self.content, re.DOTALL)
        
        for match in matches:
            component_name = match.group(1)
            component_body = match.group(2)
            
            # Extract component properties
            props = {}
            for line in component_body.strip().split('\n'):
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    props[key.strip()] = value.strip().strip('"')
            
            self.components[component_name] = props
    
    def _parse_flows(self) -> None:
        """Parse FLOW section"""
        flow_match = re.search(r'FLOW\s*\{([^}]+)\}', self.content, re.DOTALL)
        if flow_match:
            flow_content = flow_match.group(1)
            self.flows = [line.strip() for line in flow_content.split('\n') if line.strip()]
    
    def _parse_partitions(self) -> None:
        """Parse PARTITIONS section"""
        partition_match = re.search(r'PARTITIONS\s*\{([^}]+)\}', self.content, re.DOTALL)
        if partition_match:
            partition_content = partition_match.group(1)
            for line in partition_content.split('\n'):
                line = line.strip()
                if ':' in line:
                    comp, count = line.split(':', 1)
                    self.partitions[comp.strip()] = int(count.strip().rstrip(';'))
    
    def analyze(self) -> AnalysisResult:
        """Perform complete analysis"""
        self.parse()
        
        # Run all checks
        self._check_naming_conventions()
        self._check_hardcoded_paths()
        self._check_partition_configuration()
        self._check_sort_optimization()
        self._check_join_optimization()
        self._check_component_types()
        self._check_dml_references()
        self._check_flow_efficiency()
        self._check_error_handling()
        self._check_documentation()
        
        # Calculate optimization score
        score = self._calculate_optimization_score()
        
        # Generate summary
        summary = self._generate_summary()
        
        return AnalysisResult(
            file_path=str(self.file_path),
            graph_name=self.graph_name,
            version=self.version,
            total_components=len(self.components),
            issues=self.issues,
            optimization_score=score,
            summary=summary
        )
    
    def _check_naming_conventions(self) -> None:
        """Check component naming conventions"""
        for comp_name in self.components.keys():
            # Check for descriptive names
            if len(comp_name) < 3:
                self.issues.append(Issue(
                    severity=Severity.LOW,
                    category="Naming Convention",
                    component=comp_name,
                    message=f"Component name '{comp_name}' is too short",
                    suggestion="Use descriptive names (min 3 characters) that indicate component purpose"
                ))
            
            # Check for snake_case convention
            if not re.match(r'^[a-z][a-z0-9_]*$', comp_name):
                self.issues.append(Issue(
                    severity=Severity.LOW,
                    category="Naming Convention",
                    component=comp_name,
                    message=f"Component name '{comp_name}' doesn't follow snake_case convention",
                    suggestion="Use lowercase with underscores (e.g., input_customer, transform_data)"
                ))
    
    def _check_hardcoded_paths(self) -> None:
        """Check for hardcoded file paths"""
        for comp_name, props in self.components.items():
            if 'FILE' in props:
                file_path = props['FILE']
                if file_path.startswith('/') or re.match(r'^[A-Za-z]:', file_path):
                    self.issues.append(Issue(
                        severity=Severity.HIGH,
                        category="Configuration",
                        component=comp_name,
                        message=f"Hardcoded absolute path detected: {file_path}",
                        suggestion="Use parameter files or environment variables (e.g., ${INPUT_DIR}/customer.dat)"
                    ))
    
    def _check_partition_configuration(self) -> None:
        """Check partition settings for optimization"""
        for comp_name, partition_count in self.partitions.items():
            comp_type = self.components.get(comp_name, {}).get('TYPE', '')
            
            # Check if partitioning is set to 1 for components that could benefit from parallelism
            if partition_count == 1:
                if comp_type in ['sort', 'reformat', 'join', 'rollup']:
                    self.issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="Performance",
                        component=comp_name,
                        message=f"Component '{comp_name}' ({comp_type}) is not partitioned",
                        suggestion=f"Consider increasing partitions to 2-4 for parallel processing. "
                                 f"Use layout partitioning for {comp_type} operations to improve throughput."
                    ))
            
            # Check for excessive partitioning
            if partition_count > 16:
                self.issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="Performance",
                    component=comp_name,
                    message=f"Component '{comp_name}' has {partition_count} partitions (possibly excessive)",
                    suggestion="Too many partitions can cause overhead. Optimal range is typically 2-8 partitions."
                ))
    
    def _check_sort_optimization(self) -> None:
        """Check for sort optimization opportunities"""
        sort_components = {name: props for name, props in self.components.items() 
                          if props.get('TYPE') == 'sort'}
        
        for comp_name, props in sort_components.items():
            # Check if sort key is defined
            if 'KEY' not in props:
                self.issues.append(Issue(
                    severity=Severity.CRITICAL,
                    category="Configuration",
                    component=comp_name,
                    message="Sort component missing KEY specification",
                    suggestion="Define sort KEY parameter for proper sorting"
                ))
            
            # Check for sort before join
            for flow in self.flows:
                if comp_name in flow and '->' in flow:
                    parts = [p.strip().rstrip(';') for p in flow.split('->')]
                    if comp_name in parts:
                        idx = parts.index(comp_name)
                        if idx + 1 < len(parts):
                            next_comp = parts[idx + 1]
                            next_type = self.components.get(next_comp, {}).get('TYPE')
                            if next_type == 'join':
                                self.issues.append(Issue(
                                    severity=Severity.INFO,
                                    category="Optimization",
                                    component=comp_name,
                                    message=f"Sort before join detected (standard pattern)",
                                    suggestion="Good practice: Sorted inputs improve join performance. "
                                              "Consider using 'sorted join' if both inputs are already sorted."
                                ))
    
    def _check_join_optimization(self) -> None:
        """Check join optimization opportunities"""
        join_components = {name: props for name, props in self.components.items() 
                          if props.get('TYPE') == 'join'}
        
        for comp_name, props in join_components.items():
            # Check join type
            join_type = props.get('JOIN_TYPE', '').lower()
            
            if not join_type:
                self.issues.append(Issue(
                    severity=Severity.HIGH,
                    category="Configuration",
                    component=comp_name,
                    message="Join component missing JOIN_TYPE specification",
                    suggestion="Specify JOIN_TYPE (inner, left_outer, right_outer, full_outer) explicitly"
                ))
            
            # Check for join key
            if 'KEY' not in props:
                self.issues.append(Issue(
                    severity=Severity.CRITICAL,
                    category="Configuration",
                    component=comp_name,
                    message="Join component missing KEY specification",
                    suggestion="Define join KEY parameter for proper join operation"
                ))
            
            # Suggest broadcast join for small reference data
            self.issues.append(Issue(
                severity=Severity.INFO,
                category="Optimization",
                component=comp_name,
                message="Consider broadcast join optimization",
                suggestion="If one input is small (reference data), use broadcast join to avoid sorting. "
                          "Set MAX_CORE parameter to enable in-memory join for better performance."
            ))
    
    def _check_component_types(self) -> None:
        """Check for proper component type usage"""
        for comp_name, props in self.components.items():
            comp_type = props.get('TYPE', '')
            
            if not comp_type:
                self.issues.append(Issue(
                    severity=Severity.CRITICAL,
                    category="Configuration",
                    component=comp_name,
                    message="Component missing TYPE specification",
                    suggestion="Every component must have a TYPE defined"
                ))
            
            # Check for input/output file components
            if comp_type in ['input_file', 'output_file']:
                if 'FILE' not in props:
                    self.issues.append(Issue(
                        severity=Severity.CRITICAL,
                        category="Configuration",
                        component=comp_name,
                        message=f"{comp_type} component missing FILE specification",
                        suggestion="Define FILE parameter for input/output components"
                    ))
    
    def _check_dml_references(self) -> None:
        """Check DML file references"""
        for comp_name, props in self.components.items():
            if 'DML' in props:
                dml_file = props['DML']
                # Check if DML reference looks valid
                if not dml_file.endswith('.dml'):
                    self.issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="Configuration",
                        component=comp_name,
                        message=f"DML reference '{dml_file}' doesn't have .dml extension",
                        suggestion="Use .dml extension for DML files for consistency"
                    ))
            elif props.get('TYPE') in ['input_file', 'output_file']:
                self.issues.append(Issue(
                    severity=Severity.HIGH,
                    category="Configuration",
                    component=comp_name,
                    message="Input/Output component missing DML specification",
                    suggestion="Define DML parameter to specify data structure and improve maintainability"
                ))
    
    def _check_flow_efficiency(self) -> None:
        """Check flow design for efficiency"""
        # Check for unnecessary intermediate components
        reformat_count = sum(1 for props in self.components.values() 
                           if props.get('TYPE') == 'reformat')
        
        if reformat_count > 3:
            self.issues.append(Issue(
                severity=Severity.MEDIUM,
                category="Design",
                component="FLOW",
                message=f"Graph has {reformat_count} reformat components",
                suggestion="Consider consolidating multiple reformats into fewer components to reduce overhead. "
                          "Combine transformations where possible."
            ))
        
        # Check for sort after sort (potential redundancy)
        for flow in self.flows:
            if '->' in flow:
                parts = [p.strip().rstrip(';') for p in flow.split('->')]
                for i in range(len(parts) - 1):
                    curr_type = self.components.get(parts[i], {}).get('TYPE')
                    next_type = self.components.get(parts[i + 1], {}).get('TYPE')
                    if curr_type == 'sort' and next_type == 'sort':
                        self.issues.append(Issue(
                            severity=Severity.HIGH,
                            category="Design",
                            component=f"{parts[i]} -> {parts[i+1]}",
                            message="Consecutive sort operations detected",
                            suggestion="Combine sort operations or remove redundant sorting to improve performance"
                        ))
    
    def _check_error_handling(self) -> None:
        """Check for error handling mechanisms"""
        # Check for reject ports in components
        has_reject_handling = any('REJECT' in str(props) for props in self.components.values())
        
        if not has_reject_handling:
            self.issues.append(Issue(
                severity=Severity.MEDIUM,
                category="Error Handling",
                component="GRAPH",
                message="No explicit reject/error handling detected",
                suggestion="Add reject ports to components to handle bad records gracefully. "
                          "Use output_file components to capture rejected records for analysis."
            ))
    
    def _check_documentation(self) -> None:
        """Check for documentation and comments"""
        comment_lines = [line for line in self.lines if line.strip().startswith('#')]
        
        if len(comment_lines) < 3:
            self.issues.append(Issue(
                severity=Severity.LOW,
                category="Documentation",
                component="GRAPH",
                message="Insufficient documentation/comments in plan file",
                suggestion="Add comments to describe graph purpose, data flow, and business logic. "
                          "Document assumptions and dependencies."
            ))
    
    def _calculate_optimization_score(self) -> float:
        """Calculate overall optimization score (0-100)"""
        if not self.components:
            return 0.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct points based on issue severity
        severity_weights = {
            Severity.CRITICAL: 15,
            Severity.HIGH: 10,
            Severity.MEDIUM: 5,
            Severity.LOW: 2,
            Severity.INFO: 0
        }
        
        for issue in self.issues:
            score -= severity_weights.get(issue.severity, 0)
        
        # Ensure score doesn't go below 0
        return max(0.0, min(100.0, score))
    
    def _generate_summary(self) -> Dict[str, int]:
        """Generate issue summary by severity"""
        summary = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0
        }
        
        for issue in self.issues:
            summary[issue.severity.value] += 1
        
        return summary


def print_analysis_report(result: AnalysisResult, verbose: bool = False) -> None:
    """Print human-readable analysis report"""
    print("=" * 100)
    print("AB INITIO PLAN FILE ANALYSIS REPORT")
    print("=" * 100)
    print(f"File Path           : {result.file_path}")
    print(f"Graph Name          : {result.graph_name}")
    print(f"Version             : {result.version}")
    print(f"Total Components    : {result.total_components}")
    print(f"Optimization Score  : {result.optimization_score:.1f}/100")
    print()
    
    print("ISSUE SUMMARY")
    print("-" * 100)
    for severity, count in result.summary.items():
        if count > 0:
            print(f"{severity:12s}: {count:3d} issue(s)")
    print()
    
    if result.issues:
        print("DETAILED FINDINGS")
        print("-" * 100)
        
        # Group issues by severity
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            severity_issues = [i for i in result.issues if i.severity == severity]
            
            if severity_issues:
                print(f"\n[{severity.value}] Issues:")
                print("-" * 100)
                
                for idx, issue in enumerate(severity_issues, 1):
                    print(f"\n{idx}. Component: {issue.component}")
                    print(f"   Category : {issue.category}")
                    print(f"   Issue    : {issue.message}")
                    if issue.suggestion:
                        print(f"   Solution : {issue.suggestion}")
    else:
        print("No issues found! The plan file follows best practices.")
    
    print("\n" + "=" * 100)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 100)
    
    recommendations = [
        "1. PARTITIONING: Enable parallel processing by increasing partitions for sort, join, and reformat components",
        "2. BROADCAST JOIN: Use broadcast joins for small reference data to avoid unnecessary sorting",
        "3. PARAMETERIZATION: Replace hardcoded paths with parameters for environment flexibility",
        "4. ERROR HANDLING: Implement reject ports to capture and analyze bad records",
        "5. CONSOLIDATION: Combine multiple reformat operations to reduce component overhead",
        "6. SORTED JOINS: Ensure inputs are sorted before joins for optimal performance",
        "7. MONITORING: Add checkpoints and logging for better debugging and performance tracking",
        "8. DOCUMENTATION: Maintain clear comments explaining business logic and data transformations"
    ]
    
    for rec in recommendations:
        print(rec)
    
    print("=" * 100)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze Ab Initio .plan files for best practices and optimization opportunities"
    )
    parser.add_argument("plan_file", help="Path to the .plan file to analyze")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--verbose", action="store_true", help="Show detailed analysis")
    
    args = parser.parse_args()
    
    try:
        analyzer = AbInitioPlanAnalyzer(args.plan_file)
        result = analyzer.analyze()
        
        if args.json:
            # Convert to JSON-serializable format
            output = {
                "file_path": result.file_path,
                "graph_name": result.graph_name,
                "version": result.version,
                "total_components": result.total_components,
                "optimization_score": result.optimization_score,
                "summary": result.summary,
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "category": issue.category,
                        "component": issue.component,
                        "message": issue.message,
                        "suggestion": issue.suggestion
                    }
                    for issue in result.issues
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            print_analysis_report(result, args.verbose)
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

# Made with Bob
