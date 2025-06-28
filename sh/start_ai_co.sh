#!/bin/bash

# ===================================================
# AI Company (ai_co) 完全リセット版セットアップ
# プロジェクトフォルダ: ~/ai_co に統一
# ===================================================

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ログ関数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_phase() { 
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}    $1${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# プロジェクトディレクトリ（統一）
PROJECT_NAME="ai_co"
PROJECT_DIR="$HOME/$PROJECT_NAME"

clear
echo -e "${CYAN}
╔══════════════════════════════════════════════════════════╗
║         AI Company (ai_co) 完全リセット版                ║
║              統一フォルダ構成で再構築                     ║
╚══════════════════════════════════════════════════════════╝
${NC}"

# 既存環境のクリーンアップ確認
if [ -d "$PROJECT_DIR" ]; then
    log_warning "既存のai_coフォルダが見つかりました"
    read -p "削除して再構築しますか？ [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
        log_info "既存フォルダを削除しました"
    else
        log_error "セットアップを中止します"
        exit 1
    fi
fi

# ===================================================
# Phase 1: システム基盤準備
# ===================================================
log_phase "Phase 1: システム基盤準備"

log_info "必要なパッケージをインストール中..."
sudo apt update -y
sudo apt install -y \
    python3 python3-pip python3-venv \
    tmux git curl wget jq \
    rabbitmq-server

# RabbitMQ起動
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management

# RabbitMQユーザー設定
sudo rabbitmqctl add_user ai_admin ai_password 2>/dev/null || true
sudo rabbitmqctl set_user_tags ai_admin administrator 2>/dev/null || true
sudo rabbitmqctl set_permissions -p / ai_admin ".*" ".*" ".*" 2>/dev/null || true

# ===================================================
# Phase 2: プロジェクト構造作成
# ===================================================
log_phase "Phase 2: プロジェクト構造作成"

log_info "ai_coディレクトリ構造を作成中..."

# メインディレクトリ構造
mkdir -p "$PROJECT_DIR/scripts"
mkdir -p "$PROJECT_DIR/workers"
mkdir -p "$PROJECT_DIR/output"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"
mkdir -p "$PROJECT_DIR/venv"
mkdir -p "$PROJECT_DIR/tasks/pending"
mkdir -p "$PROJECT_DIR/tasks/completed"
mkdir -p "$PROJECT_DIR/tasks/failed"

# 設定ファイル
cat > "$PROJECT_DIR/config/system.conf" << EOF
# AI Company システム設定
PROJECT_NAME=ai_co
PROJECT_DIR=$PROJECT_DIR
VENV_DIR=$PROJECT_DIR/venv
OUTPUT_DIR=$PROJECT_DIR/output
LOG_DIR=$PROJECT_DIR/logs
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# RabbitMQ設定
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=ai_admin
RABBITMQ_PASS=ai_password

# tmux設定
TMUX_SESSION=ai_company
EOF

log_success "ディレクトリ構造作成完了"

# ===================================================
# Phase 3: Python環境構築
# ===================================================
log_phase "Phase 3: Python環境構築"

cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

log_info "Pythonパッケージをインストール中..."
pip install --upgrade pip
pip install pika psutil colorama tabulate

# ===================================================
# Phase 4: ワーカースクリプト作成
# ===================================================
log_phase "Phase 4: ワーカースクリプト作成"

# タスクワーカー（改良版）
cat > "$PROJECT_DIR/workers/task_worker.py" << 'WORKER_EOF'
#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import pika
import traceback
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "task_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TaskWorker")

