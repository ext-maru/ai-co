# 🏗️ エルダーズギルド 開発ワークフロー（根本解決版）

## 🎯 根本問題と解決策

### ❌ **従来の問題**
- ビルド成果物（node_modules, .next）がgitに混入
- 142MB/119MBファイルでGitHub制限オーバー
- 開発環境の不統一による問題継続

### ✅ **根本解決アプローチ**
1. **Dockerベース開発**: 成果物はコンテナ内のみ
2. **強化版.gitignore**: 全プロジェクト対応パターン  
3. **標準化されたワークフロー**: 今後の問題発生防止

## 🐳 Docker開発環境

### フロントエンドプロジェクト
```bash
# 開発開始
cd projects/frontend-project-manager
docker-compose -f docker-compose.dev.yml up

# 依存関係更新
docker-compose -f docker-compose.dev.yml build --no-cache

# 停止・クリーンアップ
docker-compose -f docker-compose.dev.yml down -v
```

### バックエンドプロジェクト
```bash
# Python環境
cd projects/upload-image-service
docker-compose up --build

# 開発モード
docker-compose -f docker-compose.dev.yml up
```

## 📁 プロジェクト構造ルール

### ✅ **Git管理対象**
```
projects/
├── frontend-project-manager/
│   ├── src/                 # ソースコード
│   ├── public/             # 静的ファイル
│   ├── package.json        # 依存関係定義
│   ├── Dockerfile.dev      # 開発環境
│   └── docker-compose.dev.yml
```

### 🚫 **Git管理外（自動除外）**
```
projects/
├── frontend-project-manager/
│   ├── node_modules/       # → Docker内のみ
│   ├── .next/             # → ビルド時生成
│   ├── dist/              # → デプロイ成果物
│   └── coverage/          # → テスト結果
```

## 🔄 開発フロー（標準化）

### 1. **新規プロジェクト開始**
```bash
# 1. プロジェクトディレクトリ作成
mkdir projects/new-project

# 2. Dockerfile.dev作成
cp templates/Dockerfile.dev projects/new-project/

# 3. docker-compose.dev.yml作成
cp templates/docker-compose.dev.yml projects/new-project/

# 4. 開発開始
cd projects/new-project
docker-compose -f docker-compose.dev.yml up
```

### 2. **既存プロジェクト作業**
```bash
# 1. 最新コード取得
git pull origin main

# 2. Docker環境起動（成果物は自動生成）
docker-compose -f docker-compose.dev.yml up --build

# 3. 開発作業
# （ホストのソースコード編集 → Docker内で自動反映）

# 4. コミット（成果物は除外される）
git add . && git commit -m "feat: 新機能実装"
```

### 3. **問題回避チェックリスト**
- ✅ `docker-compose down -v` でボリューム削除
- ✅ `.gitignore` で成果物除外確認
- ✅ `git status` で追跡ファイル確認
- ✅ 大容量ファイル警告時は即座停止

## 🚀 CI/CD統合

### GitHub Actions（将来実装）
```yaml
name: エルダーズギルド自動デプロイ
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Docker Build & Test
        run: |
          docker-compose -f docker-compose.ci.yml up --build --abort-on-container-exit
      - name: Deploy
        run: docker-compose -f docker-compose.prod.yml up -d
```

## 📊 効果測定

### 期待される改善
- **リポジトリサイズ**: 90%削減
- **クローン時間**: 80%短縮  
- **ビルド再現性**: 100%保証
- **環境差異問題**: 0件

---
**策定**: クロードエルダー（Claude Elder）  
**承認**: エルダーズ評議会  
**更新日**: 2025年7月10日