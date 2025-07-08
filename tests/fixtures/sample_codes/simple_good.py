#!/usr/bin/env python3
"""
良質なコードサンプル - 高品質スコア期待
"""

def calculate_area(length: float, width: float) -> float:
    """
    矩形の面積を計算する
    
    Args:
        length (float): 長さ
        width (float): 幅
        
    Returns:
        float: 面積
        
    Raises:
        ValueError: 負の値が入力された場合
    """
    if length < 0 or width < 0:
        raise ValueError("長さと幅は正の値である必要があります")
    
    return length * width


def main():
    """メイン関数"""
    try:
        area = calculate_area(5.0, 3.0)
        print(f"面積: {area}")
    except ValueError as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    main()