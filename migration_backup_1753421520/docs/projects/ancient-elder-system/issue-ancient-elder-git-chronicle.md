# 📜 Ancient Elder Issue #4: Git年代記魔法 (Git Chronicle Magic)

## 概要
Git/GitHub Flowの遵守、コミット規約の実践、適切なブランチ戦略の使用を監査し、プロセス違反や規約無視を検出する古代魔法システムの実装

## 背景
Elders Guildには厳格なGit運用ルールがあるが、直接main pushやコミット規約無視、プッシュ忘れなどの違反が発生している。Git履歴から真実を読み取る魔法が必要。

## 実装要件

### 1. 基底クラス継承
```python
from souls.base_soul import BaseSoul, ElderType
from libs.git_guardian import GitGuardian
import git

class AncientElderGitChronicle(BaseSoul):
    """Git履歴を読み解くエンシェントエルダー"""
    
    def __init__(self):
        super().__init__(
            name="AncientElder_GitChronicle", 
            elder_type=ElderType.ANCIENT_ELDER,
            specialty="git_chronicle"
        )
        self.git_rules = {
            "branch_naming": r"^(feature|fix|docs|chore)/issue-\d+-[\w-]+$",
            "commit_format": r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}",
            "no_direct_main": True,
            "require_pr": True,
            "immediate_push": True
        }
```

### 2. Git Flow違反検出ロジック

#### 2.1 ブランチ戦略違反検出
```python
async def detect_branch_violations(self, repo_path: Path) -> BranchViolationReport:
    """ブランチ戦略違反を検出"""
    
    repo = git.Repo(repo_path)
    violations = []
    
    # 直接main push検出
    main_commits = list(repo.iter_commits('main', max_count=100))
    for commit in main_commits:
        # PRマージ以外のコミット検出
        if not self._is_merge_commit(commit):
            author = commit.author.email
            if not self._is_automated_commit(commit):
                violations.append(BranchViolation(
                    type="DIRECT_MAIN_PUSH",
                    severity="CRITICAL",
                    commit=commit.hexsha,
                    author=author,
                    message=commit.message,
                    timestamp=commit.committed_datetime
                ))
    
    # 不適切なブランチ名
    for branch in repo.branches:
        if not re.match(self.git_rules["branch_naming"], branch.name):
            if branch.name not in ['main', 'develop']:
                violations.append(BranchViolation(
                    type="INVALID_BRANCH_NAME",
                    severity="MEDIUM",
                    branch=branch.name,
                    suggestion=self._suggest_branch_name(branch.name)
                ))
    
    # 長期間マージされていないブランチ
    stale_branches = []
    for branch in repo.branches:
        if branch.name == 'main':
            continue
        
        last_commit = branch.commit
        age_days = (datetime.now(timezone.utc) - last_commit.committed_datetime).days
        
        if age_days > 14:
            stale_branches.append({
                "branch": branch.name,
                "age_days": age_days,
                "last_commit": last_commit.hexsha
            })
    
    # Feature Branchルール違反（1 Issue = 1 Branch）
    issue_branch_mapping = {}
    for branch in repo.branches:
        match = re.match(r".*issue-(\d+)-.*", branch.name)
        if match:
            issue_num = match.group(1)
            if issue_num in issue_branch_mapping:
                violations.append(BranchViolation(
                    type="MULTIPLE_BRANCHES_PER_ISSUE",
                    severity="HIGH",
                    issue=issue_num,
                    branches=[issue_branch_mapping[issue_num], branch.name]
                ))
            else:
                issue_branch_mapping[issue_num] = branch.name
    
    return BranchViolationReport(
        violations=violations,
        stale_branches=stale_branches,
        compliance_score=self._calculate_branch_compliance(violations)
    )
```

