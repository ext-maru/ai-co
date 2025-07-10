# Elder階層ワーカーシステム クイックスタートガイド

**Elders Guild Elder Hierarchy Worker System - Quick Start Guide**

---

## 🚀 5分で始める Elder階層システム

### 1. 📦 インストール

```bash
# プロジェクトディレクトリに移動
cd /home/aicompany/ai_co

# 依存関係インストール
pip install -r requirements.txt

# 必要なパッケージが不足している場合
pip install jwt pyotp structlog aiofiles --break-system-packages
```

### 2. 🔑 認証システムの初期化

```python
from libs.unified_auth_provider import create_demo_auth_system, AuthRequest

# デモ認証システム作成
auth_system = create_demo_auth_system()

# 利用可能なユーザー確認
print("利用可能なユーザー:")
print("- grand_elder (password: grand_elder_password)")
print("- claude_elder (password: claude_elder_password)")
print("- task_sage (password: task_password)")
print("- servant1 (password: servant_password)")
```

### 3. 🔐 基本認証

```python
# Claude Elderとして認証
auth_request = AuthRequest(
    username="claude_elder",
    password="claude_elder_password"
)

result, session, user = auth_system.authenticate(auth_request)
print(f"認証結果: {result}")
print(f"ユーザー: {user.username} ({user.elder_role.value})")
```

### 4. ⚡ ワーカー起動

```python
from workers.elder_enhanced_task_worker import create_elder_task_worker

# タスクワーカー作成
task_worker = create_elder_task_worker(auth_provider=auth_system)

# コンテキスト作成
context = task_worker.create_elder_context(
    user=user,
    session=session,
    task_id="quickstart_001",
    priority=task_worker.ElderTaskPriority.HIGH
)

# タスク実行
task_data = {
    "prompt": "Hello Elder Hierarchy System!",
    "task_type": "general"
}

async def run_task():
    async def execute():
        return await task_worker.process_elder_task_message(context, task_data)
    
    result = await task_worker.execute_with_elder_context(context, execute)
    print(f"タスク結果: {result.status}")
    return result

# 実行
import asyncio
result = asyncio.run(run_task())
```

### 5. 🎯 デモ実行

```bash
# システムデモ実行
python3 tests/demo/elder_system_demo.py

# セキュリティテスト実行
python3 tests/security/elder_penetration_test.py
```

---

## 📋 主要コマンド

### 認証テスト
```bash
python3 -c "
from libs.unified_auth_provider import create_demo_auth_system, AuthRequest
auth = create_demo_auth_system()
result, session, user = auth.authenticate(AuthRequest('claude_elder', 'claude_elder_password'))
print(f'認証成功: {user.username} ({user.elder_role.value})')
"
```

### ワーカー状態確認
```bash
python3 -c "
from libs.unified_auth_provider import create_demo_auth_system
from workers.elder_enhanced_task_worker import create_elder_task_worker
auth = create_demo_auth_system()
worker = create_elder_task_worker(auth_provider=auth)
print(f'ワーカータイプ: {worker.worker_type}')
print(f'ワーカーID: {worker.worker_id}')
"
```

### セキュリティチェック
```bash
python3 -m pytest tests/security/elder_penetration_test.py -v
```

---

## 🔧 一般的な使用例

### 1. 権限チェック

```python
from libs.unified_auth_provider import ElderRole

# 権限確認
if auth_system.check_elder_permission(user, ElderRole.SAGE):
    print("Sage権限あり")
else:
    print("Sage権限なし")
```

### 2. セッション管理

```python
# セッション検証
is_valid, session, user = auth_system.validate_token(session.token)
if is_valid:
    print(f"セッション有効: {session.expires_at}")
else:
    print("セッション無効")
```

### 3. MFA有効化

```python
# MFA有効化
provisioning_uri = auth_system.enable_mfa_for_user("claude_elder")
print(f"MFA設定URI: {provisioning_uri}")
```

---

## 🚨 トラブルシューティング

### よくある問題

1. **ModuleNotFoundError**
   ```bash
   pip install [missing_package] --break-system-packages
   ```

2. **認証失敗**
   ```python
   # パスワード確認
   print("正しいパスワードを使用してください:")
   print("claude_elder: claude_elder_password")
   ```

3. **権限エラー**
   ```python
   # 権限確認
   print(f"現在の権限: {user.elder_role.value}")
   print(f"必要な権限: sage以上")
   ```

---

## 📚 次のステップ

1. **[完全ガイド](ELDER_HIERARCHY_WORKER_SYSTEM.md)** - 詳細な機能説明
2. **[API リファレンス](ELDER_HIERARCHY_WORKER_SYSTEM.md#apiリファレンス)** - API使用方法
3. **[セキュリティ](ELDER_HIERARCHY_WORKER_SYSTEM.md#セキュリティ機能)** - セキュリティ機能詳細
4. **[開発者ガイド](ELDER_HIERARCHY_WORKER_SYSTEM.md#開発者向けガイド)** - カスタムワーカー開発

---

**🏛️ Elders Guild Elder Hierarchy Worker System**  
**📞 サポート: support@eldersguild.com**