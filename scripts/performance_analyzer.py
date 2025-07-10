#!/usr/bin/env python3
"""
Performance Analyzer - システムパフォーマンス分析ツール
エルダーズギルドのシステム全体のパフォーマンス監視と最適化提案

🔍 分析項目:
- CPU/メモリ使用率
- プロセス分析
- ディスク I/O
- ネットワーク使用量
- ボトルネック特定
- 最適化提案
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List
from typing import Tuple

import psutil


@dataclass
class ProcessInfo:
    """プロセス情報"""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    create_time: str
    cmdline: str


@dataclass
class SystemMetrics:
    """システムメトリクス"""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    load_average: List[float]
    boot_time: str
    uptime_hours: float


@dataclass
class PerformanceAnalysis:
    """パフォーマンス分析結果"""

    system_metrics: SystemMetrics
    top_cpu_processes: List[ProcessInfo]
    top_memory_processes: List[ProcessInfo]
    elder_processes: List[ProcessInfo]
    bottlenecks: List[str]
    recommendations: List[str]
    health_score: int  # 0-100


class PerformanceAnalyzer:
    """システムパフォーマンス分析クラス"""

    def __init__(self, project_dir: str = "/home/aicompany/ai_co"):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / "logs"

        # ログ設定
        self.setup_logging()

        # しきい値設定
        self.cpu_warning_threshold = 80.0
        self.memory_warning_threshold = 85.0
        self.disk_warning_threshold = 90.0

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(self.logs_dir / "performance_analyzer.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def get_system_metrics(self) -> SystemMetrics:
        """システムメトリクス取得"""
        self.logger.info("📊 システムメトリクス取得開始")

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # メモリ使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # ディスク使用率
        disk = psutil.disk_usage("/")
        disk_usage_percent = disk.percent

        # 負荷平均
        load_avg = os.getloadavg()

        # ブート時間
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()

        # アップタイム
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds / 3600

        metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage_percent=disk_usage_percent,
            load_average=list(load_avg),
            boot_time=boot_time,
            uptime_hours=round(uptime_hours, 2),
        )

        self.logger.info(
            f"✅ システムメトリクス: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_usage_percent}%"
        )
        return metrics

    def get_process_info(self, limit: int = 10) -> Tuple[List[ProcessInfo], List[ProcessInfo]]:
        """プロセス情報取得"""
        self.logger.info("🔍 プロセス情報取得開始")

        processes = []

        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent", "memory_info", "status", "create_time", "cmdline"]
        ):
            try:
                pinfo = proc.info
                process_info = ProcessInfo(
                    pid=pinfo["pid"],
                    name=pinfo["name"],
                    cpu_percent=pinfo["cpu_percent"] or 0,
                    memory_percent=pinfo["memory_percent"] or 0,
                    memory_mb=(pinfo["memory_info"].rss / 1024 / 1024) if pinfo["memory_info"] else 0,
                    status=pinfo["status"],
                    create_time=(
                        datetime.fromtimestamp(pinfo["create_time"]).isoformat() if pinfo["create_time"] else ""
                    ),
                    cmdline=" ".join(pinfo["cmdline"]) if pinfo["cmdline"] else "",
                )
                processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

                # CPU使用率でソート\n        top_cpu = sorted(processes, key=lambda x: x.cpu_percent, reverse=True)[:limit]\n        \n        # メモリ使用率でソート\n        top_memory = sorted(processes, key=lambda x: x.memory_percent, reverse=True)[:limit]\n        \n        self.logger.info(f\"✅ プロセス情報: {len(processes)}プロセス分析完了\")\n        return top_cpu, top_memory\n    \n    def get_elder_processes(self) -> List[ProcessInfo]:\n        \"\"\"エルダーズギルド関連プロセス取得\"\"\"\n        self.logger.info(\"🧙‍♂️ エルダーズプロセス検出開始\")\n        \n        elder_keywords = [\n            'claude', 'elder', 'sage', 'worker', 'knight',\n            'rag_', 'task_', 'incident_', 'pm_worker',\n            'monitoring', 'quantum', 'ai_', 'elf_forest'\n        ]\n        \n        elder_processes = []\n        \n        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'cmdline']):\n            try:\n                pinfo = proc.info\n                cmdline = ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else ""\n                \n                # エルダーズ関連プロセスかチェック\n                is_elder = any(keyword in cmdline.lower() for keyword in elder_keywords)\n                \n                if is_elder:\n                    process_info = ProcessInfo(\n                        pid=pinfo['pid'],\n                        name=pinfo['name'],\n                        cpu_percent=pinfo['cpu_percent'] or 0,\n                        memory_percent=pinfo['memory_percent'] or 0,\n                        memory_mb=(pinfo['memory_info'].rss / 1024 / 1024) if pinfo['memory_info'] else 0,\n                        status=pinfo['status'],\n                        create_time=datetime.fromtimestamp(pinfo['create_time']).isoformat() if pinfo['create_time'] else "",\n                        cmdline=cmdline\n                    )\n                    elder_processes.append(process_info)\n                    \n            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # CPU使用率でソート\n        elder_processes.sort(key=lambda x: x.cpu_percent, reverse=True)\n        \n        self.logger.info(f\"🧙‍♂️ エルダーズプロセス: {len(elder_processes)}個検出\")\n        return elder_processes\n    \n    def detect_bottlenecks(self, metrics: SystemMetrics, top_cpu: List[ProcessInfo], \n                          top_memory: List[ProcessInfo]) -> List[str]:\n        \"\"\"ボトルネック検出\"\"\"\n        self.logger.info(\"🔍 ボトルネック検出開始\")\n        \n        bottlenecks = []\n        \n        # CPU ボトルネック\n        if metrics.cpu_percent > self.cpu_warning_threshold:\n            bottlenecks.append(f\"CPU使用率が高い: {metrics.cpu_percent}%\")\n            if top_cpu:\n                top_proc = top_cpu[0]\n                bottlenecks.append(f\"CPU最大消費プロセス: {top_proc.name} (PID: {top_proc.pid}, CPU: {top_proc.cpu_percent}%)\")\n        \n        # メモリ ボトルネック\n        if metrics.memory_percent > self.memory_warning_threshold:\n            bottlenecks.append(f\"メモリ使用率が高い: {metrics.memory_percent}%\")\n            if top_memory:\n                top_proc = top_memory[0]\n                bottlenecks.append(f\"メモリ最大消費プロセス: {top_proc.name} (PID: {top_proc.pid}, Memory: {top_proc.memory_mb:.1f}MB)\")\n        \n        # ディスク ボトルネック\n        if metrics.disk_usage_percent > self.disk_warning_threshold:\n            bottlenecks.append(f\"ディスク使用率が高い: {metrics.disk_usage_percent}%\")\n        \n        # 負荷平均チェック\n        cpu_count = psutil.cpu_count()\n        if metrics.load_average[0] > cpu_count * 1.5:\n            bottlenecks.append(f\"システム負荷が高い: {metrics.load_average[0]} (CPU数: {cpu_count})\")\n        \n        # Claude プロセス多重起動チェック\n        claude_processes = [p for p in top_cpu + top_memory if 'claude' in p.name.lower()]\n        if len(claude_processes) > 3:\n            bottlenecks.append(f\"Claude プロセス多重起動: {len(claude_processes)}個\")\n        \n        self.logger.info(f\"🔍 ボトルネック検出: {len(bottlenecks)}個\")\n        return bottlenecks\n    \n    def generate_recommendations(self, metrics: SystemMetrics, bottlenecks: List[str], \n                               elder_processes: List[ProcessInfo]) -> List[str]:\n        \"\"\"最適化推奨事項生成\"\"\"\n        self.logger.info(\"💡 最適化推奨事項生成開始\")\n        \n        recommendations = []\n        \n        # CPU最適化\n        if metrics.cpu_percent > 70:\n            recommendations.append(\"CPU負荷軽減: 不要なプロセス停止、非同期処理の活用\")\n            \n            high_cpu_elders = [p for p in elder_processes if p.cpu_percent > 10]\n            if high_cpu_elders:\n                recommendations.append(f\"エルダーズプロセス最適化: {len(high_cpu_elders)}個のプロセスがCPU負荷高\")\n        \n        # メモリ最適化\n        if metrics.memory_percent > 75:\n            recommendations.append(\"メモリ使用量削減: キャッシュクリア、メモリリーク調査\")\n            \n            high_mem_elders = [p for p in elder_processes if p.memory_mb > 100]\n            if high_mem_elders:\n                recommendations.append(f\"エルダーズメモリ最適化: {len(high_mem_elders)}個のプロセスがメモリ消費大\")\n        \n        # プロセス最適化\n        sleeping_processes = [p for p in elder_processes if p.status == 'sleeping' and p.cpu_percent < 0.1]\n        if len(sleeping_processes) > 5:\n            recommendations.append(f\"休眠プロセス整理: {len(sleeping_processes)}個の低活動プロセス\")\n        \n        # Claude多重起動対策\n        claude_count = len([p for p in elder_processes if 'claude' in p.name.lower()])\n        if claude_count > 2:\n            recommendations.append(f\"Claude多重起動対策: {claude_count}個のClaude プロセス統合検討\")\n        \n        # ログファイル整理\n        recommendations.append(\"定期ログメンテナンス: Log Maintenance System の定期実行設定\")\n        \n        # データベース最適化\n        recommendations.append(\"データベース最適化: インデックス再構築、古いデータアーカイブ\")\n        \n        # 監視システム\n        recommendations.append(\"継続監視設定: Performance Analyzer の定期実行とアラート設定\")\n        \n        self.logger.info(f\"💡 推奨事項: {len(recommendations)}項目生成\")\n        return recommendations\n    \n    def calculate_health_score(self, metrics: SystemMetrics, bottlenecks: List[str]) -> int:\n        \"\"\"システムヘルススコア計算 (0-100)\"\"\"\n        score = 100\n        \n        # CPU スコア減点\n        if metrics.cpu_percent > 90:\n            score -= 30\n        elif metrics.cpu_percent > 70:\n            score -= 15\n        elif metrics.cpu_percent > 50:\n            score -= 5\n        \n        # メモリ スコア減点\n        if metrics.memory_percent > 90:\n            score -= 25\n        elif metrics.memory_percent > 75:\n            score -= 10\n        elif metrics.memory_percent > 60:\n            score -= 5\n        \n        # ディスク スコア減点\n        if metrics.disk_usage_percent > 95:\n            score -= 20\n        elif metrics.disk_usage_percent > 85:\n            score -= 10\n        \n        # ボトルネック数による減点\n        score -= len(bottlenecks) * 5\n        \n        # 負荷平均による減点\n        cpu_count = psutil.cpu_count()\n        if metrics.load_average[0] > cpu_count * 2:\n            score -= 15\n        elif metrics.load_average[0] > cpu_count * 1.5:\n            score -= 10\n        \n        return max(0, min(100, score))\n    \n    def analyze_performance(self) -> PerformanceAnalysis:\n        \"\"\"総合パフォーマンス分析\"\"\"\n        self.logger.info(\"🚀 総合パフォーマンス分析開始\")\n        \n        # メトリクス取得\n        metrics = self.get_system_metrics()\n        \n        # プロセス情報取得\n        top_cpu, top_memory = self.get_process_info()\n        \n        # エルダーズプロセス取得\n        elder_processes = self.get_elder_processes()\n        \n        # ボトルネック検出\n        bottlenecks = self.detect_bottlenecks(metrics, top_cpu, top_memory)\n        \n        # 推奨事項生成\n        recommendations = self.generate_recommendations(metrics, bottlenecks, elder_processes)\n        \n        # ヘルススコア計算\n        health_score = self.calculate_health_score(metrics, bottlenecks)\n        \n        analysis = PerformanceAnalysis(\n            system_metrics=metrics,\n            top_cpu_processes=top_cpu,\n            top_memory_processes=top_memory,\n            elder_processes=elder_processes,\n            bottlenecks=bottlenecks,\n            recommendations=recommendations,\n            health_score=health_score\n        )\n        \n        self.logger.info(f\"✅ 分析完了: ヘルススコア {health_score}/100\")\n        return analysis\n    \n    def save_analysis_report(self, analysis: PerformanceAnalysis) -> str:\n        \"\"\"分析レポート保存\"\"\"\n        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n        report_file = self.logs_dir / f\"performance_analysis_{timestamp}.json\"\n        \n        # JSON形式で保存\n        with open(report_file, 'w') as f:\n            json.dump(asdict(analysis), f, indent=2, ensure_ascii=False)\n        \n        self.logger.info(f\"📊 分析レポート保存: {report_file}\")\n        return str(report_file)\n    \n    def print_summary(self, analysis: PerformanceAnalysis):\n        \"\"\"分析結果サマリー表示\"\"\"\n        print(\"\\n\" + \"=\"*60)\n        print(\"🔍 Elders Guild Performance Analysis Report\")\n        print(\"=\"*60)\n        \n        # システムメトリクス\n        print(f\"\\n📊 System Metrics (Health Score: {analysis.health_score}/100)\")\n        print(f\"  CPU Usage: {analysis.system_metrics.cpu_percent:.1f}%\")\n        print(f\"  Memory Usage: {analysis.system_metrics.memory_percent:.1f}%\")\n        print(f\"  Disk Usage: {analysis.system_metrics.disk_usage_percent:.1f}%\")\n        print(f\"  Load Average: {analysis.system_metrics.load_average}\")\n        print(f\"  Uptime: {analysis.system_metrics.uptime_hours:.1f} hours\")\n        \n        # ボトルネック\n        if analysis.bottlenecks:\n            print(f\"\\n🚨 Detected Bottlenecks ({len(analysis.bottlenecks)}):\")\n            for i, bottleneck in enumerate(analysis.bottlenecks, 1):\n                print(f\"  {i}. {bottleneck}\")\n        else:\n            print(\"\\n✅ No Critical Bottlenecks Detected\")\n        \n        # トップCPUプロセス\n        print(f\"\\n🔥 Top CPU Processes:\")\n        for i, proc in enumerate(analysis.top_cpu_processes[:5], 1):\n            print(f\"  {i}. {proc.name} (PID: {proc.pid}) - CPU: {proc.cpu_percent:.1f}%, Memory: {proc.memory_mb:.1f}MB\")\n        \n        # エルダーズプロセス\n        if analysis.elder_processes:\n            print(f\"\\n🧙‍♂️ Elders Guild Processes ({len(analysis.elder_processes)}):\")\n            for i, proc in enumerate(analysis.elder_processes[:5], 1):\n                print(f\"  {i}. {proc.name} (PID: {proc.pid}) - CPU: {proc.cpu_percent:.1f}%, Memory: {proc.memory_mb:.1f}MB\")\n        \n        # 推奨事項\n        print(f\"\\n💡 Optimization Recommendations:\")\n        for i, rec in enumerate(analysis.recommendations, 1):\n            print(f\"  {i}. {rec}\")\n        \n        print(\"\\n\" + \"=\"*60)\n\ndef main():\n    \"\"\"メイン実行関数\"\"\"\n    import argparse\n    \n    parser = argparse.ArgumentParser(description=\"Performance Analyzer\")\n    parser.add_argument(\"--analyze\", action=\"store_true\", help=\"総合パフォーマンス分析実行\")\n    parser.add_argument(\"--metrics\", action=\"store_true\", help=\"システムメトリクスのみ表示\")\n    parser.add_argument(\"--processes\", action=\"store_true\", help=\"プロセス情報のみ表示\")\n    parser.add_argument(\"--elders\", action=\"store_true\", help=\"エルダーズプロセスのみ表示\")\n    parser.add_argument(\"--save\", action=\"store_true\", help=\"結果をファイルに保存\")\n    \n    args = parser.parse_args()\n    \n    analyzer = PerformanceAnalyzer()\n    \n    if args.metrics:\n        metrics = analyzer.get_system_metrics()\n        print(json.dumps(asdict(metrics), indent=2, ensure_ascii=False))\n    elif args.processes:\n        top_cpu, top_memory = analyzer.get_process_info()\n        print(\"Top CPU Processes:\")\n        for proc in top_cpu[:10]:\n            print(f\"  {proc.name} (PID: {proc.pid}) - CPU: {proc.cpu_percent}%, Memory: {proc.memory_mb:.1f}MB\")\n    elif args.elders:\n        elder_processes = analyzer.get_elder_processes()\n        print(f\"Elders Guild Processes ({len(elder_processes)}):\")\n        for proc in elder_processes:\n            print(f\"  {proc.name} (PID: {proc.pid}) - CPU: {proc.cpu_percent}%, Memory: {proc.memory_mb:.1f}MB\")\n    elif args.analyze:\n        analysis = analyzer.analyze_performance()\n        analyzer.print_summary(analysis)\n        \n        if args.save:\n            report_file = analyzer.save_analysis_report(analysis)\n            print(f\"\\n📄 Report saved: {report_file}\")\n    else:\n        print(\"🔍 Elders Guild Performance Analyzer\")\n        print(\"使用方法:\")\n        print(\"  --analyze     : 総合パフォーマンス分析\")\n        print(\"  --metrics     : システムメトリクス表示\")\n        print(\"  --processes   : プロセス情報表示\")\n        print(\"  --elders      : エルダーズプロセス表示\")\n        print(\"  --save        : 結果保存 (--analyzeと併用)\")\n\nif __name__ == \"__main__\":\n    main()
