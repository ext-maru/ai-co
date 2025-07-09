# 🐳 Docker GUI テスト環境セットアップガイド

## 🎯 概要

AI Company Web ダッシュボードの完全な GUI テスト環境を Docker で構築するガイドです。

## 📋 必要な環境

- **OS**: Ubuntu 20.04+ (WSL2 対応)
- **Docker**: 20.10+
- **Docker Compose**: v2.0+
- **メモリ**: 最低 4GB、推奨 8GB

## 🔧 Docker インストール

### 1. Docker Engine インストール

```bash
# 既存の Docker を削除
sudo apt-get remove docker docker-engine docker.io containerd runc

# リポジトリセットアップ
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker の公式 GPG キーを追加
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# リポジトリ設定
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker インストール
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2. ユーザー権限設定

```bash
# Docker グループにユーザーを追加
sudo usermod -aG docker $USER

# 新しいグループ権限を適用
newgrp docker

# 動作確認
docker run hello-world
```

## 🚀 GUI テスト環境起動

### 1. Docker Compose 実行

```bash
# GUI テスト環境起動
docker compose -f docker-compose.gui-test.yml up --build -d

# ログ確認
docker compose -f docker-compose.gui-test.yml logs -f

# 停止
docker compose -f docker-compose.gui-test.yml down
```

### 2. テスト実行

```bash
# 完全テスト実行
docker compose -f docker-compose.gui-test.yml exec gui-test-runner python3 comprehensive_gui_test.py

# Selenium テスト実行
docker compose -f docker-compose.gui-test.yml exec gui-test-runner python3 -m pytest tests/gui/

# Playwright テスト実行
docker compose -f docker-compose.gui-test.yml exec playwright-test-runner python3 -m playwright test
```

## 🌐 GUI テスト確認

### 1. VNC でテスト実行画面確認

```bash
# Chrome テスト画面確認
# ブラウザで http://localhost:7900 にアクセス
# パスワード: secret

# Firefox テスト画面確認
# ブラウザで http://localhost:7901 にアクセス
# パスワード: secret
```

### 2. Web ダッシュボード確認

```bash
# ダッシュボード確認
# ブラウザで http://localhost:5555 にアクセス
```

## 🔍 トラブルシューティング

### WSL2 での Docker 設定

```bash
# WSL2 で Docker Desktop を使用している場合
# Docker Desktop の設定で "Use Docker Compose V2" を有効化

# メモリ不足の場合
# .wslconfig ファイルを作成
# [wsl2]
# memory=8GB
# processors=4
```

### ポート衝突の解決

```bash
# ポート使用状況確認
netstat -tulpn | grep :5555

# 既存プロセス停止
sudo lsof -ti:5555 | xargs sudo kill -9
```

## 📊 テスト結果の確認

### 1. テスト結果ファイル

```bash
# テスト結果フォルダ
ls -la test_results/

# スクリーンショット確認
ls -la test_screenshots/
```

### 2. ログ確認

```bash
# GUI テストログ
docker compose -f docker-compose.gui-test.yml logs gui-test-runner

# Web アプリログ
docker compose -f docker-compose.gui-test.yml logs ai-company-web
```

## 🎯 期待される結果

### 成功時の出力例

```
🎯 COMPREHENSIVE GUI TEST REPORT
============================================================
📊 Overall Summary:
   Test Frameworks: 4/4 successful
   Timestamp: 2025-07-08 13:15:45

📋 Detailed Results:
   ✅ API: 11/11 tests passed
   ✅ Authentication: 1/1 tests passed
   ✅ Selenium: 8/8 tests passed
   ✅ Playwright: 6/6 tests passed

🎉 Overall Success Rate: 100.0%
✅ GUI Testing Framework is ready for production use!
```

## 🔧 カスタマイズ

### 1. 新しいテストケース追加

```python
# comprehensive_gui_test.py に追加
def test_custom_dashboard_feature(self):
    """カスタム機能のテスト"""
    # テスト実装
    pass
```

### 2. 異なるブラウザでのテスト

```yaml
# docker-compose.gui-test.yml に追加
selenium-edge:
  image: selenium/standalone-edge:latest
  # 設定
```

## 💡 推奨事項

### 1. CI/CD パイプライン統合

```yaml
# .github/workflows/gui-test.yml
name: GUI Tests
on: [push, pull_request]
jobs:
  gui-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run GUI Tests
        run: |
          docker compose -f docker-compose.gui-test.yml up --build -d
          docker compose -f docker-compose.gui-test.yml exec -T gui-test-runner python3 comprehensive_gui_test.py
```

### 2. 定期テスト実行

```bash
# crontab に追加
0 2 * * * cd /home/aicompany/ai_co && docker compose -f docker-compose.gui-test.yml up --build -d && docker compose -f docker-compose.gui-test.yml exec -T gui-test-runner python3 comprehensive_gui_test.py && docker compose -f docker-compose.gui-test.yml down
```

## 🎯 まとめ

Docker を使用することで：

1. **環境汚染なし**: ホストシステムに依存関係をインストール不要
2. **再現性**: 同じ環境でテスト実行可能
3. **拡張性**: 複数ブラウザ・複数バージョンでテスト可能
4. **保守性**: 依存関係管理が容易

この環境により、AI Company Web ダッシュボードの品質を継続的に保証できます。

---

**📝 作成者**: クロードエルダー（AI Company 開発実行責任者）  
**📅 作成日**: 2025年7月8日  
**🔄 更新**: 継続的改善により適宜更新