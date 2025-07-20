# 🤖 Auto Issue Processor A2A実装ガイド

## 📋 概要

Auto Issue Processorは、GitHub Issueを自動的に処理してPull Requestを作成するシステムです。**常にA2A（Agent to Agent）モードで動作し**、各Issueを独立したプロセスで処理することで、コンテキストの蓄積とPIDロックの問題を完全に解決します。

## 🔍 解決する問題

### 従来の問題点
1. **コンテキスト爆発**: 複数Issueを同一Claude Codeセッションで処理するとコンテキストが肥大化
2. **PIDロック競合**: Elder FlowのPIDロック機能により、同一プロセス内での複数タスク実行が制限
3. **メモリ使用量**: 長時間の処理でメモリが解放されない

### A2A実装による解決
1. **独立プロセス**: 各Issueが独立したClaude CLIプロセスで実行
2. **並列処理**: 複数のIssueを同時に処理可能
3. **リソース管理**: 各プロセス終了時にメモリが自動解放

## 🏗️ アーキテクチャ

### システム構成
```
[Auto Issue Processor]
    ├── [Issue Scanner] - GitHub APIでIssueを取得
    ├── [Complexity Evaluator] - Issue複雑度を評価
    └── [A2A Processor] - 並列プロセス管理
         ├── [Claude CLI Process 1] - Issue #1処理
         ├── [Claude CLI Process 2] - Issue #2処理
         └── [Claude CLI Process N] - Issue #N処理
```

### 処理フロー
```python
1. GitHub Issueの取得
2. 複雑度評価（処理可能なIssueのフィルタリング）
3. A2Aモード判定
   - 有効: process_issues_a2a()で並列処理
   - 無効: 従来の順次処理
4. 各Issueを独立プロセスで処理
5. 結果の集約とレポート
```

## 🔧 実装詳細

### 1. A2A並列度の設定
```python
# 環境変数で並列度を設定（デフォルト: 5）
export AUTO_ISSUE_A2A_MAX_PARALLEL=10

# Auto Issue Processorは常にA2Aモードで起動
processor = AutoIssueProcessor()
# a2a_max_parallel は環境変数から自動設定
```

### 2. 独立プロセス実行
```python
async def process_issue_isolated(self, issue: Issue) -> Dict[str, Any]:
    """独立したClaude CLIプロセスでIssueを処理"""
    
    # Claude CLI用プロンプト作成
    prompt = f"""
    あなたはクロードエルダー（Claude Elder）です。
    Issue #{issue.number}: {issue.title}を処理してください。
    Elder Flowを使用してTDDで実装し、PRを作成してください。
    """
    
    # 独立プロセスで実行
    executor = ClaudeCLIExecutor()
    result = executor.execute(
        prompt=prompt,
        model="claude-sonnet-4-20250514",
        working_dir=str(Path.cwd())
    )
    
    return parse_result(result)
```

### 3. 並列処理管理
```python
async def process_issues_a2a(self, issues: List[Issue]) -> List[Dict]:
    """複数Issueの並列処理"""
    
    # セマフォで並列度を制限
    semaphore = asyncio.Semaphore(self.a2a_max_parallel)
    
    async def process_with_limit(issue):
        async with semaphore:
            return await self.process_issue_isolated(issue)
    
    # 全タスクを並列実行
    tasks = [
        asyncio.create_task(process_with_limit(issue))
        for issue in issues
    ]
    
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## 📊 パフォーマンス比較

### 順次処理（従来）
```
Issue #1 (3分) → Issue #2 (2分) → Issue #3 (4分) = 合計9分
コンテキスト: 累積的に増加
メモリ: 解放されない
```

### A2A並列処理
```
Issue #1 (3分) ┐
Issue #2 (2分) ├→ 合計4分（最長タスク時間）
Issue #3 (4分) ┘
コンテキスト: 各プロセスで独立
メモリ: プロセス終了時に解放
```

## 🔒 PIDロック対応

### 問題の回避
- 各Issueは異なるプロセスで実行されるため、PIDロック競合なし
- Elder Flowの品質保証機能をフル活用可能

### タスク名の一意性
```python
task_name = f"Auto-fix Issue #{issue.number}: {issue.title}"
# Issue番号により一意性を保証
```

## 📝 使用方法

### CLIから実行
```bash
# 通常実行（デフォルトでA2A）
python3 libs/integrations/github/auto_issue_processor.py

# 並列度を指定して実行
AUTO_ISSUE_A2A_MAX_PARALLEL=10 python3 libs/integrations/github/auto_issue_processor.py
```

### プログラムから実行
```python
# Auto Issue Processorは常にA2Aモードで動作
processor = AutoIssueProcessor()

# 自動処理開始
result = await processor.process_request({
    "type": "scan_and_process",
    "mode": "auto"
})
```

## 🧪 テスト

### テスト実行
```bash
python3 -m pytest tests/unit/test_auto_issue_processor_a2a.py -v
```

### テストカバレッジ
- 独立プロセス実行
- 並列処理
- A2Aモード切り替え
- エラーハンドリング
- 並列度制限

## ⚙️ 設定オプション

| 環境変数 | デフォルト | 説明 |
|---------|-----------|------|
| AUTO_ISSUE_A2A_MAX_PARALLEL | 5 | 最大並列実行数 |
| GITHUB_TOKEN | - | GitHub APIトークン |
| GITHUB_REPO_OWNER | ext-maru | リポジトリオーナー |
| GITHUB_REPO_NAME | ai-co | リポジトリ名 |

## 🚨 注意事項

1. **リソース使用**: 並列度を高くしすぎるとシステムリソースを圧迫
2. **API制限**: GitHub APIのレート制限に注意
3. **Claude CLI**: 各プロセスがClaude CLIを起動するため、適切なライセンスが必要

## 🔮 今後の拡張

1. **動的並列度調整**: システム負荷に応じた自動調整
2. **優先度キュー**: Issue優先度による処理順序の最適化
3. **分散処理**: 複数マシンでの処理分散

---
最終更新: 2025-01-20
作成者: Claude Elder