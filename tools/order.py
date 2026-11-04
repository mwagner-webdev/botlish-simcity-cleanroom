#!/usr/bin/env python3
"""Reorder a Botlish module's top-level definitions so that each one is
declared before the first one that uses it, and give its doc-comment back to
the definition it belongs to.

Botlish has no hoisting: a name is visible only after its definition in the
same scope (concept.definition-order), and callees are written before callers.
This tool reads a module, splits it into its top-level definitions plus the
comment block immediately above each, works out which of the module's own
names each one's *code* uses (comments never count), and writes the module
back in dependency order. The sort is stable, so a file whose written order
already satisfies the rule comes back unchanged.

Usage: tools/order.py FILE.bot
"""
import re
import sys

HEAD = re.compile(
    r"^(fn |nomethod fn |private fn |private nomethod fn |struct |opaque struct |"
    r"enum |type |direct module )"
)
CONST = re.compile(r"^[A-Z][A-Z0-9_]*\s*=")

DEF = re.compile(
    r"^(?:private )?(?:nomethod )?fn (?P<fn>[A-Za-z_][A-Za-z0-9_?]*)\("
    r"|^(?:opaque )?struct (?P<struct>[A-Za-z_][A-Za-z0-9_]*):"
    r"|^enum (?P<enum>[A-Za-z_][A-Za-z0-9_]*):"
    r"|^type (?P<type>[A-Za-z_][A-Za-z0-9_]*) =",
    re.M,
)
CONST_DEF = re.compile(r"^(?P<const>[A-Z][A-Z0-9_]*)\s*=", re.M)
QUALIFIED = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*::")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_?]*")
KEYWORDS = {
    "fn", "nomethod", "private", "return", "if", "elif", "else", "and", "or",
    "not", "true", "false", "loop", "fold", "with", "intermediate", "in",
    "from", "to", "through", "down", "break", "continue", "unit", "int",
    "str", "bool", "float", "float64", "list", "errors", "place", "on",
    "fail", "context", "variadic", "import", "struct", "enum", "type",
    "direct", "module", "satisfies", "opaque", "refined",
}


def is_head(line):
    return bool(HEAD.match(line) or CONST.match(line))


def declared(block):
    out = []
    for m in DEF.finditer(block):
        out.append(
            m.group("fn") or m.group("struct") or m.group("enum") or m.group("type")
        )
    for m in CONST_DEF.finditer(block):
        if m.start() == 0:
            out.append(m.group("const"))
    return out


def uses(block):
    """The bare names this definition's code mentions; comments never count."""
    code = "\n".join(l for l in block.split("\n") if not l.lstrip().startswith("#"))
    code = QUALIFIED.sub(" ", code)
    return set(IDENT.findall(code)) - KEYWORDS


def blocks_of(text):
    """(head, [block]) with each block carrying only its own doc-comment."""
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if is_head(l)]
    if not starts:
        return text.rstrip("\n"), []
    head = "\n".join(lines[: starts[0]]).rstrip("\n")
    out = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = lines[start:end]
        # A trailing comment run belongs to the block that follows.
        while len(body) > 1 and body[-1].strip() == "":
            body.pop()
        while len(body) > 1 and body[-1].lstrip().startswith("#"):
            body.pop()
        out.append("\n".join(body).rstrip("\n"))
    return head, out


def doc_above(lines, start):
    j = start - 1
    found = []
    while j >= 0 and (lines[j].startswith("#") or lines[j].strip() == ""):
        found.append(lines[j])
        j -= 1
    found.reverse()
    while found and found[0].strip() == "":
        found.pop(0)
    kept = [l for l in found if l.startswith("#")]
    return "\n".join(kept)


def order(text):
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if is_head(l)]
    if not starts:
        return text
    head = "\n".join(lines[: starts[0]]).rstrip("\n")
    blocks = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = lines[start:end]
        while len(body) > 1 and body[-1].strip() == "":
            body.pop()
        while len(body) > 1 and body[-1].lstrip().startswith("#"):
            body.pop()
        body = "\n".join(body).rstrip("\n")
        doc = doc_above(lines, start)
        whole = (doc + "\n" if doc else "") + body
        seen_before = {b[1] for b in blocks}
        if body not in seen_before:
            blocks.append((whole, body))
    text_blocks = [b[0] for b in blocks]
    code_blocks = [b[1] for b in blocks]
    names = set()
    for b in code_blocks:
        names.update(declared(b))
    mine = [set(declared(b)) for b in code_blocks]
    need = [uses(b) for b in code_blocks]
    todo = list(range(len(code_blocks)))
    placed = []
    done = set()
    while todo:
        moved = False
        for i in list(todo):
            wants = {n for n in need[i] if n in names and n not in mine[i]}
            if wants <= done:
                placed.append(i)
                todo.remove(i)
                done |= mine[i]
                moved = True
        if not moved:
            for i in todo:
                wants = {n for n in need[i] if n in names and n not in mine[i]}
                missing = wants - done
                if missing:
                    sys.stderr.write(
                        "cannot place %s first: it needs %s\n" % (declared(code_blocks[i]), sorted(missing))
                    )
            placed.extend(todo)
            break
    ordered = [text_blocks[i] for i in placed]
    return "\n\n".join([head] + ordered) + "\n"


def main():
    path = sys.argv[1]
    text = open(path).read()
    fixed = order(text)
    if fixed != text:
        open(path, "w").write(fixed)
    sys.stderr.write("ordered %s\n" % path)


if __name__ == "__main__":
    main()
