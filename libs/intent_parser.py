#!/usr/bin/env python3
"""
Intent Parser v0.1
自然言語からコマンドへの変換システム

💭 nWo Natural Language Parser Implementation
Convert maru様's natural language to structured commands
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging

from libs.mind_reading_core import IntentResult, IntentType


class CommandType(Enum):
    """コマンドタイプ"""
    CREATE = "create"          # 作成系コマンド
    UPDATE = "update"          # 更新系コマンド
    DELETE = "delete"          # 削除系コマンド
    READ = "read"              # 読み取り系コマンド
    EXECUTE = "execute"        # 実行系コマンド
    ANALYZE = "analyze"        # 分析系コマンド
    CONFIGURE = "configure"    # 設定系コマンド
    DEPLOY = "deploy"          # デプロイ系コマンド
    TEST = "test"              # テスト系コマンド
    OPTIMIZE = "optimize"      # 最適化系コマンド


class ParameterType(Enum):
    """パラメータタイプ"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    FILE_PATH = "file_path"
    URL = "url"
    DATE = "date"
    CODE = "code"
    CONFIG = "config"


@dataclass
class ParsedCommand:
    """パースされたコマンド"""
    command_type: CommandType
    action: str
    target: str
    parameters: Dict[str, Any]
    modifiers: List[str]
    context: Dict[str, Any]
    confidence: float
    original_text: str
    timestamp: str


@dataclass
class CommandTemplate:
    """コマンドテンプレート"""
    template_id: str
    command_type: CommandType
    pattern: str
    required_params: List[str]
    optional_params: List[str]
    examples: List[str]
    description: str


