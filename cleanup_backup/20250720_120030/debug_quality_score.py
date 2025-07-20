#!/usr/bin/env python3
"""
品質スコア計算のデバッグ
"""
import asyncio

from workers.code_review_pm_worker import CodeReviewPMWorker


async def debug_quality_calculation():
    config = {
        "quality_threshold": 85,
        "max_iterations": 5,
        "improvement_weight": {
            "syntax": 0.3,
            "logic": 0.25,
            "performance": 0.25,
            "security": 0.2,
        },
    }

    pm_worker = CodeReviewPMWorker(config)

    # テストデータ
    analysis_results = {
        "syntax_issues": [
            {
                "line": 5,
                "type": "style",
                "severity": "warning",
                "message": "Missing function docstring",
                "suggestion": "Add docstring explaining function purpose",
            }
        ],
        "logic_issues": [
            {
                "line": 5,
                "type": "naming",
                "severity": "warning",
                "message": "Variable names 'l', 'w' are not descriptive",
                "suggestion": "Use descriptive names like 'length', 'width'",
            }
        ],
        "performance_issues": [
            {
                "line": 10,
                "type": "string_concatenation",
                "severity": "info",
                "message": "Inefficient string concatenation",
                "suggestion": "Use f-string for better performance",
            }
        ],
        "security_issues": [],
    }

    code_metrics = {
        "lines_of_code": 20,
        "complexity_score": 3,
        "maintainability_index": 60,
    }

    # 品質スコア計算の詳細をプリント
    syntax_score = pm_worker._calculate_category_score(
        analysis_results["syntax_issues"]
    )
    logic_score = pm_worker._calculate_category_score(analysis_results["logic_issues"])
    performance_score = pm_worker._calculate_category_score(
        analysis_results["performance_issues"]
    )
    security_score = pm_worker._calculate_security_score(
        analysis_results["security_issues"]
    )

    print(f"各カテゴリスコア:")
    print(f"  Syntax: {syntax_score}")
    print(f"  Logic: {logic_score}")
    print(f"  Performance: {performance_score}")
    print(f"  Security: {security_score}")

    weights = pm_worker.improvement_weight
    weighted_score = (
        syntax_score * weights["syntax"]
        + logic_score * weights["logic"]
        + performance_score * weights["performance"]
        + security_score * weights["security"]
    )
    print(f"重み付きスコア: {weighted_score}")

    maintainability = code_metrics["maintainability_index"]
    complexity = code_metrics["complexity_score"]

    if maintainability < 70:
        maintainability_penalty = (70 - maintainability) * 0.5
    else:
        maintainability_penalty = 0

    complexity_penalty = max(0, (complexity - 3) * 3)

    print(f"保守性ペナルティ: {maintainability_penalty}")
    print(f"複雑度ペナルティ: {complexity_penalty}")

    final_score = weighted_score - maintainability_penalty - complexity_penalty
    print(f"最終スコア: {final_score}")

    # 実際の計算
    actual_score = await pm_worker._calculate_quality_score(
        analysis_results, code_metrics
    )
    print(f"実際の計算結果: {actual_score}")


if __name__ == "__main__":
    asyncio.run(debug_quality_calculation())
