#!/usr/bin/env python3
"""
エルダーズギルド レポート整理自動化スクリプト
エルダー評議会令第600号 - レポート管理効率化令

機能:
1. 既存レポートの分析・分類
2. 時系列・カテゴリ別整理
3. 重複レポート検出
4. アーカイブ推奨
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import shutil
import argparse
from dataclasses import dataclass
import hashlib

@dataclass
class ReportInfo:
    """レポート情報"""
    path: Path
    date: datetime
    category: str
    type: str  # daily, weekly, monthly, adhoc
    size: int
    hash: str
    title: str

class ReportOrganizer:
    """レポート整理器"""
    
    def __init__(self, base_path: str = "/home/aicompany/ai_co"):
        self.base_path = Path(base_path)
        self.reports_path = self.base_path / "docs" / "reports"
        
        # レポートカテゴリ定義
        self.categories = {
            "development": ["completion", "progress", "phase", "implementation"],
            "quality": ["test", "coverage", "quality", "benchmark"],
            "operations": ["incident", "emergency", "repair", "fix"],
            "analysis": ["analysis", "investigation", "research", "study"],
            "council": ["council", "elder", "sage", "decision"]
        }
        
        # 日付パターン
        self.date_patterns = [
            r"(\d{4})[_-]?(\d{2})[_-]?(\d{2})",  # YYYY-MM-DD or YYYYMMDD
            r"(\d{4})年(\d{1,2})月(\d{1,2})日",   # Japanese format
            r"week[_-]?(\d+)",                     # Week number
            r"phase[_-]?(\d+)",                    # Phase number
        ]
    
    def analyze_reports(self) -> Dict[str, List[ReportInfo]]:
        """既存レポートの分析"""
        reports = {
            "periodic": [],
            "category": [],
            "uncategorized": [],
            "duplicates": []
        }
        
        # ハッシュマップ（重複検出用）
        hash_map = {}
        
        # レポートファイル検索
        report_files = []
        for pattern in ["**/*report*.md", "**/*analysis*.md", "**/*completion*.md"]:
            report_files.extend(self.base_path.glob(pattern))
        
        # 仮想環境とgitディレクトリを除外
        report_files = [f for f in report_files 
                       if not any(p in str(f) for p in ["venv", ".git", "__pycache__"])]
        
        for file_path in report_files:
            try:
                # ファイル情報取得
                content = file_path.read_text(encoding='utf-8')
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                # 重複チェック
                if file_hash in hash_map:
                    reports["duplicates"].append((file_path, hash_map[file_hash]))
                    continue
                
                hash_map[file_hash] = file_path
                
                # レポート情報生成
                report_info = self._create_report_info(file_path, content)
                
                # 分類
                if report_info.type in ["daily", "weekly", "monthly"]:
                    reports["periodic"].append(report_info)
                elif report_info.category != "uncategorized":
                    reports["category"].append(report_info)
                else:
                    reports["uncategorized"].append(report_info)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return reports
    
    def _create_report_info(self, file_path: Path, content: str) -> ReportInfo:
        """レポート情報生成"""
        # 日付抽出
        date = self._extract_date(file_path.name, content)
        
        # カテゴリ判定
        category = self._determine_category(file_path.name, content)
        
        # タイプ判定
        report_type = self._determine_type(file_path.name, content)
        
        # タイトル抽出
        title = self._extract_title(content)
        
        return ReportInfo(
            path=file_path,
            date=date,
            category=category,
            type=report_type,
            size=file_path.stat().st_size,
            hash=hashlib.md5(content.encode()).hexdigest(),
            title=title
        )
    
    def _extract_date(self, filename: str, content: str) -> datetime:
        """日付抽出"""
        # ファイル名から
        for pattern in self.date_patterns[:2]:
            match = re.search(pattern, filename)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                except:
                    pass
        
        # コンテンツから
        lines = content.split('\n')[:30]  # 最初の30行
        for line in lines:
            for pattern in self.date_patterns[:2]:
                match = re.search(pattern, line)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            year, month, day = match.groups()
                            return datetime(int(year), int(month), int(day))
                    except:
                        pass
        
        # デフォルト（ファイル更新日時）
        return datetime.now()
    
    def _determine_category(self, filename: str, content: str) -> str:
        """カテゴリ判定"""
        text = (filename + " " + content[:1000]).lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return "uncategorized"
    
    def _determine_type(self, filename: str, content: str) -> str:
        """レポートタイプ判定"""
        text = (filename + " " + content[:500]).lower()
        
        if "daily" in text or "日次" in text:
            return "daily"
        elif "weekly" in text or "週次" in text:
            return "weekly"
        elif "monthly" in text or "月次" in text:
            return "monthly"
        else:
            return "adhoc"
    
    def _extract_title(self, content: str) -> str:
        """タイトル抽出"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled Report"
    
    def organize_reports(self, dry_run: bool = True) -> Dict[str, int]:
        """レポート整理実行"""
        results = {
            "moved": 0,
            "archived": 0,
            "deduplicated": 0,
            "errors": 0
        }
        
        # 分析実行
        report_analysis = self.analyze_reports()
        
        # 新ディレクトリ構造作成
        if not dry_run:
            self._create_directory_structure()
        
        # 定期レポート整理
        for report in report_analysis["periodic"]:
            try:
                new_path = self._get_periodic_path(report)
                if not dry_run:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(report.path), str(new_path))
                results["moved"] += 1
            except Exception as e:
                print(f"Error moving {report.path}: {e}")
                results["errors"] += 1
        
        # カテゴリ別レポート整理
        for report in report_analysis["category"]:
            try:
                new_path = self._get_category_path(report)
                if not dry_run:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(report.path), str(new_path))
                results["moved"] += 1
            except Exception as e:
                print(f"Error moving {report.path}: {e}")
                results["errors"] += 1
        
        # 重複処理
        for duplicate_pair in report_analysis["duplicates"]:
            try:
                if isinstance(duplicate_pair, tuple) and len(duplicate_pair) == 2:
                    original, duplicate = duplicate_pair
                    if not dry_run and duplicate.exists():
                        # アーカイブディレクトリに移動
                        archive_path = self.base_path / "archives" / "duplicate_reports"
                        archive_path.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(duplicate), str(archive_path / duplicate.name))
                    results["deduplicated"] += 1
            except Exception as e:
                print(f"Error archiving duplicate: {e}")
                results["errors"] += 1
        
        return results
    
    def _create_directory_structure(self):
        """ディレクトリ構造作成"""
        # 定期レポート
        for report_type in ["daily", "weekly", "monthly"]:
            path = self.reports_path / "periodic" / report_type / "2025"
            path.mkdir(parents=True, exist_ok=True)
        
        # カテゴリ別
        for category in self.categories.keys():
            path = self.reports_path / "category" / category
            path.mkdir(parents=True, exist_ok=True)
    
    def _get_periodic_path(self, report: ReportInfo) -> Path:
        """定期レポートパス生成"""
        if report.type == "daily":
            return self.reports_path / "periodic" / "daily" / \
                   f"{report.date.year}" / f"{report.date.month:02d}" / \
                   f"{report.date.day:02d}" / report.path.name
        elif report.type == "weekly":
            week = report.date.isocalendar()[1]
            return self.reports_path / "periodic" / "weekly" / \
                   f"{report.date.year}" / f"week-{week:02d}" / report.path.name
        else:  # monthly
            return self.reports_path / "periodic" / "monthly" / \
                   f"{report.date.year}" / f"{report.date.month:02d}" / report.path.name
    
    def _get_category_path(self, report: ReportInfo) -> Path:
        """カテゴリパス生成"""
        return self.reports_path / "category" / report.category / \
               f"{report.date.year}" / report.path.name
    
    def generate_summary(self, analysis: Dict[str, List[ReportInfo]]) -> str:
        """サマリー生成"""
        total = sum(len(v) for k, v in analysis.items() if k != "duplicates")
        duplicates = len(analysis["duplicates"])
        
        summary = f"""
📊 レポート分析結果:
総レポート数: {total}
重複: {duplicates}

カテゴリ別:
- 定期レポート: {len(analysis["periodic"])}
  - 日次: {sum(1 for r in analysis["periodic"] if r.type == "daily")}
  - 週次: {sum(1 for r in analysis["periodic"] if r.type == "weekly")}
  - 月次: {sum(1 for r in analysis["periodic"] if r.type == "monthly")}
- カテゴリ別: {len(analysis["category"])}
"""
        
        # カテゴリ分布
        category_dist = {}
        for report in analysis["category"]:
            category_dist[report.category] = category_dist.get(report.category, 0) + 1
        
        for cat, count in sorted(category_dist.items()):
            summary += f"  - {cat}: {count}\n"
        
        summary += f"- 未分類: {len(analysis['uncategorized'])}\n"
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='エルダーズギルド レポート整理ツール')
    parser.add_argument('--dry-run', action='store_true', help='実際の移動は行わない')
    parser.add_argument('--analyze-only', action='store_true', help='分析のみ実行')
    parser.add_argument('--base-path', default='/home/aicompany/ai_co', help='ベースパス')
    
    args = parser.parse_args()
    
    organizer = ReportOrganizer(args.base_path)
    
    print("🏛️ エルダーズギルド レポート整理システム")
    print("📊 レポート分析中...")
    
    analysis = organizer.analyze_reports()
    print(organizer.generate_summary(analysis))
    
    if args.analyze_only:
        return
    
    print(f"\n🔧 整理実行（ドライラン: {'有効' if args.dry_run else '無効'}）")
    results = organizer.organize_reports(dry_run=args.dry_run)
    
    print(f"""
✅ 実行結果:
- 移動: {results['moved']}
- アーカイブ: {results['archived']}
- 重複除去: {results['deduplicated']}
- エラー: {results['errors']}
""")

if __name__ == "__main__":
    main()