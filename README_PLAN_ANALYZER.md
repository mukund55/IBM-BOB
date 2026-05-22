# Ab Initio Plan File Analyzer

## Overview
A comprehensive Python-based analyzer for Ab Initio `.plan` files that checks code against standard practices and suggests optimization techniques to improve performance.

## Features

### 1. **Standard Practice Checks**
- **Naming Conventions**: Validates component names follow snake_case and are descriptive
- **Configuration Validation**: Ensures all required parameters (TYPE, FILE, DML, KEY) are properly defined
- **Hardcoded Path Detection**: Identifies absolute paths that should be parameterized
- **DML References**: Verifies proper DML file specifications for data structure definition
- **Error Handling**: Checks for reject port implementation
- **Documentation**: Validates presence of comments and documentation

### 2. **Performance Optimization Analysis**
- **Partition Configuration**: Identifies components that could benefit from parallel processing
- **Sort Optimization**: Validates sort operations and suggests improvements
- **Join Optimization**: Analyzes join patterns and suggests broadcast joins for small datasets
- **Flow Efficiency**: Detects redundant operations and unnecessary intermediate components
- **Component Consolidation**: Identifies opportunities to combine operations

### 3. **Scoring System**
- Provides an optimization score (0-100) based on detected issues
- Categorizes issues by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO
- Generates actionable recommendations for improvement

## Installation

### Prerequisites
- Python 3.7 or higher
- No external dependencies required (uses only standard library)

### Setup
```bash
# Clone or download the analyzer
# No installation needed - it's a standalone script
```

## Usage

### Basic Usage
```bash
python abinitio_plan_analyzer.py <path_to_plan_file>
```

### Example
```bash
python abinitio_plan_analyzer.py Abinitio_code/sample_customer.plan
```

### JSON Output
For programmatic processing or integration with other tools:
```bash
python abinitio_plan_analyzer.py Abinitio_code/sample_customer.plan --json
```

### Verbose Mode
For detailed analysis information:
```bash
python abinitio_plan_analyzer.py Abinitio_code/sample_customer.plan --verbose
```

## Analysis Results

### Sample Output
The analyzer provides:
1. **File Metadata**: Graph name, version, component count
2. **Optimization Score**: Overall quality score (0-100)
3. **Issue Summary**: Count of issues by severity
4. **Detailed Findings**: Specific issues with solutions
5. **Optimization Recommendations**: Best practices guide

### Issue Severity Levels

| Severity | Description | Impact on Score |
|----------|-------------|-----------------|
| CRITICAL | Must fix - prevents proper execution | -15 points |
| HIGH | Should fix - impacts reliability/portability | -10 points |
| MEDIUM | Recommended fix - impacts performance | -5 points |
| LOW | Nice to have - improves maintainability | -2 points |
| INFO | Informational - optimization opportunity | 0 points |

## Detected Issues & Solutions

### 1. Hardcoded Paths (HIGH)
**Issue**: Absolute file paths reduce portability
```
FILE="/data/in/customer.dat"
```
**Solution**: Use parameters
```
FILE="${INPUT_DIR}/customer.dat"
```

### 2. Missing Partitioning (MEDIUM)
**Issue**: Single partition limits parallelism
```
PARTITIONS {
    sort_customer : 1;
}
```
**Solution**: Enable parallel processing
```
PARTITIONS {
    sort_customer : 4;  # Use 2-8 partitions based on data volume
}
```

### 3. Missing DML Specification (HIGH)
**Issue**: No data structure definition
```
PROCESS output_summary {
    TYPE=output_file
    FILE="/data/out/summary.dat"
}
```
**Solution**: Add DML reference
```
PROCESS output_summary {
    TYPE=output_file
    DML=summary.dml
    FILE="/data/out/summary.dat"
}
```

### 4. No Error Handling (MEDIUM)
**Issue**: No reject port for bad records
**Solution**: Add reject handling
```
PROCESS validate_customer {
    TYPE=reformat
    REJECT_PORT=reject_records
}

PROCESS capture_rejects {
    TYPE=output_file
    FILE="${REJECT_DIR}/rejected_records.dat"
}
```

