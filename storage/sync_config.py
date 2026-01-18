from __future__ import annotations

import sys
from pathlib import Path

from config.log import get_logger
from storage.oss_storage import OssStorage

_logger = get_logger(__name__)


def _get_local_config_path() -> Path:
    # 假设项目根目录在 storage 的上一级
    return Path(__file__).resolve().parents[1] / "config" / "data" / "base.yaml"


def push_config() -> None:
    local_path = _get_local_config_path()
    if not local_path.exists():
        _logger.error("本地配置文件不存在: %s", local_path)
        return

    oss = OssStorage()
    # 既然是同步配置，且 base.yaml 包含敏感信息，我们还是传到私有 Bucket 的 config/base.yaml
    oss.put_file("config/base.yaml", local_path)
    _logger.info("配置已推送到 OSS: config/base.yaml")


def pull_config() -> None:
    local_path = _get_local_config_path()
    oss = OssStorage()
    
    # 确保父目录存在
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        oss.get_file("config/base.yaml", local_path)
        _logger.info("配置已拉取到本地: %s", local_path)
    except Exception:
        _logger.error("从 OSS 拉取配置失败，请确认云端是否存在 config/base.yaml")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m storage.sync_config [push|pull]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "push":
        push_config()
    elif cmd == "pull":
        pull_config()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python -m storage.sync_config [push|pull]")
        sys.exit(1)
