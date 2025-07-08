# PostgreSQL aicompanyユーザー設定

## ユーザー情報
- **ユーザー名**: aicompany
- **パスワード**: aicompany123
- **権限**: SUPERUSER, CREATEDB, CREATEROLE

## 権限詳細
aicompanyユーザーは以下の権限を持っています：

1. **スーパーユーザー権限**: PostgreSQL内のすべての操作が可能
2. **データベース作成権限**: 新しいデータベースを自由に作成可能
3. **ロール作成権限**: 新しいユーザー/ロールを作成可能
4. **elders_knowledgeデータベースの全権限**: 
   - すべてのテーブル、シーケンス、関数への完全なアクセス
   - スキーマの変更権限
   - 今後作成されるオブジェクトへの自動的な権限付与

## 接続情報
```python
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'elders_knowledge',
    'user': 'aicompany',
    'password': 'aicompany123'
}
```

## コマンドラインでの接続
```bash
# パスワード付き接続
psql -h localhost -U aicompany -d elders_knowledge

# 新しいデータベースの作成
createdb -U aicompany new_database_name

# SQLコマンドの実行
psql -U aicompany -d elders_knowledge -c "SELECT * FROM elders;"
```

## 今後の運用
aicompanyユーザーは以下の操作を自由に実行できます：

- 新しいデータベースの作成・削除
- 新しいテーブル、インデックス、ビューの作成
- 既存オブジェクトの変更・削除
- 新しいユーザー/ロールの作成・管理
- バックアップとリストア
- pgvectorを含む拡張機能の管理

## セキュリティに関する注意
- パスワードは必要に応じて変更してください
- 本番環境では、より強力なパスワードを使用することを推奨します
- 必要最小限の権限に制限することを検討してください