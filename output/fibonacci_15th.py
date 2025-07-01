def fibonacci_15th():
    """フィボナッチ数列の15番目の数を計算する関数"""
    a, b = 0, 1
    for i in range(15):
        a, b = b, a + b
    return a

if __name__ == "__main__":
    result = fibonacci_15th()
    print(f"フィボナッチ数列の15番目: {result}")