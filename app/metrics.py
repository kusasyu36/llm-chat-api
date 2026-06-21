"""Prometheus メトリクス定義。

監視の基本は「数を数える(Counter)」「分布を見る(Histogram)」「今の値(Gauge)」。
ここでは chat の呼び出し回数と応答時間を計測し、/metrics で公開する。
Prometheus がこのエンドポイントを定期的に取りに来る（pull 型）。
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# chat が何回呼ばれたか。backend ラベルで echo/hf を区別。
CHAT_REQUESTS = Counter(
    "chat_requests_total",
    "chat エンドポイントの累計リクエスト数",
    ["backend"],
)

# chat の応答時間（秒）の分布。SLO（例: 95%が1秒以内）の監視に使う。
CHAT_LATENCY = Histogram(
    "chat_latency_seconds",
    "chat エンドポイントの応答時間（秒）",
    ["backend"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
