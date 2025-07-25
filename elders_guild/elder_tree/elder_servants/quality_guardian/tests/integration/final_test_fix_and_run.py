#!/usr/bin/env python3
"""
Final Test Fix and Run Script
エルダー評議会最終修正スクリプト
"""
import re
import subprocess
from pathlib import Path


def clean_test_file(file_path):
    """テストファイルを完全にクリーンアップ"""
    content = file_path.read_text()
    lines = content.split("\n")

    cleaned_lines = []
    seen_imports = set()
    in_initial_section = True
    docstring_processed = False

    # shebang行を保持
    i = 0
    if lines and lines[0].startswith("#!"):
        cleaned_lines.append(lines[0])
        i = 1

    # docstringを処理
    while i < len(lines):
        line = lines[i]

        # 空行はスキップ
        if not line.strip():
            i += 1
            continue

        # docstringの処理
        if '"""' in line and not docstring_processed:
            # docstringの開始
            cleaned_lines.append(line)
            i += 1

            # docstringが複数行の場合
            if line.count('"""') < 2:
                while i < len(lines) and '"""' not in lines[i]:
                    cleaned_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    cleaned_lines.append(lines[i])
                    i += 1

            docstring_processed = True
            break
        else:
            break

    # 標準インポートを追加（一度だけ）
    cleaned_lines.extend(
        [
            "",
            "import sys",
            "from pathlib import Path",
            "",
            "# Add project root to Python path",
            "PROJECT_ROOT = Path(__file__).resolve().parent.parent",
            "sys.path.insert(0, str(PROJECT_ROOT))",
            "",
        ]
    )

    # 残りのコンテンツを処理（重複を除去）
    skip_next_empty = False
    for j in range(i, len(lines)):
        line = lines[j]

        # 重複するインポート行をスキップ
        if any(
            pattern in line
            for pattern in ["import sys", "sys.path.insert(0", "# Add project root"]
        ):
            skip_next_empty = True
            continue

        # 連続する空行を避ける
        if not line.strip():
            if skip_next_empty:
                skip_next_empty = False
                continue
            # すでに最後の行が空行なら追加しない
            if cleaned_lines and not cleaned_lines[-1].strip():
                continue
        else:
            skip_next_empty = False

        cleaned_lines.append(line)

    # 最後の空行を削除
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    return "\n".join(cleaned_lines)


def fix_all_test_files():
    """すべてのテストファイルを修正"""
    test_files = [
        "tests/unit/test_automated_code_review.py",
        "tests/unit/test_async_worker_optimization.py",
        "tests/unit/test_integration_test_framework.py",
        "tests/unit/test_advanced_monitoring_dashboard.py",
        "tests/unit/test_security_audit_system.py",
        "tests/unit/test_performance_optimizer.py",
        "tests/unit/test_hypothesis_generator.py",
        "tests/unit/test_ab_testing_framework.py",
        "tests/unit/test_auto_adaptation_engine.py",
        "tests/unit/test_feedback_loop_system.py",
        "tests/unit/test_knowledge_evolution.py",
        "tests/unit/test_meta_learning_system.py",
        "tests/unit/test_cross_worker_learning.py",
        "tests/unit/test_predictive_evolution.py",
    ]

    print("🔧 Cleaning test files...")

    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            try:
                cleaned_content = clean_test_file(file_path)
                file_path.write_text(cleaned_content)
                print(f"✅ Cleaned {test_file}")
            except Exception as e:
                print(f"❌ Error cleaning {test_file}: {e}")


def run_tests_with_coverage():
    """テストを実行してカバレッジを測定"""
    print("\n🚀 Running tests with coverage...")

    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/unit/test_performance_optimizer.py",
        "tests/unit/test_hypothesis_generator.py",
        "tests/unit/test_ab_testing_framework.py",
        "tests/unit/test_auto_adaptation_engine.py",
        "tests/unit/test_feedback_loop_system.py",
        "tests/unit/test_knowledge_evolution.py",
        "tests/unit/test_meta_learning_system.py",
        "tests/unit/test_cross_worker_learning.py",
        "tests/unit/test_predictive_evolution.py",
        "tests/unit/test_automated_code_review.py",
        "tests/unit/test_async_worker_optimization.py",
        "tests/unit/test_integration_test_framework.py",
        "tests/unit/test_advanced_monitoring_dashboard.py",
        "tests/unit/test_security_audit_system.py",
        "--cov=libs",
        "--cov=core",
        "--cov=workers",
        "--cov-report=term",
        "--cov-report=html",
        "-v",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("\nErrors:")
        print(result.stderr)

    # カバレッジの要約を抽出
    if "TOTAL" in result.stdout:
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                print(f"\n📊 {line}")
                break

    return result.returncode == 0


if __name__ == "__main__":
    print("🔮 Elder Council Final Test Fix & Run")
    print("=" * 50)

    # ステップ1: テストファイルのクリーンアップ
    fix_all_test_files()

    # ステップ2: テスト実行とカバレッジ測定
    print("\n" + "=" * 50)
    success = run_tests_with_coverage()

    if success:
        print("\n✨ All tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed, but coverage was measured")

    print("\n📈 Next steps:")
    print(
        "1.0 View HTML coverage report: python3 -m http.server 8080 --directory htmlcov"
    )
    print("2.0 Fix failing tests if any")
    print("3.0 Add more tests for uncovered code")
    print("4.0 Run: ai-dwarf-workshop generate-tests --uncovered")
