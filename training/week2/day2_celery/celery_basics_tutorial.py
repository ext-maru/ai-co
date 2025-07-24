#!/usr/bin/env python3
"""
Day 2: Celery基礎実習 - エルダーズギルド研修
チーム教育プログラム Week 2

実習内容:
1.0 基本的なタスク定義
2.0 非同期実行とResult取得
3.0 リトライ・エラーハンドリング
4.0 複数タスクの連携
5.0 モニタリング

実行前準備:
1.0 Redisサーバーが起動していること (localhost:6379)
2.0 Celeryワーカーを別ターミナルで起動すること
   $ cd training/week2/day2_celery
   $ celery -A celery_basics_tutorial worker --loglevel=info
"""

import random
import time
from typing import Dict, List, Optional

import redis
from celery import Celery

# =============================================================================
# Celeryアプリケーション設定
# =============================================================================

# Redisをブローカーとして使用
app = Celery(
    "elders_guild_training",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# 基本設定
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    result_expires=3600,  # 結果を1時間保持
)


# =============================================================================
# 実習1: 基本的なタスク定義
# =============================================================================


@app.task
def add_elder_levels(level1: int, level2: int) -> intprint(f"計算中: {level1} + {level2}")
"""エルダーレベルの合計計算（基本タスク）"""
    return level1 + level2


@app.task
def process_elder_data(elder_id: str, data: Dict) -> Dictprint(f"エルダー {elder_id} のデータを処理中..."):
    """ルダーデータ処理（重い処理のシミュレーション）"""

    # 重い処理をシミュレート
    time.sleep(2)

    processed_data = {
        "elder_id": elder_id,
        "original_data": data,
        "processed_at": time.time(),
        "status": "completed",
        "processed_fields": len(data) if data else 0,
    }

    print(f"エルダー {elder_id} の処理完了")
    return processed_data


