"""The bridge the desktop window exposes to the page.

The page needs real filesystem paths, because the translation queue opens the
file itself rather than receiving its bytes. A plain <input type="file"> cannot
give it one: File.path is a non-standard property that WebView2 does not
populate, so every picked file came back with an empty path and the queue
silently stayed empty. The native dialog below is the only reliable way to get
a path out of the host, so the page calls this instead of the input.
"""
from __future__ import annotations

import webview

FILE_TYPES = (
    "Documents and subtitles (*.docx;*.pdf;*.srt;*.vtt;*.txt;*.md)",
    "All files (*.*)",
)


class DesktopApi:
    """Exposed to JavaScript as window.pywebview.api."""

    def __init__(self) -> None:
        self.window: webview.Window | None = None

    def choose_files(self) -> list[str]:
        if self.window is None:
            return []
        picked = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=FILE_TYPES,
        )
        if not picked:
            return []
        return [str(p) for p in picked]


def create_window(url: str, *, title: str = "LingoGeek",
                  width: int = 1000, height: int = 760) -> webview.Window:
    """Make the window and wire the API to it."""
    api = DesktopApi()
    window = webview.create_window(title, url, width=width, height=height, js_api=api)
    api.window = window
    return window
