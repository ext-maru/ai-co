# 🏛️ 新エルダーズギルド A2Aアーキテクチャ仕様書

**制定日**: 2025年7月24日  
**制定者**: グランドエルダーmaru + クロードエルダー  
**適用範囲**: 全エルダー・サーバント間通信  
**優先度**: 最高位（基盤アーキテクチャ）  

---

## 🎯 概要

新エルダーズギルドにおけるAgent-to-Agent（A2A）通信の正式仕様書。
python-a2aライブラリ（v0.5.9）を使用したHTTP/RESTベースの通信アーキテクチャ。

---

## 📊 アーキテクチャ概要

### **階層構造と通信フロー**
```yaml
ユーザー
  ↓ 自然言語リクエスト
クロードエルダー（調整役）
  ↓ タスク振り分け
4賢者エルダー（ナレッジ・タスク・インシデント・RAG）
  ↓ A2A通信（HTTP/REST）
各種サーバント（独立HTTPサーバー）
  ↓ 結果返信
エルダー → クロードエルダー → ユーザー
```

### **通信仕様**
- **プロトコル**: HTTP/REST（python-a2a標準）
- **データ形式**: JSON
- **認証**: JWT（オプション）
- **非同期サポート**: asyncio完全対応

---

## 🔧 技術スタック

### **コアライブラリ**
```yaml
python-a2a:
  version: 0.5.9
  license: MIT
  repository: https://github.com/themanojdesai/python-a2a
  features:
    - Google A2A Protocol実装
    - Model Context Protocol (MCP) v2.0対応
    - FastAPI/Starlette統合
    - マルチLLMサポート
```

### **ポート割り当て**
```yaml
標準ポート配置:
  - 8801: ナレッジサーバント群
  - 8802: タスクサーバント群
  - 8803: インシデントサーバント群
  - 8804: RAGサーバント群
  - 8810-8820: 品質管理サーバント群（新規）
```

---

## 📋 サーバント実装標準

### **基本テンプレート**
```python
from python_a2a import A2AServer, skill, Message

class StandardServant(A2AServer):
    """新エルダーズギルド標準サーバントテンプレート"""
    
    def __init__(self, port: int):
        super().__init__()
        self.agent_name = "servant-name"
        self.description = "Servant description"
        self.port = port
        
        # 1サーバント1機能の原則
        self.primary_function = "specific_function"
        
    @skill
    async def execute_primary_function(self, request: dict) -> dict:
        """
        メイン機能の実行
        - HTTPエンドポイントとして公開
        - 純粋な判定ロジック
        - 副作用なし
        """
        # 処理実行
        result = await self._process_request(request)
        
        # 判定
        verdict = self._judge_result(result)
        
        return {
            "servant": self.agent_name,
            "verdict": verdict,
            "details": result,
            "timestamp": datetime.now().isoformat()
        }
```

### **サーバー起動テンプレート**
```python
#!/usr/bin/env python3
from python_a2a import run_server
from .servant import MyServant

def main():
    """サーバント起動スクリプト"""
    servant = MyServant(port=8811)
    
    # python-a2a標準のサーバー起動
    asyncio.run(run_server(servant))

if __name__ == "__main__":
    main()
```

---

## 🏗️ 実装例：品質管理サーバント

### **1. 静的解析サーバント**
```python
class StaticAnalysisServant(A2AServer):
    """静的解析を統合管理するサーバント"""
    
    def __init__(self):
        super().__init__()
        self.agent_name = "static-analysis-servant"
        self.port = 8811
        
        # 複数のMCPツールを統合
        self.analyzers = {
            "black": BlackFormatter(),
            "isort": ImportSorter(),
            "pylint": PylintAnalyzer(),
            "mypy": TypeChecker()
        }
    
    @skill
    async def analyze_code_quality(self, target_path: str) -> dict:
        """コード品質を総合分析"""
        results = {}
        
        # 各ツール実行
        for name, analyzer in self.analyzers.items():
            results[name] = await analyzer.run(target_path)
        
        # 統合判定
        quality_score = self._calculate_quality_score(results)
        verdict = "APPROVED" if quality_score >= 95 else "NEEDS_IMPROVEMENT"
        
        return {
            "verdict": verdict,
            "quality_score": quality_score,
            "details": results,
            "recommendations": self._get_recommendations(results)
        }
```

### **2. テスト品質サーバント**
```python
class TestQualityServant(A2AServer):
    """テスト品質を管理するサーバント"""
    
    def __init__(self):
        super().__init__()
        self.agent_name = "test-quality-servant"
        self.port = 8812
        
        # テスト関連ツール統合
        self.test_tools = {
            "pytest": PytestRunner(),
            "coverage": CoverageAnalyzer(),
            "hypothesis": PropertyTestGenerator()
        }
    
    @skill
    async def evaluate_test_quality(self, target_path: str) -> dict:
        """テスト品質を評価"""
        # 実装詳細...
```

---

## 🚫 廃止事項（古い実装の削除）

### **削除対象**
1. **libs/a2a_communication.py** - RabbitMQベースの旧実装
2. **aio_pika依存** - メッセージキューは使用しない
3. **Flask直接利用** - python-a2aが内部でFastAPIを使用
4. **複雑な並列実行ロジック** - シンプルなHTTP通信に統一

### **移行方針**
```yaml
旧実装:
  - RabbitMQメッセージキュー
  - 複雑な非同期処理
  - カスタム通信プロトコル

新実装:
  - HTTP/REST標準
  - python-a2a統一
  - Google A2Aプロトコル準拠
```

---

## 📊 メリット

### **技術的利点**
1. **標準化**: 業界標準のA2Aプロトコル採用
2. **保守性**: OSSライブラリによるメンテナンス負荷軽減
3. **拡張性**: 新サーバント追加が容易
4. **デバッグ**: HTTPなので通信内容が見やすい

### **運用的利点**
1. **独立性**: 各サーバントが独立プロセス
2. **スケーラビリティ**: 負荷に応じて個別スケール可能
3. **耐障害性**: 1つのサーバント障害が全体に波及しない
4. **監視**: 標準的なHTTP監視ツールが使用可能

---

## 🔄 移行計画

### **Phase 1: 新規サーバント（即時適用）**
- すべての新規サーバントはこの仕様に従う
- 品質管理サーバント群から開始

### **Phase 2: 既存サーバント移行（段階的）**
- 優先度順に既存サーバントを移行
- 後方互換性を保ちながら実施

### **Phase 3: 旧実装削除（最終段階）**
- すべての移行完了後
- libs/a2a_communication.py等を削除

---

## 📚 関連文書
- [新エルダーズギルド サーバント設計原則](NEW_ELDERS_GUILD_SERVANT_DESIGN_PRINCIPLE.md)
- [python-a2a公式ドキュメント](https://github.com/themanojdesai/python-a2a)
- [Model Context Protocol仕様](https://modelcontextprotocol.org/)

---

**エルダー評議会令第501号**  
「A2Aは標準に従え - python-a2aによる統一通信基盤の確立」

*制定: グランドエルダーmaru*  
*承認: クロードエルダー*  
*発効: 即時*