"""Machine-readable site glossary: rules/sanasto.yaml -> request translation.

rules/preferences.md explains the words to people. This file makes the same
words work without anybody reading anything: price_bom.py and find.py
translate a request through it before searching, so "6 mmj" prices as
MMJ 5x6 on every machine, not only where the model happened to read the
prose carefully.

The file is a flat `"word": "target"` map. It is valid YAML, but it is read
here with a regex so the query side stays standard library only and needs no
build step -- a word committed by one buyer works for the next one on pull.

  key     lowercase, may hold one {n} placeholder for a number ("{n} mmj")
  target  what to search instead: a sähkönumero, several joined with | when
          the same product has different codes per supplier, a cable spec,
          or plain search words. {n} is carried over.
"""
import os
import re

from . import paths

ROOT = paths.ROOT
PATH = paths.SANASTO[0]

LINE_RE = re.compile(r'^\s*"([^"]+)"\s*:\s*"([^"]*)"\s*(?:#.*)?$')
NUM = r"(?P<n>\d+(?:[.,]\d+)?)"
_cache = {}


def _norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def parse(text):
    """-> [(compiled key, target, key as written)]. A bad line is an error:
    a glossary line that silently does nothing is a word nobody taught."""
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            raise ValueError(
                f'sanasto.yaml line {no}: expected "word": "target", got {line!r}')
        key, target = _norm(m.group(1)), m.group(2).strip()
        pat = re.escape(key).replace(re.escape("{n}"), NUM)
        out.append((re.compile(pat), target, key))
    return out


def load(path=None):
    """One file, or with no argument every glossary in paths.SANASTO in order
    (organisation first, then the plugin's general slang)."""
    if path is None:
        return [e for p in paths.SANASTO for e in load(p)]
    if not os.path.exists(path):
        return []
    stamp = os.path.getmtime(path)
    if _cache.get(path, (None,))[0] != stamp:
        with open(path, encoding="utf-8") as fh:
            _cache[path] = (stamp, parse(fh.read()))
    return _cache[path][1]


CODE_RE = re.compile(r"^(?=.*\d)[0-9A-Za-z]{5,14}$")
NUMBER_RE = re.compile(r"^\d+(?:[.,]\d+)?$")


def _is_code(target):
    """A target that names exact products (sähkönumero, EAN, supplier code)."""
    return all(CODE_RE.match(p.strip()) for p in target.split("|") if p.strip())


def _loose(q, key):
    """Match the key's words anywhere in the request, in any order: "vipuwago
    3" for "3 vipuwago", "6 mmj PK" for "{n} mmj". -> (n, leftover words in
    request order) or None. {n} takes a plain number not used by a word."""
    words = q.split()
    used = [False] * len(words)
    n = None
    for tok in key.split():
        if tok == "{n}":
            continue
        for i, w in enumerate(words):
            if not used[i] and w == tok:
                used[i] = True
                break
        else:
            return None
    if "{n}" in key.split():
        for i, w in enumerate(words):
            if not used[i] and NUMBER_RE.match(w):
                used[i], n = True, w
                break
        else:
            return None
    elif "{n}" in key:                  # "{n}mm lerppaputki": glued, whole line only
        return None
    return n, [w for i, w in enumerate(words) if not used[i]]


def translate(request, entries):
    """-> (target, key) for the glossary entry the request means, else None.

    1. the whole request is the word ("6 mmj")
    2. the words in another order, nothing else ("vipuwago 3")
    3. the word plus more ("6 mmj PK"): the rest is kept and searched with
       the target -- not for a target that names exact products, where
       "kuppi kansi" must not become the box itself.
    Until 12.10.2026 only 1 existed: "6 mmj PK" fell through to free text
    and priced MMJ 3x1,5, "vipuwago 3" a plastic door."""
    q = _norm(request)
    for pat, target, key in entries:
        m = pat.fullmatch(q)
        if m:
            n = (m.groupdict().get("n") or "").replace(",", ".")
            return target.replace("{n}", n), key
    best = None
    for _pat, target, key in entries:
        got = _loose(q, key)
        if got is None:
            continue
        n, rest = got
        if rest and _is_code(target):
            continue
        # the most specific word wins: "iso musta nippari" over "nippari"
        score = (not rest, len(key.split()))
        if best is None or score > best[0]:
            best = (score, target, key, n, rest)
    if best is None:
        return None
    _score, target, key, n, rest = best
    target = target.replace("{n}", (n or "").replace(",", "."))
    if rest:
        # a size the buyer said beats the glossary's default size
        if "{n}" not in key and any(NUMBER_RE.match(w) for w in rest):
            target = " ".join(w for w in target.split() if not NUMBER_RE.match(w))
        target = " | ".join(f"{p.strip()} {' '.join(rest)}" for p in target.split("|"))
    return target, key
