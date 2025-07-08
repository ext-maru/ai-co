#!/usr/bin/env python3

# セキュリティ問題のあるコード - セキュリティテスト用

from pathlib import Path

# Add project root to Python path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
import subprocess

def dangerous_function(user_input):
    # SQL Injection 脆弱性
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command Injection 脆弱性
    os.system(f"echo {user_input}")
    
    # Subprocess with shell=True
    subprocess.call(f"ls {user_input}", shell=True)
    
    # eval使用
    result = eval(user_input)
    
    return result

def insecure_temp_file():
    # 不安全な一時ファイル作成
    temp_file = "/tmp/secret_data.txt"
    with open(temp_file, "w") as f:
        f.write("secret information")
    
    # ファイル権限設定なし
    return temp_file

if __name__ == "__main__":
    user_data = input("Enter data: ")
    dangerous_function(user_data)