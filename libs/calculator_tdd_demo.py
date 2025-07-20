"""
TDD-XP開発デモ: 計算機の実装
リファクタリング済み - より読みやすく、拡張可能な設計
"""
from typing import Union

Number = Union[int, float]


class Calculator:
    """シンプルな計算機クラス
    
    基本的な四則演算を提供する計算機。
    すべての演算は数値型（int/float）を受け付ける。
    """
    
    def add(self, a: Number, b: Number) -> Number:
        """2つの数を加算する
        
        Args:
            a: 第1引数
            b: 第2引数
            
        Returns:
            a + b の結果
        """
        return self._perform_operation(a, b, lambda x, y: x + y)
    
    def subtract(self, a: Number, b: Number) -> Number:
        """2つの数を減算する
        
        Args:
            a: 被減数
            b: 減数
            
        Returns:
            a - b の結果
        """
        return self._perform_operation(a, b, lambda x, y: x - y)
    
    def multiply(self, a: Number, b: Number) -> Number:
        """2つの数を乗算する
        
        Args:
            a: 第1因数
            b: 第2因数
            
        Returns:
            a × b の結果
        """
        return self._perform_operation(a, b, lambda x, y: x * y)
    
    def divide(self, a: Number, b: Number) -> float:
        """2つの数を除算する
        
        Args:
            a: 被除数
            b: 除数
            
        Returns:
            a ÷ b の結果（常にfloat）
            
        Raises:
            ValueError: bが0の場合
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return self._perform_operation(a, b, lambda x, y: x / y)
    
    def power(self, base: Number, exponent: Number) -> Number:
        """べき乗計算を行う
        
        Args:
            base: 底
            exponent: 指数
            
        Returns:
            base ^ exponent の結果
        """
        return self._perform_operation(base, exponent, lambda x, y: x ** y)
    
    def _perform_operation(self, a: Number, b: Number, operation) -> Number:
        """共通の演算処理
        
        Args:
            a: 第1引数
            b: 第2引数
            operation: 実行する演算のラムダ関数
            
        Returns:
            演算結果
        """
        return operation(a, b)