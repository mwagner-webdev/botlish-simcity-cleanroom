# SIMCITY-RAVEN-0.4-MIGRATION-MILESTONE-1

## 1. Result

Migrated. The application builds and runs on Raven 0.4.0; every existing headless
suite passes with identical figures; the deterministic simulation is unchanged;
raw mouse polling is gone from the game, replaced by Raven's public input
events and state queries; a new 14-case integration suite drives the real
input interpretation headlessly and passes; the game was launched and played on
a real X display with a Vulkan software renderer; and the input layer's
native authority was reduced to what Raven still does not wrap.

The one deliberate behavioural difference is an improvement and is tested: a
drag whose pointer moves are coalesced by Raven now visits every tile it
crossed. The old polling code saw one position per frame and silently skipped
tiles (406 roads on the scripted drag below, against 436 now).

## 2. Starting application and baseline

The project was the clean-room SimCity written against Raven 0.3.1: eleven
modules of Botlish (4,224 lines in `simcity/`, 6,865 with the entry programs),
a texture-rendered map, three headless suites, a persistence suite, a benchmark,
a headless window test and a real-renderer test.

Baseline recorded before any edit (kept in `BASELINE.md`):

| suite | result (Raven 0.3.1) |
|---|---|
| tests.bot | 38 passed, 0 failed (50.4 s) |
| labels.bot | 6 passed, 0 failed |
| crossings.bot | 13 passed, 0 failed |
| saves.bot | 5 passed, 0 failed |
| gametest.bot | every figure 1, map 512x352, "spent 3865" |
| sight.bot | frame 1040x620, image widget 1, first draw changed the window 1 |
| bench.bot | 48x48, developed 27, residents 1260, funds 88725, 1400 months, 1000 months in 20912 ms |
| simcity.bot | compiles; opens a window on DISPLAY=:0 and runs its loop (killed by a 30 s timeout, exit 124) |

Two baseline notes:

* **README says 11 crossings cases; the suite runs 13.** Corrected in the README.
* **The README's documented standalone-executable command does not work, and
  did not work before the migration.** `-emit-native-executable simcity.bot`
  writes an executable named after its input's basename, `simcity`, which is this
  program's own module directory; the linker fails with "Is a directory". Verified
  on the unmodified 0.3.1 tree. The README now documents building from a copy of
  the entry point (`cp simcity.bot game.bot` ... `mv game dist/simcity`), which
  works and was used for the verification below.

## 3. Toolchain and package versions

* Compiler: the supplied `botlish-linux-x86_64`, unchanged and not replaced.
  `-version`: "no release version; this is a development build", source revision
  `bdd5e3d, packaged`, front end `5dad9886a0a2fb70-5155727`, Tcl 9.0.1, native
  backend packaged. No newer compiler was supplied and none was used.
* Raven before: 0.3.1, installed, `botlish.json` request `"0.3"`, lock `0.3.1`,
  source archive `raven-0.3.1.botpkg` (sha256 `9336738e...`).
* Raven after: **0.4.0**, installed by the supported package manager
  (`./botlish-linux-x86_64 add raven-0.4.0.botpkg -replace`):
  * request moved to `"0.4"`, lock to `0.4.0`, source archive
    `raven-0.4.0.botpkg`, sha256 `c6acd0815bb9dc772a936cad7f7463ed02fec1eeb44315730faf38ca96c76402`.
  * `botlish verify` reports "1 package instance: as installed"; the target view
    was re-derived (41 files, 3 native libraries).
  * No lock was weakened; no native library was substituted by hand. The
  `.bot_modules` tree of 0.3.1 was replaced by the manager, not mixed.
* Compatibility check before editing: `-check` on every entry program against
  0.4.0 succeeded with no diagnostics, so the package is compatible with this
  compiler before any application change. The new `libraven.so.0` needs
  GLIBC_2.38; the host is 2.39 (the old library needed 2.38 too, so the
  requirement is unchanged).
* ABI: the event bridge's ABI is checked at start (`botlish_raven_bridge_abi`),
  and 0.4.0 is ABI **2** where 0.3.1 was ABI 1. This is a genuine breaking
  change between the two native archives, and it is why the package must be
  replaced rather than partially updated: `raven.bot` 0.4 refuses to talk to a
  1 bridge. The live check is: a program built against the new `raven.bot` fails
  to start if the old archive is still loaded. No mixing was attempted.

## 4. Raven API compatibility census

Compared `raven.bot` 0.3.1 against 0.4.0, file by file (the package's own
sources, read as a third-party consumer would).

