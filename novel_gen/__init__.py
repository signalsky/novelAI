from __future__ import annotations

from typing import Optional

from config.log import get_logger
from llm.qwen_client import QwenClient

_logger = get_logger(__name__)


def optimize_text(
    *,
    original: str,
    instruction: str = "",
    field: str = "",
    client: Optional[QwenClient] = None,
) -> str:
    resolved_original = (original or "").strip()
    resolved_instruction = (instruction or "").strip()
    resolved_field = (field or "").strip()

    prompt = (
        "你是网文小说编辑助手。\n"
        f"目标字段：{resolved_field if resolved_field else '未指定'}\n"
        f"原文：\n{resolved_original if resolved_original else '无'}\n"
        f"用户要求：\n{resolved_instruction if resolved_instruction else '无'}\n"
        "请优化原文，保持关键信息与风格一致，表达更清晰有张力。\n"
        "只输出优化后的文本，不要输出解释或多余内容。\n"
    )

    llm = client or QwenClient()
    text = llm.chat(prompt)
    if isinstance(text, str) and text.strip():
        return text.strip()
    _logger.warning("优化结果为空，返回原文")
    return resolved_original
