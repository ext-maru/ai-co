# AI Company Web Dashboard with Authentication

## 🚀 概要

AI Company の認証機能付きWebダッシュボードです。タスク管理、ワーカー監視、キュー管理、4賢者システムの状態確認などが可能です。

## ✨ 実装済み機能

### 認証システム
- ✅ ユーザー認証（ログイン/ログアウト）
- ✅ セッション管理
- ✅ Remember Me機能
- ✅ パスワードハッシュ化（bcrypt）
- ✅ CSRF保護
- ✅ ロールベースアクセス制御（管理者/一般ユーザー）
- ✅ JWTトークン対応（オプション）

### ダッシュボード機能
- ✅ システム概要（CPU、メモリ、稼働時間）
- ✅ タスク管理（作成、更新、削除）
- ✅ ワーカー監視（状態、CPU使用率、メモリ）
- ✅ メッセージキュー監視
- ✅ 4賢者システム状態表示
- ✅ 管理者用機能（ユーザー管理、システム設定）

### API機能
- ✅ RESTful API（認証付き）
- ✅ リアルタイム更新（5秒間隔）
- ✅ エラーハンドリング

## 📁 ファイル構造

```
web/
├── auth_manager.py          # 認証システムコア
├── flask_app_auth.py        # 認証付きFlaskアプリ
├── start_auth_server.py     # サーバー起動スクリプト
├── templates/
│   ├── auth/
│   │   └── login.html      # ログインページ
│   └── dashboard.html      # メインダッシュボード
├── static/
│   ├── css/
│   │   ├── auth.css        # 認証画面スタイル
│   │   └── dashboard.css   # ダッシュボードスタイル
│   └── js/
│       └── dashboard.js    # ダッシュボードJavaScript
└── README_AUTH.md          # このファイル
```

## 🚀 起動方法

### 1. 依存関係のインストール

```bash
# 仮想環境を有効化
source venv/bin/activate

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 2. サーバー起動

```bash
# 簡単な起動方法
./test_auth_web.py

# または直接起動
python web/start_auth_server.py
```

### 3. ブラウザでアクセス

```
http://localhost:5555
```

## 🔐 初期ログイン情報

- **ユーザー名**: admin
- **パスワード**: admin123

⚠️ **重要**: 初回ログイン後、必ずパスワードを変更してください。

## 📝 使い方

### ログイン
1. ブラウザで http://localhost:5555 にアクセス
2. 初期アカウントでログイン
3. ダッシュボードが表示されます

### タスク管理
1. サイドバーの「タスク管理」をクリック
2. 「新規タスク作成」ボタンをクリック
3. タイトル、説明、優先度、担当者を入力
4. 「作成」をクリック

### ワーカー監視
- サイドバーの「ワーカー」をクリック
- 各ワーカーの状態、CPU使用率、メモリ使用量を確認

### 管理者機能
管理者権限を持つユーザーのみ利用可能：
- ユーザー管理
- 期限切れセッションのクリア
- ワーカーの再起動

## 🔧 カスタマイズ

### 新規ユーザーの追加（プログラム的に）

```python
from web.auth_manager import AuthManager

auth_manager = AuthManager()
user = auth_manager.create_user(
    username="new_user",
    email="user@example.com",
    password="secure_password",
    role="user"  # または "admin"
)
```

### JWTトークン認証の有効化

```python
# flask_app_auth.py で設定
auth_manager = AuthManager(
    db_path='auth.db',
    secret_key='your_secret_key',
    use_jwt=True  # JWTを有効化
)
```

## 🛡️ セキュリティ機能

1. **パスワードセキュリティ**
   - bcryptによるハッシュ化
   - パスワード強度検証
   - 8文字以上、英数字必須

2. **セッション管理**
   - セキュアなトークン生成
   - 自動セッション期限切れ（24時間）
   - ログアウト時のセッション削除

3. **CSRF保護**
   - Flask-WTFによるCSRFトークン
   - すべてのPOSTリクエストで検証

4. **アクセス制御**
   - ロールベース（admin/user）
   - APIエンドポイントの保護
   - 管理者専用機能の制限

## 🔍 トラブルシューティング

### ログインできない
- ユーザー名とパスワードを確認
- データベースファイル（data/auth.db）が存在するか確認
- サーバーログでエラーを確認

### ダッシュボードが表示されない
- JavaScriptが有効になっているか確認
- ブラウザのコンソールでエラーを確認
- APIエンドポイントが正常に動作しているか確認

### セッションがすぐに切れる
- セッションの有効期限を延長：
  ```python
  Session(user_id=1, duration_hours=48)  # 48時間に延長
  ```

## 📊 今後の改善案

1. **UI/UX改善**
   - ダークモード対応
   - レスポンシブデザイン強化
   - リアルタイムグラフ表示

2. **機能追加**
   - メール通知
   - 2要素認証
   - APIキー認証
   - WebSocket対応

3. **パフォーマンス**
   - キャッシング実装
   - 非同期処理
   - データベース最適化

## 📝 開発者向け情報

### テスト実行

```bash
pytest tests/unit/test_web_auth.py -v
```

### 新しいAPIエンドポイントの追加

```python
@app.route('/api/new-endpoint')
@login_required  # 認証必須
def api_new_endpoint():
    user = get_current_user()
    # 処理を実装
    return jsonify({'result': 'success'})
```

### カスタムデコレーターの作成

```python
def custom_permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or not user.has_permission(permission):
                return jsonify({'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

🎯 **開発者**: AI Company Development Team
📅 **最終更新**: 2025年7月8日