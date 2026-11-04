# Two helpers used while writing the sources

Both are ordinary Python: they are not part of building or running the game,
they only rearranged Botlish sources while they were being written.

* `order.py FILE.bot` writes a module's top-level definitions in the order
  Botlish requires (a name is visible only after its definition), keeping the
  doc-comment above each. Used on the modules; the committed order is the
  result.
* `dedupe.py FILE.bot` removes a duplicate top-level definition, keeping the
  last written one. Used after the reorder tool had left duplicates behind in
  an earlier draft.

Neither is needed again unless a module is edited heavily.
