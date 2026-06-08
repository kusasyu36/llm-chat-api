# 設計ノート（DESIGN.md）

このプロジェクトで「なぜこの構成にしたか」を、面接で自分の言葉で説明できるように
記録しておくためのメモ。Lv3 の核心は「動く」ことではなく「設計判断を説明できる」こと。

## 全体方針

Web サービスの基本セット（API・DB・コンテナ・CI・監視）を**最小構成で一通り**揃える。
個々の技術を深掘りする前に、まず「それらがどう噛み合うか」の全体像を手で組む。

## 主要な設計判断

### 1. LLM バックエンドを抽象化した（app/backends.py）
- **判断**: `echo`（依存なしのダミー）と `hf`（Hugging Face）を共通インターフェイスで差し替え可能にした。
- **理由**: テスト・CI を重いモデルのダウンロードなしで高速・安定に回したい。本番だけ `hf` に切り替える。
- **他の選択肢**: 最初から transformers 直書き → テストが遅く不安定になり却下。
- **キーワード**: 依存性逆転、テスト容易性。

### 2. ORM (SQLAlchemy) を生 SQL より優先した（app/db.py）
- **判断**: 履歴テーブルを SQLAlchemy 2.0 の宣言的マッピングで定義。
- **理由**: SQLite で始めて Postgres へ移行する計画（Week 1 後半）。接続文字列を変えるだけで移行できる。
- **トレードオフ**: ORM は薄い抽象化コストがある。が、移行容易性と SQL インジェクション耐性を優先。
- **index**: `session_id` に index を張った。後で N+1 と index の効果を `docs/db-perf.md` で計測する。

### 3. 設定を pydantic-settings に集約した（app/config.py）
- **判断**: 環境変数 `CHAT_*` → 型付き設定オブジェクト。`get_settings()` を lru_cache で1回だけ評価。
- **理由**: 本番/テスト/ローカルで挙動を環境変数だけで切り替えたい（12-factor app）。

### 4. メトリクスは Counter と Histogram（app/metrics.py）
- **判断**: `chat_requests_total`(Counter) と `chat_latency_seconds`(Histogram)。
- **理由**: 監視の基本は「回数」と「応答時間の分布」。Histogram は SLO（例: p95 < 1s）の評価に使える。
- **pull 型**: Prometheus が `/metrics` を定期取得する。アプリは push しない（疎結合）。

### 5. Multi-stage Dockerfile + 非 root 実行
- **判断**: builder で依存解決 → runtime には成果物だけコピー。`appuser` で実行。
- **理由**: 最終イメージを軽く・安全に。依存定義を先にコピーしてレイヤキャッシュを効かせる。

## 今週の残タスク（Lv3 到達のため）
- [ ] Postgres へ移行し、N+1 と index 効果を計測 → `docs/db-perf.md`
- [ ] structlog の本番設定（JSON ログ）+ エラーハンドリング整理
- [ ] Grafana ダッシュボード + SLI/SLO 定義 → `docs/monitoring.md`
- [ ] テストの落とし穴メモ → `docs/testing-pitfalls.md`
- [ ] 夜間バッチで履歴集計（冪等・再実行可能）→ ETL 項目

## 既知の割り切り（今は未対応）
- 認証なし（練習用）。本番化するなら API キー or OAuth が必要。
- バックエンド初期化は単一プロセス前提。スケールアウト時はモデルサーバ分離を検討。
