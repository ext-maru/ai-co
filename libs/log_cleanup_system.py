#!/usr/bin/env python3
"""
Log Cleanup System - 自動ログファイル容量最適化
731MBのログディレクトリを効率的に管理
"""

import gzip
import json
import logging
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LogFileInfo:
    """ログファイル情報"""

    path: Path
    size_mb: float
    age_days: int
    last_modified: datetime
    type: str


@dataclass
class CleanupStats:
    """クリーンアップ統計"""

    files_processed: int
    files_compressed: int
    files_deleted: int
    space_saved_mb: float
    space_compressed_mb: float


class LogCleanupSystem:
    """ログファイル自動クリーンアップシステム"""

    def __init__(self, logs_dir: str = "/home/aicompany/ai_co/logs"):
        self.logs_dir = Path(logs_dir)
        self.cleanup_rules = self._initialize_cleanup_rules()

    def _initialize_cleanup_rules(self) -> Dict[str, Dict]:
        """クリーンアップルールを初期化"""
        return {
            "worker_logs": {
                "pattern": "*worker*.log",
                "max_age_days": 7,
                "max_size_mb": 10,
                "compress_after_days": 3,
                "action": "compress_and_rotate",
            },
            "error_logs": {
                "pattern": "*error*.log",
                "max_age_days": 14,
                "max_size_mb": 50,
                "compress_after_days": 7,
                "action": "archive",
            },
            "debug_logs": {
                "pattern": "*debug*.log",
                "max_age_days": 3,
                "max_size_mb": 5,
                "compress_after_days": 1,
                "action": "delete",
            },
            "old_logs": {
                "pattern": "*.log",
                "max_age_days": 30,
                "max_size_mb": 100,
                "compress_after_days": 14,
                "action": "archive",
            },
        }

    def scan_log_files(self) -> List[LogFileInfo]:
        """ログファイルをスキャン"""
        log_files = []

        if not self.logs_dir.exists():
            logger.warning(f"Log directory not found: {self.logs_dir}")
            return log_files

        for log_file in self.logs_dir.rglob("*.log"):
            try:
                stat = log_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                age_days = (datetime.now() - last_modified).days

                # ログタイプの判定
                log_type = self._classify_log_type(log_file.name)

                log_info = LogFileInfo(
                    path=log_file,
                    size_mb=size_mb,
                    age_days=age_days,
                    last_modified=last_modified,
                    type=log_type,
                )

                log_files.append(log_info)

            except (OSError, IOError) as e:
                logger.warning(f"Could not process {log_file}: {e}")

        return sorted(log_files, key=lambda x: x.size_mb, reverse=True)

    def _classify_log_type(self, filename: str) -> str:
        """ログファイルのタイプを分類"""
        filename_lower = filename.lower()

        if "worker" in filename_lower:
            return "worker_logs"
        elif "error" in filename_lower:
            return "error_logs"
        elif "debug" in filename_lower:
            return "debug_logs"
        else:
            return "old_logs"

    def compress_log_file(self, log_file: LogFileInfo) -> bool:
        """ログファイルをgzip圧縮"""
        try:
            compressed_path = log_file.path.with_suffix(log_file.path.suffix + ".gz")

            with open(log_file.path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # 元ファイルを削除
            log_file.path.unlink()

            logger.info(f"Compressed {log_file.path} -> {compressed_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to compress {log_file.path}: {e}")
            return False

    def rotate_log_file(self, log_file: LogFileInfo, max_rotations: int = 5) -> bool:
        """ログファイルをローテーション"""
        try:
            base_path = log_file.path

            # 既存のローテーションファイルをシフト
            for i in range(max_rotations - 1, 0, -1):
                old_file = base_path.with_suffix(f".{i}")
                new_file = base_path.with_suffix(f".{i + 1}")

                if old_file.exists():
                    if new_file.exists():
                        new_file.unlink()
                    old_file.rename(new_file)

            # 現在のファイルを.1にリネーム
            if base_path.exists():
                rotated_file = base_path.with_suffix(".1")
                if rotated_file.exists():
                    rotated_file.unlink()
                base_path.rename(rotated_file)

                # 新しい空ファイルを作成
                base_path.touch()

            logger.info(f"Rotated {log_file.path}")
            return True

        except Exception as e:
            logger.error(f"Failed to rotate {log_file.path}: {e}")
            return False

    def delete_old_compressed_files(self, max_age_days: int = 30) -> int:
        """古い圧縮ファイルを削除"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        for gz_file in self.logs_dir.rglob("*.gz"):
            try:
                stat = gz_file.stat()
                last_modified = datetime.fromtimestamp(stat.st_mtime)

                if last_modified < cutoff_date:
                    gz_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old compressed file: {gz_file}")

            except Exception as e:
                logger.warning(f"Could not delete {gz_file}: {e}")

        return deleted_count

    def cleanup_by_size_threshold(self, target_size_mb: float = 500) -> CleanupStats:
        """サイズ閾値によるクリーンアップ"""
        log_files = self.scan_log_files()
        current_size = sum(f.size_mb for f in log_files)

        stats = CleanupStats(0, 0, 0, 0.0, 0.0)

        if current_size <= target_size_mb:
            logger.info(
                f"Current size {current_size:.1f}MB is within target {target_size_mb}MB"
            )
            return stats

        # サイズの大きいファイルから処理
        size_to_reduce = current_size - target_size_mb
        size_reduced = 0.0

        for log_file in log_files:
            if size_reduced >= size_to_reduce:
                break

            stats.files_processed += 1
            original_size = log_file.size_mb

            # ルールに基づいて処理
            rule = self.cleanup_rules.get(log_file.type, self.cleanup_rules["old_logs"])

            if (
                log_file.age_days > rule["max_age_days"]
                or log_file.size_mb > rule["max_size_mb"]
            ):
                if rule["action"] == "delete":
                    log_file.path.unlink()
                    stats.files_deleted += 1
                    stats.space_saved_mb += original_size
                    size_reduced += original_size

                elif rule["action"] == "compress_and_rotate":
                    if self.compress_log_file(log_file):
                        stats.files_compressed += 1
                        compressed_size = original_size * 0.1  # 想定圧縮率
                        stats.space_compressed_mb += original_size - compressed_size
                        size_reduced += original_size - compressed_size

                elif rule["action"] == "archive":
                    if log_file.age_days > rule["compress_after_days"]:
                        if self.compress_log_file(log_file):
                            stats.files_compressed += 1
                            compressed_size = original_size * 0.1
                            stats.space_compressed_mb += original_size - compressed_size
                            size_reduced += original_size - compressed_size

        return stats

    def execute_scheduled_cleanup(self) -> Dict[str, any]:
        """スケジュールされたクリーンアップを実行"""
        start_time = datetime.now()
        log_files = self.scan_log_files()

        cleanup_result = {
            "timestamp": start_time.isoformat(),
            "before": {
                "total_files": len(log_files),
                "total_size_mb": sum(f.size_mb for f in log_files),
            },
            "actions_taken": [],
            "stats": CleanupStats(0, 0, 0, 0.0, 0.0),
            "after": {},
        }

        # 1. サイズ閾値によるクリーンアップ
        size_stats = self.cleanup_by_size_threshold(target_size_mb=300)
        cleanup_result["stats"] = size_stats
        cleanup_result["actions_taken"].append(
            f"サイズ最適化: {size_stats.files_processed}個処理"
        )

        # 2. 古い圧縮ファイルの削除
        deleted_gz = self.delete_old_compressed_files(max_age_days=30)
        cleanup_result["actions_taken"].append(f"古い圧縮ファイル削除: {deleted_gz}個")

        # 3. 特定パターンのクリーンアップ
        self._cleanup_specific_patterns()
        cleanup_result["actions_taken"].append("特定パターンクリーンアップ完了")

        # 最終状態の測定
        final_log_files = self.scan_log_files()
        cleanup_result["after"] = {
            "total_files": len(final_log_files),
            "total_size_mb": sum(f.size_mb for f in final_log_files),
            "reduction_mb": cleanup_result["before"]["total_size_mb"]
            - sum(f.size_mb for f in final_log_files),
        }

        execution_time = (datetime.now() - start_time).total_seconds()
        cleanup_result["execution_time_seconds"] = execution_time

        return cleanup_result

    def _cleanup_specific_patterns(self):
        """特定パターンのクリーンアップ"""
        patterns_to_cleanup = ["*.tmp", "*.temp", "*~", "*.bak", "core.*"]

        for pattern in patterns_to_cleanup:
            for file_path in self.logs_dir.rglob(pattern):
                try:
                    file_path.unlink()
                    logger.info(f"Deleted temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")

    def generate_cleanup_report(self) -> Dict[str, any]:
        """クリーンアップレポートを生成"""
        log_files = self.scan_log_files()

        # タイプ別統計
        type_stats = defaultdict(
            lambda: {"count": 0, "total_size_mb": 0, "avg_age_days": 0}
        )

        for log_file in log_files:
            type_stats[log_file.type]["count"] += 1
            type_stats[log_file.type]["total_size_mb"] += log_file.size_mb
            type_stats[log_file.type]["avg_age_days"] += log_file.age_days

        # 平均を計算
        for stats in type_stats.values():
            if stats["count"] > 0:
                stats["avg_age_days"] = stats["avg_age_days"] / stats["count"]

        # 推奨アクション
        recommendations = []
        total_size = sum(f.size_mb for f in log_files)

        if total_size > 500:
            recommendations.append("ログディレクトリが500MBを超過。クリーンアップを推奨")

        large_files = [f for f in log_files if f.size_mb > 50]
        if large_files:
            recommendations.append(f"{len(large_files)}個の大型ログファイル(50MB+)を圧縮推奨")

        old_files = [f for f in log_files if f.age_days > 14]
        if old_files:
            recommendations.append(f"{len(old_files)}個の古いログファイル(14日+)をアーカイブ推奨")

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": len(log_files),
                "total_size_mb": total_size,
                "largest_file": max(log_files, key=lambda x: x.size_mb).path.name
                if log_files
                else None,
                "oldest_file": max(log_files, key=lambda x: x.age_days).path.name
                if log_files
                else None,
            },
            "type_statistics": dict(type_stats),
            "recommendations": recommendations,
            "cleanup_preview": {
                "estimated_compression_savings_mb": sum(
                    f.size_mb * 0.9 for f in log_files if f.size_mb > 10
                ),
                "deletable_old_files": len([f for f in log_files if f.age_days > 30]),
                "large_files_to_compress": len(
                    [f for f in log_files if f.size_mb > 20]
                ),
            },
        }

    def export_report(self, output_path: str):
        """レポートをファイルにエクスポート"""
        report = self.generate_cleanup_report()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Cleanup report exported to {output_path}")


def main():
    """メイン実行関数"""
    print("🧹 Log Cleanup System - ログファイル容量最適化")
    print("=" * 60)

    cleanup_system = LogCleanupSystem()

    # 現在の状況分析
    print("📊 現在のログファイル状況分析...")
    report = cleanup_system.generate_cleanup_report()

    print(f"\n📂 ログディレクトリ統計:")
    print(f"   総ファイル数: {report['summary']['total_files']}")
    print(f"   総サイズ: {report['summary']['total_size_mb']:.1f}MB")
    if report["summary"]["largest_file"]:
        print(f"   最大ファイル: {report['summary']['largest_file']}")

    print(f"\n📋 タイプ別統計:")
    for log_type, stats in report["type_statistics"].items():
        print(
            f"   {log_type}: {stats['count']}個, {stats['total_size_mb']:.1f}MB, 平均{stats['avg_age_days']:.1f}日"
        )

    print(f"\n💡 推奨事項:")
    for rec in report["recommendations"]:
        print(f"   • {rec}")

    # クリーンアップ実行
    if report["summary"]["total_size_mb"] > 300:
        print(f"\n🧹 クリーンアップ実行中...")
        cleanup_result = cleanup_system.execute_scheduled_cleanup()

        print(f"✅ クリーンアップ完了:")
        print(f"   処理前: {cleanup_result['before']['total_size_mb']:.1f}MB")
        print(f"   処理後: {cleanup_result['after']['total_size_mb']:.1f}MB")
        print(f"   削減量: {cleanup_result['after']['reduction_mb']:.1f}MB")
        print(f"   実行時間: {cleanup_result['execution_time_seconds']:.1f}秒")

        print(f"\n📋 実行されたアクション:")
        for action in cleanup_result["actions_taken"]:
            print(f"   • {action}")

    # レポート保存
    cleanup_system.export_report(
        "/home/aicompany/ai_co/ai_todo/log_cleanup_report.json"
    )
    print(f"\n📄 詳細レポートを保存しました")

    print(f"\n🎉 Log Cleanup System 最適化完了！")


if __name__ == "__main__":
    main()
