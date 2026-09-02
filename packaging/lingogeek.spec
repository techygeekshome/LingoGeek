# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for LingoGeek.

The sys.path line is not decoration. collect_submodules() runs in an isolated
subprocess whose sys.path does not include the project, so without it the call
returns an empty list in silence and the built exe is missing half the app.
That is what shipped as ShortGeek 1.0.0.
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

datas = [
    (str(ROOT / "app" / "templates"), "app/templates"),
    (str(ROOT / "app" / "static"), "app/static"),
]
datas += collect_data_files("ctranslate2")
datas += collect_data_files("sentencepiece")
datas += collect_data_files("docx")

binaries = collect_dynamic_libs("ctranslate2") + collect_dynamic_libs("sentencepiece")

hiddenimports = [
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto", "uvicorn.lifespan.on",
    "ctranslate2", "sentencepiece", "docx", "pypdf",
]
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("lingogeek")
hiddenimports += collect_submodules("pydantic")

a = Analysis(
    [str(ROOT / "packaged.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["torch", "stanza", "tkinter", "matplotlib", "numpy.testing", "PIL.ImageQt"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="LingoGeek",
    console=False,
    icon=str(ROOT / "packaging" / "lingogeek.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="LingoGeek")