**Added (all new to the game, and all used or tested):**

| symbol | what it is |
|---|---|
| `watch_input(window, bool)` | turns a window's keys, buttons, pointer and wheel into events |
| `key_down?(window, key)` | whether a key is held now |
| `mouse_button_down?(window, button)` | whether a button is held now |
| `modifiers_down(window)` | the modifiers held now, ORed |
| `mouse_inside?(window)` | whether the pointer is over the window's content |
| `mouse_position(window) -> Point` | where the pointer is, in the window's logical units |
| `Point {x, y}` | a point, as a value |
| `inject_move`, `inject_button`, `inject_wheel` | synthetic pointer and wheel |
| `inject_key_down`, `inject_key_up` | a key held, then released |
| `EventKind::{KeyPressed, KeyRepeated, KeyReleased, MousePressed, MouseReleased, MouseMoved, Wheel}` | input events |
| `Event.{x, y, dx, dy}` | where the pointer was, and how far it moved |
| `raven::lost()` | how many events the bridge could not record |

**Removed:** none. Every symbol the game used in 0.3.1 still exists.

**Changed contracts (the reason the error handlers could be simplified):**

| call | 0.3.1 | 0.4.0 |
|---|---|---|
| `raven::events()` | `errors NonFiniteFloat` | no error; the bridge's numbers are finite and are read as finite |
| `raven::rect(widget)` | `errors NonFiniteFloat` | no error |
| `raven::mouse_position(window)` | did not exist | no error |
| `raven::capture`, `size`, `click` | unchanged | unchanged |

The package documents the guarantee directly: "the numbers this module reads
back from Raven -- events, a widget's rectangle, the pointer's position -- are
finite (a number that is not reads 0.0), so reading them declares no error."

**Module namespaces unchanged** (`raven`, `raven::window`, `raven::widget`,
`raven::core`, ...). The generated binding files are byte-identical between
0.3.1 and 0.4.0 in size and in content, except `raven.bot` itself, which is
larger (48,083 bytes against 40,803) because of the new input section.

Three of the new symbols are available but **not used**, because nothing in this
application asks the question they answer: `modifiers_down` (no control here is
modified by a modifier key), `mouse_inside?` (the tile conversion's rectangle
test already says whether the pointer is over the map, and a pointer outside the
window is outside the map), and `lost()` (a counter for events the bridge could
not record, which is a diagnostic rather than an input). They are recorded here
so that the census is complete rather than flattering.

**Texture and widget interfaces unchanged** and still low-level:
`Rtexture_create_from_pixels`, `Rtexture_update`, `Rwidget_create`,
`Rimage_set_texture`, `Rwidget_set_size`, `Rwidget_get_desired_size` are all as
they were. The game's rendering path compiled against 0.4.0 with no change.

**Discovered, and worth recording:** the 0.3.1 binding already contained
`Rwindow_inject_mouse_move`, `Rwindow_inject_mouse_button`,
`Rwindow_inject_key`, `Rwindow_get_modifiers` and `Rwindow_is_mouse_inside`.
What was missing in 0.3.2 was not the C functions but (a) the wrapper that
exposes them safely without native memory of the application's own, and (b) the
event bridge's ability to record raw input at all. That distinction matters for
the BOTLISH-EXPERIENCE follow-up: the game's "nothing watches the map" was read
off the wrapper's surface, and the wrapper was the part that was incomplete.

## 5. Input architecture before and after

