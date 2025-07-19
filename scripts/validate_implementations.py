#!/usr/bin/env python3
"""
実装検証システム - 4賢者会議決定事項
抽象メソッドの実装漏れを自動検出
"""

import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImplementationValidator:
    """抽象クラス実装検証器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.errors = []
        self.warnings = []

    def validate_all_implementations(self) -> Dict[str, Any]:
        """全ての実装を検証"""
        logger.info("🔍 抽象クラス実装検証開始")

        results = {
            "total_classes": 0,
            "abstract_classes": 0,
            "implementation_errors": [],
            "warnings": [],
            "success": True,
        }

        # 主要モジュールの検証
        modules_to_check = [
            "libs.task_history_db",
            "libs.knowledge_base_manager",
            "libs.incident_manager",
            "libs.enhanced_rag_manager",
            "libs.claude_task_tracker",
            "workers.enhanced_task_worker",
            "workers.pm_worker",
            "core.base_worker",
            "core.base_manager",
        ]

        for module_name in modules_to_check:
            try:
                module_results = self._validate_module(module_name)
                results["total_classes"] += module_results["total_classes"]
                results["abstract_classes"] += module_results["abstract_classes"]
                results["implementation_errors"].extend(module_results["errors"])
                results["warnings"].extend(module_results["warnings"])

            except Exception as e:
                error_msg = f"モジュール {module_name} の検証エラー: {e}"
                results["implementation_errors"].append(error_msg)
                logger.error(error_msg)

        # 結果判定
        if results["implementation_errors"]:
            results["success"] = False
            logger.error(f"❌ 実装エラー {len(results['implementation_errors'])} 件発見")
        else:
            logger.info("✅ 全ての実装検証完了")

        return results

    def _validate_module(self, module_name: str) -> Dict[str, Any]:
        """モジュールの検証"""
        results = {
            "module": module_name,
            "total_classes": 0,
            "abstract_classes": 0,
            "errors": [],
            "warnings": [],
        }

        try:
            module = importlib.import_module(module_name)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module_name:
                    continue  # 他のモジュールから import されたクラスはスキップ

                results["total_classes"] += 1

                # 抽象クラスの検証
                if hasattr(obj, "__abstractmethods__"):
                    if obj.__abstractmethods__:
                        results["abstract_classes"] += 1

                        # 抽象メソッドが実装されているかチェック
                        unimplemented = []
                        for abstract_method in obj.__abstractmethods__:
                            if abstract_method not in obj.__dict__:
                                unimplemented.append(abstract_method)

                        if unimplemented:
                            error_msg = (
                                f"{module_name}.{name}: 未実装抽象メソッド {unimplemented}"
                            )
                            results["errors"].append(error_msg)
                        else:
                            logger.info(f"✅ {module_name}.{name}: 抽象メソッド実装完了")

                # BaseWorker/BaseManagerの継承チェック
                if any(
                    base.__name__ in ["BaseWorker", "BaseManager"]
                    for base in obj.__bases__
                ):
                    validation_result = self._validate_base_class_implementation(obj)
                    if validation_result["errors"]:
                        results["errors"].extend(validation_result["errors"])
                    if validation_result["warnings"]:
                        results["warnings"].extend(validation_result["warnings"])

        except ImportError as e:
            results["errors"].append(f"モジュールインポートエラー {module_name}: {e}")
        except Exception as e:
            results["errors"].append(f"モジュール検証エラー {module_name}: {e}")

        return results

    def _validate_base_class_implementation(self, cls) -> Dict[str, List[str]]:
        """BaseWorker/BaseManager継承クラスの検証"""
        results = {"errors": [], "warnings": []}

        # 必須メソッドの存在チェック
        required_methods = {
            "BaseWorker": ["process_message"],
            "BaseManager": ["initialize"],
        }

        for base in cls.__bases__:
            if base.__name__ in required_methods:
                for method_name in required_methods[base.__name__]:
                    if not hasattr(cls, method_name):
                        results["errors"].append(
                            f"{cls.__name__}: 必須メソッド {method_name} が未実装"
                        )
                    elif method_name not in cls.__dict__:
                        results["warnings"].append(
                            f"{cls.__name__}: {method_name} が継承元のデフォルト実装を使用"
                        )

        # docstringの存在チェック
        if not cls.__doc__:
            results["warnings"].append(f"{cls.__name__}: docstring が未記述")

        return results


def main():
    """メイン処理"""
    print("🧙‍♂️ 4賢者システム: 実装検証開始")

    validator = ImplementationValidator()
    results = validator.validate_all_implementations()

    # 結果レポート
    print(f"\n📊 検証結果:")
    print(f"  総クラス数: {results['total_classes']}")
    print(f"  抽象クラス数: {results['abstract_classes']}")
    print(f"  エラー数: {len(results['implementation_errors'])}")
    print(f"  警告数: {len(results['warnings'])}")

    if results["implementation_errors"]:
        print(f"\n❌ 実装エラー:")
        for error in results["implementation_errors"]:
            print(f"  - {error}")

    if results["warnings"]:
        print(f"\n⚠️ 警告:")
        for warning in results["warnings"]:
            print(f"  - {warning}")

    if results["success"]:
        print(f"\n✅ 全ての実装検証完了！")
        sys.exit(0)
    else:
        print(f"\n❌ 実装エラーが見つかりました")
        sys.exit(1)


if __name__ == "__main__":
    main()