@app.tdef validate_elder_name(name: str) -> Dicttime.sleep(0.5)  # 検証処理をシミュレート:
    """"""エルダー名の妥当性検証"""

    is_valid = bool(
        name and len(name) >= 2 and (name.startswith("エルダー") or name.endswith("Elder"))
    )

    return {
        "name": name,
        "is_valid": is_valid,
        "reason": "Valid elder name" if is_valid else "Invalid format",
        "checked_at": time.time(),
    }


# =============================================================================
# 実習2: エラーハンドリングとリトライ
# =============================================================================


@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def unstable_elder_processing(self, elder_id: str) -> Dictprint(f"不安定処理開始: {elder_id} (試行回数: {self.request.retries + 1})")
"""不安定な処理（リトライ機能のデモ）"""

    # 70%の確率で失敗
    if random.random() < 0.7:
        print(f"処理失敗: {elder_id}")
        raise Exception(f"Elder {elder_id} processing failed randomly")

    print(f"処理成功: {elder_id}")
    return {
        "elder_id": elder_id,
        "status": "success",
        "retry_count": self.request.retries,
        "processed_at": time.time(),
    }


@app.task
def validate_elder_level(level: int) -> Dict:
    """エルダーレベル検証（エラー例を含む）"""
    if level < 0:
        raise ValueError("Level cannot be negative")
    if level > 100:
        raise ValueError("Level cannot exceed 100")

    rank = (
        "見習い"
        if level < 10
        else "一般"
        if level < 40
        else "上級"
        if level < 60
        else "達人"
        if level < 90
        else "エルダー"
    )

    return {
        "level": level,
        "rank": rank,
        "is_elder": level >= 90,
        "validated_at": time.time(),
    }


# =============================================================================
# 実習3: タスクチェーンと複雑なワークフロー
# =============================================================================


@app.task
def collect_elder_info(elder_id: str) -> Dictprint(f"ステップ1: {elder_id} の情報収集中...")
"""ステップ1: エルダー情報収集"""
    time.sleep(1)

    # モックデータ生成
    mock_data = {
        "elder_id": elder_id,
        "name": f"エルダー{elder_id}",
        "level": random.randint(50, 99),
        "skills": ["コード", "設計", "指導"],
        "collected_at": time.time(),
    }

    print(f"ステップ1完了: {elder_id}")
    return mock_data


@app.task
def enhance_elder_data(elder_info: Dict) -> Dictprint(f"ステップ2: {elder_info['elder_id']} のデータ拡張中...")
"""ステップ2: エルダーデータ拡張"""
    time.sleep(1.5)

    enhanced = elder_info.copy()
    enhanced.update(
        {
            "enhanced_at": time.time(),
            "skill_count": len(elder_info.get("skills", [])),
            "rank": "達人" if elder_info.get("level", 0) >= 75 else "上級",
            "experience_points": elder_info.get("level", 0) * 1000,
        }
    )

    print(f"ステップ2完了: {elder_info['elder_id']}")
    return enhanced


@app.task
def finalize_elder_profile(enhanced_data: Dict) -> Dictprint(f"ステップ3: {enhanced_data['elder_id']} のプロフィール完成中...")
"""ステップ3: エルダープロフィール完成"""
    time.sleep(0.5)

    final_profile = enhanced_data.copy()
    final_profile.update(
        {
            "profile_completed": True,
            "completed_at": time.time(),
            "profile_version": "1.0",
            "total_processing_time": time.time()
            - enhanced_data.get("collected_at", time.time()),
        }
    )

    print(f"ステップ3完了: {enhanced_data['elder_id']} プロフィール完成")
    return final_profile


# =============================================================================
# 実習4: バッチ処理
# =============================================================================


@app.task
def process_elder_batch(elder_ids: List[str]) -> Dictprint(f"バッチ処理開始: {len(elder_ids)} 人のエルダー")
"""複数エルダーのバッチ処理"""

    results = []
    start_time = time.time()

    for elder_id in elder_ids:
        time.sleep(0.3)  # 各エルダーの処理時間
        result = {"elder_id": elder_id, "processed": True, "timestamp": time.time()}
        results.append(result)
        print(f"  - {elder_id} 処理完了")

    total_time = time.time() - start_time

    return {
        "batch_id": f"batch_{int(start_time)}",
        "total_processed": len(results),
        "processing_time": total_time,
        "results": results,
        "completed_at": time.time(),
    }


# =============================================================================
# 実習5: 監視・デバッグ機能
# =============================================================================


@app.task(bind=True)
def monitored_elder_task(self, elder_id: str, complexity: str = "normal") -> Dict:
    """監視機能付きエルダータスク"""
    task_id = self.request.id
    print(f"タスク開始: {task_id} - エルダー {elder_id}")

    # 複雑度に応じた処理時間
    sleep_time = {"simple": 0.5, "normal": 1.0, "complex": 2.0}.get(complexity, 1.0)

    # プログレス更新
    self.update_state(
        state="PROGRESS", meta={"current": 10, "total": 100, "status": "データ準備中..."}
    )
    time.sleep(sleep_time / 3)

    self.update_state(
        state="PROGRESS", meta={"current": 50, "total": 100, "status": "メイン処理中..."}
    )
    time.sleep(sleep_time / 3)

    self.update_state(
        state="PROGRESS", meta={"current": 90, "total": 100, "status": "最終処理中..."}
    )
    time.sleep(sleep_time / 3)

    result = {
        "task_id": task_id,
        "elder_id": elder_id,
        "complexity": complexity,
        "processing_time": sleep_time,
        "status": "completed",
        "completed_at": time.time(),
    }

    print(f"タスク完了: {task_id}")
    return result


# =============================================================================
# 実習用ヘルパー関数
# =============================================================================


def demo_basic_tasks()print("🚀 基本タスクデモ開始")
"""基本タスクのデモ実行"""

    # 1.0 簡単な計算タスク
    result1 = add_elder_levels.delay(50, 30)
    print(f"計算タスク送信: ID={result1.0id}")
    print(f"計算結果: {result1.0get(timeout}")

    # 2.0 エルダー名検証
    result2 = validate_elder_name.delay("エルダーmaru")
    print(f"検証結果: {result2.0get(timeout}")

    print("✅ 基本タスクデモ完了\n")


def demo_workflow()print("🔄 ワークフローデモ開始")
"""ワークフローデモ実行"""

    elder_id = "demo_001"

    # チェーン実行: 情報収集 → データ拡張 → プロフィール完成
    from celery import chain

    workflow = chain(
        collect_elder_info.s(elder_id),
        enhance_elder_data.s(),
        finalize_elder_profile.s(),
    )

    result = workflow.apply_async()
    print(f"ワークフロー送信: ID={result.id}")
    final_result = result.get(timeout=30)
    print(f"ワークフロー完了: {final_result}")

    print("✅ ワークフローデモ完了\n")


def demo_batch_processing()print("📦 バッチ処理デモ開始")
"""バッチ処理デモ"""

    elder_ids = [f"elder_{i:03d}" for i in range(5)]
    result = process_elder_batch.delay(elder_ids)

    print(f"バッチ処理送信: ID={result.id}")
    batch_result = result.get(timeout=30)
    print(f"バッチ処理完了: {batch_result['total_processed']} 人処理")

    print("✅ バッチ処理デモ完了\n")


def demo_monitoring()print("👀 監視機能デモ開始")
"""監視機能デモ"""

    result = monitored_elder_task.delay("monitor_001", "complex")
    print(f"監視タスク送信: ID={result.id}")

    # プログレス監視
    while not result.ready():
        if result.state == "PROGRESS":
            meta = result.info
            print(f"プログレス: {meta['current']}/{meta['total']} - {meta['status']}")
        time.sleep(0.5)

    final_result = result.get()
    print(f"監視タスク完了: {final_result}")

    print("✅ 監視機能デモ完了\n")


if __name__ == "__main__":
    print("🏛️ Celery基礎実習へようこそ！")
    print("\n📋 実行手順:")
    print("1.0 Redisサーバーが起動していることを確認")
    print("2.0 別ターミナルでCeleryワーカーを起動:")
    print("   $ celery -A celery_basics_tutorial worker --loglevel=info")
    print("3.0 以下のデモ関数を実行:")
    print("   >>> demo_basic_tasks()")
    print("   >>> demo_workflow()")
    print("   >>> demo_batch_processing()")
    print("   >>> demo_monitoring()")
    print("\n🔍 タスク監視:")
    print("   http://localhost:15673 (RabbitMQ管理画面)")
    print("   または Flower: $ celery -A celery_basics_tutorial flower")

    # Redis接続テスト
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("\n✅ Redis接続確認: OK")
    except Exception as e:
        print(f"\n❌ Redis接続エラー: {e}")
        print(
            "Redisサーバーを起動してください: docker compose -f ../../docker-compose.sonarqube.yml up -d"
        )