class TaskWorker:
    def __init__(self, worker_id="worker-1"):
        self.worker_id = worker_id
        self.model = "claude-3-5-sonnet-20241022"  # 正しいモデル名
        
    def connect(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='task_queue', durable=True)
            self.channel.queue_declare(queue='result_queue', durable=True)
            logger.info(f"{self.worker_id} - RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False
    
    def process_task(self, ch, method, properties, body):
        """タスク処理"""
        try:
            task = json.loads(body)
            task_id = task.get('task_id', f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            prompt = task.get('prompt', '')
            
            logger.info(f"タスク受信: {task_id}")
            logger.info(f"プロンプト: {prompt[:100]}...")
            
            # 出力ファイルパス
            output_file = OUTPUT_DIR / f"task_{task_id}.txt"
            logger.info(f"出力先: {output_file}")
            
            # Claude CLI実行
            if self.check_claude_cli():
                # 正しいモデル名で実行
                cmd = ["claude", "--model", self.model, "--max-tokens", "4000"]
                logger.info(f"コマンド実行: {' '.join(cmd)}")
                
                try:
                    # プロンプトを標準入力で渡す
                    result = subprocess.run(
                        cmd,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    logger.info(f"実行完了 - リターンコード: {result.returncode}")
                    
                    if result.returncode == 0:
                        output_text = result.stdout
                        logger.info(f"出力文字数: {len(output_text)}")
                    else:
                        output_text = f"エラー: {result.stderr}"
                        logger.error(f"Claude CLIエラー: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    output_text = "エラー: タイムアウト (5分)"
                    logger.error("Claude CLIタイムアウト")
                    
            else:
                # シミュレーションモード
                logger.warning("Claude CLI未検出 - シミュレーションモード")
                output_text = f"[シミュレーション]\nタスクID: {task_id}\nプロンプト: {prompt}\n\nシミュレーション応答です。"
            
            # ファイル保存（詳細ログ付き）
            try:
                logger.info(f"ファイル保存開始: {output_file}")
                
                # メタデータ付きで保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== Task Information ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Worker: {self.worker_id}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Model: {self.model}\n")
                    f.write(f"\n=== Prompt ===\n")
                    f.write(prompt)
                    f.write(f"\n\n=== Response ===\n")
                    f.write(output_text)
                    f.write(f"\n\n=== End ===\n")
                
                # ファイル存在確認
                if output_file.exists():
                    file_size = output_file.stat().st_size
                    logger.info(f"ファイル保存成功: {output_file} (サイズ: {file_size} bytes)")
                else:
                    logger.error(f"ファイルが作成されませんでした: {output_file}")
                    
            except Exception as e:
                logger.error(f"ファイル保存エラー: {e}")
                traceback.print_exc()
            
            # 結果をresult_queueに送信
            result_data = {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": "completed",
                "output_file": str(output_file),
                "timestamp": datetime.now().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='result_queue',
                body=json.dumps(result_data),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"タスク完了: {task_id}")
            
        except Exception as e:
            logger.error(f"タスク処理エラー: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def check_claude_cli(self):
        """Claude CLI確認"""
        try:
            result = subprocess.run(["which", "claude"], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def start(self):
        """ワーカー開始"""
        if not self.connect():
            return
            
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='task_queue',
            on_message_callback=self.process_task
        )
        
        logger.info(f"{self.worker_id} 起動完了 - タスク待機中...")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("シャットダウン中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = TaskWorker(worker_id)
    worker.start()
WORKER_EOF

# 結果処理ワーカー
cat > "$PROJECT_DIR/workers/result_worker.py" << 'RESULT_EOF'
#!/usr/bin/env python3
import os
import sys
import json
import pika
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ResultWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "result_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ResultWorker")

class ResultWorker:
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='result_queue', durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False
    
    def process_result(self, ch, method, properties, body):
        try:
            result = json.loads(body)
            logger.info(f"結果受信: {result['task_id']} - {result['status']}")
            
            # 結果をログに記録（将来的にはDB保存など）
            logger.info(f"出力ファイル: {result.get('output_file', 'N/A')}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"結果処理エラー: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start(self):
        if not self.connect():
            return
            
        self.channel.basic_consume(
            queue='result_queue',
            on_message_callback=self.process_result
        )
        
        logger.info("ResultWorker起動 - 結果待機中...")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("シャットダウン中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker = ResultWorker()
    worker.start()
RESULT_EOF

chmod +x "$PROJECT_DIR/workers/task_worker.py"
chmod +x "$PROJECT_DIR/workers/result_worker.py"

# ===================================================
# Phase 5: 管理スクリプト作成
# ===================================================
log_phase "Phase 5: 管理スクリプト作成"

# タスク送信スクリプト
cat > "$PROJECT_DIR/scripts/send_task.py" << 'SEND_EOF'
#!/usr/bin/env python3
import pika
import json
import sys
from datetime import datetime

def send_task(prompt, task_type="general"):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)
        
        task = {
            "task_id": f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": task_type,
            "prompt": prompt,
            "created_at": datetime.now().isoformat()
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        print(f"✅ タスク送信成功")
        print(f"   ID: {task['task_id']}")
        print(f"   プロンプト: {prompt[:50]}...")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: send_task.py <prompt> [type]")
        print("例: send_task.py 'Pythonでフィボナッチ数列を生成' code")
        sys.exit(1)
    
    prompt = sys.argv[1]
    task_type = sys.argv[2] if len(sys.argv) > 2 else "general"
    send_task(prompt, task_type)
SEND_EOF

# tmux起動スクリプト
cat > "$PROJECT_DIR/scripts/start_company.sh" << 'START_EOF'
#!/bin/bash

SESSION="ai_company"
PROJECT_DIR="$HOME/ai_co"

# セッションリセット
tmux kill-session -t $SESSION 2>/dev/null

echo "🏢 AI Company を起動中..."

# セッション作成
tmux new-session -d -s $SESSION -n "dashboard"

# 1. ダッシュボード
tmux send-keys -t $SESSION:dashboard "cd $PROJECT_DIR && clear" C-m
tmux send-keys -t $SESSION:dashboard "watch -n 2 '$PROJECT_DIR/scripts/status.sh'" C-m

# 2. タスクワーカー1
tmux new-window -t $SESSION -n "worker-1"
tmux send-keys -t $SESSION:worker-1 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-1 "python3 workers/task_worker.py worker-1" C-m

# 3. タスクワーカー2
tmux new-window -t $SESSION -n "worker-2"
tmux send-keys -t $SESSION:worker-2 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-2 "python3 workers/task_worker.py worker-2" C-m

# 4. 結果ワーカー
tmux new-window -t $SESSION -n "result-worker"
tmux send-keys -t $SESSION:result-worker "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:result-worker "python3 workers/result_worker.py" C-m

# 5. ログモニター
tmux new-window -t $SESSION -n "logs"
tmux send-keys -t $SESSION:logs "cd $PROJECT_DIR/logs" C-m
tmux send-keys -t $SESSION:logs "tail -f *.log" C-m

echo "✅ AI Company 起動完了！"
echo "接続: tmux attach -t $SESSION"
START_EOF

# ステータス表示スクリプト
cat > "$PROJECT_DIR/scripts/status.sh" << 'STATUS_EOF'
#!/bin/bash

PROJECT_DIR="$HOME/ai_co"

echo "🏢 AI Company Status - $(date +%H:%M:%S)"
echo "===================================="

# RabbitMQ
echo "[RabbitMQ]"
if systemctl is-active --quiet rabbitmq-server; then
    echo "  状態: ✅ 稼働中"
    sudo rabbitmqctl list_queues name messages 2>/dev/null | grep -E "task_queue|result_queue" | awk '{printf "  %-15s: %s messages\n", $1, $2}'
else
    echo "  状態: ❌ 停止"
fi

# Claude CLI
echo ""
echo "[Claude CLI]"
if command -v claude &> /dev/null; then
    echo "  状態: ✅ 利用可能"
else
    echo "  状態: ⚠️  シミュレーションモード"
fi

# 出力ファイル
echo ""
echo "[出力ファイル]"
OUTPUT_COUNT=$(ls -1 "$PROJECT_DIR/output" 2>/dev/null | wc -l)
echo "  ファイル数: $OUTPUT_COUNT"
if [ $OUTPUT_COUNT -gt 0 ]; then
    echo "  最新: $(ls -t "$PROJECT_DIR/output" | head -1)"
fi

# ワーカー
echo ""
echo "[ワーカー状態]"
ps aux | grep -E "task_worker|result_worker" | grep -v grep | awk '{print "  " $NF}'
STATUS_EOF

chmod +x "$PROJECT_DIR/scripts/"*.sh
chmod +x "$PROJECT_DIR/scripts/"*.py

# ===================================================
# Phase 6: 環境設定
# ===================================================
log_phase "Phase 6: 環境設定"

# エイリアス設定
cat >> ~/.bashrc << 'BASHRC_EOF'

# AI Company (ai_co) 設定
export AI_CO_HOME="$HOME/ai_co"
export PATH="$PATH:$AI_CO_HOME/scripts"

# エイリアス
alias ai-start="$AI_CO_HOME/scripts/start_company.sh"
alias ai-stop="tmux kill-session -t ai_company"
alias ai-attach="tmux attach -t ai_company"
alias ai-send="cd $AI_CO_HOME && source venv/bin/activate && python3 scripts/send_task.py"
alias ai-status="$AI_CO_HOME/scripts/status.sh"
alias ai-logs="tail -f $AI_CO_HOME/logs/*.log"
alias ai-output="ls -la $AI_CO_HOME/output/"
alias ai-venv="cd $AI_CO_HOME && source venv/bin/activate"

# ヘルプ
ai-help() {
    echo "🏢 AI Company (ai_co) コマンド"
    echo "==============================="
    echo "  ai-start   : システム起動"
    echo "  ai-stop    : システム停止"
    echo "  ai-attach  : tmux接続"
    echo "  ai-send    : タスク送信"
    echo "  ai-status  : 状態確認"
    echo "  ai-logs    : ログ表示"
    echo "  ai-output  : 出力確認"
    echo "  ai-venv    : Python環境"
    echo ""
    echo "📁 プロジェクトフォルダ: ~/ai_co"
}
BASHRC_EOF

# ===================================================
# 完了
# ===================================================
clear
echo -e "${GREEN}
╔══════════════════════════════════════════════════════════╗
║              🎉 セットアップ完了！🎉                      ║
║         AI Company (ai_co) 構築完了                       ║
╚══════════════════════════════════════════════════════════╝
${NC}

${CYAN}■ フォルダ構成:${NC}
  ~/ai_co/
  ├── scripts/      # 管理スクリプト
  ├── workers/      # ワーカープログラム
  ├── output/       # 出力ファイル（ここに保存される）
  ├── logs/         # ログファイル
  ├── config/       # 設定ファイル
  └── venv/         # Python仮想環境

${YELLOW}■ 次のステップ:${NC}

1. 新しいターミナルで環境反映:
   ${GREEN}source ~/.bashrc${NC}

2. Claude CLIの確認:
   ${GREEN}claude --version${NC}
   ※未インストールの場合はシミュレーションモードで動作

3. システム起動:
   ${GREEN}ai-start${NC}

4. 別ターミナルでタスク送信:
   ${GREEN}ai-send \"Pythonで素数判定関数を作成\" code${NC}

5. 出力確認:
   ${GREEN}ai-output${NC}
   ${GREEN}cat ~/ai_co/output/task_*.txt${NC}

${PURPLE}■ トラブルシューティング:${NC}
  ${BLUE}ai-help${NC}    - ヘルプ表示
  ${BLUE}ai-status${NC}  - システム状態確認
  ${BLUE}ai-logs${NC}    - ログ確認

${RED}■ 重要:${NC}
  - 出力は必ず ${CYAN}~/ai_co/output/${NC} に保存されます
  - ログは ${CYAN}~/ai_co/logs/${NC} で確認できます
  - RabbitMQ管理UI: ${BLUE}http://localhost:15672${NC}
    (ユーザー: ai_admin / パスワード: ai_password)

${GREEN}準備完了です！ai-startでシステムを起動してください。${NC}
"