**Before.** `simcity/screen` held one native allocation of five pointers: a
4*width*height byte frame buffer, two `Ptr[Float]` cells for the mouse's x and
y, and two more for a widget's desired size. Every frame, `simcity::app::run`
called `read_keys` (four `Rwindow_is_key_down` calls, assembled into a bit mask,
compared against last frame's mask to derive a press) and `read_mouse`
(`Rwindow_get_mouse_position` into the two cells, read back through
`std::binary::native::view`, plus `Rwindow_is_mouse_button_down`), then derived
a press from the state by comparing frames, as the 0.3.2 module had to.

**After.** `window.watch_input(true)` is called once when the window is built.
Each frame the loop asks for one frame, then takes the events:

```
nomethod fn run(game: Game) -> unit:
    awake = raven::wait_frame(-1.0)
    if not awake:
        unit
    else:
        heard = take_events(game)
        next = month(heard)
        shown = show(next)
        run(shown)

nomethod fn take_events(game: Game) -> Game:
    map = raven::rect(game.map)
    fold event in raven::events() with intermediate s game:
        accept(s, event, map)
```

The event fan-out is one function, `accept`, which routes by kind:

| event | answer |
|---|---|
| `Action` | `act` (unchanged: the palette's named actions) |
| `ValueChanged` | `rate` (the tax spin box, unchanged) |
| `KeyPressed` | `key_press`: the four arrow keys scroll one step |
| `MousePressed` | `press`: on the map, one construction and the start of a drag |
| `MouseMoved` | `move_pointer`: the preview follows, a drag builds along the tiles crossed |
| `MouseReleased` | `release`: the drag is over |
| `Wheel` | `wheel_turn`: the view scrolls one step a line |
| `KeyRepeated`, `KeyReleased` | dropped (see below) |
| everything else | dropped |

Two of Raven's two facilities are used, for the two questions they answer, and
not one for both:

* **A press is an event.** `MousePressed` arrives once per press however long
  the button is held, so a construction happens once and a held button spends
  nothing -- because nothing is delivered. This replaced the derived press
  (button state + "was it down last frame") that had to be right by hand, and
  that had a real defect in it (the treasury drained at $10 a frame until the
  derivation was fixed, per BOTLISH-EXPERIENCE section 11).
* **"Is it held now, and where?" is the state.** `mouse_button_down?` is asked
  on every move event, so a drag continues only while the button really is down
  (a button released outside the window must not go on building), and
  `mouse_position` answers the pointer for the tests' direct check.

The key mask, the `keys` field in `State`, `just_pressed`, `key_mask` and the
four `KEY_*` constants are gone. A held key is now one `KeyPressed` and Raven's
own auto-repeat arrives as `KeyRepeated`, which the game deliberately does not
act on -- which is exactly what the mask implemented.

## 6. Mouse construction and dragging

The conversion from the window's coordinates to a tile is `tile_at`:

```
nomethod fn tile_at(map: raven::Rect, origin_x: int, origin_y: int, px: Float64, py: Float64) -> Place:
    x = offset(px, map.x)
    y = offset(py, map.y)
    if x < 0.0 or y < 0.0 or x >= map.width or y >= map.height:
        nowhere()
    else:
        place_of(origin_x + simcity::render::div(whole(x), TILE_PX), origin_y + simcity::render::div(whole(y), TILE_PX))
```

`offset` is `px - edge` with the one `NonFiniteFloat` a Float64 subtraction can
raise; a distance that is no number answers -1.0, which is a point nowhere on the
map. Raven's `Rect` and `Point` are finite, so no other error can arise and
`tile_at` declares none.

**A point outside the map's rectangle answers no tile at all** -- not the tile
at the edge, and not the origin. This is the fix for a defect the old conversion
had: `whole(x)` clamped a negative distance to 0, so a click on the label row
above the map built on the map's first row. It is also what keeps a click on the
palette, the scroll row, the save field or the tax box from building, since none
of them is inside the map's rectangle.

**Distinct x and y cannot be coupled through the ordinary API.** The old bug
(BOTLISH-EXPERIENCE section 7) was passing one address for two out-parameters.
There is no call left in the game that could express it: `raven::mouse_position`
answers a `Point`, and an event's `x` and `y` are two fields of one record.
Input test 9 pins it (presses at (3,7), (20,5) and (9,3) each land on the tile
they name, and the pairs (3,5) stays bare).

**A drag is move events with the button's state.** `steps_between` walks the
line between the tile the drag is on and the tile the pointer is now on,
excluding the first (already built) and including the last:

```
nomethod fn steps_between(from_x: int, from_y: int, to_x: int, to_y: int) -> List[Place]:
    ...
    loop i from 1 to count + 1:
        step_x = ...
        step_y = ...
        place_of(from_x + step_x, from_y + step_y)
```

Because Raven coalesces the pointer moves of one frame into a single
`MouseMoved` (verified: three injected moves between two event takes answer one
event with `x`/`y` at the final position and `dx`/`dy` the whole delta), the
walk is what keeps a fast drag from skipping tiles. The expectation is computed
a second way in the tests (`line_tile`, rounding a Float64 rather than dividing
an Int) so that a case is not the implementation reading itself; the two agree
everywhere except at an exact half, which is why the drags in the tests are
chosen so that no step is one.

**Costs.** A walk builds each tile it crosses through the same `build_at` the
press uses, which calls `simcity::actions::fits` and charges for what it builds;
a refusal says why and costs nothing. So a drag is charged per tile built, and a
drag across water is refused tile by tile, exactly as a click on water was.

## 7. Keyboard and wheel input

Preserved, on the new mechanism:

* The four arrow keys move the view one step per press, once, and then wait.
  `KeyPressed` gives the press; `KeyRepeated` is dropped. A key held down over
  four frames answers one step (measured, input test 11 and gametest).
* No other key does anything, as before. An unbound key changes nothing (tested
  with `R_KEY_A`).
* The view still clamps to the map, and still does not move when it has nowhere
  to go.
* **The wheel now scrolls the view, one step a line**, the same step the keys and
  the four buttons use. This is the one control the migration added, and it is
  the smallest possible use of a facility the package now supplies: the game has
  no zoom, so the wheel can only scroll, and scrolling is a control the game
  already had. A wheel turn never constructs (tested with a tool picked and the
  pointer on the map).

## 8. Removed native code and remaining native authority

Removed from `simcity/screen`:

* the two `Ptr[Float]` cells for the mouse's position, their allocation in
  `open`, their release in `release`, and their fields in `Cell`;
* `mouse_at` (the raw `Rwindow_get_mouse_position` call and the
  `std::binary::native::view` read-back);
* `down?`, `key_down`, `inside` (the raw button and key polls);
* the now-unused imports (`std::binary`'s list/mutable-array partners, `raven`,
  `raven::window`, `std::list`) and the dead `flat_bytes` helper.

Removed from `simcity/app`: `tile_under`, `read_mouse`, `read_keys`, `key_mask`,
`just_pressed`, the four `KEY_*` constants, the `held` and `keys` fields of
`State` (replaced by `drag_x`/`drag_y`, which say where a drag is rather than
whether a button was down), and the `NonFiniteFloat` handlers that clamped a
rect to zeros or a pointer to (0,0).

**Remaining native authority, with its justification:**

| operation | why it stays |
|---|---|
| `calloc`/`free` and the 4*width*height byte frame buffer | a texture is made from RGBA bytes in native memory; Raven 0.4.0 has no higher-level texture from Botlish bytes |
| `botlish_raven_bytes_copy` | the one copy that carries a frame to Raven; the package's own bridge function |
| `Rtexture_create_from_pixels`, `Rtexture_update` | no wrapped equivalent |
| `Rwidget_get_desired_size` with two `Ptr[Float]` cells | **not wrapped in 0.4.0**: the only reason the `Screen` context survives. The game's own test reads a widget's natural size to prove the palette fits its window |
| `Rwindow_get_type`, `Rwidget_create`, `Rwidget_set_size`, `Rimage_set_texture` | the map is an image widget; these are the only way to make one |
| `simcity/store`'s raw file layer | unchanged, and out of this migration's scope (its own context, its own authority) |

The `Screen` context was **not** removed, because `wish` still needs it. Its
responsibility is now narrower and is stated in the module's header: one frame
buffer and two floats for a size Raven does not wrap.

`raven.bot` still declares `calloc`/`free` in the package, so the game's own
extern declarations of them are the application's; nothing about that changed.

## 9. Error-contract simplification

Removed because 0.4.0's contract makes them unnecessary:

* `raven::rect`'s `on NonFiniteFloat: Rect {0,0,0,0}` in `tile_at` and in
  `gametest`'s `at` -- `rect` no longer declares the error.
* `raven::events()`'s error propagation (and `startup_reasons`'s handler inside
  the package) -- `events()` no longer declares it.
* every `on NonFiniteFloat` handler around `raven::size`, `raven::draw_frame`,
  `raven::capture` in `sight.bot` and `gametest.bot`: none of those ever
  declared it, so the handlers were dead code; removing them changed nothing and
  the compiler confirms the contracts.
* `run`'s own `errors NonFiniteFloat`: nothing in the loop raises it now
  (`wait_frame`, `take_events`, `month`, `show` are all total). The entry
  program's handler stays, because `build` (a `Rwidget_set_size` and a
  `raven::timer` call) genuinely can.

