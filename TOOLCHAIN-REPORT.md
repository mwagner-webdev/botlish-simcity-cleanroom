# A report on the deficiencies of Botlish and Raven

Written after building a graphical SimCity clone in the language -- a windowed
game with a simulation, a texture the game draws itself, three headless test
suites, a deterministic benchmark and a save file. Everything below happened to
this project; every claim is something I can reproduce.

The project is in this repository: 11 modules of Botlish plus Raven, about 4,400
lines, 60 passing test cases. Nothing in this report is hypothetical.

I have ordered it by what it actually cost. Section 1 is the short list.


## 1. The short list

| # | deficiency | what it cost here |
|---|---|---|
| 1 | **The input model reports state, not events** | a $600/second treasury drain that a player found by playtesting |
| 2 | **The module wall on distinct function values** | three test files instead of one, and an error that names the wrong thing |
| 3 | **The test report cannot show a struct** | three defects found by hand because a failing case printed "a value with no text form" |
| 4 | **No file input or output** | save/load only possible because Raven happens to export file calls |
| 5 | **No integer division** | a 32-step division on every tile of every month |
| 6 | **A context-requiring function cannot be passed as a value** | one of my four test programs is not a suite |
| 7 | **No hoisting** | a helper script that reorders every file I edit |
| 8 | **The FFI's declaration rules are enforced but undiscoverable** | three separate mistakes before one file call linked |
| 9 | **`Usize`/`ULong`/`int` are three types with no conversions** | an hour of type errors over a length |
| 10 | **Error clauses are viral and cannot be converted** | `NonFiniteFloat` declared in seven places in one module |
| 11 | **No field assignment, no field chosen by a runtime value** | fifteen near-identical setters |
| 12 | **Unsuppressable style warnings** | code restructured around `SAME-RETURN-VALUE` |
| 13 | **std has no split, no parse, no trim, no interpolation** | every text format is a hand-written parser |
| 14 | **Raven has no key events, no key state query of its own, no wheel delta** | scrolling had to be built on a private-looking `Rwindow_is_key_down` |

Sections 2 to 15 take each in turn: what I hit, why it cost what it did, and what
would fix it. Section 16 lists what worked, because that is the part worth
keeping.


## 2. The input model reports state, and never reports a press

This is the one that produced a real bug in shipped behaviour.

Raven's event bridge carries twelve kinds: `Clicked`, `Toggled`,
`ValueChanged`, `TextChanged`, `TextCommitted`, `Selected`, `Action`,
`CloseRequested`, `Resized`, `TimerElapsed`, `Error`. A control that reports is
watched when it is made, and a widget Raven does not watch -- a texture, which
is what a game's map is -- reports nothing at all.

What Raven does offer is state: `Rwindow_is_mouse_button_down`,
`Rwindow_get_mouse_position`, `Rwindow_is_key_down`, `Rwindow_get_modifiers`. So
a game polls. Which is fine, until the game needs to answer "the player pressed
the button" and not "the button is down".

My first version of building did this:

    if button and inside?(city, x, y):
        place(tool, x, y)

That places on every frame the button is down. Drag to run a line works. But a
road laid on a road was also allowed -- because my crossing rule tested only the
line that may not share the tile, not the line already there -- so holding the
button still on the tile just built paid $10 a frame. **$600 a second of
standing still with the mouse down.** A player found it in minutes.

The game now derives the press: the button's state and the tile under it are
stored between frames, and a placement happens when the button has gone down or
the pointer has moved onto a tile it was not on. Dragging still runs a line a
tile at a time; resting builds nothing.

**What would fix it.** Two things, either of which would do:

* a `Pressed`/`Released` event kind in the bridge, delivered with the button and
  the widget -- which needs the map to be watchable, or a window-level key/mouse
  event anyone can subscribe to;
* or document the polling contract as the *only* input model and say plainly
  that a press must be derived, with a worked example. A game author who knows
  this once will not make my mistake.

A `Rwindow_is_key_down` and a wheel delta getter would also mean a game did not
have to build scrolling out of button-press edges.


## 3. The module wall on distinct function values passed as arguments

`tests.bot` holds 38 cases and will not take a 39th. The error is:

    "check_16" has typed parameter requirements that cannot be preserved
    passed as an ordinary call argument: its declared parameter contract
    would be erased and could no longer be checked at every future call

