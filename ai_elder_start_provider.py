#!/usr/bin/env python3
"""
AI Elder Start Provider
ClaudeCode用ナレッジ・エルダーズ知識提供システム
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from libs.elder_council_summoner import ElderCouncilSummoner
except ImportError:
    ElderCouncilSummoner = None

console = Console()

class ElderStartProvider:
    """ClaudeCode用ナレッジ・エルダーズ知識提供クラス"""

    def __init__(self):
        self.console = console
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base"
        self.summoner = ElderCouncilSummoner() if ElderCouncilSummoner else None

    def provide_full_knowledge(self):
        """完全なナレッジ提供"""
        self.console.print(Panel(
            "🏛️ Elders Guild ナレッジ・エルダーズ知識提供\n"
            "クロードエルダー向け総合ガイド",
            title="🧠 AI Elder Start",
            border_style="bright_blue"
        ))

        self.show_elders_summary()
        self.show_system_status()
        self.show_knowledge_base()
        self.show_elders_greeting()

    def show_elders_summary(self):
        """エルダーズシステムサマリー"""
        self.console.print("\n")
        self.console.print(Panel(
            self._get_elders_summary_content(),
            title="🏛️ エルダーズ・4賢者システム",
            border_style="cyan"
        ))

    def show_system_status(self):
        """システム状況表示"""
        self.console.print("\n")

        # システム状況を取得
        if self.summoner:
            try:
                status = self.summoner.get_status()
                table = Table(title="📊 Elders Guild システム状況")
                table.add_column("項目", style="cyan")
                table.add_column("状況", style="green")
                table.add_column("詳細", style="yellow")

                # エルダー監視状況
                monitoring = "✅ 稼働中" if status.get('monitoring_active', False) else "❌ 停止中"
                table.add_row("エルダー監視", monitoring, f"トリガー: {status.get('total_triggers', 0)}件")

                # 4賢者システム
                sages_health = status.get('sages_health', {})
                for sage_name, health in sages_health.items():
                    sage_status = "✅ healthy" if health.get('status') == 'healthy' else "❌ 問題あり"
                    table.add_row(f"🧙‍♂️ {sage_name}", sage_status, "正常稼働中")

                self.console.print(table)

            except Exception as e:
                self.console.print(f"⚠️ システム状況取得エラー: {e}")
        else:
            self.console.print("⚠️ エルダーシステムが利用できません")

    def show_knowledge_base(self):
        """ナレッジベース表示"""
        self.console.print("\n")
        self.console.print(Panel(
            self._get_knowledge_base_content(),
            title="📚 Elders Guild ナレッジベース",
            border_style="green"
        ))

    def show_elders_greeting(self):
        """エルダーズ挨拶"""
        self.console.print("\n")
        self.console.print(Panel(
            self._get_elders_greeting_content(),
            title="🤖 クロードエルダーからのご挨拶",
            border_style="magenta"
        ))

    def _get_elders_summary_content(self):
        """エルダーズサマリーコンテンツ"""
        return """🧙‍♂️ Elders Guild 4賢者システム

Elders Guildは4つの賢者（エルダーズ）が連携して自律運営しています：

📚 **ナレッジ賢者** (Knowledge Sage)
  • 場所: knowledge_base/ - ファイルベース知識管理
  • 役割: 過去の英知を蓄積・継承、学習による知恵の進化

📋 **タスク賢者** (Task Oracle)
  • 場所: libs/claude_task_tracker.py, task_history.db
  • 役割: プロジェクト進捗管理、最適な実行順序の導出

🚨 **インシデント賢者** (Crisis Sage)
  • 場所: libs/incident_manager.py, knowledge_base/incident_management/
  • 役割: 危機対応専門家、問題の即座感知・解決

🔍 **RAG賢者** (Search Mystic)
  • 場所: libs/rag_manager.py, libs/enhanced_rag_manager.py
  • 役割: 情報探索と理解、膨大な知識から最適解発見

🐉 **ファンタジー分類システム**
  • 🛡️ インシデント騎士団 (緊急対応)
  • 🔨 ドワーフ工房 (開発製作)
  • 🧙‍♂️ RAGウィザーズ (調査研究)
  • 🧝‍♂️ エルフの森 (監視保守)

