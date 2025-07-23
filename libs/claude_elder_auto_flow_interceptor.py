#!/usr/bin/env python3
"""
Claude Elder Auto Flow Interceptor - クロードエルダー自動Elder Flow適用システム
Created: 2025-01-20
Author: Claude Elder

クロードエルダーが直で呼び出された場合、全ての開発系タスクを自動的にElder Flowで処理する
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Elder Flow実行は軽量版で直接実装（依存関係最小化）

logger = logging.getLogger("claude_elder_auto_flow")


class ClaudeElderAutoFlowInterceptor:
    """クロードエルダー自動Elder Flow適用システム"""

    def __init__(self):
        """初期化メソッド"""
        self.auto_flow_patterns = self._load_auto_flow_patterns()
        self.config_file = Path.home() / ".claude_elder_auto_flow_config.json"
        self._load_config()
        self.bypass_keywords = ["help", "status", "explain", "show", "list", "describe"]

    def _load_auto_flow_patterns(self) -> List[Dict[str, Any]]:
        """Elder Flow自動適用パターンの読み込み"""
        return [
            # CLAUDE.mdに定義されている自動適用条件
            {
                "category": "implementation",
                "patterns": [
                    r"実装|implement|add|create|build|develop|新機能|作成|構築",
                    r"OAuth|認証|システム|API|機能|コンポーネント|ライブラリ",
                ],
                "priority": "high",
            },
            {
                "category": "fix",
                "patterns": [
                    r"修正|fix|bug|エラー|error|問題|issue|バグ|直す",
                    r"デバッグ|debug|解決|repair|治す",
                ],
                "priority": "high",
            },
            {
                "category": "optimization",
                "patterns": [
                    r"最適化|optimize|リファクタリング|refactor|改善|improve",
                    r"パフォーマンス|performance|速度|メモリ|効率",
                ],
                "priority": "medium",
            },
            {
                "category": "security",
                "patterns": [
                    r"セキュリティ|security|認証|authentication|暗号|encrypt",
                    r"脆弱性|vulnerability|権限|permission|アクセス制御",
                ],
                "priority": "high",
            },
            {
                "category": "testing",
                "patterns": [
                    r"テスト|test|TDD|単体テスト|統合テスト|カバレッジ",
                    r"検証|validation|自動テスト|pytest",
                ],
                "priority": "medium",
            },
            {
                "category": "forced",
                "patterns": [
                    r"elder flow|elder-flow|エルダーフロー|エルダー・フロー",
                    r"elder flowで|elder-flowで|エルダーフローで",
                ],
                "priority": "high",
                "force": True,
            },
        ]

    def should_apply_elder_flow(
        self, user_input: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Elder Flow適用判定"""
        if not self.enabled:
            return False, None

        user_input_lower = user_input.lower()

        # バイパスキーワードをチェック
        if any(keyword in user_input_lower for keyword in self.bypass_keywords):
            return False, None

        # パターンマッチング
        for pattern_group in self.auto_flow_patterns:
            patterns = pattern_group["patterns"]
            category = pattern_group["category"]

            # すべてのパターンをチェック
            matches = sum(
                1 for pattern in patterns if re.search(pattern, user_input_lower)
            )

            # 強制適用の場合
            if pattern_group.get("force", False) and matches > 0:
                return True, {
                    "category": category,
                    "priority": pattern_group["priority"],
                    "confidence": 1.0,
                    "matched_patterns": matches,
                    "force": True,
                }

            # 通常の適用判定（複数パターンマッチまたは高信頼度）
            if matches >= 1:  # 1つ以上のパターンマッチで適用
                confidence = min(matches / len(patterns), 1.0)

                # 信頼度が0.3以上で適用
                if confidence >= 0.3:
                    return True, {
                        "category": category,
                        "priority": pattern_group["priority"],
                        "confidence": confidence,
                        "matched_patterns": matches,
                        "force": False,
                    }

        return False, None

    async def process_user_request(self, user_input: str) -> Dict[str, Any]:
        """ユーザーリクエストの処理"""
        should_apply, flow_info = self.should_apply_elder_flow(user_input)

        if not should_apply:
            return {
                "status": "bypass",
                "message": "通常のClaude Elder処理で実行します",
                "user_input": user_input,
                "reason": "Elder Flow適用条件に該当しません",
            }

        # Elder Flow自動適用
        logger.info(
            f"🌊 Elder Flow自動適用開始: {flow_info['category']} (信頼度: {flow_info['confidence']:.2f})"
        )

        try:
            # Elder Flow実行（軽量版 - シンプルなコマンド実行）
            result = await self._execute_elder_flow_lightweight(user_input, flow_info["priority"])

            if result.get("error"):
                # Elder Flow失敗時は通常処理にフォールバック
                logger.warning(f"Elder Flow実行失敗、通常処理にフォールバック: {result['error']}")
                return {
                    "status": "fallback",
                    "message": "Elder Flow実行に失敗しました。通常のClaude Elder処理で実行します",
                    "user_input": user_input,
                    "elder_flow_error": result["error"],
                    "flow_info": flow_info,
                }

            return {
                "status": "success",
                "message": "Elder Flowで正常に処理されました",
                "user_input": user_input,
                "flow_info": flow_info,
                "elder_flow_result": result,
                "flow_id": result.get("flow_id"),
                "execution_time": result.get("execution_time"),
            }

        except Exception as e:
            logger.error(f"Elder Flow自動実行エラー: {e}")
            return {
                "status": "error",
                "message": "Elder Flow実行中にエラーが発生しました。通常のClaude Elder処理で実行します",
                "user_input": user_input,
                "error": str(e),
                "flow_info": flow_info,
            }

    def enable_auto_flow(self) -> None:
        """Elder Flow自動適用を有効化"""
        self.enabled = True
        self._save_config()
        logger.info("🌊 Elder Flow自動適用が有効化されました")

    def disable_auto_flow(self) -> None:
        """Elder Flow自動適用を無効化"""
        self.enabled = False
        self._save_config()
        logger.info("⏸️ Elder Flow自動適用が無効化されました")

    def add_bypass_keyword(self, keyword: str) -> None:
        """バイパスキーワードを追加"""
        if keyword not in self.bypass_keywords:
            self.bypass_keywords.append(keyword)
            logger.info(f"➕ バイパスキーワード追加: {keyword}")

    def remove_bypass_keyword(self, keyword: str) -> None:
        """バイパスキーワードを削除"""
        if keyword in self.bypass_keywords:
            self.bypass_keywords.remove(keyword)
            logger.info(f"➖ バイパスキーワード削除: {keyword}")

    def get_status(self) -> Dict[str, Any]:
        """インターセプター状態取得"""
        return {
            "enabled": self.enabled,
            "pattern_categories": len(self.auto_flow_patterns),
            "bypass_keywords": self.bypass_keywords,
            "total_patterns": sum(
                len(pg["patterns"]) for pg in self.auto_flow_patterns
            ),
            "version": "1.0.0",
        }

    def test_pattern_matching(self, test_input: str) -> Dict[str, Any]:
        """パターンマッチングのテスト"""
        should_apply, flow_info = self.should_apply_elder_flow(test_input)

        return {
            "input": test_input,
            "should_apply_elder_flow": should_apply,
            "flow_info": flow_info,
            "pattern_matches": self._analyze_pattern_matches(test_input),
        }

    def _analyze_pattern_matches(self, text: str) -> List[Dict[str, Any]]:
        """パターンマッチング詳細分析"""
        results = []
        text_lower = text.lower()

        # 繰り返し処理
        for pattern_group in self.auto_flow_patterns:
            matches = []
            for pattern in pattern_group["patterns"]:
                if re.search(pattern, text_lower):
                    matches.append(pattern)

            if matches:
                results.append(
                    {
                        "category": pattern_group["category"],
                        "priority": pattern_group["priority"],
                        "matched_patterns": matches,
                        "confidence": len(matches) / len(pattern_group["patterns"]),
                        "force": pattern_group.get("force", False),
                    }
                )

        return results

    def _load_config(self) -> None:
        """設定ファイルから状態を読み込み"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.enabled = config.get('enabled', True)
            except Exception as e:
                logger.warning(f"設定ファイル読み込みエラー: {e}")
                self.enabled = True
        else:
            self.enabled = True

    def _save_config(self) -> None:
        """設定ファイルに状態を保存"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'enabled': self.enabled}, f)
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")

    async def _execute_elder_flow_lightweight(
        self,
        task_name: str,
        priority: str
    ) -> Dict[str, Any]:
        """軽量版Elder Flow実行（依存関係最小化）"""
        import subprocess
        import uuid
        
        flow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Elder Flow CLIコマンドを実行
            cmd = [
                "python3", 
                f"{project_root}/scripts/elder-flow", 
                "execute", 
                task_name,
                "--priority", priority,
                "--retry"
            ]
            
            logger.info(f"🚀 Elder Flow軽量実行: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root
            )
            
            stdout, stderr = await process.communicate()
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            if process.returncode == 0:
                return {
                    "flow_id": flow_id,
                    "status": "success",
                    "stdout": stdout.decode('utf-8'),
                    "execution_time": end_time.isoformat(),
                    "duration": execution_time
                }
            else:
                return {
                    "error": f"Elder Flow failed with return code {process.returncode}",
                    "stderr": stderr.decode('utf-8'),
                    "stdout": stdout.decode('utf-8'),
                    "execution_time": end_time.isoformat(),
                    "duration": execution_time
                }
                
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "error": f"Elder Flow execution failed: {str(e)}",
                "execution_time": end_time.isoformat(),
                "duration": execution_time
            }


