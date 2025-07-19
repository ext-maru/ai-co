#!/usr/bin/env python3
"""
Celery移行デモンストレーション
既存のasync_worker_optimizationとCelery/Ray版の比較
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.async_worker_optimization import AsyncWorkerOptimizer
from libs.celery_migration_poc import (
    AsyncWorkerOptimizationCompat,
    CeleryWorkerOptimizer,
)
from libs.celery_ray_hybrid_poc import HybridWorkerOptimizer


async def demo_existing_optimizer():
    """既存の非同期ワーカー最適化のデモ"""
    print("=" * 60)
    print("🔧 既存のasync_worker_optimization.pyのデモ")
    print("=" * 60)

    optimizer = AsyncWorkerOptimizer()

    # サンプルデータ
    items = [{"id": i, "data": f"item-{i}"} for i in range(100)]

    # サンプルタスク関数
    async def sample_task(item):
        await asyncio.sleep(0.01)  # 処理のシミュレーション
        return {"processed": item["id"]}

    try:
        start_time = time.time()
        results = await optimizer.optimize_batch_processing(
            items, sample_task, batch_size=10, max_concurrent=5
        )
        elapsed = time.time() - start_time

        print(f"✅ 処理完了")
        print(f"  - アイテム数: {len(items)}")
        print(f"  - 処理時間: {elapsed:.2f}秒")
        print(f"  - スループット: {len(items)/elapsed:.1f} items/秒")
    except Exception as e:
        print(f"❌ エラー: {e}")


async def demo_celery_optimizer():
    """Celery版最適化のデモ"""
    print("\n" + "=" * 60)
    print("🚀 Celery移行POCのデモ")
    print("=" * 60)

    compat = AsyncWorkerOptimizationCompat()

    # 同じサンプルデータ
    items = [{"id": i, "data": f"item-{i}"} for i in range(100)]

    try:
        start_time = time.time()
        # 互換性レイヤー経由で実行
        results = await compat.optimize_batch_processing(
            items, None, batch_size=10, max_concurrent=5
        )
        elapsed = time.time() - start_time

        print(f"✅ 処理完了（Celery版）")
        print(f"  - アイテム数: {len(items)}")
        print(f"  - 処理時間: {elapsed:.2f}秒")
        print(f"  - スループット: {len(items)/elapsed:.1f} items/秒")

        print("\n📋 Celeryの追加機能:")
        print("  - タスクの永続化（ブローカー経由）")
        print("  - 自動リトライ機能")
        print("  - タスクルーティング（優先度キュー）")
        print("  - 分散実行（複数ワーカー）")
        print("  - タスクチェーン・グループ・コード")
        print("  - 定期タスク（Celery Beat）")
        print("  - 結果バックエンド")
        print("  - モニタリング（Flower）")

    except Exception as e:
        print(f"❌ エラー: {e}")
        print("  注: Celeryワーカーが起動していない可能性があります")
        print(
            "  起動コマンド: celery -A libs.celery_migration_poc worker --loglevel=info"
        )


async def demo_hybrid_optimizer():
    """Celery + Rayハイブリッドのデモ"""
    print("\n" + "=" * 60)
    print("🌟 Celery + Rayハイブリッドのデモ")
    print("=" * 60)

    optimizer = HybridWorkerOptimizer()

    # 小規模と大規模のデータセット
    small_items = [{"id": i, "data": f"item-{i}"} for i in range(50)]
    large_items = [{"id": i, "data": f"item-{i}"} for i in range(500)]

    try:
        # 小規模（Celery使用）
        print("\n📦 小規模バッチ（50アイテム）:")
        result = await optimizer.hybrid_optimization(small_items, threshold=100)
        print(f"  - 使用手法: {result.method}")
        print(f"  - 処理時間: {result.processing_time:.3f}秒")
        print(f"  - メモリ使用: {result.metrics['memory_usage']:.1f} MB")

        # 大規模（Ray使用）
        print("\n📦 大規模バッチ（500アイテム）:")
        result = await optimizer.hybrid_optimization(large_items, threshold=100)
        print(f"  - 使用手法: {result.method}")
        print(f"  - 処理時間: {result.processing_time:.3f}秒")
        print(f"  - メモリ使用: {result.metrics['memory_usage']:.1f} MB")

        print("\n🎯 ハイブリッドアプローチの利点:")
        print("  - 小規模タスク: Celeryの信頼性とタスク管理")
        print("  - 大規模タスク: Rayの高速並列処理")
        print("  - 自動選択: データサイズに応じて最適な手法を選択")

    except Exception as e:
        print(f"❌ エラー: {e}")
        print("  注: RayまたはCeleryが正しく設定されていない可能性があります")


def show_migration_benefits():
    """Celery/Ray移行のメリットを表示"""
    print("\n" + "=" * 60)
    print("💡 Celery/Ray移行のメリット")
    print("=" * 60)

    benefits = [
        ("🎯", "成熟度", "Celeryは10年以上の実績、Rayは最新の分散処理"),
        ("📊", "スケーラビリティ", "水平スケーリングが容易"),
        ("🔌", "統合", "Redis/RabbitMQ/Kafkaなど多様なブローカー対応"),
        ("📈", "モニタリング", "Flower, Ray Dashboardなど豊富なツール"),
        ("🔄", "信頼性", "自動リトライ、デッドレターキュー"),
        ("⚡", "パフォーマンス", "Rayは特に大規模データで高速"),
        ("🎪", "柔軟性", "タスクルーティング、優先度管理"),
        ("📅", "スケジューリング", "Celery Beatによる定期実行"),
        ("🌐", "分散実行", "複数マシンでの実行が簡単"),
        ("🛠️", "エコシステム", "豊富なプラグインとツール"),
    ]

    for icon, title, desc in benefits:
        print(f"{icon} {title}: {desc}")


def show_migration_comparison():
    """既存実装とOSSの比較"""
    print("\n" + "=" * 60)
    print("📊 実装比較")
    print("=" * 60)

    comparison = """
    | 機能 | 既存実装 | Celery | Ray | ハイブリッド |
    |------|---------|--------|-----|------------|
    | コード行数 | 811行 | ~200行 | ~150行 | ~300行 |
    | 分散実行 | ❌ | ✅ | ✅ | ✅ |
    | 永続化 | ❌ | ✅ | ❌ | ✅ |
    | 自動リトライ | 手動 | ✅ | ❌ | ✅ |
    | モニタリング | 基本 | Flower | Dashboard | 両方 |
    | 学習曲線 | 高 | 中 | 中 | 高 |
    | パフォーマンス | 中 | 高 | 最高 | 最適化 |
    | 保守性 | 低 | 高 | 高 | 中 |
    """
    print(comparison)


def show_migration_steps():
    """移行手順を表示"""
    print("\n" + "=" * 60)
    print("📋 推奨移行手順")
    print("=" * 60)

    steps = [
        ("1️⃣", "環境準備", "Redis/RabbitMQのセットアップ"),
        ("2️⃣", "小規模テスト", "一部のワーカーでCeleryを試験運用"),
        ("3️⃣", "互換性レイヤー", "既存APIを維持しながら内部実装を置換"),
        ("4️⃣", "段階的移行", "ワーカーを順次Celeryに移行"),
        ("5️⃣", "モニタリング", "Flowerでパフォーマンスを監視"),
        ("6️⃣", "最適化", "タスクルーティングとワーカー設定の調整"),
        ("7️⃣", "Ray導入", "大規模処理にRayを追加（オプション）"),
        ("8️⃣", "完全移行", "旧実装の廃止と文書更新"),
    ]

    for num, title, desc in steps:
        print(f"{num} {title}: {desc}")

    print("\n⏱️ 推定期間: 2-3週間（段階的移行）")


async def main():
    """メインデモ実行"""
    print("🏛️ OSS移行POC - 非同期ワーカー最適化比較デモ")
    print("📅 2025年7月19日")
    print("👤 クロードエルダー")

    # 既存実装のデモ
    await demo_existing_optimizer()

    # Celery版のデモ（注: 実際にはCeleryワーカーが必要）
    print("\n⚠️  注意: Celeryデモは実際のワーカーが必要です")
    print("スキップして概要のみ表示します")
    await demo_celery_optimizer()

    # ハイブリッド版のデモ（注: RayとCeleryが必要）
    print("\n⚠️  注意: ハイブリッドデモはRayとCeleryが必要です")
    print("スキップして概要のみ表示します")
    # await demo_hybrid_optimizer()

    # メリットと移行計画
    show_migration_benefits()
    show_migration_comparison()
    show_migration_steps()

    print("\n✅ デモ完了！")
    print("\n📝 次のアクション:")
    print("1. docker-compose.ymlにRedis/RabbitMQを追加")
    print("2. requirements-poc.txtにCelery/Rayを追加")
    print("3. 小規模ワーカーで試験運用開始")


if __name__ == "__main__":
    asyncio.run(main())
