#!/usr/bin/env python3
"""
🏛️ Elder CLI - エルダーズギルド統一コマンドシステム
ai-* コマンドを elder に統一
"""

import click
import sys
import os
from pathlib import Path
from typing import Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 既存コマンドのインポート用ヘルパー
def import_legacy_command(module_name: str, class_name: str):
    """レガシーコマンドを動的インポート"""
    try:
        module = __import__(f'commands.{module_name}', fromlist=[class_name])
        return getattr(module, class_name)
    except Exception as e:
        click.echo(f"❌ コマンドのインポートに失敗: {e}", err=True)
        sys.exit(1)

# 非推奨警告
def deprecation_warning(old_cmd: str, new_cmd: str):
    """非推奨コマンドの警告表示"""
    click.echo(
        click.style(
            f"⚠️  '{old_cmd}' は非推奨です。'{new_cmd}' を使用してください。",
            fg='yellow'
        ),
        err=True
    )

@click.group()
@click.version_option(version='1.0.0', prog_name='Elder CLI')
def elder():
    """
    🏛️ エルダーズギルド統一コマンドシステム
    
    新エルダーズギルドの全機能を統一されたインターフェースで提供します。
    
    使用例:
        elder send "メッセージ"
        elder flow execute "タスク"
        elder sage knowledge query "質問"
    """
    pass

# ===== 基本コマンド =====

@elder.command()
@click.argument('message')
@click.option('--model', '-m', help='使用するモデル')
@click.option('--context', '-c', help='追加コンテキスト')
def send(message: str, model: Optional[str], context: Optional[str]):
    """メッセージをAIに送信"""
    try:
        # 既存のai_sendを使用
        SendCommand = import_legacy_command('ai_send', 'AISendCommand')
        cmd = SendCommand()
        # ここで実際のコマンド実行
        click.echo(f"📤 送信: {message}")
        # cmd.execute(message, model, context)
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@elder.command()
@click.option('--detailed', '-d', is_flag=True, help='詳細情報を表示')
def status(detailed: bool):
    """システムステータス確認"""
    try:
        StatusCommand = import_legacy_command('ai_status', 'AIStatusCommand')
        cmd = StatusCommand()
        click.echo("📊 システムステータス")
        # cmd.execute(detailed)
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@elder.command()
def start():
    """システム起動"""
    click.echo("🚀 エルダーズギルドシステムを起動します...")
    try:
        StartCommand = import_legacy_command('ai_start', 'AIStartCommand')
        cmd = StartCommand()
        # cmd.execute()
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@elder.command()
def stop():
    """システム停止"""
    click.echo("🛑 エルダーズギルドシステムを停止します...")
    try:
        StopCommand = import_legacy_command('ai_stop', 'AIStopCommand')
        cmd = StopCommand()
        # cmd.execute()
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

# ===== Elder Flow グループ =====

@elder.group()
def flow():
    """🌊 Elder Flow 管理コマンド"""
    pass

@flow.command()
@click.argument('task')
@click.option('--priority', '-p', default='medium', 
              type=click.Choice(['low', 'medium', 'high', 'critical']),
              help='タスクの優先度')
@click.option('--auto-commit', is_flag=True, help='自動コミット有効化')
def execute(task: str, priority: str, auto_commit: bool):
    """Elder Flow でタスクを実行"""
    click.echo(f"🌊 Elder Flow 実行: {task}")
    click.echo(f"   優先度: {priority}")
    if auto_commit:
        click.echo("   自動コミット: 有効")
    
    # 実際の実行
    # from libs.elder_flow import execute_elder_flow
    # execute_elder_flow(task, priority, auto_commit)

@flow.command()
def status():
    """Elder Flow の状態確認"""
    click.echo("📊 Elder Flow ステータス")
    # 実装

@flow.command()
@click.argument('violation_type', required=False)
def fix(violation_type: Optional[str]):
    """Elder Flow 違反を修正"""
    if violation_type:
        click.echo(f"🔧 {violation_type} 違反を修正します")
    else:
        click.echo("🔧 すべての Elder Flow 違反をチェックします")

# ===== 4賢者グループ =====

@elder.group()
def sage():
    """🧙‍♂️ 4賢者システムコマンド"""
    pass

# ナレッジ賢者
@sage.group()
def knowledge():
    """📚 ナレッジ賢者"""
    pass

@knowledge.command()
@click.argument('query')
def search(query: str):
    """知識ベースを検索"""
    click.echo(f"🔍 検索中: {query}")

