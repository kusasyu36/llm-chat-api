# llm-chat-api

軽量 LLM 推論 API。**FastAPI + Docker + GitHub Actions + Prometheus 監視**を
一通り体験するための練習プロジェクト。

> 「LLM に話しかけると返事が返ってきて、その会話が記録され、サーバーの調子も
> 数字で見える」——Web サービスの基本セット一式を最小構成で実装している。

## できること

| エンドポイント | 説明 |
|---|---|
| `POST /chat` | メッセージを送ると LLM が応答し、履歴を DB に保存する |
| `GET /history?session_id=...` | そのセッションの会話履歴を新しい順に返す |
| `GET /metrics` | Prometheus 形式のメトリクス（呼び出し回数・応答時間） |
| `GET /healthz` | 死活監視用ヘルスチェック |
| `GET /docs` | 自動生成された API ドキュメント（Swagger UI） |

## アーキテクチャ（ざっくり）

```
   クライアント
        │  POST /chat {"message": "こんにちは"}
        ▼
   ┌──────────────┐     ┌─────────────┐
   │  FastAPI app │────▶│  Backend     │  echo（既定）/ hf（任意）
   │  (app/main)  │     │ (app/backends)│
   └──────┬───────┘     └─────────────┘
          │ 履歴を保存            ┌─────────────┐
          ├────────────────────▶│  SQLite/PG  │ (app/db)
          │ メトリクス記録        └─────────────┘
          ▼
   /metrics ◀── Prometheus が定期取得
```

LLM バックエンドは差し替え可能。既定の `echo` は依存なしで動く（テスト・CI 用）。
`hf` に切り替えると Hugging Face の小型モデルで実際に推論する。

## セットアップ

依存管理は [uv](https://docs.astral.sh/uv/) を使う。

```bash
# 仮想環境作成 + 依存インストール（開発用ツール込み）
uv sync --extra dev

# 起動（http://localhost:8000）
uv run uvicorn app.main:app --reload

# 動作確認
curl -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"こんにちは","session_id":"demo"}'
curl 'localhost:8000/history?session_id=demo'
curl localhost:8000/metrics
```

### 本物の LLM で動かす（任意）

```bash
uv sync --extra dev --extra hf          # torch / transformers を追加
CHAT_BACKEND=hf uv run uvicorn app.main:app
```

## テスト

```bash
uv run pytest          # カバレッジ付きで全テスト実行
```

## Docker

```bash
docker compose up --build      # api + prometheus を一括起動
# API:        http://localhost:8000
# Prometheus: http://localhost:9090
```

## 設定（環境変数）

| 変数 | 既定 | 説明 |
|---|---|---|
| `CHAT_DATABASE_URL` | `sqlite:///./chat.db` | DB 接続先。Postgres なら `postgresql+psycopg://...` |
| `CHAT_BACKEND` | `echo` | `echo` か `hf` |
| `CHAT_HF_MODEL` | `sshleifer/tiny-gpt2` | hf バックエンドのモデル名 |
| `CHAT_MAX_NEW_TOKENS` | `64` | 生成する最大トークン数 |

## ドキュメント
- [DESIGN.md](DESIGN.md) — なぜこの構成にしたか（設計判断）
- [docs/](docs/) — テスト・DB性能・監視の落とし穴メモ（随時追記）

## ライセンス
MIT
