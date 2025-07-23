# 🏛️ Micro A2A+FastAPI 実証実験

Elder Tree技術選定の実証実験：python-a2a + FastAPIの統合検証

## 📋 概要

最小限の実装でA2A（Agent-to-Agent）プロトコルとFastAPIの統合が期待通り動作するかを実証します。

## 🏗️ アーキテクチャ

```
Client (HTTP) → FastAPI (8000) → A2A Agent → Response
                      ↓
                A2A Server (5001)
```

## 📁 ファイル構成

- `micro_a2a_server.py` - A2A+FastAPI統合サーバー
- `test_client.py` - HTTPクライアントテスト
- `README.md` - このファイル

## 🚀 実行手順

### 1. サーバー起動

```bash
cd /home/aicompany/ai_co/elders_guild/proof_of_concept
source ../venv/bin/activate
python micro_a2a_server.py
```

### 2. テスト実行（別ターミナル）

```bash
cd /home/aicompany/ai_co/elders_guild/proof_of_concept
source ../venv/bin/activate
python test_client.py
```

## 📊 期待される結果

1. **サーバー起動**：FastAPI（8000）とA2A（5001）が両方起動
2. **ヘルスチェック**：`/health`エンドポイントが正常応答
3. **チャット機能**：`/chat`でA2Aエージェントとの通信成功
4. **A2A統合**：FastAPI経由でA2Aメッセージ処理が正常動作

## 🔧 技術詳細

### A2Aエージェント
- `python_a2a.A2AServer`を継承
- `handle_message()`でメッセージ処理
- Elder風のレスポンス生成

### FastAPI統合
- RESTエンドポイントからA2Aエージェント呼び出し
- 同一プロセス内でのダイレクト通信
- 並行スレッド実行

## ✅ 成功基準

- [ ] サーバーが正常起動
- [ ] ヘルスチェックが成功
- [ ] チャット機能が動作
- [ ] A2Aメッセージ処理が正常
- [ ] レスポンスが期待通りの形式

これらが全て成功すれば、Elder Tree本体への適用が可能です。