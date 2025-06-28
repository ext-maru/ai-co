#!/bin/bash
# pm_cli.sh
# フォルダ・依存を自動準備し、PM用最小対話型CLIを起動するシェルスクリプト（フェーズ1-1）

set -e

BASE_DIR="$HOME/ai_co"
VENV_DIR="$BASE_DIR/venv"
SCRIPTS_DIR="$BASE_DIR/scripts"
CLI_SCRIPT="$SCRIPTS_DIR/pm_cli.py"

log() {
  echo "[INFO]" "$@"
}

# 1. 必要ディレクトリ作成
for dir in "$BASE_DIR" "$VENV_DIR" "$SCRIPTS_DIR"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    log "ディレクトリ作成: $dir"
  else
    log "ディレクトリ存在: $dir"
  fi
done

# 2. Python仮想環境の作成と依存パッケージインストール
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  log "仮想環境作成: $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install pika colorama

# 3. PM用Python CLIスクリプトの用意（簡易版）
cat > "$CLI_SCRIPT" << 'EOF'
import pika
import json

def send_task(prompt, task_type="general"):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    task = {
        "task_id": "pm_cli_task",
        "type": task_type,
        "prompt": prompt
    }

    channel.basic_publish(exchange='', routing_key='task_queue',
                          body=json.dumps(task),
                          properties=pika.BasicProperties(delivery_mode=2))
    print("タスク送信完了:", task)

def main():
    print("PM CLI 簡易版 - タスク送信用")
    while True:
        prompt = input("タスク内容（終了はexit）> ")
        if prompt.lower() == "exit":
            break
        send_task(prompt)

if __name__ == "__main__":
    main()
EOF

log "PM CLIスクリプト準備完了: $CLI_SCRIPT"

# 4. 実行
python3 "$CLI_SCRIPT"