# シングルトンインスタンス
_claude_elder_interceptor = None


def get_claude_elder_interceptor() -> ClaudeElderAutoFlowInterceptor:
    """Claude Elder Auto Flow Interceptorのシングルトンインスタンス取得"""
    global _claude_elder_interceptor
    if _claude_elder_interceptor is None:
        _claude_elder_interceptor = ClaudeElderAutoFlowInterceptor()
    return _claude_elder_interceptor


# CLI実行用
async def main():
    """mainメソッド"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Elder Auto Flow Interceptor")
    parser.add_argument(
        "action", choices=["status", "test", "enable", "disable"], help="実行するアクション"
    )
    parser.add_argument("--input", help="テスト用入力文字列")

    args = parser.parse_args()

    interceptor = get_claude_elder_interceptor()

    if args.action == "status":
        status = interceptor.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.action == "test":
        if not args.input:
            print("❌ --inputオプションが必要です")
            return 1

        result = interceptor.test_pattern_matching(args.input)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "enable":
        interceptor.enable_auto_flow()
        print("✅ Elder Flow自動適用が有効化されました")

    elif args.action == "disable":
        interceptor.disable_auto_flow()
        print("⏸️ Elder Flow自動適用が無効化されました")

    return 0


if __name__ == "__main__":
    asyncio.run(main())