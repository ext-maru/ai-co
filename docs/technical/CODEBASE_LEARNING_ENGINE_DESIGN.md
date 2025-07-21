# コードベース学習エンジン設計書

## 概要
Issue #184 Phase 3: 既存コードベースから学習してコード生成品質を向上させるシステム

## 目標
- 既存コードパターンの学習
- プロジェクト固有の慣習・スタイルの検出
- コンテキスト情報の強化
- 品質スコア95-100点の達成

## システム構成

### 1. CodebaseAnalyzer
既存コードの解析と分類

```python
class CodebaseAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.patterns = {}
        
    async def analyze_codebase(self) -> Dict[str, Any]:
        """コードベース全体の分析"""
        
    def extract_patterns(self, file_path: Path) -> Dict[str, Any]:
        """ファイルからパターンを抽出"""
        
    def categorize_files(self) -> Dict[str, List[Path]]:
        """ファイルをカテゴリ別に分類"""
```

**機能:**
- ファイル構造の分析
- インポートパターンの抽出
- 命名規則の検出
- クラス・関数構造の学習

### 2. PatternLearningEngine
パターンの学習と蓄積

```python
class PatternLearningEngine:
    def __init__(self):
        self.learned_patterns = {}
        
    async def learn_from_files(self, files: List[Path]) -> None:
        """ファイル群からパターンを学習"""
        
    def extract_coding_style(self, code: str) -> Dict[str, Any]:
        """コーディングスタイルを抽出"""
        
    def build_project_vocabulary(self) -> Dict[str, int]:
        """プロジェクト固有の語彙を構築"""
```

**学習対象:**
- コーディングスタイル（インデント、命名）
- エラーハンドリングパターン
- ロギングパターン
- テストパターン
- ドキュメンテーションスタイル

### 3. ContextEnhancer
学習結果でコンテキストを強化

```python
class ContextEnhancer:
    def __init__(self, pattern_engine: PatternLearningEngine):
        self.pattern_engine = pattern_engine
        
    def enhance_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """学習パターンでコンテキストを強化"""
        
    def suggest_similar_implementations(self, context: Dict[str, Any]) -> List[Dict]:
        """類似実装の提案"""
        
    def add_project_specific_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクト固有のコンテキスト追加"""
```

**強化内容:**
- プロジェクト固有のインポート
- 標準的なエラーハンドリング
- 一貫した命名規則
- 適切なロギング・テストパターン

## データ構造

### 学習パターン
```python
{
    "coding_style": {
        "indentation": "spaces",
        "line_length": 88,
        "naming_convention": "snake_case",
        "docstring_style": "google"
    },
    "import_patterns": [
        "from typing import Dict, Any, Optional",
        "import logging",
        "from pathlib import Path"
    ],
    "error_handling": {
        "common_exceptions": ["ValueError", "FileNotFoundError"],
        "logging_pattern": "logger.error(f'Error: {e}')",
        "try_except_style": "specific_exceptions"
    },
    "test_patterns": {
        "framework": "pytest",
        "naming": "test_*",
        "assertions": ["assert", "pytest.raises"],
        "mocking": "unittest.mock"
    }
}
```

### 類似実装データベース
```python
{
    "implementation_id": "file_processor_001",
    "file_path": "libs/file_processor.py",
    "similarity_score": 0.85,
    "patterns": {
        "async_file_handling": True,
        "error_handling": "comprehensive",
        "logging": "structured",
        "type_hints": "complete"
    },
    "code_snippet": "...",
    "usage_example": "..."
}
```

## 実装フェーズ

### Phase 3.1: コードベース分析
- [ ] `CodebaseAnalyzer` 実装
- [ ] ファイル分類・パターン抽出
- [ ] 基本統計の収集

### Phase 3.2: パターン学習
- [ ] `PatternLearningEngine` 実装
- [ ] スタイル・慣習の学習
- [ ] パターンデータベース構築

### Phase 3.3: コンテキスト強化
- [ ] `ContextEnhancer` 実装
- [ ] Template Manager統合
- [ ] 類似実装提案機能

### Phase 3.4: 統合テスト
- [ ] エンドツーエンドテスト
- [ ] 品質スコア測定
- [ ] パフォーマンス最適化

## 品質向上期待値
- **現在**: 90/100点（Phase 2完了時）
- **Phase 3目標**: 95-100点
- **改善要因**:
  - プロジェクト固有パターンの活用 (+3-5点)
  - 一貫性のあるコードスタイル (+2-3点)
  - 適切なエラーハンドリング・ロギング (+2-3点)

## 技術仕様

### ファイル構成
```
libs/code_generation/
├── codebase_analyzer.py      # コードベース分析
├── pattern_learning.py       # パターン学習エンジン
├── context_enhancer.py       # コンテキスト強化
├── similarity_matcher.py     # 類似性マッチング
└── learned_patterns/         # 学習済みパターン保存
    ├── coding_style.json
    ├── import_patterns.json
    ├── error_patterns.json
    └── test_patterns.json
```

### 依存関係
- `ast` モジュール（Python AST解析）
- `pathlib` （ファイルパス操作）
- `json` （パターン保存）
- `difflib` （類似性計算）

## リスク・制約
- **パフォーマンス**: 大量ファイルの解析時間
- **メモリ使用量**: パターンデータベースのサイズ
- **精度**: パターンマッチングの質

## 成功指標
1. **品質スコア**: 95点以上
2. **実行時間**: 学習処理30秒以内
3. **パターン検出精度**: 80%以上
4. **プロジェクト適合性**: 手動評価で90%以上

---
*設計日: 2025-07-21*
*設計者: Claude Elder (クロードエルダー)*