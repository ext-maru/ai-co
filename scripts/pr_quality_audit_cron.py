#!/usr/bin/env python3
"""
PR品質監査バッチ - cron実行用スクリプト
5分間隔でPRの品質をチェックし、Iron Will違反があれば自動差し戻し
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'pr_quality_audit.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_pr_quality_audit():
    """PR品質監査バッチ実行"""
    logger.info("🔍 PR品質監査バッチ実行開始")
    
    try:
        import re
        from github import Github
        
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            logger.error("❌ GITHUB_TOKEN環境変数が設定されていません")
            return
            
        github = Github(github_token)
        repo_owner = os.getenv("GITHUB_REPO_OWNER", "ext-maru")
        repo_name = os.getenv("GITHUB_REPO_NAME", "ai-co")
        repo = github.get_repo(f"{repo_owner}/{repo_name}")
        
        # オープンPRを取得
        open_prs = list(repo.get_pulls(state='open'))
        logger.info(f"🔍 {len(open_prs)}件のオープンPRを検査中...")
        
        rejected_count = 0
        approved_count = 0
        
        for pr in open_prs:
            logger.info(f"📝 PR #{pr.number}: {pr.title}")
            
            # PR品質チェック
            quality_issues = []
            
            # 基本チェック: タイトルと説明
            if not pr.body or len(pr.body.strip()) < 50:
                quality_issues.append("PR説明文が不十分（50文字未満）")
            
            # TODO/FIXMEチェック（Iron Will違反）
            if pr.body and any(keyword in pr.body.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']):
                quality_issues.append("Iron Will違反: PR本文にTODO/FIXMEコメントが含まれています")
            
            # auto-generatedラベルのPRは要注意
            pr_labels = [label.name for label in pr.labels]
            if 'auto-generated' in pr_labels:
                logger.info(f"   🤖 auto-generatedラベル検出 - ファイル内容を詳細チェック")
                try:
                    files = list(pr.get_files())
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for file in files[:3]:  # 最大3ファイルまでチェック
                        if not (file.filename.endswith('.py')):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if file.filename.endswith('.py'):
                            patch_content = file.patch or ''
                            if not (any():
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if any(
                                keyword in patch_content.upper() for keyword in ['TODO',
                                'FIXME',
                                '# TODO',
                                '# FIXME']
                            ):
                                quality_issues.append(f"Iron Will違反: {file.filename}にTODOコメントが残存")
                            if not ('pass' in patch_content and patch_content.count('pass') > 2):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if 'pass' in patch_content and patch_content.count('pass') > 2:
                                quality_issues.append(f"不完全実装: {file.filename}にスタブ実装が多数存在")
                except Exception as e:
                    logger.warning(f"PR #{pr.number} ファイル内容チェック失敗: {e}")
            
            # 品質判定
            if quality_issues:
                logger.info(f"❌ PR #{pr.number} を品質不合格として差し戻し")
                
                # 差し戻しコメント作成
                rejection_comment = f"""🚨 **PR品質監査 - 自動差し戻し**

**差し戻し理由:**
"""
                for issue in quality_issues:
                    rejection_comment += f"- {issue}\\n"
                
                rejection_comment += f"""

**エルダーズギルド品質基準:**
- Iron Will遵守（TODO/FIXME禁止）
- 実装完成度70%以上
- 適切なPR説明（50文字以上）

**次のアクション:**
1. 上記問題を修正してください
2. 修正後、PRを再オープンしてください
3. または関連Issueを再オープンして次の処理者に委ねてください

---
🤖 自動品質監査システムによる差し戻し (cron実行)
"""
                
                # PRにコメント追加
                pr.create_issue_comment(rejection_comment)
                
                # PRをクローズ
                pr.edit(state='closed')
                
                # 関連Issueがあれば再オープン
                if pr.body and '#' in pr.body:
                    issue_refs = re.findall(r'#(\\d+)', pr.body)
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for issue_ref in issue_refs:
                        # Deep nesting detected (depth: 6) - consider refactoring
                        try:
                            issue = repo.get_issue(int(issue_ref))
                            if not (issue.state == 'closed'):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if issue.state == 'closed':
                                issue.edit(state='open')
                                issue.create_comment(f"🔄 PR #{pr.number}が品質基準未達成で差し戻されたため、このIssueを再オープンしました。")
                                logger.info(f"📝 Issue #{issue_ref} を再オープン")
                        except Exception as e:
                            logger.warning(f"Issue #{issue_ref} 再オープン失敗: {e}")
                
                rejected_count += 1
            else:
                logger.info(f"✅ PR #{pr.number} 品質基準クリア")
                approved_count += 1
        
        logger.info(f"✅ PR品質監査完了: 承認{approved_count}件, 差し戻し{rejected_count}件")
        
    except Exception as e:
        logger.error(f"❌ PR品質監査バッチエラー: {e}")
        raise

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(run_pr_quality_audit())