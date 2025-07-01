def fibonacci_10th():
    """
    フィボナッチ数列の10番目の値を計算する関数
    フィボナッチ数列: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...
    10番目 = 55
    """
    a, b = 1, 1
    for i in range(8):
        a, b = b, a + b
    return b

if __name__ == "__main__":
    result = fibonacci_10th()
    print(f"フィボナッチ数列の10番目: {result}")