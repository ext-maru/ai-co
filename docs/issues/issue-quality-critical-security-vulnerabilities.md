# 🚨 Critical: 品質システム セキュリティ脆弱性修正

**Issue Type**: 🔴 Critical Security Vulnerability  
**Priority**: P0 - 即座修正必須  
**Assignee**: Claude Elder  
**Labels**: `security`, `critical`, `quality-system`, `vulnerability`  
**Estimated**: 4 hours  

## 🎯 **問題概要**

Elder Guild品質システムに重大なセキュリティ脆弱性が発見されました。現在の実装では外部入力検証が不十分で、コードインジェクション攻撃の可能性があります。

## 🔍 **脆弱性詳細**

### **1. コードインジェクション脆弱性**
**場所**: `scripts/git-hooks/pre-merge-commit:572-620`

```bash
# 危険な実装
python3 -c "
import asyncio
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from libs.four_sages_quality_bridge import four_sages_analyze_file

async def main():
    try:
        result = await four_sages_analyze_file('$file')  # ← 外部入力未検証
        # ...
```

**リスク**: ファイル名にシェルコマンドが含まれている場合、任意コード実行可能

### **2. 環境変数インジェクション**
**場所**: `scripts/setup-merge-quality-integration:138-164`

```bash
# 検証不十分
PROJECT_ROOT=\"/home/aicompany/ai_co\"
cd \"$PROJECT_ROOT\"  # ← パストラバーサル可能
```

### **3. 一時ファイル競合状態**
**場所**: 複数の品質チェックスクリプト

```bash
# 安全でない一時ファイル
MERGE_REPORT_FILE="$PROJECT_ROOT/data/merge_quality_report_$(date +%Y%m%d_%H%M%S).json"
# ← 同時実行時の競合状態、権限エスカレーション可能
```

## ✅ **修正要件**

### **Priority 1: 即座修正必須**

1. **入力検証の完全実装**
```bash
# 修正例
validate_file_path() {
    local file="$1"
    # パストラバーサル防止
    if [[ "$file" =~ \.\./|^/|^\~ ]]; then
        print_error "Invalid file path: $file"
        return 1
    fi
    # 危険文字の除去
    file=$(echo "$file" | tr -d ';|&$`<>(){}[]')
    echo "$file"
}
```

2. **安全なPython実行**
```bash
# 修正例
execute_safe_python() {
    local script="$1"
    local file="$2"
    
    # 入力検証
    file=$(validate_file_path "$file")
    
    # 安全な実行
    python3 << 'EOF'
import sys
import subprocess
import shlex

# エスケープ処理
safe_file = shlex.quote(sys.argv[1])
script_content = f"""
import asyncio
import sys
sys.path.insert(0, '/home/aicompany/ai_co')
from libs.four_sages_quality_bridge import four_sages_analyze_file

async def main():
    try:
        result = await four_sages_analyze_file({safe_file})
        print(f'SCORE:{{result["analysis"].get("quality_score", 0)}}')
    except Exception as e:
        print(f'ERROR:{{str(e)}}')
        print('SCORE:70')

asyncio.run(main())
"""

# タイムアウト付き実行
result = subprocess.run(
    [sys.executable, '-c', script_content], 
    capture_output=True, 
    timeout=30,
    text=True
)
print(result.stdout)
EOF
}
```

3. **安全な一時ファイル管理**
```bash
# 修正例
create_secure_temp_file() {
    local prefix="$1"
    local temp_dir="/tmp/elder_guild_secure"
    
    # セキュアな一時ディレクトリ作成
    mkdir -p "$temp_dir"
    chmod 700 "$temp_dir"
    
    # 安全な一時ファイル
    mktemp "$temp_dir/${prefix}_XXXXXXXX.json"
}
```

4. **権限最小化**
```bash
# 修正例
# 専用ユーザーでの実行
if [[ $(id -u) -eq 0 ]]; then
    print_error "品質チェックはrootで実行してはいけません"
    exit 1
fi

# ファイル権限の制限
umask 077
```

### **Priority 2: セキュリティ強化**

5. **ログ出力の安全化**
```bash
# 機密情報のログ出力防止
sanitize_log_output() {
    sed -e 's/password=[^[:space:]]*/password=****/g' \
        -e 's/token=[^[:space:]]*/token=****/g' \
        -e 's/key=[^[:space:]]*/key=****/g'
}
```

6. **セキュリティヘッダーの追加**
```bash
# すべてのスクリプトにセキュリティヘッダー
set -euo pipefail
IFS=$'\n\t'
export PATH="/usr/local/bin:/usr/bin:/bin"
```

## 🧪 **テスト要件**

### **セキュリティテストケース**
```bash
# テスト1: パストラバーサル攻撃
test_path_traversal_protection() {
    local malicious_file="../../../etc/passwd"
    result=$(validate_file_path "$malicious_file")
    [[ $? -eq 1 ]] || fail "Path traversal not blocked"
}

# テスト2: コマンドインジェクション
test_command_injection_protection() {
    local malicious_file="test.py; rm -rf /"
    result=$(validate_file_path "$malicious_file")
    [[ "$result" == "test.py rmrf" ]] || fail "Command injection not sanitized"
}

# テスト3: 権限エスカレーション
test_privilege_escalation_prevention() {
    [[ $(id -u) -ne 0 ]] || fail "Running as root not prevented"
}
```

## 📊 **成功基準**

- [ ] すべての外部入力が適切に検証・エスケープされている
- [ ] パストラバーサル攻撃が防止されている
- [ ] コマンドインジェクション攻撃が防止されている
- [ ] 一時ファイルの競合状態が解決されている
- [ ] 権限最小化が実装されている
- [ ] セキュリティテストが全て合格
- [ ] 脆弱性スキャンツールでの検証合格

## 🎯 **受け入れ基準**

1. **セキュリティ監査合格**: 外部セキュリティツールでの検証
2. **侵入テスト合格**: 実際の攻撃シナリオでの検証
3. **コードレビュー合格**: セキュリティ専門家による査読
4. **自動テスト合格**: CI/CDでのセキュリティテスト自動実行

## ⚡ **実装計画**

### **Phase 1: 緊急修正 (2時間)**
- [ ] 入力検証の実装
- [ ] 安全なPython実行の実装
- [ ] 基本的なセキュリティヘッダー追加

### **Phase 2: セキュリティ強化 (1時間)**
- [ ] 安全な一時ファイル管理
- [ ] 権限最小化の実装
- [ ] ログ出力の安全化

### **Phase 3: テスト・検証 (1時間)**
- [ ] セキュリティテストの実装
- [ ] 脆弱性スキャンの実行
- [ ] ドキュメント更新

## 🏛️ **Elder Guild 承認要件**

この修正は**Elder Council 緊急承認**が必要です。

**承認者**: グランドエルダーmaru  
**レビュー要求**: 4賢者セキュリティ評議会  
**緊急度**: P0 - 24時間以内修正必須  

---

**🔒 「セキュリティは最優先事項である」- Elder Guild セキュリティ憲章**