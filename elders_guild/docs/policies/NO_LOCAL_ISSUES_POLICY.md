# 🚫 Elders Guild ローカルIssue廃止ポリシー

**ポリシー番号**: EG-POLICY-002  
**制定日**: 2025年7月23日  
**制定者**: グランドエルダーmaru  
**施行者**: クロードエルダー  
**状態**: 即時発効

## 📋 概要
Elders Guildにおけるすべてのローカルファイルベースのタスク・Issue管理を廃止し、GitHub Issuesへ完全移行する。

## 🎯 目的
- **一元管理**: すべてのタスクをGitHub上で統一管理
- **透明性**: 進捗状況の可視化
- **コラボレーション**: チームメンバーとの円滑な連携
- **検索性**: GitHub標準機能による高度な検索

## ❌ 廃止対象
以下のローカルIssue管理方法を**完全廃止**：
- `docs/issues/`内の個別Issueマークダウンファイル
- TODO.mdファイル
- タスク管理用JSONファイル
- ローカルデータベースでのタスク管理
- その他あらゆるファイルベースのIssue管理

## ✅ 新しい運用ルール

### 1. Issue作成
```bash
# すべてのIssueはGitHub上で作成
gh issue create --title "タイトル" --body "内容"
```

### 2. Issue管理
- **作成**: 必ずGitHub Issues使用
- **更新**: GitHub上でコメント・ステータス更新
- **検索**: GitHub検索機能使用
- **ラベル**: 適切なラベル付与

### 3. ドキュメント連携
- 詳細仕様が必要な場合は`docs/projects/`に技術文書作成
- GitHub IssueからMarkdownファイルへのリンク

## 🔧 実装ガイドライン

### クロードエルダーの義務
1. **新規Issue**: 必ずGitHub上で作成
2. **既存Issue**: ローカルファイルを見つけたら即座にGitHub移行
3. **定期確認**: ローカルIssueファイルの存在を監視・削除

### 禁止事項
- ❌ `docs/issues/issue-XXX.md`形式のファイル作成
- ❌ TODO.mdやTASKS.mdの作成・更新
- ❌ ローカルデータベースでのタスク管理

## 📊 移行完了基準
- [ ] 既存のローカルIssueすべてGitHub移行完了
- [ ] ローカルIssueファイル完全削除
- [ ] チーム全員への周知完了
- [ ] 監視スクリプト実装

## 🚨 違反時の対応
1. **即座の是正**: ローカルIssueをGitHubへ移行
2. **ファイル削除**: ローカルIssueファイル削除
3. **記録**: 違反履歴として記録

## 📚 関連資料
- [GitHub Issues公式ドキュメント](https://docs.github.com/en/issues)
- [GitHub CLI (gh) マニュアル](https://cli.github.com/manual/)

---
**このポリシーは即時発効され、すべてのElders Guild開発において適用されます。**