#!/usr/bin/env python3
"""
OSS統合スタック動作確認スクリプト
OSS移行プロジェクト Week 1 環境セットアップ検証用
"""

import sys
import requests
import redis
import json
from datetime import datetime

def test_sonarqube():
    """SonarQube接続テスト"""
    print("🔍 SonarQube接続テスト...")
    try:
        response = requests.get('http://localhost:9000/api/system/status', 
                              auth=('admin', 'admin'), timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SonarQube: {data['status']} (v{data['version']})")
            return True
        else:
            print(f"❌ SonarQube: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SonarQube: {e}")
        return False

def test_redis():
    """Redis接続テスト"""
    print("📦 Redis接続テスト...")
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        # テストデータの書き込み・読み取り
        test_key = f"oss_test:{datetime.now().isoformat()}"
        r.set(test_key, "OSS Migration Test", ex=60)
        value = r.get(test_key)
        if value == "OSS Migration Test":
            print("✅ Redis: 接続・読み書き正常")
            r.delete(test_key)
            return True
        else:
            print("❌ Redis: データ不整合")
            return False
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False

def test_rabbitmq():
    """RabbitMQ接続テスト"""
    print("🐰 RabbitMQ接続テスト...")
    try:
        response = requests.get('http://localhost:15673/api/overview', 
                              auth=('admin', 'admin'), timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RabbitMQ: {data['node']} (Queues: {data['object_totals']['queues']})")
            return True
        else:
            print(f"❌ RabbitMQ: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ RabbitMQ: {e}")
        return False

def test_linters():
    """リンターツール動作テスト"""
    print("🧹 リンターツール動作テスト...")
    test_results = {}
    
    # Black
    try:
        import black
        test_results['black'] = f"✅ Black v{black.__version__}"
    except ImportError:
        test_results['black'] = "❌ Black not available"
    
    # Flake8
    try:
        from flake8.api import legacy as flake8
        test_results['flake8'] = "✅ Flake8 available"
    except ImportError:
        test_results['flake8'] = "❌ Flake8 not available"
    
    # Bandit
    try:
        import bandit
        test_results['bandit'] = f"✅ Bandit v{bandit.__version__}"
    except ImportError:
        test_results['bandit'] = "❌ Bandit not available"
    
    # Mypy
    try:
        import mypy
        test_results['mypy'] = "✅ Mypy available"
    except ImportError:
        test_results['mypy'] = "❌ Mypy not available"
    
    # pytest
    try:
        import pytest
        test_results['pytest'] = f"✅ pytest v{pytest.__version__}"
    except ImportError:
        test_results['pytest'] = "❌ pytest not available"
    
    # Celery
    try:
        import celery
        test_results['celery'] = f"✅ Celery v{celery.__version__}"
    except ImportError:
        test_results['celery'] = "❌ Celery not available"
    
    for tool, status in test_results.items():
        print(f"  {status}")
    
    return all('✅' in status for status in test_results.values())

def main():
    """OSS統合スタック全体テスト"""
    print("🏛️ エルダーズギルド OSS統合スタック動作確認")
    print("=" * 50)
    
    results = []
    
    # 各サービステスト実行
    results.append(test_sonarqube())
    results.append(test_redis())
    results.append(test_rabbitmq())
    results.append(test_linters())
    
    print("\n📊 テスト結果サマリー")
    print("=" * 50)
    
    if all(results):
        print("🎉 全てのOSSサービスが正常に動作しています！")
        print("✅ Week 1 Docker環境セットアップ完了")
        return 0
    else:
        failed_count = len([r for r in results if not r])
        print(f"⚠️  {failed_count}個のサービスで問題があります")
        print("🔧 各サービスの起動状況を確認してください")
        return 1

if __name__ == "__main__":
    sys.exit(main())