#!/usr/bin/env python3
"""
CodeReviewTaskWorker - コードレビュー機能付きTaskWorker
TDD Green Phase - テストを通すための最小実装
"""

import ast
import re
import asyncio
from typing import Dict, Any, List
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker_v2 import AsyncBaseWorkerV2


class CodeReviewTaskWorker(AsyncBaseWorkerV2):
    """コードレビュー機能付きTaskWorker"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            worker_name="code_review_task_worker",
            config=config,
            input_queues=['ai_tasks'],
            output_queues=['ai_pm']
        )
        self.analysis_timeout = config.get('analysis_timeout', 30)
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """メッセージ処理 - コードレビュー要求を処理"""
        message_type = message.get("message_type")
        
        if message_type == "code_review_request":
            return await self._analyze_code(message)
        elif message_type == "improvement_request":
            return await self._re_analyze_improved_code(message)
        else:
            raise ValueError(f"Unsupported message type: {message_type}")
    
    async def _analyze_code(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """コード解析実行"""
        payload = message["payload"]
        code_content = payload["code_content"]
        language = payload.get("language", "python")
        review_options = payload.get("review_options", {})
        
        # 基本的な解析実行
        analysis_results = {
            "syntax_issues": [],
            "logic_issues": [],
            "performance_issues": [],
            "security_issues": []
        }
        
        if language == "python":
            # Python固有の解析
            if review_options.get("check_syntax", True):
                analysis_results["syntax_issues"] = await self._check_python_syntax(code_content)
            
            if review_options.get("check_logic", True):
                analysis_results["logic_issues"] = await self._check_python_logic(code_content)
            
            if review_options.get("check_performance", True):
                analysis_results["performance_issues"] = await self._check_python_performance(code_content)
            
            if review_options.get("check_security", True):
                analysis_results["security_issues"] = await self._check_python_security(code_content)
        
        # コードメトリクス計算
        code_metrics = await self._calculate_code_metrics(code_content)
        
        return {
            "message_id": f"analysis_{message['task_id']}",
            "task_id": message["task_id"],
            "worker_source": "task_worker",
            "worker_target": "pm_worker",
            "message_type": "code_analysis_result",
            "iteration": message.get("iteration", 1),
            "payload": {
                "analysis_results": analysis_results,
                "code_metrics": code_metrics
            }
        }
    
    async def _re_analyze_improved_code(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """改善されたコードの再解析"""
        payload = message["payload"]
        revised_code = payload["revised_code"]
        
        # 改善されたコードで新しい解析実行
        code_message = {
            "task_id": message["task_id"],
            "iteration": message.get("iteration", 1) + 1,
            "payload": {
                "code_content": revised_code,
                "language": "python",
                "review_options": {
                    "check_syntax": True,
                    "check_logic": True,
                    "check_performance": True,
                    "check_security": True
                }
            }
        }
        
        return await self._analyze_code(code_message)
    
    async def _check_python_syntax(self, code: str) -> List[Dict[str, Any]]:
        """Python構文チェック"""
        issues = []
        
        try:
            # AST解析で構文チェック
            ast.parse(code)
        except SyntaxError as e:
            issues.append({
                "line": e.lineno or 0,
                "type": "syntax_error",
                "severity": "error",
                "message": f"Syntax error: {e.msg}",
                "suggestion": "Fix syntax error"
            })
        
        # 基本的なスタイルチェック
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # docstringチェック
            if line.strip().startswith('def ') and 'def __' not in line:
                # 次の行がdocstringでない場合
                if i < len(lines) and not lines[i].strip().startswith('"""') and not lines[i].strip().startswith("'''"):
                    issues.append({
                        "line": i,
                        "type": "style",
                        "severity": "warning",
                        "message": "Missing function docstring",
                        "suggestion": "Add docstring explaining function purpose"
                    })
        
        return issues
    
    async def _check_python_logic(self, code: str) -> List[Dict[str, Any]]:
        """Python論理チェック"""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # 短い変数名チェック
            if 'def ' in line and '(' in line:
                # 関数定義から引数を抽出
                func_match = re.search(r'def\s+\w+\s*\(([^)]*)\)', line)
                if func_match:
                    params = func_match.group(1)
                    # 1文字の引数名をチェック
                    param_names = [p.strip().split(':')[0].strip() for p in params.split(',') if p.strip()]
                    for param in param_names:
                        if len(param) == 1 and param.isalpha():
                            issues.append({
                                "line": i,
                                "type": "naming",
                                "severity": "warning",
                                "message": f"Variable names '{param}' are not descriptive",
                                "suggestion": "Use descriptive names like 'length', 'width'"
                            })
            
            # 未使用変数チェック（簡易版）
            if ' = ' in line and '=' not in line.replace(' = ', ''):
                var_match = re.search(r'(\w+)\s*=', line)
                if var_match:
                    var_name = var_match.group(1)
                    if var_name not in code.replace(line, ''):  # 他の場所で使われていない
                        issues.append({
                            "line": i,
                            "type": "unused_variable",
                            "severity": "warning",
                            "message": f"Variable '{var_name}' is defined but never used",
                            "suggestion": "Remove unused variable or use it"
                        })
        
        return issues
    
    async def _check_python_performance(self, code: str) -> List[Dict[str, Any]]:
        """Pythonパフォーマンスチェック"""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # 非効率的な文字列結合チェック
            if '" + ' in line or "' + " in line:
                issues.append({
                    "line": i,
                    "type": "string_concatenation",
                    "severity": "info",
                    "message": "Inefficient string concatenation",
                    "suggestion": "Use f-string for better performance"
                })
        
        return issues
    
    async def _check_python_security(self, code: str) -> List[Dict[str, Any]]:
        """Pythonセキュリティチェック"""
        issues = []
        
        # 危険なパターンをチェック
        security_patterns = [
            (r'eval\s*\(', "eval_usage", "critical", "Use of eval() is dangerous"),
            (r'exec\s*\(', "exec_usage", "critical", "Use of exec() is dangerous"),
            (r'os\.system\s*\(', "command_injection", "critical", "os.system() is vulnerable to command injection"),
            (r'subprocess\.call\([^)]*shell=True', "command_injection", "critical", "subprocess with shell=True is dangerous"),
            # SQL injection用の改善されたパターン（f-stringとSQLを区別）
            (r'f["\'].*SELECT.*\{.*\}.*["\']', "sql_injection", "high", "Potential SQL injection vulnerability"),
            (r'f["\'].*INSERT.*\{.*\}.*["\']', "sql_injection", "high", "Potential SQL injection vulnerability"),
            (r'f["\'].*UPDATE.*\{.*\}.*["\']', "sql_injection", "high", "Potential SQL injection vulnerability"),
        ]
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, issue_type, severity, message in security_patterns:
                if re.search(pattern, line):
                    issues.append({
                        "line": i,
                        "type": issue_type,
                        "severity": severity,
                        "message": message,
                        "suggestion": "Use safer alternatives"
                    })
        
        return issues
    
    async def _calculate_code_metrics(self, code: str) -> Dict[str, Any]:
        """コードメトリクス計算"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # 基本メトリクス
        lines_of_code = len(non_empty_lines)
        
        # シンプルな複雑度計算（制御構造の数）
        complexity_keywords = ['if', 'elif', 'for', 'while', 'try', 'except']
        complexity_score = 1  # 基本複雑度
        for line in lines:
            for keyword in complexity_keywords:
                if f' {keyword} ' in line or line.strip().startswith(keyword + ' '):
                    complexity_score += 1
        
        # 保守性指数（簡易計算）
        # 短いコード、低複雑度、コメント有りで高スコア
        comment_lines = len([line for line in lines if line.strip().startswith('#') or '"""' in line])
        maintainability_index = max(0, 100 - complexity_score * 5 - max(0, lines_of_code - 50) + comment_lines * 2)
        
        return {
            "lines_of_code": lines_of_code,
            "complexity_score": complexity_score,
            "maintainability_index": min(100, maintainability_index)
        }


# メイン実行部分（既存のワーカーとの互換性維持）
async def main():
    """ワーカーのメイン実行"""
    config = {
        'circuit_breaker_threshold': 5,
        'circuit_breaker_timeout': 60,
        'analysis_timeout': 30
    }
    
    worker = CodeReviewTaskWorker(config)
    
    print("🚀 CodeReviewTaskWorker started")
    
    try:
        while True:
            await asyncio.sleep(10)
            print("💓 CodeReview TaskWorker heartbeat")
    except KeyboardInterrupt:
        print("\n🛑 CodeReview TaskWorker stopping...")
        await worker.shutdown()
        print("✅ CodeReview TaskWorker stopped")


if __name__ == "__main__":
    asyncio.run(main())