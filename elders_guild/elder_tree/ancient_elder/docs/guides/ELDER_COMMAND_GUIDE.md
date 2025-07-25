# 📖 Elder Command 完全ガイド

**バージョン**: 1.0.0  
**最終更新**: 2025年7月24日  
**対象**: 新エルダーズギルド開発者

---

## 🚀 クイックスタート

### インストール
```bash
# セットアップスクリプト実行
./elder_tree/elder_servants/dwarf_tribe/tools/setup-elder-commands.sh

# 確認
elder --version
elder help
```

### 基本的な使い方
```bash
# AIとの対話
elder send "OAuth2.0認証を実装して"

# システム管理
elder status              # 状態確認
elder start              # システム起動
elder stop               # システム停止

# ヘルプ
elder help               # 全体ヘルプ
elder help flow          # カテゴリヘルプ
elder flow execute --help # コマンドヘルプ
```

---

## 🏗️ コマンド体系

### **階層構造**
```
elder [カテゴリ] [サブカテゴリ] [アクション] [引数] [オプション]
```

### **例**
```bash
elder sage knowledge search "エラー解決方法"
#     ^^^^ ^^^^^^^^^ ^^^^^^ ^^^^^^^^^^^^^^^
#     カテゴリ サブ   アクション  引数
```

---

## 📚 カテゴリ別コマンドリファレンス

### **🌊 Elder Flow (`elder flow`)**

Elder Flow システムの管理

```bash
# タスク実行
elder flow execute "タスク説明" [options]
  --priority, -p    優先度 (low/medium/high/critical)
  --auto-commit     自動コミット有効化
  --no-quality      品質チェックスキップ（非推奨）

# 状態確認
elder flow status
  --active          アクティブなフローのみ
  --detailed, -d    詳細表示

# 違反修正
elder flow fix [violation-type]
  identity          アイデンティティ違反
  abstract          抽象メソッド違反
  all              すべての違反（デフォルト）

# パイプライン
elder flow pipeline create "パイプライン名"
elder flow pipeline run <pipeline-id>
elder flow pipeline list
```

### **🧙‍♂️ 4賢者システム (`elder sage`)**

4賢者への相談・情報取得

#### 📚 ナレッジ賢者
```bash
elder sage knowledge search "検索クエリ"
  --limit, -l       結果数（デフォルト: 10）
  --category, -c    カテゴリ絞り込み

elder sage knowledge add "新しい知識" 
  --category, -c    カテゴリ指定
  --tags, -t        タグ（カンマ区切り）

elder sage knowledge update <knowledge-id>
elder sage knowledge list
  --recent          最近の知識
  --popular         人気の知識
```

#### 📋 タスク賢者
```bash
elder sage task list
  --status, -s      ステータスフィルタ (pending/running/done)
  --priority, -p    優先度フィルタ

elder sage task status <task-id>
  --detailed, -d    詳細表示

elder sage task create "タスク内容"
  --priority, -p    優先度
  --assign, -a      担当者

elder sage task update <task-id>
  --status, -s      ステータス変更
  --priority, -p    優先度変更
```

#### 🚨 インシデント賢者
```bash
elder sage incident analyze <log-file>
  --severity, -s    重要度フィルタ
  --recent, -r      直近N件

elder sage incident report
  --format, -f      出力形式 (text/json/html)
  --period, -p      期間 (daily/weekly/monthly)

elder sage incident predict
  --threshold, -t   予測閾値
```

#### 🔍 RAG賢者
```bash
elder sage rag search "検索クエリ"
  --limit, -l       結果数
  --similarity, -s  類似度閾値

elder sage rag index <path>
  --recursive, -r   再帰的インデックス
  --update, -u      既存インデックス更新
```

### **🏛️ エルダー評議会 (`elder council`)**

重要な意思決定・承認

```bash
elder council consult "相談内容"
  --urgent          緊急相談
  --category, -c    相談カテゴリ

elder council compliance
  --check           チェックのみ
  --fix             自動修正提案

elder council approve <item-type> <item-id>
  pr                プルリクエスト
  design            設計
  architecture      アーキテクチャ

elder council review <pr-number>
  --detailed, -d    詳細レビュー
  --quick, -q       クイックレビュー
```

### **🧪 開発ツール (`elder test`, `elder commit`)**

#### テスト関連
```bash
elder test run [path]
  --coverage, -c    カバレッジ計測
  --watch, -w       ファイル監視モード
  --parallel, -p    並列実行

elder test coverage
  --html            HTMLレポート生成
  --threshold, -t   閾値チェック

elder test generate <module>
  --tdd             TDDスタイル
```

#### コミット関連
```bash
elder commit auto "コミットメッセージ"
  --no-verify       フック無視
  --amend           前回修正

elder commit lightning "メッセージ"
  --push            即プッシュ

elder commit council "メッセージ"
  --reviewers, -r   レビュアー指定
```

