# 🛠️ Upload Image Service - 開発モード設定

## 📅 開発モード移行日
2025年1月10日

## 🎯 開発モード概要

このドキュメントは、Upload Image Serviceプロジェクトの機能追加・改修を効率的に行うためのガイドです。

## 🏗️ プロジェクト構造

```
upload-image-service/
├── backend/                 # FastAPIバックエンド
│   ├── app/
│   │   ├── api/            # APIエンドポイント
│   │   ├── core/           # コア機能（認証、設定）
│   │   ├── models/         # データベースモデル
│   │   ├── services/       # ビジネスロジック
│   │   └── utils/          # ユーティリティ
│   └── tests/              # テストスイート
├── frontend/               # React + TypeScript
│   ├── src/
│   │   ├── components/     # UIコンポーネント
│   │   ├── services/       # API通信
│   │   └── types/          # 型定義
│   └── public/             # 静的ファイル
└── docker-compose.yml      # Docker設定
```

## 🚀 開発環境セットアップ

### 1. 環境起動
```bash
cd /home/aicompany/ai_co/projects/upload-image-service
docker-compose up -d
```

### 2. ログ監視
```bash
# バックエンドログ
docker-compose logs -f backend

# フロントエンドログ
docker-compose logs -f frontend
```

### 3. 開発URL
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- APIドキュメント: http://localhost:8000/docs
- データベース: localhost:5432
- Redis: localhost:6379

## 📝 機能追加ガイドライン

### バックエンド機能追加

#### 1. 新規エンドポイント追加
```python
# backend/app/api/endpoints/new_feature.py
from fastapi import APIRouter, Depends
from app.services.new_feature_service import NewFeatureService

router = APIRouter()
service = NewFeatureService()

@router.post("/new-feature")
async def create_new_feature(data: dict):
    return await service.process(data)
```

#### 2. サービス層実装
```python
# backend/app/services/new_feature_service.py
class NewFeatureService:
    async def process(self, data: dict):
        # ビジネスロジック実装
        pass
```

#### 3. テスト追加
```python
# backend/tests/unit/test_new_feature.py
import pytest
from app.services.new_feature_service import NewFeatureService

@pytest.mark.asyncio
async def test_new_feature():
    service = NewFeatureService()
    result = await service.process({"test": "data"})
    assert result is not None
```

### フロントエンド機能追加

#### 1. 新規コンポーネント
```typescript
// frontend/src/components/features/NewFeature.tsx
import React from 'react';

export const NewFeature: React.FC = () => {
  return (
    <div className="new-feature">
      {/* コンポーネント実装 */}
    </div>
  );
};
```

#### 2. API通信追加
```typescript
// frontend/src/services/api.ts に追加
export const createNewFeature = async (data: any) => {
  const response = await api.post('/api/v1/new-feature', data);
  return response.data;
};
```

## 🧪 テスト実行

### バックエンドテスト
```bash
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=app
```

### フロントエンドテスト
```bash
docker-compose exec frontend npm test
```

## 📊 品質チェック

### PDCA分析
```bash
ai-project pdca upload-image-service
```

### 品質レポート
```bash
ai-project report upload-image-service
```

## 🔄 ホットリロード

- **バックエンド**: FastAPIの`--reload`フラグにより自動リロード
- **フロントエンド**: Create React Appのホットリロード機能

## 📋 推奨される機能追加

### 優先度: 高
1. **ファイルタイプ検証強化**
   - 画像フォーマット詳細チェック
   - ウイルススキャン統合

2. **画像処理機能拡張**
   - 自動リサイズオプション
   - フォーマット変換機能

3. **ユーザー体験向上**
   - ドラッグ&ドロップ改善
   - プログレスバー詳細化

### 優先度: 中
1. **管理機能強化**
   - 一括承認/却下
   - フィルタリング機能

2. **通知システム**
   - メール通知
   - Webhook統合

3. **分析ダッシュボード**
   - アップロード統計
   - ユーザー行動分析

### 優先度: 低
1. **API拡張**
   - GraphQL対応
   - WebSocket通信

2. **国際化**
   - 多言語対応
   - タイムゾーン対応

## 🏛️ エルダーズギルド統合

### TDD実践
```bash
# テスト作成
ai-tdd new FeatureName "機能要件"

# カバレッジ確認
ai-tdd coverage backend/app
```

### 4賢者協調
- ナレッジ賢者: 実装パターン参照
- タスク賢者: 機能優先順位管理
- インシデント賢者: エラー監視
- RAG賢者: 最適解探索

## 📞 サポート

問題が発生した場合:
1. `docker-compose logs` でログ確認
2. PDCA分析で品質チェック
3. エルダー評議会への相談

---
開発モード準備完了！
機能追加・改修を開始できます。