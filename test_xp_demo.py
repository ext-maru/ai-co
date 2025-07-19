#!/usr/bin/env python3
"""XP TDD Demo - 電卓機能"""


# Refactored Implementation (Blue)
class Calculator:
    """シンプルな電卓クラス"""

    def add(self, a, b):
        """二つの数を足す"""
        return a + b

    def multiply(self, a, b):
        """二つの数を掛ける"""
        return a * b


# Legacy functions for compatibility
calc = Calculator()


def calculator_add(a, b):
    return calc.add(a, b)


def calculator_multiply(a, b):
    return calc.multiply(a, b)


def test_calculator_add():
    """足し算のテスト"""
    result = calculator_add(2, 3)
    assert result == 5


def test_calculator_add_negative():
    """負の数の足し算テスト"""
    result = calculator_add(-1, 1)
    assert result == 0


def test_calculator_multiply():
    """掛け算のテスト"""
    result = calculator_multiply(3, 4)
    assert result == 12


if __name__ == "__main__":
    test_calculator_add()
    test_calculator_add_negative()
    test_calculator_multiply()
    print("All tests passed!")
