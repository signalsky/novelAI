from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config.log import get_logger
from storage.oss_storage import OssStorage

_logger = get_logger(__name__)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class NovelCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class StoryPayload(BaseModel):
    background: str = ""
    mainline: str = ""
    darkline: str = ""


class AdvancedPayload(BaseModel):
    style: str = ""
    core_design: str = ""
    reversal: str = ""
    highlights: str = ""


class OptimizeRequest(BaseModel):
    text: str = ""
    field: str = ""


def _oss() -> OssStorage:
    return OssStorage()


def _novels_index_key() -> str:
    return "novels/index.json"


def _novel_prefix(novel_id: str) -> str:
    return f"novels/{novel_id}"


def _story_key(novel_id: str) -> str:
    return f"{_novel_prefix(novel_id)}/story.json"


def _advanced_key(novel_id: str) -> str:
    return f"{_novel_prefix(novel_id)}/advanced.json"


def _load_index(oss: OssStorage) -> list[dict[str, Any]]:
    try:
        raw = oss.get_text(_novels_index_key())
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _save_index(oss: OssStorage, items: list[dict[str, Any]]) -> None:
    payload = json.dumps(items, ensure_ascii=False, indent=2)
    oss.put_text(_novels_index_key(), payload)


def _find_novel(index: list[dict[str, Any]], novel_id: str) -> dict[str, Any] | None:
    for item in index:
        if item.get("id") == novel_id:
            return item
    return None


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/novel/{novel_id}", response_class=HTMLResponse)
def novel_page(novel_id: str) -> str:
    html = (TEMPLATE_DIR / "novel.html").read_text(encoding="utf-8")
    return html.replace("{{NOVEL_ID}}", novel_id)


@app.get("/api/novels")
def list_novels() -> list[dict[str, Any]]:
    oss = _oss()
    return _load_index(oss)


@app.post("/api/novels")
def create_novel(payload: NovelCreateRequest) -> dict[str, Any]:
    oss = _oss()
    index = _load_index(oss)
    novel_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    item = {"id": novel_id, "title": payload.title.strip(), "created_at": now}
    index.append(item)
    _save_index(oss, index)
    placeholder_key = f"{_novel_prefix(novel_id)}/.keep"
    oss.put_text(placeholder_key, "placeholder")
    return item


@app.get("/api/novels/{novel_id}")
def get_novel(novel_id: str) -> dict[str, Any]:
    oss = _oss()
    index = _load_index(oss)
    item = _find_novel(index, novel_id)
    if item is None:
        raise HTTPException(status_code=404, detail="novel_not_found")
    story = {"background": "", "mainline": "", "darkline": ""}
    advanced = {"style": "", "core_design": "", "reversal": "", "highlights": ""}
    try:
        raw = oss.get_text(_story_key(novel_id))
        data = json.loads(raw)
        if isinstance(data, dict):
            story.update(
                {
                    "background": str(data.get("background", "")),
                    "mainline": str(data.get("mainline", "")),
                    "darkline": str(data.get("darkline", "")),
                }
            )
    except Exception:
        pass
    try:
        raw = oss.get_text(_advanced_key(novel_id))
        data = json.loads(raw)
        if isinstance(data, dict):
            advanced.update(
                {
                    "style": str(data.get("style", "")),
                    "core_design": str(data.get("core_design", "")),
                    "reversal": str(data.get("reversal", "")),
                    "highlights": str(data.get("highlights", "")),
                }
            )
    except Exception:
        pass
    return {"novel": item, "story": story, "advanced": advanced}


@app.post("/api/novels/{novel_id}/story")
def save_story(novel_id: str, payload: StoryPayload) -> dict[str, Any]:
    oss = _oss()
    index = _load_index(oss)
    item = _find_novel(index, novel_id)
    if item is None:
        raise HTTPException(status_code=404, detail="novel_not_found")
    data = {
        "background": payload.background,
        "mainline": payload.mainline,
        "darkline": payload.darkline,
    }
    oss.put_text(_story_key(novel_id), json.dumps(data, ensure_ascii=False, indent=2))
    return {"ok": True}


@app.post("/api/novels/{novel_id}/advanced")
def save_advanced(novel_id: str, payload: AdvancedPayload) -> dict[str, Any]:
    oss = _oss()
    index = _load_index(oss)
    item = _find_novel(index, novel_id)
    if item is None:
        raise HTTPException(status_code=404, detail="novel_not_found")
    data = {
        "style": payload.style,
        "core_design": payload.core_design,
        "reversal": payload.reversal,
        "highlights": payload.highlights,
    }
    oss.put_text(_advanced_key(novel_id), json.dumps(data, ensure_ascii=False, indent=2))
    return {"ok": True}


@app.post("/api/optimize")
def optimize(payload: OptimizeRequest) -> dict[str, Any]:
    text = payload.text.strip()
    return {"text": text}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