The number in the message is whichever case happens to sit at the wall. It is
not the count, and there is no way to ask the compiler what the count is.

I measured the real behaviour:

* reusing a function value is free -- five more registrations that share their
  checks and runs compile;
* a *new* distinct pair breaks at 38;
* splitting the registration across two or three functions does not help,
  because the budget is the module's, not the function's;
* the same wall applies to any function value, not just tests.

So a project with a naturally-growing test suite reaches a wall it cannot argue
with, and the fix is a new file. I now have `tests.bot`, `labels.bot`,
`crossings.bot` and `saves.bot` -- three of which exist because of this, not
because of what they test.

**What would fix it.** Erase the contract and say so, or explain which contract
and why it cannot be preserved. Failing that, name the wall: an error that says
"this module passes 38 distinct function values as arguments; the limit is 38"
is actionable, and an error that says "check_16 cannot be checked at every
future call" is not.


## 4. The test report cannot show a struct

`std::test::holds` takes a message, a check function and a case function, and
the case returns a struct. When the case is wrong, the report prints:

    FAIL two letters are not the same shape
      expected: fewer pixels than housing's letter, and some
      actual: a value with no text form

That is the whole diagnosis. No numbers. For `std::test::value` the same thing
happens: `actual: a value with no text form`.

Three of my defects were found by writing throwaway programs that printed the
figures a case should have shown me:

* a glyph guard that leaked pixels outside the letter's box -- the case counted
  23 ink pixels where the glyph set 14, and I only found out by hand;
* the same glyphs drawn upside down;
* a bank field one digit too short for a 32-bit generator state.

In each case the test existed and could have caught it, but I could not see
*what* was wrong, so the test was useless as a debugging tool. That is the worst
possible property for a test framework: it tells you that you are wrong and
nothing else.

**What would fix it.** Derive a text form for a struct from its fields, the way
`std::test` already does for lists and intrinsics. Failing that, let a case
answer a string, or print a caller-supplied rendering of the actual figure.


## 5. No file input or output

`std::io` is exactly four functions -- `print`, `print_line`, `write_error`,
`write_error_line` -- and one error, `WriteFailed`. Nothing reads a file and
nothing writes one. There is no `std::file`, no `std::path`, no `std::env`, no
`std::process`.

A related gap, on the tooling side rather than the library's: nothing notices a
comment that has been duplicated. My own reordering helper ran over a module
more than once and each pass repeated the comment it was moving, so
`simcity/scenario.bot` carried 63 copies of one two-line comment and
`simcity/render.bot` 32 copies of one line, with the blank lines between them.
The compiler is happy with that, the tests are happy with that, and the program
it compiles to is identical. Cleaning it up meant a script and a file-by-file
proof that the only lines removed were duplicated comments.

Save/load was possible only because Raven happens to export `Rfile_read` and
`Rfile_write` alongside its GUI, which is not where a language would put file
I/O. A console program in Botlish cannot persist anything at all.

**What would fix it.** `std::file` with read/write/append and a path type. The
standard library of a language that can call C should not be unable to write a
file.


## 6. No integer division

`/` divides `Float64` values. `int` has `.mod()` and `to_string`/`from_string`
and nothing else. So `i / width` -- a loop over a grid -- is not available, and
my simulation carries a 32-step restoring division:

    nomethod fn div_bits(a: int, b: int, rem: int, q: int, bit: int) -> int:
        if bit < 0:
            q
        else:
            here = rem.shift_left(1) + bit_and(a.shift_right(bit), 1)
            ...

It is called on every tile of every month. The benchmark says one month is 20 ms
on a 48 by 48 map, and the division is a real slice of it: `div` appears in
`simcity::sim` twice per tile per pass, in `render.bot` for every colour it packs,
and in my save codec.

**What would fix it.** `div`, `div_mod`, and a truncating `div` that answers
(-7) / 2 as -3 rather than a Float64. Fifteen lines and one call per hot loop
removed.


## 7. A context-requiring function cannot be passed as a value

    function the_file_holds_what_was_written requires context
    simcity::store::Store, so it can only be called (or bound to another name
    as a statement): it cannot be passed, returned or stored as a value,
    because a call through an unknown function value could not prove that
    context installed