Preserved, because the operation can genuinely fail:

* `offset`'s subtraction (a Float64 subtraction can overflow);
* `raven::inject_move`, `inject_wheel`, `inject_click` (a Float64 to a C float);
* `raven::spin_box_value` / `set_spin_box_value` (a raw C value admitted);
* `simcity::screen::{OutOfRange, IndexNotFound, NativeViewNull}` on texture
  upload and on `wish`;
* `raven::RavenFailed` on start.

Net: the input path no longer declares or handles `NonFiniteFloat` at all,
except for the one subtraction in `offset`, which is real.

## 10. Simulation regression results

Nothing in `simcity/city`, `sim`, `actions`, `render`, `rng`, `save`, `store`,
`scenario` or `words` was changed, and the simulation was not rebalanced.

* **tests.bot 38/38, labels 6/6, crossings 13/13, saves 5/5** -- identical
  verdicts, identical order, identical messages.
* **bench.bot**, the deterministic report (same seed, same 400 warm-up months,
  same 1000 measured months): 48x48, developed tiles 27, residents 1260, funds
  88725, months advanced 1400 -- all four figures identical to the 0.3.1
  baseline. Timing: 20,912 ms before, 19,265/19,891/20,477 ms after (three runs;
  the spread is machine noise, the median is ~2% faster, and this is a
  simulation benchmark that never opens a window).
