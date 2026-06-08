"""テスト共通のフィクスチャ。

本番 DB ではなく、テストごとに使い捨ての一時 SQLite を使う。
これで「テストがお互いに干渉しない」「本番データを汚さない」を担保する。
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    # 一時ファイルの SQLite を環境変数で指定 → 設定キャッシュ前に差し込む。
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("CHAT_DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("CHAT_BACKEND", "echo")

    # 設定とDBエンジンはモジュール読み込み時に確定するため、
    # 環境変数を入れてから import し、キャッシュをクリアして読み直す。
    from app import config

    config.get_settings.cache_clear()

    # db モジュールはエンジンをモジュール変数に持つので import し直す。
    import importlib

    from app import db as db_module

    importlib.reload(db_module)

    import app.main as main_module

    importlib.reload(main_module)

    from fastapi.testclient import TestClient

    with TestClient(main_module.app) as c:
        yield c
