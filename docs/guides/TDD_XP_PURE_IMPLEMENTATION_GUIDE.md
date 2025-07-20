# TDD-XP 純粋実装ガイドライン

**エルダー評議会令第77号 - TDD軸XP開発純粋実装令**

## 🎯 絶対原則: TDD-XPの純粋性維持

### 🚫 禁止事項
- 他の開発手法との混在
- テストなしのコード作成
- テスト後回しの実装

### ✅ 必須事項
- すべてのコードはテストから始まる
- Red→Green→Refactorサイクルの厳守
- XPの12プラクティス完全準拠

## 📋 TDD-XP実装フロー

### 1. ユーザーストーリー理解
```
As a [role]
I want [feature]
So that [benefit]
```

### 2. テストリスト作成
- 正常系テスト
- 異常系テスト
- 境界値テスト
- 統合テスト

### 3. Red Phase（失敗するテスト）
```python
def test_user_can_login_with_valid_credentials():
    # Arrange
    user = User("test@example.com", "password123")
    
    # Act
    result = login(user.email, user.password)
    
    # Assert
    assert result.success is True
    assert result.user.email == "test@example.com"
```

### 4. Green Phase（最小実装）
```python
def login(email, password):
    # 最小限の実装でテストを通す
    if email == "test@example.com" and password == "password123":
        return LoginResult(success=True, user=User(email, ""))
    return LoginResult(success=False, user=None)
```

### 5. Refactor Phase（改善）
```python
def login(email, password):
    user = user_repository.find_by_email(email)
    if user and user.verify_password(password):
        return LoginResult(success=True, user=user)
    return LoginResult(success=False, user=None)
```

## 🔄 日次サイクル

### 朝のスタンドアップ（自問自答）
- 昨日完了したテスト
- 今日書くテスト
- ブロッカーの確認

### コーディングセッション
1. **テストファースト**: 必ずテストから開始
2. **ベイビーステップ**: 小さな変更を積み重ねる
3. **頻繁なコミット**: 各サイクル完了時にコミット

### 夕方の振り返り
- テストカバレッジ確認
- リファクタリング候補の洗い出し
- 明日のテストリスト準備

## 📊 品質指標

### 必須メトリクス
- **テストカバレッジ**: 95%以上
- **サイクルタイム**: 30分以内/サイクル
- **ビルド時間**: 5分以内

### 継続的改善
- 週次でメトリクスレビュー
- ボトルネック特定と改善
- チーム全体での学習共有

## 🛡️ アンチパターン回避

### ❌ やってはいけないこと
1. **テスト後書き**: 実装後にテストを追加
2. **巨大なテスト**: 1つのテストで複数の振る舞いを検証
3. **テストの無効化**: 失敗するテストをスキップ
4. **モックの乱用**: 過度なモック使用で脆弱なテスト

### ✅ 推奨プラクティス
1. **1テスト1アサーション**: 明確な意図
2. **Arrange-Act-Assert**: テスト構造の統一
3. **テストの独立性**: 他のテストに依存しない
4. **意味のある名前**: テスト名で意図を表現

## 🚀 継続的統合

### 自動化必須項目
```yaml
# .github/workflows/tdd-xp.yml
name: TDD-XP Pipeline
on: [push, pull_request]

jobs:
  test:
    steps:
      - run: pytest --cov=. --cov-report=html
      - run: pytest --tb=short --strict
      - run: ruff check .
      - run: mypy .
```

### プッシュ前チェックリスト
- [ ] すべてのテストがグリーン
- [ ] カバレッジ95%以上
- [ ] リファクタリング完了
- [ ] コミットメッセージ明確

## 📚 参考資料
- Test Driven Development: By Example (Kent Beck)
- Extreme Programming Explained (Kent Beck)
- Clean Code (Robert C. Martin)

---
**Remember: No Code Without Test! 🧪**