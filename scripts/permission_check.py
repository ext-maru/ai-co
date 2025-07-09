#!/usr/bin/env python3
"""
AI Company コマンド実行時の権限チェックラッパー
root/sudo実行を防ぐ
"""
import os
import sys
import subprocess

def check_and_run(command_args):
    """権限チェックしてからコマンドを実行"""
    if os.geteuid() == 0:
        print("❌ エラー: このコマンドはroot/sudo権限では実行できません")
        print("💡 通常ユーザーとして実行してください")
        print(f"   例: {' '.join(command_args)} (sudoなし)")
        sys.exit(1)
    
    # sudoで実行されているかチェック
    if os.getenv('SUDO_USER'):
        print("❌ エラー: sudoを使用しないでください")
        print(f"💡 直接実行してください: {' '.join(command_args)}")
        sys.exit(1)
    
    # 権限OKなら元のコマンドを実行
    try:
        subprocess.run(command_args, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: permission_check.py <command> [args...]")
        sys.exit(1)
    
    check_and_run(sys.argv[1:])
