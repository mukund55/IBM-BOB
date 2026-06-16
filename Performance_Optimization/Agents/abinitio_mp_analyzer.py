#!/usr/bin/env python3
"""
Ab Initio MP (Metadata) File Analyzer
Analyzes .mp files for standard practices and optimization opportunities
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
    suggestion: Optional[str] = None


@dataclass
class ComponentInfo:
    """Information about a graph component"""
    name: str
    type: str
    parameters: Dict[str, str]


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    file_path: str
    graph_name: str
    components: List[ComponentInfo]
    issues: List[Issue]
    optimization_score: float
    summary: Dict[str, int]


class AbInitioMPAnalyzer:
    """Analyzer for Ab Initio .mp (metadata) files"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self._read_file()
        self.graph_name = ""
        self.components: List[ComponentInfo] = []
        self.issues: List[Issue] = []
        
    def _read_file(self) -> str:
        """Read the MP file"""
        try:
            return self.file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Error reading file {self.file_path}: {e}")
    
    def parse(self) -> None:
        """Parse the MP file structure"""
        self._extract_graph_name()
        self._extract_components()
    
    def _extract_graph_name(self) -> None:
        """Extract graph name from MP file"""
        # Look for graph name pattern
        match = re.search(r'\|inmemory_total_sales_by_store\|', self.content)
        if match:
            self.graph_name = "inmemory_total_sales_by_store"
        else:
            # Try to find any graph name pattern
            match = re.search(r'\|([a-z_][a-z0-9_]*)\|User\|', self.content)
            if match:
                self.graph_name = match.group(1)
            else:
                self.graph_name = "Unknown"
    
    def _extract_components(self) -> None:
        """Extract component information from MP file"""
        # Extract Rollup component
        rollup_match = re.search(r'sorted_input\|(False|True)\|', self.content)
        if rollup_match:
            sorted_input = rollup_match.group(1)
            
            # Extract key
            key_match = re.search(r'key\|\\{([^}]+)\\}\|', self.content)
            key = key_match.group(1) if key_match else "Unknown"
            
            # Extract transform logic
            transform_match = re.search(r'transform\|(/\*.*?\*/.*?end;)\|', self.content, re.DOTALL)
            transform = transform_match.group(1) if transform_match else "Unknown"
            
            # Extract max_core
            max_core_match = re.search(r'max_core\|(\d+)\|', self.content)
            max_core = max_core_match.group(1) if max_core_match else "67108864"
            
            self.components.append(ComponentInfo(
                name="Rollup",
                type="rollup",
                parameters={
                    "sorted_input": sorted_input,
                    "key": key,
                    "transform": transform[:100] + "..." if len(transform) > 100 else transform,
                    "max_core": max_core
                }
            ))
        
        # Extract Input File component
        input_match = re.search(r'Layout\|file:\$AI_SERIAL/transactions\.dat\|', self.content)
        if input_match:
            read_metadata_match = re.search(r'read_metadata\|\$AI_DML/transactions\.dml\|', self.content)
            
            self.components.append(ComponentInfo(
                name="Input File (Transactions)",
                type="input_file",
                parameters={
                    "Layout": "file:$AI_SERIAL/transactions.dat",
                    "read_metadata": "$AI_DML/transactions.dml" if read_metadata_match else "Not specified"
                }
            ))
        
        # Extract Output File component
        output_match = re.search(r'Layout\|file:\$AI_SERIAL/total_sales_by_store\.dat\|', self.content)
        if output_match:
            write_metadata_match = re.search(r'write_metadata\|(record.*?end;)\|', self.content, re.DOTALL)
            
            self.components.append(ComponentInfo(
                name="Output File (Total Sales)",
                type="output_file",
                parameters={
                    "Layout": "file:$AI_SERIAL/total_sales_by_store.dat",
                    "write_metadata": write_metadata_match.group(1) if write_metadata_match else "Not specified"
                }
            ))
    
    def analyze(self) -> AnalysisResult:
        """Perform complete analysis"""
        self.parse()
        
        # Run all checks
        self._check_rollup_configuration()
        self._check_memory_settings()
        self._check_file_paths()
        self._check_metadata_definitions()
        self._check_transform_logic()
        self._check_error_handling()
        self._check_partitioning()
        self._check_performance_optimization()
        
        # Calculate optimization score
        score = self._calculate_optimization_score()
        
        # Generate summary
        summary = self._generate_summary()
        
        return AnalysisResult(
            file_path=str(self.file_path),
            graph_name=self.graph_name,
            components=self.components,
            issues=self.issues,
            optimization_score=score,
            summary=summary
        )
    
    def _check_rollup_configuration(self) -> None:
        """Check Rollup component configuration"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            sorted_input = rollup.parameters.get("sorted_input", "True")
            
            if sorted_input == "False":
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Configuration",
                    component="Rollup",
                    message="Rollup is configured for in-memory (unsorted) processing",
                    suggestion="In-memory rollup is good for small to medium datasets. "
                              "Ensure max-core is set appropriately to avoid disk spilling. "
                              "For large datasets, consider using sorted input for better memory efficiency."
                ))
            else:
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Configuration",
                    component="Rollup",
                    message="Rollup is configured for sorted input processing",
                    suggestion="Sorted rollup is memory-efficient for large datasets. "
                              "Ensure input data is properly sorted by the key field(s)."
                ))
    
    def _check_memory_settings(self) -> None:
        """Check memory configuration"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            max_core = int(rollup.parameters.get("max_core", "67108864"))
            sorted_input = rollup.parameters.get("sorted_input", "True")
            
            # 64MB default
            if sorted_input == "False":
                if max_core == 67108864:  # 64MB
                    self.issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="Performance",
                        component="Rollup",
                        message=f"max-core is set to default 64MB for in-memory rollup",
                        suggestion="For in-memory rollup, consider increasing max-core based on data volume:\n"
                                  "  - Small datasets (<100K records): 128MB-256MB\n"
                                  "  - Medium datasets (100K-1M records): 512MB-1GB\n"
                                  "  - Large datasets (>1M records): 2GB-4GB or use sorted input\n"
                                  "Set max-core to prevent disk spilling and improve performance."
                    ))
                elif max_core < 134217728:  # < 128MB
                    self.issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="Performance",
                        component="Rollup",
                        message=f"max-core is set to {max_core / (1024*1024):.0f}MB (relatively low for in-memory)",
                        suggestion="Consider increasing max-core for better in-memory performance. "
                                  "Monitor memory usage and adjust based on actual data volume."
                    ))
                elif max_core > 4294967296:  # > 4GB
                    self.issues.append(Issue(
                        severity=Severity.LOW,
                        category="Performance",
                        component="Rollup",
                        message=f"max-core is set to {max_core / (1024*1024*1024):.1f}GB (very high)",
                        suggestion="Ensure sufficient system memory is available. "
                                  "Consider if sorted rollup might be more appropriate for very large datasets."
                    ))
                else:
                    self.issues.append(Issue(
                        severity=Severity.INFO,
                        category="Performance",
                        component="Rollup",
                        message=f"max-core is set to {max_core / (1024*1024):.0f}MB (good for in-memory)",
                        suggestion="Memory setting appears appropriate for in-memory processing. "
                                  "Monitor actual usage and adjust if needed."
                    ))
    
    def _check_file_paths(self) -> None:
        """Check file path configurations"""
        for component in self.components:
            if component.type in ["input_file", "output_file"]:
                layout = component.parameters.get("Layout", "")
                
                if "$AI_SERIAL" in layout:
                    self.issues.append(Issue(
                        severity=Severity.INFO,
                        category="Configuration",
                        component=component.name,
                        message=f"Using parameter $AI_SERIAL for file path",
                        suggestion="Good practice: Using parameters for file paths enables environment flexibility. "
                                  "Ensure $AI_SERIAL is properly defined in your environment."
                    ))
                elif layout.startswith("file:/"):
                    self.issues.append(Issue(
                        severity=Severity.HIGH,
                        category="Configuration",
                        component=component.name,
                        message=f"Hardcoded absolute path detected: {layout}",
                        suggestion="Replace hardcoded paths with parameters (e.g., $AI_SERIAL, $INPUT_DIR) "
                                  "for better portability across environments."
                    ))
    
    def _check_metadata_definitions(self) -> None:
        """Check metadata (DML) definitions"""
        for component in self.components:
            if component.type == "input_file":
                read_metadata = component.parameters.get("read_metadata", "")
                
                if "$AI_DML" in read_metadata:
                    self.issues.append(Issue(
                        severity=Severity.INFO,
                        category="Configuration",
                        component=component.name,
                        message="Using parameterized DML path ($AI_DML)",
                        suggestion="Good practice: Centralized DML management improves maintainability."
                    ))
                elif not read_metadata or read_metadata == "Not specified":
                    self.issues.append(Issue(
                        severity=Severity.HIGH,
                        category="Configuration",
                        component=component.name,
                        message="Missing read_metadata (DML) specification",
                        suggestion="Define DML metadata to ensure proper data structure and validation."
                    ))
            
            elif component.type == "output_file":
                write_metadata = component.parameters.get("write_metadata", "")
                
                if write_metadata and write_metadata != "Not specified":
                    if "record" in write_metadata and "end;" in write_metadata:
                        self.issues.append(Issue(
                            severity=Severity.INFO,
                            category="Configuration",
                            component=component.name,
                            message="Inline DML metadata defined for output",
                            suggestion="Consider externalizing DML to a separate file for reusability "
                                      "if this structure is used in multiple places."
                        ))
                else:
                    self.issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="Configuration",
                        component=component.name,
                        message="Missing write_metadata (DML) specification",
                        suggestion="Define DML metadata for output to ensure data structure consistency."
                    ))
    
    def _check_transform_logic(self) -> None:
        """Check transform logic in Rollup"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            transform = rollup.parameters.get("transform", "")
            
            if "sum(" in transform:
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Logic",
                    component="Rollup",
                    message="Using sum() aggregation function",
                    suggestion="Ensure numeric fields are properly typed (decimal, integer) for accurate summation. "
                              "Consider adding null handling if data may contain nulls."
                ))
            
            # Check for proper field assignments
            if "::" in transform:
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Logic",
                    component="Rollup",
                    message="Transform uses proper field assignment syntax (::)",
                    suggestion="Good practice: Clear field assignments improve code readability."
                ))
    
    def _check_error_handling(self) -> None:
        """Check error handling configuration"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            # Check if reject port is configured
            has_reject = "reject" in str(self.content).lower()
            
            if not has_reject:
                self.issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="Error Handling",
                    component="Rollup",
                    message="No explicit reject port handling detected",
                    suggestion="Configure reject port to capture and analyze records that fail processing. "
                              "This helps in debugging and data quality monitoring."
                ))
    
    def _check_partitioning(self) -> None:
        """Check partitioning configuration"""
        # MP files don't explicitly show partition counts like .plan files
        # But we can provide general guidance
        self.issues.append(Issue(
            severity=Severity.INFO,
            category="Performance",
            component="Graph",
            message="Partitioning configuration not visible in MP file",
            suggestion="Ensure appropriate partitioning is set in graph properties:\n"
                      "  - For in-memory rollup: 1-2 partitions (to maximize memory per partition)\n"
                      "  - For sorted rollup: 2-8 partitions (for parallel processing)\n"
                      "  - Consider data volume and available system resources"
        ))
    
    def _check_performance_optimization(self) -> None:
        """Check for performance optimization opportunities"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            sorted_input = rollup.parameters.get("sorted_input", "True")
            key = rollup.parameters.get("key", "")
            
            if sorted_input == "False":
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Optimization",
                    component="Rollup",
                    message="In-memory rollup optimization strategy",
                    suggestion="In-memory rollup advantages:\n"
                              "  + No sorting overhead - faster for small/medium datasets\n"
                              "  + Simpler data flow - no sort component needed\n"
                              "  + Better for random key distribution\n\n"
                              "Considerations:\n"
                              "  - Requires sufficient memory (set max-core appropriately)\n"
                              "  - May spill to disk if data exceeds max-core\n"
                              "  - Output order is non-deterministic\n\n"
                              "When to use sorted rollup instead:\n"
                              "  - Very large datasets (>10M records)\n"
                              "  - Limited memory availability\n"
                              "  - Need deterministic output order"
                ))
            else:
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Optimization",
                    component="Rollup",
                    message="Sorted rollup optimization strategy",
                    suggestion="Sorted rollup advantages:\n"
                              "  + Memory-efficient for large datasets\n"
                              "  + Predictable memory usage\n"
                              "  + Deterministic output order\n\n"
                              "Optimization tips:\n"
                              "  - Ensure input is properly sorted by key\n"
                              "  - Use parallel sort with appropriate partitions\n"
                              "  - Consider in-memory rollup for smaller datasets\n"
                              "  - Enable check-sort to validate input order"
                ))
            
            # Check key complexity
            if key and key != "Unknown":
                key_fields = key.count(",") + 1 if "," in key else 1
                
                if key_fields > 3:
                    self.issues.append(Issue(
                        severity=Severity.LOW,
                        category="Performance",
                        component="Rollup",
                        message=f"Rollup key has {key_fields} fields (complex key)",
                        suggestion="Complex keys may impact performance. Consider:\n"
                                  "  • Simplifying the key if possible\n"
                                  "  • Using composite key fields\n"
                                  "  • Ensuring proper indexing for sorted input"
                    ))
    
    def _calculate_optimization_score(self) -> float:
        """Calculate overall optimization score (0-100)"""
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


def print_analysis_report(result: AnalysisResult) -> None:
    """Print human-readable analysis report"""
    print("=" * 100)
    print("AB INITIO MP FILE ANALYSIS REPORT")
    print("=" * 100)
    print(f"File Path           : {result.file_path}")
    print(f"Graph Name          : {result.graph_name}")
    print(f"Total Components    : {len(result.components)}")
    print(f"Optimization Score  : {result.optimization_score:.1f}/100")
    print()
    
    print("COMPONENTS DETECTED")
    print("-" * 100)
    for idx, comp in enumerate(result.components, 1):
        print(f"\n{idx}. {comp.name} ({comp.type})")
        for key, value in comp.parameters.items():
            # Truncate long values
            display_value = value if len(str(value)) < 80 else str(value)[:77] + "..."
            print(f"   {key:20s}: {display_value}")
    print()
    
    print("ISSUE SUMMARY")
    print("-" * 100)
    for severity, count in result.summary.items():
        if count > 0:
            print(f"{severity:12s}: {count:3d} issue(s)")
    print()
    
    if result.issues:
        print("DETAILED FINDINGS & RECOMMENDATIONS")
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
                    print(f"   Finding  : {issue.message}")
                    if issue.suggestion:
                        # Format multi-line suggestions
                        suggestion_lines = issue.suggestion.split('\n')
                        print(f"   Guidance : {suggestion_lines[0]}")
                        for line in suggestion_lines[1:]:
                            print(f"              {line}")
    
    print("\n" + "=" * 100)
    print("KEY OPTIMIZATION INSIGHTS")
    print("=" * 100)
    
    insights = [
        "1. IN-MEMORY ROLLUP:",
        "   • Best for: Small to medium datasets (<1M records)",
        "   • Advantage: No sorting overhead, faster processing",
        "   • Requirement: Sufficient memory (set max-core appropriately)",
        "   • Trade-off: Non-deterministic output order",
        "",
        "2. SORTED ROLLUP:",
        "   • Best for: Large datasets (>1M records) or limited memory",
        "   • Advantage: Memory-efficient, predictable performance",
        "   • Requirement: Input must be sorted by key",
        "   • Trade-off: Sorting overhead",
        "",
        "3. MEMORY TUNING:",
        "   • Monitor actual memory usage during execution",
        "   • Adjust max-core to prevent disk spilling",
        "   • Balance between memory usage and parallelism",
        "",
        "4. BEST PRACTICES:",
        "   • Use parameters for file paths and DML references",
        "   • Implement reject ports for error handling",
        "   • Document transform logic clearly",
        "   • Test with representative data volumes"
    ]
    
    for insight in insights:
        print(insight)
    
    print("=" * 100)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze Ab Initio .mp files for best practices and optimization opportunities"
    )
    parser.add_argument("mp_file", help="Path to the .mp file to analyze")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    try:
        analyzer = AbInitioMPAnalyzer(args.mp_file)
        result = analyzer.analyze()
        
        if args.json:
            # Convert to JSON-serializable format
            output = {
                "file_path": result.file_path,
                "graph_name": result.graph_name,
                "optimization_score": result.optimization_score,
                "summary": result.summary,
                "components": [
                    {
                        "name": comp.name,
                        "type": comp.type,
                        "parameters": comp.parameters
                    }
                    for comp in result.components
                ],
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
            print_analysis_report(result)
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

# Made with Bob
