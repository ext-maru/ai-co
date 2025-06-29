#!/bin/bash
# setup_rag_system.sh
# RAG履歴管理システム一括セットアップスクリプト

set -e

BASE_DIR="/root/ai_co"
LIBS_DIR="$BASE_DIR/libs"
DB_DIR="$BASE_DIR/db"

echo "🧠 RAG履歴管理システムセットアップ開始..."

# 1. 必要ディレクトリ作成
echo "📁 ディレクトリ作成中..."
mkdir -p "$LIBS_DIR"
mkdir -p "$DB_DIR"

# 2. libsディレクトリに__init__.pyを作成
echo "📦 Pythonパッケージ初期化..."
touch "$LIBS_DIR/__init__.py"

# 3. task_history_db.pyを配置
echo "💾 task_history_db.py配置中..."
cat > "$LIBS_DIR/task_history_db.py" << 'EOF'
#!/usr/bin/env python3
"""
RAG履歴管理 - SQLite操作クラス
ファイル配置: /root/ai_co/libs/task_history_db.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging

# プロジェクトディレクトリ
PROJECT_DIR = Path(__file__).parent.parent
DB_DIR = PROJECT_DIR / "db"
DB_FILE = DB_DIR / "task_history.db"

logger = logging.getLogger(__name__)

class TaskHistoryDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DB_FILE
        
        self.db_path = Path(db_path)
        # DBディレクトリ作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # テーブル初期化
        self._init_tables()
    
    def _init_tables(self):
        """テーブル作成"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    worker TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    summary TEXT,
                    status TEXT DEFAULT 'completed',
                    task_type TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_id ON task_history(task_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON task_history(created_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_worker ON task_history(worker)
            """)
    
    def save_task(self, task_id, worker, model, prompt, response, 
                  summary=None, status="completed", task_type="general"):
        """タスク履歴を保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO task_history 
                    (task_id, worker, model, prompt, response, summary, status, task_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id, worker, model, prompt, response, summary, 
                    status, task_type, datetime.now(), datetime.now()
                ))
                logger.info(f"タスク履歴保存成功: {task_id}")
                return True
        except Exception as e:
            logger.error(f"タスク履歴保存失敗: {e}")
            return False
    
    def update_summary(self, task_id, summary):
        """要約を更新"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE task_history 
                    SET summary = ?, updated_at = ?
                    WHERE task_id = ?
                """, (summary, datetime.now(), task_id))
                logger.info(f"要約更新成功: {task_id}")
                return True
        except Exception as e:
            logger.error(f"要約更新失敗: {e}")
            return False
    
    def search_tasks(self, keyword=None, worker=None, limit=10):
        """タスク検索"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM task_history WHERE 1=1"
                params = []
                
                if keyword:
                    query += " AND (prompt LIKE ? OR response LIKE ? OR summary LIKE ?)"
                    params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
                
                if worker:
                    query += " AND worker = ?"
                    params.append(worker)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"タスク検索失敗: {e}")
            return []
    
    def get_recent_tasks(self, limit=10):
        """最新タスク取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM task_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"最新タスク取得失敗: {e}")
            return []
    
    def get_stats(self):
        """統計情報取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(DISTINCT worker) as unique_workers,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                        COUNT(CASE WHEN summary IS NOT NULL THEN 1 END) as summarized_tasks
                    FROM task_history
                """)
                return dict(cursor.fetchone())
        except Exception as e:
            logger.error(f"統計情報取得失敗: {e}")
            return {}
    
    def get_task_by_id(self, task_id):
        """タスクIDで検索"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM task_history 
                    WHERE task_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (task_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"タスクID検索失敗: {e}")
            return None
EOF

# 4. rag_manager.pyを配置
echo "🧠 rag_manager.py配置中..."
cat > "$LIBS_DIR/rag_manager.py" << 'EOF'
#!/usr/bin/env python3
"""
RAG管理 - Claude CLI連携・要約生成クラス
ファイル配置: /root/ai_co/libs/rag_manager.py
"""

import subprocess
import logging
from datetime import datetime
from pathlib import Path
from .task_history_db import TaskHistoryDB

logger = logging.getLogger(__name__)

class RAGManager:
    def __init__(self, model="claude-sonnet-4-20250514"):
        self.model = model
        self.db = TaskHistoryDB()
        
    def generate_summary(self, prompt, response):
        """Claude CLIで要約生成"""
        summary_prompt = f"""以下のタスクと応答を簡潔に要約してください（100文字以内）：

【タスク】
{prompt[:500]}...

【応答】  
{response[:1000]}...

要約:"""
        
        try:
            cmd = ["claude", "--model", self.model, "--print"]
            result = subprocess.run(
                cmd,
                input=summary_prompt,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                summary = result.stdout.strip()
                logger.info(f"要約生成成功: {len(summary)}文字")
                return summary
            else:
                logger.error(f"要約生成失敗: {result.stderr}")
                return f"要約生成失敗: プロンプト={prompt[:50]}..."
                
        except Exception as e:
            logger.error(f"要約生成例外: {e}")
            return f"要約生成エラー: プロンプト={prompt[:50]}..."
    
    def save_task_with_summary(self, task_id, worker, prompt, response, 
                              status="completed", task_type="general"):
        """タスク保存＋要約生成"""
        # 1. まず基本情報を保存
        success = self.db.save_task(
            task_id=task_id,
            worker=worker,
            model=self.model,
            prompt=prompt,
            response=response,
            status=status,
            task_type=task_type
        )
        
        if not success:
            return False
        
        # 2. 要約生成（非同期でも良いが、今回は同期）
        if len(response) > 100:  # 短い応答は要約不要
            summary = self.generate_summary(prompt, response)
            self.db.update_summary(task_id, summary)
        
        return True
    
    def get_related_history(self, current_prompt, limit=5):
        """関連履歴検索"""
        # キーワード抽出（簡易版）
        keywords = self._extract_keywords(current_prompt)
        
        related_tasks = []
        for keyword in keywords[:3]:  # 最大3キーワード
            tasks = self.db.search_tasks(keyword=keyword, limit=limit)
            related_tasks.extend(tasks)
        
        # 重複除去・並び替え
        unique_tasks = {}
        for task in related_tasks:
            if task['task_id'] not in unique_tasks:
                unique_tasks[task['task_id']] = task
        
        return list(unique_tasks.values())[:limit]
    
    def _extract_keywords(self, text):
        """簡易キーワード抽出"""
        # 簡単な実装（将来的にはより高度な手法に変更可能）
        import re
        
        # 日本語・英語の単語抽出
        words = re.findall(r'[ぁ-んァ-ヶー一-龠a-zA-Z]{2,}', text)
        
        # 頻出単語を除外
        stopwords = {
            'こと', 'もの', 'ため', 'です', 'ます', 'する', 'ある', 'いる',
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'why'
        }
        
        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 2]
        
        # 頻度順にソート（簡易版）
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(10)]
    
    def build_context_prompt(self, current_prompt, include_history=True):
        """過去の履歴を含めたプロンプト構築"""
        if not include_history:
            return current_prompt
        
        # 関連履歴取得
        related_tasks = self.get_related_history(