#### 2.2 コミット規約違反検出
```python
async def detect_commit_violations(self, repo_path: Path, branch: str = None) -> CommitViolationReport:
    """コミット規約違反を検出"""
    
    repo = git.Repo(repo_path)
    commits = list(repo.iter_commits(branch or 'HEAD', max_count=500))
    violations = []
    
    for commit in commits:
        # Conventional Commits形式チェック
        if not re.match(self.git_rules["commit_format"], commit.message):
            violations.append(CommitViolation(
                type="INVALID_COMMIT_FORMAT",
                severity="MEDIUM",
                commit=commit.hexsha,
                message=commit.message,
                suggestion=self._suggest_commit_format(commit.message)
            ))
        
        # コミットメッセージの品質チェック
        quality_issues = self._analyze_commit_message_quality(commit.message)
        if quality_issues:
            violations.append(CommitViolation(
                type="LOW_QUALITY_MESSAGE",
                severity="LOW",
                commit=commit.hexsha,
                issues=quality_issues
            ))
        
        # WIP/仮コミットの検出
        if self._is_wip_commit(commit.message):
            violations.append(CommitViolation(
                type="WIP_COMMIT",
                severity="HIGH",
                commit=commit.hexsha,
                message=commit.message,
                suggestion="Complete the work before committing"
            ))
        
        # 空コミットまたは無意味なコミット
        if not commit.stats.total['lines'] and not self._is_merge_commit(commit):
            violations.append(CommitViolation(
                type="EMPTY_COMMIT",
                severity="MEDIUM",
                commit=commit.hexsha
            ))
    
    # Elder Flow自動適用の検証
    elder_flow_commits = [c for c in commits if "Elder Flow" in c.message]
    for ef_commit in elder_flow_commits:
        # Elder Flowが必要なキーワードが含まれているか確認
        if not self._requires_elder_flow(ef_commit.message):
            violations.append(CommitViolation(
                type="UNNECESSARY_ELDER_FLOW",
                severity="LOW",
                commit=ef_commit.hexsha,
                reason="Elder Flow applied to non-qualifying commit"
            ))
    
    return CommitViolationReport(
        total_commits=len(commits),
        violations=violations,
        compliance_rate=self._calculate_commit_compliance(commits, violations)
    )
```

#### 2.3 プッシュ忘れ検出
```python
async def detect_push_delays(self, repo_path: Path) -> PushDelayReport:
    """コミット後のプッシュ遅延を検出"""
    
    repo = git.Repo(repo_path)
    push_delays = []
    
    # ローカルとリモートの差分確認
    for branch in repo.branches:
        if branch.tracking_branch():
            local_commits = list(repo.iter_commits(branch))
            remote_commits = list(repo.iter_commits(branch.tracking_branch()))
            
            # ローカルのみに存在するコミット
            unpushed = set(c.hexsha for c in local_commits) - set(c.hexsha for c in remote_commits)
            
            for commit_sha in unpushed:
                commit = repo.commit(commit_sha)
                delay = datetime.now(timezone.utc) - commit.committed_datetime
                
                if delay.total_seconds() > 3600:  # 1時間以上
                    push_delays.append(PushDelay(
                        branch=branch.name,
                        commit=commit_sha,
                        message=commit.message[:50],
                        delay_hours=delay.total_seconds() / 3600,
                        severity=self._calculate_delay_severity(delay)
                    ))
    
    # リモートブランチの状態確認
    remote_status = await self._check_remote_status(repo)
    
    return PushDelayReport(
        unpushed_commits=push_delays,
        at_risk_branches=[d.branch for d in push_delays if d.severity == "HIGH"],
        total_delay_hours=sum(d.delay_hours for d in push_delays),
        recommendations=self._generate_push_recommendations(push_delays)
    )
```

#### 2.4 PR/Issue連携検証
```python
async def verify_pr_issue_linkage(self, repo_path: Path, github_token: str) -> PRIssueLinkageReport:
    """PR/Issue連携の適切性を検証"""
    
    from github import Github
    g = Github(github_token)
    repo_name = self._get_repo_name(repo_path)
    gh_repo = g.get_repo(repo_name)
    
    violations = []
    
    # 最近のPRを確認
    recent_prs = gh_repo.get_pulls(state='all')[:50]
    
    for pr in recent_prs:
        # Issue番号の抽出
        issue_refs = self._extract_issue_references(pr.body)
        
        if not issue_refs:
            violations.append(PRViolation(
                type="NO_ISSUE_REFERENCE",
                severity="HIGH",
                pr_number=pr.number,
                pr_title=pr.title
            ))
        
        # "Closes #XX" パターンの確認
        if not self._has_closes_pattern(pr.body):
            violations.append(PRViolation(
                type="MISSING_CLOSES_KEYWORD",
                severity="MEDIUM",
                pr_number=pr.number,
                suggestion=f"Add 'Closes #{issue_refs[0]}' to PR body"
            ))
        
        # ブランチ名とIssue番号の一致確認
        branch_issue = self._extract_issue_from_branch(pr.head.ref)
        if branch_issue and issue_refs and str(branch_issue) not in issue_refs:
            violations.append(PRViolation(
                type="BRANCH_ISSUE_MISMATCH",
                severity="HIGH",
                pr_number=pr.number,
                branch_issue=branch_issue,
                pr_issues=issue_refs
            ))
    
    return PRIssueLinkageReport(
        total_prs=len(recent_prs),
        violations=violations,
        compliance_score=self._calculate_pr_compliance(violations, len(recent_prs))
    )
```

