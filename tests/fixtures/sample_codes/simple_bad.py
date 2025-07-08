#!/usr/bin/env python3

# 問題の多いコードサンプル - 低品質スコア期待

def calc(l,w):
    # ドキュメントなし、型ヒントなし、変数名不適切
    return l*w

def main():
    # エラーハンドリングなし
    result = calc(5,3)
    print("Result: " + str(result))  # 非効率的な文字列結合
    
    # 未使用変数
    unused_var = "hello"
    
    # ハードコード
    if result > 10:
        print("Big")
    else:
        print("Small")

if __name__ == "__main__":
    main()