* **gametest.bot** prints the same nineteen figures as before, including
  "spent 3865", "holding the button cost 1 0/0 1" and "the arrow key moved the
  view 1 ... 0-30-30 0-0". It now drives the game through `inject_move`,
  `inject_button`, `inject_key_down/up` and `simcity::app::take_events` instead
  of raw injection plus `read_mouse`/`read_keys`, and the properties it checks
  are the properties it checked before: the pointer's position is read as the
  position it was given; a click builds and the treasury moves; a held button
  costs nothing; the inspector reads a tile; save/load round-trips through the
  game's own buttons; an arrow key moves the view one step, once.
* **Save compatibility:** the save format is untouched, `saves.bot` is
  unchanged and passes, and gametest's save/load chain passes. Existing save
  files remain compatible; no migration of data was needed.
* **sight.bot** on the real renderer: frame 1040x620, the map is an image
  widget 1, the first draw changed the window 1 -- and a new fourth figure,
  "a click drew a road 1 1": a MousePressed on the desktop backend builds a road
  and the window's pixels change.

The strongest single equivalence: `perf.bot` runs the same scripted 1000-frame
drag on both trees. With one injected move per frame both the old polling code
and the new event code end with **440 roads and $15,600** -- the same seed and
the same scripted mouse path give the same city.

## 11. Synthetic-input tests

`inputtest.bot`, 14 cases, all passing. It is a program rather than a suite for
the same reason `saves.bot` is: a case needs Raven's context, and a function
that needs a context cannot be passed as a value, which is what a suite's
registration is. It drives the game through Raven's own `inject_*` and the
game's own `take_events`, so there is no second input implementation: the
assertions are about tiles and money, never about what an event said.

| # | case | what it pins |
|---|---|---|
| 1 | a press builds once, and charges once | one road, and exactly the road's price |
| 2 | a button held still builds once | three further event steps with the button down cost nothing and build nothing |
| 3 | a drag builds along the tiles it crossed | two moves over sixteen tiles are sixteen roads, 16 x price |
| 4 | a coalesced drag skips no tile | three moves, one frame: every tile of the line is laid, the count is exact, the charge is exact |
| 5 | a coalesced drag the other way skips no tile | the same, left and up, where the rounding is the other sign |
| 6 | a release ends the drag | the tiles built before the release stay, the pointer moving after it builds nothing |
| 7 | a click off the map builds nothing | the label row above, the palette beside, the control row below |
| 8 | a click on a control builds nothing, and the control keeps its input | a click on the save field and on the tax box build nothing, and the field still takes typed text (watching consumes nothing) |
| 9 | distinct x and y pick the tile they name | three presses at three (x, y) pairs land on the right tiles; the crossed pair stays bare |
| 10 | the window's edge is the map's edge | a press at the first pixel of the map builds the view's first tile; one pixel past the map's edge builds nothing |
| 11 | the arrow keys move the view once per press | a held key over four frames is one step; a release is not a step; a second press steps again and clamps; an unbound key does nothing |
| 12 | the wheel moves the view and nothing else | one step a line, up/left/down/right, with a tool picked and the pointer on the map: no road, no charge |
| 13 | a scrolled view builds where the pointer is | after a key-scrolled view, a press lands on the tile the moved view shows, and the tile at the same view position before the move is untouched |
| 14 | the map's last visible column is built | a press on the view's last column builds it; one tile past the map's edge builds nothing |

Coverage of the required list: 1, 2, 3, 4, 5, 6, 7, 8, 9 and 10 are cases 1-9
and 13; keyboard is case 11; wheel is case 12. Viewport offsets and scrolled maps
are case 13; window and map edges are cases 10 and 14. Zoom does not exist in
this application, so no zoom case is applicable. Costs are asserted alongside
tile counts in every construction case.

