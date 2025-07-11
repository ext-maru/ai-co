#!/usr/bin/env python3
"""
Intent Parser
自然言語をコマンドに変換するパーサー

🎯 nWo Mind Reading Protocol - Natural Language Command Parser
Think it, Rule it, Own it - 自然言語コマンド変換システム
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
import logging


class CommandType(Enum):
    """コマンドタイプ"""
    CREATE = "create"           # 作成系
    UPDATE = "update"           # 更新系
    DELETE = "delete"           # 削除系
    READ = "read"              # 読み取り系
    EXECUTE = "execute"        # 実行系
    ANALYZE = "analyze"        # 分析系
    OPTIMIZE = "optimize"      # 最適化系
    TEST = "test"              # テスト系
    DEPLOY = "deploy"          # デプロイ系
    CONFIGURE = "configure"    # 設定系


class ParameterType(Enum):
    """パラメータタイプ"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    FILE_PATH = "file_path"
    URL = "url"
    EMAIL = "email"
    DATE = "date"
    TIME = "time"


@dataclass
class Parameter:
    """パラメータ情報"""
    name: str
    value: Any
    type: ParameterType
    confidence: float
    source_text: str
    is_required: bool = False


@dataclass
class ParsedCommand:
    """パースされたコマンド"""
    command_type: CommandType
    action: str
    target: str
    parameters: List[Parameter]
    confidence: float
    original_text: str
    suggested_syntax: str
    validation_errors: List[str]
    timestamp: str


