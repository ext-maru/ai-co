#!/usr/bin/env python3
"""
Log Maintenance System - ログメンテナンスシステム
エルダーズギルドのログファイル管理とローテーション

🧹 機能:
- 大容量ログファイルの自動アーカイブ
- 古いログファイルの自動削除
- ログローテーション設定
- ログ統計の生成
"""

import gzip
import json
import logging
import shutil
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Dict
from typing import List


class LogMaintenanceSystem:
    """ログメンテナンスシステム"""

    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / "logs"
        self.archive_dir = self.logs_dir / "archive"
        self.config_file = self.project_dir / "config" / "log_maintenance.json"

        # 設定
        self.max_file_size_mb = 10  # MB
        self.max_age_days = 30  # 日
        self.compress_older_than_days = 7  # 日
        self.keep_compressed_days = 60  # 日

        # アーカイブディレクトリ作成
        self.archive_dir.mkdir(exist_ok=True)

        # ログ設定
        self.setup_logging()

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.logs_dir / "log_maintenance.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def analyze_logs(self) -> Dict:
        """ログファイル分析"""
        self.logger.info("🔍 ログファイル分析開始")

        analysis = {
            "total_files": 0,
            "total_size_mb": 0,
            "large_files": [],  # 10MB以上
            "old_files": [],  # 30日以上
            "empty_files": [],  # 空ファイル
            "by_extension": {},
            "by_date": {},
        }

        for log_file in self.logs_dir.glob("*.log"):
            if not log_file.is_file():
                continue

            stat = log_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified_date = datetime.fromtimestamp(stat.st_mtime)
            age_days = (datetime.now() - modified_date).days

            analysis["total_files"] += 1
            analysis["total_size_mb"] += size_mb

            # 大容量ファイル
            if size_mb > self.max_file_size_mb:
                analysis["large_files"].append(
                    {
                        "file": str(log_file.name),
                        "size_mb": round(size_mb, 2),
                        "age_days": age_days,
                    }
                )

            # 古いファイル
            if age_days > self.max_age_days:
                analysis["old_files"].append(
                    {
                        "file": str(log_file.name),
                        "size_mb": round(size_mb, 2),
                        "age_days": age_days,
                    }
                )

            # 空ファイル
            if stat.st_size == 0:
                analysis["empty_files"].append(str(log_file.name))

            # 拡張子別
            ext = log_file.suffix
            if ext not in analysis["by_extension"]:
                analysis["by_extension"][ext] = {"count": 0, "size_mb": 0}
            analysis["by_extension"][ext]["count"] += 1
            analysis["by_extension"][ext]["size_mb"] += size_mb

            # 日付別
            date_str = modified_date.strftime("%Y-%m-%d")
            if date_str not in analysis["by_date"]:
                analysis["by_date"][date_str] = {"count": 0, "size_mb": 0}
            analysis["by_date"][date_str]["count"] += 1
            analysis["by_date"][date_str]["size_mb"] += size_mb

        analysis["total_size_mb"] = round(analysis["total_size_mb"], 2)

        self.logger.info(
            f"📊 分析完了: {analysis['total_files']}ファイル, {analysis['total_size_mb']}MB"
        )
        return analysis

    def rotate_large_files(self) -> List[str]:
        """大容量ファイルのローテーション"""
        self.logger.info("🔄 大容量ファイルローテーション開始")

        rotated_files = []

        for log_file in self.logs_dir.glob("*.log"):
            if not log_file.is_file():
                continue

            size_mb = log_file.stat().st_size / (1024 * 1024)

            if size_mb > self.max_file_size_mb:
                self.logger.info(
                    f"📦 ローテーション: {log_file.name} ({size_mb:0.1f}MB)"
                )

                # タイムスタンプ付きファイル名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archived_name = f"{log_file.stem}_{timestamp}.log"
                archived_path = self.archive_dir / archived_name

                # ファイル移動
                shutil.move(str(log_file), str(archived_path))

                # 新しい空ファイル作成
                log_file.touch()

                # 圧縮
                self._compress_file(archived_path)

                rotated_files.append(str(log_file.name))

        self.logger.info(f"✅ ローテーション完了: {len(rotated_files)}ファイル")
        return rotated_files

    def compress_old_files(self) -> List[str]:
        """古いファイルの圧縮"""
        self.logger.info("🗜️ 古いファイル圧縮開始")

        compressed_files = []
        cutoff_date = datetime.now() - timedelta(days=self.compress_older_than_days)

        # アーカイブディレクトリ内の未圧縮ファイル
        for log_file in self.archive_dir.glob("*.log"):
            if not log_file.is_file():
                continue

            modified_date = datetime.fromtimestamp(log_file.stat().st_mtime)

            if modified_date < cutoff_date:
                self.logger.info(f"🗜️ 圧縮: {log_file.name}")
                self._compress_file(log_file)
                compressed_files.append(str(log_file.name))

        self.logger.info(f"✅ 圧縮完了: {len(compressed_files)}ファイル")
        return compressed_files

    def cleanup_old_files(self) -> List[str]:
        """古いファイルの削除"""
        self.logger.info("🗑️ 古いファイル削除開始")

        deleted_files = []
        cutoff_date = datetime.now() - timedelta(days=self.keep_compressed_days)

        # 古い圧縮ファイルを削除
        for gz_file in self.archive_dir.glob("*.gz"):
            if not gz_file.is_file():
                continue

            modified_date = datetime.fromtimestamp(gz_file.stat().st_mtime)

            if modified_date < cutoff_date:
                self.logger.info(f"🗑️ 削除: {gz_file.name}")
                gz_file.unlink()
                deleted_files.append(str(gz_file.name))

        # 空ファイルの削除
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.is_file() and log_file.stat().st_size == 0:
                # 最近作成されたファイルでない場合のみ削除
                created_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                if (datetime.now() - created_date).days > 1:
                    self.logger.info(f"🗑️ 空ファイル削除: {log_file.name}")
                    log_file.unlink()
                    deleted_files.append(str(log_file.name))

        self.logger.info(f"✅ 削除完了: {len(deleted_files)}ファイル")
        return deleted_files

    def _compress_file(self, file_path: Path):
        """ファイル圧縮"""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

        with open(file_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # 元ファイル削除
        file_path.unlink()

    def generate_logrotate_config(self):
        """logrotate設定ファイル生成"""
        config_content = f"""# Elders Guild Log Rotation Configuration
{self.logs_dir}/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 aicompany aicompany
    size {self.max_file_size_mb}M

    postrotate
        # ワーカープロセスにログ再開シグナル送信
        pkill -USR1 -f "python.*worker" 2>/dev/null || true
    endscript
}}

# 特別な設定が必要な大容量ログ
{self.logs_dir}/elf_forest.log {{
    hourly
    size 50M
    rotate 48
    compress
    delaycompress
    missingok
    notifempty
    create 0644 aicompany aicompany
}}
"""

        logrotate_config = self.project_dir / "config" / "logrotate.conf"
        logrotate_config.parent.mkdir(exist_ok=True)

        with open(logrotate_config, "w") as f:
            f.write(config_content)

        self.logger.info(f"📝 logrotate設定生成: {logrotate_config}")
        return str(logrotate_config)

    def setup_cron_job(self):
        """cron設定の生成"""
        cron_entry = f"""# Elders Guild Log Maintenance
0 2 * * * {sys.executable} {__file__} --maintenance 2>&1 | logger -t log_maintenance
0 */6 * * * {sys.executable} {__file__} --rotate 2>&1 | logger -t log_maintenance
"""

        cron_file = self.project_dir / "config" / "log_maintenance.cron"
        with open(cron_file, "w") as f:
            f.write(cron_entry)

        self.logger.info(f"⏰ cron設定生成: {cron_file}")
        self.logger.info("手動でcrontabに追加してください:")
        self.logger.info(f"crontab -e && cat {cron_file}")

        return str(cron_file)

    def run_maintenance(self):
        """メンテナンス実行"""
        self.logger.info("🧹 ログメンテナンス開始")

        # 分析
        analysis = self.analyze_logs()

        # メンテナンス実行
        rotated = self.rotate_large_files()
        compressed = self.compress_old_files()
        deleted = self.cleanup_old_files()

        # 設定ファイル生成
        logrotate_config = self.generate_logrotate_config()
        cron_file = self.setup_cron_job()

        # レポート生成
        report = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "actions": {
                "rotated_files": rotated,
                "compressed_files": compressed,
                "deleted_files": deleted,
            },
            "configs": {"logrotate_config": logrotate_config, "cron_file": cron_file},
        }

        # レポート保存
        report_file = (
            self.logs_dir
            / f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"📊 メンテナンスレポート: {report_file}")
        self.logger.info("✅ ログメンテナンス完了")

        return report


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Log Maintenance System")
    parser.add_argument("--analyze", action="store_true", help="ログ分析のみ実行")
    parser.add_argument("--rotate", action="store_true", help="ローテーションのみ実行")
    parser.add_argument(
        "--maintenance", action="store_true", help="フルメンテナンス実行"
    )
    parser.add_argument("--config", action="store_true", help="設定ファイル生成のみ")

    args = parser.parse_args()

    maintenance = LogMaintenanceSystem()

    if args.analyze:
        analysis = maintenance.analyze_logs()
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    elif args.rotate:
        rotated = maintenance.rotate_large_files()
        print(f"ローテーション完了: {rotated}")
    elif args.config:
        logrotate_config = maintenance.generate_logrotate_config()
        cron_file = maintenance.setup_cron_job()
        print(f"設定ファイル生成完了: {logrotate_config}, {cron_file}")
    elif args.maintenance:
        maintenance.run_maintenance()
        print("メンテナンス完了")
    else:
        print("🧹 Elders Guild Log Maintenance System")
        print("使用方法:")
        print("  --analyze     : ログ分析")
        print("  --rotate      : 大容量ファイルローテーション")
        print("  --maintenance : フルメンテナンス")
        print("  --config      : 設定ファイル生成")


if __name__ == "__main__":
    main()
