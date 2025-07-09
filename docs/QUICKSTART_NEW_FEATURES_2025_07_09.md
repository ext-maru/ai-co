# 🚀 AI Company 新機能クイックスタートガイド - 2025年7月9日

## 🎯 概要

本日実装された新機能の使用方法を簡潔に説明します。

## 🔮 マナシステム

### 基本的な使用方法

```bash
# Webダッシュボードにアクセス
open http://localhost:5011/mana-dashboard

# または、コマンドラインから
python3 -c "
from libs.mana_system import mana_system
print(mana_system.get_all_mana_status())
"
```

### APIエンドポイント

```bash
# マナ状態確認
curl http://localhost:5011/api/mana/status

# 評議会シミュレーション
curl -X POST http://localhost:5011/api/mana/council/simulate \
  -H "Content-Type: application/json" \
  -d '{"duration": 300}'

# 緊急マナブースト
curl -X POST http://localhost:5011/api/mana/emergency/boost
```

### Python API

```python
from libs.mana_system import mana_system

# 全精霊のマナ状態取得
status = mana_system.get_all_mana_status()
print(f"システム健全性: {status['overall_health']}%")

# 特定精霊のマナ消費
result = mana_system.consume_mana('will', 20, 'strategic_decision')
print(f"消費結果: {result}")

# マナ回復
result = mana_system.restore_mana('wisdom', 15)
print(f"回復結果: {result}")
```

## 🚀 A2A通信システム

### 基本的な使用方法

```bash
# システム状態確認
python3 commands/ai_a2a.py status

# 通信テスト
python3 commands/ai_a2a.py test --source knowledge_sage --target task_sage

# 4賢者協調デモ
python3 commands/ai_a2a.py demo --scenario collaboration
```

### Python API

```python
from libs.a2a_communication import A2AClient, MessageType, MessagePriority

# クライアント作成
client = A2AClient(
    agent_id="my_agent",
    agent_type="custom_agent"
)

# メッセージ送信
await client.send_message(
    target_agent="task_sage",
    message_type=MessageType.QUERY_REQUEST,
    content={"query": "システム状態確認"},
    priority=MessagePriority.NORMAL
)
```

## ⚙️ 統合設定システム

### 基本的な使用方法

```bash
# 統合テスト実行
python3 test_config_integration.py

# 設定マイグレーション（ドライラン）
python3 tools/config_migration_tool.py --phase all --dry-run --verbose

# 設定マイグレーション（実行）
python3 tools/config_migration_tool.py --phase all --verbose
```

### Python API

```python
from libs.integrated_config_system import IntegratedConfigManager

# 設定管理
config_manager = IntegratedConfigManager()

# 設定取得
core_config = config_manager.get_config('core')
claude_config = config_manager.get_config('claude')

# 設定更新
config_manager.update_config('core', 'log_level', 'DEBUG')
```

## 🧪 テストシステム

### 新規テストの実行

```bash
# マナシステムテスト
python3 -m pytest tests/unit/libs/test_mana_system.py -v

# Web APIテスト
python3 -m pytest tests/unit/web/test_sages_api.py -v

# 統合テスト
python3 -m pytest tests/unit/libs/test_mana_system.py tests/unit/web/test_sages_api.py -v

# 設定統合テスト
python3 test_config_integration.py
```

### テスト結果確認

```bash
# 成功例
=== 52 passed, 1 skipped in 0.75s ===

# 詳細な結果
pytest --tb=short -v tests/unit/libs/test_mana_system.py
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. マナシステムが起動しない

```bash
# 依存関係確認
pip3 install flask

# ポート確認
netstat -tulnp | grep 5011

# 再起動
python3 web/master_console_final.py
```

#### 2. A2A通信エラー

```bash
# RabbitMQ状態確認
systemctl status rabbitmq-server

# 設定確認
python3 -c "from libs.env_config import config; print(config.get_rabbitmq_config())"
```

#### 3. 設定統合エラー

```bash
# 設定ファイル確認
ls -la config/integrated/

# 権限確認
chmod +r config/integrated/*.yaml
```

### 緊急時の対応

```bash
# 全システム再起動
python3 commands/ai_restart.py

# ログ確認
tail -f logs/*.log

# 4賢者状態確認
python3 -c "from web.sages_api import sages_manager; print(sages_manager.get_knowledge_sage_status())"
```

## 📱 Webダッシュボードアクセス

### 主要URL

- **メインダッシュボード**: http://localhost:5011/
- **マナシステム**: http://localhost:5011/mana-dashboard
- **統合ダッシュボード**: http://localhost:5011/dashboard
- **完了レポート**: http://localhost:5011/completion-report
- **システムテスト**: http://localhost:5011/final-test

### 機能概要

1. **リアルタイム監視**: 5秒間隔でマナ状態更新
2. **インタラクティブ操作**: 評議会シミュレーション・緊急ブースト
3. **履歴表示**: マナ変動履歴のリアルタイム表示
4. **アラート機能**: 精霊の状態変化時の自動通知

## 🛠️ 高度な使用方法

### カスタムスクリプト例

```python
#!/usr/bin/env python3
"""
カスタムマナ監視スクリプト
"""
import time
from libs.mana_system import mana_system

def monitor_mana():
    while True:
        status = mana_system.get_all_mana_status()
        
        # 健全性チェック
        if status['overall_health'] < 50:
            print(f"⚠️  システム健全性低下: {status['overall_health']}%")
            
            # 緊急ブースト実行
            boost_result = mana_system.emergency_mana_boost()
            print(f"🚀 緊急ブースト実行: {boost_result}")
        
        # アラート確認
        if status['alerts']:
            for alert in status['alerts']:
                print(f"🚨 {alert['level'].upper()}: {alert['message']}")
        
        time.sleep(30)  # 30秒間隔

if __name__ == "__main__":
    monitor_mana()
```

### バッチ処理例

```bash
#!/bin/bash
# 定期メンテナンススクリプト

echo "🔍 システム状態チェック開始"

# マナシステムチェック
python3 -c "
from libs.mana_system import mana_system
status = mana_system.get_all_mana_status()
print(f'マナシステム健全性: {status[\"overall_health\"]}%')
"

# 設定システムチェック
python3 test_config_integration.py

# A2A通信テスト
python3 commands/ai_a2a.py test --source knowledge_sage --target task_sage

echo "✅ システム状態チェック完了"
```

## 📚 詳細ドキュメント

- **マナシステム**: `docs/MANA_SYSTEM_GUIDE.md`
- **A2A通信**: `docs/A2A_COMMUNICATION_GUIDE.md`
- **設定統合**: `docs/CONFIG_INTEGRATION_GUIDE.md`
- **テストガイド**: `docs/TESTING_GUIDE.md`

## 🆘 サポート

問題が発生した場合：

1. **ログ確認**: `tail -f logs/*.log`
2. **システム状態**: `python3 commands/ai_status.py`
3. **4賢者相談**: `python3 -c "from web.sages_api import sages_manager; print(sages_manager.get_knowledge_sage_status())"`

---

*🎯 このガイドで新機能を効果的に活用してください！*

**最終更新**: 2025年7月9日  
**作成者**: クロードエルダー（開発実行責任者）