class IntentParser:
    """Intent Parser - 自然言語コマンド変換システム"""

    def __init__(self, config_file: Optional[str] = None):
        self.logger = self._setup_logger()

        # パターン辞書
        self.command_patterns = self._load_command_patterns()
        self.parameter_patterns = self._load_parameter_patterns()
        self.action_mapping = self._load_action_mapping()

        # 設定読み込み
        self.config = self._load_config(config_file)

        self.logger.info("🎯 Intent Parser initialized")

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

    def _load_config(self, config_file: Optional[str]) -> Dict:
        """設定読み込み"""
        default_config = {
            "min_confidence": 0.6,
            "max_suggestions": 5,
            "enable_fuzzy_matching": True,
            "parameter_extraction_threshold": 0.5
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    custom_config = json.load(f)
                default_config.update(custom_config)
            except Exception as e:
                self.logger.warning(f"Config loading error: {e}")

        return default_config

    def _load_command_patterns(self) -> Dict[CommandType, List[str]]:
        """コマンドパターン辞書"""
        return {
            CommandType.CREATE: [
                r'作成|作って|create|make|新しい|build|implement|実装',
                r'生成|generate|add|追加',
                r'書いて|write|develop|開発'
            ],
            CommandType.UPDATE: [
                r'更新|update|修正|fix|変更|change|modify',
                r'改善|improve|enhance|refactor|リファクタリング',
                r'編集|edit|revise'
            ],
            CommandType.DELETE: [
                r'削除|delete|remove|消して|消去',
                r'取り除く|clear|clean|クリア'
            ],
            CommandType.READ: [
                r'読んで|read|見て|show|表示|display',
                r'確認|check|view|閲覧|参照',
                r'教えて|tell|説明|explain'
            ],
            CommandType.EXECUTE: [
                r'実行|execute|run|起動|start|開始',
                r'動かして|launch|invoke|call',
                r'やって|perform|process'
            ],
            CommandType.ANALYZE: [
                r'分析|analyze|調査|investigate|研究',
                r'調べて|examine|inspect|review',
                r'解析|parse|study'
            ],
            CommandType.OPTIMIZE: [
                r'最適化|optimize|高速化|speed|performance',
                r'改良|tune|enhance|boost',
                r'効率化|streamline|improve'
            ],
            CommandType.TEST: [
                r'テスト|test|検証|verify|validate',
                r'試して|try|experiment|確認',
                r'チェック|check|診断|debug'
            ],
            CommandType.DEPLOY: [
                r'デプロイ|deploy|公開|publish|release',
                r'配布|distribute|ship|launch'
            ],
            CommandType.CONFIGURE: [
                r'設定|configure|config|setup|セットアップ',
                r'構成|initialize|init|prepare'
            ]
        }

    def _load_parameter_patterns(self) -> Dict[ParameterType, str]:
        """パラメータパターン辞書"""
        return {
            ParameterType.FILE_PATH: r'[/\\]?[\w\-_./\\]+\.\w{2,4}|[\w\-_]+/[\w\-_./]+',
            ParameterType.URL: r'https?://[\w\-._~:/?#[\]@!$&\'()*+,;=]+',
            ParameterType.EMAIL: r'[\w\-_.]+@[\w\-_.]+\.\w{2,}',
            ParameterType.INTEGER: r'\b\d+\b',
            ParameterType.FLOAT: r'\b\d+\.\d+\b',
            ParameterType.DATE: r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            ParameterType.TIME: r'\d{1,2}:\d{2}(:\d{2})?',
            ParameterType.BOOLEAN: r'\b(true|false|yes|no|はい|いいえ|真|偽)\b',
        }

    def _load_action_mapping(self) -> Dict[str, List[str]]:
        """アクション・ターゲットマッピング"""
        return {
            "file_operations": [
                "ファイル", "file", "スクリプト", "script", "コード", "code",
                "プログラム", "program", "モジュール", "module"
            ],
            "api_operations": [
                "api", "endpoint", "サービス", "service", "インターフェース", "interface"
            ],
            "database_operations": [
                "データベース", "database", "db", "テーブル", "table", "レコード", "record"
            ],
            "test_operations": [
                "テスト", "test", "単体テスト", "unit test", "統合テスト", "integration test"
            ],
            "system_operations": [
                "システム", "system", "サーバー", "server", "プロセス", "process"
            ],
            "ui_operations": [
                "ui", "画面", "screen", "ページ", "page", "フォーム", "form"
            ]
        }

    def parse_command(self, text: str) -> ParsedCommand:
        """
        自然言語をコマンドにパース

        Args:
            text: 入力テキスト

        Returns:
            ParsedCommand: パース結果
        """
        self.logger.info(f"🎯 Parsing command: {text[:50]}...")

        # テキスト前処理
        normalized_text = self._normalize_text(text)

        # コマンドタイプ識別
        command_type, command_confidence = self._identify_command_type(normalized_text)

        # アクション・ターゲット抽出
        action, target = self._extract_action_target(normalized_text, command_type)

        # パラメータ抽出
        parameters = self._extract_parameters(normalized_text)

        # 全体的な信頼度計算
        overall_confidence = self._calculate_confidence(
            command_confidence, parameters, action, target
        )

        # 構文提案
        suggested_syntax = self._suggest_syntax(command_type, action, target, parameters)

        # バリデーション
        validation_errors = self._validate_command(command_type, action, target, parameters)

        result = ParsedCommand(
            command_type=command_type,
            action=action,
            target=target,
            parameters=parameters,
            confidence=overall_confidence,
            original_text=text,
            suggested_syntax=suggested_syntax,
            validation_errors=validation_errors,
            timestamp=datetime.now().isoformat()
        )

        self.logger.info(f"✅ Command parsed: {command_type.value} (confidence: {overall_confidence:.2f})")

        return result

    def _normalize_text(self, text: str) -> str:
        """テキスト正規化"""
        # 小文字化
        normalized = text.lower()

        # 余分な空白除去
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _identify_command_type(self, text: str) -> Tuple[CommandType, float]:
        """コマンドタイプ識別"""
        type_scores = {}

        for command_type, patterns in self.command_patterns.items():
            score = 0.0

            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                score += len(matches) * 0.5

                # 完全一致の場合は高スコア
                if re.search(rf'\b{pattern}\b', text, re.IGNORECASE):
                    score += 1.0

            type_scores[command_type] = score

        # 最高スコアのコマンドタイプを選択
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            max_score = type_scores[best_type]

            # 正規化（0-1の範囲）
            confidence = min(1.0, max_score / 3.0)

            return best_type, confidence

        # デフォルトはREAD
        return CommandType.READ, 0.3

    def _extract_action_target(self, text: str, command_type: CommandType) -> Tuple[str, str]:
        """アクション・ターゲット抽出"""
        # 基本的なアクション抽出
        action_words = []
        target_words = []

        words = text.split()

        # コマンドタイプに基づく基本アクション
        action_base = {
            CommandType.CREATE: "create",
            CommandType.UPDATE: "update",
            CommandType.DELETE: "delete",
            CommandType.READ: "read",
            CommandType.EXECUTE: "execute",
            CommandType.ANALYZE: "analyze",
            CommandType.OPTIMIZE: "optimize",
            CommandType.TEST: "test",
            CommandType.DEPLOY: "deploy",
            CommandType.CONFIGURE: "configure"
        }.get(command_type, "process")

        # ターゲット特定
        target_candidates = []

        for category, keywords in self.action_mapping.items():
            for keyword in keywords:
                if keyword in text:
                    target_candidates.append(keyword)

        # より具体的なターゲットを探す
        file_pattern = r'[\w\-_]+\.(py|js|json|yaml|md|txt|sql|html|css)'
        file_matches = re.findall(file_pattern, text)
        if file_matches:
            target_candidates.extend([f"file.{ext}" for ext in file_matches])

        # API/サービス名の抽出
        api_pattern = r'(\w+)\s*(api|service|endpoint)'
        api_matches = re.findall(api_pattern, text, re.IGNORECASE)
        if api_matches:
            target_candidates.extend([f"{name}_api" for name, _ in api_matches])

        # 最適なターゲット選択
        target = target_candidates[0] if target_candidates else "system"

        return action_base, target

    def _extract_parameters(self, text: str) -> List[Parameter]:
        """パラメータ抽出"""
        parameters = []

        for param_type, pattern in self.parameter_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                value = match.group(0)

                # パラメータ名推定
                param_name = self._infer_parameter_name(value, param_type, text, match.start())

                # 値の型変換
                typed_value = self._convert_parameter_value(value, param_type)

                # 信頼度計算
                confidence = self._calculate_parameter_confidence(value, param_type, text)

                parameter = Parameter(
                    name=param_name,
                    value=typed_value,
                    type=param_type,
                    confidence=confidence,
                    source_text=value,
                    is_required=self._is_required_parameter(param_name, param_type)
                )

                parameters.append(parameter)

        # 重複除去と優先度ソート
        parameters = self._deduplicate_parameters(parameters)
        parameters.sort(key=lambda p: p.confidence, reverse=True)

        return parameters[:10]  # 最大10個まで

    def _infer_parameter_name(self, value: str, param_type: ParameterType, text: str, position: int) -> str:
        """パラメータ名推定"""
        # 前後のコンテキストから名前を推定
        context_start = max(0, position - 50)
        context_end = min(len(text), position + len(value) + 50)
        context = text[context_start:context_end]

        # パラメータタイプ別の名前推定
        if param_type == ParameterType.FILE_PATH:
            if any(ext in value for ext in ['.py', '.js', '.json']):
                return "source_file"
            elif any(ext in value for ext in ['.md', '.txt', '.doc']):
                return "document_file"
            else:
                return "file_path"

        elif param_type == ParameterType.URL:
            if "api" in context:
                return "api_url"
            elif "webhook" in context:
                return "webhook_url"
            else:
                return "url"

        elif param_type == ParameterType.EMAIL:
            return "email"

        elif param_type == ParameterType.INTEGER:
            if any(word in context for word in ["port", "ポート"]):
                return "port"
            elif any(word in context for word in ["count", "数", "件数"]):
                return "count"
            elif any(word in context for word in ["timeout", "タイムアウト"]):
                return "timeout"
            else:
                return "number"

        elif param_type == ParameterType.FLOAT:
            if any(word in context for word in ["rate", "ratio", "割合"]):
                return "rate"
            elif any(word in context for word in ["version", "バージョン"]):
                return "version"
            else:
                return "value"

        elif param_type == ParameterType.BOOLEAN:
            return "flag"

        elif param_type == ParameterType.DATE:
            return "date"

        elif param_type == ParameterType.TIME:
            return "time"

        else:
            return f"param_{param_type.value}"

    def _convert_parameter_value(self, value: str, param_type: ParameterType) -> Any:
        """パラメータ値の型変換"""
        try:
            if param_type == ParameterType.INTEGER:
                return int(value)
            elif param_type == ParameterType.FLOAT:
                return float(value)
            elif param_type == ParameterType.BOOLEAN:
                return value.lower() in ['true', 'yes', 'はい', '真']
            else:
                return value
        except ValueError:
            return value  # 変換失敗時は文字列のまま

    def _calculate_parameter_confidence(self, value: str, param_type: ParameterType, text: str) -> float:
        """パラメータ信頼度計算"""
        base_confidence = 0.7

        # パターンマッチの精度
        pattern = self.parameter_patterns[param_type]
        if re.fullmatch(pattern, value, re.IGNORECASE):
            base_confidence += 0.2

        # コンテキストによる補正
        if param_type == ParameterType.FILE_PATH:
            if any(ext in value for ext in ['.py', '.js', '.json', '.md']):
                base_confidence += 0.1

        elif param_type == ParameterType.URL:
            if value.startswith(('http://', 'https://')):
                base_confidence += 0.1

        return min(1.0, base_confidence)

    def _is_required_parameter(self, param_name: str, param_type: ParameterType) -> bool:
        """必須パラメータ判定"""
        required_params = [
            "source_file", "target_file", "api_url", "endpoint",
            "database", "table", "service_name"
        ]

        return param_name in required_params

    def _deduplicate_parameters(self, parameters: List[Parameter]) -> List[Parameter]:
        """パラメータ重複除去"""
        seen = set()
        unique_params = []

        for param in parameters:
            key = (param.name, param.value)
            if key not in seen:
                seen.add(key)
                unique_params.append(param)

        return unique_params

    def _calculate_confidence(self, command_confidence: float, parameters: List[Parameter],
                            action: str, target: str) -> float:
        """全体信頼度計算"""
        # 基本信頼度
        confidence = command_confidence * 0.6

        # パラメータ信頼度の貢献
        if parameters:
            param_confidence = sum(p.confidence for p in parameters) / len(parameters)
            confidence += param_confidence * 0.3

        # アクション・ターゲット明確性
        if action and target and target != "system":
            confidence += 0.1

        return min(1.0, confidence)

    def _suggest_syntax(self, command_type: CommandType, action: str, target: str,
                       parameters: List[Parameter]) -> str:
        """構文提案"""
        # 基本構文
        syntax = f"{command_type.value} {target}"

        # パラメータ追加
        if parameters:
            param_parts = []
            for param in parameters[:3]:  # 主要パラメータのみ
                if param.type == ParameterType.STRING:
                    param_parts.append(f'--{param.name} "{param.value}"')
                else:
                    param_parts.append(f'--{param.name} {param.value}')

            if param_parts:
                syntax += " " + " ".join(param_parts)

        return syntax

    def _validate_command(self, command_type: CommandType, action: str, target: str,
                         parameters: List[Parameter]) -> List[str]:
        """コマンドバリデーション"""
        errors = []

        # 必須要素チェック
        if not action:
            errors.append("Action not specified")

        if not target:
            errors.append("Target not specified")

        # パラメータバリデーション
        required_params = [p for p in parameters if p.is_required]
        if command_type in [CommandType.CREATE, CommandType.UPDATE] and not required_params:
            errors.append("Required parameters missing for this operation")

        # ファイルパス検証
        file_params = [p for p in parameters if p.type == ParameterType.FILE_PATH]
        for param in file_params:
            if not self._is_valid_file_path(param.value):
                errors.append(f"Invalid file path: {param.value}")

        # URL検証
        url_params = [p for p in parameters if p.type == ParameterType.URL]
        for param in url_params:
            if not self._is_valid_url(param.value):
                errors.append(f"Invalid URL: {param.value}")

        return errors

    def _is_valid_file_path(self, path: str) -> bool:
        """ファイルパス妥当性チェック"""
        # 基本的なパス検証
        if not path:
            return False

        # 危険な文字チェック
        dangerous_chars = ['<', '>', '|', '"', '*', '?']
        if any(char in path for char in dangerous_chars):
            return False

        return True

    def _is_valid_url(self, url: str) -> bool:
        """URL妥当性チェック"""
        url_pattern = r'^https?://[\w\-._~:/?#[\]@!$&\'()*+,;=]+$'
        return bool(re.match(url_pattern, url))

    def validate_syntax(self, command: str) -> bool:
        """
        コマンド構文の妥当性チェック

        Args:
            command: コマンド文字列

        Returns:
            bool: 妥当性
        """
        if not command or not command.strip():
            return False

        # 基本的な構文チェック
        parsed = self.parse_command(command)

        return parsed.confidence >= self.config["min_confidence"] and not parsed.validation_errors

    def get_suggestions(self, partial_text: str) -> List[str]:
        """
        部分テキストからの提案生成

        Args:
            partial_text: 部分テキスト

        Returns:
            List[str]: 提案リスト
        """
        suggestions = []

        # コマンドタイプ候補
        for command_type in CommandType:
            for pattern in self.command_patterns[command_type]:
                pattern_words = pattern.split('|')
                for word in pattern_words:
                    if word.startswith(partial_text.lower()):
                        suggestions.append(f"{word} [target]")

        # よく使われる組み合わせ
        common_combinations = [
            "create api endpoint",
            "update database table",
            "delete old files",
            "read configuration file",
            "execute test suite",
            "analyze performance data",
            "optimize database queries",
            "deploy to production",
            "configure environment"
        ]

        for combo in common_combinations:
            if combo.startswith(partial_text.lower()):
                suggestions.append(combo)

        return suggestions[:self.config["max_suggestions"]]

    def get_command_history(self, limit: int = 10) -> List[Dict]:
        """コマンド履歴取得（将来の拡張用）"""
        # 実装は将来追加
        return []

    def analyze_parsing_accuracy(self) -> Dict[str, Any]:
        """パース精度分析（将来の拡張用）"""
        return {
            "total_parsed": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "avg_confidence": 0.0
        }


# 使用例とテスト用関数
def demo_intent_parser():
    """Intent Parserのデモ"""
    print("🎯 Intent Parser Demo")
    print("=" * 50)

    parser = IntentParser()

    test_commands = [
        "APIを実装してください",
        "user.pyファイルを更新して",
        "データベースのテストを実行",
        "https://api.example.com にデプロイ",
        "システムを最適化してポート8080で起動",
        "config.jsonを削除",
        "ログファイルを分析して結果をreport.mdに保存"
    ]

    for i, command in enumerate(test_commands, 1):
        print(f"\n[Test {i}] Input: {command}")

        result = parser.parse_command(command)

        print(f"Command Type: {result.command_type.value}")
        print(f"Action: {result.action}")
        print(f"Target: {result.target}")
        print(f"Confidence: {result.confidence:.2f}")

        if result.parameters:
            print("Parameters:")
            for param in result.parameters[:3]:
                print(f"  - {param.name}: {param.value} ({param.type.value})")

        print(f"Suggested: {result.suggested_syntax}")

        if result.validation_errors:
            print(f"Errors: {', '.join(result.validation_errors)}")

    # 提案機能のテスト
    print("\n🎯 Suggestion Test:")
    test_partials = ["create", "update", "api"]

    for partial in test_partials:
        suggestions = parser.get_suggestions(partial)
        print(f"'{partial}' → {suggestions[:3]}")


if __name__ == "__main__":
    demo_intent_parser()