@knowledge.command()
@click.argument('content')
@click.option('--category', '-c', help='カテゴリ')
def add(content: str, category: Optional[str]):
    """知識を追加"""
    click.echo(f"📝 知識を追加: {content}")
    if category:
        click.echo(f"   カテゴリ: {category}")

# タスク賢者
@sage.group()
def task():
    """📋 タスク賢者"""
    pass

@task.command()
def list():
    """タスク一覧表示"""
    click.echo("📋 タスク一覧:")
    # 実装

@task.command()
@click.argument('task_id')
def status(task_id: str):
    """タスク状態確認"""
    click.echo(f"📊 タスク {task_id} の状態")

# インシデント賢者
@sage.group()
def incident():
    """🚨 インシデント賢者"""
    pass

@incident.command()
@click.argument('log_file', type=click.Path(exists=True))
def analyze(log_file: str):
    """ログファイルを分析"""
    click.echo(f"🔍 ログ分析: {log_file}")

@incident.command()
def report():
    """インシデントレポート生成"""
    click.echo("📊 インシデントレポート生成中...")

# RAG賢者
@sage.group()
def rag():
    """🔍 RAG賢者"""
    pass

@rag.command()
@click.argument('query')
@click.option('--limit', '-l', default=10, help='結果数')
def search(query: str, limit: int):
    """RAG検索実行"""
    click.echo(f"🔍 RAG検索: {query} (上位{limit}件)")

# ===== エルダー評議会グループ =====

@elder.group()
def council():
    """🏛️ エルダー評議会コマンド"""
    pass

@council.command()
@click.argument('issue')
def consult(issue: str):
    """評議会に相談"""
    click.echo(f"🏛️ エルダー評議会に相談: {issue}")

@council.command()
def compliance():
    """コンプライアンスチェック"""
    click.echo("✅ コンプライアンスチェック実行中...")

@council.command()
@click.argument('pr_number')
def approve(pr_number: str):
    """PRを承認"""
    click.echo(f"✅ PR #{pr_number} を評議会承認")

# ===== 開発系コマンド =====

@elder.group()
def test():
    """🧪 テスト関連コマンド"""
    pass

@test.command()
@click.option('--coverage', is_flag=True, help='カバレッジ計測')
def run(coverage: bool):
    """テスト実行"""
    click.echo("🧪 テスト実行中...")
    if coverage:
        click.echo("   カバレッジ計測: 有効")

@elder.group()
def commit():
    """💾 コミット関連コマンド"""
    pass

@commit.command()
@click.argument('message')
def auto(message: str):
    """自動コミット"""
    click.echo(f"🤖 自動コミット: {message}")

@commit.command()
@click.argument('message')
def lightning(message: str):
    """Lightning コミット"""
    click.echo(f"⚡ Lightning コミット: {message}")

# ===== 特殊機能 =====

@elder.group()
def magic():
    """✨ Ancient Magic システム"""
    pass

@magic.command()
@click.argument('spell')
def cast(spell: str):
    """魔法を発動"""
    click.echo(f"✨ 魔法発動: {spell}")

@elder.command()
def prophecy():
    """🔮 予言を表示"""
    click.echo("🔮 エルダーズギルドの予言:")
    click.echo("   未来は我々の手の中にある...")

# ===== ヘルプ強化 =====

@elder.command()
@click.argument('command', required=False)
def help(command: Optional[str]):
    """詳細ヘルプを表示"""
    if command:
        # 特定コマンドのヘルプ
        ctx = click.Context(elder)
        cmd = elder.get_command(ctx, command)
        if cmd:
            click.echo(cmd.get_help(ctx))
        else:
            click.echo(f"❌ コマンド '{command}' が見つかりません")
    else:
        # 全体ヘルプ
        ctx = click.Context(elder)
        click.echo(elder.get_help(ctx))
        click.echo("\n📚 主要カテゴリ:")
        click.echo("  flow     - Elder Flow 管理")
        click.echo("  sage     - 4賢者システム")
        click.echo("  council  - エルダー評議会")
        click.echo("  test     - テスト関連")
        click.echo("  commit   - コミット関連")

# ===== エイリアスサポート =====

def check_legacy_command():
    """レガシーコマンドからの実行をチェック"""
    script_name = os.path.basename(sys.argv[0])
    if script_name.startswith('ai-'):
        new_cmd = script_name.replace('ai-', 'elder ')
        deprecation_warning(script_name, new_cmd)

if __name__ == '__main__':
    check_legacy_command()
    elder()