#!/usr/bin/env python3
"""Check relative links, anchors and image paths in the repository's Markdown.

External (http/https/mailto) links are not checked. Anchors follow GitHub's
heading-slug rules, including duplicate-heading suffixes (-1, -2, ...).

Usage: python3 scripts/check-md-links.py [ROOT]
Exits non-zero when a link points at a missing file or anchor.
"""
import os
import re
import sys
import unicodedata
from urllib.parse import unquote

SKIP_DIRS = {".git", "node_modules"}
LINK_RE = re.compile(r'(!?)\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)')
HTML_RE = re.compile(r'<(?:a|img)\b[^>]*?\b(?:href|src)\s*=\s*"([^"]+)"', re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.M)


def strip_code(text):
    """Blank out fenced code blocks, keeping line numbers stable."""
    out, fence = [], None
    for line in text.split("\n"):
        m = re.match(r"^\s*(```+|~~~+)", line)
        if fence is None and m:
            fence = m.group(1)[:3]
            out.append("")
            continue
        if fence is not None:
            if re.match(r"^\s*" + re.escape(fence), line):
                fence = None
            out.append("")
            continue
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)


def slug(heading):
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    heading = heading.replace("`", "").strip().lower()
    out = []
    for ch in heading:
        cat = unicodedata.category(ch)
        if ch == " ":
            out.append("-")
        elif ch in "-_" or cat[0] in ("L", "N") or cat in ("Mn", "Mc") or ch == "️":
            out.append(ch)
    return "".join(out)


_anchor_cache = {}


def anchors(path):
    if path not in _anchor_cache:
        try:
            text = strip_code(open(path, encoding="utf-8").read())
        except OSError:
            text = ""
        seen, found = {}, set()
        for m in HEADING_RE.finditer(text):
            s = slug(m.group(2))
            if s in seen:
                seen[s] += 1
                found.add(f"{s}-{seen[s]}")
            else:
                seen[s] = 0
                found.add(s)
        found.update(re.findall(r'<a\s+(?:name|id)="([^"]+)"', text))
        _anchor_cache[path] = found
    return _anchor_cache[path]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    problems = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            body = strip_code(open(path, encoding="utf-8").read())
            targets = [(m.group(2), m.start()) for m in LINK_RE.finditer(body)]
            targets += [(m.group(1), m.start()) for m in HTML_RE.finditer(body)]
            for target, pos in targets:
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("//"):
                    continue
                file_part, _, frag = target.partition("#")
                resolved = path if not file_part else os.path.normpath(
                    os.path.join(dirpath, unquote(file_part)))
                line = body.count("\n", 0, pos) + 1
                rel = os.path.relpath(path, root)
                if not os.path.exists(resolved):
                    problems.append(f"{rel}:{line}: missing target {target}")
                elif frag and resolved.endswith(".md"):
                    if unquote(frag).lower() not in anchors(resolved):
                        problems.append(f"{rel}:{line}: missing anchor {target}")
    for p in problems:
        print(p)
    print(f"{len(problems)} broken internal link(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
