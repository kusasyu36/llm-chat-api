"""エラー処理のテスト。

「正常系が動く」だけでなく「異常系で正しく失敗する」ことも Lv3 の要件。
バックエンドが落ちたとき 503 を返し、サーバーが落ちないことを確認する。
"""

from __future__ import annotations


def test_chat_returns_503_when_backend_fails(client):
    # 実行中アプリのバックエンドを、必ず例外を投げるものに差し替える。
    import app.main as main_module

    class BrokenBackend:
        name = "broken"

        def generate(self, prompt: str) -> str:
            raise RuntimeError("模擬: モデルサーバ落ちた")

    main_module.app.state.backend = BrokenBackend()

    res = client.post("/chat", json={"message": "hi", "session_id": "s"})
    assert res.status_code == 503
    assert "利用できません" in res.json()["detail"]


def test_request_id_header_present(client):
    # すべての応答に追跡用 X-Request-ID が付くこと。
    res = client.get("/healthz")
    assert "X-Request-ID" in res.headers
