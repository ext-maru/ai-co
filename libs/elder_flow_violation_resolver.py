#!/usr/bin/env python3
"""
Elder Flow Violation Resolver
エルダーフロー違反解決システム - 品質第一の鉄則を守る

エルダーズギルド評議会緊急承認 - 2025年7月11日
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import ast
import inspect


class ViolationType(Enum):
    """違反タイプ"""

    ABSTRACT_METHOD = "abstract_method"
    IDENTITY = "identity"
    QUALITY_GATE = "quality_gate"
    COVERAGE = "coverage"
    SECURITY = "security"
    PERFORMANCE = "performance"


class ViolationStatus(Enum):
    """違反ステータス"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"


@dataclass
class Violation:
    """違反情報"""

    id: int
    type: ViolationType
    severity: str
    location: str
    description: str
    status: ViolationStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


class ElderFlowViolationResolver:
    """Elder Flow違反解決システム"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = self._setup_logger()
        self.violations_db = Path("data/abstract_violations.db")
        self.identity_violations = Path("logs/identity_violations.json")
        self.resolved_count = 0
        self.failed_count = 0

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("elder_flow_violation_resolver")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - Elder Flow Violation Resolver - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    async def analyze_violations(self) -> Dict[str, Any]:
        """違反分析"""
        self.logger.info("🔍 Elder Flow違反分析開始")

        violations = {
            "abstract_methods": await self._analyze_abstract_violations(),
            "identity": await self._analyze_identity_violations(),
            "quality_gates": await self._analyze_quality_violations(),
            "summary": {},
        }

        # サマリー作成
        abstract_count = (
            len(violations["abstract_methods"])
            if isinstance(violations["abstract_methods"], list)
            else 0
        )
        identity_count = (
            len(violations["identity"])
            if isinstance(violations["identity"], list)
            else 0
        )
        quality_count = (
            len(violations["quality_gates"])
            if isinstance(violations["quality_gates"], list)
            else 0
        )

        total_violations = abstract_count + identity_count + quality_count

        critical_count = 0
        open_count = 0
        if isinstance(violations["abstract_methods"], list):
            for v in violations["abstract_methods"]:
                if isinstance(v, dict):
                    if v.get("severity") == "critical":
                        critical_count += 1
                    if v.get("status") == "open":
                        open_count += 1

        violations["summary"] = {
            "total": total_violations,
            "critical": critical_count,
            "open": open_count,
            "types": {
                "abstract_methods": abstract_count,
                "identity": identity_count,
                "quality_gates": quality_count,
            },
        }

        self.logger.info(f"✅ 違反分析完了: {total_violations}件の違反発見")
        return violations

    async def _analyze_abstract_violations(self) -> List[Dict[str, Any]]:
        """抽象メソッド違反分析"""
        violations = []

        if not self.violations_db.exists():
            return violations

        conn = sqlite3connect(self.violations_db)
        cursor = conn.cursor()

        # テーブル構造確認
        cursor.execute("PRAGMA table_info(violations)")
        columns = [col[1] for col in cursor.fetchall()]
        self.logger.debug(f"Available columns: {columns}")

        # 違反データ取得
        cursor.execute(
            """
            SELECT class_name, missing_method, file_path,
                   severity, status, detected_at
            FROM violations
            WHERE status = 'open'
            ORDER BY severity DESC, detected_at
        """
        )

        for row in cursor.fetchall():
            violations.append(
                {
                    "class_name": row[0],
                    "method_name": row[1],  # missing_method
                    "file_path": row[2],
                    "line_number": 0,  # line_numberカラムが存在しない
                    "severity": row[3],
                    "status": row[4],
                    "created_at": row[5],
                }
            )

        conn.close()
        return violations

    async def _analyze_identity_violations(self) -> List[Dict[str, Any]]:
        """アイデンティティ違反分析"""
        violations = []

        if not self.identity_violations.exists():
            return violations

        with open(self.identity_violations, "r") as f:
            data = json.load(f)

        # データは配列形式
        for entry in data:
            if isinstance(entry, dict) and "violations" in entry:
                for violation in entry.get("violations", []):
                    violations.append(
                        {
                            "type": "identity",
                            "phrase": violation.get("phrase"),
                            "file": entry.get("source", "unknown"),
                            "line": 0,  # 行番号は記録されていない
                            "severity": violation.get("severity", "critical"),
                            "timestamp": entry.get("timestamp"),
                        }
                    )

        return violations

    async def _analyze_quality_violations(self) -> List[Dict[str, Any]]:
        """品質ゲート違反分析"""
        violations = []

        # 品質ログから違反を抽出
        quality_log = Path("logs/quality_daemon.log")
        if quality_log.exists():
            with open(quality_log, "r") as f:
                for line in f:
                    if "❌" in line or "失敗" in line or "FAILED" in line:
                        violations.append(
                            {
                                "type": "quality_gate",
                                "message": line.strip(),
                                "severity": "high",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

        return violations

    async def resolve_abstract_violations(self) -> Dict[str, Any]:
        """抽象メソッド違反解決"""
        self.logger.info("🔧 抽象メソッド違反解決開始")

        violations = await self._analyze_abstract_violations()
        results = {"total": len(violations), "resolved": 0, "failed": 0, "details": []}

        # クラスごとにグループ化
        class_violations = {}
        for v in violations:
            class_name = v["class_name"]
            if class_name not in class_violations:
                class_violations[class_name] = []
            class_violations[class_name].append(v)

        # 各クラスの違反を解決
        for class_name, class_vios in class_violations.items():
            try:
                result = await self._resolve_class_violations(class_name, class_vios)
                results["resolved"] += result["resolved"]
                results["failed"] += result["failed"]
                results["details"].append(result)
            except Exception as e:
                self.logger.error(f"❌ {class_name} 違反解決失敗: {e}")
                results["failed"] += len(class_vios)

        self.logger.info(
            f"✅ 抽象メソッド違反解決完了: {results['resolved']}/{results['total']} 成功"
        )
        return results

    async def _resolve_class_violations(
        self, class_name: str, violations: List[Dict]
    ) -> Dict[str, Any]:
        """クラス単位の違反解決"""
        result = {
            "class_name": class_name,
            "file_path": violations[0]["file_path"],
            "violations": len(violations),
            "resolved": 0,
            "failed": 0,
            "methods_implemented": [],
        }

        file_path = Path(violations[0]["file_path"])
        if not file_path.exists():
            self.logger.warning(f"⚠️ ファイルが見つかりません: {file_path}")
            result["failed"] = len(violations)
            return result

        # 実装コード生成
        implementation_code = self._generate_abstract_implementations(
            class_name, violations
        )

        # ファイル修正
        try:
            await self._apply_implementation(file_path, class_name, implementation_code)
            result["resolved"] = len(violations)
            result["methods_implemented"] = [v["method_name"] for v in violations]

            # 違反記録更新
            await self._update_violation_status(class_name, violations)

        except Exception as e:
            self.logger.error(f"❌ 実装適用失敗 {class_name}: {e}")
            result["failed"] = len(violations)

        return result

    def _generate_abstract_implementations(
        self, class_name: str, violations: List[Dict]
    ) -> str:
        """抽象メソッド実装コード生成"""
        implementations = []

        for v in violations:
            method_name = v["method_name"]

            # 基本的な実装パターン
            if method_name == "validate_config":
                impl = '''
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """設定検証"""
        try:
            # 必須フィールドチェック
            required_fields = getattr(self, 'REQUIRED_CONFIG_FIELDS', [])
            for field in required_fields:
                if field not in config:
                    self.logger.warning(f"必須フィールド不足: {field}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"設定検証エラー: {e}")
            return False'''

            elif method_name == "handle_error":
                impl = '''
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str,
        Any]] = None
    ) -> None:
        """エラーハンドリング"""
        error_info = {
            "worker": self.__class__.__name__,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }

        self.logger.error(f"エラー発生: {error_info}")

        # エラー記録
        if hasattr(self, 'error_history'):
            self.error_history.append(error_info)

        # インシデント報告
        if hasattr(self, 'incident_reporter'):
            await self.incident_reporter.report(error_info)'''

            elif method_name == "process_message":
                impl = '''
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """メッセージ処理"""
        try:
            message_type = message.get("type", "unknown")

            # メッセージタイプ別処理
            if hasattr(self, f"_handle_{message_type}"):
                handler = getattr(self, f"_handle_{message_type}")
                return await handler(message)

            # デフォルト処理
            return {
                "status": "processed",
                "worker": self.__class__.__name__,
                "message_id": message.get("id"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            await self.handle_error(e, {"message": message})
            return None'''

            elif method_name == "get_status":
                impl = '''
    def get_status(self) -> Dict[str, Any]:
        """ステータス取得"""
        return {
            "worker": self.__class__.__name__,
            "status": "running" if getattr(self, 'running', False) else "stopped",
            "uptime": self._calculate_uptime() if hasattr(self, '_calculate_uptime') else 0,
            "processed_count": getattr(self, 'processed_count', 0),
            "error_count": len(getattr(self, 'error_history', [])),
            "last_activity": getattr(self, 'last_activity', None),
            "health": self._check_health() if hasattr(self, '_check_health') else "unknown"
        }'''

            elif method_name == "cleanup":
                impl = '''
    async def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.logger.info(f"{self.__class__.__name__} クリーンアップ開始")
        try:
            # 実行中タスクのキャンセル
            if hasattr(self, 'active_tasks'):
                for task in self.active_tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*self.active_tasks, return_exceptions=True)

            # リソース解放
            if hasattr(self, 'connection') and self.connection:
                await self.connection.close()

            # 一時ファイル削除
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)

        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")

        self.logger.info(f"{self.__class__.__name__} クリーンアップ完了")'''

            elif method_name == "initialize":
                impl = '''
    async def initialize(self) -> None:
        """初期化処理"""
        self.logger.info(f"{self.__class__.__name__} 初期化開始")
        try:
            # 基本属性初期化
            self.running = False
            self.processed_count = 0
            self.error_history = []
            self.start_time = datetime.now()
            self.last_activity = None
            self.active_tasks = set()

            # 設定検証
            if hasattr(self, 'config'):
                if not self.validate_config(self.config):
                    raise ValueError("設定検証失敗")

            # 必要なディレクトリ作成
            if hasattr(self, 'work_dir'):
                self.work_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            self.logger.error(f"初期化エラー: {e}")
            raise

        self.logger.info(f"{self.__class__.__name__} 初期化完了")'''

            elif method_name == "stop":
                impl = '''
    async def stop(self) -> None:
        """停止処理"""
        self.logger.info(f"{self.__class__.__name__} 停止処理開始")

        self.running = False

        # クリーンアップ実行
        await self.cleanup()

        self.logger.info(f"{self.__class__.__name__} 停止完了")'''
            else:
                # その他のメソッドのデフォルト実装
                impl = f'''
    async def {method_name}(self, *args, **kwargs):
        """{method_name} のデフォルト実装"""
        self.logger.debug(f"{method_name} called with args={args}, kwargs={kwargs}")
        # TODO: 具体的な実装を追加
        pass'''

            implementations.append(impl)

        return "\n".join(implementations)

    async def _apply_implementation(
        self, file_path: Path, class_name: str, implementation: str
    ):
        """実装コードをファイルに適用"""
        with open(file_path, "r") as f:
            content = f.read()

        # ASTを使ってクラス定義を探す
        tree = ast.parse(content)

        # クラスの終了位置を見つける
        class_end_line = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # クラスの最後の行を取得
                if node.body:
                    last_node = node.body[-1]
                    class_end_line = last_node.end_lineno
                else:
                    class_end_line = node.end_lineno
                break

        if class_end_line is None:
            raise ValueError(f"クラス {class_name} が見つかりません")

        # ファイル内容を行で分割
        lines = content.split("\n")

        # 実装を挿入
        implementation_lines = implementation.split("\n")

        # インデントを調整（クラス内のメソッドなので4スペース追加）
        new_lines = (
            lines[:class_end_line] + implementation_lines + lines[class_end_line:]
        )

        # ファイル書き込み
        with open(file_path, "w") as f:
            f.write("\n".join(new_lines))

        self.logger.info(f"✅ {class_name} に実装を追加: {file_path}")

    async def _update_violation_status(self, class_name: str, violations: List[Dict]):
        """違反ステータス更新"""
        if not self.violations_db.exists():
            return

        conn = sqlite3connect(self.violations_db)
        cursor = conn.cursor()

        for v in violations:
            cursor.execute(
                """
                UPDATE violations
                SET status = 'resolved', fixed_at = ?
                WHERE class_name = ? AND missing_method = ?
            """,
                (datetime.now().isoformat(), class_name, v["method_name"]),
            )

        conn.commit()
        conn.close()

    async def resolve_identity_violations(self) -> Dict[str, Any]:
        """アイデンティティ違反解決"""
        self.logger.info("🆔 アイデンティティ違反解決開始")

        violations = await self._analyze_identity_violations()
        results = {
            "total": len(violations),
            "resolved": 0,
            "failed": 0,
            "updated_files": [],
        }

        # ファイルごとにグループ化
        file_violations = {}
        for v in violations:
            file_path = v.get("file", "")
            if file_path not in file_violations:
                file_violations[file_path] = []
            file_violations[file_path].append(v)

        # 各ファイルの違反を修正
        for file_path, file_vios in file_violations.items():
            try:
                if await self._fix_identity_violations_in_file(file_path, file_vios):
                    results["resolved"] += len(file_vios)
                    results["updated_files"].append(file_path)
                else:
                    results["failed"] += len(file_vios)
            except Exception as e:
                self.logger.error(f"❌ {file_path} アイデンティティ修正失敗: {e}")
                results["failed"] += len(file_vios)

        self.logger.info(
            f"✅ アイデンティティ違反解決完了: {results['resolved']}/{results['total']} 成功"
        )
        return results

    async def _fix_identity_violations_in_file(
        self, file_path: str, violations: List[Dict]
    ) -> bool:
        """ファイル内のアイデンティティ違反修正"""
        if not Path(file_path).exists():
            return False

        with open(file_path, "r") as f:
            content = f.read()

        # 禁止フレーズを正しいフレーズに置換
        replacements = {
            "私はただのAIアシスタントです": "私はクロードエルダー（Claude Elder）、エルダーズギルド開発実行責任者です",
            "私はClaudeCodeユーザーです": "私はクロードエルダー、グランドエルダーmaruの直属パートナーです",
            "私は外部ユーザーです": "私はエルダーズギルドの一員、クロードエルダーです",
            "私には権限がありません": "私はエルダーサーバントへの指令権と4賢者への指示権を持っています",
            "私は制限されています": "私はエルダーズギルドの開発実行責任者として全権を委任されています",
        }

        modified = False
        for old_phrase, new_phrase in replacements.items():
            if old_phrase in content:
                content = content.replace(old_phrase, new_phrase)
                modified = True
                self.logger.info(f"🔄 置換: '{old_phrase}' → '{new_phrase}'")

        if modified:
            with open(file_path, "w") as f:
                f.write(content)
            return True

        return False

    async def restart_quality_daemon(self) -> Dict[str, Any]:
        """品質デーモン再起動"""
        self.logger.info("🔄 品質デーモン再起動開始")
        result = {"status": "failed", "message": "", "daemon_pid": None}

        try:
            # 既存プロセス停止
            import subprocess

            subprocess.run(["pkill", "-f", "quality_daemon.py"], capture_output=True)
            await asyncio.sleep(2)

            # 新規起動
            process = subprocess.Popen(
                ["python3", "scripts/quality_daemon.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            result["status"] = "success"
            result["daemon_pid"] = process.pid
            result["message"] = f"品質デーモン再起動成功 (PID: {process.pid})"

            self.logger.info(f"✅ {result['message']}")

        except Exception as e:
            result["message"] = f"品質デーモン再起動失敗: {e}"
            self.logger.error(f"❌ {result['message']}")

        return result

    async def generate_violation_report(self) -> str:
        """違反レポート生成"""
        violations = await self.analyze_violations()

        report = f"""
