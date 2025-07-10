#!/usr/bin/env python3
"""
認証付きWebサーバー起動スクリプト
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    from web.flask_app_auth import app
    from web.flask_app_auth import create_initial_admin

    print("🚀 Elders Guild 認証付きダッシュボードを起動しています...")
    print("📝 初期管理者アカウント:")
    print("   ユーザー名: admin")
    print("   パスワード: admin123")
    print("   ※ 初回ログイン後にパスワードを変更してください")

    # 初期管理者作成
    create_initial_admin()

    # サーバー起動
    app.run(host="0.0.0.0", port=5555, debug=False)
