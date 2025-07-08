#!/usr/bin/env python3
"""
AI Company WSGI Configuration for Apache mod_wsgi
"""

import sys
import os
from pathlib import Path

# プロジェクトルートパスを設定
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# 環境変数設定
os.environ.setdefault('PYTHONPATH', project_root)

# 仮想環境を有効にする場合（オプション）
# virtual_env = os.path.join(project_root, 'venv')
# if os.path.exists(virtual_env):
#     activate_this = os.path.join(virtual_env, 'bin/activate_this.py')
#     if os.path.exists(activate_this):
#         exec(open(activate_this).read(), {'__file__': activate_this})

# Flaskアプリケーションをインポート
from web.flask_app import application

# WSGI アプリケーション
if __name__ == "__main__":
    application.run()