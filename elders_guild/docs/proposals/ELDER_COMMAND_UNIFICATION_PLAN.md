# 🏛️ Elder Command 統一計画

**提案日**: 2025年7月24日  
**提案者**: Grand Elder maru  
**実装者**: Claude Elder  
**目的**: `ai-*` コマンドを `elder` に統一

---

## 🎯 統一の理念

**現状**: `ai-send`, `ai-test`, `ai-elder-flow` など分散したコマンド体系  
**目標**: `elder` コマンドに統一し、サブコマンドで整理

```bash
# Before
ai-send "メッセージ"
ai-elder-flow execute "タスク"
ai-test run

# After  
elder send "メッセージ"
elder flow execute "タスク"
elder test run
```

---

## 🏗️ 新コマンド体系

### **基本構造**
```
elder [カテゴリ] [アクション] [オプション]
```

### **カテゴリ分類**

#### **1. 基本操作**
```bash
elder send "メッセージ"           # ai-send
elder status                      # ai-status
elder start                       # ai-start
elder stop                        # ai-stop
elder help                        # ai-help
```

#### **2. 開発系**
```bash
elder test run                    # ai-test
elder test coverage              
elder code review                 # ai-code
elder commit auto                 # ai-commit-auto
elder commit lightning           # ai-commit-lightning
```

#### **3. Elder Flow系**
```bash
elder flow execute "タスク"        # ai-elder-flow
elder flow status
elder flow fix                    # ai-elder-flow-fix
elder flow knights               # ai-elder-flow-knights-fix
```

#### **4. 賢者系**
```bash
elder sage knowledge query        # ナレッジ賢者
elder sage task status           # タスク賢者
elder sage incident report       # インシデント賢者
elder sage rag search           # RAG賢者
```

#### **5. 評議会系**
```bash
elder council consult            # ai-elder-council
elder council compliance         # ai-elder-compliance
elder council proactive          # ai-elder-proactive
```

#### **6. 管理系**
```bash
elder worker add                 # ai-worker-add
elder worker scale              # ai-worker-scale
elder config edit               # ai-config
elder monitor                   # ai-monitor
```

#### **7. 特殊機能**
```bash
elder magic ancient             # ai-ancient-magic
elder prophecy show             # ai-prophecy
elder nwo vision                # ai-nwo-vision
```

---

## 📝 移行戦略

### **Phase 1: エイリアス期間（1ヶ月）**
```bash
# 両方のコマンドが使える
ai-send "hello"     # 動作する（非推奨警告）
elder send "hello"  # 新コマンド（推奨）
```

### **Phase 2: 段階的廃止（2-3ヶ月）**
```bash
# ai-* コマンドは警告強化
$ ai-send "hello"
⚠️ 'ai-send' は非推奨です。'elder send' を使用してください。
（まだ動作する）
```

### **Phase 3: 完全移行（3ヶ月後）**
```bash
# ai-* コマンドは削除
$ ai-send "hello"
エラー: コマンドが見つかりません。'elder send' を使用してください。
```

---

## 🔧 実装方法

### **1. Elder CLI フレームワーク**
```python
# elder_cli.py
import click

@click.group()
def elder():
    """エルダーズギルド統一コマンドシステム"""
    pass

# サブコマンドグループ
@elder.group()
def flow():
    """Elder Flow 管理"""
    pass

@elder.group()
def sage():
    """4賢者システム"""
    pass

@elder.group()
def council():
    """エルダー評議会"""
    pass

# 基本コマンド
@elder.command()
@click.argument('message')
def send(message):
    """メッセージ送信"""
    from commands.ai_send import AISendCommand
    cmd = AISendCommand()
    cmd.execute(message)

# Elder Flow
@flow.command()
@click.argument('task')
@click.option('--priority', default='medium')
def execute(task, priority):
    """Elder Flow 実行"""
    from libs.elder_flow import execute_elder_flow
    execute_elder_flow(task, priority)
```

### **2. 自動移行スクリプト**
```bash
#!/bin/bash
# migrate-to-elder-commands.sh

# 既存コマンドのエイリアス作成
for cmd in /usr/local/bin/ai-*; do
    basename=$(basename "$cmd")
    elder_name=${basename/ai-/elder }
    
    # エイリアス作成
    cat > "/usr/local/bin/$basename.new" << EOF
#!/bin/bash
echo "⚠️ '$basename' は非推奨です。'$elder_name' を使用してください。" >&2
exec $elder_name "\$@"
EOF
    chmod +x "/usr/local/bin/$basename.new"
done
```

### **3. 設定ファイル**
```yaml
# .elder/config.yml
command_style: unified  # unified or legacy

aliases:
  enabled: true
  deprecation_warnings: true
  
categories:
  - name: flow
    description: "Elder Flow 管理"
  - name: sage
    description: "4賢者システム"
  - name: council
    description: "エルダー評議会"
```

---

## 📊 メリット

### **1. 統一性**
- 一貫したコマンド体系
- 学習コストの削減
- 予測可能なインターフェース

### **2. 階層的整理**
```bash
elder sage knowledge query "エラー解決方法"
#     ^^^^ ^^^^^^^^^ ^^^^^
#     カテゴリ サブカテゴリ アクション
```

### **3. 拡張性**
- 新機能追加が容易
- プラグインシステム対応
- バージョン管理簡素化

### **4. ブランディング**
- "Elder" ブランドの確立
- エルダーズギルドのアイデンティティ強化

---

## 🚀 実装ステップ

### **Week 1: 基盤構築**
- [ ] elder_cli.py フレームワーク作成
- [ ] 基本コマンド（send, status, start, stop）実装
- [ ] テスト環境構築

### **Week 2: カテゴリ実装**
- [ ] flow カテゴリ
- [ ] sage カテゴリ
- [ ] council カテゴリ

### **Week 3: 移行ツール**
- [ ] エイリアス自動生成
- [ ] ドキュメント更新
- [ ] 移行ガイド作成

### **Week 4: テスト・調整**
- [ ] 統合テスト
- [ ] パフォーマンス確認
- [ ] ユーザーフィードバック

---

## 💡 使用例

### **日常的な使用**
```bash
# メッセージ送信
elder send "OAuth実装して"

# Elder Flow
elder flow execute "新機能実装" --priority high

# 4賢者相談
elder sage incident analyze error.log
elder sage knowledge search "ベストプラクティス"

# ステータス確認
elder status --detailed
```

### **高度な使用**
```bash
# パイプライン実行
elder flow pipeline quality-check | elder sage judge

# 一括操作
elder worker scale up 5
elder council approve PR-123
```

---

## 📚 ドキュメント更新

1. **README.md** - インストール手順更新
2. **CLAUDE.md** - コマンド一覧更新
3. **ユーザーガイド** - 新コマンド体系説明
4. **移行ガイド** - 既存ユーザー向け

---

## 🎯 成功基準

- [ ] すべての ai-* コマンドが elder に移行
- [ ] ドキュメント100%更新
- [ ] ユーザーからの移行完了率 90%以上
- [ ] エラー率 1%未満

---

**「統一されたコマンドが、統一された思想を生む」**  
*- Elder Command Unification Principle -*