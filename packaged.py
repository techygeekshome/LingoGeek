"""The entry point PyInstaller builds.

Two things here are the whole reason this file exists, both learned the hard
way on ShortGeek 1.0.1:

  1. A windowed build starts with sys.stdout and sys.stderr set to None. Any
     library that configures logging then dies on startup with nothing on
     screen. So the streams are given somewhere to go before anything else runs.
  2. The ASGI app is imported directly rather than passed to uvicorn as a
     string, because the string form re-imports through a path that does not
     exist inside a frozen bundle.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import traceback
from pathlib import Path


def _crash_log_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    p = Path(base) / "TechyGeeksHome" / "LingoGeek"
    p.mkdir(parents=True, exist_ok=True)
    return p / "startup-error.txt"


def _give_the_process_somewhere_to_write() -> None:
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        path = _crash_log_path().with_name("output.txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        sink = open(path, "w", encoding="utf-8", errors="replace", buffering=1)
    except Exception:
        sink = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = sink
    if sys.stderr is None:
        sys.stderr = sink


def _show_startup_failure(failures: list[str]) -> None:
    if not failures:
        return
    text = "\n\n".join(failures)
    try:
        _crash_log_path().write_text(text, encoding="utf-8")
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None,
            "LingoGeek could not start.\n\nThe details were written to:\n"
            f"{_crash_log_path()}",
            "LingoGeek",
            0x10,
        )
    except Exception:
        print(text, file=sys.stderr)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    if os.environ.get("LINGOGEEK_NO_STREAMS"):
        sys.stdout = None       # type: ignore[assignment]
        sys.stderr = None       # type: ignore[assignment]
    _give_the_process_somewhere_to_write()

    failure: list[str] = []
    try:
        import uvicorn
        from app.main import app as asgi_app
    except Exception:
        failure.append(traceback.format_exc())
        asgi_app = None
        uvicorn = None          # type: ignore[assignment]

    if asgi_app is None:
        _show_startup_failure(failure)
        return 1

    port = free_port()

    def serve() -> None:
        try:
            uvicorn.run(asgi_app, host="127.0.0.1", port=port,
                        log_level="warning", log_config=None)
        except Exception:
            failure.append(traceback.format_exc())

    threading.Thread(target=serve, daemon=True).start()
    time.sleep(1.2)

    if failure:
        _show_startup_failure(failure)
        return 1

    url = f"http://127.0.0.1:{port}/"

    if os.environ.get("LINGOGEEK_NO_WINDOW"):
        print(url, flush=True)
        while True:
            time.sleep(1)

    try:
        import webview
        from app.desktop_api import create_window
        create_window(url)
        webview.start()
    except Exception:
        failure.append(traceback.format_exc())
        _show_startup_failure(failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