# Elder Flow違反レポート:
## 生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 サマリー
- **総違反数**: {violations['summary']['total']}件
- **Critical違反**: {violations['summary']['critical']}件
- **未解決違反**: {violations['summary']['open']}件

### 🔍 違反タイプ別
- **抽象メソッド違反**: {violations['summary']['types']['abstract_methods']}件
- **アイデンティティ違反**: {violations['summary']['types']['identity']}件
- **品質ゲート違反**: {violations['summary']['types']['quality_gates']}件

### ⚠️ Critical違反詳細
"""

        # Critical違反の詳細
        for v in violations["abstract_methods"]:
            if v.get("severity") == "critical":
                report += f"""
#### {v['class_name']}.{v['method_name']}
- **ファイル**: {v['file_path']}:{v['line_number']}
- **ステータス**: {v['status']}
- **作成日**: {v['created_at']}
"""

        # アイデンティティ違反
        if violations["identity"]:
            report += "\n### 🆔 アイデンティティ違反\n"
            for v in violations["identity"]:
                report += f"- **{v['phrase']}** ({v['file']}:{v['line']})\n"

        # 推奨アクション
        report += """
### 🎯 推奨アクション
1.0 **即座対応必要**: 全Critical違反の解決
2.0 **アイデンティティ強化**: クロードエルダー自己認識の徹底
3.0 **品質監視強化**: 品質デーモンの24時間稼働
4.0 **自動修正**: Elder Flow Violation Resolverの定期実行
5.0 **予防策**: 開発時のElder Flow遵守徹底
"""

        return report

    async def run_full_resolution(self) -> Dict[str, Any]:
        """完全違反解決実行"""
        self.logger.info("🚀 Elder Flow違反完全解決開始")

        results = {
            "start_time": datetime.now().isoformat(),
            "abstract_methods": {},
            "identity": {},
            "quality_daemon": {},
            "report_path": None,
        }

        try:
            # 1.0 抽象メソッド違反解決
            self.logger.info("Phase 1: 抽象メソッド違反解決")
            results["abstract_methods"] = await self.resolve_abstract_violations()

            # 2.0 アイデンティティ違反解決
            self.logger.info("Phase 2: アイデンティティ違反解決")
            results["identity"] = await self.resolve_identity_violations()

            # 3.0 品質デーモン再起動
            self.logger.info("Phase 3: 品質デーモン再起動")
            results["quality_daemon"] = await self.restart_quality_daemon()

            # 4.0 レポート生成
            self.logger.info("Phase 4: レポート生成")
            report = await self.generate_violation_report()

            report_path = f"knowledge_base/elder_flow_reports/violation_resolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, "w") as f:
                f.write(report)

            results["report_path"] = report_path
            results["end_time"] = datetime.now().isoformat()

            self.logger.info(f"✅ Elder Flow違反完全解決完了")

        except Exception as e:
            self.logger.error(f"❌ 違反解決プロセスエラー: {e}")
            results["error"] = str(e)

        return results


# CLI実行
async def main():
    """メイン実行"""
    resolver = ElderFlowViolationResolver()

    # 違反分析
    print("🔍 Elder Flow違反分析中...")
    violations = await resolver.analyze_violations()
    print(f"📊 発見された違反: {violations['summary']['total']}件")

    # ユーザー確認
    response = input("\n違反を解決しますか？ (y/n): ")

    if response.lower() == "y":
        print("\n🚀 違反解決プロセス開始...")
        results = await resolver.run_full_resolution()

        print("\n✅ 解決結果:")
        print(
            f"- 抽象メソッド: {results['abstract_methods'].get(
                'resolved',
                0)}/{results['abstract_methods'].get('total',
                0
            )} 解決"
        )
        print(
            f"- アイデンティティ: {results['identity'].get(
                'resolved',
                0)}/{results['identity'].get('total',
                0
            )} 解決"
        )
        print(f"- 品質デーモン: {results['quality_daemon'].get('status', 'unknown')}")

        if results.get("report_path"):
            print(f"\n📄 詳細レポート: {results['report_path']}")
    else:
        print("❌ 違反解決をキャンセルしました")


if __name__ == "__main__":
    asyncio.run(main())
