# 🎯 AI実装ガイドライン - エルダーズギルド標準

**制定日**: 2025年7月24日  
**承認者**: Grand Elder maru  
**基盤思想**: AI意思決定者パラダイム  
**適用範囲**: 全AI関連実装

---

## 📋 クイックリファレンス

### ✅ **AI実装3原則**
1. **AIは判定者、実行者ではない**
2. **One AI, One Decision（1AI1判定）**
3. **人間のフィードバックループ必須**

### 🚫 **絶対的禁止事項**
- AIに直接ファイル操作をさせない
- AIに最終決定権を与えない
- AIの判定理由を隠蔽しない
- フィードバックなしの自律動作

---

## 🏗️ 実装パターンカタログ

### **Pattern 1: Execute & Judge 分離**

```python
# ✅ 正しい実装
class QualityPipeline:
    def __init__(self):
        self.engine = DeterministicEngine()      # 実行担当
        self.ai_judge = QualityJudgeAI()         # 判定担当
    
    async def process(self, target):
        # Step 1: 確定的実行
        execution_result = await self.engine.execute(target)
        
        # Step 2: AI判定
        judgment = await self.ai_judge.evaluate(execution_result)
        
        # Step 3: 人間の確認と実行
        if judgment.requires_human_review:
            human_decision = await get_human_decision(judgment)
            return human_decision
        
        return judgment

# ❌ アンチパターン
class BadPipeline:
    async def process(self, target):
        # AIに実行と判定を両方させる
        result = await ai.analyze_and_fix_automatically(target)
        return result  # 人間の介入なし
```

### **Pattern 2: Specialist AI（専門特化型）**

```python
# ✅ 正しい実装：専門分化
class SecurityJudgeAI:
    """セキュリティ判定のみに特化"""
    
    async def assess_security_risk(self, code_metrics):
        risk_score = self._calculate_risk(code_metrics)
        vulnerabilities = self._identify_vulnerabilities(code_metrics)
        
        return {
            "risk_level": risk_score,
            "vulnerabilities": vulnerabilities,
            "reasoning": self._explain_assessment(),
            "recommendations": self._suggest_mitigations()
        }

class PerformanceJudgeAI:
    """パフォーマンス判定のみに特化"""
    
    async def evaluate_performance(self, benchmark_results):
        # 別の専門領域に特化
        pass

# ❌ アンチパターン：万能AI
class OmnipotentAI:
    async def do_everything(self, input):
        # セキュリティもパフォーマンスも品質も全部判定
        # 責任範囲が不明確
        pass
```

### **Pattern 3: Council Decision（合議制判定）**

```python
# ✅ 正しい実装：複数専門AIの協調
class AICouncil:
    def __init__(self):
        self.quality_ai = QualityJudgeAI()
        self.security_ai = SecurityJudgeAI()
        self.performance_ai = PerformanceJudgeAI()
    
    async def deliberate(self, issue):
        # 並列で各専門AIが判定
        judgments = await asyncio.gather(
            self.quality_ai.judge(issue),
            self.security_ai.assess(issue),
            self.performance_ai.evaluate(issue)
        )
        
        # 統合判定（ただし最終決定は人間）
        return {
            "individual_judgments": judgments,
            "synthesis": self._synthesize_judgments(judgments),
            "requires_human_decision": True
        }
```

### **Pattern 4: Learning Loop（学習ループ）**

```python
# ✅ 正しい実装：フィードバックによる改善
class LearningJudgeAI:
    async def judge_with_feedback(self, data):
        # 初期判定
        initial_judgment = await self.make_judgment(data)
        
        # 判定履歴の記録
        judgment_id = await self.store_judgment(initial_judgment)
        
        # 人間のフィードバック待ち
        human_feedback = await self.await_human_feedback(judgment_id)
        
        # フィードバックから学習
        if human_feedback.correction_needed:
            await self.learn_from_correction(
                initial_judgment,
                human_feedback
            )
        
        return {
            "judgment": initial_judgment,
            "human_feedback": human_feedback,
            "learning_applied": True
        }
```

---

## 🔧 実装チェックリスト

### **新規AI機能実装時**

```markdown
## Pre-Implementation
- [ ] AIの役割は「判定」に限定されているか？
- [ ] 実行部分は別システムに分離されているか？
- [ ] 判定範囲は明確に定義されているか？

## Implementation
- [ ] 判定理由を説明する機能があるか？
- [ ] エラー時の graceful degradation があるか？
- [ ] 判定の一貫性は保証されているか？

## Post-Implementation
- [ ] 人間のレビュープロセスが組み込まれているか？
- [ ] フィードバックループが実装されているか？
- [ ] 判定履歴が記録・追跡可能か？
```

