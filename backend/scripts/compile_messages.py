"""Compile locale/*/LC_MESSAGES/django.po to .mo without GNU gettext.

Fallback for machines without ``msgfmt`` (used by ``make compilemessages``).
Supports plain msgid/msgstr entries (no plurals, no msgctxt).
"""

import ast
import struct
import sys
from pathlib import Path


def parse_po(text):
    entries, field, cur = {}, None, {"msgid": "", "msgstr": ""}

    def flush():
        if cur["msgid"] or cur.get("seen"):
            entries[cur["msgid"]] = cur["msgstr"]

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#") or not line:
            if not line and cur.get("seen"):
                flush()
                cur = {"msgid": "", "msgstr": ""}
                field = None
            continue
        if line.startswith("msgid "):
            if cur.get("seen") and field == "msgstr":
                flush()
                cur = {"msgid": "", "msgstr": ""}
            field, cur["seen"] = "msgid", True
            cur["msgid"] = ast.literal_eval(line[6:])
        elif line.startswith("msgstr "):
            field = "msgstr"
            cur["msgstr"] = ast.literal_eval(line[7:])
        elif line.startswith('"') and field:
            cur[field] += ast.literal_eval(line)
    if cur.get("seen"):
        flush()
    return {k: v for k, v in entries.items() if v or k == ""}


def write_mo(entries, path):
    keys = sorted(entries)
    ids = b""
    strs = b""
    offsets = []
    for k in keys:
        kb, vb = k.encode("utf-8"), entries[k].encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\0"
        strs += vb + b"\0"
    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    out = struct.pack("Iiiiiii", 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
    out += b"".join(struct.pack("ii", o[1], keystart + o[0]) for o in offsets)
    out += b"".join(struct.pack("ii", o[3], valuestart + o[2]) for o in offsets)
    path.write_bytes(out + ids + strs)


def main(root):
    for po in Path(root).glob("*/LC_MESSAGES/django.po"):
        write_mo(parse_po(po.read_text(encoding="utf-8")), po.with_suffix(".mo"))
        print(f"compiled {po}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "locale")
