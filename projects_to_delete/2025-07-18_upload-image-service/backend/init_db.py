#!/usr/bin/env python3
"""データベース初期化スクリプト"""

from app.core.database import engine, Base
from app.models import SubmissionSession, UploadedFile

print("データベーステーブルを作成しています...")
Base.metadata.create_all(bind=engine)
print("データベーステーブルの作成が完了しました！")
