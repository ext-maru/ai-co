#!/usr/bin/env python3
"""
実際のログファイルでエラー分類システムを実行
242万件の「Other」エラーを詳細分類
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json

from libs.enhanced_error_classifier import EnhancedErrorClassifier


def main():
    """実際のログファイルで分析実行"""
    print("🔍 Elders Guild ログファイル エラー分類実行")
    print("=" * 60)

    classifier = EnhancedErrorClassifier()

    # ログディレクトリ確認
    logs_dir = Path("/home/aicompany/ai_co/logs")

    if not logs_dir.exists():
        print("❌ ログディレクトリが見つかりません")
        return False

    # ログファイル一覧取得
    log_files = list(logs_dir.glob("*.log"))

    if not log_files:
        print("⚠️ ログファイルが見つかりません")
        return False

    print(f"📁 発見されたログファイル: {len(log_files)}個")

    total_errors = 0
    all_categories = {}
    analysis_results = []

    # 各ログファイルを分析
    for log_file in log_files[-5:]:  # 最新5ファイルのみ処理
        print(f"\n🔄 分析中: {log_file.name}")

        analysis = classifier.analyze_log_file(str(log_file))

        if "error" in analysis:
            print(f"   ❌ {analysis['error']}")
            continue

        errors_found = analysis["total_errors"]
        total_errors += errors_found

        print(f"   📊 エラー数: {errors_found}")

        # カテゴリ統計を集計
        for category, count in analysis["categories"].items():
            all_categories[category] = all_categories.get(category, 0) + count
            print(f"     {category}: {count}件")

        analysis_results.append(analysis)

    # 全体統計表示
    print(f"\n📈 全体統計:")
    print(f"   総エラー数: {total_errors:,}")
    print(f"   分類されたカテゴリ: {len(all_categories)}")

    print(f"\n📊 カテゴリ別統計:")
    sorted_categories = sorted(all_categories.items(), key=lambda x: x[1], reverse=True)

    for category, count in sorted_categories:
        percentage = (count / total_errors * 100) if total_errors > 0 else 0
        print(f"   {category}: {count:,}件 ({percentage:.1f}%)")

    # 改善提案生成
    print(f"\n💡 改善提案:")
    if sorted_categories:
        top_category, top_count = sorted_categories[0]
        print(f"   1. 最多の{top_category}エラー({top_count:,}件)の対策を優先実施")

        if top_category == "system":
            print("      → 依存関係とファイルパスの確認")
        elif top_category == "network":
            print("      → ネットワーク設定とタイムアウト値の調整")
        elif top_category == "database":
            print("      → データベース接続とクエリの最適化")
        elif top_category == "memory":
            print("      → メモリ使用量の最適化")
        elif top_category == "other":
            print("      → 未分類エラーの詳細調査と新パターン追加")

    if len(sorted_categories) > 1:
        print("   2. 複数カテゴリのエラーに対する包括的対策")
        print("   3. エラー予防システムの実装")

    # 結果をファイルに保存（ClassifiedErrorオブジェクトを辞書に変換）
    simplified_analysis = []
    for analysis in analysis_results:
        simplified = analysis.copy()
        # ClassifiedErrorオブジェクトを辞書に変換
        if "classified_errors" in simplified:
            simplified["classified_errors"] = [
                {
                    "original_error": err.original_error,
                    "category": err.category,
                    "subcategory": err.subcategory,
                    "severity": err.severity,
                    "confidence": err.confidence,
                    "auto_fix_suggestion": err.auto_fix_suggestion,
                    "timestamp": err.timestamp,
                }
                for err in simplified["classified_errors"]
            ]
        simplified_analysis.append(simplified)

    output_data = {
        "analysis_timestamp": classifier.get_statistics()["timestamp"],
        "total_errors_analyzed": total_errors,
        "category_statistics": all_categories,
        "log_files_analyzed": [str(f) for f in log_files[-5:]],
        "detailed_analysis": simplified_analysis,
        "improvement_recommendations": [
            f"最多の{sorted_categories[0][0]}エラー対策を優先実施"
            if sorted_categories
            else "エラーパターンの詳細分析が必要",
            "エラー予防システムの実装",
            "定期的なエラー分析の自動化",
        ],
    }

    output_file = Path(
        "/home/aicompany/ai_co/ai_todo/error_classification_results.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 分析結果を保存: {output_file}")

    # 分類器の統計エクスポート
    classifier.export_results(
        "/home/aicompany/ai_co/ai_todo/classified_errors_export.json"
    )

    print("🎉 エラー分類システム実行完了！")
    print("\n📋 次のステップ:")
    print("1. 最多エラーカテゴリの対策実施")
    print("2. 自動修正スクリプトの開発")
    print("3. 予防的監視システムの構築")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
