<div align="center">

<img src="icons/lingogeek-256.png" alt="LingoGeek logo" width="96" height="96">

# LingoGeek

**Translate a document on your own machine. No account, no character limit, nothing uploaded.**

[![Build](https://github.com/techygeekshome/LingoGeek/actions/workflows/build-windows.yml/badge.svg)](https://github.com/techygeekshome/LingoGeek/actions/workflows/build-windows.yml)
[![Version](https://img.shields.io/github/v/release/techygeekshome/LingoGeek?label=version&color=4c9bff)](https://github.com/techygeekshome/LingoGeek/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078d4)](#download)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue)](LICENSE)
[![Made by TechyGeeksHome](https://img.shields.io/badge/made%20by-TechyGeeksHome-b191f2)](https://techygeekshome.info)
[![Support on Ko-fi](https://img.shields.io/badge/support-Ko--fi-ff5e5b)](https://ko-fi.com/techygeekshome)

[Download](#download) · [What it does](#what-it-does) · [Formats](#what-it-does-with-each-kind-of-file) · [Languages](#languages) · [Requirements](#requirements)

</div>

## 🎬 See it in action

[![LingoGeek demo video](https://img.youtube.com/vi/hOF9UWpFFd8/maxresdefault.jpg)](https://www.youtube.com/watch?v=hOF9UWpFFd8)

A whole document translated, start to finish, in under a minute.

---

## Why it exists

DeepL's free tier allows **one document translation per month**, up to 5 MB. A second costs
$8.74 a month. Every other free route asks you to upload the file to somebody's server, which is
exactly what you cannot do with a contract, a medical letter, an HR file or anything under an NDA.

The translation models are free and openly licensed. The thing that did not exist was a Windows
app that puts one in front of you without a meter attached. That is all LingoGeek is.

## What it does

- Translates **Word documents, PDFs, subtitle files, Markdown and plain text**
- Runs entirely on this machine once a language pack is downloaded
- Writes a **new file beside the original**, never over it
- **No account, no sign-up, no character allowance, no watermark**
- Free at home and at work

## What it does with each kind of file

| Format | What happens |
|---|---|
| **Word (.docx)** | Headings, lists, tables, headers and footers keep their place. Formatting that changes part way through a sentence does not survive, because translation moves the words. The app says how many paragraphs that affected. |
| **PDF** | Read as text, written out as a Word document. A PDF's layout cannot be rebuilt around text that is now a different length, and pretending otherwise produces a mess. Scanned PDFs need OCR first, and LingoGeek says so rather than producing an empty file. |
| **Subtitles (.srt, .vtt)** | Only the spoken lines change. Timings and cue numbers are copied through exactly. |
| **Text and Markdown** | Paragraph breaks are kept as they were. |

## Languages

Around 100 language pairs, from the openly licensed Argos and OPUS-MT collection. A pair is
downloaded once, the first time you use it, and works offline from then on. Packs are roughly
40 to 80 MB each and live in `%LOCALAPPDATA%\TechyGeeksHome\LingoGeek`, where you can delete any
you no longer want.

## Honest limits

- **Machine translation, not a translator.** It is good, and on plain prose it is very good. It is
  not a human being and it should not be the last word on anything that matters legally.
- **No voice, no images, no scanned text.** Text in pictures is not touched.
- **Formatting inside a sentence is lost**, as described above. Structure is not.

## Requirements

Windows 10 or 11, 64-bit. It installs for the current user, so no administrator password is
needed. Nothing else to install first, and no internet connection is needed except to fetch a
language pack the first time you use it.

## Download

Grab the installer from the [latest release](https://github.com/techygeekshome/LingoGeek/releases/latest).

## Running from source

```
pip install -r requirements.txt
python desktop.py
```

## Built on

[CTranslate2](https://github.com/OpenNMT/CTranslate2) and
[SentencePiece](https://github.com/google/sentencepiece) for the translation itself, with language
packs from the [Argos](https://github.com/argosopentech/argos-translate) collection. Argos itself is
not a dependency: it requires stanza, which requires torch, which is about 2.5 GB for the sake of
deciding where sentences end. LingoGeek does that part itself.

## Support

LingoGeek is free and always will be. If it saved you a subscription, you can
[buy us a coffee on Ko-fi](https://ko-fi.com/techygeekshome). Welcome, but never expected.

## Licence

GPL-3.0. Free for everyone, including commercial use.

---

<div align="center">
Made by <a href="https://techygeekshome.info">TechyGeeksHome</a>
</div>
