from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable, Optional

from config.loader import BaseConfig, get_base_config
from config.log import get_logger

_logger = get_logger(__name__)


def _resolve_config() -> BaseConfig:
    cfg = get_base_config()
    api_key = os.getenv("AI_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or cfg.api_key
    base_url = os.getenv("AI_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL") or cfg.base_url
    model = os.getenv("AI_MODEL") or os.getenv("DASHSCOPE_MODEL") or cfg.model
    return BaseConfig(api_key=api_key, base_url=base_url, model=model)


class QwenClient:
    def __init__(self) -> None:
        cfg = _resolve_config()
        self.model = cfg.model
        self.base_url = cfg.base_url

        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError("缺少依赖：openai。请先安装：pip install openai") from exc

        self.client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

    def chat(self, prompt: str) -> Optional[str]:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
            )
            return completion.choices[0].message.content
        except Exception:
            _logger.exception("调用Qwen模型失败 (base_url=%s, model=%s)", self.base_url, self.model)
            return None

    def chat_messages(self, messages: list[dict[str, Any]]) -> Optional[str]:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return completion.choices[0].message.content
        except Exception:
            _logger.exception(
                "调用Qwen模型失败 (base_url=%s, model=%s)", self.base_url, self.model
            )
            return None

    def chat_messages_stream(self, messages: list[dict[str, Any]]) -> Iterable[str]:
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                try:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None)
                    if isinstance(content, str) and content:
                        yield content
                except Exception:
                    continue
        except Exception:
            _logger.exception(
                "调用Qwen模型失败 (stream, base_url=%s, model=%s)", self.base_url, self.model
            )
            return


def extract_json_from_text(text: Optional[str]) -> Optional[dict[str, Any]]:
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        pass

    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        parsed = json.loads(match.group())
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        _logger.exception("JSON解析失败")
        return None
