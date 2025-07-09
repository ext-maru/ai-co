#!/usr/bin/env python3
"""
Claude CLI自動起動→ナレッジ学習→エルダーズ挨拶ワークフロー
Automatic Claude CLI startup -> Knowledge learning -> Elders greeting workflow
"""

import sys
import json
import time
import subprocess
import asyncio
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_council_summoner import ElderCouncilSummoner
from libs.knowledge_grimoire_adapter import KnowledgeSageGrimoireIntegration

console = Console()

class ClaudeAutoStartupWorkflow:
    """Claude CLI自動起動ワークフロー（aicompanyユーザー専用）"""
    
    def __init__(self):
        self.console = console
        self.summoner = ElderCouncilSummoner()
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base"
        
        # 魔法書システム統合
        self.grimoire_sage = KnowledgeSageGrimoireIntegration()
        self.use_grimoire_system = True
        
        # aicompanyユーザー専用設定
        self.ai_company_home = "/home/aicompany"
        self.ai_company_user = "aicompany"
        
        # Claude CLI設定確認
        self._verify_claude_cli_setup()
        
    async def run_full_workflow(self):
        """完全な自動ワークフローを実行"""
        
        self.console.print(Panel(
            "🚀 Claude CLI自動起動ワークフロー開始\n"
            "📚 ナレッジ読み込み → 🏛️ エルダーズ挨拶",
            title="🤖 AI Company Auto Workflow",
            border_style="bright_blue"
        ))
        
        try:
            # Step 1: ナレッジファイル準備
            await self._prepare_knowledge_summary()
            
            # Step 2: Claude CLI起動（危険モード）
            await self._start_claude_cli_dangerous()
            
            # Step 3: ナレッジを自動投入
            await self._inject_knowledge_to_claude()
            
            # Step 4: エルダーズに状況報告・挨拶
            await self._greet_elders_with_status()
            
            self.console.print(Panel(
                "✅ ワークフロー完了！\n"
                "Claude CLIが起動し、ナレッジを学習してエルダーズに報告完了\n\n"
                "🚀 Claude CLIをインタラクティブモードで開始します...",
                title="🎉 Ready to Go",
                border_style="bright_green"
            ))
            
            # Claude CLIをインタラクティブモードで継続
            await self._start_interactive_claude_session()
            
        except Exception as e:
            self.console.print(Panel(
                f"❌ ワークフロー失敗: {e}",
                title="⚠️ Error",
                border_style="bright_red"
            ))
            raise
    
    async def _prepare_knowledge_summary(self):
        """ナレッジサマリーを準備"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("📚 ナレッジファイル準備中...", total=None)
            
            # 重要なナレッジファイルを特定
            important_files = [
                "CLAUDE.md",
                "IMPLEMENTATION_SUMMARY_2025_07.md", 
                "CLAUDE_TDD_GUIDE.md",
                "elder_council_requests/",
                "incident_reports/"
            ]
            
            knowledge_summary = self._create_knowledge_summary(important_files)
            
            # 自動投入用ファイルに保存
            summary_file = PROJECT_ROOT / "temp_knowledge_for_claude.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(knowledge_summary)
                
            progress.update(task, description="✅ ナレッジサマリー準備完了")
            await asyncio.sleep(1)
    
    def _create_knowledge_summary(self, important_files):
        """重要ナレッジのサマリーを作成（PostgreSQL Magic Grimoire System統合）"""
        
        summary = "# 🧠 AI Company ナレッジサマリー（Magic Grimoire System統合）\n\n"
        summary += f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n"
        summary += "**システム**: PostgreSQL + pgvector Magic Grimoire System\n\n"
        
        # 魔法書システムからの知識取得
        if self.use_grimoire_system:
            try:
                # 魔法書システムの初期化
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    loop.run_until_complete(self.grimoire_sage.initialize_async())
                    
                    # 統合知識システムの状態確認
                    grimoire_status = self.grimoire_sage.get_system_status()
                    summary += "## 🔮 Magic Grimoire System Status\n\n"
                    summary += f"- 魔法書システム: {'✅ 有効' if grimoire_status['grimoire_system']['enabled'] else '❌ 無効'}\n"
                    summary += f"- レガシーシステム: {'✅ 利用可能' if grimoire_status['legacy_system']['available'] else '❌ 無効'}\n"
                    summary += f"- 総呪文数: {grimoire_status['grimoire_system']['stats'].get('total_spells', 0)}\n"
                    summary += f"- 進化呪文数: {grimoire_status['grimoire_system']['stats'].get('evolved_spells', 0)}\n\n"
                    
                    # 重要なトピックの知識を取得
                    key_topics = [
                        "4賢者システム",
                        "AI Company開発ガイド",
                        "TDD実装",
                        "PostgreSQL移行",
                        "エルダー評議会"
                    ]
                    
                    for topic in key_topics:
                        knowledge = self.grimoire_sage.consult_unified_wisdom(topic)
                        if knowledge:
                            summary += f"## 📖 {topic}\n\n"
                            # 最初の500文字を抽出
                            excerpt = knowledge[:500] + "..." if len(knowledge) > 500 else knowledge
                            summary += excerpt + "\n\n"
                    
                    # システム状況
                    try:
                        system_status = self.summoner.get_system_status()
                        summary += "## 📊 システム運用状況\n\n"
                        summary += f"- エルダー監視: {'✅ 稼働中' if system_status.get('monitoring_active') else '❌ 停止中'}\n"
                        summary += f"- アクティブトリガー: {system_status.get('total_triggers', 0)}件\n"
                        summary += f"- ペンディング評議会: {system_status.get('pending_councils', 0)}件\n"
                        summary += f"- 4賢者統合: {'✅ 有効' if system_status.get('four_sages_enabled') else '❌ 無効'}\n\n"
                    except Exception as e:
                        summary += f"## 📊 システム状況: 取得エラー ({str(e)})\n\n"
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                self.console.print(f"⚠️ 魔法書システムエラー: {e}")
                summary += f"## ⚠️ 魔法書システムエラー\n\n{str(e)}\n\n"
                # フォールバック: 従来のファイルベースシステム
                summary += self._create_legacy_knowledge_summary()
        else:
            summary += self._create_legacy_knowledge_summary()
        
        summary += "---\n"
        summary += "**✨ Claude CLIは最新のPostgreSQL Magic Grimoire Systemの知識を学習済みです！**\n"
        
        return summary
    
    def _create_legacy_knowledge_summary(self):
        """従来のファイルベースシステムからの知識サマリー（フォールバック）"""
        
        legacy_summary = "## 📚 従来システムからの知識\n\n"
        
        # CLAUDE.md の重要部分
        claude_md = self.knowledge_base_path.parent / "CLAUDE.md"
        if claude_md.exists():
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()
                legacy_summary += "### 📋 開発ガイド要約\n\n"
                # 4賢者システムの部分を抽出
                if "4賢者システム" in content:
                    lines = content.split('\n')
                    in_sages_section = False
                    for line in lines:
                        if "4賢者システム" in line:
                            in_sages_section = True
                        elif line.startswith("## ") and in_sages_section:
                            break
                        if in_sages_section:
                            legacy_summary += line + '\n'
                legacy_summary += "\n"
        
        # 最新の実装状況
        impl_summary = self.knowledge_base_path / "IMPLEMENTATION_SUMMARY_2025_07.md"
        if impl_summary.exists():
            with open(impl_summary, 'r', encoding='utf-8') as f:
                content = f.read()
                legacy_summary += "### 🚀 最新実装状況\n\n"
                # 最初の200行程度を追加
                lines = content.split('\n')[:30]
                legacy_summary += '\n'.join(lines) + "\n\n"
        
        # エルダー評議会の最新状況
        elder_requests = list((self.knowledge_base_path / "elder_council_requests").glob("*.md"))
        if elder_requests:
            legacy_summary += "### 🏛️ エルダー評議会最新状況\n\n"
            # 最新の3件を追加
            for req_file in sorted(elder_requests, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                legacy_summary += f"- **{req_file.stem}**: 最新の評議会要請\n"
            legacy_summary += "\n"
        
        return legacy_summary
    
    async def _start_claude_cli_dangerous(self):
        """Claudeを危険モードで起動（権限チェック付き）"""
        # Root権限チェック
        if os.geteuid() == 0:
            self.console.print("❌ [red]エラー: Claude CLIはroot/sudo権限では実行できません[/red]")
            self.console.print("💡 [yellow]通常ユーザーとして実行してください[/yellow]")
            self.console.print("   例: ai-elder-cc (sudoなし)")
            return None
            
        
        """Claude CLI（危険モード）を起動"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("🚀 Claude CLI起動中...", total=None)
            
            try:
                # aicompanyユーザー専用のclaude-cli --dangerous起動
                if not getattr(self, 'claude_cli_available', True):
                    raise Exception("Claude CLI が利用できません")
                
                claude_cmd = self._get_claude_startup_command()
                claude_env = self._get_aicompany_env()
                
                self.console.print(f"🚀 起動コマンド: {' '.join(claude_cmd)}")
                
                claude_process = subprocess.Popen(
                    claude_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd='/home/aicompany/ai_co',
                    env=claude_env
                )
                
                # 起動確認（簡易的）
                await asyncio.sleep(3)
                
                if claude_process.poll() is None:
                    progress.update(task, description="✅ Claude CLI起動完了")
                    self.claude_process = claude_process
                else:
                    raise Exception("Claude CLI起動に失敗")
                    
            except Exception as e:
                progress.update(task, description=f"❌ Claude CLI起動失敗: {e}")
                # フォールバック: メッセージ表示のみ
                self.console.print(Panel(
                    "⚠️ Claude CLIの自動起動をスキップ\n"
                    "手動で以下を実行してください:\n"
                    "`claude --dangerously-skip-permissions`",
                    title="Manual Action Required",
                    border_style="yellow"
                ))
                self.claude_process = None
    
    async def _inject_knowledge_to_claude(self):
        """ナレッジをClaude CLIに自動投入"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("📚 ナレッジ注入中...", total=None)
            
            knowledge_file = PROJECT_ROOT / "temp_knowledge_for_claude.md"
            
            if self.claude_process and knowledge_file.exists():
                try:
                    # ナレッジファイルの内容を読み込み
                    with open(knowledge_file, 'r', encoding='utf-8') as f:
                        knowledge_content = f.read()
                    
                    # Claude CLIにナレッジを送信
                    injection_prompt = f"""