**The suite has teeth.** A deliberate regression (making `steps_between` answer
only the final tile, i.e. removing the interpolation) fails exactly cases 3, 4,
5 and 6 and nothing else: "10 passed, 4 failed". The file was restored
immediately afterwards and re-verified.

**Semantic-instance budget:** not encountered. The suite is a program, so no
predicate is passed as a value. The limitation is recorded in
BOTLISH-EXPERIENCE's follow-up as the reason the suite is a program rather than
as a workaround around the budget.

## 12. GUI runtime observations

A usable display environment was available (DISPLAY=:0, Mesa's lavapipe Vulkan
driver, `lvp_icd.json`), so the graphical criteria are verified, not assumed.
* `./botlish-linux-x86_64 -backend cranelift simcity.bot` compiles, opens the
  window on the display and runs its frame loop until killed (30 s timeout,
  exit 124) -- the same as at baseline. A window opens and the loop is live.
* `sight.bot` on the real renderer: "the frame is 1040 by 620", "the map is an
  image widget 1", "the first draw changed the window 1", "a click drew a road 1
  1". The last is the new one: the press that built the road also changed the
  rendered pixels, so the texture path and the input path are both exercised on
  the renderer that actually draws.
* `guiplay.bot` plays the real window and reads it back: picks the road tool,
  drags a road across the map, scrolls the view with a right-arrow key, and
  answers "the window drew a road 1", "roads on the map 12", "funds left 19880"
  (12 roads at $10 each, exactly), "the window scrolled 1 30, 0", "the map is at
  0, 36 512x352" -- so the map's rectangle, the viewport, the drag, the charge
  and the scroll are all confirmed against the live window rather than against
  the code.
* Input ownership was confirmed directly: with `watch_input(true)`, a click on
  the save field still produces the field's own `TextChanged` events and typed
  text still lands in it, and a click on the tax box still produces the button
  and box events the window reports; Raven's own widgets keep receiving their
  events, and the map builds nothing because the pointer is not in its
  rectangle.
* **Caveat:** the mouse and keyboard driven here are Raven's synthetic input
  delivered to the real window on the real renderer, not a physical mouse and
  keyboard from an X client. No XTest client (`xdotool`) is installed in this
  environment, so input from outside the process could not be used. The
  interpretation code under test is the same code in both cases (the game's own
  `take_events`), and the coordinates are the window's logical coordinates, so
  the only thing not exercised by a physical device is the driver's own
  delivery, which is Raven's.

## 13. Performance comparisons

`perf.bot` (new) and `perf_old.bot` (in a scratch copy of the unmodified 0.3.1
tree at `git archive HEAD`, with 0.3.1 re-installed by the package manager) run
identical workloads: a thousand frames of a pointer walked across the whole map
with the button held and the map uploaded every twentieth frame; then three
thousand pointer moves three to a frame (what a fast drag looks like); then two
thousand idle frames with no input at all. Each measures the game's own frame
step, not a reimplementation.

| workload | Raven 0.3.1 (polled) | Raven 0.4.0 (events) |
|---|---|---|
| 1000 frames of dragged input (upload every 20th) | 4,469 / 4,647 / 4,749 ms | 4,416 / 4,584 / 4,744 ms |
| 3000 moves, 3 a frame | 20 / 21 / 25 ms | 23 / 24 / 27 ms |
| 2000 idle frames | 9 / 10 / 10 ms | 1 / 1 / 1 ms |
| roads built by the dragged frames | 440 | 440 |
| funds left | 15,600 | 15,600 |
| roads built once the moves are coalesced | 406 | **436** |
| funds left after coalesced moves | 15,940 | 15,640 |

Readings:

* **Idle frames are ~10x cheaper.** 2000 frames with no input cost 9-10 ms
  polled (six native calls per frame: a rect, a mouse position, a button state
  and four key states) and 1 ms with events (an empty queue drained). The old
  code paid for input it did not get.
* **Moved frames are the same.** 3000 moves over 1000 frames: 20-27 ms either
  way.
* **The dragged-frame phase is dominated by rendering, not input.** Both spend
  ~4.5 s of which ~50 texture uploads account for essentially all of it; the
  measured difference is inside the run-to-run spread.
* **Coalesced movement: the new code does more, on purpose.** The old poll read
  one position per frame and skipped the tiles in between (406 roads); the new
  code walks the line and visits every tile (436). That is the behaviour the
  brief asked to preserve, and it is the only place the new code costs more
  work.
