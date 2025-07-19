def fibonacci_12th():
    """フィボナッチ数列の12番目の値を計算する関数"""
    if 12 <= 0:
        return 0
    elif 12 == 1:
        return 1

    a, b = 0, 1
    for i in range(2, 12 + 1):
        a, b = b, a + b

    return b


if __name__ == "__main__":
    result = fibonacci_12th()
    print(f"フィボナッチ数列の12番目: {result}")
