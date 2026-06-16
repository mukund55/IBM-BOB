import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


SEVERITY_KEYWORDS = ("FATAL", "ERROR", "ABORT", "FAILED", "WARNING")


def safe_search(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def collect_matches(pattern: str, text: str, flags: int = 0) -> List[str]:
    return [match.strip() for match in re.findall(pattern, text, flags)]


def extract_block(text: str, start_marker: str, end_marker: Optional[str] = None) -> Optional[str]:
    start_index = text.find(start_marker)
    if start_index == -1:
        return None

    block_start = start_index + len(start_marker)
    if end_marker:
        end_index = text.find(end_marker, block_start)
        if end_index == -1:
            end_index = len(text)
    else:
        end_index = len(text)

    return text[block_start:end_index].strip()


def parse_failed_record(text: str) -> Dict[str, str]:
    block = extract_block(text, "Failed Record:", 'Component "')
    if not block:
        return {}

    record = {}
    for line in block.splitlines():
        line = line.strip()
        if "=" in line:
            key, value = line.split("=", 1)
            record[key.strip()] = value.strip()
    return record


def parse_component_counts(text: str) -> Dict[str, Dict[str, int]]:
    component_counts: Dict[str, Dict[str, int]] = {}
    patterns = [
        r"\[(.*?)\]\s+Records processed:\s+(\d+)",
        r"\[(.*?)\]\s+Records accepted:\s+(\d+)",
        r"\[(.*?)\]\s+Records rejected:\s+(\d+)",
        r"\[(.*?)\]\s+Input records\s*:\s*(\d+)",
        r"\[(.*?)\]\s+Output records:\s+(\d+)",
    ]

    metric_names = {
        "Records processed": r"\[(.*?)\]\s+Records processed:\s+(\d+)",
        "Records accepted": r"\[(.*?)\]\s+Records accepted:\s+(\d+)",
        "Records rejected": r"\[(.*?)\]\s+Records rejected:\s+(\d+)",
        "Input records": r"\[(.*?)\]\s+Input records\s*:\s*(\d+)",
        "Output records": r"\[(.*?)\]\s+Output records:\s+(\d+)",
    }

    for metric_name, pattern in metric_names.items():
        for component, count in re.findall(pattern, text):
            component_counts.setdefault(component, {})[metric_name] = int(count)

    return component_counts


def parse_graph_summary(text: str) -> Dict[str, str]:
    summary_block = extract_block(text, "Graph Summary", "=======================================================================")
    if not summary_block:
        return {}

    summary = {}
    for line in summary_block.splitlines():
        line = line.strip("- ").rstrip()
        if ":" in line:
            key, value = line.split(":", 1)
            summary[key.strip()] = value.strip()
    return summary


def detect_validation_issues(parsed: Dict) -> List[str]:
    issues: List[str] = []

    required_fields = [
        "graph_name",
        "start_time",
        "host",
        "graph_status",
        "end_time",
    ]
    for field in required_fields:
        if not parsed.get(field):
            issues.append(f"Missing required field: {field}")

    if parsed.get("graph_status") and parsed["graph_status"].upper() == "FAILED" and not parsed.get("root_error"):
        issues.append("Graph status is FAILED but no root error was extracted")

    if parsed.get("error_count", 0) == 0 and parsed.get("graph_status", "").upper() == "FAILED":
        issues.append("Graph failed but no ERROR lines were found")

    return issues


def infer_root_cause(parsed: Dict) -> str:
    root_error = parsed.get("root_error", "")
    oracle_error = parsed.get("oracle_error", "")
    component = parsed.get("failed_component", "")

    if "ORA-00001" in oracle_error or "unique constraint" in oracle_error.lower():
        record = parsed.get("failed_record", {})
        customer_id = record.get("CUSTOMER_ID", "unknown")
        return (
            f"Primary cause: duplicate key violation while loading data into component "
            f"'{component}'. Oracle rejected the record because a unique constraint was violated. "
            f"Likely duplicate business key/customer already exists. Failed CUSTOMER_ID={customer_id}."
        )

    if "non-zero status" in root_error.lower():
        return (
            f"Primary cause: component '{component}' exited with non-zero status, causing graph abort."
        )

    if root_error:
        return f"Primary cause: {root_error}"

    return "Primary cause could not be determined from the log."


def analyze_log(text: str, source: str) -> Dict:
    graph_name = safe_search(r"Graph:\s*(.+)", text)
    start_time = safe_search(r"Start time:\s*(.+)", text)
    host = safe_search(r"Running on host:\s*(.+)", text)
    graph_status = safe_search(r"Graph Status\s*:\s*(.+)", text)
    end_time = safe_search(r"End time\s*:\s*(.+)", text)
    elapsed_time = safe_search(r"Elapsed time\s*:\s*(.+)", text)
    failed_component = safe_search(r'Component "(.*?)" failed', text) or safe_search(r"Component Name\s*:\s*(.+)", text)
    root_error = safe_search(r"\[load_customer\]\s+db_load>\s+(.+)", text)
    oracle_error = safe_search(r"(ORA-\d+:\s*.+(?:\n\(.+\)\s+violated)?)", text, re.MULTILINE)
    exit_status = safe_search(r"Exit Status\s*:\s*(.+)", text)

    severity_lines = []
    for line in text.splitlines():
        if any(keyword in line.upper() for keyword in SEVERITY_KEYWORDS):
            severity_lines.append(line.strip())

    parsed = {
        "source_file": source,
        "graph_name": graph_name,
        "start_time": start_time,
        "host": host,
        "graph_status": graph_status,
        "end_time": end_time,
        "elapsed_time": elapsed_time,
        "failed_component": failed_component,
        "root_error": root_error,
        "oracle_error": oracle_error,
        "exit_status": exit_status,
        "failed_record": parse_failed_record(text),
        "component_counts": parse_component_counts(text),
        "graph_summary": parse_graph_summary(text),
        "error_count": sum(1 for line in severity_lines if "ERROR" in line.upper()),
        "warning_count": sum(1 for line in severity_lines if "WARNING" in line.upper()),
        "severity_lines": severity_lines,
    }

    parsed["validation_issues"] = detect_validation_issues(parsed)
    parsed["root_cause_analysis"] = infer_root_cause(parsed)
    return parsed


def print_human_readable_report(result: Dict) -> None:
    print("=" * 80)
    print("AB INITIO LOG ANALYSIS REPORT")
    print("=" * 80)
    print(f"Source File         : {result.get('source_file', 'N/A')}")
    print(f"Graph Name          : {result.get('graph_name', 'N/A')}")
    print(f"Host                : {result.get('host', 'N/A')}")
    print(f"Start Time          : {result.get('start_time', 'N/A')}")
    print(f"End Time            : {result.get('end_time', 'N/A')}")
    print(f"Elapsed Time        : {result.get('elapsed_time', 'N/A')}")
    print(f"Graph Status        : {result.get('graph_status', 'N/A')}")
    print(f"Failed Component    : {result.get('failed_component', 'N/A')}")
    print(f"Exit Status         : {result.get('exit_status', 'N/A')}")
    print()

    print("ROOT ERROR")
    print("-" * 80)
    print(result.get("root_error", "N/A"))
    if result.get("oracle_error"):
        print(result["oracle_error"])
    print()

    print("ROOT CAUSE ANALYSIS")
    print("-" * 80)
    print(result.get("root_cause_analysis", "N/A"))
    print()

    print("FAILED RECORD")
    print("-" * 80)
    failed_record = result.get("failed_record", {})
    if failed_record:
        for key, value in failed_record.items():
            print(f"{key}: {value}")
    else:
        print("No failed record block found.")
    print()

    print("VALIDATION ISSUES")
    print("-" * 80)
    validation_issues = result.get("validation_issues", [])
    if validation_issues:
        for issue in validation_issues:
            print(f"- {issue}")
    else:
        print("No structural validation issues found.")
    print()

    print("SEVERITY LINES")
    print("-" * 80)
    for line in result.get("severity_lines", []):
        print(line)
    print()

    print("GRAPH SUMMARY")
    print("-" * 80)
    for key, value in result.get("graph_summary", {}).items():
        print(f"{key}: {value}")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze and validate Ab Initio graph log files.")
    parser.add_argument("path", help="Path to a log file or directory containing log files")
    parser.add_argument("--json", action="store_true", help="Print output in JSON format")
    args = parser.parse_args()

    target = Path(args.path)
    files: List[Path]

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(
            [p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in {".log", ".out", ".txt"}]
        )
    else:
        raise FileNotFoundError(f"Path not found: {target}")

    if not files:
        raise FileNotFoundError("No log files found to analyze.")

    results = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        results.append(analyze_log(text, str(file_path)))

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    else:
        for index, result in enumerate(results, start=1):
            if len(results) > 1:
                print(f"\nLOG {index} OF {len(results)}")
            print_human_readable_report(result)


if __name__ == "__main__":
    main()

# Made with Bob
