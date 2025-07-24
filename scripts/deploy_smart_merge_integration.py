#!/usr/bin/env python3
"""
🚀 スマートマージシステム統合デプロイメントスクリプト

enhanced_auto_issue_processorにスマートマージ機能を統合します。
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_header(message):
    """ヘッダーメッセージを表示"""
    print("\n" + "=" * 60)
    print(f"🔧 {message}")
    print("=" * 60)

def check_environment():
    """環境チェック"""
    print_header("環境チェック")
    
    # Python バージョン
    print(f"✅ Python {sys.version.split()[0]}")
    
    # GitHub トークン
    if os.environ.get("GITHUB_TOKEN"):
        print("✅ GITHUB_TOKEN 設定済み")
    else:
        print("❌ GITHUB_TOKEN が設定されていません")
        return False
    
    # リポジトリ情報
    repo = os.environ.get("GITHUB_REPOSITORY", "ext-maru/ai-co")
    print(f"✅ リポジトリ: {repo}")
    
    return True

def check_dependencies():
    """依存関係チェック"""
    print_header("依存関係チェック")
    
    required_libs = [
        ("github", "PyGithub"),      # PyGithub
        ("git", "GitPython"),        # GitPython
        ("aiohttp", "aiohttp"),      # 非同期HTTP
    ]
    
    missing = []
    for lib, package_name in required_libs:
        try:
            __import__(lib)
            print(f"✅ {package_name} インストール済み")
        except ImportError:
            print(f"⚠️ {package_name} が見つかりません（オプション）")
            missing.append(package_name)
    
    if missing:
        print("\n💡 推奨: 以下のライブラリをインストールすると機能が向上します:")
        print(f"pip install {' '.join(missing)}")
        print("\n※ ただし、基本機能は動作します")
    
    return True  # 必須ではないので常にTrue

def validate_integration():
    """統合の検証"""
    print_header("統合検証")
    
    # ファイル存在チェック
    files = [
        "libs/integrations/github/enhanced_auto_issue_processor.py",
        "libs/integrations/github/enhanced_merge_system_v2.0py",
        "libs/integrations/github/smart_merge_retry.py",
        "libs/integrations/github/pr_state_monitor.py",
        "libs/integrations/github/improved_conflict_analyzer.py",
        "libs/integrations/github/branch_updater.py"
    ]
    
    project_root = Path(__file__).parent.parent
    all_exist = True
    
    for file in files:
        file_path = project_root / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} が見つかりません")
            all_exist = False
    
    return all_exist

def create_test_script():
    """テストスクリプトの作成"""
    print_header("テストスクリプト作成")
    
    test_script = """#!/usr/bin/env python3
import asyncio
import os
from libs.integrations.github.enhanced_auto_issue_processor import EnhancedAutoIssueProcessor

async def test_integration():
    \"\"\"統合テスト\"\"\"
    print("🧪 統合テスト開始...")
    
    # プロセッサ初期化
    processor = EnhancedAutoIssueProcessor()
    
    # スマートマージシステムが初期化可能か確認
    if processor.conflict_resolution_enabled:
        print("✅ コンフリクト解決機能: 有効")
    else:
        print("❌ コンフリクト解決機能: 無効")
    
    print("✅ 統合テスト完了")

if __name__ == "__main__":
    asyncio.run(test_integration())
"""
    
    test_path = Path("test_smart_merge_integration.py")
    test_path.write_text(test_script)
    test_path.chmod(0o755)
    print(f"✅ テストスクリプト作成: {test_path}")
    
    return test_path

def create_usage_doc():
    """使用方法ドキュメントの作成"""
    print_header("ドキュメント作成")
    
    doc_content = f"""# スマートマージシステム統合ガイド

## 概要
enhanced_auto_issue_processorにスマートマージ機能が統合されました。
PRが作成されると自動的にマージを試行します。

## 機能
- **自動マージ試行**: PR作成後、自動的にマージを試行
- **スマートリトライ**: CI待機、ブランチ更新などを自動処理
- **コンフリクト解決**: 安全なコンフリクトは自動解決
- **進捗レポート**: イシューコメントで状況を報告

## 使用方法

### 1.0 環境変数設定
```bash
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="owner/repo"
```

### 2.0 実行
```bash
python3 -m libs.integrations.github.enhanced_auto_issue_processor
```

### 3.0 動作確認
- イシューが自動処理される
- PRが作成される
- スマートマージが自動実行される
- 結果がイシューにコメントされる

## 設定

### コンフリクト解決を無効化
```python
processor = EnhancedAutoIssueProcessor()
processor.conflict_resolution_enabled = False
```

### マージ監視時間の調整
```python
# _attempt_smart_merge メソッド内
merge_result = await self.smart_merge_system.handle_pull_request(
    pr_number=pr.number,
    monitoring_duration=600,  # 10分間監視
    auto_merge=True
)
```

## トラブルシューティング

### マージが失敗する場合
1.0 ブランチ保護ルールを確認
2.0 CI/CDの設定を確認
3.0 権限設定を確認

### ログの確認
```bash
# 詳細ログを有効化
export LOG_LEVEL=DEBUG
```

作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    doc_path = Path("docs/SMART_MERGE_INTEGRATION_GUIDE.md")
    doc_path.parent.mkdir(exist_ok=True)
    doc_path.write_text(doc_content)
    print(f"✅ ドキュメント作成: {doc_path}")

def main():
    """メイン処理"""
    print("\n🚀 スマートマージシステム統合デプロイメント")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # チェック実行
    if not check_environment():
        print("\n❌ 環境チェック失敗")
        return 1
    
    if not check_dependencies():
        print("\n❌ 依存関係チェック失敗")
        return 1
    
    if not validate_integration():
        print("\n❌ 統合検証失敗")
        return 1
    
    # テストとドキュメント作成
    test_script = create_test_script()
    create_usage_doc()
    
    print_header("統合完了")
    print("✅ スマートマージシステムの統合が完了しました！")
    print("\nテスト実行:")
    print(f"  python3 {test_script}")
    print("\n使用方法:")
    print("  python3 -m libs.integrations.github.enhanced_auto_issue_processor")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())