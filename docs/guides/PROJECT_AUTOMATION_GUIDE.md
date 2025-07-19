# 🤖 エルダーズギルド プロジェクト自動化システム

## 📋 概要

プロジェクト進行テンプレートに従って、**毎回同じ流れを自動化**し、効率的なプロジェクト進行を実現します。

### 🎯 解決する問題

- **毎回同じ作業の繰り返し**: ファイル作成、ディレクトリ作成、初期設定
- **手動作業の非効率性**: 人間がやる必要のない定型作業
- **作業忘れのリスク**: チェックリストがあっても人間は忘れる
- **コンテキスト断絶**: 作業の途中で止まった時の再開困難

## 🚀 自動化の流れ

### 1. プロジェクト作成
```bash
# テンプレートからプロジェクト作成
ai-project-template create "新しいWebアプリ" web_development
```

### 2. 自動化計画確認
```bash
# 何が自動化されるか確認
ai-project-template auto project_20250711_124425_a9ab847b --plan
```

### 3. 自動化実行
```bash
# ファイル作成のみ（安全）
ai-project-template auto project_20250711_124425_a9ab847b

# コマンド実行も含む（フル自動化）
ai-project-template auto project_20250711_124425_a9ab847b --execute
```

## 🛠️ 自動化内容

### Web開発プロジェクト (web_development)

#### Phase 1: 要件定義・設計
**自動作成ファイル:**
- `requirements.md` - 要件定義書テンプレート
- `architecture.md` - アーキテクチャ設計書テンプレート
- `database_schema.sql` - データベース設計用SQLファイル
- `tech_stack.md` - 技術選定記録

**自動実行コマンド:**
- `mkdir -p docs/design` - 設計書用ディレクトリ作成
- `mkdir -p src` - ソースコード用ディレクトリ作成
- `mkdir -p tests` - テスト用ディレクトリ作成
- `touch .gitignore` - Gitignoreファイル作成

#### Phase 2: 基盤実装
**自動作成ファイル:**
- `src/auth/auth.py` - 認証システムの基本コード
- `src/database/models.py` - データベースモデル
- `src/api/main.py` - API基盤コード
- `frontend/package.json` - フロントエンド設定

**自動実行コマンド:**
- `python -m venv venv` - 仮想環境作成
- `pip install -r requirements.txt` - 依存関係インストール
- `npm init -y` - Node.js初期化

#### Phase 3: 機能実装
**自動作成ファイル:**
- `tests/test_auth.py` - 認証テストコード
- `tests/test_api.py` - APIテストコード
- `src/core/business_logic.py` - ビジネスロジック基盤

**自動実行コマンド:**
- `pytest --cov=src tests/` - テスト実行とカバレッジ
- `npm test` - フロントエンドテスト

#### Phase 4: 最適化・デプロイ
**自動作成ファイル:**
- `Dockerfile` - Docker設定
- `docker-compose.yml` - コンテナオーケストレーション
- `deploy.sh` - デプロイスクリプト

**自動実行コマンド:**
- `docker build -t app .` - Dockerイメージビルド
- `docker-compose up -d` - コンテナ起動

### AI開発プロジェクト (ai_development)

#### Phase 1: 問題定義・データ調査
**自動作成ファイル:**
- `data_analysis.ipynb` - データ分析用Jupyter Notebook
- `problem_definition.md` - 問題定義書
- `dataset_info.md` - データセット情報

**自動実行コマンド:**
- `mkdir -p data/raw` - 生データ用ディレクトリ
- `mkdir -p data/processed` - 処理済みデータ用ディレクトリ
- `mkdir -p notebooks` - ノートブック用ディレクトリ
- `mkdir -p models` - モデル用ディレクトリ

#### Phase 2: モデル開発
**自動作成ファイル:**
- `src/model.py` - モデル定義
- `src/preprocessing.py` - 前処理コード
- `src/training.py` - 学習コード
- `requirements.txt` - 依存関係

**自動実行コマンド:**
- `pip install pandas numpy scikit-learn` - ML基本ライブラリ
- `jupyter notebook --generate-config` - Jupyter設定

## 💡 実際の使用例

### 1. 新規Webアプリプロジェクト開始
```bash
# 1. プロジェクト作成
ai-project-template create "ECサイト構築" web_development

# 2. 自動化計画確認
ai-project-template auto project_20250711_xxx --plan

# 3. Phase1の自動化実行
ai-project-template auto project_20250711_xxx --execute

# 4. 作成されたファイルを確認
ls projects/project_20250711_xxx/

# 5. 要件定義書を編集
vim projects/project_20250711_xxx/requirements.md

# 6. Phase1完了後、次のフェーズに進む
ai-project-template advance project_20250711_xxx

# 7. Phase2の自動化実行
ai-project-template auto project_20250711_xxx --execute
```

### 2. 途中で止まったプロジェクトの再開
```bash
# 1. コンテキスト確認
ai-project-template context project_20250711_xxx --format json

# 2. 現在のフェーズで自動化実行
ai-project-template auto project_20250711_xxx

# 3. 作業再開
cd projects/project_20250711_xxx/
# 必要なファイルとディレクトリが既に準備されている
```

## 🔧 カスタマイズ

### 独自テンプレートの追加
`libs/project_automation_engine.py` の `automation_rules` を編集して、独自のテンプレートを追加できます。

```python
"custom_template": {
    "phase_1": {
        "auto_create_files": [
            "custom_file.py",
            "custom_config.json"
        ],
        "auto_commands": [
            "custom_command"
        ]
    }
}
```

### ファイルテンプレートの追加
`_get_file_template()` メソッドでファイルテンプレートを追加できます。

## 🎯 効果

### 従来の手動作業
- ファイル作成: 30分
- ディレクトリ構成: 15分
- 初期設定: 45分
- **合計: 1時間30分**

### 自動化後
- 自動化実行: 2分
- 確認・調整: 10分
- **合計: 12分**

**⚡ 87%の時間短縮！**

## 📋 チェックリスト

### Phase完了前に確認すること
- [ ] 自動生成ファイルの内容確認
- [ ] 必要な情報の追記
- [ ] テストの実行
- [ ] 次のPhaseへの準備

### 注意点
- `--execute` フラグは慎重に使用する
- 重要なコマンドは事前に確認する
- 自動生成ファイルは必ず内容を確認する

## 🏛️ エルダーズギルドの理念

**「人間は創造的な仕事に集中し、定型作業はシステムが自動化する」**

- **効率性**: 同じ作業を繰り返さない
- **一貫性**: 毎回同じ品質を保証
- **継続性**: 途中で止まっても再開可能
- **進化性**: 学習したベストプラクティスを自動適用

---

**🤖 プロジェクト自動化で、クリエイティブな作業に集中しよう！**

*作成: タスクエルダー + 自動化エンジン*
*最終更新: 2025年7月11日*