The reasoning is sound. The consequence is that `std::test::holds` cannot take a
case that touches a file, or a case that draws a frame through Raven. So
`saves.bot` is not a suite -- it is a program that calls five functions and
builds its own report string. The shape of a test is the same; the runner is
mine.

**What would fix it.** A way to pass a function together with a proof its
context is installed, even a verbose one. Or accept `fn (Context) -> T` values
and call them with the ambient context at the call site.


## 8. No hoisting

A binding is visible only after it is established, with no exceptions and no
forward declarations. In a 4000-line project this is a structural tax:

* a function must be written after everything it calls, so a file is ordered by
  its call graph rather than by what a reader wants to read. `simcity/save.bot`
  currently has its fixed-width decimal helpers above the bank section above the
  tile section, because that is the only order that compiles;
* adding a helper means moving it, so every edit is a reorder;
* I shipped `tools/order.py`, a script that walks a file and moves each
  definition below its callees, and it is a real part of my development loop.

It also hid a bug for a while: an out-of-order function looked like a syntax
error, and I read it as indentation.

**What would fix it.** Hoisting of module-level definitions, at least for
functions. If that is a deliberate cost of the proof system, say so in the
guide, because it is currently undocumented.


## 9. The FFI's declaration rules are enforced but undiscoverable

Getting one file call to link took three compiler errors, each correct and each
a surprise:

1. `extern c library "raven" static` fails to link. The package's own
   declaration is bare `raven`, and there is a `libraven.so` and no
   `libraven.a`. I only found the difference by reading the error message.
2. A parameter declared `Ptr[Char] read noescape` whose function answers a
   pointer: the answer "may point into" the argument, so a temporary `Bytes`
   cannot be passed. The declaration must say `-> Ptr[Char] independent`.
3. A parameter that "may retain" a pointer needs a context struct or
   `direct module`, and the fix is the last clause of a four-clause error.

None of this is in the package's guide. Worse: the Raven package's own source
references five documents that do not ship with it:

    C-POINTER-BORROWING.md      C-BINDGEN.md
    C-BINDGEN-LAYOUTS.md        RAVEN-BINDINGS.md
    DIRECT-MODULES.md

`.bot_modules/raven/` contains `GUIDE.md` and `README.md` and nothing else. The
rules are enforced by the compiler and documented only in files that are not
there. The ownership analysis itself is excellent -- it caught a genuine double
allocation in my `store.bot` at compile time -- but I had to discover the rules
by failing three times.

**What would fix it.** Ship the five files the source already references. Put the
`direct module` escape hatch first in the error rather than last.


## 10. `Usize` and `ULong` are different types and neither converts to `int`

    std::abi::Bytes.length()       -> std::abi::Usize
    a C size_t                     -> std::ffi::c::ULong
    std::str::length(text)        -> int

Three types, no conversion between any pair, and a `Bytes`'s length is not an
`int`. `std::abi` declares only constructors (`i8`..`u64`, `usize`) -- there is
no `usize_to_int`. The way through is that `std::abi::usize` happens to accept a
`ULong`, so a length read out of native memory can go `ULong -> Usize`, and a
length the program counts itself must stay an `int`.

**What would fix it.** `usize_to_int`, `usize_to_long` and back. A length is the
most ordinary value in a program.


## 11. Error clauses are viral and cannot be converted

`NonFiniteFloat` is declared in seven places in `simcity/app.bot` because Raven
reports a float somewhere near the top of a call, and the compiler will not let
a caller swallow it. There is no `map`, no `from`, no way to say "every error
inside this call becomes my error".

The honest reading is that this is the proof system working as designed: an
error cannot be silently dropped. But there is no way to *deliberately* convert
one either, which means every module boundary either leaks another module's
error names upward or repeats a pile of inline handlers.

**What would fix it.** An operator that converts: `expr as MyError` with an
explicit list, or `expr guard MyError`.


## 12. No field assignment and no field chosen by a runtime value

Botlish structs have no field assignment. So the numbers a tick changes live in
`MutableArray`s and a field is immutable, which my `City` documents. The
consequence is `simcity::actions` has fifteen setters that are all the same
three lines, because there is no way to choose `grid.land` / `grid.zone` /
`grid.road` by a runtime value.

