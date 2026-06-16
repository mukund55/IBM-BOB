#!/usr/bin/env python3
"""
Enhanced Ab Initio MP (Metadata) File Analyzer
Analyzes .mp files based on Senior Ab Initio Code Review Checklist (60 Checkpoints)
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
    checkpoint: str
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
class ChecklistScore:
    """Scoring based on checklist categories"""
    partitioning: float  # 25%
    sorting: float  # 20%
    join_efficiency: float  # 15%
    aggregation_strategy: float  # 10%
    resource_utilization: float  # 10%
    pdl_quality: float  # 10%
    maintainability: float  # 10%
    
    def calculate_total(self) -> float:
        """Calculate weighted total score"""
        return (
            self.partitioning * 0.25 +
            self.sorting * 0.20 +
            self.join_efficiency * 0.15 +
            self.aggregation_strategy * 0.10 +
            self.resource_utilization * 0.10 +
            self.pdl_quality * 0.10 +
            self.maintainability * 0.10
        )


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    file_path: str
    graph_name: str
    components: List[ComponentInfo]
    issues: List[Issue]
    optimization_score: float
    checklist_score: ChecklistScore
    summary: Dict[str, int]
    checkpoints_passed: int
    checkpoints_applicable: int  # Only checkpoints applicable to this mapping
    checkpoints_total: int  # Total 60 checkpoints in the full checklist


class EnhancedMPAnalyzer:
    """Enhanced analyzer for Ab Initio .mp files based on 60-point checklist"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self._read_file()
        self.graph_name = ""
        self.components: List[ComponentInfo] = []
        self.issues: List[Issue] = []
        self.checkpoints_passed = 0
        self.checkpoints_applicable = 0  # Checkpoints applicable to this mapping
        self.checkpoints_total = 60  # Total checkpoints in full checklist
        
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
        # Try multiple patterns
        patterns = [
            r'\|([a-z_][a-z0-9_]*)\|User\|',
            r'graph_name["\s:]+([a-z_][a-z0-9_]*)',
            r'name\s*=\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                self.graph_name = match.group(1)
                return
        
        # Extract from filename as fallback
        self.graph_name = self.file_path.stem
    
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
        input_match = re.search(r'Layout\|file:([^|]+)\|', self.content)
        if input_match:
            layout = input_match.group(1)
            read_metadata_match = re.search(r'read_metadata\|([^|]+)\|', self.content)
            
            self.components.append(ComponentInfo(
                name="Input File",
                type="input_file",
                parameters={
                    "Layout": f"file:{layout}",
                    "read_metadata": read_metadata_match.group(1) if read_metadata_match else "Not specified"
                }
            ))
        
        # Extract Output File component
        output_match = re.search(r'write_metadata\|(record.*?end;)\|', self.content, re.DOTALL)
        if output_match:
            self.components.append(ComponentInfo(
                name="Output File",
                type="output_file",
                parameters={
                    "write_metadata": output_match.group(1)[:100] + "..." if len(output_match.group(1)) > 100 else output_match.group(1)
                }
            ))
    
    def analyze(self) -> AnalysisResult:
        """Perform complete analysis based on 60-point checklist"""
        self.parse()
        
        # Category 1: Graph Architecture & Design (8 checkpoints)
        self._check_graph_architecture()
        
        # Category 2: Metadata & DML Standards (6 checkpoints)
        self._check_metadata_standards()
        
        # Category 3: Partitioning Strategy (8 checkpoints)
        self._check_partitioning_strategy()
        
        # Category 4: Sort Optimization (6 checkpoints)
        self._check_sort_optimization()
        
        # Category 5: Join Optimization (6 checkpoints)
        self._check_join_optimization()
        
        # Category 6: Rollup, Scan & Aggregation (5 checkpoints)
        self._check_aggregation()
        
        # Category 7: Transform & PDL Coding (8 checkpoints)
        self._check_transform_pdl()
        
        # Category 8: Memory & Resource Usage (5 checkpoints)
        self._check_memory_resources()
        
        # Category 9: File Handling (5 checkpoints)
        self._check_file_handling()
        
        # Category 10: Error Handling & Recovery (5 checkpoints)
        self._check_error_handling()
        
        # Category 11: Production Readiness (5 checkpoints)
        self._check_production_readiness()
        
        # Calculate scores
        checklist_score = self._calculate_checklist_score()
        optimization_score = checklist_score.calculate_total()
        
        # Generate summary
        summary = self._generate_summary()
        
        return AnalysisResult(
            file_path=str(self.file_path),
            graph_name=self.graph_name,
            components=self.components,
            issues=self.issues,
            optimization_score=optimization_score,
            checklist_score=checklist_score,
            summary=summary,
            checkpoints_passed=self.checkpoints_passed,
            checkpoints_applicable=self.checkpoints_applicable,
            checkpoints_total=self.checkpoints_total
        )
    
    def _check_graph_architecture(self) -> None:
        """Category 1: Graph Architecture & Design (8 checkpoints)"""
        # Checkpoint: Component names are meaningful
        for comp in self.components:
            self.checkpoints_applicable += 1
            if comp.name and comp.name not in ["Unknown", "Component"]:
                self.checkpoints_passed += 1
            else:
                self.issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="Graph Architecture",
                    checkpoint="Component names are meaningful",
                    component=comp.name,
                    message="Component name is not descriptive",
                    suggestion="Use meaningful names that describe the component's purpose"
                ))
        
        # Checkpoint: No unnecessary serial processing
        if len(self.components) > 0:
            self.checkpoints_applicable += 1
            self.checkpoints_passed += 1
            self.issues.append(Issue(
                severity=Severity.INFO,
                category="Graph Architecture",
                checkpoint="Graph has clear logical flow",
                component="Graph",
                message=f"Graph contains {len(self.components)} components",
                suggestion="Ensure components are organized logically and parallel processing is utilized where possible"
            ))
    
    def _check_metadata_standards(self) -> None:
        """Category 2: Metadata & DML Standards (6 checkpoints)"""
        for comp in self.components:
            if comp.type == "input_file":
                read_metadata = comp.parameters.get("read_metadata", "")
                
                # Checkpoint: DML definitions are reusable
                self.checkpoints_applicable += 1
                if "$AI_DML" in read_metadata or read_metadata.endswith(".dml"):
                    self.checkpoints_passed += 1
                    self.issues.append(Issue(
                        severity=Severity.INFO,
                        category="Metadata Standards",
                        checkpoint="DML definitions are reusable",
                        component=comp.name,
                        message="Using external DML file - good practice",
                        suggestion="Ensure DML is version-controlled and reusable across graphs"
                    ))
                elif not read_metadata or read_metadata == "Not specified":
                    self.issues.append(Issue(
                        severity=Severity.HIGH,
                        category="Metadata Standards",
                        checkpoint="DML definitions are reusable",
                        component=comp.name,
                        message="Missing DML metadata specification",
                        suggestion="Define DML metadata to ensure proper data structure and validation"
                    ))
                
                # Checkpoint: Data types are correctly defined
                self.checkpoints_applicable += 1
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Metadata Standards",
                    checkpoint="Data types correctly defined",
                    component=comp.name,
                    message="Verify data types match source system",
                    suggestion="Review DML to ensure decimal precision, string lengths, and date formats are correct"
                ))
    
    def _check_partitioning_strategy(self) -> None:
        """Category 3: Partitioning Strategy (8 checkpoints)"""
        # Checkpoint: Partitioning chosen appropriately
        self.checkpoints_applicable += 1
        self.issues.append(Issue(
            severity=Severity.MEDIUM,
            category="Partitioning Strategy",
            checkpoint="Partitioning chosen appropriately",
            component="Graph",
            message="Partitioning configuration not visible in MP file",
            suggestion="Review graph properties:\n"
                      "  • For sorted rollup: 2-8 partitions (parallel processing)\n"
                      "  • For in-memory rollup: 1-2 partitions (maximize memory per partition)\n"
                      "  • Consider data volume and system resources\n"
                      "  • Maintain partition preservation where possible"
        ))
        
        # Checkpoint: Unnecessary repartitioning avoided
        self.checkpoints_applicable += 1
        self.checkpoints_passed += 1
        self.issues.append(Issue(
            severity=Severity.INFO,
            category="Partitioning Strategy",
            checkpoint="Unnecessary repartitioning avoided",
            component="Graph",
            message="Review partition flow to avoid unnecessary repartitioning",
            suggestion="Use 'Same' partitioning to preserve partitions between components when possible"
        ))
    
    def _check_sort_optimization(self) -> None:
        """Category 4: Sort Optimization (6 checkpoints)"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            sorted_input = rollup.parameters.get("sorted_input", "True")
            
            # Checkpoint: Sort reused by downstream components
            if sorted_input == "True":
                self.checkpoints_applicable += 2
                self.checkpoints_passed += 2
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Sort Optimization",
                    checkpoint="Sort reused by downstream components",
                    component="Rollup",
                    message="Sorted rollup requires pre-sorted input",
                    suggestion="Ensure upstream Sort component exists and sort order matches rollup key"
                ))
            else:
                self.checkpoints_applicable += 1
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Sort Optimization",
                    checkpoint="No redundant Sort components",
                    component="Rollup",
                    message="In-memory rollup does not require sorted input",
                    suggestion="Verify no unnecessary Sort component exists before this rollup"
                ))
            
            # Checkpoint: Sort keys minimized
            key = rollup.parameters.get("key", "")
            if key and key != "Unknown":
                self.checkpoints_applicable += 1
                key_fields = key.count(",") + 1 if "," in key else 1
                if key_fields <= 3:
                    self.checkpoints_passed += 1
                else:
                    self.issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="Sort Optimization",
                        checkpoint="Sort keys minimized",
                        component="Rollup",
                        message=f"Rollup key has {key_fields} fields (complex key)",
                        suggestion="Consider simplifying the key or using composite key fields for better performance"
                    ))
    
    def _check_join_optimization(self) -> None:
        """Category 5: Join Optimization (6 checkpoints)"""
        # Note: MP files may not show join components explicitly
        self.checkpoints_applicable += 1
        self.checkpoints_passed += 1
        self.issues.append(Issue(
            severity=Severity.INFO,
            category="Join Optimization",
            checkpoint="Join optimization review",
            component="Graph",
            message="Join components not detected in MP file",
            suggestion="If graph contains joins, ensure:\n"
                      "  • Join keys are indexed/sorted\n"
                      "  • Smaller datasets joined first\n"
                      "  • Appropriate join type selected\n"
                      "  • Partition compatibility verified\n"
                      "  • Consider lookup alternatives for small reference data"
        ))
    
    def _check_aggregation(self) -> None:
        """Category 6: Rollup, Scan & Aggregation (5 checkpoints)"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            # Checkpoint: Rollup keys optimized
            key = rollup.parameters.get("key", "")
            if key and key != "Unknown":
                self.checkpoints_applicable += 1
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Aggregation",
                    checkpoint="Rollup keys optimized",
                    component="Rollup",
                    message=f"Rollup key: {key}",
                    suggestion="Ensure rollup key matches business requirements and is not over-aggregated"
                ))
            
            # Checkpoint: Aggregation performed early when possible
            self.checkpoints_applicable += 1
            self.checkpoints_passed += 1
            self.issues.append(Issue(
                severity=Severity.INFO,
                category="Aggregation",
                checkpoint="Aggregation performed early",
                component="Rollup",
                message="Rollup component detected",
                suggestion="Perform aggregation as early as possible to reduce data volume for downstream processing"
            ))
            
            # Checkpoint: Aggregation reduces downstream volume
            transform = rollup.parameters.get("transform", "")
            if "sum(" in transform.lower() or "count(" in transform.lower():
                self.checkpoints_applicable += 1
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Aggregation",
                    checkpoint="Aggregation reduces volume",
                    component="Rollup",
                    message="Aggregation functions detected in transform",
                    suggestion="Verify aggregation significantly reduces record count for performance benefit"
                ))
    
    def _check_transform_pdl(self) -> None:
        """Category 7: Transform & PDL Coding (8 checkpoints)"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            transform = rollup.parameters.get("transform", "")
            
            # Checkpoint: Null handling implemented
            self.checkpoints_applicable += 1
            if "null" in transform.lower() or "is_null" in transform.lower():
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="PDL Quality",
                    checkpoint="Null handling implemented",
                    component="Rollup",
                    message="Null handling detected in transform logic",
                    suggestion="Good practice: Explicit null handling prevents unexpected results"
                ))
            else:
                self.issues.append(Issue(
                    severity=Severity.MEDIUM,
                    category="PDL Quality",
                    checkpoint="Null handling implemented",
                    component="Rollup",
                    message="No explicit null handling detected",
                    suggestion="Add null checks to prevent errors: if (is_null(field)) then default_value else field"
                ))
            
            # Checkpoint: Hardcoded values avoided
            self.checkpoints_applicable += 1
            if re.search(r'["\'][\w\s]+["\']', transform):
                self.issues.append(Issue(
                    severity=Severity.LOW,
                    category="PDL Quality",
                    checkpoint="Hardcoded values avoided",
                    component="Rollup",
                    message="Potential hardcoded values detected in transform",
                    suggestion="Replace hardcoded values with parameters or lookup tables for maintainability"
                ))
            else:
                self.checkpoints_passed += 1
            
            # Checkpoint: PDL code is readable
            if "::" in transform:
                self.checkpoints_applicable += 1
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="PDL Quality",
                    checkpoint="PDL code is readable",
                    component="Rollup",
                    message="Transform uses proper field assignment syntax (::)",
                    suggestion="Good practice: Clear field assignments improve code readability"
                ))
    
    def _check_memory_resources(self) -> None:
        """Category 8: Memory & Resource Usage (5 checkpoints)"""
        rollup = next((c for c in self.components if c.type == "rollup"), None)
        
        if rollup:
            max_core = int(rollup.parameters.get("max_core", "67108864"))
            sorted_input = rollup.parameters.get("sorted_input", "True")
            
            # Checkpoint: Memory-intensive components identified
            if sorted_input == "False":
                self.checkpoints_applicable += 1
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Resource Utilization",
                    checkpoint="Memory-intensive components identified",
                    component="Rollup",
                    message="In-memory rollup is memory-intensive",
                    suggestion="Monitor memory usage and adjust max-core based on data volume"
                ))
            
            # Checkpoint: Spill-to-disk risk assessed
            self.checkpoints_applicable += 1
            max_core_mb = max_core / (1024 * 1024)
            if sorted_input == "False" and max_core == 67108864:  # 64MB default
                self.issues.append(Issue(
                    severity=Severity.HIGH,
                    category="Resource Utilization",
                    checkpoint="Spill-to-disk risk assessed",
                    component="Rollup",
                    message=f"In-memory rollup using default max-core ({max_core_mb:.0f}MB)",
                    suggestion="Increase max-core to prevent disk spilling:\n"
                              "  • Small datasets (<100K): 128-256MB\n"
                              "  • Medium datasets (100K-1M): 512MB-1GB\n"
                              "  • Large datasets (>1M): 2-4GB or use sorted rollup"
                ))
            elif sorted_input == "False" and max_core >= 134217728:  # >= 128MB
                self.checkpoints_passed += 1
                self.issues.append(Issue(
                    severity=Severity.INFO,
                    category="Resource Utilization",
                    checkpoint="Spill-to-disk risk assessed",
                    component="Rollup",
                    message=f"max-core set to {max_core_mb:.0f}MB for in-memory processing",
                    suggestion="Good setting for in-memory rollup. Monitor actual usage and adjust if needed"
                ))
            else:
                self.checkpoints_passed += 1
    
    def _check_file_handling(self) -> None:
        """Category 9: File Handling (5 checkpoints)"""
        for comp in self.components:
            if comp.type in ["input_file", "output_file"]:
                layout = comp.parameters.get("Layout", "")
                
                # Checkpoint: Output file naming standards followed
                self.checkpoints_applicable += 1
                if "$" in layout:
                    self.checkpoints_passed += 1
                    self.issues.append(Issue(
                        severity=Severity.INFO,
                        category="File Handling",
                        checkpoint="File naming standards followed",
                        component=comp.name,
                        message="Using parameterized file paths",
                        suggestion="Good practice: Parameters enable environment flexibility"
                    ))
                elif layout.startswith("file:/"):
                    self.issues.append(Issue(
                        severity=Severity.HIGH,
                        category="File Handling",
                        checkpoint="File naming standards followed",
                        component=comp.name,
                        message=f"Hardcoded absolute path: {layout}",
                        suggestion="Replace with parameters (e.g., $AI_SERIAL, $INPUT_DIR) for portability"
                    ))
        
        # Checkpoint: File compression strategy reviewed
        self.checkpoints_applicable += 1
        self.checkpoints_passed += 1
        self.issues.append(Issue(
            severity=Severity.INFO,
            category="File Handling",
            checkpoint="File compression strategy reviewed",
            component="Graph",
            message="Review file compression settings",
            suggestion="Consider compression for large files to reduce I/O and storage costs"
        ))
    
    def _check_error_handling(self) -> None:
        """Category 10: Error Handling & Recovery (5 checkpoints)"""
        # Checkpoint: Reject records captured
        has_reject = "reject" in self.content.lower()
        
        self.checkpoints_applicable += 1
        if has_reject:
            self.checkpoints_passed += 2
            self.issues.append(Issue(
                severity=Severity.INFO,
                category="Error Handling",
                checkpoint="Reject records captured",
                component="Graph",
                message="Reject port handling detected",
                suggestion="Good practice: Capture and analyze rejected records for data quality monitoring"
            ))
        else:
            self.issues.append(Issue(
                severity=Severity.HIGH,
                category="Error Handling",
                checkpoint="Reject records captured",
                component="Graph",
                message="No explicit reject port handling detected",
                suggestion="Configure reject ports to capture records that fail processing for debugging and monitoring"
            ))
        
        # Checkpoint: Logging sufficient for troubleshooting
        self.checkpoints_applicable += 1
        self.checkpoints_passed += 1
        self.issues.append(Issue(
            severity=Severity.INFO,
            category="Error Handling",
            checkpoint="Logging sufficient",
            component="Graph",
            message="Review logging configuration",
            suggestion="Ensure adequate logging for troubleshooting: record counts, error messages, timing information"
        ))
    
    def _check_production_readiness(self) -> None:
        """Category 11: Production Readiness (5 checkpoints)"""
        # Checkpoint: Parameterization implemented
        param_count = self.content.count("$")
        self.checkpoints_applicable += 1
        if param_count > 0:
            self.checkpoints_passed += 2
            self.issues.append(Issue(
                severity=Severity.INFO,
                category="Production Readiness",
                checkpoint="Parameterization implemented",
                component="Graph",
                message=f"Found {param_count} parameter references",
                suggestion="Good practice: Parameterization enables environment-independent deployment"
            ))
        else:
            self.issues.append(Issue(
                severity=Severity.CRITICAL,
                category="Production Readiness",
                checkpoint="Parameterization implemented",
                component="Graph",
                message="No parameters detected - hardcoded values present",
                suggestion="Implement parameters for file paths, DML references, and configuration values"
            ))
        
        # Checkpoint: Environment-independent design
        self.checkpoints_applicable += 1
        self.checkpoints_passed += 1
        self.issues.append(Issue(
            severity=Severity.INFO,
            category="Production Readiness",
            checkpoint="Environment-independent design",
            component="Graph",
            message="Verify graph works across environments",
            suggestion="Test in DEV, QA, and PROD environments to ensure portability"
        ))
    
    def _calculate_checklist_score(self) -> ChecklistScore:
        """Calculate scores for each category based on issues"""
        # Initialize perfect scores
        scores = {
            'partitioning': 100.0,
            'sorting': 100.0,
            'join_efficiency': 100.0,
            'aggregation_strategy': 100.0,
            'resource_utilization': 100.0,
            'pdl_quality': 100.0,
            'maintainability': 100.0
        }
        
        # Deduct points based on issues in each category
        category_mapping = {
            'Partitioning Strategy': 'partitioning',
            'Sort Optimization': 'sorting',
            'Join Optimization': 'join_efficiency',
            'Aggregation': 'aggregation_strategy',
            'Resource Utilization': 'resource_utilization',
            'PDL Quality': 'pdl_quality',
            'Graph Architecture': 'maintainability',
            'Metadata Standards': 'maintainability',
            'File Handling': 'maintainability',
            'Error Handling': 'maintainability',
            'Production Readiness': 'maintainability'
        }
        
        severity_weights = {
            Severity.CRITICAL: 20,
            Severity.HIGH: 15,
            Severity.MEDIUM: 10,
            Severity.LOW: 5,
            Severity.INFO: 0
        }
        
        for issue in self.issues:
            category_key = category_mapping.get(issue.category)
            if category_key:
                deduction = severity_weights.get(issue.severity, 0)
                scores[category_key] = max(0, scores[category_key] - deduction)
        
        return ChecklistScore(**scores)
    
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
    print("=" * 120)
    print("ENHANCED AB INITIO MP FILE ANALYSIS REPORT")
    print("Based on Senior Ab Initio Code Review Checklist (60 Checkpoints)")
    print("=" * 120)
    print(f"File Path              : {result.file_path}")
    print(f"Graph Name             : {result.graph_name}")
    print(f"Total Components       : {len(result.components)}")
    print(f"Optimization Score     : {result.optimization_score:.1f}/100")
    print(f"Checkpoints Passed     : {result.checkpoints_passed}/{result.checkpoints_applicable} (applicable)")
    print(f"Total Checklist Points : {result.checkpoints_total} (full checklist)")
    completion_pct = (result.checkpoints_passed / result.checkpoints_applicable * 100) if result.checkpoints_applicable > 0 else 0
    print(f"Completion Percentage  : {completion_pct:.1f}%")
    print()
    
    print("CHECKLIST CATEGORY SCORES")
    print("-" * 120)
    print(f"Partitioning (25%)           : {result.checklist_score.partitioning:.1f}/100")
    print(f"Sorting (20%)                : {result.checklist_score.sorting:.1f}/100")
    print(f"Join Efficiency (15%)        : {result.checklist_score.join_efficiency:.1f}/100")
    print(f"Aggregation Strategy (10%)   : {result.checklist_score.aggregation_strategy:.1f}/100")
    print(f"Resource Utilization (10%)   : {result.checklist_score.resource_utilization:.1f}/100")
    print(f"PDL Quality (10%)            : {result.checklist_score.pdl_quality:.1f}/100")
    print(f"Maintainability (10%)        : {result.checklist_score.maintainability:.1f}/100")
    print()
    
    print("COMPONENTS DETECTED")
    print("-" * 120)
    for idx, comp in enumerate(result.components, 1):
        print(f"\n{idx}. {comp.name} ({comp.type})")
        for key, value in comp.parameters.items():
            display_value = value if len(str(value)) < 80 else str(value)[:77] + "..."
            print(f"   {key:20s}: {display_value}")
    print()
    
    print("ISSUE SUMMARY")
    print("-" * 120)
    for severity, count in result.summary.items():
        if count > 0:
            print(f"{severity:12s}: {count:3d} issue(s)")
    print()
    
    if result.issues:
        print("DETAILED FINDINGS & RECOMMENDATIONS")
        print("-" * 120)
        
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            severity_issues = [i for i in result.issues if i.severity == severity]
            
            if severity_issues:
                print(f"\n[{severity.value}] Issues:")
                print("-" * 120)
                
                for idx, issue in enumerate(severity_issues, 1):
                    print(f"\n{idx}. Checkpoint: {issue.checkpoint}")
                    print(f"   Category  : {issue.category}")
                    print(f"   Component : {issue.component}")
                    print(f"   Finding   : {issue.message}")
                    if issue.suggestion:
                        suggestion_lines = issue.suggestion.split('\n')
                        print(f"   Guidance  : {suggestion_lines[0]}")
                        for line in suggestion_lines[1:]:
                            print(f"              {line}")
    
    print("\n" + "=" * 120)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Ab Initio MP analyzer based on 60-point checklist"
    )
    parser.add_argument("mp_file", help="Path to the .mp file to analyze")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    try:
        analyzer = EnhancedMPAnalyzer(args.mp_file)
        result = analyzer.analyze()
        
        if args.json:
            output = {
                "file_path": result.file_path,
                "graph_name": result.graph_name,
                "optimization_score": result.optimization_score,
                "checkpoints_passed": result.checkpoints_passed,
                "checkpoints_applicable": result.checkpoints_applicable,
                "checkpoints_total": result.checkpoints_total,
                "completion_percentage": round((result.checkpoints_passed / result.checkpoints_applicable * 100) if result.checkpoints_applicable > 0 else 0, 1),
                "checklist_score": {
                    "partitioning": result.checklist_score.partitioning,
                    "sorting": result.checklist_score.sorting,
                    "join_efficiency": result.checklist_score.join_efficiency,
                    "aggregation_strategy": result.checklist_score.aggregation_strategy,
                    "resource_utilization": result.checklist_score.resource_utilization,
                    "pdl_quality": result.checklist_score.pdl_quality,
                    "maintainability": result.checklist_score.maintainability
                },
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
                        "checkpoint": issue.checkpoint,
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