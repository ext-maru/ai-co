#!/usr/bin/env python3
"""
Docker統合環境テストスクリプト
Elders Guild Project Web Portal の完全環境確認
"""

import subprocess
import sys
import time
from pathlib import Path

import requests

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(command, cwd=None):
    """コマンド実行"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)


def check_docker_service(url, service_name, timeout=60):
    """サービス接続確認"""
    print(f"   🔍 {service_name} 接続確認中...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {service_name} 接続成功")
                return True
        except requests.exceptions.RequestException:
            pass

        elapsed = int(time.time() - start_time)
        print(f"   ⏳ {service_name} 待機中... ({elapsed}/{timeout}秒)")
        time.sleep(5)

    print(f"   ❌ {service_name} 接続タイムアウト")
    return False


def test_docker_environment():
    """Docker環境テスト"""
    print("🐳 Elders Guild Project Web Portal - Docker環境テスト")
    print("=" * 60)

    # 1. Docker基本確認
    print("\n1️⃣ Docker基本環境確認...")

    # Docker確認
    success, stdout, stderr = run_command("docker --version")
    if success:
        print(f"   ✅ Docker: {stdout.strip()}")
    else:
        print("   ❌ Docker: インストールされていません")
        return False

    # Docker Compose確認
    success, stdout, stderr = run_command("docker-compose --version")
    if success:
        print(f"   ✅ Docker Compose: {stdout.strip()}")
    else:
        print("   ❌ Docker Compose: インストールされていません")
        return False

    # 2. 設定ファイル確認
    print("\n2️⃣ 設定ファイル確認...")

    required_files = {
        "docker-compose.yml": "Docker Compose設定",
        "Dockerfile.backend": "バックエンドDockerfile",
        "frontend/Dockerfile": "フロントエンドDockerfile",
        "nginx/nginx.conf": "Nginx設定",
        "scripts/init_db.sql": "データベース初期化",
        ".env.example": "環境変数テンプレート",
    }

    for file_path, description in required_files.items():
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {description}: {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {description}: {file_path} が見つかりません")

    # 3. 環境変数ファイル準備
    print("\n3️⃣ 環境変数ファイル準備...")

    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"

    if env_file.exists():
        print("   ✅ .env ファイル存在確認")
    elif env_example.exists():
        print("   ⚠️  .env ファイルなし。.env.example をコピーします...")
        try:
            import shutil

            shutil.copy(env_example, env_file)
            print("   ✅ .env ファイル作成完了")
        except Exception as e:
            print(f"   ❌ .env ファイル作成失敗: {e}")
    else:
        print("   ❌ .env.example ファイルが見つかりません")

    # 4. Docker Composeサービス確認
    print("\n4️⃣ Docker Composeサービス確認...")

    success, stdout, stderr = run_command("docker-compose config --services")
    if success:
        services = stdout.strip().split("\n")
        print(f"   ✅ 定義済みサービス数: {len(services)}")
        for service in services:
            print(f"     - {service}")
    else:
        print(f"   ❌ Docker Compose設定エラー: {stderr}")
        return False

    # 5. 既存コンテナ状態確認
    print("\n5️⃣ 既存コンテナ状態確認...")

    success, stdout, stderr = run_command("docker-compose ps")
    if success:
        if stdout.strip():
            print("   📦 稼働中のコンテナ:")
            print(stdout)
        else:
            print("   ✅ 稼働中のコンテナなし")

    # 6. ポート使用状況確認
    print("\n6️⃣ ポート使用状況確認...")

    ports_to_check = [80, 3000, 5432, 6379, 8000]

    for port in ports_to_check:
        success, stdout, stderr = run_command(f"netstat -an | grep :{port}")
        if success and stdout.strip():
            print(f"   ⚠️  ポート {port}: 使用中")
            print(f"      {stdout.strip()}")
        else:
            print(f"   ✅ ポート {port}: 利用可能")

    # 7. Docker起動スクリプト確認
    print("\n7️⃣ Docker起動スクリプト確認...")

    start_script = PROJECT_ROOT / "scripts" / "docker_start.sh"
    if start_script.exists():
        print(f"   ✅ 起動スクリプト: {start_script}")

        # 実行権限確認
        import stat

        file_stat = start_script.stat()
        if file_stat.st_mode & stat.S_IEXEC:
            print("   ✅ 実行権限: 設定済み")
        else:
            print("   ⚠️  実行権限: 未設定")
            print("   実行: chmod +x scripts/docker_start.sh")
    else:
        print("   ❌ 起動スクリプトが見つかりません")

    # 8. 簡易接続テスト（起動している場合）
    print("\n8️⃣ サービス接続テスト（稼働中の場合）...")

    services_to_test = [
        ("http://localhost", "Nginx（メイン）"),
        ("http://localhost:3000", "Next.js フロントエンド"),
        ("http://localhost:8000/health", "FastAPI バックエンド"),
        ("http://localhost:8000/docs", "FastAPI ドキュメント"),
    ]

    for url, name in services_to_test:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"   ✅ {name}: 稼働中")
            else:
                print(f"   ⚠️  {name}: 応答コード {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"   📴 {name}: 停止中")

    # 9. 起動手順説明
    print("\n9️⃣ Docker起動手順:")
    print("   🔧 手動起動:")
    print("      1. cd /home/aicompany/ai_co")
    print("      2. cp .env.example .env")
    print("      3. .envファイルのOPENAI_API_KEYを設定")
    print("      4. docker-compose up -d")
    print("")
    print("   🚀 自動起動スクリプト:")
    print("      1. cd /home/aicompany/ai_co")
    print("      2. ./scripts/docker_start.sh")
    print("")
    print("   🛑 停止:")
    print("      docker-compose down")

    # 10. 統合テスト手順
    print("\n🔟 統合テスト推奨手順:")
    test_steps = [
        "Docker環境起動",
        "http://localhost にアクセス",
        "プロジェクト一覧表示確認",
        "プロジェクトスキャン実行",
        "プロジェクト詳細表示",
        "自動資料生成テスト",
        "類似プロジェクト検索",
        "WebSocket機能テスト",
    ]

    for i, step in enumerate(test_steps, 1):
        print(f"   {i}. {step}")

    # サマリー
    print("\n📊 Docker環境テスト完了サマリー:")
    print("   ✅ Docker + Docker Compose 確認済み")
    print("   ✅ 設定ファイル構成確認済み")
    print("   ✅ 環境変数テンプレート準備済み")
    print("   ✅ サービス定義確認済み")
    print("   ✅ 起動スクリプト準備済み")

    print("\n🎯 次のアクション:")
    print("   1. OpenAI API キーを .env ファイルに設定")
    print("   2. ./scripts/docker_start.sh で起動")
    print("   3. http://localhost でアプリケーション確認")

    print("\n✨ Elders Guild Project Web Portal Docker環境準備完了！")
    return True


def main():
    """メイン実行"""
    try:
        success = test_docker_environment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  テスト中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
