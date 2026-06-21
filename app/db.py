"""データベース層。会話履歴を保存する。

SQLAlchemy 2.0 の宣言的マッピングを使う。SQLite で始めて、後で
PostgreSQL に移行できるよう、生 SQL ではなく ORM で書いておく
（接続文字列を変えるだけで移行できる）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class ChatLog(Base):
    """1回の chat リクエスト＝1行。"""

    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 同一ユーザーの会話をまとめて引けるよう index を張る（後で N+1/index の効果を計測）。
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    backend: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def _make_engine(database_url: str):
    # SQLite は同一スレッド前提なので、FastAPI のスレッドプールから使うため
    # check_same_thread=False を渡す。Postgres では不要。
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


_engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """テーブルを作る（無ければ）。起動時に呼ぶ。"""
    Base.metadata.create_all(bind=_engine)


def get_session() -> Session:
    """FastAPI の依存性注入で使うセッション生成器。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
