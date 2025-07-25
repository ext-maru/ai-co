#!/usr/bin/env python3
"""
🛠️ AI意思決定者パラダイム 移行ヘルパー
既存コードを段階的に新パラダイムへ移行するためのヘルパー関数群
"""

import asyncio
import functools
import json
import os
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import inspect
import traceback

# 型定義
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class ExecutionMode(Enum):
    """実行モード"""
    AUTO_EXECUTE = "auto"          # 従来の自動実行（非推奨）
    JUDGE_ONLY = "judge"           # 判定のみ（推奨）
    SUPERVISED = "supervised"       # 人間確認付き実行

@dataclass
class JudgmentResult:
    """AI判定結果"""
    verdict: str                   # 判定結果
    reasoning: str                 # 判定理由
    recommendations: List[str]     # 推奨事項
    risk_level: str               # リスクレベル (low/medium/high)
    requires_human_review: bool    # 人間レビュー必須かどうか
    proposed_action: Optional[Dict] = None  # 提案されるアクション

class AIJudgmentWrapper:
    """
    既存の実行関数をAI判定関数に変換するラッパー
    段階的移行を支援
    """
    
    def __init__(self, mode: ExecutionMode = ExecutionMode.JUDGE_ONLY):
        self.mode = mode
        self.judgment_history = []
        self.feedback_history = []
    
    def judge_instead_of_execute(self, 
                                risk_level: str = "medium",
                                requires_review: bool = True):
        """
        デコレータ: 実行関数を判定関数に変換
        
        使用例:
        @judge_instead_of_execute(risk_level="high")
        def delete_old_logs(directory):
            # 従来: 実際に削除していた
            # 新: 削除推奨のみ返す
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._convert_to_judgment(
                    func, args, kwargs, risk_level, requires_review
                )
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(
                    self._convert_to_judgment(
                        func, args, kwargs, risk_level, requires_review
                    )
                )
            
            # 非同期/同期を自動判定
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def _convert_to_judgment(self, 
                                  func: Callable,
                                  args: tuple,
                                  kwargs: dict,
                                  risk_level: str,
                                  requires_review: bool) -> JudgmentResult:
        """実行関数を判定に変換"""
        
        # 関数の情報を取得
        func_name = func.__name__
        func_doc = func.__doc__ or "No description"
        
        # 実行をシミュレート（実際には実行しない）
        proposed_action = {
            "function": func_name,
            "args": self._serialize_args(args),
            "kwargs": self._serialize_args(kwargs),
            "timestamp": datetime.now().isoformat()
        }
        
        # モードに応じた処理
        if self.mode == ExecutionMode.JUDGE_ONLY:
            # 判定のみモード
            judgment = JudgmentResult(
                verdict="REQUIRES_APPROVAL",
                reasoning=f"関数 '{func_name}' の実行には承認が必要です",
                recommendations=[
                    f"提案されたアクション: {func_name}",
                    f"パラメータ: {proposed_action['args']}",
                    "実行前に影響を確認してください"
                ],
                risk_level=risk_level,
                requires_human_review=requires_review,
                proposed_action=proposed_action
            )
            
            # 判定履歴に記録
            self.judgment_history.append(judgment)
            
            return judgment
        
        elif self.mode == ExecutionMode.SUPERVISED:
            # 監督付き実行モード
            judgment = await self._supervised_execution(
                func, args, kwargs, risk_level
            )
            return judgment
        
        else:
            # 自動実行モード（非推奨、警告を出す）
            print("⚠️ 警告: 自動実行モードは非推奨です。judge_onlyモードの使用を推奨します。")
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            return JudgmentResult(
                verdict="AUTO_EXECUTED",
                reasoning="自動実行モード（非推奨）により実行されました",
                recommendations=["judge_onlyモードへの移行を推奨"],
                risk_level=risk_level,
                requires_human_review=False,
                proposed_action=proposed_action
            )
    
    async def _supervised_execution(self,
                                   func: Callable,
                                   args: tuple,
                                   kwargs: dict,
                                   risk_level: str) -> JudgmentResult:
        """監督付き実行"""
        print(f"\n🤖 AI判定: '{func.__name__}' の実行を提案します")
        print(f"リスクレベル: {risk_level}")
        print(f"引数: {self._serialize_args(args)}")
        
        if risk_level == "high":
            print("⚠️  高リスク操作です。慎重に確認してください。")
        
        confirm = input("\n実行しますか？ (y/n): ").strip().lower()
        
        if confirm == 'y':
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return JudgmentResult(
                    verdict="EXECUTED_WITH_APPROVAL",
                    reasoning="人間の承認を得て実行しました",
                    recommendations=[],
                    risk_level=risk_level,
                    requires_human_review=False
                )
            except Exception as e:
                return JudgmentResult(
                    verdict="EXECUTION_FAILED",
                    reasoning=f"実行中にエラーが発生: {str(e)}",
                    recommendations=["エラーの原因を調査してください"],
                    risk_level="high",
                    requires_human_review=True
                )
        else:
            return JudgmentResult(
                verdict="EXECUTION_CANCELLED",
                reasoning="人間により実行がキャンセルされました",
                recommendations=[],
                risk_level=risk_level,
                requires_human_review=False
            )
    
    def _serialize_args(self, args):
        """引数をシリアライズ"""
        try:
            return json.dumps(args, default=str)
        except:
            return str(args)
    
    def record_feedback(self, judgment_id: int, feedback: str):
        """フィードバックを記録"""
        self.feedback_history.append({
            "judgment_id": judgment_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })

# グローバルインスタンス（簡単に使えるように）
judge_wrapper = AIJudgmentWrapper()
judge_instead_of_execute = judge_wrapper.judge_instead_of_execute

# 実用的なヘルパー関数
def require_human_approval(func: F) -> F:
    """
    人間の承認を必須にするデコレータ
    
    使用例:
    @require_human_approval
    def dangerous_operation():
        pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n⚠️  承認が必要な操作: {func.__name__}")
        print(f"説明: {func.__doc__ or 'なし'}")
        
        confirm = input("実行しますか？ (yes/no): ").strip().lower()
        if confirm == "yes":
            return func(*args, **kwargs)
        else:
            print("操作がキャンセルされました。")
            return None
    
    return wrapper