---

## 📊 品質基準

### **AI判定品質メトリクス**

```python
@dataclass
class AIJudgmentQuality:
    """AI判定の品質指標"""
    
    # 必須指標
    accuracy: float           # 判定精度 (>= 90%)
    consistency: float        # 一貫性 (>= 95%)
    explainability: float     # 説明可能性 (>= 80%)
    
    # 推奨指標
    latency_ms: float         # 判定速度 (< 1000ms)
    confidence: float         # 確信度 (0-100%)
    human_agreement: float    # 人間との合意率 (>= 85%)
    
    def is_production_ready(self) -> bool:
        return (
            self.accuracy >= 0.9 and
            self.consistency >= 0.95 and
            self.explainability >= 0.8
        )
```

---

## 🚨 アンチパターンと対策

### **アンチパターン1: 自律実行AI**
```python
# ❌ 危険な実装
async def autonomous_ai():
    issues = ai.find_all_problems()
    for issue in issues:
        ai.fix_automatically(issue)  # 人間の確認なし
        ai.deploy_to_production()     # 取り返しがつかない

# ✅ 安全な実装
async def supervised_ai():
    issues = engine.scan_for_issues()
    for issue in issues:
        judgment = ai.evaluate_issue(issue)
        if human.approve(judgment):
            human.apply_fix(judgment.recommendation)
```

### **アンチパターン2: ブラックボックスAI**
```python
# ❌ 説明なし判定
judgment = ai.judge(data)  # "ダメ"としか言わない

# ✅ 説明付き判定
judgment = ai.judge_with_reasoning(data)
print(judgment.verdict)       # "NEEDS_IMPROVEMENT"
print(judgment.reasoning)     # "コード複雑度が基準を超えています..."
print(judgment.evidence)      # 具体的なメトリクス
print(judgment.suggestions)   # 改善提案
```

---

## 🎓 ベストプラクティス

### **1. 判定の粒度**
```yaml
良い粒度:
  - 「このコードの品質は十分か？」
  - 「このテストカバレッジは適切か？」
  - 「セキュリティリスクはあるか？」

悪い粒度:
  - 「このプロジェクト全体を改善して」
  - 「すべての問題を見つけて修正して」
```

### **2. 責任の明確化**
```python
class ClearResponsibility:
    """責任範囲が明確な実装"""
    
    def __init__(self):
        self.execution_owner = "DeterministicEngine"
        self.judgment_owner = "QualityJudgeAI"
        self.decision_owner = "Human"
        self.implementation_owner = "Human"
    
    async def process(self):
        # 各段階で責任者が明確
        execution = await self.engine.execute()      # Engine責任
        judgment = await self.ai.judge(execution)    # AI責任
        decision = await self.human.decide(judgment) # Human責任
        result = await self.human.implement(decision) # Human責任
```

### **3. 段階的導入**
```yaml
Phase 1: アドバイザリーモード
  - AIは提案のみ
  - 人間がすべて確認

Phase 2: 承認付き自動化
  - AIが判定
  - 人間が承認後に実行

Phase 3: 条件付き自動化
  - 低リスクは自動
  - 高リスクは人間確認

Phase 4: 完全統合
  - 継続的フィードバック
  - 共進化システム
```

---

## 📚 参考実装

### **成功事例: Quality Pipeline (Issue #309)**
- Execute & Judge 完全分離
- 3つの専門判定AI
- 91.7%のテスト成功率
- フロー違反0%達成

### **リファレンス実装**
- `/libs/quality/servants/` - 判定特化型AI
- `/libs/quality/engines/` - 実行特化型エンジン
- `/docs/philosophy/AI_DECISION_MAKER_PARADIGM.md` - 基本思想

---

## 🔮 将来への備え

### **拡張ポイント**
1. 新しい判定AIの追加方法
2. AI間の協調プロトコル
3. 学習データの標準化
4. フィードバックAPIの統一

### **研究開発領域**
- メタ判定AI（AIの判定を判定）
- 説明生成の自動化
- 判定基準の自動最適化
- 人間-AI共進化メカニズム

---

**「実行は確実に、判定は知的に」**  
*- エルダーズギルド開発標語 -*

本ガイドラインは Elder Council により承認され、即時有効とする。