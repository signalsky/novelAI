from __future__ import annotations

from pathlib import Path
from typing import Optional

from config.loader import OssConfig, get_oss_config
from config.log import get_logger

_logger = get_logger(__name__)


def _normalize_endpoint(endpoint: str) -> str:
    ep = (endpoint or "").strip()
    if ep.startswith("http://") or ep.startswith("https://"):
        return ep
    return f"https://{ep}"


def _normalize_key(key: str) -> str:
    return (key or "").lstrip("/")


def _is_not_found_error(exc: Exception) -> bool:
    name = exc.__class__.__name__
    status = getattr(exc, "status", None)
    code = getattr(exc, "code", None)

    details = getattr(exc, "details", None)
    if details is not None:
        status = status or getattr(details, "status", None)
        code = code or getattr(details, "code", None)

    if code in {"NoSuchKey", "NoSuchObject"}:
        return True
    if status == 404 and (code in {None, "NoSuchKey", "NoSuchObject"} or name in {"NoSuchKey"}):
        return True
    if "NoSuchKey" in str(exc):
        return True
    return False


class OssStorage:
    def __init__(self, cfg: Optional[OssConfig] = None) -> None:
        self.cfg = cfg or get_oss_config()
        if not self.cfg.endpoint or not self.cfg.bucket:
            raise ValueError("OSS配置不完整：endpoint/bucket 不能为空")
        if not self.cfg.access_key_id or not self.cfg.access_key_secret:
            raise ValueError(
                "OSS配置不完整：access_key_id/access_key_secret 不能为空（请用环境变量注入）"
            )

        try:
            import oss2
        except Exception as exc:
            raise RuntimeError("缺少依赖：oss2。请先安装：poetry install 或 pip install oss2") from exc

        auth = oss2.Auth(self.cfg.access_key_id, self.cfg.access_key_secret)
        self.bucket = oss2.Bucket(auth, _normalize_endpoint(self.cfg.endpoint), self.cfg.bucket)

    def put_text(self, key: str, text: str, *, encoding: str = "utf-8") -> None:
        k = _normalize_key(key)
        try:
            result = self.bucket.put_object(
                k,
                text.encode(encoding),
                headers={"Content-Type": f"text/plain; charset={encoding}"},
            )
            _logger.info(
                "OSS put_text ok (bucket=%s, key=%s, status=%s)",
                self.cfg.bucket,
                k,
                result.status,
            )
        except Exception:
            _logger.exception("OSS put_text failed (bucket=%s, key=%s)", self.cfg.bucket, k)
            raise

    def get_text(self, key: str, *, encoding: str = "utf-8") -> str:
        k = _normalize_key(key)
        try:
            obj = self.bucket.get_object(k)
            data = obj.read()
            _logger.info("OSS get_text ok (bucket=%s, key=%s)", self.cfg.bucket, k)
            return data.decode(encoding)
        except Exception as exc:
            if _is_not_found_error(exc):
                _logger.info("OSS get_text miss (bucket=%s, key=%s)", self.cfg.bucket, k)
                return ""
            _logger.exception("OSS get_text failed (bucket=%s, key=%s)", self.cfg.bucket, k)
            raise

    def put_file(self, key: str, file_path: str | Path) -> None:
        k = _normalize_key(key)
        p = Path(file_path)
        try:
            result = self.bucket.put_object_from_file(k, str(p))
            _logger.info(
                "OSS put_file ok (bucket=%s, key=%s, status=%s)",
                self.cfg.bucket,
                k,
                result.status,
            )
        except Exception:
            _logger.exception(
                "OSS put_file failed (bucket=%s, key=%s, file=%s)", self.cfg.bucket, k, p
            )
            raise

    def get_file(self, key: str, file_path: str | Path) -> None:
        k = _normalize_key(key)
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.bucket.get_object_to_file(k, str(p))
            _logger.info("OSS get_file ok (bucket=%s, key=%s, file=%s)", self.cfg.bucket, k, p)
        except Exception:
            _logger.exception(
                "OSS get_file failed (bucket=%s, key=%s, file=%s)", self.cfg.bucket, k, p
            )
            raise

    def sign_url(self, key: str, *, expires: int = 3600, method: str = "GET") -> str:
        k = _normalize_key(key)
        try:
            url = self.bucket.sign_url(method, k, expires)
            _logger.info(
                "OSS sign_url ok (bucket=%s, key=%s, expires=%s)", self.cfg.bucket, k, expires
            )
            return url
        except Exception:
            _logger.exception("OSS sign_url failed (bucket=%s, key=%s)", self.cfg.bucket, k)
            raise
