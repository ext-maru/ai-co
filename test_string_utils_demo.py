#!/usr/bin/env python3
"""
String Utils デモ実行
"""

from libs.string_utils import reverse_string

def main():
    print("🔄 String Utils デモ実行")
    print("=" * 40)
    
    # 基本テスト
    test_cases = [
        "Hello World!",
        "Claude Elder",
        "エルダーズギルド",
        "12345",
        "racecar",
        "",
        "a"
    ]
    
    for test in test_cases:
        result = reverse_string(test)
        print(f"'{test}' → '{result}'")
    
    # エラーテスト
    print("\n❌ エラーテスト:")
    
    try:
        reverse_string(None)
    except ValueError as e:
        print(f"None → ValueError: {e}")
    
    try:
        reverse_string(123)
    except TypeError as e:
        print(f"123 → TypeError: {e}")

if __name__ == "__main__":
    main()