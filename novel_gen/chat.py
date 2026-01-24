from __future__ import annotations

import os
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional

from config.log import get_logger
from llm.baidu_client import BaiduAiSearchClient
from llm.qwen_client import QwenClient
from llm.qwen_client import extract_json_from_text

_logger = get_logger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


_lock = Lock()
_messages: list[ChatMessage] = []
_system_prompt = (
    "你是中文小说创作助手。\n"
    "你与用户进行多轮对话，帮助完善故事设定、剧情结构与写作表达。\n"
    "回答要具体可执行，优先给可直接复制到编辑框的文字。\n"
)

_route_mode = (os.getenv("CHAT_ROUTE_MODE") or "auto").strip().lower()


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = [{"role": "system", "content": _system_prompt}]
    for msg in messages:
        role = msg.role if msg.role in ("user", "assistant") else "user"
        result.append({"role": role, "content": msg.content})
    return result


def _detect_route(*, message: str, client: Optional[QwenClient] = None) -> str:
    resolved = (message or "").strip()
    if not resolved:
        return "chat"

    if _route_mode in ("search", "baidu", "ai_search"):
        return "search"
    if _route_mode in ("chat", "qwen", "llm"):
        return "chat"

    heuristic_keywords = (
        "今天",
        "昨日",
        "明天",
        "近期",
        "最近",
        "刚刚",
        "最新",
        "消息",
        "新闻",
        "价格",
        "油价",
        "汇率",
        "股价",
        "天气",
        "政策",
        "公告",
        "发布",
        "发生了什么",
        "谁是",
        "什么时候",
        "在哪",
        "来源",
        "链接",
    )
    if any(k in resolved for k in heuristic_keywords):
        return "search"

    prompt = (
        "你是意图识别器，只做路由判断，不要输出多余内容。\n"
        "判断用户问题是否需要联网搜索（需要最新信息、具体事实核验、引用来源、或依赖外部网页）。\n"
        "仅输出JSON，不要解释。\n"
        'JSON格式：{"route":"search"} 或 {"route":"chat"}\n'
        f"用户问题：{resolved}\n"
    )

    llm = client or QwenClient()
    text = llm.chat(prompt)
    data = extract_json_from_text(text)
    if isinstance(data, dict):
        route = data.get("route")
        if route == "search":
            return "search"
        if route == "chat":
            return "chat"

    return "chat"


def get_history() -> list[dict[str, str]]:
    with _lock:
        return [{"role": m.role, "content": m.content} for m in _messages]


def clear_history() -> None:
    with _lock:
        _messages.clear()


def send_message(
    *,
    message: str,
    use_search: Optional[bool] = None,
    client: Optional[QwenClient] = None,
) -> str:
    content = (message or "").strip()
    if not content:
        return ""

    if use_search is None:
        route = _detect_route(message=content, client=client)
        resolved_use_search = route == "search"
    else:
        resolved_use_search = bool(use_search)

    with _lock:
        _messages.append(ChatMessage(role="user", content=content))
        if len(_messages) > 60:
            _messages[:] = _messages[-60:]

    if resolved_use_search:
        try:
            baidu = BaiduAiSearchClient()
            reply = baidu.chat_completions(
                messages=[{"role": "user", "content": content}],
                instruction=_system_prompt,
            )
        except Exception as exc:
            _logger.exception("百度智能搜索调用异常")
            if isinstance(exc, ValueError):
                reply = str(exc)
            else:
                reply = None
    else:
        payload = _to_openai_messages(get_messages_snapshot())
        llm = client or QwenClient()
        reply = llm.chat_messages(payload)

    if not isinstance(reply, str) or not reply.strip():
        _logger.warning("聊天回复为空")
        reply_text = "我没能生成有效回复，你可以换个问法再试一次。"
    else:
        reply_text = reply.strip()

    with _lock:
        _messages.append(ChatMessage(role="assistant", content=reply_text))
        if len(_messages) > 60:
            _messages[:] = _messages[-60:]

    return reply_text


def get_messages_snapshot() -> list[ChatMessage]:
    with _lock:
        return list(_messages)


def send_message_stream(
    *,
    message: str,
    use_search: Optional[bool] = None,
    client: Optional[QwenClient] = None,
) -> Any:
    content = (message or "").strip()
    if not content:
        yield ""
        return

    if use_search is None:
        route = _detect_route(message=content, client=client)
        resolved_use_search = route == "search"
    else:
        resolved_use_search = bool(use_search)

    with _lock:
        _messages.append(ChatMessage(role="user", content=content))
        if len(_messages) > 60:
            _messages[:] = _messages[-60:]

    if resolved_use_search:
        yield "正在搜索…\n"
        try:
            baidu = BaiduAiSearchClient()
            reply = baidu.chat_completions(
                messages=[{"role": "user", "content": content}],
                instruction=_system_prompt,
            )
            reply_text = (reply or "").strip()
        except Exception:
            _logger.exception("百度智能搜索调用异常")
            reply_text = ""

        if not reply_text:
            reply_text = "我没能生成有效回复，你可以换个问法再试一次。"

        step = 40
        for i in range(0, len(reply_text), step):
            yield reply_text[i : i + step]

        with _lock:
            _messages.append(ChatMessage(role="assistant", content=reply_text))
            if len(_messages) > 60:
                _messages[:] = _messages[-60:]
        return

    payload = _to_openai_messages(get_messages_snapshot())
    llm = client or QwenClient()
    buf_parts: list[str] = []
    try:
        for part in llm.chat_messages_stream(payload):
            buf_parts.append(part)
            yield part
    except Exception:
        _logger.exception("Qwen流式聊天失败")

    reply_text = "".join(buf_parts).strip()
    if not reply_text:
        reply_text = "我没能生成有效回复，你可以换个问法再试一次。"
        yield reply_text

    with _lock:
        _messages.append(ChatMessage(role="assistant", content=reply_text))
        if len(_messages) > 60:
            _messages[:] = _messages[-60:]