class IntentParser:
    """Intent Parser - 自然言語をコマンドに変換"""

    def __init__(self, template_dir: str = "data/command_templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logger()

        # テンプレート管理
        self.templates_file = self.template_dir / "command_templates.json"
        self.parse_history_file = self.template_dir / "parse_history.json"

        # メモリ内データ
        self.command_templates: List[CommandTemplate] = []
        self.parse_cache: Dict[str, ParsedCommand] = {}

        # 初期化
        self._load_default_templates()
        self._load_custom_templates()

        self.logger.info("💭 Intent Parser v0.1 initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("intent_parser")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Intent Parser - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_default_templates(self):
        """デフォルトテンプレートの読み込み"""
        self.command_templates = [
            # CREATE系
            CommandTemplate(
                template_id="create_feature",
                command_type=CommandType.CREATE,
                pattern=r"(.+?)を(実装|作成|作って|開発|build|create)",
                required_params=["feature_name"],
                optional_params=["technology", "priority"],
                examples=["OAuth認証を実装", "APIを作成して"],
                description="新機能の作成"
            ),
            CommandTemplate(
                template_id="create_file",
                command_type=CommandType.CREATE,
                pattern=r"(.+?)(ファイル|file)を(作成|作って|create)",
                required_params=["file_name"],
                optional_params=["content", "directory"],
                examples=["config.jsonファイルを作成", "READMEファイルを作って"],
                description="ファイルの作成"
            ),

            # UPDATE系
            CommandTemplate(
                template_id="update_code",
                command_type=CommandType.UPDATE,
                pattern=r"(.+?)を(修正|更新|変更|update|fix)",
                required_params=["target"],
                optional_params=["change_type", "reason"],
                examples=["バグを修正", "設定を更新"],
                description="コードの更新"
            ),

            # DELETE系
            CommandTemplate(
                template_id="delete_resource",
                command_type=CommandType.DELETE,
                pattern=r"(.+?)を(削除|消して|remove|delete)",
                required_params=["target"],
                optional_params=["confirm", "backup"],
                examples=["古いファイルを削除", "キャッシュを消して"],
                description="リソースの削除"
            ),

            # EXECUTE系
            CommandTemplate(
                template_id="execute_command",
                command_type=CommandType.EXECUTE,
                pattern=r"(.+?)を(実行|動かして|run|execute)",
                required_params=["command"],
                optional_params=["args", "env"],
                examples=["テストを実行", "ビルドを動かして"],
                description="コマンドの実行"
            ),

            # TEST系
            CommandTemplate(
                template_id="run_test",
                command_type=CommandType.TEST,
                pattern=r"(.+?)を?(テスト|test)",
                required_params=["test_target"],
                optional_params=["test_type", "coverage"],
                examples=["APIをテスト", "全体をテスト"],
                description="テストの実行"
            ),

            # OPTIMIZE系
            CommandTemplate(
                template_id="optimize_performance",
                command_type=CommandType.OPTIMIZE,
                pattern=r"(.+?)を(最適化|高速化|optimize)",
                required_params=["optimization_target"],
                optional_params=["metrics", "constraints"],
                examples=["DBクエリを最適化", "レンダリングを高速化"],
                description="パフォーマンス最適化"
            )
        ]

    def _load_custom_templates(self):
        """カスタムテンプレートの読み込み"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                    custom_templates = [
                        CommandTemplate(**t) for t in data
                    ]
                    self.command_templates.extend(custom_templates)
                    self.logger.info(f"📋 Loaded {len(custom_templates)} custom templates")
            except Exception as e:
                self.logger.error(f"Template loading error: {e}")

    async def parse_intent(self, intent_result: IntentResult, original_text: str) -> ParsedCommand:
        """
        IntentResultから構造化コマンドへの変換

        Args:
            intent_result: Mind Reading Coreの結果
            original_text: 元の入力テキスト

        Returns:
            ParsedCommand: 構造化されたコマンド
        """
        self.logger.info(f"💭 Parsing intent: {intent_result.intent_type.value}")

        # キャッシュチェック
        cache_key = f"{intent_result.intent_type.value}:{original_text}"
        if cache_key in self.parse_cache:
            return self.parse_cache[cache_key]

        # IntentTypeに基づくコマンドタイプマッピング
        command_type = self._map_intent_to_command(intent_result.intent_type)

        # テキストからアクションとターゲットを抽出
        action, target = self._extract_action_target(original_text, intent_result)

        # パラメータ抽出
        parameters = self._extract_command_parameters(
            original_text,
            intent_result,
            command_type
        )

        # モディファイア抽出（緊急、重要など）
        modifiers = self._extract_modifiers(original_text, intent_result)

        # コンテキスト情報
        context = {
            "intent_type": intent_result.intent_type.value,
            "confidence_level": intent_result.confidence_level.value,
            "priority": intent_result.priority,
            "urgency": intent_result.urgency,
            "keywords": intent_result.extracted_keywords
        }

        parsed_command = ParsedCommand(
            command_type=command_type,
            action=action,
            target=target,
            parameters=parameters,
            modifiers=modifiers,
            context=context,
            confidence=intent_result.confidence,
            original_text=original_text,
            timestamp=datetime.now().isoformat()
        )

        # キャッシュに保存
        self.parse_cache[cache_key] = parsed_command

        # 履歴保存
        await self._save_parse_history(parsed_command)

        self.logger.info(f"✅ Parsed command: {command_type.value} {action} {target}")

        return parsed_command

    def _map_intent_to_command(self, intent_type: IntentType) -> CommandType:
        """IntentTypeをCommandTypeにマッピング"""
        mapping = {
            IntentType.DEVELOPMENT: CommandType.CREATE,
            IntentType.FEATURE_REQUEST: CommandType.CREATE,
            IntentType.BUG_FIX: CommandType.UPDATE,
            IntentType.OPTIMIZATION: CommandType.OPTIMIZE,
            IntentType.RESEARCH: CommandType.ANALYZE,
            IntentType.STRATEGY: CommandType.CONFIGURE,
            IntentType.DIRECTIVE: CommandType.EXECUTE,
            IntentType.QUESTION: CommandType.READ,
            IntentType.PRAISE: CommandType.READ,
            IntentType.VISION: CommandType.ANALYZE
        }

        return mapping.get(intent_type, CommandType.EXECUTE)

    def _extract_action_target(self, text: str, intent_result: IntentResult) -> Tuple[str, str]:
        """アクションとターゲットの抽出"""
        # テンプレートマッチング
        for template in self.command_templates:
            match = re.search(template.pattern, text)
            if match:
                groups = match.groups()
                if len(groups) >= 1:
                    target = groups[0]
                    action = template.template_id.split('_')[0]  # create, update, etc.
                    return action, target

        # デフォルト処理
        keywords = intent_result.extracted_keywords

        # アクション候補
        action_keywords = ["実装", "作成", "修正", "削除", "実行", "テスト", "最適化"]
        action = "execute"  # デフォルト

        for keyword in keywords:
            for action_keyword in action_keywords:
                if action_keyword in keyword:
                    action = self._normalize_action(action_keyword)
                    break

        # ターゲット候補（最も長いキーワードをターゲットとする）
        target = max(keywords, key=len) if keywords else "unknown"

        return action, target

    def _normalize_action(self, action_keyword: str) -> str:
        """アクションキーワードの正規化"""
        action_map = {
            "実装": "create",
            "作成": "create",
            "作って": "create",
            "修正": "update",
            "更新": "update",
            "削除": "delete",
            "消して": "delete",
            "実行": "execute",
            "動かして": "execute",
            "テスト": "test",
            "最適化": "optimize",
            "高速化": "optimize"
        }

        return action_map.get(action_keyword, action_keyword)

    def _extract_command_parameters(
        self,
        text: str,
        intent_result: IntentResult,
        command_type: CommandType
    ) -> Dict[str, Any]:
        """コマンドパラメータの抽出"""
        parameters = {}

        # IntentResultのパラメータを基に
        parameters.update(intent_result.parameters)

        # コマンドタイプ別の特別な処理
        if command_type == CommandType.CREATE:
            # 技術スタック
            if "technologies" in parameters and parameters["technologies"]:
                parameters["tech_stack"] = parameters["technologies"]

            # ファイルタイプ
            if "file_types" in parameters and parameters["file_types"]:
                parameters["output_format"] = parameters["file_types"][0]

        elif command_type == CommandType.UPDATE:
            # 重要度
            if "severity" in parameters:
                parameters["importance"] = parameters["severity"]

        elif command_type == CommandType.TEST:
            # テストタイプ
            if "unit" in text or "ユニット" in text:
                parameters["test_type"] = "unit"
            elif "integration" in text or "統合" in text:
                parameters["test_type"] = "integration"
            else:
                parameters["test_type"] = "all"

        elif command_type == CommandType.OPTIMIZE:
            # 最適化目標
            if "速度" in text or "speed" in text:
                parameters["optimization_goal"] = "speed"
            elif "メモリ" in text or "memory" in text:
                parameters["optimization_goal"] = "memory"
            else:
                parameters["optimization_goal"] = "general"

        return parameters

    def _extract_modifiers(self, text: str, intent_result: IntentResult) -> List[str]:
        """モディファイアの抽出"""
        modifiers = []

        # 緊急度
        if intent_result.urgency in ["urgent", "high"]:
            modifiers.append("urgent")

        # 優先度
        if intent_result.priority in ["critical", "high"]:
            modifiers.append("high_priority")

        # その他のモディファイア
        modifier_patterns = {
            "force": ["強制", "force", "必ず"],
            "dry_run": ["テスト実行", "dry-run", "シミュレーション"],
            "verbose": ["詳細", "verbose", "詳しく"],
            "quiet": ["静かに", "quiet", "サイレント"]
        }

        text_lower = text.lower()
        for modifier, patterns in modifier_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                modifiers.append(modifier)

        return modifiers

    async def generate_command(self, parsed_command: ParsedCommand) -> str:
        """
        ParsedCommandから実行可能なコマンド文字列を生成

        Args:
            parsed_command: パース済みコマンド

        Returns:
            str: 実行可能なコマンド文字列
        """
        # コマンドタイプ別の生成
        if parsed_command.command_type == CommandType.CREATE:
            return self._generate_create_command(parsed_command)
        elif parsed_command.command_type == CommandType.UPDATE:
            return self._generate_update_command(parsed_command)
        elif parsed_command.command_type == CommandType.DELETE:
            return self._generate_delete_command(parsed_command)
        elif parsed_command.command_type == CommandType.EXECUTE:
            return self._generate_execute_command(parsed_command)
        elif parsed_command.command_type == CommandType.TEST:
            return self._generate_test_command(parsed_command)
        elif parsed_command.command_type == CommandType.OPTIMIZE:
            return self._generate_optimize_command(parsed_command)
        else:
            return f"echo 'Command type {parsed_command.command_type.value} not implemented'"

    def _generate_create_command(self, parsed_command: ParsedCommand) -> str:
        """CREATE系コマンドの生成"""
        target = parsed_command.target
        params = parsed_command.parameters

        # Elder Flow実行
        if "elder" in target.lower() or "flow" in target.lower():
            priority = params.get("priority", "medium")
            return f'elder-flow execute "{target}" --priority {priority}'

        # ファイル作成
        if "file" in target or "ファイル" in target:
            file_name = params.get("file_name", target)
            return f'touch {file_name}'

        # デフォルト：TDD開発
        return f'ai-tdd new "{target}" "Implementation of {target}"'

    def _generate_update_command(self, parsed_command: ParsedCommand) -> str:
        """UPDATE系コマンドの生成"""
        target = parsed_command.target

        # バグ修正
        if "bug" in target or "バグ" in target:
            return f'ai-fix-bug "{target}"'

        # デフォルト：編集
        return f'ai-edit "{target}"'

    def _generate_delete_command(self, parsed_command: ParsedCommand) -> str:
        """DELETE系コマンドの生成"""
        target = parsed_command.target
        modifiers = parsed_command.modifiers

        # 強制フラグ
        force_flag = "-f" if "force" in modifiers else "-i"

        return f'rm {force_flag} {target}'

    def _generate_execute_command(self, parsed_command: ParsedCommand) -> str:
        """EXECUTE系コマンドの生成"""
        target = parsed_command.target

        # よく使うコマンドのマッピング
        common_commands = {
            "test": "pytest",
            "build": "python setup.py build",
            "deploy": "./deploy.sh",
            "start": "ai-start",
            "stop": "ai-stop"
        }

        for key, command in common_commands.items():
            if key in target.lower():
                return command

        return target

    def _generate_test_command(self, parsed_command: ParsedCommand) -> str:
        """TEST系コマンドの生成"""
        target = parsed_command.target
        params = parsed_command.parameters
        test_type = params.get("test_type", "all")

        if test_type == "unit":
            return f'pytest tests/unit/ -v'
        elif test_type == "integration":
            return f'pytest tests/integration/ -v'
        else:
            return f'pytest -v'

    def _generate_optimize_command(self, parsed_command: ParsedCommand) -> str:
        """OPTIMIZE系コマンドの生成"""
        target = parsed_command.target
        params = parsed_command.parameters
        goal = params.get("optimization_goal", "general")

        return f'ai-optimize "{target}" --goal {goal}'

    async def _save_parse_history(self, parsed_command: ParsedCommand):
        """パース履歴の保存"""
        try:
            history = []
            if self.parse_history_file.exists():
                with open(self.parse_history_file, 'r') as f:
                    history = json.load(f)

            # ParsedCommandを辞書に変換
            command_dict = asdict(parsed_command)
            command_dict["command_type"] = parsed_command.command_type.value

            history.append(command_dict)

            # 最大1000件まで保持
            if len(history) > 1000:
                history = history[-1000:]

            with open(self.parse_history_file, 'w') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Parse history saving error: {e}")

    def add_custom_template(self, template: CommandTemplate):
        """カスタムテンプレートの追加"""
        self.command_templates.append(template)
        self._save_templates()

    def _save_templates(self):
        """テンプレートの保存"""
        try:
            # デフォルトテンプレートは除外
            custom_templates = [
                t for t in self.command_templates
                if not t.template_id.startswith("create_")
                and not t.template_id.startswith("update_")
                and not t.template_id.startswith("delete_")
                and not t.template_id.startswith("execute_")
                and not t.template_id.startswith("run_")
                and not t.template_id.startswith("optimize_")
            ]

            template_dicts = [asdict(t) for t in custom_templates]

            with open(self.templates_file, 'w') as f:
                json.dump(template_dicts, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Template saving error: {e}")

    def get_command_suggestions(self, partial_text: str) -> List[str]:
        """コマンド候補の取得"""
        suggestions = []

        for template in self.command_templates:
            for example in template.examples:
                if partial_text.lower() in example.lower():
                    suggestions.append(example)

        return suggestions[:5]  # 上位5個まで


# デモと使用例
async def demo_intent_parser():
    """Intent Parser デモ"""
    print("💭 Intent Parser v0.1 Demo")
    print("=" * 50)

    from libs.mind_reading_core import MindReadingCore

    # 初期化
    mind_reader = MindReadingCore()
    parser = IntentParser()

    # テストケース
    test_cases = [
        "OAuth2.0認証システムを実装してください",
        "バグを今すぐ修正して",
        "全体のテストを実行",
        "DBクエリを最適化してください",
        "古いキャッシュファイルを削除"
    ]

    for text in test_cases:
        print(f"\n📝 Input: {text}")

        # Mind Reading
        intent_result = await mind_reader.understand_intent(text)
        print(f"🧠 Intent: {intent_result.intent_type.value}")

        # Parse to Command
        parsed_command = await parser.parse_intent(intent_result, text)
        print(f"💭 Command Type: {parsed_command.command_type.value}")
        print(f"🎯 Action: {parsed_command.action}")
        print(f"📌 Target: {parsed_command.target}")

        # Generate Command
        command = await parser.generate_command(parsed_command)
        print(f"⚡ Generated Command: {command}")


if __name__ == "__main__":
    asyncio.run(demo_intent_parser())
