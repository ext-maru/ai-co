"""
TDD-XP開発デモ: 計算機のテスト
Red→Green→Refactorサイクルの実践
"""
import pytest
from elders_guild.elder_tree.calculator_tdd_demo import Calculator


class TestCalculatorTDD:
    """TDD-XPによる計算機テスト"""
    
    def test_add_two_positive_numbers(self):
        """正の数の加算"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.add(2, 3)
        
        # Assert
        assert result == 5
    
    def test_add_negative_numbers(self):
        """負の数の加算"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.add(-5, -3)
        
        # Assert
        assert result == -8
    
    def test_subtract_two_numbers(self):
        """減算のテスト"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.subtract(10, 4)
        
        # Assert
        assert result == 6
    
    def test_multiply_two_numbers(self):
        """乗算のテスト"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.multiply(6, 7)
        
        # Assert
        assert result == 42
    
    def test_divide_two_numbers(self):
        """除算のテスト"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.divide(10, 2)
        
        # Assert
        assert result == 5.0
    
    def test_divide_by_zero_raises_error(self):
        """ゼロ除算エラーのテスト"""
        # Arrange
        calc = Calculator()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)
    
    def test_power_calculation(self):
        """べき乗計算のテスト"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.power(2, 3)
        
        # Assert
        assert result == 8
    
    def test_power_with_zero_exponent(self):
        """指数が0の場合のテスト"""
        # Arrange
        calc = Calculator()
        
        # Act
        result = calc.power(5, 0)
        
        # Assert
        assert result == 1