### 5. Broadcast Join Opportunity (INFO)
**Issue**: Small reference data sorted unnecessarily
**Solution**: Use broadcast join
```
PROCESS join_with_country {
    TYPE=join
    JOIN_TYPE="inner"
    KEY="country_code"
    MAX_CORE=100000  # Enable in-memory join for small datasets
}
```

## Optimization Recommendations

### 1. **Partitioning Strategy**
- Use 2-4 partitions for small datasets (< 1GB)
- Use 4-8 partitions for medium datasets (1-10GB)
- Use 8-16 partitions for large datasets (> 10GB)
- Avoid excessive partitioning (overhead increases)

### 2. **Join Optimization**
- **Sorted Join**: Best for large datasets, both inputs sorted
- **Broadcast Join**: Best when one input is small (< 100MB)
- **Hash Join**: Best for unsorted data with sufficient memory

### 3. **Component Consolidation**
- Combine multiple reformats into single component
- Merge filter operations with transformations
- Reduce intermediate file writes

### 4. **Parameterization**
- Use parameter files (.pset) for environment-specific values
- Externalize all file paths, connection strings, thresholds
- Enable easy migration between environments (DEV/QA/PROD)

### 5. **Error Handling**
- Implement reject ports on all transformation components
- Log rejected records with reason codes
- Set up monitoring for reject thresholds

### 6. **Documentation**
- Add header comments explaining graph purpose
- Document business logic and transformations
- Include data lineage information
- Note dependencies and prerequisites

## Sample Analysis Report

```
====================================================================================================
AB INITIO PLAN FILE ANALYSIS REPORT
====================================================================================================
File Path           : Abinitio_code/sample_customer.plan
Graph Name          : sample_customer
Version             : 4.0
Total Components    : 8
Optimization Score  : 28.0/100

ISSUE SUMMARY
----------------------------------------------------------------------------------------------------
HIGH        :   4 issue(s)
MEDIUM      :   6 issue(s)
LOW         :   1 issue(s)
INFO        :   1 issue(s)
```

## Best Practices Checklist

- [ ] All file paths parameterized
- [ ] DML files specified for all I/O components
- [ ] Appropriate partitioning configured
- [ ] Reject ports implemented
- [ ] Join types explicitly specified
- [ ] Sort keys defined
- [ ] Comments and documentation present
- [ ] Naming conventions followed
- [ ] Error handling implemented
- [ ] Performance optimizations applied

## Integration with CI/CD

### Example Jenkins Pipeline
```groovy
stage('Analyze Ab Initio Plans') {
    steps {
        script {
            def result = sh(
                script: "python abinitio_plan_analyzer.py ${PLAN_FILE} --json",
                returnStdout: true
            )
            def analysis = readJSON text: result
            
            if (analysis.optimization_score < 70) {
                error("Plan file quality below threshold: ${analysis.optimization_score}")
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

**Issue**: "Error reading file"
- **Solution**: Verify file path and permissions

**Issue**: "No components found"
- **Solution**: Ensure file is valid .plan format with PROCESS blocks

**Issue**: "Invalid syntax"
- **Solution**: Check plan file for proper Ab Initio syntax

## Advanced Usage

### Batch Analysis
Analyze multiple plan files:
```bash
for file in Abinitio_code/*.plan; do
    python abinitio_plan_analyzer.py "$file" --json >> analysis_results.json
done
```

### Custom Thresholds
Modify severity weights in the code to match your organization's standards.

## Contributing

To extend the analyzer:
1. Add new check methods following the pattern `_check_<feature_name>()`
2. Append issues to `self.issues` list
3. Update severity weights if needed
4. Add corresponding recommendations

## Version History

- **v1.0** (2026-05-22): Initial release
  - Standard practice checks
  - Performance optimization analysis
  - Scoring system
  - JSON output support

## License

This tool is provided as-is for analyzing Ab Initio plan files.

## Support

For issues or questions:
- Review the documentation above
- Check the sample analysis output
- Examine the code comments for implementation details

---

**Made with Bob** - Your AI Software Engineering Assistant