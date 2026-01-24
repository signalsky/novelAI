from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from config.log import get_logger

_logger = get_logger(__name__)


@dataclass(frozen=True)
class BaiduAiSearchConfig:
    api_key: str
    base_url: str
    model: str
    search_source: str
    enable_corner_markers: bool
    enable_deep_search: bool
    stream: bool


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    return default


def _normalize_base_url(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    v = v.strip("`").strip()
    v = v.rstrip(",").strip()
    return v


def _resolve_config() -> BaiduAiSearchConfig:
    from config.loader import get_qianfan_config

    qf = get_qianfan_config()

    api_key = os.getenv("BAIDU_QIANFAN_API_KEY") or os.getenv("QIANFAN_API_KEY") or qf.api_key
    base_url = _normalize_base_url(os.getenv("BAIDU_QIANFAN_BASE_URL") or qf.base_url)
    model = os.getenv("BAIDU_QIANFAN_MODEL") or qf.model
    search_source = os.getenv("BAIDU_QIANFAN_SEARCH_SOURCE") or qf.search_source
    enable_corner_markers = _as_bool(
        os.getenv("BAIDU_QIANFAN_ENABLE_CORNER_MARKERS"), default=qf.enable_corner_markers
    )
    enable_deep_search = _as_bool(
        os.getenv("BAIDU_QIANFAN_ENABLE_DEEP_SEARCH"), default=qf.enable_deep_search
    )
    stream = _as_bool(os.getenv("BAIDU_QIANFAN_STREAM"), default=qf.stream)
    return BaiduAiSearchConfig(
        api_key=api_key or "",
        base_url=base_url or "https://qianfan.baidubce.com",
        model=model or "ernie-3.5-8k",
        search_source=search_source or "baidu_search_v2",
        enable_corner_markers=enable_corner_markers,
        enable_deep_search=enable_deep_search,
        stream=stream,
    )


class BaiduAiSearchClient:
    def __init__(self, cfg: Optional[BaiduAiSearchConfig] = None) -> None:
        self.cfg = cfg or _resolve_config()
        if not self.cfg.api_key:
            raise ValueError(
                "百度千帆 API Key 为空：请设置环境变量 BAIDU_QIANFAN_API_KEY（或 QIANFAN_API_KEY）"
            )

    def chat_completions(
        self,
        *,
        messages: list[dict[str, Any]],
        instruction: str = "",
        model: Optional[str] = None,
        enable_deep_search: Optional[bool] = None,
        enable_corner_markers: Optional[bool] = None,
        search_source: Optional[str] = None,
        timeout_s: float = 180,
    ) -> Optional[str]:
        resolved_model = (model or self.cfg.model).strip()
        resolved_search_source = (search_source or self.cfg.search_source).strip()

        payload: dict[str, Any] = {
            "messages": messages,
            "stream": self.cfg.stream,
            "model": resolved_model,
            "instruction": instruction or "",
            "enable_corner_markers": (
                self.cfg.enable_corner_markers
                if enable_corner_markers is None
                else bool(enable_corner_markers)
            ),
            "enable_deep_search": (
                self.cfg.enable_deep_search if enable_deep_search is None else bool(enable_deep_search)
            ),
            "search_source": resolved_search_source,
        }

        url = f"{self.cfg.base_url.rstrip('/')}/v2/ai_search/chat/completions"

        try:
            import requests
        except Exception as exc:
            raise RuntimeError("缺少依赖：requests。请先安装：pip install requests") from exc

        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.cfg.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=(10, timeout_s),
            )
            if resp.status_code < 200 or resp.status_code >= 300:
                try:
                    err = resp.json()
                    if isinstance(err, dict):
                        code = err.get("code")
                        msg = err.get("message")
                        if isinstance(code, int) and isinstance(msg, str) and msg.strip():
                            _logger.warning(
                                "百度智能搜索失败 (status=%s, code=%s, message=%s)",
                                resp.status_code,
                                code,
                                msg.strip(),
                            )
                            return None
                except Exception:
                    pass
                _logger.warning(
                    "百度智能搜索失败 (status=%s): %s",
                    resp.status_code,
                    resp.text[:2000],
                )
                return None
            data = resp.json()
        except Exception:
            _logger.exception("调用百度智能搜索失败 (url=%s, model=%s)", url, resolved_model)
            return None

        try:
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                msg = choices[0].get("message")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
        except Exception:
            _logger.exception("解析百度智能搜索响应失败: %s", str(data)[:2000])
            return None

        _logger.warning("百度智能搜索响应缺少有效 content: %s", str(data)[:2000])
        return None
