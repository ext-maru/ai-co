# 🔧 Ancient Magic System トラブルシューティングガイド

**最終更新**: 2025-07-21  
**作成者**: クロードエルダー（Claude Elder）

## 📋 目次

1. [よくあるエラーと解決方法](#よくあるエラーと解決方法)
2. [パフォーマンス問題](#パフォーマンス問題)
3. [環境設定の問題](#環境設定の問題)
4. [監査結果の問題](#監査結果の問題)
5. [デバッグ手法](#デバッグ手法)
6. [既知の問題と回避策](#既知の問題と回避策)

## 🚨 よくあるエラーと解決方法

### 1. ImportError: No module named 'libs.ancient_elder'

**症状**:
```
ImportError: No module named 'libs.ancient_elder'
```

**原因**: Pythonパスが正しく設定されていない

**解決方法**:
```bash
# プロジェクトルートから実行
cd /home/aicompany/ai_co
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# または、スクリプトを使用
./scripts/ai-ancient-magic list
```

### 2. AttributeError: 'AncientElderIntegrityAuditor' object has no attribute 'name'

**症状**:
```
AttributeError: 'AncientElderIntegrityAuditor' object has no attribute 'name'
```

**原因**: 古いバージョンの実装を使用している

**解決方法**:
```bash
# 最新のコードを取得
git pull origin main

# キャッシュをクリア
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

### 3. asyncio TimeoutError

**症状**:
```
asyncio.TimeoutError
Command timed out after 2m 0.0s
```

**原因**: TDD Guardianが大規模プロジェクトで時間がかかりすぎる

**解決方法**:
```bash
# 個別の魔法を実行（TDDをスキップ）
ai-ancient-magic single integrity --target .
ai-ancient-magic single git --target .
ai-ancient-magic single flow --target .

# または小さなディレクトリを対象に
ai-ancient-magic audit --target ./src/specific_module
```

### 4. Git関連エラー

**症状**:
```
Git log failed: fatal: not a git repository
```

**原因**: Gitリポジトリ外で実行している

**解決方法**:
```bash
# Gitリポジトリに移動
cd /path/to/your/git/repo

# またはGit関連チェックをスキップ（未実装）
# 現在は個別実行で回避
ai-ancient-magic single integrity --target .
```

### 5. Permission Denied

**症状**:
```
PermissionError: [Errno 13] Permission denied: '/home/aicompany/ai_co/scripts/ai-ancient-magic'
```

**原因**: 実行権限がない

**解決方法**:
```bash
# 実行権限を付与
chmod +x /home/aicompany/ai_co/scripts/ai-ancient-magic

# または直接Python実行
python3 /home/aicompany/ai_co/commands/ai_ancient_magic.py list
```

## ⚡ パフォーマンス問題

### 1. 監査が遅い

**症状**: 監査に数分以上かかる

**解決方法**:

#### a) 対象を限定
```bash
# 特定のディレクトリのみ
ai-ancient-magic audit --target ./src/core

# 特定の魔法のみ
ai-ancient-magic single git --target .
```

#### b) キャッシュを活用
```python
# Pythonスクリプトで実行
from libs.ancient_elder.audit_cache import AuditCache, CachedAuditEngine

cache = AuditCache(ttl_hours=48)  # 48時間キャッシュ
# 2回目以降は高速
```

#### c) 並列度を調整
```bash
# CPUコア数を確認
nproc

# 環境変数で並列度を制限（未実装のため効果なし）
export ANCIENT_MAGIC_WORKERS=2
```

### 2. メモリ使用量が多い

**症状**: メモリ不足エラー

**解決方法**:
```bash
# メモリ使用量を監視しながら実行
/usr/bin/time -v ai-ancient-magic audit

# 部分的に実行
for dir in src tests docs; do
    echo "Auditing $dir..."
    ai-ancient-magic audit --target ./$dir
done
```

## 🛠️ 環境設定の問題

### 1. Python バージョン

**要件**: Python 3.8以上

**確認方法**:
```bash
python3 --version
```

**解決方法**:
```bash
# Python 3.12をインストール（推奨）
sudo apt update
sudo apt install python3.12 python3.12-venv
```

### 2. 依存パッケージ

**必要なパッケージ**:
- click
- asyncio（標準ライブラリ）
- pathlib（標準ライブラリ）

**インストール**:
```bash
pip install click
```

### 3. 環境変数

**設定可能な環境変数**:
```bash
# デバッグモード
export ANCIENT_MAGIC_DEBUG=1

# キャッシュディレクトリ
export ANCIENT_MAGIC_CACHE_DIR="$HOME/.cache/ancient_magic"

# タイムアウト（秒）
export ANCIENT_MAGIC_TIMEOUT=300
```

## 📊 監査結果の問題

### 1. Health Scoreが0

**症状**: 常にHealth Scoreが0になる

**原因**: 監査エラーまたは違反が多すぎる

**解決方法**:
```bash
# 詳細を確認
ai-ancient-magic audit --comprehensive --output debug.json
cat debug.json | jq '.all_violations[] | {severity, title}'
```

### 2. 違反が検出されない

**症状**: 明らかな問題があるのに違反が0

**原因**: 簡易実装のため一部の監査が機能していない

**解決方法**:
```bash
# Git Chronicleは実装済みなので動作確認
ai-ancient-magic single git --target .

# 他の監査は簡易実装
# 実際の違反検出は限定的
```

## 🐛 デバッグ手法

### 1. 詳細ログの有効化

```bash
# Pythonログレベルを設定
export PYTHONUNBUFFERED=1
python3 -u /home/aicompany/ai_co/commands/ai_ancient_magic.py audit 2>&1 | tee debug.log
```

### 2. 個別コンポーネントのテスト

```python
# Python REPLで個別テスト
python3
>>> from libs.ancient_elder.git_chronicle_impl import GitChronicleImpl
>>> impl = GitChronicleImpl()
>>> result = impl.analyze_commit_messages(days=7)
>>> print(result)
```

### 3. プロファイリング

```bash
# 実行時間の詳細を確認
python3 -m cProfile -s cumulative /home/aicompany/ai_co/commands/ai_ancient_magic.py health
```

### 4. スタックトレースの取得

```bash
# エラー時の詳細情報
python3 -m traceback /home/aicompany/ai_co/commands/ai_ancient_magic.py audit
```

## ⚠️ 既知の問題と回避策

### 1. TDD Guardian タイムアウト

**問題**: 大規模プロジェクトでTDD Guardianがタイムアウトする

**回避策**:
```bash
# TDD以外の監査を実行
for magic in integrity git flow sages servant; do
    ai-ancient-magic single $magic --target .
done
```

### 2. マージコンフリクトの誤検出

**問題**: .venvディレクトリ内のファイルもチェックしてしまう

**回避策**:
```bash
# .gitignoreに追加
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### 3. Conventional Commits の厳密すぎる判定

**問題**: 絵文字付きコミットが違反扱いになる

**現状**: 仕様通りの動作（絵文字は標準外）

**推奨**:
```bash
# 標準フォーマットを使用
git commit -m "feat: add new feature"
# 絵文字は使わない
```

### 4. キャッシュの不整合

**問題**: 古いキャッシュが残って正しい結果が出ない

**解決方法**:
```python
# キャッシュをクリア
from libs.ancient_elder.audit_cache import AuditCache
cache = AuditCache()
cache.clear()  # 全キャッシュクリア
```

## 🔍 詳細な調査方法

### ログファイルの場所
```bash
# システムログ
journalctl -u ancient-magic

# アプリケーションログ
~/.ancient_magic_cache/logs/

# 一時ファイル
/tmp/ancient_magic_*
```

### デバッグ用コマンド
```bash
# 依存関係の確認
pip list | grep -E "(click|pytest|asyncio)"

# ファイル権限の確認
ls -la /home/aicompany/ai_co/scripts/ai-ancient-magic
ls -la /home/aicompany/ai_co/libs/ancient_elder/

# プロセスの確認
ps aux | grep ancient
```

## 📞 サポート連絡先

解決しない問題は：

1. エラーログを収集
2. 実行環境の情報を記録
3. [GitHub Issue](https://github.com/ext-maru/ai-co/issues)で報告

**情報収集スクリプト**:
```bash
#!/bin/bash
echo "=== Environment Info ==="
echo "Date: $(date)"
echo "Python: $(python3 --version)"
echo "PWD: $(pwd)"
echo "Git branch: $(git branch --show-current)"
echo ""
echo "=== Error Log ==="
ai-ancient-magic audit 2>&1
```

---

**Remember: Every problem has a solution! 🏛️**