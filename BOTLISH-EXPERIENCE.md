# Botlish, for a real program

What writing a playable SimCity clone in Botlish was like, and what the language
and its toolchain are good and bad at. Every claim below is either a compiler
diagnostic that was printed, a measurement that was taken, or a piece of the
program that exists. Where something is a matter of taste I say so.

## 1. What the language is

Botlish looks like Python and is not. It is indentation-structured, immutable
by default, and statically checked in a way that caught several real mistakes.
The nine things I had to unlearn, in the order I met them:

1. **`for` is `loop`.** `loop x in xs:` collects a List; `loop i from 0 to n:`
   counts.
2. **No assignment.** `x = x + 1` in a loop binds a new name in the loop body
   and leaves the outer one alone. There is no `+=`, no field assignment, and no
   element assignment. The ways to keep a running value are a fold, a parameter
   passed on, a collecting loop, or a mutable collection.
3. **A function's own state is not mutable.** A struct's fields cannot be
   assigned. A mutable struct is a struct of `MutableArray`s, `MutableVector`s
   and `MutableMap`s, and those are mutated through *places*.
4. **Callees before callers.** No hoisting. This is the one that shaped the
   source files most: every file reads helpers-then-caller.
5. **There is no integer division.** `/` is Float64 only; there is no `%` and no
   integer-division function. `mod` exists, and shifts divide by powers of two.
6. **A loop is never an operand.** A loop or an `if` is a value only as the
   whole right side of `=` or of `return`, or a body's last expression. Bind it
   to a name first.
7. **`mutual recursion is not supported.** Two functions cannot call each other.
8. **A list is built with one literal or one collecting loop.** There is no cons,
   no append and no concatenation. This shapes every function that builds a
   pixel list.
9. **One character is `'x'`, not `"x"`**, and `"x"` is a warning.

## 2. The type system

The strongest thing about Botlish is that a *declared* type is a contract the
compiler must prove at each use, not an annotation. Three moments where it saved
me:

* The compiler proved my out-of-range array accesses impossible, or made me guard
  them. In the model I wrote every accessor with a bounds guard so that `at` and
  `set` cannot fail, and after that nothing in the simulation carries
  `IndexNotFound`. A test case could then be one plain expression rather than a
  pile of handlers. That was the single highest-leverage decision of the whole
  project.
* `equality` on a collection is a compile error, not a surprise. I wrote
  `if placed == city` to detect a placement that did nothing, and the compiler
  said `EQUALITY` because a `MutableArray` has no `==`. It was right: a city is
  its arrays, and the question I wanted to ask was "did it fit?", which is
  `simcity::actions::fits`. Two language facts made me write the correct code.
* `Reads` of a struct's field out of a `place` are refused with
  `AFFINE-FIELD-MOVE-REQUIRES-DESTRUCTURE` and `AFFINE-TEMPORARY-UNSUPPORTED`.
  Those messages are long and pedantic, but they name the exact operation.

The weakest thing is that the *proofs* are shape-sensitive: the compiler accepts
`if i < 0 or i >= xs.length(): return ...` followed by `xs.at(i)`, and rejects
the same check written as two nested `if`s, or with the bounds computed in a
different order. I lost time to this repeatedly, and the workaround is always
"rewrite the guard in the one recognised form". It is not guesswork -- the
message names `-help proof.list-bounds` -- but the shape it wants is narrow and
discovering it means trying forms.

## 3. Mutable state, and the shape that emerged

An early draft held the city as an ordinary Python-style object with fields. That
does not compile: field assignment does not exist. There was exactly one
representation that worked, and the compiler's own diagnostics led me to it:

```
struct City:
    width: int          # fixed
    height: int         # fixed
    grid: Grid          # one MutableArray per tile attribute
    bank: MutableArray[int]  # one slot per number that changes
