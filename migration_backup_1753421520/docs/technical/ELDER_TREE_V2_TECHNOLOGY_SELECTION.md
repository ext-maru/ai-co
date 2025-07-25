# Elder Tree v2 技術選定書

**エルダー評議会技術選定書 第1号**  
**作成日**: 2025年1月22日  
**作成者**: クロードエルダー（Claude Elder）  
**承認者**: グランドエルダーmaru（申請中）

## 📋 概要

本文書は、Elder Tree v2システムの開発において採用したOSS（オープンソースソフトウェア）の選定理由、比較検討結果、および技術的判断根拠を記録するものです。エルダー評議会令第300号「OSS First開発方針」に準拠しています。

## 🎯 選定基準

1. **実績**: 本番環境での採用実績
2. **保守性**: アクティブなメンテナンス状況
3. **パフォーマンス**: 処理速度・メモリ効率
4. **エコシステム**: 関連ツール・ライブラリの充実度
5. **学習曲線**: チーム習熟の容易さ

## 🏗️ コア技術スタック

### 1. Agent-to-Agentプロトコル実装

#### 選定: python-a2a (0.5.9)

**理由**:
- エージェント間通信に特化した専門ライブラリ
- MCP（Model Context Protocol）サポート
- 非同期処理に完全対応
- 軽量で拡張性が高い設計

**比較検討**:
| ライブラリ | 評価 | 不採用理由 |
|---------|-----|----------|
| 自作実装 | ❌ | OSS First方針違反、開発工数過大 |
| Pykka | ⚠️ | アクターモデルは良いが、AI特化機能不足 |
| Ray | ⚠️ | 分散処理に強いが、過剰な機能で複雑 |

### 2. Web APIフレームワーク

#### 選定: FastAPI + Uvicorn

**理由**:
- **非同期ネイティブ**: async/awaitを標準サポート
- **自動ドキュメント生成**: OpenAPI/Swagger UI自動生成
- **型安全**: Pydanticとの統合による型チェック
- **パフォーマンス**: NodeJS並みの高速処理
- **実績**: Netflix、Uber、Microsoft等で採用

**比較検討**:
| フレームワーク | 評価 | 不採用理由 |
|------------|-----|----------|
| Flask | ⚠️ | 非同期サポートが弱い、手動設定多い |
| Django | ⚠️ | フルスタック過ぎて重い、非同期は後付け |
| Tornado | ⚠️ | 低レベルすぎて開発効率悪い |
| aiohttp | ⚠️ | APIドキュメント自動生成なし |

### 3. データベース層

#### 選定: SQLModel + AsyncPG + PostgreSQL

**理由**:
- **SQLModel**: Pydanticとの完全統合、型安全なORM
- **AsyncPG**: PostgreSQL専用の高速非同期ドライバ
- **PostgreSQL**: 最も信頼性の高いRDBMS、JSON対応

**比較検討**:
| ORM/DB | 評価 | 不採用理由 |
|--------|-----|----------|
| SQLAlchemy | ⚠️ | SQLModelの基盤だが、Pydantic統合なし |
| Tortoise-ORM | ⚠️ | コミュニティが小さい |
| MongoDB | ⚠️ | スキーマレスは利点だが、一貫性に課題 |

### 4. キャッシュ・セッション管理

#### 選定: Redis

**理由**:
- 業界標準のインメモリDB
- pub/sub機能でエージェント間通信も可能
- 永続化オプションあり
- クラスタリング対応

**比較検討**:
| ツール | 評価 | 不採用理由 |
|-------|-----|----------|
| Memcached | ⚠️ | データ型が少ない、永続化なし |
| KeyDB | ⚠️ | Redis互換だが、コミュニティ小 |

### 5. 監視・ロギング

#### 選定: Prometheus + Grafana + structlog

**理由**:
- **Prometheus**: CNCF卒業プロジェクト、時系列DB標準
- **Grafana**: 豊富なダッシュボード、アラート機能
- **structlog**: 構造化ログで検索・分析が容易

**比較検討**:
| ツール | 評価 | 不採用理由 |
|-------|-----|----------|
| ELK Stack | ⚠️ | リソース消費大、セットアップ複雑 |
| Datadog | ⚠️ | 有料、ベンダーロックイン |
| 標準logging | ❌ | 構造化ログ非対応 |

### 6. テストフレームワーク

#### 選定: pytest + pytest-asyncio + pytest-cov

**理由**:
- Python標準のテストツール
- 非同期テスト完全対応
- 豊富なプラグイン
- カバレッジ測定統合

**比較検討**:
| ツール | 評価 | 不採用理由 |
|-------|-----|----------|
| unittest | ⚠️ | 冗長、非同期サポート弱い |
| nose2 | ❌ | 開発停止状態 |

## 📊 依存関係管理

### 選定: Poetry

**理由**:
- 依存関係の自動解決
- ロックファイルで再現性確保
- パッケージ公開も統合
- pyproject.toml標準準拠

## 🔒 セキュリティ考慮事項

1. **依存関係の定期更新**: Dependabotや安全性チェックツール導入予定
2. **最小権限の原則**: 各サービスは必要最小限の権限で動作
3. **監査ログ**: structlogで全APIアクセスを記録

