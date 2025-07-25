#!/usr/bin/env python3
"""
AI会話詳細コマンドのテスト
"""
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from commands.ai_conv_info import AIConvInfoCommand
from commands.base_command import CommandResult


class TestAIConvInfoCommand:
    """AI会話詳細コマンドのテスト"""

    def setup_method(self):
        """セットアップ"""
        self.command = AIConvInfoCommand()

    def test_init(self):
        """初期化テスト"""
        assert self.command.name == "ai-conv-info"
        assert self.command.description == "会話詳細"
        assert self.command.version == "1.0.0"

    def test_execute_returns_not_available(self):
        """実行時に利用不可メッセージを返すことを確認"""
        result = self.command.execute([])
        
        assert isinstance(result, CommandResult)
        assert result.success is False
        assert "会話詳細機能は現在利用できません" in result.message

    def test_execute_with_args(self):
        """引数付き実行テスト"""
        result = self.command.execute(["--help"])
        
        assert isinstance(result, CommandResult)
        assert result.success is False
        assert "会話詳細機能は現在利用できません" in result.message