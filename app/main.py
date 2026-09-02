"""LingoGeek's local web app. Serves the one page and runs the queue."""
from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lingogeek.documents import SUPPORTED, translate_file
from lingogeek.engine import LanguagePair, ModelStore, Translator

HERE = Path(__file__).resolve().parent

app = FastAPI(title="LingoGeek")
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

store = ModelStore()


# --------------------------------------------------------------- the queue
@dataclass
class Item:
    id: int
    path: str
    name: str
    pair: str
    state: str = "waiting"        # waiting | downloading | working | done | failed
    done_blocks: int = 0
    total_blocks: int = 0
    output: str | None = None
    message: str = ""
    warnings: list[str] = field(default_factory=list)


class Queue:
    def __init__(self) -> None:
        self.items: dict[int, Item] = {}
        self._next = 1
        self._work: queue.Queue[int] = queue.Queue()
        self._lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def add(self, path: str, pair: str) -> Item:
        with self._lock:
            item = Item(id=self._next, path=path, name=Path(path).name, pair=pair)
            self.items[item.id] = item
            self._next += 1
        self._work.put(item.id)
        return item

    def _run(self) -> None:
        while True:
            item_id = self._work.get()
            item = self.items.get(item_id)
            if item is None:
                continue
            try:
                self._do(item)
            except Exception as exc:                      # noqa: BLE001
                item.state = "failed"
                item.message = str(exc) or exc.__class__.__name__
                traceback.print_exc()

    def _do(self, item: Item) -> None:
        source, target = item.pair.split("-", 1)
        folder = store.path_for(item.pair)
        if folder is None:
            item.state = "downloading"
            pair = next((p for p in store.index() if p.key == item.pair), None)
            if pair is None:
                raise RuntimeError(f"There is no language pack for {item.pair}.")

            def on_bytes(done: int, total: int) -> None:
                item.done_blocks = done
                item.total_blocks = total or 0

            folder = store.install(pair, progress=on_bytes)

        item.state = "working"
        item.done_blocks = item.total_blocks = 0
        translator = Translator.load(folder)

        def on_block(done: int, total: int) -> None:
            item.done_blocks, item.total_blocks = done, total

        job = translate_file(
            Path(item.path), target, lambda s: translator.translate_block(s), on_block
        )
        item.state = "done"
        item.output = str(job.output)
        item.warnings = job.warnings
        item.message = job.note or f"{job.blocks} blocks translated"


work_queue = Queue()


# ------------------------------------------------------------------ routes
@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (HERE / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/api/languages")
def languages() -> dict:
    try:
        pairs = store.index()
    except Exception as exc:                              # noqa: BLE001
        raise HTTPException(503, f"The language list could not be fetched: {exc}") from exc
    have = store.installed()
    return {
        "pairs": [
            {
                "key": p.key,
                "from_code": p.from_code, "from_name": p.from_name,
                "to_code": p.to_code, "to_name": p.to_name,
                "installed": p.key in have,
            }
            for p in pairs
        ],
        "installed_bytes": store.size_on_disk(),
    }


class AddBody(BaseModel):
    paths: list[str]
    pair: str


@app.post("/api/queue")
def add_to_queue(body: AddBody) -> dict:
    if not body.paths:
        raise HTTPException(400, "No files were given.")
    added, skipped = [], []
    for raw in body.paths:
        p = Path(raw)
        if not p.exists():
            skipped.append({"name": p.name, "why": "not found"})
        elif p.suffix.lower() not in SUPPORTED:
            skipped.append({"name": p.name, "why": f"{p.suffix or 'no extension'} is not supported"})
        else:
            added.append(work_queue.add(str(p), body.pair).id)
    return {"added": added, "skipped": skipped}


@app.get("/api/queue")
def read_queue() -> dict:
    return {"items": [vars(i) for i in work_queue.items.values()]}


@app.delete("/api/models/{key}")
def remove_model(key: str) -> dict:
    return {"removed": store.remove(key)}


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "supported": sorted(SUPPORTED)}