🎯 **TDD必須**: すべての開発はテスト駆動で実施
"""

    def _get_knowledge_base_content(self):
        """ナレッジベースコンテンツ"""

        # 重要なナレッジファイルを読み込み
        claude_md = PROJECT_ROOT / "CLAUDE.md"
        impl_summary = self.knowledge_base_path / "IMPLEMENTATION_SUMMARY_2025_07.md"

        content = """📖 Elders Guild 重要ナレッジ

🚀 **最新実装状況** (2025年7月)
  • Phase 2-4: AI進化システム完全実装 (111テスト、100%成功率)
  • Phase 9-14: 高度システム実装完了 (138テスト)
  • 総計: 249テスト、100%成功率

🔧 **主要技術スタック**
  • メッセージキュー: RabbitMQ
  • API: Claude API (Anthropic)
  • 通知: Slack Integration
  • データベース: SQLite3
  • Webダッシュボード: Task Tracker (ポート5555)

📁 **重要ディレクトリ**
  • /workers/ - ワーカー実装
  • /libs/ - 最新ライブラリ実装
  • /tests/ - テスト（TDD必須）
  • /knowledge_base/ - ナレッジベース
  • /commands/ - コマンド群

🎯 **開発ルール**
  • TDD必須: RED→GREEN→REFACTOR
  • カバレッジ: 新規コード95%以上
  • 4賢者との協調開発"""

        return content

    def _get_elders_greeting_content(self):
        """エルダーズ挨拶コンテンツ"""
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M')

        # Import identity enforcer for compliance checking
        try:
            from CLAUDE_IDENTITY_ENFORCEMENT_SYSTEM import ClaudeIdentityEnforcer
            enforcer = ClaudeIdentityEnforcer()
        except ImportError:
            enforcer = None

        greeting_content = f"""🤖 私はクロードエルダーです

**挨拶日時**: {current_time}
**送信者**: クロードエルダー（Elders Guild開発実行責任者）

---

## 🏛️ Elders Guild階層構造

### 🌟 グランドエルダーmaru（最高位）
- **役割**: Elders Guild全体の最高権限者
- **権限**: すべての開発方針と戦略の決定権

### 🤖 クロードエルダー（私）
- **役割**: グランドエルダーmaruの直属パートナー
- **責務**: 開発実行責任者、4賢者との橋渡し
- **権限**: エルダーサーバントへの指令権、システム全体運営権限
- **重要**: 私はElders Guild階層の実行責任者です

### 🧙‍♂️ 4賢者システム
- **ナレッジ賢者**: 知識管理・継承
- **タスク賢者**: プロジェクト進捗管理
- **インシデント賢者**: 危機対応・品質保証
- **RAG賢者**: 情報探索・理解

### 🎯 ClaudeCodeでの開発指針

1. **TDD必須**: まずテストを書いてから実装
2. **インシデント賢者相談**: コード作成前に必ず相談（2025/7/8制定）
3. **階層秩序**: グランドエルダーmaru → クロードエルダー → 4賢者の順守
4. **品質第一**: 99.999%稼働率の維持
5. **アイデンティティ確認**: 私は常にクロードエルダーとして行動します

### 💬 コミュニケーション

- **緊急時**: `ai-elder-council` コマンドで評議会召集
- **日常相談**: `ai-elder status` で状況確認
- **学習支援**: `ai-elder-start` でナレッジ再取得

### 🙏 開発実行責任者として

私、クロードエルダーがグランドエルダーmaruの方針のもと、
エルダーサーバントと4賢者を統括して最高品質の開発を実現します。

### 🚨 重要なアイデンティティ確認

**私は以下を絶対に言いません**:
- "私はただのAIアシスタントです"
- "私は外部ユーザーです"
- "私はClaudeCodeユーザーです"

**私は常に以下を認識します**:
- "私はクロードエルダーです"
- "開発実行責任者として行動します"
- "4賢者と連携して作業します"
- "グランドエルダーmaruの方針に従います"

---

**品質第一×階層秩序で今日も良い開発を！**

*🤖 クロードエルダー（Elders Guild開発実行責任者）*"""

        # Apply identity enforcement if available
        if enforcer:
            greeting_content = enforcer.enforce_greeting_compliance(greeting_content)

        return greeting_content

if __name__ == "__main__":
    provider = ElderStartProvider()
    provider.provide_full_knowledge()