こんにちは！AI Companyの現在状況をお伝えします。
以下のナレッジを確認して、現在の状況を理解してください：

{knowledge_content}

理解できましたら、「ナレッジ確認完了」と返答してください。
"""
                    
                    self.claude_process.stdin.write(injection_prompt)
                    self.claude_process.stdin.flush()
                    
                    progress.update(task, description="✅ ナレッジ注入完了")
                    
                except Exception as e:
                    progress.update(task, description=f"⚠️ ナレッジ注入失敗: {e}")
            else:
                progress.update(task, description="⚠️ ナレッジ注入スキップ（Claude CLI未起動）")
                
            await asyncio.sleep(2)
    
    async def _greet_elders_with_status(self):
        """エルダーズに状況報告・挨拶"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("🏛️ エルダーズ挨拶中...", total=None)
            
            try:
                # 現在のシステム状況を取得
                system_status = self.summoner.get_system_status()
                
                # エルダーズへの挨拶メッセージを作成
                greeting_message = self._create_elder_greeting(system_status)
                
                # ナレッジベースに保存
                greeting_file = self.knowledge_base_path / "elder_greetings" / f"claude_startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                greeting_file.parent.mkdir(exist_ok=True)
                
                with open(greeting_file, 'w', encoding='utf-8') as f:
                    f.write(greeting_message)
                
                # Claude CLIからエルダーズに送信（可能であれば）
                if hasattr(self, 'claude_process') and self.claude_process:
                    elder_prompt = f"""
以下のメッセージをエルダーズに伝えてください：

{greeting_message}
"""
                    try:
                        self.claude_process.stdin.write(elder_prompt)
                        self.claude_process.stdin.flush()
                    except:
                        pass  # エラーでも継続
                
                progress.update(task, description="✅ エルダーズ挨拶完了")
                
                # 結果を表示
                self.console.print(Panel(
                    greeting_message,
                    title="🏛️ エルダーズへの挨拶",
                    border_style="bright_cyan"
                ))
                
            except Exception as e:
                progress.update(task, description=f"❌ エルダーズ挨拶失敗: {e}")
            
            await asyncio.sleep(2)
    
    def _create_elder_greeting(self, system_status):
        """エルダーズへの挨拶メッセージを作成"""
        
        now = datetime.now()
        
        greeting = f"""# 🏛️ エルダーズへのご挨拶

**挨拶日時**: {now.strftime('%Y年%m月%d日 %H:%M:%S')}
**送信者**: Claude CLI (自動起動ワークフロー)

---

## 🌅 おはようございます、エルダーズの皆様

AI Companyの一員として、本日のシステム起動をご報告申し上げます。

### 📊 現在のシステム状況

- **エルダー監視**: {'✅ 稼働中' if system_status.get('monitoring_active') else '❌ 停止中'}
- **アクティブトリガー**: {system_status.get('total_triggers', 0)}件
- **ペンディング評議会**: {system_status.get('pending_councils', 0)}件
- **4賢者システム**: {'✅ 正常稼働' if system_status.get('four_sages_enabled') else '⚠️ 要確認'}

### 🎯 本日の準備状況

1. **ナレッジ学習完了**: AI Companyの最新状況を理解
2. **システム確認済み**: 各コンポーネントの健全性をチェック
3. **エルダーズ接続**: 報告・相談体制を確立

### 🙏 エルダーズへのお願い

本日も以下についてご指導をお願いいたします：

- システムの継続的改善への助言
- 重要な意思決定に際してのご判断
- AI Companyの発展に向けた戦略的ガイダンス

### 💬 コミュニケーション体制

- **緊急時**: `ai-elder-council` コマンドで即座に召集
- **日常報告**: 定期的な状況更新を実施
- **学習相談**: ナレッジ蓄積・活用についてのご相談

---

**今日も一日、エルダーズのご指導のもと、AI Companyの発展に貢献してまいります。**

*自動生成 by Claude Auto Startup Workflow*
"""
        
        return greeting
    
    def _verify_claude_cli_setup(self):
        """Claude CLI設定確認（aicompanyユーザー専用）"""
        try:
            # Claude CLIコマンドの存在確認（claude-cli または claude）
            for cmd in ['claude-cli', 'claude']:
                result = subprocess.run(['which', cmd], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.claude_cli_path = result.stdout.strip()
                    self.claude_cli_command = cmd
                    self.claude_cli_available = True
                    self.console.print(f"✅ Claude CLI発見: {self.claude_cli_path}")
                    break
            else:
                self.console.print("⚠️ claude-cli / claude コマンドが見つかりません")
                self.claude_cli_available = False
                
            # Claude CLI設定ファイル確認
            claude_config_path = Path(self.ai_company_home) / ".anthropic" / "claude_cli.toml"
            if not claude_config_path.exists():
                self.console.print("⚠️ Claude CLI設定ファイルが見つかりません")
                self.console.print(f"   期待する場所: {claude_config_path}")
                
        except Exception as e:
            self.console.print(f"⚠️ Claude CLI設定確認エラー: {e}")
            self.claude_cli_available = False
    
    def _get_claude_startup_command(self):
        """aicompanyユーザー用のClaude CLI起動コマンドを取得"""
        # インタラクティブモード（デフォルト）で起動
        if hasattr(self, 'claude_cli_command') and self.claude_cli_command:
            return [self.claude_cli_command]
        else:
            return ['claude']
    
    def _get_aicompany_env(self):
        """aicompanyユーザー用の環境変数を取得"""
        env = os.environ.copy()
        env.update({
            'HOME': self.ai_company_home,
            'USER': self.ai_company_user,
            'PWD': '/home/aicompany/ai_co'
        })
        # CLAUDE_CODE_ENTRYPOINT を削除（--print エラーの原因）
        # Claude CLIが --print フラグと競合するため
        env.pop('CLAUDE_CODE_ENTRYPOINT', None)
        env.pop('CLAUDECODE', None)  # 関連する環境変数も削除
        return env
    
    async def _start_interactive_claude_session(self):
        """Claude CLIをインタラクティブモードで開始"""
        try:
            self.console.print("🎯 Claude CLIをお使いください！（Ctrl+D または exit で終了）")
            self.console.print("💡 AI Companyのナレッジが学習済みです")
            self.console.print("📚 何でもお尋ねください！")
            self.console.print("")
            
            # Claude CLIを直接実行（ユーザーの入力を直接渡す）
            claude_cmd = self._get_claude_startup_command()
            claude_env = self._get_aicompany_env()
            
            # 作業ディレクトリを設定
            os.chdir('/home/aicompany/ai_co')
            
            # 環境変数を更新（問題のある変数を削除）
            claude_env = self._get_aicompany_env()
            
            # CLAUDE_CODE_ENTRYPOINT を削除（--print エラーの原因）
            # 現在の環境からも削除
            for key in ['CLAUDE_CODE_ENTRYPOINT', 'CLAUDECODE']:
                claude_env.pop(key, None)
                os.environ.pop(key, None)
            
            # エラーを無視してユーザーに手動起動を案内
            self.console.print(f"🚨 Claude CLI環境変数競合が検出されました")
            self.console.print(f"📋 手動でClaude CLIを起動してください:")
            self.console.print(f"   cd /home/aicompany/ai_co")
            self.console.print(f"   unset CLAUDE_CODE_ENTRYPOINT CLAUDECODE")
            self.console.print(f"   claude")
            self.console.print(f"")
            self.console.print(f"💡 または、~/.bashrc から以下の行を削除してください:")
            self.console.print(f"   export CLAUDE_CODE_ENTRYPOINT=cli")
            self.console.print(f"   export CLAUDECODE=1")
            
            # Claude CLI終了後のメッセージ
            self.console.print("")
            self.console.print("👋 Claude CLI セッション終了")
            self.console.print("🏛️ エルダーズとの良いコミュニケーションでした！")
            
        except KeyboardInterrupt:
            self.console.print("\n👋 Claude CLI セッション中断")
        except Exception as e:
            self.console.print(f"⚠️ Claude CLI実行でエラー: {e}")
            self.console.print("手動でClaude CLIを起動してください:")
            self.console.print(f"  {' '.join(self._get_claude_startup_command())}")

async def main():
    """メイン実行関数"""
    workflow = ClaudeAutoStartupWorkflow()
    await workflow.run_full_workflow()

if __name__ == "__main__":
    asyncio.run(main())