### 3. 監査実行フロー
```python
async def execute_audit(self, audit_request: GitAuditRequest) -> GitAuditResult:
    """Git運用監査を実行"""
    
    # Phase 1: ブランチ戦略監査
    branch_report = await self.detect_branch_violations(audit_request.repo_path)
    
    # Phase 2: コミット規約監査
    commit_report = await self.detect_commit_violations(
        audit_request.repo_path,
        audit_request.target_branch
    )
    
    # Phase 3: プッシュ遅延監査
    push_report = await self.detect_push_delays(audit_request.repo_path)
    
    # Phase 4: PR/Issue連携監査
    pr_report = None
    if audit_request.github_token:
        pr_report = await self.verify_pr_issue_linkage(
            audit_request.repo_path,
            audit_request.github_token
        )
    
    # Phase 5: 総合スコア計算
    overall_score = self._calculate_git_compliance_score(
        branch_report,
        commit_report,
        push_report,
        pr_report
    )
    
    # Phase 6: 違反への自動対応
    all_violations = self._collect_all_violations(
        branch_report, commit_report, push_report, pr_report
    )
    
    critical_violations = [v for v in all_violations if v.severity == "CRITICAL"]
    if critical_violations:
        # 緊急対応
        await self._block_deployments()
        await self._notify_grand_elder(critical_violations)
        
        # 自動修正
        for violation in critical_violations:
            if violation.type == "DIRECT_MAIN_PUSH":
                await self._revert_direct_push(violation)
            elif violation.type == "UNPUSHED_COMMITS":
                await self._force_push_reminder(violation)
    
    # Phase 7: 改善アクション生成
    improvements = self._generate_git_improvements(all_violations)
    
    return GitAuditResult(
        audit_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        overall_score=overall_score,
        branch_compliance=branch_report,
        commit_compliance=commit_report,
        push_timeliness=push_report,
        pr_linkage=pr_report,
        critical_violations=critical_violations,
        improvements=improvements,
        enforcement_actions=self._get_enforcement_actions()
    )
```

### 4. Git違反パターン定義
```python
class GitViolationPatterns:
    """Git運用違反パターン"""
    
    # ブランチ違反
    BRANCH_VIOLATIONS = {
        "direct_main": "commits directly to main branch",
        "wrong_naming": "branch name doesn't follow convention",
        "no_issue_branch": "feature without issue reference",
        "abandoned_branch": "branch inactive for >30 days",
    }
    
    # コミット違反
    COMMIT_VIOLATIONS = {
        "wip_patterns": ["WIP", "仮", "一旦", "TODO", "TEMP"],
        "meaningless": ["update", "fix", "change", "commit"],
        "too_large": "commit changes >1000 lines",
        "mixed_concerns": "commit mixes multiple features",
    }
    
    # プロセス違反
    PROCESS_VIOLATIONS = {
        "no_pr": "merge without pull request",
        "force_push": "force push to shared branch",
        "skip_review": "self-approved pull request",
        "late_push": "commits not pushed within 1 hour",
    }
```

### 5. Git運用改善アクション
```python
async def enforce_git_discipline(self, violations: List[GitViolation]) -> None:
    """Git規律を強制する自動アクション"""
    
    # Pre-commitフックの自動設定
    await self._install_precommit_hooks(
        check_branch_name=True,
        check_commit_message=True,
        run_tests=True
    )
    
    # Git aliasの自動設定
    await self._setup_git_aliases({
        "ci": "elder-commit",  # Elder Flow自動適用
        "feature": "git-feature",  # 適切なブランチ作成
        "push-safe": "git push --no-force"
    })
    
    # 定期リマインダー設定
    await self._schedule_git_reminders(
        push_reminder_minutes=30,
        pr_reminder_hours=4,
        branch_cleanup_days=14
    )
    
    # 違反者への教育
    for violation in violations:
        if violation.severity in ["CRITICAL", "HIGH"]:
            await self._require_git_training(violation.author)
```

## 実装優先度: HIGH

## 関連ファイル
- `.git/` - Gitリポジトリ
- `scripts/git-feature` - ブランチ作成ツール
- `.github/` - GitHub設定
- `ELDERFLOW_USAGE.md` - Elder Flow使用ガイド

## テスト要件
- 各種Git違反パターンの検出テスト
- 誤検出防止テスト（正当な操作を違反と判定しない）
- GitHub API連携テスト
- 自動修正アクションのテスト

## 成功基準
- Git Flow違反の100%検出
- コミット規約違反の95%以上検出
- プッシュ忘れの90%以上検出
- 違反率を50%削減