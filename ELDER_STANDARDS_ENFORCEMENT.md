# 🏛️ エルダーズギルド開発標準自動適用システム

## 📋 概要

エルダー評議会の決定により、すべての開発において以下の標準が自動的に適用されます：

1. **CO-STAR文書化フレームワーク**
2. **TDD（テスト駆動開発）必須**
3. **PDCAサイクル自動化**
4. **GUI開発標準**
5. **エルダーデコレーター使用**

## 🚀 セットアップ

### 1. 初期設定（1回のみ）

```bash
# セットアップスクリプト実行
python scripts/setup_elder_precommit.py

# または手動でインストール
pip install pre-commit
pre-commit install
pre-commit install --hook-type post-commit
```

### 2. 設定確認

```bash
# インストール状態確認
pre-commit --version

# フック確認
ls -la .git/hooks/
```

## 🔧 使用方法

### 通常の開発フロー

```bash
# 1. コード変更
vim your_file.py

# 2. ステージング
git add .

# 3. コミット（自動チェック実行）
git commit -m "feat: 新機能追加"

# → 自動的に以下が実行されます：
#   - エルダー開発標準チェック
#   - TDD準拠確認
#   - インシデント予測
#   - PDCAトラッキング更新
```

### 手動チェック

```bash
# 全ファイルチェック
pre-commit run --all-files

# 特定ファイルチェック
pre-commit run --files path/to/file.py

# エルダー標準チェックのみ
python scripts/check_elder_standards.py

# 詳細出力付き
python scripts/check_elder_standards.py --verbose
```

## 📊 チェック項目詳細

### 1. CO-STAR文書チェック

- `COSTAR*.md` または `costar*.md` ファイルの存在確認
- 必須セクション（Context, Objective, Style, Tone, Audience, Response）の確認
- 不足時は自動でテンプレート生成

### 2. TDD準拠チェック

- 変更されたPythonファイルに対応するテストファイルの存在確認
- テストファイル探索パス：
  - `tests/unit/test_*.py`
  - `tests/integration/test_*.py`
  - 同一ディレクトリの `test_*.py`

### 3. PDCAトラッキング

- `.pdca/` ディレクトリの自動作成
- コミット情報の記録
- 改善点の自動収集

### 4. GUI標準チェック

- TSX/JSXファイルのエルダー標準適合性確認
- エルダーコンポーネント使用確認

### 5. エルダーデコレーター

- `@incident_aware` デコレーターの使用推奨
- `@pdca_aware` デコレーターの使用推奨

## 🚨 エラー対処法

### チェック失敗時

```bash
❌ エルダーズ開発標準: 不合格

# 自動修正を試行
python scripts/check_elder_standards.py --fix

# または手動で修正後、再度コミット
git commit -m "fix: エルダー標準準拠"
```

### 緊急時のスキップ（推奨しません）

```bash
# チェックをスキップしてコミット
git commit --no-verify -m "hotfix: 緊急修正"

# ただし、後で必ず標準に準拠させること
```

## 🎯 リスクスコア

インシデント予測システムによるリスク評価：

| スコア | 意味 | アクション |
|--------|------|------------|
| 0.0-0.3 | 低リスク | コミット可能 |
| 0.3-0.5 | 中リスク | 警告表示 |
| 0.5-0.7 | 高リスク | 要確認 |
| 0.7-1.0 | 危険 | コミット拒否 |

## 📈 効果測定

### 自動記録される指標

- チェック実行回数
- 失敗率と原因分析
- 改善提案の実装率
- 開発速度の変化

### ログ確認

```bash
# チェック履歴
cat logs/precommit_checks.json | jq '.'

# PDCA履歴
cat .pdca/pdca_tracking.json | jq '.'
```

## 🔄 継続的改善

### 週次レポート

```bash
# PDCAサイクル分析
python libs/pdca_automation_engine.py --analyze-weekly

# 改善提案生成
python libs/pdca_automation_engine.py --generate-improvements
```

### 月次見直し

エルダー評議会による標準見直し：

1. 効果測定結果の評価
2. 新しいベストプラクティスの採用
3. ツールのアップデート

## 🏛️ エルダー評議会推奨事項

### 品質第一の実現

1. **予防的品質管理**: 問題を事前に検出
2. **自動化による一貫性**: 人的ミスの排除
3. **継続的学習**: PDCAサイクルによる改善

### チーム文化の醸成

1. **透明性**: すべてのチェック結果を共有
2. **協調性**: 問題を個人でなくチームで解決
3. **成長志向**: 失敗から学び、システムを改善

## 📞 サポート

問題や提案がある場合：

1. **インシデント賢者**: 緊急の技術的問題
2. **タスク賢者**: プロセスの改善提案
3. **ナレッジ賢者**: ドキュメントの更新
4. **RAG賢者**: 新技術の調査・導入

---

**🧙‍♂️ 品質第一・階層秩序 - エルダーズギルドの理念を実現**

*最終更新: 2025年7月10日*
*承認: エルダー評議会*
