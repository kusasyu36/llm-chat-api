"""API の単体・統合テスト。"""

from __future__ import annotations


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_chat_returns_echo(client):
    res = client.post("/chat", json={"message": "こんにちは", "session_id": "s1"})
    assert res.status_code == 200
    body = res.json()
    assert body["backend"] == "echo"
    assert body["response"] == "[echo] こんにちは"
    assert body["latency_ms"] >= 0


def test_chat_validates_empty_message(client):
    # 空メッセージは Pydantic のバリデーションで弾かれる（422）。
    res = client.post("/chat", json={"message": "", "session_id": "s1"})
    assert res.status_code == 422


def test_history_records_and_orders(client):
    for msg in ["一通目", "二通目", "三通目"]:
        client.post("/chat", json={"message": msg, "session_id": "conv"})

    res = client.get("/history", params={"session_id": "conv", "limit": 10})
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 3
    # 新しい順に並ぶ（id 降順）。
    assert items[0]["prompt"] == "三通目"
    assert items[-1]["prompt"] == "一通目"


def test_history_isolated_by_session(client):
    client.post("/chat", json={"message": "A用", "session_id": "A"})
    client.post("/chat", json={"message": "B用", "session_id": "B"})

    res = client.get("/history", params={"session_id": "A"})
    items = res.json()
    assert len(items) == 1
    assert items[0]["session_id"] == "A"


def test_metrics_exposes_counter(client):
    client.post("/chat", json={"message": "x", "session_id": "m"})
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "chat_requests_total" in res.text
    assert "chat_latency_seconds" in res.text