* **Headless simulation is not regressed:** bench.bot 20,912 ms before,
  19,265/19,501/19,891/20,477 ms after on the same machine, same seed.

Behaviour under accelerated simulation: the frame loop calls `wait_frame(-1.0)`
(no timeout) and then one month of city time per the timer's tick count, so a
frame never blocks on the simulation and the city advances whether the player is
clicking or not. Nothing in the loop was changed except where the input comes
from, so responsiveness is unchanged; the benchmark above includes the same
`month` scheduling.

## 14. Documentation and discoverability findings

* The 0.4.0 `GUIDE.md` is a genuine, discoverable description of the input
  facility: it names both ways to read input, states the ownership rule
  ("Watching consumes nothing"), documents the coalescing ("the moves between
  two takes of events() are one event"), and ships a complete headless example
  that uses injection. The migration was done from that document plus
  `raven.bot`'s own comments, with no internal or undocumented file read.
* `botlish -help` was used to resolve every standard-library question
  (`std::test::holds`, `std::float64::truncate`, `std::int`, `std::list`), and
  the package manager's `-help cli.packages` for `add -replace`.
* The stale-Compilerpedia findings from the earlier investigation (file I/O,
  `Usize.value`, `on Low: fail Mine`, `std::int::from_string`) are now
  documented: verified present, and none needed by this migration. The
  BOTLISH-EXPERIENCE follow-up says so.
* A discoverability gap remains: the two ways to read input are documented in
  `raven.bot`'s comment and in the guide, but the *generated binding* still
  exposes the raw `Rwindow_*` calls with no note that a wrapped facility now
  exists for them. A consumer arrives at `Rwindow_get_mouse_position` first,
  because the binding is the complete API surface and the wrapper is a subset.
  Recorded as a packaging suggestion, not worked around.
* The compiler prints a program's value after it runs (Compilerpedia
  `cli.output`). It was *not* printed for `simcity.bot` only because the process
  was still running when a timeout killed it; verified with a trivial program.
  Nothing in the supplied documentation suggests that printing has been removed,
  and nothing about it needed a workaround; recorded here because it is the kind
  of toolchain difference a migration report should state explicitly.

## 15. Known remaining language/toolchain gaps

Unchanged, and their workarounds preserved rather than re-solved:

* **No integer division.** `simcity::render::div` (thirty-two restoring steps)
  is used by the tile conversion and by the drag's line walk. Load-bearing.
* **No struct-update expression.** The `State` literals remain eleven copies of
  one shape; the migration added a field and paid for it in all of them.
* **No mutual recursion; a semantic-instance budget** of sixteen typed
  predicates per callee. `inputtest.bot` is a program rather than a suite for
  the documented context rule, which is a better reason than splitting a module
  to dodge the budget.
* **No string split, trim or search.** The save format is fixed-width decimal
  fields so that none is needed.
* **General struct rendering in failing `std::test` comparisons.** Cases still
  report named figures.