That is workable for a fixed set of tile attributes. It is not workable for
anything where the set is discovered at runtime, and it makes a grid-of-attributes
program -- which is most simulations -- write one function per column.

**What would fix it.** A way to name a field by a value (`fields` as a list of
accessors), or a first-class record update.


## 13. Unsuppressable style warnings

`SAME-RETURN-VALUE` and `METHOD-ELIGIBLE` cannot be suppressed, and neither can
be turned off. Both are style; both are cheap to comply with; and both restructured
my code:

* `SAME-RETURN-VALUE` forced `key_of`/`letter_of` into two functions where one
  decision would have read better, and forced `glyph`'s eight letter exits into
  one table;
* `METHOD-ELIGIBLE` forced `std::list::get(xs, i, d)` into `xs.get(i, d)` even
  where the call form is clearer, and made me wrap one-character button labels in
  a helper because `"<"` warns as a one-character string.

**What would fix it.** A suppression attribute, or an allow-list in the project
manifest. A warning the author cannot waive is an error.


## 14. No split, no parse, no trim, no interpolation

`std::str` is `append_char`, `char_at`, `concat`, `encode_utf8`, `is_tcl_alnum`,
`is_tcl_alpha`, `length`, `lowercase`, `substring`. There is no `split`, no
`trim`, no `parse_int`, no `%`-formatting, and no string interpolation.

My save format is fixed-width decimal fields *because* of this: a format a reader
can take apart by position needs no splitter. That happened to be a good property
anyway, but I chose it under constraint, not freely.

**What would fix it.** `split`, `trim`, `parse_int` returning an option, and any
form of interpolation.


## 15. Raven: no key events, no key state query of its own, no wheel delta

* the event bridge has no key kind, so a program cannot `accept` a key press;
* `Rwindow_is_key_down` exists but is not in the bridge, so reading keys is a
  raw call into `raven::window` from a module that has nothing else to do with
  it -- and it is the only reason scrolling was implementable at all;
* `Rwindow_inject_mouse_wheel` exists for tests, and there is no getter, so a
  scroll gesture cannot be read;
* a file dialog exists (`Rfile_dialog_open`/`save`) but its descriptor is an
  opaque C struct whose layout lives in another module, so a program cannot
  build one without re-declaring a C type by hand. I skipped the dialog and used
  a text field.

**What would fix it.** A `Key` event kind in the bridge, a
`Rwindow_get_wheel_delta`, and a public constructor for the file dialog.


## 16. What worked, and should not be lost

* **The totality proof.** Every accessor in `simcity::city` guards its index, and
  `proof.list-bounds` proves it. That is why the model carries no
  `IndexNotFound` at all, and a test can state a case as one plain expression.
  This is the best thing in the toolchain.
* **The ownership analysis.** `AFFINE-CONTEXT-COPY-OUT` caught a double
  allocation in my file store before it ran, and `FOREIGN-BORROW` caught a
  pointer Raven might have kept after a temporary died. The messages are long but
  they are right.
* **`-check` is separate from running.** A full check of an 11-module project is
  seconds, and it is how I worked.
* **Deterministic randomness with a documented design.** `simcity::rng` is 60
  lines and every test that needs it is deterministic.
* **The error catalogue with `-help <topic>`.** Most semantic errors point at a
  topic, and the topics that exist are good.


## 17. One more thing: what I could not do at all

* **No file dialog.** Raven's exists; its descriptor is opaque; I did not wire
  it up. A player names the file in a text field.
* **No scroll gesture.** No wheel delta to read.
* **No way to make a save of more than one city at a time** without re-entering
  a filename, for the same reason.
* **No autosave on a timer** -- trivial given save works, left undone.

## 18. Summary of what I would change first

If I could change five things, in order:

1. Make a press an event, or document that it must be derived. A $600/second
   treasury drain is not a small thing.
2. Erase or explain the function-value wall. It cost me three test files.
3. Show struct figures in the test report. A test that says "wrong" without
   saying "how" is half a test.
4. `std::file`, `div`, and `usize_to_int`. Three small additions, each of which
   removed real work from this project.
5. Ship the borrowing reference, and hoist module-level definitions.

Everything else on this list is friction. Those five are correctness and
velocity.
