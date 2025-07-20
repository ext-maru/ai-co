#!/usr/bin/env python3
"""
Elder Flow Game - CUIゲーム風インターフェース起動スクリプト
"""
import asyncio
import sys
import os

# パスを追加してモジュールをインポート可能にする
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.elder_flow_game_ui import main

if __name__ == "__main__":
    asyncio.run(main())
