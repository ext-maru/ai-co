def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

def fibonacci_1st():
    return fibonacci(1)

def fibonacci_3rd():
    return fibonacci(3)

def fibonacci_5th():
    return fibonacci(5)

if __name__ == "__main__":
    result_1st = fibonacci_1st()
    result_3rd = fibonacci_3rd()
    result_5th = fibonacci_5th()
    print(f"1st Fibonacci number: {result_1st}")
    print(f"3rd Fibonacci number: {result_3rd}")
    print(f"5th Fibonacci number: {result_5th}")