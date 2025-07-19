#!/usr/bin/env python3
"""
Performance Report Generator
パフォーマンスレポート生成ツール
"""

import json
import argparse
from pathlib import Path
import datetime
from typing import Dict, Any


def generate_html_report(benchmark_data: Dict[str, Any]) -> str:
    """HTMLフォーマットのパフォーマンスレポートを生成"""

    # Extract benchmark information
    benchmarks = benchmark_data.get("benchmarks", [])

    # Start HTML template
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Performance Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                margin-bottom: 30px;
            }}
            h2 {{
                color: #555;
                margin-top: 30px;
                margin-bottom: 20px;
            }}
            .summary {{
                background-color: #f0f7ff;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
            .benchmark {{
                background-color: #fafafa;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
                border-left: 4px solid #0066cc;
            }}
            .benchmark-name {{
                font-weight: bold;
                font-size: 18px;
                color: #0066cc;
                margin-bottom: 10px;
            }}
            .metric {{
                display: inline-block;
                margin-right: 30px;
                margin-bottom: 10px;
            }}
            .metric-label {{
                font-weight: 600;
                color: #666;
            }}
            .metric-value {{
                font-size: 16px;
                color: #333;
            }}
            .chart {{
                margin-top: 20px;
                height: 200px;
                background-color: #f5f5f5;
                border-radius: 5px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Performance Report</h1>

            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">
                    <span class="metric-label">Total Benchmarks:</span>
                    <span class="metric-value">{len(benchmarks)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Generated:</span>
                    <span class="metric-value">{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                </div>
            </div>

            <h2>Benchmark Results</h2>
    """

    # Add benchmark details
    for benchmark in benchmarks:
        name = benchmark.get("name", "Unknown")
        stats = benchmark.get("stats", {})

        mean = stats.get("mean", 0)
        median = stats.get("median", 0)
        stddev = stats.get("stddev", 0)
        min_val = stats.get("min", 0)
        max_val = stats.get("max", 0)

        html += f"""
            <div class="benchmark">
                <div class="benchmark-name">{name}</div>
                <div class="metric">
                    <span class="metric-label">Mean:</span>
                    <span class="metric-value">{mean:.4f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Median:</span>
                    <span class="metric-value">{median:.4f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Std Dev:</span>
                    <span class="metric-value">{stddev:.4f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Min:</span>
                    <span class="metric-value">{min_val:.4f}s</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Max:</span>
                    <span class="metric-value">{max_val:.4f}s</span>
                </div>
            </div>
        """

    # Close HTML
    html += """
        </div>
    </body>
    </html>
    """

    return html


def generate_text_report(benchmark_data: Dict[str, Any]) -> str:
    """テキストフォーマットのパフォーマンスレポートを生成"""

    benchmarks = benchmark_data.get("benchmarks", [])

    report = []
    report.append("=" * 60)
    report.append("PERFORMANCE REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Benchmarks: {len(benchmarks)}")
    report.append("")

    for benchmark in benchmarks:
        name = benchmark.get("name", "Unknown")
        stats = benchmark.get("stats", {})

        report.append(f"Benchmark: {name}")
        report.append("-" * 40)
        report.append(f"  Mean:    {stats.get('mean', 0):.4f}s")
        report.append(f"  Median:  {stats.get('median', 0):.4f}s")
        report.append(f"  Std Dev: {stats.get('stddev', 0):.4f}s")
        report.append(f"  Min:     {stats.get('min', 0):.4f}s")
        report.append(f"  Max:     {stats.get('max', 0):.4f}s")
        report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Generate performance report from benchmark data"
    )
    parser.add_argument("--input", required=True, help="Input benchmark JSON file")
    parser.add_argument("--output", required=True, help="Output report file")
    parser.add_argument(
        "--format", choices=["html", "text"], default="html", help="Report format"
    )

    args = parser.parse_args()

    # Load benchmark data
    try:
        with open(args.input, "r") as f:
            benchmark_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading benchmark data: {e}")
        return 1

    # Generate report
    if args.format == "html":
        report = generate_html_report(benchmark_data)
    else:
        report = generate_text_report(benchmark_data)

    # Save report
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ Performance report saved to {args.output}")
        return 0
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
