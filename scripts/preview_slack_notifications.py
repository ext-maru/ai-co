#!/usr/bin/env python3
"""
Result Worker Slack通知テスト
新しいフォーマットのプレビュー
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def preview_success_notification():
    """成功通知のプレビュー"""
    print("=" * 60)
    print("SUCCESS NOTIFICATION PREVIEW")
    print("=" * 60)
    print("""
💻 **Task Completed: code_20250702_143256**
Type: `code` | Duration: `3.45s` | Files: `5`

**Request:** PythonでRESTful APIサーバー。FastAPI使用、認証付き、Docker対応...

**Summary:** FastAPIベースのRESTful APIサーバーを実装しました。JWT認証、PostgreSQLデータベース、Docker Compose設定を含む完全なプロジェクトです。エンドポイント仕様書も生成...

**Performance Metrics:**
• Success Rate: `98.5%` (197/200)
• Average Duration: `4.23s`

**Quick Actions:**
```bash
# View output
cat /home/aicompany/ai_co/output/code_20250702_143256/main.py

# Check logs
ai-logs code_20250702_143256
```
""")
    
    print("\n--- File Details (Separate Message) ---\n")
    print("""
📁 **Files Created:**
🐍 `/home/aicompany/ai_co/src/api/main.py`
🐍 `/home/aicompany/ai_co/src/api/auth.py`
🐍 `/home/aicompany/ai_co/src/api/models.py`
📋 `/home/aicompany/ai_co/config/api_config.json`
🔧 `/home/aicompany/ai_co/scripts/start_api.sh`

**File Operations:**
```bash
# List all created files
ls -la /home/aicompany/ai_co/src/api/main.py /home/aicompany/ai_co/src/api/auth.py /home/aicompany/ai_co/src/api/models.py

# Run if executable
chmod +x /home/aicompany/ai_co/scripts/start_api.sh && /home/aicompany/ai_co/scripts/start_api.sh
```
""")

def preview_error_notification():
    """エラー通知のプレビュー"""
    print("\n" + "=" * 60)
    print("ERROR NOTIFICATION PREVIEW")
    print("=" * 60)
    print("""
❌ **Task Failed: general_20250702_143512**
Type: `general` | Status: `failed`

**Error:** `ConnectionError: Unable to connect to Claude API after 3 retries`

**Trace:**
```
Traceback (most recent call last):
  File "/home/aicompany/ai_co/workers/task_worker.py", line 87, in process_message
    response = self._execute_claude(prompt)
  File "/home/aicompany/ai_co/workers/task_worker.py", line 145, in _execute_claude
    raise ConnectionError("Unable to connect to Claude API after 3 retries")
ConnectionError: Unable to connect to Claude API after 3 retries...
```

**Debug Commands:**
```bash
# Check full logs
ai-logs general_20250702_143512 --verbose

# Retry task
ai-retry general_20250702_143512

# Check DLQ
ai-dlq show general_20250702_143512
```
""")

def preview_hourly_report():
    """時間別レポートのプレビュー"""
    print("\n" + "=" * 60)
    print("HOURLY REPORT PREVIEW")
    print("=" * 60)
    print("""
📊 **Hourly Performance Report**
Period: 2025-07-02 18:00

• Total Tasks: `47`
• Success Rate: `95.7%`
• Failed Tasks: `2`
• Average Duration: `3.82s`
• Total Processing Time: `179.5s`
""")

def preview_dialog_completion():
    """対話型タスク完了のプレビュー"""
    print("\n" + "=" * 60)
    print("DIALOG TASK COMPLETION PREVIEW")
    print("=" * 60)
    print("""
💬 **Task Completed: dialog_20250702_144023**
Type: `dialog` | Duration: `12.34s` | Files: `3`

**Request:** マイクロサービスアーキテクチャの設計と実装について相談したい...

**Summary:** マイクロサービスアーキテクチャの設計を完了しました。4つのサービス（Auth, User, Product, Order）の実装、API Gateway設定、Docker Compose構成を作成...

**Performance Metrics:**
• Success Rate: `96.8%` (182/188)
• Average Duration: `5.67s`

**Quick Actions:**
```bash
# View output
cat /home/aicompany/ai_co/output/dialog_20250702_144023/architecture.md

# Check logs
ai-logs dialog_20250702_144023
```
""")

def preview_template_execution():
    """テンプレート実行完了のプレビュー"""
    print("\n" + "=" * 60)
    print("TEMPLATE EXECUTION PREVIEW")
    print("=" * 60)
    print("""
📝 **Task Completed: template_daily_report_20250702_150000**
Type: `template` | Duration: `2.15s` | Files: `1`

**Request:** Execute template: daily_report with params: {'date': '2025-07-02'}

**Summary:** Daily report generated successfully. Analyzed 156 tasks, identified 3 error patterns, generated performance insights and recommendations...

**Performance Metrics:**
• Success Rate: `99.1%` (224/226)
• Average Duration: `3.45s`

**Quick Actions:**
```bash
# View output
cat /home/aicompany/ai_co/reports/daily_report_20250702.md

# Check logs
ai-logs template_daily_report_20250702_150000
```
""")

if __name__ == "__main__":
    print("\n🚀 Elders Guild v5.0 - Result Worker Slack Notification Preview\n")
    
    # 各種通知のプレビュー
    preview_success_notification()
    preview_error_notification()
    preview_dialog_completion()
    preview_template_execution()
    preview_hourly_report()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
新しいSlack通知の特徴:
✅ プロフェッショナルなデータ中心のフォーマット
✅ 測定可能な指標（Duration, Success Rate, Files）
✅ 実行可能なコマンドを含む
✅ エラー時のデバッグ支援
✅ タスクタイプ別の最適化
✅ 控えめな絵文字使用（システム状態のみ）
✅ 1時間ごとのパフォーマンスレポート
""")
