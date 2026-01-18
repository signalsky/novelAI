from __future__ import annotations

from typing import Optional

from config.log import get_logger
from llm.qwen_client import QwenClient, extract_json_from_text

_logger = get_logger(__name__)


def generate_name(
    *,
    gender: str = "男",
    style: str = "仙侠",
    description: str = "",
    client: Optional[QwenClient] = None,
) -> Optional[str]:
    resolved_description = (description or "").strip()
    resolved_gender = (gender or "男").strip()
    resolved_style = (style or "仙侠").strip()

    prompt = (
        "你是中文小说取名助手。\n"
        f"小说风格：{resolved_style}\n"
        f"性别：{resolved_gender}\n"
        f"名字说明：{resolved_description if resolved_description else '无'}\n"
        "\n"
        "请生成1个名字，要求：\n"
        "1) 更像人名，可带少量姓氏，不要生僻到难读\n"
        "2) 贴合风格与说明（如果有说明）\n"
        "3) 只输出JSON，不要输出任何多余文本\n"
        'JSON格式：{"name":"..."}\n'
    )

    llm = client or QwenClient()
    text = llm.chat(prompt)
    data = extract_json_from_text(text)
    if not data:
        _logger.warning("取名结果无法解析为JSON: %s", text)
        return None

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        _logger.warning("取名结果缺少name字段: %s", data)
        return None
    return name.strip()


if __name__ == "__main__":
    name = generate_name(
        gender="男",
        style="仙侠",
        description="姓韩，一个喜欢战斗的角色",
    )
    print(name)
    name = generate_name(
        gender="女",
        style="仙侠",
        description="一个喜欢战斗的角色",
    )
    print(name)