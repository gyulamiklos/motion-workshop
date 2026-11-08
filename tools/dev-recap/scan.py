"""Scan the text a recap will put on screen or say out loud, before building it.

Usage: python3 -I tools/dev-recap/scan.py <recap.json> [private-terms.txt]
Flags e-mail addresses, URLs and hosts, IP addresses, key-like strings, the em dash (BRAND.md bans it),
and every term from the optional private-terms file (one per line: customer names, internal hosts...).
Exit code 1 when something is found; a hit is fixed in recap.json or, when it was asked for, accepted.
"""
import json
import re
import sys

PATTERNS = {
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "url/host": re.compile(r"https?://\S+|\b[\w-]+\.(?:hu|com|io|app|dev|net|org|cloud)\b(?:/\S*)?", re.I),
    "ip": re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    "key-like": re.compile(r"\b(?=[A-Za-z0-9_-]{24,}\b)(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9_-]+\b"),
    "em dash": re.compile("—"),
}


def strings(node, path=""):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in ("sources", "left_out", "period"):  # notes for the maker, never rendered
                continue
            yield from strings(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from strings(v, f"{path}[{i}]")


def main() -> int:
    recap = json.load(open(sys.argv[1], encoding="utf-8"))
    terms = []
    if len(sys.argv) > 2:
        terms = [t.strip() for t in open(sys.argv[2], encoding="utf-8") if t.strip() and not t.startswith("#")]
    hits = 0
    for path, text in strings(recap):
        for name, rx in PATTERNS.items():
            for m in rx.finditer(text):
                print(f"{name:9} {path}: {m.group(0)!r}")
                hits += 1
        for term in terms:
            if term.lower() in text.lower():
                print(f"{'private':9} {path}: {term!r}")
                hits += 1
    print(f"{hits} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