```

`Grid` is fifteen arrays, one per tile attribute, indexed `y * width + x`. A
month takes a city, mutates its grid through a `place city` parameter, and returns
a *new* `City` holding the new scalars, because the arrays are shared and so
building a city is a handful of integers rather than a copy of the map.

Three things followed from that, none of them planned:

* **Update-one-field is expensive.** With no field assignment, a change is a new
  `State { ...eleven fields... }` literal. `simcity/app.bot` pays it in ten places.
  It is explicit and easy to read, and it is the most verbose thing in the
  program. A record-update operator would remove it entirely. This is my
  strongest ergonomic finding.
* **Writing through a copy is silently lost.** I wrote `fn put(field: MutableArray[int], i, v)` and called it with a grid's field, and the write went into the callee's own
  copy. The same trap caught `std::mutable_array::copy` (the *destination* must
  be a place, not a parameter) and `std::mutable_array::set` from a module that
  imports `std::byte`. In each case the compiler said exactly why, and in each
  case the fix was one word (`place`). But the failure mode -- a write that is
  silently dropped -- is the worst one a language can have, and it is reachable
  from an entirely natural-looking program.
* **`MutableArray` beat `MutableVector` for the game's state.** Its indexed
  bounds are provable by a capacity guard; a `MutableVector`'s `at` declares
  `IndexNotFound` and the compiler does not prove its indices, so every read
  would have carried a handler. For a fixed-size grid that decided it.

## 4. The frame loop and Raven

Raven's own event model cannot see the map: the package's bridge watches named
widget kinds, and the map is a texture. So `simcity/app.bot` polls the window
directly through the generated binding (`Rwindow_get_mouse_position`,
`Rwindow_is_mouse_button_down`), reading a C float into this program's own
native memory. That needed raw authority, so the `screen` module declares a
context of its own (`Screen`) and the entry program installs it -- exactly as
Raven's own `raven.bot` installs `Ui`. The whole raw layer of the game is one
module and one context, which is what the design asks for and is easy to point at
in review.

The frame loop itself is plain recursion over a state value, which the native
backends run as a loop. Nothing was awkward here.

## 5. What the toolchain did well

* **Compilerpedia is genuinely good.** `-help` is a topic search over 1169 pages:
rules, diagnostics, standard-library symbols, backend facts. `-help proof.list-bounds`
and `-help std::mutable_array::copy` answered the two questions I asked most.
  The concept pages carry a "WHY" that is usually the actual design rationale.
* **The warnings are a lint with a policy.** `METHOD-ELIGIBLE`, `ONE-CHAR-STRING-LITERAL`,
  `SAME-RETURN-VALUE` named habits and I fixed them in one pass. Every warning is
  followed by a `help:` line with the topic that explains it.
* **`std::test` is ordinary Botlish.** No framework, no import of a test DSL:
  `with context std::test::suite()`, register, `report()`. A test body may not
  declare an error other than `CompilerError`, which is precisely what pushed me
  to make the model's accessors total. The design of the test framework changed
  the design of the program, for the better.
* **`-check` reports diagnostics without running.** With a program that opens a
  window that is not worth it.

## 6. What the toolchain did badly

* **The package manager's view layout is undocumented-in-the-package.** A package
  is at `.bot_modules/.targets/TARGET/NAME/NAME.bot`, and the namespace is the
  *package's root* `NAME`, so the module file for `raven` is
  `.bot_modules/raven/targets/linux-x86_64/raven/raven.bot`. I found that by
  listing files, not by reading anything.
* **There is no integer division and no `usize`-to-`int` bridge.** A loop over a
  48 by 48 map needs `i / width`, so the simulation carries a 32-step restoring
  division (`div_bits`) that is used on every tile. A library `div` would remove
  ~15 lines and one call from every hot loop.
* **No cons, no append, no concatenation.** Every function that builds a list of
  tiles is a nested collecting loop. `simcity/render.bot`'s `frame` is two loops
  deep for this reason. It is workable and it is the least pleasant part of
  writing the renderer.
* **Module-level constants cannot be structs.** `Colour` as a struct could not
  be bound at module scope (`MODULE-CONTEXT: unsupported initializer expression
  struct`), so the renderer packs a colour into an integer and takes it apart
  with masks. That is a workaround for a restriction I could not find documented
  anywhere.
* **The compiler's `errors` clauses are viral and verbose.** A function that
  calls `NonFiniteFloat` must declare it; its caller then must declare it, and so
  on to the top. `simcity/app.bot` declares `NonFiniteFloat` in seven places
  because Raven reports a float somewhere near the top. There is no way to
  convert one error into another at a boundary except by handling it there.
* **`compilerpedia` does not know a project's own symbols.** `-help simcity::sim::tick`
  answers "no Compilerpedia topic matches". For a program of eleven modules that
  leaves cross-references as plain comments.
* **A module can only hold so many test cases, and nothing says where the wall
  is.** `tests.bot` has 38 cases and would not take a 39th. The compiler's
  answer is `"check_16" has typed parameter requirements that cannot be
  preserved passed as an ordinary call argument` and it names whichever case
  happens to sit at the wall, not the count that was reached. Reusing a function
  costs nothing, so 38 cases that share their checks fit and a 39th with a check
  of its own does not; splitting the registration across two functions does not
  help either, because the budget is the module's. The fix is what any test file
  eventually does anyway: `labels.bot` is the renderer's own suite, and it holds
  6 cases with room to spare. I found the wall by walking into it.
* **A loop's bounds are exclusive of the upper number, and nothing says so.**
  `loop i from 0 to 1000` runs 1000 times, which is what a reader expects, but
  the frame renderer's `loop py from 0 to TILE * down` is what a reader does not
  expect: it produces `TILE * down` rows, and the texture is uploaded at
  `4 * width * height` bytes, so the two only agree because the reader guessed
  right. A sentence in the guide would have saved the guessing.
* **`std::str::length` is not `List::length`.** `pixels.length()` on a list
  answers a type error naming `std::str::length`, and the list's own measure is
  `std::list::length(pixels)`. Two functions with the same name and neither is
  the one a reader reaches for first.

## 7. The bug that reads like a language bug and is not

The worst defect of the whole session was one line:

```
raven::window::Rwindow_get_mouse_position(window.id, cell.xy, cell.xy)
```

`Rwindow_get_mouse_position` takes two out-parameters. A C pointer in Botlish
is affine and has no arithmetic, so the pair cannot be one stepped pointer --
but passing one address for both is a perfectly legal call, and Raven then
wrote the mouse's y over its x and left the second slot untouched. The game
read `(y, 0)` and the cursor could only ever travel along the map's diagonal:
every position off that line was unreachable. Nothing in the compiler objected,
because the call was well typed.

The fix was two separate one-float cells, and the shape of the fix is worth
recording: the module now allocates two pointers and the context's `Cell` holds
both, because the discharge is a memory fact and not a type fact. A `Ptr[Float]`
and a `Ptr[Void]` re-typed are indistinguishable to the type system.

The second bug was mine and not the language's: `Tool::Inspect` was passed to
`simcity::actions::place`, which only knows line tools, zone tools and the
bulldozer. The inspect tool fell through to the zone branch and was refused.
A sum type over the tools would have made that a compile error; an enum with a
`None` case that `kind_of` answers `0` for cannot. That is a real cost of
enums-as-ints here, and the honest fix was to branch on the tool in the input
layer rather than to overload the model with a tool it does not place.

## 8. What the compiler made me do that was right

* Make every accessor total, by guarding an index against its array's
  capacity. That is what let the tests become plain expressions.
* Rewrite the sweep direction, because propagation over a tile list advances
  one tile per pass. Measured: 47 s to 19 s over 1000 months.
* Replace positional lists of six figures with a struct, because
  `FIXED-ARITY-LIST-RETURN` said a reader should not count positions.

## 9. The one thing I would change first

Update-one-field. A record-update expression (`game{message: text}`) would remove
the most verbose code in the program, remove the temptation to hold it in a
mutable one-slot array, and make the frame loop shorter.

The second is integer division.

The third is a way to say, in a type, that two C pointers are not one: a
`Ptr[Float]` pair stepped through one allocation is a memory fact the type
system cannot see, and the bug in section 7 was exactly a well-typed call.

## 10. Things I am not calling defects

* Rejection of my first, invalid programs: those were my errors.
* `NATIVE-ONLY` for `interp` on a C call: documented, and correct.
* The verbosity of error clauses: the design is deliberate and the compile-time
  checking is real.
* The `SAME-RETURN-VALUE` and `METHOD-ELIGIBLE` warnings: both are style and
  both are suppressed by writing the style, so they cost nothing in the end.

## 11. Numbers from this session

| measurement | value |
|---|---|
| lines of Botlish in `simcity/` and the five entry programs | about 3,700 |
| modules | 11 |
| first working headless simulation | the afternoon of day one |
| the whole simulation, once the sweep direction was fixed | 21 ms a month on 48 by 48 |
| test cases | 44 (38 for the city, 6 for the map's letters), all passing |
| defects found by a test written after the fact | 2, both in the new label
  drawing: the glyph guard leaked pixels outside the letter's box, and the rows
  were read the wrong way up. Neither was visible in the headless figure, and
  both were visible the moment a case counted the pixels |
