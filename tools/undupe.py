#!/usr/bin/env python3
"""Clean the duplicated comment debris out of the Botlish sources.

An earlier reordering tool ran over these files more than once and each pass
repeated the comment it was moving, so the sources carry runs of the same
comment line, or the same comment block, repeated 2, 4, 8, 16 ... times with a
blank line between the copies. The module headers have every line separated by
a blank for the same reason. None of it means anything: the intent is one copy
of each comment where it was first written.

A *run* is a maximal span of comment lines and blank lines. A run is debris
when either

  * a comment line in it appears more than once -- the repeated block; or
  * every comment line in it is followed by a blank line -- the module header
    that was duplicated line by line.

A run that is neither is left exactly as it was, because a blank line between
two comments that are not the same is a paragraph break somebody wrote.

A debris run is rebuilt: duplicated comment lines collapse to one, duplicated
paragraphs collapse to one (a paragraph is the text between bare "#"
separators), and the blank lines that sat between the copies go. One blank line
is left after the run when the original had one, so the code that follows is
not jammed against the comment.

A repeated comment separated by *code* is not a run and stays, so two sections
that legitimately share a name both remain.

Usage: tools/undupe.py FILE.bot [...]
"""
import sys

BARE = "#"


def is_comment(line):
    return line.lstrip().startswith("#")


def texts_of(run):
    """The comment lines of a run, blanks dropped."""
    return [l for l in run if is_comment(l)]


def debris(run):
    texts = texts_of(run)
    body = [t for t in texts if t.strip() != BARE]
    if len(body) != len(set(body)):
        return True
    # every comment line followed by a blank line
    i = 0
    while i < len(run):
        if is_comment(run[i]):
            if i + 1 >= len(run) or run[i + 1].strip() != "":
                return False
        i += 1
    return len(texts) > 1


def paragraphs(texts):
    out = [[]]
    for line in texts:
        if line.strip() == BARE:
            out.append([])
        else:
            out[-1].append(line)
    return [p for p in out if p]


def collapse_lines(texts):
    """Runs of the same comment line to one; a bare separator is a paragraph
    break and is kept."""
    out = []
    for line in texts:
        if line.strip() == BARE:
            out.append(line)
        elif out and out[-1] == line:
            continue
        else:
            out.append(line)
    return out


def reduce_prefix(lines):
    """A run whose first block repeats, reduced to that block and its tail.

    The debris repeats whole blocks -- a section header, a `#`, four lines of
    explanation, then the same header and the same four lines -- so the flat list
    of comment lines has a prefix that recurs. What was written is one copy of
    that prefix plus whatever followed it, which for a block repeated twice is
    the documentation of the function the block sits above.
    """
    n = len(lines)
    for size in range(1, n // 2 + 1):
        reps = 1
        while lines[size * reps:size * (reps + 1)] == lines[:size]:
            reps += 1
        if reps >= 2:
            return lines[:size] + lines[size * reps:]
    return lines


def rebuild(run):
    texts = collapse_lines(texts_of(run))
    texts = reduce_prefix(texts)
    kept = []
    for para in paragraphs(texts):
        if kept and kept[-1] == para:
            continue
        kept.append(para)
    out = []
    for n, para in enumerate(kept):
        if n:
            out.append(BARE)
        out.extend(para)
    if run and run[-1].strip() == "":
        out.append("")
    return out


def clean(text):
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if is_comment(lines[i]) or lines[i].strip() == "":
            j = i
            while j < len(lines) and (is_comment(lines[j]) or lines[j].strip() == ""):
                j += 1
            run = lines[i:j]
            if any(is_comment(l) for l in run) and debris(run):
                out.extend(rebuild(run))
            else:
                out.extend(run)
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def main():
    for path in sys.argv[1:]:
        text = open(path).read()
        fixed = clean(text)
        if fixed != text:
            open(path, "w").write(fixed)
            sys.stderr.write("cleaned %s\n" % path)
        else:
            sys.stderr.write("unchanged %s\n" % path)


if __name__ == "__main__":
    main()
