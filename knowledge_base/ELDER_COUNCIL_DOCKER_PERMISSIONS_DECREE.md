# エルダー評議会公式令 - Docker権限管理規程

**制定日**: 2025年7月10日
**制定者**: エルダーズギルド 4賢者評議会
**承認者**: グランドエルダーmaru
**実行責任者**: クロードエルダー

## 🏛️ エルダー評議会決議事項

### 📜 **第1条 - Docker権限問題の根本原因認定**

エルダー評議会は以下を認定する：
- Docker権限エラーは**システム設計上の構造的問題**である
- 場当たり的解決は**エルダーズギルドの品質基準に反する**
- 根本解決と**永続的ルール化**が必須である

### ⚖️ **第2条 - 解決アプローチ階層**

#### 🥇 **Tier 1: 根本解決 (最優先)**
1. **権限設計の標準化**
2. **自動化スクリプトの整備**
3. **systemdサービス統合**
4. **完全ドキュメント化**

#### 🥈 **Tier 2: 即座対応 (緊急時)**
1. **sgコマンド活用**: `sg docker -c "docker command"`
2. **権限確認スクリプト実行**
3. **一時的サービス起動**

#### 🥉 **Tier 3: 場当たり的手法 (禁止)**
- ❌ 手動ポート起動のみ
- ❌ Docker無視の回避策
- ❌ 問題放置

### 🛡️ **第3条 - クロードエルダー必須義務**

クロードエルダーは以下を**絶対に遵守**すること：

1. **📋 問題発見時**:
   - 即座にエルダー評議会への報告
   - 根本原因分析の実施
   - 解決策の体系的立案

2. **🔧 解決実装時**:
   - Tier 1解決の優先実施
   - 自動化スクリプト作成
   - 完全ドキュメント化

3. **📚 ルール化時**:
   - CLAUDE.mdへの明記
   - 知識ベース更新
   - エルダー評議会承認記録

4. **🚨 忘却防止**:
   - 重要事項のTodoWrite必須
   - 評議会決定の公式記録
   - 定期的なルール見直し

### 📋 **第4条 - Docker権限管理標準手順**

#### **4.1 権限確認**
```bash
# 必須チェックリスト
groups | grep docker          # dockerグループ確認
ls -la /var/run/docker.sock  # socket権限確認
systemctl is-active docker   # デーモン状態確認
```

#### **4.2 即座解決**
```bash
# sgコマンド使用 (推奨)
sg docker -c "docker ps"
sg docker -c "docker compose up -d"
```

#### **4.3 永続解決**
```bash
# systemdサービス使用
systemctl --user enable elders-guild-projects.service
systemctl --user start elders-guild-projects.service
```

#### **4.4 自動化スクリプト**
- `/home/aicompany/ai_co/scripts/start_project_services.sh`
- `/home/aicompany/ai_co/scripts/fix_docker_permissions.sh`

### 🎯 **第5条 - 品質基準**

すべてのDocker権限解決は以下を満たすこと：

- **✅ 根本性**: 問題の構造的解決
- **✅ 永続性**: 再起動後も機能
- **✅ 自動性**: 手動介入最小化
- **✅ 文書性**: 完全ドキュメント化
- **✅ 検証性**: テスト可能な手順

### 🚀 **第6条 - 実装状況記録**

**2025年7月10日現在の実装**:
- ✅ 根本原因分析完了
- ✅ sgコマンド即座解決確立
- ✅ 自動化スクリプト作成
- ✅ systemdサービス設定
- ✅ 完全ドキュメント化
- ✅ CLAUDE.md統合予定

## 📚 **関連ドキュメント**

- [Docker権限問題解決方法](DOCKER_PERMISSIONS_SOLUTION.md)
- [プロジェクトサービス起動ガイド](../scripts/start_project_services.sh)
- [権限修復スクリプト](../scripts/fix_docker_permissions.sh)

## ⚡ **緊急時クイックリファレンス**

```bash
# 1. 権限確認
/home/aicompany/ai_co/scripts/fix_docker_permissions.sh

# 2. サービス起動
sg docker -c "cd /home/aicompany/ai_co/projects && docker compose -f docker-compose.projects.yml up -d"

# 3. 自動化実行
/home/aicompany/ai_co/scripts/start_project_services.sh
```

---

**🏛️ エルダー評議会印章**
**制定者**: 📚ナレッジ賢者 + 📋タスク賢者 + 🚨インシデント賢者 + 🔍RAG賢者
**承認**: グランドエルダーmaru 🌟
**実行**: クロードエルダー 🤖

**この令は、エルダーズギルドの永続的ルールとして効力を有する**
