#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import signal
import threading

import pika
import traceback
from datetime import datetime
from pathlib import Path
import logging
import re

# RAG・Slack・自己進化統合
sys.path.append(str(Path(__file__).parent.parent))
from features.ai.github_aware_rag import GitHubAwareRAGManager
from features.notification.slack_notifier import SlackNotifier
from features.ai.self_evolution_manager import SelfEvolutionManager

PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [TaskWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "task_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TaskWorker")

class TaskWorker:
    def __init__(self, worker_id="worker-1"):
        self.worker_id = worker_id
        self.model = "claude-sonnet-4-20250514"
        # RAG・Slack・自己進化統合
        self.rag = GitHubAwareRAGManager(model=self.model)
        self.slack = SlackNotifier()
        self.evolution = SelfEvolutionManager()
        
        

    def connect(self):
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
        try:
            task = json.loads(body)
            task_id = task.get('task_id', f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            prompt = task.get('prompt', '')
            task_type = task.get('type', 'general')

            logger.info(f"📨 タスク受信: {task_id} (タイプ: {task_type})")
            logger.info(f"プロンプト: {prompt[:100]}")

            # 🧠 RAG: 過去履歴を含めたプロンプト構築
            enhanced_prompt = self.rag.build_context_with_github(prompt, include_code=True)
            # Claude CLIの権限付与を明示的に追加
            permission_prompt = """I'll help you with this task. I have full access to create and edit files.

Task to complete:
"""
            enhanced_prompt = permission_prompt + "\n" + enhanced_prompt + "\n\nPlease complete this task by creating the necessary files."
            rag_applied = len(enhanced_prompt) > len(prompt)
            
            if rag_applied:
                logger.info(f"✨ RAG適用: プロンプト拡張 {len(prompt)} → {len(enhanced_prompt)} 文字")

            # 出力フォルダ作成（従来通り）
            task_output_dir = OUTPUT_DIR / task_type / task_id
            os.makedirs(task_output_dir, exist_ok=True)
            result_file = task_output_dir / "result.txt"

            # Claude CLI実行
            evolution_result = None
            if self.check_claude_cli():
                cmd = ["claude", "--model", self.model, "--allowedTools", "Edit,Write,FileSystem", "--print"]
                logger.info(f"🤖 Claude CLI実行中...")
                
                try:
                    result = subprocess.run(
                        cmd,
                        input=enhanced_prompt,
                        capture_output=True,
                        text=True,
                        cwd=str(OUTPUT_DIR),
                        timeout=300
                    )

                    if result.returncode == 0:
                        output_text = result.stdout.strip()
                        
                        # デバッグ: 実際の出力を確認
                        logger.info(f"📝 CLI stdout: '{output_text[:100]}...'")
                        if result.stderr:
                            logger.info(f"📝 CLI stderr: '{result.stderr[:100]}...'")
                        
                        # Claude Codeが短い応答やエラーメッセージを返すことがある
                        if len(output_text) < 50 or "error" in output_text.lower():
                            logger.warning(f"⚠️ 短い応答またはエラー: '{output_text}'")
                            
                            # ファイルが生成されているか確認
                            import glob
                            import time
                            time.sleep(1)  # ファイル生成を待つ
                            
                            recent_files = sorted(
                                glob.glob(str(OUTPUT_DIR / "*.py")), 
                                key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0,
                                reverse=True
                            )
                            
                            # 最近作成されたファイルを確認
                            for recent_file in recent_files[:3]:
                                file_age = time.time() - os.path.getmtime(recent_file)
                                if file_age < 30:  # 30秒以内
                                    logger.info(f"📁 最近のファイル検出: {os.path.basename(recent_file)} ({file_age:.1f}秒前)")
                                    with open(recent_file, 'r') as f:
                                        file_content = f.read()
                                    output_text = f"ファイルを生成しました: {os.path.basename(recent_file)}\n\n```python\n{file_content}\n```"
                                    break
                            else:
                                # ファイルが見つからない場合
                                if "error" in output_text.lower():
                                    output_text = f"Claude CLI エラー: {output_text}"
                                else:
                                    output_text = f"Claude CLI 応答: {output_text}"
                        
                        status = "completed"
                        logger.info(f"✅ CLI処理完了: 最終出力{len(output_text)}文字")
                        
                        # 🧬 自己進化: 必ず実行
                        logger.info(f"🧬 自己進化処理開始...")
                        evolution_result = self.handle_evolution(output_text, task_id, prompt)
                        if evolution_result:
                            logger.info(f"🧬 自己進化成功: {evolution_result}")
                        else:
                            logger.info(f"🧬 自己進化: 該当コードなし")
                        
                    else:
                        output_text = f"エラー: {result.stderr}"
                        status = "failed"
                        logger.error(f"❌ CLI失敗: {result.stderr}")

                except subprocess.TimeoutExpired:
                    output_text = "エラー: CLIタイムアウト(5分)"
                    status = "failed"
                    logger.error("⏱️ CLIタイムアウト")
            else:
                output_text = self.generate_simulated_response(prompt, task_type)
                status = "completed"
                logger.warning("🔧 シミュレーションモード")

            # result.txt 保存
            try:
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== Task Info ===\n")
                    f.write(f"Task ID: {task_id}\n")
                    f.write(f"Worker: {self.worker_id}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Model: {self.model}\n")
                    f.write(f"RAG Applied: {'Yes' if rag_applied else 'No'}\n")
                    f.write(f"Evolution Applied: {'Yes' if evolution_result and evolution_result.get('success') else 'No'}\n")
                    f.write(f"\n=== Original Prompt ===\n{prompt}\n")
                    f.write(f"\n=== Response ===\n{output_text}\n")
                    if evolution_result:
                        f.write(f"\n=== Evolution Result ===\n{json.dumps(evolution_result, indent=2)}\n")
                    f.write(f"=== End ===\n")
                logger.info(f"💾 結果ファイル保存: {result_file}")
            except Exception as e:
                logger.error(f"💾 ファイル保存失敗: {e}")

            # 🧠 RAG: 履歴保存・要約生成
            try:
                self.rag.save_task_with_summary(
                    task_id=task_id,
                    worker=self.worker_id,
                    prompt=prompt,
                    response=output_text,
                    status=status,
                    task_type=task_type
                )
                logger.info(f"🧠 RAG履歴保存完了")
            except Exception as e:
                logger.error(f"🧠 RAG履歴保存失敗: {e}")

            # 📱 Slack通知送信（自己進化情報も含む）
            try:
                evolution_info = ""
                if evolution_result and evolution_result.get("success"):
                    evolved_files = evolution_result.get("evolved_files", [])
                    if evolved_files:
                        evolution_info = f"\n🧬 自己進化: {evolved_files[0]['relative_path']}"
                
                slack_response = output_text + evolution_info
                slack_success = self.slack.send_task_completion_simple(
                    task_id=task_id,
                    worker=self.worker_id,
                    prompt=prompt,
                    response=slack_response,
                    status=status,
                    task_type=task_type,
                    rag_applied=rag_applied
                )
                if slack_success:
                    logger.info(f"📱 Slack通知送信完了")
                else:
                    logger.warning(f"📱 Slack通知送信失敗")
            except Exception as e:
                logger.error(f"📱 Slack通知例外: {e}")

            # 結果キュー送信
            result_data = {
                "task_id": task_id,
                "worker": self.worker_id,
                "status": status,
                "output_file": str(result_file),
                "evolution_result": evolution_result,
                "timestamp": datetime.now().isoformat()
            }

            self.channel.basic_publish(
                exchange='',
                routing_key='result_queue',
                body=json.dumps(result_data),
                properties=pika.BasicProperties(delivery_mode=2)
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"🎯 タスク完了: {task_id}")

        except Exception as e:
            logger.error(f"❌ タスク処理例外: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def handle_evolution(self, claude_output, task_id, original_prompt):
        """
        Claude出力から自己進化候補を検出・配置（デバッグ強化版）
        """
        try:
            logger.info(f"🧬 handle_evolution開始: 出力長{len(claude_output)}文字")
            
            # コードブロック抽出（修正版）
            code_blocks = self.extract_code_blocks(claude_output)
            logger.info(f"🧬 抽出されたコードブロック数: {len(code_blocks)}")
            
            evolution_results = []
            
            for i, code_block in enumerate(code_blocks):
                logger.info(f"🧬 コードブロック{i+1}: 言語={code_block['language']}, 長さ={len(code_block['content'])}文字")
                
                if self.is_significant_code(code_block['content']):
                    logger.info(f"🧬 有意なコードと判定: ブロック{i+1}")
                    
                    # ファイル名推測
                    suggested_name = self.suggest_filename(
                        code_block['content'], 
                        code_block['language'], 
                        original_prompt,
                        task_id,
                        i
                    )
                    logger.info(f"🧬 推測ファイル名: {suggested_name}")
                    
                    # 自己進化配置実行
                    evolution_result = self.evolution.auto_place_file(
                        source_content=code_block['content'],
                        suggested_filename=suggested_name,
                        task_id=task_id
                    )
                    
                    if evolution_result.get("success"):
                        logger.info(f"🧬 自己進化成功: {evolution_result['relative_path']}")
                        evolution_results.append(evolution_result)
                    else:
                        logger.warning(f"🧬 自己進化失敗: {evolution_result.get('error')}")
                else:
                    logger.info(f"🧬 有意でないコードのためスキップ: ブロック{i+1}")
            
            if evolution_results:
                return {
                    "success": True,
                    "evolved_files": evolution_results,
                    "count": len(evolution_results)
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"🧬 自己進化処理エラー: {e}")
            traceback.print_exc()
            return None

    def extract_code_blocks(self, text):
        """Claude出力からコードブロックを抽出（修正版）"""
        logger.info(f"🧬 コードブロック抽出開始: テキスト長{len(text)}文字")
        
        # ```language code ``` パターン（修正版）
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        logger.info(f"🧬 正規表現マッチ数: {len(matches)}")
        
        code_blocks = []
        for i, match in enumerate(matches):
            language = match[0] or 'text'
            content = match[1].strip()
            if content:
                logger.info(f"🧬 コードブロック{i+1}: {language}, {len(content)}文字")
                code_blocks.append({
                    'language': language,
                    'content': content
                })
        
        return code_blocks

    def is_significant_code(self, content):
        """有意なコードかどうか判定（緩和版）"""
        # 最小行数チェック（緩和）
        lines = content.split('\n')
        if len(lines) < 3:  # 5から3に緩和
            logger.info(f"🧬 行数不足: {len(lines)}行")
            return False
        
        # 重要なキーワードを含むか
        significant_patterns = [
            r'def\s+\w+',  # 関数定義
            r'class\s+\w+',  # クラス定義
            r'import\s+\w+',  # インポート
            r'#!/bin/bash',  # シェルスクリプト
            r'echo\s+',  # echo文
            r'if\s+__name__\s*==\s*["\']__main__["\']',  # メイン実行
        ]
        
        for pattern in significant_patterns:
            if re.search(pattern, content):
                logger.info(f"🧬 有意パターンマッチ: {pattern}")
                return True
        
        logger.info(f"🧬 有意パターンなし")
        return False

    def suggest_filename(self, content, language, prompt, task_id, index=0):
        """ファイル名提案"""
        # プロンプトから名前のヒントを抽出
        prompt_lower = prompt.lower()
        
        # 特定のキーワードからファイル名推測
        if 'test_fix' in prompt_lower:
            return "test_fix.sh"
        elif 'setup' in prompt_lower and 'database' in prompt_lower:
            return "setup_database.sh"
        elif 'worker' in prompt_lower:
            return f"enhanced_worker_{task_id}.py"
        elif 'manager' in prompt_lower:
            return f"new_manager_{task_id}.py"
        elif 'script' in prompt_lower:
            return f"script_{task_id}.sh"
        
        # 言語別デフォルト
        if language == 'python':
            return f"evolution_{task_id}_{index}.py"
        elif language == 'bash':
            return f"evolution_{task_id}_{index}.sh"
        else:
            return f"evolution_{task_id}_{index}.{language}"

    def check_claude_cli(self):
        try:
            result = subprocess.run(["which", "claude"], capture_output=True)
            return result.returncode == 0
        except:
            return False

    
    def generate_simulated_response(self, prompt, task_type):
        """シミュレーションモードでの応答生成"""
        prompt_lower = prompt.lower()
        
        if task_type == "code":
            if "hello" in prompt_lower or "挨拶" in prompt_lower:
                return """Created hello_ai_company.py with the following content:
```python
print("Hello, AI Company!")
```"""
            elif "fibonacci" in prompt_lower or "フィボナッチ" in prompt_lower:
                return """Created fibonacci.py with the following content:
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 使用例
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")
```"""
            elif "素数" in prompt_lower or "prime" in prompt_lower:
                return """Created prime_checker.py with the following content:
```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# 1から100までの素数
primes = [n for n in range(1, 101) if is_prime(n)]
print(f"Prime numbers: {primes}")
```"""
            else:
                return f"[シミュレーション] コードタスク処理完了: {prompt[:50]}..."
        else:
            return f"[シミュレーション] 一般タスク処理完了: {prompt[:50]}..."

    def setup_signal_handlers(self):
        """シグナルハンドラーの設定"""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        logger.info("🛡️ Graceful Shutdownハンドラー設定完了")
    
    def handle_shutdown(self, signum, frame):
        """シャットダウンシグナルの処理"""
        logger.info(f"📤 シャットダウンシグナル受信: {signum}")
        pass
        
        if self.current_task:
            logger.info("⏳ 現在のタスク完了を待機中...")
            # 最大30秒待機
            timeout = 30
            start_time = time.time()
            while self.current_task and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            if self.current_task:
                logger.warning(f"⚠️ タスク完了待機タイムアウト: {self.current_task}")
        
        logger.info("👋 ワーカー終了")
        sys.exit(0)

    def start(self):
        if not self.connect():
            return

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='task_queue', on_message_callback=self.process_task)

        logger.info(f"🚀 {self.worker_id} 自己進化デバッグ版起動 - task_queue待機中...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("🛑 ワーカー停止中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
    worker = TaskWorker(worker_id)
    worker.start()
