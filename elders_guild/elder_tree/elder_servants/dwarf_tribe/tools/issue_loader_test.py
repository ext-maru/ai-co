#!/usr/bin/env python3

import asyncio
import requests
import os

async def load_real_issues():
    """load_real_issuesを読み込み"""
    print('📋 実際のGitHub Issueローダー開始')
    print('=' * 50)
    
    # GitHub設定確認
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('GITHUB_REPO_OWNER', 'ext-maru')
    repo_name = os.getenv('GITHUB_REPO_NAME', 'ai-co')
    
    print(f'🔗 Repository: {repo_owner}/{repo_name}')
    
    if not github_token:
        print('❌ GITHUB_TOKEN環境変数が未設定')
        return None
    
    try:
        headers = {'Authorization': f'token {github_token}'}
        
        # オープンなIssueを取得
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
        params = {
            'state': 'open',
            'per_page': 10,
            'sort': 'created',
            'direction': 'desc'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f'❌ GitHub API Error: {response.status_code}')
            print(f'   Response: {response.text[:200]}')
            return None
        
        issues = response.json()
        
        print(f'📊 取得されたIssue数: {len(issues)}')
        print()
        print('📋 利用可能なIssue一覧:')
        
        suitable_issues = []
        
        for i, issue in enumerate(issues):
            # Pull Requestは除外
            if 'pull_request' in issue:
                continue
            
            issue_number = issue['number']
            title = issue['title']
            body = issue.get('body', '')
            labels = [label['name'] for label in issue.get('labels', [])]
            created_at = issue['created_at']
            
            # A2A処理に適したIssueかチェック
            is_suitable = any([

                'enhancement' in [l.lower() for l in labels],
                'feature' in [l.lower() for l in labels],
                'documentation' in [l.lower() for l in labels],
                len(body) > 50  # 十分な説明があるか
            ])
            
            status = '🎯 適合' if is_suitable else '⚠️  要確認'
            
            print(f'{i+1}. Issue #{issue_number} {status}')
            print(f'   タイトル: {title}')
            print(f'   ラベル: {labels}')
            print(f'   作成日: {created_at}')
            print(f'   本文長: {len(body)} 文字')
            print()
            
            if is_suitable:
                suitable_issues.append({
                    'number': issue_number,
                    'title': title,
                    'body': body,
                    'labels': labels,
                    'suitable_reason': '適切なラベルまたは十分な説明'
                })
        
        print(f'🎯 A2A処理に適したIssue: {len(suitable_issues)} 件')
        
        if suitable_issues:
            # 最適なIssueを選択（最新かつ最も詳細）
            best_issue = max(suitable_issues, key=lambda x: len(x['body']))
            
            print()
            print(f'🏆 推奨Issue: #{best_issue["number"]}')
            print(f'   理由: {best_issue["suitable_reason"]}')
            print(f'   詳細度: {len(best_issue["body"])} 文字')
            
            return best_issue
        else:
            print()
            print('⚠️  A2A処理に適したIssueが見つかりませんでした')
            print('   - 十分な説明があるIssueがありません')
            print('   - 適切なラベルが付いていません')
            return None
            
    except Exception as e:
        print(f'❌ Issueローダーエラー: {str(e)}')
        return None

if __name__ == "__main__":
    # 実行
    selected_issue = asyncio.run(load_real_issues())
    if selected_issue:
        print()
        print(f'📋 選択されたIssue: #{selected_issue["number"]} - {selected_issue["title"]}')
        
        # Issue情報をJSONで保存
        import json
        with open('/tmp/selected_issue.json', 'w', encoding='utf-8') as f:
            json.dump(selected_issue, f, ensure_ascii=False, indent=2)
        print(f'💾 Issue情報を保存: /tmp/selected_issue.json')
    else:
        print()
        print('❌ 処理可能なIssueが見つかりませんでした')