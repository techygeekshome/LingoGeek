"""Local translation, on this machine, with no account and no metering.

The models are the Argos/OPUS-MT packages published at argos-net.com. Each one
is a zip holding a CTranslate2 model and a SentencePiece vocabulary, so the two
of those are the only runtime dependencies. Argos itself is not installed
because it pulls in stanza, and stanza pulls in torch.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .sentences import split as split_sentences

INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"

# Some of the hosts serving the language packs reject urllib's default agent
# outright with a 403, so every request this module makes sends a real one.
USER_AGENT = "LingoGeek/1.0 (+https://techygeekshome.info/lingogeek/)"


def _open(url: str, timeout: int):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=timeout)

# One marker sentencepiece uses for a word boundary. Decoding by hand is
# deliberate: SentencePieceProcessor.decode leaves these in when it is handed
# pieces that came back from CTranslate2 rather than from its own encoder.
_WORD_BOUNDARY = "▁"


def data_root() -> Path:
    """Where models and the index live. Per user, never in Program Files."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share")
    p = Path(base) / "TechyGeeksHome" / "LingoGeek"
    p.mkdir(parents=True, exist_ok=True)
    return p


@dataclass(frozen=True)
class LanguagePair:
    from_code: str
    from_name: str
    to_code: str
    to_name: str
    url: str
    code: str

    @property
    def key(self) -> str:
        return f"{self.from_code}-{self.to_code}"


class ModelStore:
    """Downloads and unpacks language packs, and says what is already here."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or data_root()
        self.models = self.root / "models"
        self.models.mkdir(parents=True, exist_ok=True)
        self._index: list[LanguagePair] | None = None
        self._lock = threading.Lock()

    # -- the catalogue ----------------------------------------------------
    def index(self, refresh: bool = False) -> list[LanguagePair]:
        cached = self.root / "index.json"
        if self._index is not None and not refresh:
            return self._index
        raw: list[dict] | None = None
        if cached.exists() and not refresh:
            try:
                raw = json.loads(cached.read_text(encoding="utf-8"))
            except Exception:
                raw = None
        if raw is None:
            with _open(INDEX_URL, timeout=30) as r:
                raw = json.loads(r.read().decode("utf-8"))
            cached.write_text(json.dumps(raw), encoding="utf-8")
        pairs = [
            LanguagePair(
                p["from_code"], p["from_name"], p["to_code"], p["to_name"],
                p["links"][0], p["code"],
            )
            for p in raw
            if p.get("links")
        ]
        pairs.sort(key=lambda p: (p.from_name, p.to_name))
        self._index = pairs
        return pairs

    def installed(self) -> set[str]:
        return {d.name for d in self.models.iterdir() if (d / "model" / "model.bin").exists()}

    def path_for(self, key: str) -> Path | None:
        d = self.models / key
        return d if (d / "model" / "model.bin").exists() else None

    # -- getting one ------------------------------------------------------
    def install(self, pair: LanguagePair, progress=None) -> Path:
        """Download and unpack one language pack. Returns its folder."""
        target = self.models / pair.key
        if (target / "model" / "model.bin").exists():
            return target

        tmp = self.models / (pair.key + ".part")
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        archive = tmp / "pack.zip"

        with _open(pair.url, timeout=120) as r:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            with open(archive, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if progress:
                        progress(done, total)

        with zipfile.ZipFile(archive) as z:
            # The stanza folder is never used and is a third of the download.
            names = [n for n in z.namelist() if "/stanza/" not in n]
            z.extractall(tmp, members=names)
        archive.unlink(missing_ok=True)

        inner = next((d for d in tmp.iterdir() if d.is_dir()), None)
        if inner is None or not (inner / "model" / "model.bin").exists():
            shutil.rmtree(tmp, ignore_errors=True)
            raise RuntimeError(f"{pair.key}: the language pack did not contain a model")

        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        inner.rename(target)
        shutil.rmtree(tmp, ignore_errors=True)
        return target

    def remove(self, key: str) -> bool:
        d = self.models / key
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            return True
        return False

    def size_on_disk(self) -> int:
        return sum(f.stat().st_size for f in self.models.rglob("*") if f.is_file())


class Translator:
    """One loaded language pair. Loading is lazy and cached per process."""

    _cache: dict[str, "Translator"] = {}
    _cache_lock = threading.Lock()

    def __init__(self, folder: Path) -> None:
        import ctranslate2
        import sentencepiece as spm

        self.folder = folder
        self._sp = spm.SentencePieceProcessor(model_file=str(folder / "sentencepiece.model"))
        self._ct = ctranslate2.Translator(
            str(folder / "model"),
            device="cpu",
            compute_type="int8",
            inter_threads=1,
            intra_threads=max(1, (os.cpu_count() or 4) // 2),
        )

    @classmethod
    def load(cls, folder: Path) -> "Translator":
        key = str(folder)
        with cls._cache_lock:
            t = cls._cache.get(key)
            if t is None:
                t = cls(folder)
                cls._cache[key] = t
            return t

    @staticmethod
    def _detokenise(pieces: list[str]) -> str:
        return "".join(pieces).replace(_WORD_BOUNDARY, " ").strip()

    def translate_sentences(self, sentences: list[str], beam_size: int = 4) -> list[str]:
        if not sentences:
            return []
        tokens = [self._sp.encode(s, out_type=str) for s in sentences]
        results = self._ct.translate_batch(
            tokens, beam_size=beam_size, max_batch_size=16, replace_unknowns=True
        )
        return [self._detokenise(r.hypotheses[0]) for r in results]

    def translate_block(self, text: str, beam_size: int = 4) -> str:
        """Translate a paragraph, preserving its leading and trailing space."""
        if not text or not text.strip():
            return text
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        sentences = split_sentences(text)
        done = self.translate_sentences(sentences, beam_size=beam_size)
        return lead + " ".join(done) + trail
