#!/usr/bin/env python3
"""
💬 Quality Pipeline PR コメント自動投稿
GitHub PRに品質チェック結果を自動コメント
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
import requests

class QualityPRCommentBot:
    """品質チェック結果PR投稿ボット"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('GITHUB_REPOSITORY')
        self.pr_number = os.getenv('PR_NUMBER')
        
        if not all([self.github_token, self.repository, self.pr_number]):
            raise ValueError("必要な環境変数が設定されていません")
    
    def run_quality_checks(self, target_path: str) -> Dict:
        """品質チェック実行"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "target_path": target_path,
            "checks": {}
        }
        
        # Black フォーマットチェック
        try:
            cmd = f"black --check --diff {target_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            results["checks"]["black"] = {
                "status": "✅ PASS" if result.returncode == 0 else "❌ FAIL",
                "details": result.stdout or result.stderr
            }
        except Exception as e:
            results["checks"]["black"] = {"status": "⚠️ ERROR", "details": str(e)}
        
        # isort チェック
        try:
            cmd = f"isort --check-only --diff {target_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            results["checks"]["isort"] = {
                "status": "✅ PASS" if result.returncode == 0 else "❌ FAIL",
                "details": result.stdout or result.stderr
            }
        except Exception as e:
            results["checks"]["isort"] = {"status": "⚠️ ERROR", "details": str(e)}
        
        # Pylint チェック
        try:
            cmd = f"pylint {target_path} --output-format=parseable --score=yes"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            # Pylint score 抽出
            score = "N/A"
            for line in result.stdout.split('\n'):
                if "Your code has been rated at" in line:
                    score = line.split("at ")[1].split("/")[0].strip()
                    break
            
            results["checks"]["pylint"] = {
                "status": "✅ PASS" if float(score.replace("N/A", "0")) >= 8.0 else "⚠️ WARN",
                "score": score,
                "details": result.stdout[-500:] if result.stdout else result.stderr[-500:]
            }
        except Exception as e:
            results["checks"]["pylint"] = {"status": "⚠️ ERROR", "details": str(e)}
        
        # MyPy チェック
        try:
            cmd = f"mypy {target_path} --ignore-missing-imports"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            error_count = len([line for line in result.stdout.split('\n') if ': error:' in line])
            
            results["checks"]["mypy"] = {
                "status": "✅ PASS" if result.returncode == 0 else "⚠️ WARN",
                "errors": error_count,
                "details": result.stdout[-500:] if result.stdout else "No type errors"
            }
        except Exception as e:
            results["checks"]["mypy"] = {"status": "⚠️ ERROR", "details": str(e)}
        
        return results
    
    def generate_comment_body(self, results: Dict) -> str:
        """PRコメント本文生成"""
        checks = results["checks"]
        
        # 総合判定
        statuses = [check["status"] for check in checks.values()]
        overall_status = "✅ PASS" if all("✅" in status for status in statuses) else "⚠️ NEEDS ATTENTION"
        
        comment = f"""## 🏛️ Quality Pipeline レポート

**実行時刻**: {results["timestamp"]}  
**対象**: `{results["target_path"]}`  
**総合判定**: {overall_status}

---

### 📊 品質チェック結果

| ツール | 状態 | 詳細 |
|--------|------|------|
| **Black** (フォーマット) | {checks.get('black', {}).get('status', 'N/A')} | {'コード整形済み' if '✅' in checks.get('black', {}).get('status', '') else '要修正'} |
| **isort** (Import順序) | {checks.get('isort', {}).get('status', 'N/A')} | {'Import順序適正' if '✅' in checks.get('isort', {}).get('status', '') else '要修正'} |
| **Pylint** (静的解析) | {checks.get('pylint', {}).get('status', 'N/A')} | スコア: {checks.get('pylint', {}).get('score', 'N/A')}/10 |
| **MyPy** (型チェック) | {checks.get('mypy', {}).get('status', 'N/A')} | エラー: {checks.get('mypy', {}).get('errors', 'N/A')}件 |

---

### 🔧 修正方法

"""
        
        # 修正方法の提案
        if "❌" in checks.get('black', {}).get('status', ''):
            comment += """
**Black フォーマット修正**:
```bash
black {target_path}
```
""".format(target_path=results["target_path"])
        
        if "❌" in checks.get('isort', {}).get('status', ''):
            comment += """
**isort Import順序修正**:
```bash
isort {target_path}
```
""".format(target_path=results["target_path"])
        
        if float(checks.get('pylint', {}).get('score', '0').replace('N/A', '0')) < 8.0:
            comment += """
**Pylint 品質改善**:
- スコア8.0以上を目指してください
- 詳細: `pylint {target_path}`
""".format(target_path=results["target_path"])
        
        comment += """
---

### 🚀 次のステップ

1. 上記の修正を適用
2. ローカルでテスト実行: `pytest tests/integration/test_quality_servants_mock.py`
3. 変更をコミット・プッシュ

---

*🤖 Generated by Elder Council Quality Pipeline*
*💡 質問は [Quality Pipeline ドキュメント](./docs/technical/QUALITY_PIPELINE_PROGRESS_REPORT.md) を参照*
"""
        
        return comment
    
    def post_comment(self, comment_body: str) -> bool:
        """GitHub PRにコメント投稿"""
        url = f"https://api.github.com/repos/{self.repository}/issues/{self.pr_number}/comments"
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {"body": comment_body}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            print(f"✅ PRコメント投稿成功: {response.json()['html_url']}")
            return True
            
        except requests.RequestException as e:
            print(f"❌ PRコメント投稿失敗: {str(e)}")
            return False
    
    def run(self, target_path: str = "libs/quality/") -> bool:
        """メイン実行"""
        print(f"🔍 Quality Pipeline PR チェック開始: {target_path}")
        
        # 品質チェック実行
        results = self.run_quality_checks(target_path)
        
        # コメント生成
        comment_body = self.generate_comment_body(results)
        
        # PR投稿
        return self.post_comment(comment_body)


def main():
    """メイン関数"""
    try:
        # 環境変数チェック用のダミー実行
        if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
            print("🧪 Dry Run モード")
            print("環境変数チェック:")
            print(f"  GITHUB_TOKEN: {'✅ 設定済み' if os.getenv('GITHUB_TOKEN') else '❌ 未設定'}")
            print(f"  GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY', '❌ 未設定')}")
            print(f"  PR_NUMBER: {os.getenv('PR_NUMBER', '❌ 未設定')}")
            return 0
        
        bot = QualityPRCommentBot()
        target_path = sys.argv[1] if len(sys.argv) > 1 else "libs/quality/"
        
        success = bot.run(target_path)
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())