#!/usr/bin/env python3
"""
Web Interface Startup Script
Webインターフェース起動スクリプト

使用例:
python3 scripts/start_web_interface.py
python3 scripts/start_web_interface.py --port 8080
python3 scripts/start_web_interface.py --host 0.0.0.0
"""

import sys
import argparse
import asyncio
from pathlib import Path

# パス設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.simple_web_interface import SimpleWebInterface

async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Webインターフェース起動スクリプト')
    parser.add_argument('--host', default='localhost', help='ホストアドレス')
    parser.add_argument('--port', type=int, default=8000, help='ポート番号')
    parser.add_argument('--no-init', action='store_true', help='システム初期化をスキップ')

    args = parser.parse_args()

    try:
        print("🌐 Elders Guild Web Interface Starting...")
        print("=" * 60)

        # Webインターフェース作成
        web_interface = SimpleWebInterface()
        web_interface.host = args.host
        web_interface.port = args.port

        # システム初期化
        if not args.no_init:
            print("🔧 システム初期化中...")
            init_result = await web_interface.initialize_system()
            if init_result['success']:
                print("✅ システム初期化完了")
            else:
                print(f"❌ システム初期化失敗: {init_result.get('error')}")
                print("⚠️  初期化失敗でもWebサーバーは起動します")

        # サーバー起動
        print(f"\n🚀 Webサーバー起動中...")
        print(f"   URL: http://{args.host}:{args.port}")
        print(f"   Dashboard: http://{args.host}:{args.port}/")
        print(f"   API Status: http://{args.host}:{args.port}/api/status")
        print(f"\n🛑 停止するには Ctrl+C を押してください")
        print("=" * 60)

        web_interface.start_server()

    except KeyboardInterrupt:
        print("\n⚠️ Webサーバーを停止しています...")
        print("✅ 正常に停止しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
