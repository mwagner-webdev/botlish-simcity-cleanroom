#!/usr/bin/env python3
"""Drop duplicate top-level definitions from a Botlish module, keeping the
last written one, and drop stray `# ---` section banners.

Usage: tools/dedupe.py FILE.bot
"""
import re
import sys

HEAD = re.compile(
    r"^(?:private )?(?:nomethod )?fn |^struct |^opaque struct |^enum |^type |^direct module "
)
CONST = re.compile(r"^[A-Z][A-Z0-9_]*\s*=")


def is_head(line):
    return bool(HEAD.match(line) or CONST.match(line))


def main():
    path = sys.argv[1]
    lines = open(path).read().split("\n")
    starts = [i for i, l in enumerate(lines) if is_head(l)]
    if not starts:
        return
    first = starts[0]
    head = lines[:first]
    # (signature -> body-with-doc), last written wins.
    best = {}
    order = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = lines[start:end]
        while len(body) > 1 and body[-1].strip() == "":
            body.pop()
        while len(body) > 1 and body[-1].lstrip().startswith("#"):
            body.pop()
        sig = lines[start]
        doc = []
        j = start - 1
        while j >= 0 and (lines[j].startswith("#") or lines[j].strip() == ""):
            doc.append(lines[j])
            j -= 1
        doc.reverse()
        doc = [l for l in doc if l.startswith("#") and not l.startswith("# ---")]
        entry = ("\n".join(doc) + "\n" if doc else "") + "\n".join(body).rstrip("\n")
        if sig not in best:
            order.append(sig)
        best[sig] = (start, entry)
    # Emit in the written order of first appearance, with each definition
    # where it last stood.
    placed = sorted(best.values(), key=lambda e: e[0])
    out = list(head)
    for start, entry in placed:
        out.append(entry)
    sys.stderr.write("dedupe %s: %d definitions\n" % (path, len(placed)))
    open(path, "w").write("\n\n".join(x.rstrip("\n") for x in out) + "\n")


if __name__ == "__main__":
    main()
