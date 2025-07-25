#!/usr/bin/env python3
"""Pattern Analyzer line 956 特定修正スクリプト"""

def fix_line_956():
    filepath = 'libs/pattern_analyzer.py'
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # ライン955-957の問題を修正
    # 現在:
    # 955:    def _predict_performance_trends(self, data:
    # 956:        """predict_performance_trends（内部メソッド）"""
    # 957:    List[Dict], days: int) -> List[Dict]:
    
    # 修正後:
    # 955:    def _predict_performance_trends(self, data: List[Dict], days: int) -> List[Dict]:
    # 956:        """predict_performance_trends（内部メソッド）"""
    
    if len(lines) > 957:
        # ライン954-958をチェック (0-indexed)
        if 'def _predict_performance_trends(self, data:' in lines[954]:
            # 3行を1行にマージ
            new_line = '    def _predict_performance_trends(self, data: List[Dict], days: int) -> List[Dict]:\n'
            docstring = '        """predict_performance_trends（内部メソッド）"""\n'
            
            # 元の3行を新しい2行で置き換え
            lines[954] = new_line
            lines[955] = docstring
            # 957行目を削除（956行目になっているため）
            del lines[956]
            
            with open(filepath, 'w') as f:
                f.writelines(lines)
            
            print('✅ pattern_analyzer.py line 956エラー修正完了！')
            return True
    
    print('❌ 想定した位置にエラーが見つかりませんでした')
    return False

if __name__ == '__main__':
    fix_line_956()