def fibonacci_14th():
    """フィボナッチ数列の14番目の値を計算する関数"""
    if 14 <= 0:
        return 0
    elif 14 == 1:
        return 1
    
    a, b = 0, 1
    for i in range(2, 14 + 1):
        a, b = b, a + b
    
    return b

if __name__ == "__main__":
    result = fibonacci_14th()
    print(f"フィボナッチ数列の14番目: {result}")