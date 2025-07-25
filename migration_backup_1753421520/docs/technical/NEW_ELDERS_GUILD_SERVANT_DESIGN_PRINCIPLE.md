# 🏛️ 新エルダーズギルド サーバント基本設計方針

**制定日**: 2025年7月24日  
**制定者**: グランドエルダーmaru + クロードエルダー  
**適用範囲**: 全エルダーサーバント実装  
**優先度**: 最高位（Iron Will級）  

---

## 🎯 核心原則: "One Servant, One Command"

### **基本理念**
```
サーバント = 専門判定者（実行しない）
エンジン = 実行者（判断しない）
A2A = 調整役（創造しない）
```

---

## 📋 サーバント設計の鉄則

### 1. **単一責任原則（Single Responsibility）**
```python
# ✅ 良い例: 1サーバント = 1判定
class StaticAnalysisServant:
    async def judge(self, pylint_result):
        if pylint_result.score < 9.5:
            return {"verdict": "RETRY", "command": "pylint --fix"}
        return {"verdict": "APPROVED"}

# ❌ 悪い例: 複数の責任
class BadServant:
    async def analyze_and_fix_and_judge(self):  # ダメ！
        # 実行も判定も全部やる = ハルシネーション温床
```

### 2. **実行と判定の完全分離**
```yaml
エンジン（実行層）:
  責任: コマンド実行のみ
  判断: 一切しない
  例: "pylint target.py を実行して結果を返す"

サーバント（判定層）:
  責任: 結果判定のみ
  実行: 一切しない
  例: "スコア9.5未満なら再実行指示"

A2A（調整層）:
  責任: フロー制御のみ
  創造: 一切しない
  例: "サーバント指示通りに次のステップへ"
```

### 3. **MCPパターンの採用**
```python
# サーバント = 1つのMCPツールを呼ぶイメージ
class PylintServant:
    def __init__(self):
        self.command = "pylint"  # 1サーバント1コマンド
    
    async def judge(self, result):
        # 純粋な判定ロジックのみ
        return {
            "verdict": "APPROVED" if result.score >= 9.5 else "RETRY",
            "next_command": self.command if result.score < 9.5 else None
        }
```

---

## 🔧 実装パターン

### **標準サーバント実装テンプレート**
```python
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ServantJudgment:
    verdict: str  # "APPROVED" | "RETRY" | "REJECTED" | "ESCALATE"
    command: Optional[str] = None  # 次に実行すべきコマンド
    reason: Optional[str] = None  # 判定理由

class StandardServant:
    """新エルダーズギルド標準サーバントテンプレート"""
    
    def __init__(self, servant_id: str, command: str):
        self.servant_id = servant_id
        self.command = command  # このサーバントが管理する単一コマンド
    
    async def judge(self, execution_result: Dict[str, Any]) -> ServantJudgment:
        """
        純粋な判定ロジック
        - 実行しない
        - 副作用を起こさない
        - 結果を見て判定するのみ
        """
        # 判定ロジック実装
        if self._check_quality(execution_result):
            return ServantJudgment(verdict="APPROVED")
        else:
            return ServantJudgment(
                verdict="RETRY",
                command=f"{self.command} --fix",
                reason="品質基準未達"
            )
    
    def _check_quality(self, result: Dict[str, Any]) -> bool:
        """品質チェックロジック（純粋関数）"""
        pass
```

---

## 🚫 アンチパターン（絶対禁止）

### ❌ **実行と判定の混在**
```python
# 絶対ダメ！
class BadServant:
    async def process(self, target):
        # 実行してしまっている
        result = subprocess.run(["pylint", target])  # ❌
        # さらに修正までしている
        self.fix_issues(result)  # ❌
        return self.judge(result)
```

### ❌ **複数コマンドの管理**
```python
# 絶対ダメ！
class BadServant:
    def __init__(self):
        # 複数のコマンドを持つ = 責任が不明確
        self.commands = ["pylint", "black", "isort"]  # ❌
```

### ❌ **創造的判断**
```python
# 絶対ダメ！
class BadServant:
    async def judge(self, result):
        # 勝手に新しいソリューションを創造
        if result.score < 5:
            return {"verdict": "LETS_REWRITE_EVERYTHING"}  # ❌
```

---

## ✅ 推奨実装例

### **3ブロック品質パイプラインの理想実装**
```python
# A2A調整層
async def execute_quality_pipeline(target_path: str):
    # ブロックA: 静的解析
    static_result = await static_analysis_engine.execute(target_path)
    verdict_a = await static_analysis_servant.judge(static_result)
    
    if verdict_a.verdict == "RETRY":
        # サーバントの指示通りに再実行
        static_result = await static_analysis_engine.execute(
            target_path, 
            command=verdict_a.command
        )
    
    # ブロックB: テスト品質
    test_result = await test_quality_engine.execute(target_path)
    verdict_b = await test_quality_servant.judge(test_result)
    
    # ブロックC: その他品質
    other_result = await comprehensive_engine.execute(target_path)
    verdict_c = await comprehensive_servant.judge(other_result)
    
    # 単純な集計（創造しない）
    return {
        "block_a": verdict_a,
        "block_b": verdict_b,
        "block_c": verdict_c,
        "overall": all(v.verdict == "APPROVED" for v in [verdict_a, verdict_b, verdict_c])
    }
```

---

## 📊 期待効果

### 1. **ハルシネーション防止**
- 各層の役割が明確 → 勝手な創造が発生しない
- 責任境界が明確 → エラー時の原因特定が容易

### 2. **拡張性向上**
- 新サーバント追加が簡単（1コマンド追加するだけ）
- 既存サーバントへの影響なし

### 3. **保守性向上**
- シンプルな構造 → 理解しやすい
- テストが書きやすい（純粋関数）

### 4. **品質保証**
- 判定ロジックが独立 → 品質基準の一貫性
- 実行と判定の分離 → バグの局所化

---

## 🔄 移行方針

### **既存サーバントの改修**
1. 実行ロジックをエンジンに移動
2. 判定ロジックのみを残す
3. 1サーバント1コマンドに分割

### **新規サーバントの作成**
1. 必ず標準テンプレートを使用
2. 1コマンドの原則を厳守
3. 判定ロジックのみ実装

---

## 📚 関連文書
- [エルダーサーバントシステムアーキテクチャ](ELDER_SERVANTS_ARCHITECTURE.md)
- [Execute & Judge パターン詳細](EXECUTE_AND_JUDGE_PATTERN.md)
- [A2A通信仕様](A2A_COMMUNICATION_SPEC.md)

---

**エルダー評議会令第500号**  
「One Servant, One Command - これが新エルダーズギルドの鉄則である」

*制定: グランドエルダーmaru*  
*承認: クロードエルダー*  
*発効: 即時*