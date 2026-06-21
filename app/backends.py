"""LLM バックエンド。差し替え可能にしておく。

- EchoBackend: 依存なし。入力をそのまま装飾して返す。テスト・CI・デモ用。
- HFBackend: Hugging Face transformers で実際に小型モデル推論する（任意）。

「バックエンドを抽象化しておく」ことで、テストは軽い echo で高速に回し、
本番は hf に切り替える、という運用ができる（依存性逆転の小さな実例）。
"""

from __future__ import annotations

from typing import Protocol

from app.config import Settings


class Backend(Protocol):
    name: str

    def generate(self, prompt: str) -> str: ...


class EchoBackend:
    name = "echo"

    def generate(self, prompt: str) -> str:
        # 本物の LLM の代わりに、決まった形で返す。テストが安定する。
        return f"[echo] {prompt.strip()}"


class HFBackend:
    name = "hf"

    def __init__(self, model_name: str, max_new_tokens: int) -> None:
        # import を遅延させ、hf extra を入れていない環境で読み込みエラーにしない。
        from transformers import pipeline

        self._pipe = pipeline("text-generation", model=model_name)
        self._max_new_tokens = max_new_tokens

    def generate(self, prompt: str) -> str:
        out = self._pipe(prompt, max_new_tokens=self._max_new_tokens, num_return_sequences=1)
        return out[0]["generated_text"]


def make_backend(settings: Settings) -> Backend:
    if settings.backend == "hf":
        return HFBackend(settings.hf_model, settings.max_new_tokens)
    return EchoBackend()
