# Multi-stage build:
#   stage1(builder) で依存を入れ、stage2(runtime) には成果物だけコピーする。
#   こうするとビルドツールを最終イメージに含めず、軽く・安全にできる。

# ---- builder ----
FROM python:3.12-slim AS builder

# uv をコピーして依存解決に使う（高速・再現性のあるロック）。
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
# 依存定義を先にコピー → レイヤキャッシュが効き、コード変更だけなら再インストール不要。
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# アプリ本体をコピーしてプロジェクトをインストール。
COPY app ./app
RUN uv sync --frozen --no-dev

# ---- runtime ----
FROM python:3.12-slim AS runtime

# 非 root ユーザーで動かす（セキュリティの基本）。
RUN useradd --create-home appuser
WORKDIR /app

# builder から仮想環境とアプリだけ持ってくる。
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000

# コンテナの死活確認。
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
