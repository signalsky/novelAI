from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from config.log import get_logger

_logger = get_logger(__name__)
_CACHED_BASE_CONFIG: Optional["BaseConfig"] = None
_CACHED_OSS_CONFIG: Optional["OssConfig"] = None
_CACHED_QIANFAN_CONFIG: Optional["QianfanConfig"] = None


@dataclass(frozen=True)
class BaseConfig:
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class OssConfig:
    endpoint: str
    bucket: str
    domain: str
    access_key_id: str
    access_key_secret: str


@dataclass(frozen=True)
class QianfanConfig:
    api_key: str
    base_url: str
    model: str
    search_source: str
    enable_corner_markers: bool
    enable_deep_search: bool
    stream: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_config_path() -> Path:
    return _project_root() / "config" / "data" / "base.yaml"


def _read_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except Exception as exc:
        raise RuntimeError("缺少依赖：PyYAML。请先安装：pip install pyyaml") from exc

    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"配置文件内容必须是YAML字典：{path}")
    return data


def _as_str(value: Any, *, field_name: str, path: Path) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    raise ValueError(f"字段 {field_name} 必须是字符串：{path}")


def _as_mapping(value: Any, *, field_name: str, path: Path) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    raise ValueError(f"字段 {field_name} 必须是YAML字典：{path}")


def _as_bool(value: Any, *, field_name: str, path: Path, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes", "y", "on"):
            return True
        if v in ("0", "false", "no", "n", "off"):
            return False
        return default
    raise ValueError(f"字段 {field_name} 必须是布尔值：{path}")


def _normalize_urlish(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    v = v.strip("`").strip()
    v = v.rstrip(",").strip()
    return v


def load_base_config(config_path: Optional[str | Path] = None) -> BaseConfig:
    path = (
        Path(config_path)
        if config_path is not None
        else Path(os.getenv("NOVELAI_CONFIG_PATH") or _default_config_path())
    )
    path = path.resolve()

    data = _read_yaml(path)

    api_key = os.getenv("DASHSCOPE_API_KEY") or _as_str(
        data.get("api_key"), field_name="api_key", path=path
    )
    base_url = os.getenv("DASHSCOPE_BASE_URL") or _as_str(
        data.get("base_url"), field_name="base_url", path=path
    )
    model = os.getenv("DASHSCOPE_MODEL") or _as_str(
        data.get("model"), field_name="model", path=path
    )

    base_url = _normalize_urlish(base_url)
    cfg = BaseConfig(api_key=api_key, base_url=base_url, model=model)
    _logger.info(
        "BaseConfig loaded (api_key=%s, base_url=%s, model=%s)",
        "set" if bool(cfg.api_key) else "empty",
        cfg.base_url,
        cfg.model,
    )
    return cfg


def get_base_config() -> BaseConfig:
    global _CACHED_BASE_CONFIG
    if _CACHED_BASE_CONFIG is None:
        _CACHED_BASE_CONFIG = load_base_config()
    return _CACHED_BASE_CONFIG


def load_oss_config(config_path: Optional[str | Path] = None) -> OssConfig:
    path = (
        Path(config_path)
        if config_path is not None
        else Path(os.getenv("NOVELAI_CONFIG_PATH") or _default_config_path())
    )
    path = path.resolve()

    data = _read_yaml(path)
    oss_data = _as_mapping(data.get("oss"), field_name="oss", path=path)

    endpoint = os.getenv("OSS_ENDPOINT") or _as_str(
        oss_data.get("endpoint"), field_name="oss.endpoint", path=path
    )
    bucket = os.getenv("OSS_BUCKET") or _as_str(
        oss_data.get("bucket"), field_name="oss.bucket", path=path
    )
    domain = os.getenv("OSS_DOMAIN") or _as_str(
        oss_data.get("domain"), field_name="oss.domain", path=path
    )
    access_key_id = (
        os.getenv("OSS_ACCESS_KEY_ID")
        or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        or _as_str(oss_data.get("access_key_id"), field_name="oss.access_key_id", path=path)
    )
    access_key_secret = (
        os.getenv("OSS_ACCESS_KEY_SECRET")
        or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        or _as_str(
            oss_data.get("access_key_secret"), field_name="oss.access_key_secret", path=path
        )
    )

    cfg = OssConfig(
        endpoint=endpoint,
        bucket=bucket,
        domain=domain,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
    )
    _logger.info(
        "OssConfig loaded (bucket=%s, endpoint=%s, domain=%s, access_key_id=%s, access_key_secret=%s)",
        cfg.bucket,
        cfg.endpoint,
        cfg.domain,
        "set" if bool(cfg.access_key_id) else "empty",
        "set" if bool(cfg.access_key_secret) else "empty",
    )
    return cfg


def get_oss_config() -> OssConfig:
    global _CACHED_OSS_CONFIG
    if _CACHED_OSS_CONFIG is None:
        _CACHED_OSS_CONFIG = load_oss_config()
    return _CACHED_OSS_CONFIG


def load_qianfan_config(config_path: Optional[str | Path] = None) -> QianfanConfig:
    path = (
        Path(config_path)
        if config_path is not None
        else Path(os.getenv("NOVELAI_CONFIG_PATH") or _default_config_path())
    )
    path = path.resolve()

    data = _read_yaml(path)
    qf_data = _as_mapping(
        data.get("qianfan") or data.get("baidu_qianfan"), field_name="qianfan", path=path
    )

    api_key = (
        os.getenv("BAIDU_QIANFAN_API_KEY")
        or os.getenv("QIANFAN_API_KEY")
        or _as_str(qf_data.get("api_key"), field_name="qianfan.api_key", path=path)
    )
    base_url = (
        os.getenv("BAIDU_QIANFAN_BASE_URL")
        or _as_str(qf_data.get("base_url"), field_name="qianfan.base_url", path=path)
        or "https://qianfan.baidubce.com"
    )
    model = (
        os.getenv("BAIDU_QIANFAN_MODEL")
        or _as_str(qf_data.get("model"), field_name="qianfan.model", path=path)
        or "ernie-3.5-8k"
    )
    search_source = (
        os.getenv("BAIDU_QIANFAN_SEARCH_SOURCE")
        or _as_str(qf_data.get("search_source"), field_name="qianfan.search_source", path=path)
        or "baidu_search_v2"
    )

    enable_corner_markers = _as_bool(
        qf_data.get("enable_corner_markers"),
        field_name="qianfan.enable_corner_markers",
        path=path,
        default=True,
    )
    enable_deep_search = _as_bool(
        qf_data.get("enable_deep_search"),
        field_name="qianfan.enable_deep_search",
        path=path,
        default=True,
    )
    stream = _as_bool(qf_data.get("stream"), field_name="qianfan.stream", path=path, default=False)

    base_url = _normalize_urlish(base_url)
    cfg = QianfanConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        search_source=search_source,
        enable_corner_markers=enable_corner_markers,
        enable_deep_search=enable_deep_search,
        stream=stream,
    )
    _logger.info(
        "QianfanConfig loaded (api_key=%s, base_url=%s, model=%s, search_source=%s)",
        "set" if bool(cfg.api_key) else "empty",
        cfg.base_url,
        cfg.model,
        cfg.search_source,
    )
    return cfg


def get_qianfan_config() -> QianfanConfig:
    global _CACHED_QIANFAN_CONFIG
    if _CACHED_QIANFAN_CONFIG is None:
        _CACHED_QIANFAN_CONFIG = load_qianfan_config()
    return _CACHED_QIANFAN_CONFIG
