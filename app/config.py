"""アプリ設定。環境変数 or .env から読み込む。

pydantic-settings を使うと「環境変数 → 型付き設定オブジェクト」への変換と
バリデーションを自動でやってくれる。設定値を一箇所に集約することで、
本番(Docker)・テスト・ローカルで挙動を切り替えやすくする。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHAT_", env_file=".env", extra="ignore")

    # DB 接続先。既定は SQLite（ファイル1個で動く）。
    # 本番では CHAT_DATABASE_URL=postgresql+psycopg://... に差し替えるだけで移行できる。
    database_url: str = "sqlite:///./chat.db"

    # LLM バックエンドの選択。"echo"（依存なしのダミー）か "hf"（Hugging Face）。
    backend: str = "echo"

    # backend="hf" のとき使うモデル名。小型を既定にする。
    hf_model: str = "sshleifer/tiny-gpt2"

    # 生成する最大トークン数。
    max_new_tokens: int = 64


@lru_cache
def get_settings() -> Settings:
    """設定を1回だけ読み込んで使い回す（毎リクエスト読み直さない）。"""
    return Settings()