## 🔧 FastAPIとpython-a2aの組み合わせ方法

**FastAPI**と**python-a2a（A2A Python SDK）**は、それぞれ独立した強力なWeb/AIライブラリですが、**APIエンドポイントの構築**や**A2Aプロトコルによるエージェント化**を"いいとこ取り"で組み合わせられます。

### 利用シナリオ

- **FastAPI**：高速なWeb APIやUI、他システムとのHTTP連携、認証やWebフックの実装
- **python-a2a**：GoogleのA2A（Agent-to-Agent）プロトコル準拠のAIエージェント化、標準化されたエージェント間通信やレジストリでのエージェント管理

### 典型的な組み合わせパターン

| 利用方法                                  | メリット                                                 | ポイント             |
|-------------------------------------------|----------------------------------------------------------|----------------------|
| FastAPIでWebエンドポイント＋a2a対応       | 従来のREST＋A2Aプロトコル両対応が一つのプロセスで可能    | 共存の設定          |
| FastAPIアプリからA2Aエージェントを呼ぶ    | FastAPI上のビジネスロジックから柔軟にA2Aエージェント利用 | HTTPクライアント型  |
| A2AエージェントをFastAPIアプリ化          | A2A機能をFastAPIルーティングで拡張しやすい               | Uvicornで一括起動等  |

### サンプル実装イメージ

#### 1. FastAPIでA2AエージェントのAPIも一緒に公開

```python
from fastapi import FastAPI, Request
from python_a2a import A2AServer, run_server, Message, MessageRole, TextContent
import uvicorn

# A2Aエージェント部分
class MyAgent(A2AServer):
    def handle_message(self, message):
        return Message(
            content=TextContent(text=f"Hello, {message.content.text}!"),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )

# FastAPI部分
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

# エージェント用のA2Aサーバー起動
if __name__ == "__main__":
    from threading import Thread
    agent = MyAgent()
    # A2Aエージェント（例: 5001番ポート）とFastAPI（例: 8000番ポート）を並列で起動
    Thread(target=lambda: run_server(agent, host="0.0.0.0", port=5001)).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

各機能をプロセス分離またはスレッド並列で起動します。

#### 2. FastAPIからA2Aエージェントを呼び出すクライアント連携例

```python
from fastapi import FastAPI, Request
from python_a2a import A2AClient, Message, MessageRole, TextContent

app = FastAPI()
a2a_client = A2AClient("http://localhost:5001/a2a")  # A2AエージェントのURL

@app.post("/run_a2a")
async def run_a2a(req: Request):
    data = await req.json()
    msg = Message(
        content=TextContent(text=data.get("input", "")),
        role=MessageRole.USER
    )
    result = a2a_client.send_message(msg)
    return {"a2a_response": result.content.text}
```

FastAPIのAPIエンドポイント経由でA2Aエージェントを利用する形です。

### ワンランク上の組み合わせ：ASGI対応

- **python-a2a**自体はASGI/WSGI（例：FastAPI, Starlette, Uvicorn）互換も意識しているプロジェクトがあり（例: [FastA2A](https://github.com/pydantic/fasta2a)）、**純粋なASGIアプリとしてA2Aサーバーを直接マウント**することもできます。

### Elder Tree v2での実装方針

1. **マイクロサービス分離**: 各賢者（Sage）は独立したFastAPI + python-a2aサービスとして実装
2. **統一API Gateway**: FastAPIでREST APIとA2Aプロトコルの両方を提供
3. **非同期通信**: FastAPIの非同期機能とpython-a2aの非同期サポートを最大活用
4. **監視統合**: PrometheusメトリクスでFastAPIとA2A両方のパフォーマンスを統一監視

### まとめ

- **FastAPIで通常のREST APIや認証機能＋A2AエージェントAPIも一緒に提供**
- **内部HTTPクライアントでA2Aプロトコル準拠のエージェントを柔軟に呼び出せる**
- **要件に応じてポート分離か単一アプリ統合どちらも可能**
- **公式の例やコミュニティ実装も増加中**

A2AプロトコルによるAI連携やエージェント化と、Web/業務アプリケーションとしてのFastAPIの強みを組み合わせた**拡張性・保守性の高い実装**が可能です。

## 📈 将来の拡張性

1. **マイクロサービス化**: FastAPIの軽量性により容易に分割可能
2. **スケーリング**: Redis Cluster、PostgreSQL レプリケーション対応
3. **AI/MLパイプライン**: LangChain統合により拡張可能
4. **A2A統合**: FastAPIとpython-a2aの組み合わせでエージェント間通信を強化

## ✅ 承認

本技術選定書は、OSS First開発方針に基づき、既存の実績あるOSSを最大限活用することで、開発効率の向上と品質の確保を実現します。

**申請者**: クロードエルダー  
**承認待ち**: グランドエルダーmaru

---

**関連文書**:
- [OSS First Development Policy](../policies/OSS_FIRST_DEVELOPMENT_POLICY.md)
- [エルダー評議会令第300号](../../knowledge_base/ELDER_COUNCIL_OSS_FIRST_DECREE.md)