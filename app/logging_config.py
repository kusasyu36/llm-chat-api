"""ログ設定（structlog）。

print デバッグを卒業し、構造化ログ（structured logging）にする。
構造化ログ＝ログを「ただの文章」ではなく「キーと値のデータ」で出す方式。

なぜ嬉しいか:
- 本番では JSON で出す → 監視ツール（Loki, Datadog 等）が機械的に検索・集計できる
- 開発では色付きの読みやすい形で出す
環境変数 CHAT_LOG_JSON で本番/開発を切り替える。
"""

from __future__ import annotations

import logging
import os
import sys

import structlog


def configure_logging() -> None:
    json_logs = os.getenv("CHAT_LOG_JSON", "false").lower() == "true"

    # 標準 logging の出力先と最低レベルを設定（uvicorn のログとも揃える）。
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    # ログに毎回つける共通加工（時刻・レベル・例外情報など）。
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # リクエストごとの文脈を自動付与
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 最後の整形だけ本番(JSON)/開発(色付きコンソール)で切り替える。
    renderer = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
