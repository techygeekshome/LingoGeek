"""Run LingoGeek as a desktop window. Used when running from source."""
from __future__ import annotations

import socket
import threading
import time

import uvicorn
import webview

from app.main import app


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    port = free_port()
    threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning"),
        daemon=True,
    ).start()
    time.sleep(1.0)
    webview.create_window("LingoGeek", f"http://127.0.0.1:{port}/", width=1000, height=760)
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
