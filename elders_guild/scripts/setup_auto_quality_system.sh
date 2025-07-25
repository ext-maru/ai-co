#!/bin/bash
# 🤖 エルダーズギルド自動品質進化システム セットアップスクリプト

set -e  # エラー時に停止

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_NAME=$(whoami)

echo "🤖 エルダーズギルド自動品質進化システム セットアップ"
echo "================================================================"
echo "📁 プロジェクトルート: $PROJECT_ROOT"
echo "👤 ユーザー: $USER_NAME"
echo ""

# 1. 必要なディレクトリ作成
echo "📁 必要なディレクトリを作成中..."
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/backups/auto_upgrades"
mkdir -p "$PROJECT_ROOT/config"

# 2. Python依存関係チェック
echo "🐍 Python依存関係をチェック中..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3が見つかりません"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3が見つかりません"
    exit 1
fi

# 3. systemdサービスファイル作成
echo "⚙️ systemdサービスファイルを作成中..."
cat > "$PROJECT_ROOT/config/quality-evolution.service" << EOF
[Unit]
Description=🤖 エルダーズギルド品質進化デーモン
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/python3 $PROJECT_ROOT/scripts/quality_daemon.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=10

# 環境変数
Environment=PYTHONPATH=$PROJECT_ROOT
Environment=PYTHONUNBUFFERED=1

# ログ設定
StandardOutput=journal
StandardError=journal
SyslogIdentifier=quality-evolution

# セキュリティ設定
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_ROOT

[Install]
WantedBy=multi-user.target
EOF

# 4. systemdサービス登録（権限がある場合）
echo "🔧 systemdサービスを登録中..."
if sudo cp "$PROJECT_ROOT/config/quality-evolution.service" /etc/systemd/system/ 2>/dev/null; then
    sudo systemctl daemon-reload
    sudo systemctl enable quality-evolution
    echo "✅ systemdサービスが正常に登録されました"

    # サービス開始
    if sudo systemctl start quality-evolution; then
        echo "🚀 品質進化デーモンが開始されました"
        sudo systemctl status quality-evolution --no-pager
    else
        echo "⚠️ サービスの開始に失敗しました。手動で確認してください"
    fi
else
    echo "⚠️ systemdサービスの登録にはsudo権限が必要です"
    echo "💡 手動でサービスを登録するには以下を実行してください:"
    echo "   sudo cp $PROJECT_ROOT/config/quality-evolution.service /etc/systemd/system/"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl enable quality-evolution"
    echo "   sudo systemctl start quality-evolution"
fi

# 5. 設定ファイル作成
echo "📄 設定ファイルを作成中..."
cat > "$PROJECT_ROOT/config/auto_quality_config.yaml" << EOF
# 🤖 エルダーズギルド自動品質進化システム設定

auto_evolution:
  enabled: true
  monitoring_interval: 3600  # 1時間 (秒)
  upgrade_time: "02:00"     # 深夜2時

stability_requirements:
  minimum_days: 7           # 最低安定期間
  max_error_rate: 0.05      # 最大エラー率 (5%)
  max_complaints: 0         # 最大苦情数

notifications:
  slack_webhook: "\${SLACK_WEBHOOK_URL}"
  email_enabled: true
  daily_progress: true
  achievement_alerts: true

phases:
  phase_1:
    stability_threshold: 0.95
    required_metrics: ["commit_success_rate", "precommit_time"]

  phase_2:
    stability_threshold: 0.98
    required_metrics: ["format_compliance", "import_order"]

  phase_3:
    stability_threshold: 0.99
    required_metrics: ["code_quality", "test_coverage"]

rollback:
  auto_rollback: true
  threshold_error_rate: 0.1  # 10%エラー率でロールバック
  monitoring_hours: 72       # 72時間監視
EOF

# 6. 手動実行用スクリプト作成
echo "📋 手動実行用スクリプトを作成中..."
cat > "$PROJECT_ROOT/scripts/manual_quality_check.py" << 'EOF'
#!/usr/bin/env python3
"""
手動品質チェック用スクリプト
デーモンを使わずに一度だけ品質チェックを実行
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.quality_daemon import QualityEvolutionDaemon

async def main():
    """メイン関数"""
    daemon = QualityEvolutionDaemon()

    print("🔍 品質チェックを実行中...")
    await daemon.run_monitoring_cycle()
    print("✅ 品質チェック完了")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x "$PROJECT_ROOT/scripts/manual_quality_check.py"

# 7. 管理用スクリプト作成
echo "🛠️ 管理用スクリプトを作成中..."
cat > "$PROJECT_ROOT/scripts/quality_system_manager.sh" << EOF
#!/bin/bash
# 品質進化システム管理用スクリプト

PROJECT_ROOT="$PROJECT_ROOT"

case "\$1" in
    status)
        echo "🔍 品質進化システム状態確認"
        sudo systemctl status quality-evolution --no-pager
        ;;
    start)
        echo "🚀 品質進化システム開始"
        sudo systemctl start quality-evolution
        ;;
    stop)
        echo "⏹️ 品質進化システム停止"
        sudo systemctl stop quality-evolution
        ;;
    restart)
        echo "🔄 品質進化システム再起動"
        sudo systemctl restart quality-evolution
        ;;
    logs)
        echo "📋 品質進化システムログ表示"
        sudo journalctl -u quality-evolution -f
        ;;
    check)
        echo "🔍 手動品質チェック実行"
        python3 "\$PROJECT_ROOT/scripts/manual_quality_check.py"
        ;;
    *)
        echo "使用方法: \$0 {status|start|stop|restart|logs|check}"
        exit 1
        ;;
esac
EOF

chmod +x "$PROJECT_ROOT/scripts/quality_system_manager.sh"

# 8. 通知設定ファイル作成
echo "📧 通知設定を作成中..."
cat > "$PROJECT_ROOT/config/notification_config.json" << EOF
{
  "slack": {
    "enabled": false,
    "webhook_url": "",
    "channel": "#quality-evolution",
    "username": "品質進化ボット"
  },
  "email": {
    "enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "",
    "password": "",
    "recipients": []
  },
  "discord": {
    "enabled": false,
    "webhook_url": ""
  }
}
EOF

# 9. 最終確認
echo ""
echo "✅ セットアップ完了！"
echo "================================================================"
echo ""
echo "🎯 次のステップ:"
echo "1. 通知設定 (オプション):"
echo "   - Slack: export SLACK_WEBHOOK_URL='your_webhook_url'"
echo "   - 設定ファイル: $PROJECT_ROOT/config/notification_config.json"
echo ""
echo "2. システム管理:"
echo "   - 状態確認: $PROJECT_ROOT/scripts/quality_system_manager.sh status"
echo "   - 手動チェック: $PROJECT_ROOT/scripts/quality_system_manager.sh check"
echo "   - ログ確認: $PROJECT_ROOT/scripts/quality_system_manager.sh logs"
echo ""
echo "3. 設定ファイル:"
echo "   - メイン設定: $PROJECT_ROOT/config/auto_quality_config.yaml"
echo "   - 通知設定: $PROJECT_ROOT/config/notification_config.json"
echo ""
echo "🤖 これで自動的に品質が向上していきます！"
echo "💡 問題があれば: $PROJECT_ROOT/logs/quality_daemon.log を確認してください"
echo ""
echo "🏛️ エルダーズギルド品質進化システムが稼働中です"
