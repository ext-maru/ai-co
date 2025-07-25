# Flask移行ノウハウ集 - Elder Tree v2大改修から学んだこと

**作成日**: 2025年7月23日  
**作成者**: クロードエルダー（Claude Elder）  

## 🎯 このドキュメントの目的

python-a2a 0.5.9への移行で遭遇した問題と解決策を体系的にまとめ、今後の同様の移行作業の参考資料とします。

## 🔍 問題パターンと解決策

### パターン1: AttributeError: 'Agent' object has no attribute 'handle'

**症状**
```python
AttributeError: 'KnowledgeSage' object has no attribute 'handle'
AttributeError: 'ElderFlow' object has no attribute 'on_message'
```

**原因**
python-a2a 0.5.9で`@self.handle()`や`@self.on_message()`デコレータが廃止された

**解決策**
```python
# ❌ 古いパターン
@self.handle("my_message")
async def handle_my_message(message):
    pass

# ✅ 新しいパターン
def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
    message_type = data.get('type', 'unknown')
    if message_type == "my_message":
        return self._handle_my_message(data)
```

### パターン2: ModuleNotFoundError: No module named 'libs'

**症状**
```python
ModuleNotFoundError: No module named 'libs'
```

**原因**
1. 古い依存関係の残存
2. Dockerコンテナ内のパス問題

**解決策**
1. 依存関係を完全に排除
2. スタンドアロンな実装に変更
3. 必要に応じて`__init__.py`を追加

### パターン3: No module named elder_tree.__main__

**症状**
```bash
/usr/local/bin/python: No module named elder_tree.__main__; 'elder_tree' is a package and cannot be directly executed
```

**原因**
`python -m elder_tree`形式での実行時に`__main__.py`が見つからない

**解決策**
```python
# __main__.pyを作成
# または直接モジュールを指定
command: ["python", "-m", "elder_tree.agents.knowledge_sage"]
```

## 🛠️ ベストプラクティス

### 1. 基底クラスの設計

```python
class ElderTreeAgent:
    """Flask-based基底エージェント"""
    
    def __init__(self, name: str, domain: str, port: int):
        self.name = name
        self.domain = domain
        self.port = port
        self.start_time = datetime.now()
        self.logger = structlog.get_logger().bind(
            agent=name,
            domain=domain
        )
    
    def create_app(self) -> Flask:
        """Flaskアプリケーション作成"""
        app = Flask(self.name)
        
        # 共通エンドポイント
        @app.route('/health')
        def health():
            return jsonify(self.get_health_status())
        
        @app.route('/metrics')
        def metrics():
            return Response(
                generate_latest(REGISTRY),
                mimetype='text/plain'
            )
        
        @app.route('/message', methods=['POST'])
        def message():
            data = request.get_json()
            result = self.handle_message(data)
            return jsonify(result)
        
        return app
    
    def handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """サブクラスでオーバーライド"""
        raise NotImplementedError
```

### 2. main関数の標準パターン

```python
def main():
    # 環境変数からポート取得
    port = int(os.getenv("SERVICE_PORT", 50051))
    
    # サービスインスタンス作成
    service = MyService(port=port)
    
    # Flaskアプリ作成
    app = service.create_app()
    
    # Consul登録（オプション）
    if os.getenv("CONSUL_HOST"):
        try:
            import consul
            # Consul登録処理
        except ImportError:
            print("Consul client not available")
        except Exception as e:
            print(f"Failed to register with Consul: {e}")
    
    # サーバー起動
    print(f"Service running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
```

### 3. Docker環境での注意点

#### Dockerfile
```dockerfile
# PYTHONPATHを明示的に設定
ENV PYTHONPATH=/app/src

# 非rootユーザーで実行
RUN useradd -m -u 1000 elderuser && chown -R elderuser:elderuser /app
USER elderuser
```

#### docker-compose.yml
```yaml
service_name:
  build: .
  container_name: service_name
  # 直接モジュールを指定
  command: ["python", "-m", "elder_tree.agents.service_name"]
  # ポートマッピングを忘れずに
  ports:
    - "50051:50051"
  environment:
    - SERVICE_PORT=50051
  depends_on:
    postgres:
      condition: service_healthy
```

### 4. デバッグ手法

#### ステップ1: 個別ログ確認
```bash
docker logs <container_name> --tail 50
```

#### ステップ2: コンテナ内確認
```bash
# ファイル構造確認
docker exec <container_name> ls -la /app/src/

# Pythonパス確認
docker exec <container_name> python -c "import sys; print(sys.path)"
```

#### ステップ3: 最小実装でテスト
```python
# 最小限のFlaskアプリでテスト
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

## 🚨 トラブルシューティング

### Q: サービスが再起動ループする
**A**: 
1. ログを確認して具体的なエラーを特定
2. ImportError → 依存関係確認
3. AttributeError → API変更確認
4. ModuleNotFoundError → パッケージ構造確認

### Q: ポートに接続できない
**A**:
1. docker-compose.ymlでポートマッピング確認
2. `docker port <container_name>`で公開ポート確認
3. ファイアウォール設定確認

### Q: Dockerイメージの変更が反映されない
**A**:
```bash
# キャッシュを使わずに再ビルド
docker-compose build --no-cache

# または強制再作成
docker-compose up -d --build --force-recreate
```

## 📋 チェックリスト

Flask移行時の確認事項：

- [ ] python-a2a依存を完全に排除したか
- [ ] 全サービスでFlaskパターンを統一したか
- [ ] `__init__.py`ファイルを適切に配置したか
- [ ] docker-compose.ymlでポートマッピングを設定したか
- [ ] 環境変数の重複がないか確認したか
- [ ] ヘルスチェックエンドポイントを実装したか
- [ ] エラーハンドリングを適切に実装したか
- [ ] ログ出力を統一したか（structlog推奨）
- [ ] 非rootユーザーで実行しているか
- [ ] depends_onで起動順序を制御したか

## 🎯 まとめ

Flask移行の成功の鍵：

1. **シンプルさを保つ** - 複雑な非同期処理より同期的な実装
2. **段階的に進める** - 最小実装から始めて徐々に機能追加
3. **ログを活用する** - エラーパターンを認識して効率化
4. **標準化する** - 全サービスで同じパターンを使用
5. **Iron Will遵守** - 妥協せず完全動作まで実装

この経験を活かし、今後の移行作業をスムーズに進めましょう。

---

**文責**: クロードエルダー（Claude Elder）  
**エルダーズギルド品質保証済み**