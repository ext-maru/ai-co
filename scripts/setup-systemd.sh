#!/bin/bash
# AI Company systemd サービス設定スクリプト

set -e

PROJECT_ROOT="/home/aicompany/ai_co"
SERVICE_DIR="/etc/systemd/system"

echo "🔧 AI Company systemd サービス設定開始..."

# runディレクトリを作成
echo "📁 実行時ディレクトリを作成中..."
mkdir -p "$PROJECT_ROOT/run"
chown aicompany:aicompany "$PROJECT_ROOT/run"

# サービスファイルをコピー
echo "📋 サービスファイルを配置中..."
sudo cp "$PROJECT_ROOT/config/aicompany.service" "$SERVICE_DIR/"
sudo cp "$PROJECT_ROOT/config/aicompany-web.service" "$SERVICE_DIR/"

# 権限設定
sudo chmod 644 "$SERVICE_DIR/aicompany.service"
sudo chmod 644 "$SERVICE_DIR/aicompany-web.service"

# systemdを再読み込み
echo "🔄 systemd設定を再読み込み中..."
sudo systemctl daemon-reload

# サービスを有効化
echo "✅ サービスを有効化中..."
sudo systemctl enable aicompany.service
sudo systemctl enable aicompany-web.service

# RabbitMQサービスも有効化（依存関係）
echo "🐰 RabbitMQ サービスを有効化中..."
sudo systemctl enable rabbitmq-server

echo "🎉 systemd サービス設定完了！"
echo ""
echo "🔧 管理コマンド:"
echo "  システム起動: sudo systemctl start aicompany"
echo "  システム停止: sudo systemctl stop aicompany"
echo "  システム再起動: sudo systemctl restart aicompany"
echo "  サービス状態確認: sudo systemctl status aicompany"
echo "  ログ確認: sudo journalctl -u aicompany -f"
echo ""
echo "  Webサービス単体:"
echo "  Web起動: sudo systemctl start aicompany-web"
echo "  Web停止: sudo systemctl stop aicompany-web"
echo "  Webログ: sudo journalctl -u aicompany-web -f"
echo ""
echo "🚀 自動起動設定:"
echo "  - aicompany.service: システム起動時に自動実行"
echo "  - aicompany-web.service: Webサービス単体の自動実行"
echo "  - rabbitmq-server: RabbitMQサーバーの自動実行"
echo ""
echo "⚠️  注意事項:"
echo "  - サービス開始前にRabbitMQが起動していることを確認してください"
echo "  - 仮想環境が正しく設定されていることを確認してください"
echo "  - ファイアウォール設定が必要な場合があります"