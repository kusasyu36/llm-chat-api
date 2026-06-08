"""リクエスト/レスポンスのスキーマ（Pydantic）。

FastAPI は型ヒントから自動でバリデーションと OpenAPI ドキュメントを作る。
入出力の形をここで宣言しておくと、不正な入力は API に届く前に弾かれる。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="ユーザーの入力")
    session_id: str = Field("default", max_length=64, description="会話セッションの識別子")


class ChatResponse(BaseModel):
    response: str
    backend: str
    latency_ms: int


class HistoryItem(BaseModel):
    id: int
    session_id: str
    prompt: str
    response: str
    backend: str
    latency_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}
