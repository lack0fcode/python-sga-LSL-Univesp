#!/usr/bin/env python3
"""
Bandit Report Analyzer for GitHub Actions

Combines and analyzes multiple Bandit JSON reports
Generates HTML report for better visualization
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime


def generate_html_report(
    all_results, severity_counts, confidence_counts, total_issues, total_files
):
    """Generate HTML report from Bandit analysis results"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Determine status classes
    if severity_counts["HIGH"] > 0:
        status_class = "status-high"
        overall_status_class = "status-high"
        overall_status = "CRITICAL"
    elif severity_counts["MEDIUM"] > 0:
        status_class = "status-medium"
        overall_status_class = "status-medium"
        overall_status = "WARNING"
    elif severity_counts["LOW"] > 0:
        status_class = "status-low"
        overall_status_class = "status-low"
        overall_status = "REVIEW"
    else:
        status_class = "status-good"
        overall_status_class = "status-good"
        overall_status = "SECURE"

    # Generate issues table
    if all_results:
        issues_html = """
    <div class="issues-table">
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Confidence</th>
                    <th>Issue</th>
                    <th>File</th>
                    <th>Line</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>"""

        for issue in sorted(
            all_results,
            key=lambda x: (x["issue_severity"], x["issue_confidence"]),
            reverse=True,
        ):
            severity_class = f"severity-{issue['issue_severity'].lower()}"
            issues_html += f"""
                <tr>
                    <td><span class="severity-badge {severity_class}">{issue['issue_severity']}</span></td>
                    <td>{issue['issue_confidence']}</td>
                    <td>{issue['test_id']}</td>
                    <td>{issue['filename']}</td>
                    <td>{issue['line_number']}</td>
                    <td>{issue['issue_text']}</td>
                </tr>"""

        issues_html += """
            </tbody>
        </table>
    </div>"""
    else:
        issues_html = """
    <div class="issues-table">
        <div class="no-issues">
            <h3> No Security Issues Found!</h3>
            <p>All scanned files passed the security analysis.</p>
        </div>
    </div>"""

    # Simple HTML template
    html_template = (
        """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bandit Security Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; text-align: center; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; text-align: center; }
        .status-high { color: #e74c3c; }
        .status-medium { color: #f39c12; }
        .status-low { color: #f1c40f; }
        .status-good { color: #27ae60; }
        .issues-table { background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow-x: auto; }
        .issues-table table { width: 100%; border-collapse: collapse; }
        .issues-table th { background: #34495e; color: white; padding: 10px; text-align: left; }
        .issues-table td { padding: 10px; border-bottom: 1px solid #ddd; }
        .severity-high { background: #fee; color: #c0392b; }
        .severity-medium { background: #fff8e1; color: #e67e22; }
        .severity-low { background: #e8f4f8; color: #27ae60; }
        .severity-badge { padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1> Bandit Security Analysis Report</h1>
        <p>Generated on: """
        + timestamp
        + """</p>
    </div>
    <div class="summary">
        <div class="card">
            <h3>Files Scanned</h3>
            <div class="number">"""
        + str(total_files)
        + """</div>
        </div>
        <div class="card">
            <h3>Total Issues</h3>
            <div class="number """
        + status_class
        + """">"""
        + str(total_issues)
        + """</div>
        </div>
        <div class="card">
            <h3>High Severity</h3>
            <div class="number status-high">"""
        + str(severity_counts["HIGH"])
        + """</div>
        </div>
        <div class="card">
            <h3>Medium Severity</h3>
            <div class="number status-medium">"""
        + str(severity_counts["MEDIUM"])
        + """</div>
        </div>
        <div class="card">
            <h3>Low Severity</h3>
            <div class="number status-low">"""
        + str(severity_counts["LOW"])
        + """</div>
        </div>
        <div class="card">
            <h3>Status</h3>
            <div class="number """
        + overall_status_class
        + """">"""
        + overall_status
        + """</div>
        </div>
    </div>"""
        + issues_html
        + """
</body>
</html>"""
    )

    # Write HTML report
    with open("bandit_report.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"\n HTML Report generated: bandit_report.html")


def analyze_bandit_reports():
    """Analyze Bandit JSON reports and provide summary"""

    reports = [
        "bandit_core_report.json",
        "bandit_administrador_report.json",
        "bandit_guiche_report.json",
        "bandit_recepcionista_report.json",
        "bandit_profissional_saude_report.json",
        "bandit_api_report.json",
        "bandit_sga_report.json",
    ]

    total_issues = 0
    total_files = 0
    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    confidence_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    all_results = []

    print(" BANDIT SECURITY ANALYSIS - GITHUB ACTIONS")
    print("=" * 50)

    for report_file in reports:
        if Path(report_file).exists():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                results = data.get("results", [])
                all_results.extend(results)

                # Count total files from metrics (exclude _totals)
                metrics = data.get("metrics", {})
                files_in_report = len([k for k in metrics.keys() if k != "_totals"])
                total_files += files_in_report

                print(f"\n {report_file}:")
                print(f"   Files scanned: {files_in_report}")
                print(f"   Issues found: {len(results)}")

                # Count issues in this report
                for issue in results:
                    sev = issue["issue_severity"]
                    conf = issue["issue_confidence"]
                    severity_counts[sev] += 1
                    confidence_counts[conf] += 1
                    total_issues += 1

            except Exception as e:
                print(f"    Error reading {report_file}: {e}")
        else:
            print(f"\n {report_file}: Not found")

    print(f"\n SUMMARY:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Total issues: {total_issues}")
    print(f"   HIGH severity: {severity_counts['HIGH']}")
    print(f"   MEDIUM severity: {severity_counts['MEDIUM']}")
    print(f"   LOW severity: {severity_counts['LOW']}")

    # Generate HTML report
    generate_html_report(
        all_results, severity_counts, confidence_counts, total_issues, total_files
    )

    # Determine overall status
    if severity_counts["HIGH"] > 0 or severity_counts["MEDIUM"] > 0:
        print("   ❌ Status: SECURITY ISSUES FOUND - REVIEW REQUIRED")
        return 1
    elif severity_counts["LOW"] > 0:
        print("   ⚠️  Status: ONLY LOW SEVERITY ISSUES FOUND")
        return 0
    else:
        print("   ✅ Status: NO SECURITY ISSUES FOUND")
        return 0


if __name__ == "__main__":
    sys.exit(analyze_bandit_reports())
