#!/usr/bin/env python3
"""
AI Report Manager Command

完了報告を管理し、次のアクションを提案するコマンド
"""

import sys
sys.path.append('/home/aicompany/ai_co')

from libs.report_management.report_manager import main

if __name__ == '__main__':
    main()