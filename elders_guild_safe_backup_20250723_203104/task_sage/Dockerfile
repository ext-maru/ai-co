FROM python:3.11-slim

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 共有ライブラリのコピー
COPY shared_libs /app/shared_libs

# 魂固有のファイルをコピー
COPY task_sage/ /app/task_sage/

# 環境変数
ENV PYTHONPATH=/app
ENV SOUL_NAME=task_sage

# 実行
CMD ["python", "task_sage/soul.py"]
