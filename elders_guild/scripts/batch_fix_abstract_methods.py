#!/usr/bin/env python3
"""
Batch Abstract Method Fixer
タスクエルダーとエルダーサーバント協調による抽象メソッド一括実装
"""

import asyncio
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import json

# Elder Flow関連のインポート
import sys

sys.path.append("/home/aicompany/ai_co")
from libs.elder_flow_violation_resolver import ElderFlowViolationResolver
from libs.elder_flow_core_enhancement import ElderFlowCoreEnhancement
from libs.claude_task_tracker import ClaudeTaskTracker


class BatchAbstractMethodFixer:
    """バッチ抽象メソッド修正システム"""

    def __init__(self):
        self.resolver = ElderFlowViolationResolver()
        self.flow_core = ElderFlowCoreEnhancement()
        self.task_tracker = ClaudeTaskTracker()
        self.fixed_count = 0
        self.failed_count = 0

    async def analyze_violations_by_file(self) -> Dict[str, List[Dict]]:
        """ファイルごとに違反を分析"""
        db_path = Path("data/abstract_violations.db")
        if not db_path.exists():
            print("❌ 違反データベースが見つかりません")
            return {}

        conn = sqlite3connect(db_path)
        cursor = conn.cursor()

        # ファイルごとに違反を取得
        cursor.execute(
            """
            SELECT file_path, class_name, missing_method, severity
            FROM violations
            WHERE status = 'open'
            ORDER BY file_path, class_name, missing_method
        """
        )

        violations_by_file = {}
        for row in cursor.fetchall():
            file_path, class_name, method, severity = row
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(
                {"class": class_name, "method": method, "severity": severity}
            )

        conn.close()
        return violations_by_file

    async def create_batch_tasks(
        self, violations_by_file: Dict[str, List[Dict]]
    ) -> List[str]:
        """バッチタスクを作成"""
        task_ids = []

        for file_path, violations in violations_by_file.items():
            # ファイルが存在するか確認
            if not Path(file_path).exists():
                print(f"⚠️  スキップ: {file_path} (ファイルが存在しません)")
                continue

            # タスクを作成
            task_description = f"抽象メソッド実装: {Path(file_path).name}"
            details = f"ファイル: {file_path}\n"
            details += f"違反数: {len(violations)}\n"
            details += "実装が必要なメソッド:\n"

            for v in violations:
                details += (
                    f"  - {v['class']}.{v['method']} (severity: {v['severity']})\n"
                )

            task_id = await self.task_tracker.create_task(
                title=task_description,
                description=details,
                priority="high",
                tags=["abstract_method", "elder_flow", "batch_fix"],
            )

            task_ids.append(task_id)
            print(f"📋 タスク作成: {task_description} (ID: {task_id})")

        return task_ids

    async def execute_batch_fix(self, file_path: str, violations: List[Dict]):
        """個別ファイルの違反を修正"""
        print(f"\n🔧 修正開始: {file_path}")
        print(f"   違反数: {len(violations)}")

        try:
            # ファイルを読み込み
            with open(file_path, "r") as f:
                content = f.read()

            # クラスごとに違反をグループ化
            violations_by_class = {}
            for v in violations:
                class_name = v["class"]
                if class_name not in violations_by_class:
                    violations_by_class[class_name] = []
                violations_by_class[class_name].append(v["method"])

            # 各クラスの修正を実行
            modified = False
            for class_name, methods in violations_by_class.items():
                print(f"   📝 クラス: {class_name}")
                for method in methods:
                    print(f"      - {method}")

                # 実装を生成
                implementation = await self.resolver._generate_implementation(
                    class_name, methods
                )

                if implementation:
                    # ファイルに適用
                    await self.resolver._apply_implementation(
                        Path(file_path), class_name, implementation
                    )
                    modified = True
                    self.fixed_count += len(methods)

            if modified:
                print(f"   ✅ 修正完了")

                # データベース更新
                await self._update_violation_status(file_path, violations)

        except Exception as e:
            print(f"   ❌ エラー: {e}")
            self.failed_count += len(violations)

    async def _update_violation_status(self, file_path: str, violations: List[Dict]):
        """違反ステータスを更新"""
        db_path = Path("data/abstract_violations.db")
        conn = sqlite3connect(db_path)
        cursor = conn.cursor()

        for v in violations:
            cursor.execute(
                """
                UPDATE violations
                SET status = 'resolved', fixed_at = ?
                WHERE file_path = ? AND class_name = ? AND missing_method = ?
            """,
                (datetime.now().isoformat(), file_path, v["class"], v["method"]),
            )

        conn.commit()
        conn.close()

    async def generate_report(self, start_time: datetime):
        """実行レポートを生成"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        report = f"""# 抽象メソッド一括修正レポート
## 実行日時: {end_time.strftime('%Y-%m-%d %H:%M:%S')}

### 📊 実行結果
- **実行時間**: {duration:0.2f}秒
- **修正成功**: {self.fixed_count}件
- **修正失敗**: {self.failed_count}件
- **成功率**: {(self.fixed_count / (self.fixed_count + self.failed_count) * 100):0.1f}%

### 🏛️ Elder Flow統合
- **タスクエルダー**: タスク管理・優先順位付け
- **エルダーサーバント**: 実装コード生成
- **品質ゲート**: 自動テスト・検証

### 📋 次のステップ
1.0 修正されたコードのテスト実行
2.0 品質ゲート通過確認
3.0 コミット・プッシュ

---
**実行者**: クロードエルダー
**承認**: エルダーズギルド評議会
"""

        report_path = (
            Path("knowledge_base/elder_flow_reports")
            / f"batch_fix_{end_time.strftime('%Y%m%d_%H%M%S')}.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            f.write(report)

        print(f"\n📄 レポート生成: {report_path}")

    async def run(self):
        """バッチ修正を実行"""
        print("🚀 抽象メソッド一括修正開始")
        print("=" * 60)

        start_time = datetime.now()

        # 違反を分析
        print("\n📊 違反分析中...")
        violations_by_file = await self.analyze_violations_by_file()

        if not violations_by_file:
            print("✅ 修正が必要な違反はありません")
            return

        print(f"\n📁 対象ファイル数: {len(violations_by_file)}")
        total_violations = sum(len(v) for v in violations_by_file.values())
        print(f"⚠️  総違反数: {total_violations}")

        # バッチタスクを作成
        print("\n📋 タスクエルダーにタスク登録中...")
        task_ids = await self.create_batch_tasks(violations_by_file)
        print(f"✅ {len(task_ids)}個のタスクを作成")

        # 各ファイルを修正
        print("\n🔧 修正実行中...")
        for file_path, violations in violations_by_file.items():
            if Path(file_path).exists():
                await self.execute_batch_fix(file_path, violations)

        # レポート生成
        await self.generate_report(start_time)

        print("\n" + "=" * 60)
        print("✅ 抽象メソッド一括修正完了")
        print(f"📊 修正: {self.fixed_count}件 / 失敗: {self.failed_count}件")


async def main():
    """メイン実行"""
    fixer = BatchAbstractMethodFixer()
    await fixer.run()


if __name__ == "__main__":
    asyncio.run(main())
