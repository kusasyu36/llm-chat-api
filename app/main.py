"""FastAPI アプリ本体。エンドポイントを定義する。

- POST /chat     : メッセージを送ると LLM が応答し、履歴を DB に保存する
- GET  /history  : セッションの会話履歴を返す
- GET  /metrics  : Prometheus 形式のメトリクスを公開する
- GET  /healthz  : 死活監視用ヘルスチェック
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backends import make_backend
from app.config import get_settings
from app.db import ChatLog, get_session, init_db
from app.logging_config import configure_logging
from app.metrics import CHAT_LATENCY, CHAT_REQUESTS
from app.schemas import ChatRequest, ChatResponse, HistoryItem

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: ログ設定 → テーブル作成 → バックエンド初期化（重いモデルは1回だけ読む）。
    configure_logging()
    init_db()
    settings = get_settings()
    app.state.backend = make_backend(settings)
    log.info("startup", backend=app.state.backend.name, db=settings.database_url)
    yield
    log.info("shutdown")


app = FastAPI(title="llm-chat-api", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # リクエストごとに固有IDを振り、以降のログ全部に自動で付ける。
    # 障害調査時に「このリクエストで何が起きたか」を一本の糸で追える。
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # 想定外の例外を握りつぶさずログに残し、利用者には安全な500を返す
    # （スタックトレースなど内部情報を漏らさない）。
    log.error("unhandled_exception", error=str(exc), exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "内部エラーが発生しました"})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_session)) -> ChatResponse:
    backend = app.state.backend

    start = time.perf_counter()
    try:
        answer = backend.generate(req.message)
    except Exception as exc:
        # LLM バックエンドが落ちた/混んでいる時は 503 を返す。
        # 利用者側で「少し待って再試行」のフォールバックを取れるようにする。
        log.error("backend_failed", backend=backend.name, error=str(exc), exc_info=exc)
        raise HTTPException(status_code=503, detail="LLMバックエンドが一時的に利用できません") from exc
    latency_s = time.perf_counter() - start
    latency_ms = int(latency_s * 1000)

    # メトリクス記録（回数 + 応答時間）。
    CHAT_REQUESTS.labels(backend=backend.name).inc()
    CHAT_LATENCY.labels(backend=backend.name).observe(latency_s)

    # 履歴を DB に保存。
    row = ChatLog(
        session_id=req.session_id,
        prompt=req.message,
        response=answer,
        backend=backend.name,
        latency_ms=latency_ms,
    )
    db.add(row)
    db.commit()

    log.info("chat", session_id=req.session_id, backend=backend.name, latency_ms=latency_ms)
    return ChatResponse(response=answer, backend=backend.name, latency_ms=latency_ms)


@app.get("/history", response_model=list[HistoryItem])
def history(
    session_id: str = Query("default", max_length=64),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_session),
) -> list[ChatLog]:
    stmt = (
        select(ChatLog)
        .where(ChatLog.session_id == session_id)
        .order_by(ChatLog.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