* **Context requirements in function types.** A function needing a context
  cannot be passed as a value (`std::test` registration, a fold's function).

Observed differences from the earlier report: none that matter. The earlier
report's claims about the frame loop, `std::test`, and the event bridge were
either already correct or were about the wrapper, not the language.

## 16. Remaining Raven library gaps

* **No wrapped access to a widget's desired size.** `Rwidget_get_desired_size`
  takes two out-parameters; this is why `Screen` survives, with two float cells.
  A `raven::desired_size(widget) -> Size` would remove them.
* **No retained callbacks and no arbitrary painting**, as the brief notes: the
  texture upload stays low-level, and there is no reason to replace a working
  renderer.
* **No wrapped text input for a path** (the file dialog is not wrapped): the
  game's save field is the documented approach.
* **`Rwindow_get_type` and the widget constructors are raw**, so "is the map an
  image widget" is a binding call in the tests. A wrapped `widget.kind` would
  help tests more than the game.

## 17. Files changed

| file | change |
|---|---|
| `botlish.json` | raven request 0.3 -> 0.4, lock 0.3.1 -> 0.4.0, source archive and sha256 to raven-0.4.0.botpkg (written by the package manager) |
| `simcity/app.bot` | the input migration: `watch_input`, `accept`/`press`/`move_pointer`/`release`/`key_press`/`wheel_turn`, `tile_at`, `steps_between`, `drag_along`, `build_at`, `take_events`, `offset`, `Place`; `held`/`keys` replaced by `drag_x`/`drag_y`; `tile_under`, `read_mouse`, `read_keys`, `key_mask`, `just_pressed`, the `KEY_*` constants and the dead `NonFiniteFloat` handlers removed |
| `simcity/screen.bot` | the mouse's two float cells, their allocation and release, and `mouse_at`/`down?`/`key_down`/`inside` removed; `Place` moved to `simcity::app`; dead `flat_bytes` removed; the module's header rewritten to state the narrower responsibility |
| `gametest.bot` | driven by `inject_move`/`inject_button`/`inject_key_down`/`inject_key_up` and `take_events`; the `Rect`/`draw_frame`/`size` handlers that were dead removed; the arrow-key check restructured around a held key |
| `sight.bot` | a fourth figure: a click on the real renderer builds a road and the window's pixels change; dead handlers removed; the store context installed (which `take_events` now reaches) |
| `inputtest.bot` | **new**: the 14-case synthetic-input suite |
| `perf.bot` | **new**: the input cost per frame, against the identical workload run on the 0.3.1 tree |
| `guiplay.bot` | **new**: the game played on a real display and read back |
| `README.md` | 0.4.0, the new files, the corrected crossings count, the corrected standalone-build command, the wheel, and a pointer to the migration report |
| `BOTLISH-EXPERIENCE.md` | an appended follow-up (the original is untouched) |
| `BASELINE.md` | **new**: the pre-migration figures |
| `SIMCITY-RAVEN-0.4-MIGRATION-MILESTONE-1.md` | this report |
| `raven-0.4.0.botpkg`, `raven-0.4.0.provenance.json` | the supplied package and its provenance record |

Untouched: `city.bot`, `sim.bot`, `actions.bot`, `render.bot`, `rng.bot`,
`save.bot`, `store.bot`, `scenario.bot`, `toolbar.bot`, `words.bot`,
`tests.bot`, `labels.bot`, `crossings.bot`, `saves.bot`, `bench.bot`,
`simcity.bot`, `tools/`, `GAME-DESIGN.md`, `RESULTS.md`, `TOOLCHAIN-REPORT.md`.

## 18. Exact reproduction commands

Install the supplied package once:

```
./botlish-linux-x86_64 add raven-0.4.0.botpkg -replace
./botlish-linux-x86_64 verify
./botlish-linux-x86_64 native plan -target linux-x86_64
```

Check every entry point (each answers "ok", with no warnings):

```
for f in simcity tests labels crossings saves gametest inputtest sight bench perf guiplay; do
    ./botlish-linux-x86_64 -check $f.bot
done
```

Run the suites:

```
./botlish-linux-x86_64 -backend cranelift tests.bot      # 38 passed, 0 failed
./botlish-linux-x86_64 -backend cranelift labels.bot     # 6 passed, 0 failed
./botlish-linux-x86_64 -backend cranelift crossings.bot  # 13 passed, 0 failed
./botlish-linux-x86_64 -backend cranelift saves.bot      # 5 passed, 0 failed
./botlish-linux-x86_64 -backend cranelift gametest.bot   # the windowed game, headless
./botlish-linux-x86_64 -backend cranelift inputtest.bot  # 14 passed, 0 failed
./botlish-linux-x86_64 -backend cranelift bench.bot      # the deterministic report
./botlish-linux-x86_64 -backend cranelift perf.bot       # the input cost per frame
./botlish-linux-x86_64 -backend cranelift sight.bot      # needs a display and Vulkan
./botlish-linux-x86_64 -backend cranelift guiplay.bot    # needs a display and Vulkan
```

Build and run the game:

```
./botlish-linux-x86_64 -backend cranelift simcity.bot
```

Build the standalone executable (the entry point is copied first, because the
executable is named after its input's basename and `simcity` is a directory):

```
./botlish-linux-x86_64 native deploy -target linux-x86_64 -out dist
cp simcity.bot game.bot
./botlish-linux-x86_64 -emit-native-executable -runtime-path '$ORIGIN/lib' game.bot
mv game dist/simcity
./dist/simcity
```

Re-run the old tree's identical input workload, for the performance comparison
(the package manager's `install` recreates the locked 0.3.1 from the archive):

```
git archive HEAD | tar -x -C /tmp/perfold
cd /tmp/perfold
cp ../../raven-0.3.1.botpkg .
./botlish-linux-x86_64 install
# perf_old.bot is the same workload as perf.bot; it is kept beside the 0.3.1 tree
./botlish-linux-x86_64 -backend cranelift perf_old.bot
```