def explain_before_execute(explanation_func: Callable):
    """
    実行前に説明を表示するデコレータ
    
    使用例:
    @explain_before_execute(lambda: "これはデータベースをクリアします")
    def clear_database():
        pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            explanation = explanation_func() if callable(explanation_func) else str(explanation_func)
            print(f"\n📋 操作説明: {explanation}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

class ExecuteJudgeSeparator:
    """
    Execute（実行）とJudge（判定）を明確に分離するためのベースクラス
    
    使用例:
    class MyFeature(ExecuteJudgeSeparator):
        def judge_quality(self, code):
            return self.make_judgment(...)
        
        def execute_fix(self, fix_plan):
            return self.execute_with_confirmation(...)
    """
    
    def __init__(self, auto_confirm: bool = False):
        self.auto_confirm = auto_confirm
        self.execution_log = []
        self.judgment_log = []
    
    def make_judgment(self, 
                     verdict: str,
                     reasoning: str,
                     recommendations: List[str],
                     risk_level: str = "medium") -> JudgmentResult:
        """判定を作成（実行はしない）"""
        judgment = JudgmentResult(
            verdict=verdict,
            reasoning=reasoning,
            recommendations=recommendations,
            risk_level=risk_level,
            requires_human_review=(risk_level in ["high", "critical"])
        )
        
        self.judgment_log.append({
            "judgment": judgment,
            "timestamp": datetime.now().isoformat()
        })
        
        return judgment
    
    def execute_with_confirmation(self,
                                 action_description: str,
                                 action_func: Callable,
                                 *args, **kwargs) -> Any:
        """確認付きで実行"""
        if not self.auto_confirm:
            print(f"\n🔧 実行予定: {action_description}")
            confirm = input("実行しますか？ (y/n): ").strip().lower()
            
            if confirm != 'y':
                print("実行をキャンセルしました。")
                return None
        
        # 実行ログ記録
        self.execution_log.append({
            "action": action_description,
            "timestamp": datetime.now().isoformat(),
            "executed": True
        })
        
        return action_func(*args, **kwargs)
    
    def display_judgment(self, judgment: JudgmentResult):
        """判定結果を表示"""
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🔴",
            "critical": "🚨"
        }
        
        print(f"\n{risk_emoji.get(judgment.risk_level, '⚪')} AI判定結果")
        print(f"判定: {judgment.verdict}")
        print(f"理由: {judgment.reasoning}")
        print("\n推奨事項:")
        for i, rec in enumerate(judgment.recommendations, 1):
            print(f"  {i}. {rec}")
        
        if judgment.requires_human_review:
            print("\n⚠️  この判定は人間のレビューが必要です。")

# 移行支援ツール
def migration_guide(old_function_name: str) -> str:
    """
    移行ガイドを生成
    
    使用例:
    print(migration_guide("auto_fix_errors"))
    """
    guide = f"""
🔄 移行ガイド: {old_function_name}

1. 現在の実装を確認:
   - 何を自動実行しているか？
   - どんなリスクがあるか？

2. Execute と Judge を分離:
   ```python
   # Before
   def {old_function_name}():
       # 自動で実行
       execute_something()
   
   # After
   def judge_{old_function_name}():
       # 判定のみ
       return JudgmentResult(...)
   
   def execute_{old_function_name}_with_approval():
       # 承認後に実行
       if get_approval():
           execute_something()
   ```

3. デコレータを適用:
   ```python
   @judge_instead_of_execute(risk_level="medium")
   def {old_function_name}():
       pass
   ```

4. テストとフィードバック:
   - 判定の精度を確認
   - フィードバックを収集
   - 継続的改善
"""
    return guide

# 実用例
if __name__ == "__main__":
    # デモ: 危険な関数を安全に変換
    
    @judge_instead_of_execute(risk_level="high", requires_review=True)
    def delete_old_logs(directory: str, days: int = 30):
        """古いログファイルを削除"""
        # 実際の削除コードはここに書かない
        # 判定のみ返される
        pass
    
    # 使用例
    result = delete_old_logs("/var/log", days=30)
    judge_wrapper.display_judgment(result)
    
    print(migration_guide("delete_old_logs"))