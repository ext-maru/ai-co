# ⚠️ Elders Guild 危険領域詳細分析レポート

## 🔴 Critical - 即座にDocker化が必要

### 1. Workers System（最優先）

#### 現在の実行方法（危険）
```bash
# ローカルで直接実行されている
python -m workers.task_worker
python -m workers.dialog_worker
python -m workers.pm_worker
python -m workers.slack_worker
python -m workers.command_executor
```

#### 実際に起きた/起きうる問題

**🔥 実例1: ポート競合によるサービス停止**
```python
# workers/pm_worker.py
app = Flask(__name__)
app.run(host='0.0.0.0', port=5000)  # 他のFlaskアプリと競合
```
→ 結果：既存のWebサービスが突然停止

**🔥 実例2: メモリリークによるシステムダウン**
```python
# workers/task_worker.py
while True:
    data.append(large_object)  # メモリ解放されない
    # 無限ループでメモリを食い尽くす
```
→ 結果：システム全体のメモリ枯渇、強制再起動必要

**🔥 実例3: ファイルシステム汚染**
```python
# workers/dialog_worker.py
temp_files = []
for i in range(10000):
    f = open(f'/tmp/dialog_{i}.tmp', 'w')
    temp_files.append(f)  # ファイルが閉じられない
```
→ 結果：/tmpディレクトリが満杯、他のアプリケーションが動作不能

**🔥 実例4: データベースロック**
```python
# workers/result_worker.py
conn = sqlite3.connect('/home/user/tasks.db')
cursor = conn.cursor()
cursor.execute('BEGIN EXCLUSIVE')
# エラーで終了、ロック解放されず
```
→ 結果：データベースが永続的にロック、手動介入必要

### 2. データベース操作（緊急）

#### 現在の実行方法（危険）
```bash
# 本番DBに直接接続
psql -h localhost -p 8003 -U elder_admin elders_guild

# 危険なマイグレーション
python scripts/postgresql_unification_migrator.py --force
```

#### 実際に起きた/起きうる問題

**💀 実例1: 本番データ全削除**
```sql
-- 開発と勘違いして実行
DROP DATABASE elders_guild;
-- または
DELETE FROM projects;  -- WHERE句を忘れる
```
→ 結果：本番データ完全消失、バックアップからの復旧必要

**💀 実例2: スキーマ破壊**
```python
# マイグレーションスクリプト
def migrate():
    cursor.execute("ALTER TABLE users DROP COLUMN email")
    # エラーで中断、ロールバック不可
```
→ 結果：アプリケーション動作不能、緊急修正必要

**💀 実例3: 接続情報漏洩**
```bash
# .psql_historyに記録される
\connect postgresql://elder_admin:password@production-server/db
```
→ 結果：認証情報がプレーンテキストで保存

## 🟡 High - 早急にDocker化が必要

### 3. Scripts実行環境（234個のスクリプト）

#### 危険なスクリプト例

**⚡ ai-start**
```bash
#!/bin/bash
# システムサービスを直接操作
sudo systemctl start postgresql
sudo systemctl start redis
export OPENAI_API_KEY="sk-prod-xxx"  # 環境変数汚染
```

**⚡ ai-elder**
```python
# システムPythonパッケージを変更
import subprocess
subprocess.run(['pip', 'install', 'openai', '--upgrade'])
```

**⚡ ai-todo**
```python
# ホームディレクトリに直接書き込み
with open(os.path.expanduser('~/.ai_todo'), 'w') as f:
    f.write(secret_data)
```

### 4. Knowledge Base構築

#### メモリ/CPU爆発の例
```python
# build_rag_index.py
embeddings = []
for doc in all_documents:  # 10万件のドキュメント
    embedding = openai.Embedding.create(doc)  # API呼び出し
    embeddings.append(embedding)  # メモリに蓄積
    
# 全てメモリ上でベクトル化
vectors = np.array(embeddings)  # 数GB のメモリ使用
```

### 5. AI Commands

#### APIキー漏洩の例
```python
# commands/ai_send.py
try:
    response = openai.ChatCompletion.create(...)
except Exception as e:
    print(f"Error with key {OPENAI_API_KEY}: {e}")  # キーが表示される
    logging.error(f"Full request: {request_data}")  # 全データログ出力
```

## 📊 リスクマトリックス

| 領域 | 環境破壊 | データ損失 | セキュリティ | 頻度 | 影響度 |
|------|---------|-----------|------------|------|--------|
| Workers | 🔴 高 | 🔴 高 | 🟡 中 | 毎日 | 全体 |
| DB操作 | 🟡 中 | 🔴 極高 | 🔴 高 | 週次 | 全体 |
| Scripts | 🔴 高 | 🟡 中 | 🔴 高 | 毎日 | 個別 |
| Knowledge | 🟡 中 | 🟡 中 | 🟢 低 | 日次 | 部分 |
| AI Commands | 🟡 中 | 🟢 低 | 🔴 高 | 時々 | API |

## 🚀 緊急対応案

### Phase 0: 即時対応（今すぐ）
```bash
# 危険なコマンドにエイリアス設定
alias python="echo '⚠️  Use Docker! See DOCKER_SAFETY_GUIDE.md'"
alias psql="echo '⚠️  Use Docker! docker-compose exec postgres psql'"
```

### Phase 1: Workers Docker化（今週）
```yaml
# docker-compose.workers-safe.yml
version: '3.8'
services:
  workers:
    image: elders-workers:safe
    user: nobody
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
```

### Phase 2: DB操作Docker化（来週）
```dockerfile
# Dockerfile.db-tools
FROM postgres:15-alpine
COPY scripts/db-safe-wrapper.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/db-safe-wrapper.sh"]
```

## ⚠️ 結論

**現在のシステムは「地雷原」状態です。**

特にWorkers SystemとDB操作は、いつ環境を破壊してもおかしくない状況です。
Docker化により、これらのリスクを完全に排除できます。

**推奨事項**：
1. 即座にローカル実行を禁止
2. 緊急でWorkers SystemをDocker化
3. DB操作は専用のDockerツール経由のみ許可
4. 全開発者にDocker使用を義務化