### **⚙️ システム管理**

```bash
# ワーカー管理
elder worker scale <up|down> <count>
elder worker status
elder worker restart <worker-id>

# 設定管理
elder config edit
elder config get <key>
elder config set <key> <value>

# 監視
elder monitor
  --metrics, -m     メトリクス表示
  --alerts, -a      アラート表示

# ログ
elder logs [service]
  --follow, -f      リアルタイム追跡
  --lines, -n       行数指定
```

### **✨ 特殊機能**

```bash
# Ancient Magic
elder magic cast <spell-name>
elder magic list
elder magic learn <spell-file>

# 予言システム
elder prophecy show
  --next-features   次期機能予測
  --timeline        タイムライン表示

# NWO ビジョン
elder nwo vision
  --stats           統計情報
  --forecast        予測情報
```

---

## 🎨 高度な使用法

### **パイプライン処理**
```bash
# 品質チェックパイプライン
elder flow execute "実装" | elder flow pipeline quality | elder sage judge

# 複数賢者協調
elder sage knowledge search "OAuth" | elder sage rag enhance | elder council review
```

### **バッチ処理**
```bash
# 複数ファイルの品質チェック
find . -name "*.py" | xargs -I {} elder flow check {}

# 一括タスク作成
cat tasks.txt | while read task; do elder sage task create "$task"; done
```

### **スクリプト統合**
```python
#!/usr/bin/env python3
import subprocess

def elder_command(cmd):
    """Elder コマンド実行"""
    result = subprocess.run(
        f"elder {cmd}", 
        shell=True, 
        capture_output=True, 
        text=True
    )
    return result.stdout

# 使用例
response = elder_command("sage knowledge search 'Python best practices'")
print(response)
```

---

## 🔧 設定とカスタマイズ

### **設定ファイル**
```yaml
# ~/.elder/config.yml
default_priority: medium
auto_commit: false
quality_threshold: 90

aliases:
  s: send
  f: flow
  t: test

shortcuts:
  daily: "flow execute 'デイリータスク処理' --priority high"
```

### **環境変数**
```bash
export ELDER_HOME=/home/user/.elder
export ELDER_LOG_LEVEL=INFO
export ELDER_DEFAULT_MODEL=gpt-4
```

### **プラグイン**
```bash
# プラグインインストール
elder plugin install <plugin-name>

# プラグイン一覧
elder plugin list

# プラグイン設定
elder plugin config <plugin-name>
```

---

## 🐛 トラブルシューティング

### **よくある問題**

#### コマンドが見つからない
```bash
# PATHを確認
echo $PATH | grep -q /usr/local/bin || echo "PATH設定が必要"

# 再インストール
./elder_tree/elder_servants/dwarf_tribe/tools/setup-elder-commands.sh
```

#### 権限エラー
```bash
# 実行権限付与
chmod +x /usr/local/bin/elder

# sudo が必要な場合
sudo elder [command]  # 非推奨、なるべく避ける
```

#### レガシーコマンドの警告
```bash
# 警告を無視（非推奨）
export ELDER_NO_DEPRECATION_WARNING=1

# 正しい方法：新コマンドを使う
elder send "hello"  # ai-send の代わり
```

### **デバッグモード**
```bash
# 詳細ログ出力
export ELDER_LOG_LEVEL=DEBUG
elder --debug [command]

# ドライラン
elder --dry-run flow execute "テスト"
```

---

## 📊 コマンド対応表

| 旧コマンド (ai-*) | 新コマンド (elder) |
|-----------------|------------------|
| ai-send | elder send |
| ai-status | elder status |
| ai-elder-flow | elder flow execute |
| ai-elder-council | elder council consult |
| ai-test | elder test run |
| ai-commit-auto | elder commit auto |
| ai-logs | elder logs |
| ai-config | elder config edit |
| ai-rag | elder sage rag search |
| ai-prophecy | elder prophecy show |

---

## 🎯 ベストプラクティス

1. **カテゴリを活用**: 関連コマンドはカテゴリでグループ化
2. **Tab補完を使う**: 効率的なコマンド入力
3. **ヘルプを読む**: `--help` で詳細オプション確認
4. **エイリアス設定**: よく使うコマンドは短縮形を設定
5. **パイプライン活用**: 複数コマンドを組み合わせて強力な処理

---

## 🔗 関連ドキュメント

- [新エルダーズギルド概要](../NEW_ELDERS_GUILD_OVERVIEW.md)
- [AI意思決定者パラダイム](../philosophy/AI_DECISION_MAKER_PARADIGM.md)
- [Elder Command統一計画](../proposals/ELDER_COMMAND_UNIFICATION_PLAN.md)

---

**"Unified Commands, Unified Vision"**  
*- Elder Command System -*