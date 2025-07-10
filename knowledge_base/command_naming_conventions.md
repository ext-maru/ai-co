# 🏷️ Elders Guild コマンド命名規則

**作成日**: 2025年7月7日 16:58  
**作成者**: Claude CLI  
**カテゴリ**: naming_conventions

---

## 📋 基本的な命名パターン

### 1. **ai-** プレフィックス
すべてのElders Guildコマンドは `ai-` で始まる

### 2. **主要な略語**
- **cc**: Claude CLI
- **pm**: Project Manager
- **kb**: Knowledge Base
- **rag**: Retrieval-Augmented Generation

---

## 🔧 具体的なコマンド例と意味

### **ai-elder-cc**
- **構成**: `ai-elder` + `cc`
- **意味**: AI Elder システムと **Claude CLI** を連携
- **誤解されやすい点**: "cc"はCouncilではなくClaude CLI

### **ai-pm**
- **構成**: `ai` + `pm`
- **意味**: AI Project Manager
- **用途**: プロジェクト管理タスクの実行

### **ai-send**
- **構成**: `ai` + `send`
- **意味**: AI タスク送信
- **用途**: AIワーカーへのタスク送信

### **ai-elder-council**
- **構成**: `ai` + `elder-council`
- **意味**: AI エルダー評議会管理
- **用途**: エルダー評議会の直接操作

### **ai-incident-knights**
- **構成**: `ai` + `incident-knights`
- **意味**: AI インシデント騎士団
- **用途**: 緊急対応システムの管理

---

## 🎯 命名の原則

### 1. **明確性**
- コマンド名から機能が推測できる
- 略語は一般的なものを使用

### 2. **一貫性**
- 同じ概念には同じ略語を使用
- 階層構造を反映した命名

### 3. **簡潔性**
- 長すぎない（3単語以内）
- タイプしやすい

---

## 📊 よくある誤解

### ❌ 間違い
- `ai-elder-cc` の "cc" = "Council" または "Committee"
- `ai-pm` = "Post Mortem" または "Prime Minister"

### ✅ 正解
- `ai-elder-cc` の "cc" = "Claude CLI"
- `ai-pm` = "Project Manager"

---

## 🔮 今後の命名指針

新しいコマンドを作成する際は：
1. `ai-` プレフィックスを必ず付ける
2. 機能を表す明確な単語を選ぶ
3. 既存の略語規則に従う
4. ドキュメントに意味を明記する

---

**この規則により、Elders Guildのコマンド体系の一貫性が保たれます。**