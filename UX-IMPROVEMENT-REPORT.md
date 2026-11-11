# What the UI work cost, and what Botlish and the Raven package got in its way

This is the report of the pass that took the game from a working, plain window
to a themed one, written for whoever maintains Botlish and the `raven`
package. Every entry is something that actually happened while it was being
written, with what it cost and what would remove it. Where a deficiency has a
workaround the workaround is named, so a reader can judge the cost.

The work itself is in `simcity/skin.bot` (the game's look: its theme and its
three widget recipes), `simcity/toolbar.bot` (the palette, with headings,
tooltips and the chosen tool marked), `simcity/render.bot` (the map: the three
networks drawn as lines, a block grid, and a cursor that says whether a
placement will fit), `simcity/words.bot` (the figures, grouped as a person
reads them) and `simcity/app.bot` (the window's layout, the hotkeys, the
right button, the status line).

---

## 1. The friendly module wraps 87 of Raven's 921 C functions

**What happened.** `raven.bot` gives comfortable wrappers for windows, the
four panels, the label, the button, the checkbox, the text input, the combo
box, the slider, the spin box, actions, timers and events. Everything else --
label text sizes and colours, button styles, separators, progress bars,
borders, slot alignment, theme metrics, widget classes and materials, minimum
window sizes, keyboard shortcuts, the island, accessibility -- is in the
generated binding (`raven::controls`, `raven::widget`, `raven::style`,
`raven::layout`, `raven::shell`, `raven::window`) and reachable only as raw C
calls with a handle and a number.

**What it cost.** The whole pass needed 28 raw C calls (47 call sites) that
the friendly module does not have -- 11 of them in `simcity/skin`, 8 in
`simcity/app`, 7 in `simcity/toolbar` and 2 in `simcity/render`. A game cannot
be themed through the package's own surface: there is no way to give a label a
size, a button a style, a control a minimum width, a row a fill coefficient,
or a theme an accent. `simcity/skin` exists to hold those calls in one place,
and its first paragraph says so.

| the call the package does not wrap | what a program cannot do without it |
|---|---|
| `Rlabel_set_text_size`, `Rlabel_set_color` | every label the same size and colour: a caption and a figure read alike |
| `Rbutton_set_style` | show which tool the player has chosen -- `R_BUTTON_PRIMARY` is the accent |
| `Rborder_set_background`, `..._outline`, `..._corner_radius`, `..._shadow`, `..._padding` | group controls on a surface: no cards, so the screen is a scatter |
| `Rseparator_set_orientation` | no rule between two things that are not the same thing |
| `Rprogress_bar_set_value` | no bars: the demand curves stay text |
| `Rslot_set_fill`, `Rslot_set_halign`, `Rslot_set_valign` | no say over how a child fills its slot, so a status line wraps into a narrow column |
| `Rwidget_set_min_size`, `Rwidget_set_size` | no control over a control's own size |
| `Rtheme_set_accent`, `Rtheme_set_metric` | no identity: Raven's default dark theme is neutral, and every control keeps the default height |
| `Rwindow_set_min_size`, `Rwindow_center` | no say over the smallest a window may be dragged to |
| `Rwindow_register_shortcut` | no keyboard shortcuts |
| `Rwidget_is_focused` | no way to tell that a control has the keyboard (see 6) |
| `Raccessibility_*` | no text scale, no high contrast, no announcement: a program cannot ask for its accessible settings at all |
| `Rheader_bar_*`, `Rmenu_*`, `Risland_*`, `Rwindow_set_island` | the shell widgets: no custom header, no menu bar, no transient notification |
| `Rtheme_load`, `Rtheme_use`, `Rtheme_save` | no theme files |
| `Rwidget_set_class`, `Rwidget_add_class`, `Rwidget_set_color`, `Rwidget_set_material` | no per-widget styling, and no state shown as a class |
| `Rimage_set_stretch`, `Rimage_set_corner_radius`, `Rimage_set_tint_color` | no say over how a texture is shown |
| `Rtext_input_set_placeholder`, `Rtext_input_set_max_length` | no affordance on a text field: a player is not told what the field wants |
| `Rspin_box_set_step`, `Rspin_box_set_decimals` | a tax rate reads `7.00` rather than `7` |
| `Rcheckbox_set_style`, `Rslider_set_step`, `Rslider_set_orientation`, `Rcombo_box_add_item` | the remaining control settings |

**What would fix it.** Wrappers for those the package's own guide describes
in its "Controls", "Layout", "Themes, styles and materials" and "Accessibility"
sections. The nine the friendly module is furthest from are, in order:
`Rtheme_set_accent`, `Rlabel_set_text_size`, `Rlabel_set_color`,
`Rbutton_set_style`, `Rborder_set_background`, `Rslot_set_fill`,
`Rprogress_bar_set_value`, `Rwidget_set_min_size`, `Rwindow_set_min_size`.
With those ten a program can build a screen that is not a list of equal grey
widgets, and the game's own `skin.bot` becomes about twenty lines of
preference rather than a hundred of C plumbing.

---

## 2. A string cannot be given to the generated binding's `const char*`

**What happened.** The binding declares `Rwidget_set_action(Rid widget,
const char *action)`, and a Botlish `str` is not a `std::ffi::c::Ptr[Char]`:
the compiler refuses it (`cannot be proven to satisfy
std::ffi::c::Ptr[std::ffi::c::Char] (argument type: str)`). The trick the
friendly module uses -- `cstring(text).Rlabel_create()`, passing a `Bytes`
where a `read noescape` pointer is expected -- works, but the six lines that
build the NUL-terminated bytes are `private` in `raven.bot`.

**What it cost.** Any program that wants an unwrapped string-taking call --
setting a widget's action by name, its class, its name, a placeholder, a
theme's style -- writes its own copy:

```
nomethod fn nul() -> std::byte::Byte:
    0

nomethod fn cstr(text: str) -> std::abi::bytes::Bytes:
    std::abi::bytes::from_list(std::str::encode_utf8(text).append(nul()))
```

This is the second copy in the repository (`simcity::store` has one too, for
the save file's path) and the fourth in the tree if the package's private one
counts. It is six lines, but it is the kind of six lines a reader has to stop
at and re-derive.

**What would fix it.** Make `cstring` public in `raven.bot`, or put
`std::ffi::c::cstring(text)` in the standard library. A `str` that is lent to
a `read noescape` `Ptr[Char]` is exactly the `Bytes` the module already
builds; nothing about it needs to be private.

---

## 3. A named `Float64` makes every C float call declare `NonFiniteFloat`

**What happened.** `Rlabel_set_color(0.58, 0.61, 0.66, 1.0)` compiles with no
handler: the compiler knows the literal fits a `float` and says so. Bind the
same number to a name and the call becomes an error:

```
DIM_RED = 0.58
made.id.Rlabel_set_color(DIM_RED, DIM_GREEN, DIM_BLUE, 1.0)
#   this call may produce the declared error "NonFiniteFloat", which is
#   neither handled here nor admitted by the enclosing function's own
#   "errors" declaration
```

**What it cost.** The palette's colours are written inline at the point of use
(`Rlabel_set_color(0.58, 0.61, 0.66, 1.0)` in `skin::caption`) rather than
named, and a comment says which of the map's own inks the number is. `theme()`
declares `errors NonFiniteFloat` only so that its named metric values can be
passed. Anything that takes a *runtime* float -- a bar's fraction -- has to
carry the error or handle it (`skin::show_bar` handles it, so that no caller
of a figure carries Raven's float range with it).

**What would fix it.** A module-level `Float64` constant the compiler can
prove is inside `binary32`, exactly as it does for a literal. It knows the
value already; the rule is that it cannot see it. A `const Float64`, or the
same treatment `rule.c-floats` already applies to literals, would let a
palette be a table of names.

---

## 4. The generated bindings are not `nomethod`, so every call warns

**What happened.** `Rtheme_set_accent(0.21, 0.65, 0.33)` and
`Rtheme_set_metric(metric, value)` are declared in `raven::style` with their
first parameter as an ordinary one, so the linter reports METHOD-ELIGIBLE for
each call written in functional form. Declaring the *caller* `nomethod` does
not help: the warning is about the call site, and the package's declarations
are not modifiable from a program.

**What it cost.** The tree is kept warning-free (the repository's own
convention -- see commit `121bb04`'s "clear every warning"), so `theme()` now
calls two wrappers rather than the C functions directly:

```
nomethod fn metric_set(metric: std::ffi::c::UInt, value: Float64) -> unit errors NonFiniteFloat:
    metric.Rtheme_set_metric(value)
    unit

nomethod fn accent_set(red: Float64, green: Float64, blue: Float64) -> unit errors NonFiniteFloat:
    red.Rtheme_set_accent(green, blue)
    unit
```

**What would fix it.** Declare the generated binding's functions whose first
argument is a *parameter* rather than a subject -- `Rtheme_set_*`, `Rslot_*`,
`Rlabel_set_color`'s four-argument family, `Rborder_set_*` -- with `nomethod`.
`std` marks its symmetric functions (`bit_and`, `bit_or`) and its
destination-first ones (`std::mutable_array::copy`) that way already; the
bindings' families are the same shape.

---

## 5. A watched window reports every key a control has taken

**What happened.** `watch_input(true)` reports the window's `KeyPressed`
events, and Raven's guide is explicit that "watching consumes nothing: the
window's controls still get every key and click". The catch is that the
watched window is never told the control took the key: a `raven::Event` has
`kind`, `source`, `value`, `extra`, `number`, `text`, `x`, `y`, `dx`, `dy` and
no "consumed" flag.

**What it cost.** The game has one text field (the file a city is kept in) and
a keyboard, so a digit typed into the filename is also a `KeyPressed` the game
would read as "choose this tool", and an arrow key typed into the field moves
the caret *and* scrolls the view. The fix is to ask the field itself whether
it has the keyboard:

```
nomethod fn typing?(game: Game) -> bool:
    game.path.id.Rwidget_is_focused() != 0
```

That works only because there is exactly one text input. A second field, or a
spin box with the keyboard, needs the same question asked of every control;
there is no `Rwindow_get_focused` in the package's wrappers to ask once.

**What would fix it.** One of:
(a) a `consumed`/`handled` field on `Event`, set when a widget's own class
answered the key first;
(b) `Rwindow_get_focused(window)` in the friendly module, so a program can
ask "is any control taking text?" without knowing which one;
(c) `watch_input(true, only_unhandled)`, or a note in `raven::watch_input`'s
comment that the events arrive whether or not a control took them.

---

## 6. A shortcut does not fire while a text input has focus, but a key press is still reported

**What happened.** Verified headlessly with the game itself: `inject_key` on
key `'2'` while the save field is focused produces **no** `Action` event (so
`Rwindow_register_shortcut` correctly defers to the control) but **does**
produce a `KeyPressed` event on the watched window. The two mechanisms
disagree about what the player did.

**What it cost.** The game's hotkeys are implemented in its own `key_press`
rather than through Raven's shortcuts, because a shortcut that fires only when
nothing has focus would be silently inert while the player types -- and the
game needs to know *which* of the two happened.

**What would fix it.** A shortcut's `Action` event carrying the key and the
modifiers it came from, or `Event::extra` on a window's `KeyPressed` naming
the focused widget.

---

## 7. A `str` for one character needs an append

**What happened.** A single character is a character literal in Botlish
(`'R'`, a `UnicodeChar`) and every text Raven takes is a `str`, so one
character's label is `"".append_char('R')` -- three times in this tree
(`skin`'s bars, `toolbar`'s scroll glyphs, `app`'s own helper). The linter
also warns on a written one-character String literal, which is the same gap
seen from the other side.

**What it cost.** Twelve lines of `nomethod fn char` / `fn one` in three
modules.

**What would fix it.** `std::str::from_char(c)`, or a coercion of a
`UnicodeChar` literal to a `str` where a text is expected.

---

## 8. No integer division and no number formatting

**What happened.** `/` divides `Float64` values only. `simcity::render`
carries a thirty-two-step restoring division (`div`) because a texture pixel
and a packed colour both need one. Numbers become text only through
`std::int::to_string`, which has no grouping, no precision and no
interpolation.

**What it cost.** `words.bot` groups a figure's digits by walking the text
(`group_walk`), which is honest but is a *string* pass for a *number*
grouping. `$16,035` is a run of digits a player has to parse otherwise. The
tax spin box has no suffix, so the rate is spelled `7` beside a caption that
says "Rate".

**What would fix it.** `Int // Int`, and a formatting call with at least a
grouping separator and a precision (`std::int::to_string(n, grouped: true)`).

---

## 9. `std::list::get` needs an eager default of the element type

**What happened.** `xs.get(i, default)` evaluates `default` whether or not the
index is out of range, and `default` must be the list's own element type.
Marking "the chosen one of thirteen tool buttons" is an index into a list of
widgets: there is no widget to hand back as the default.

**What it cost.** `show_picks` folds over the list and compares each button's
*position* against the tool's number, carrying the position in the fold's
intermediate:

```
fold pick in game.picks with intermediate n 0:
    simcity::skin::picked(pick, n + 1 == simcity::toolbar::code_of(s.tool))
    n + 1
```

This is correct and reads well, but it is a detour: `List[Widget]` with no
total reader means every "pick the one at i" is an iteration.

**What would fix it.** `xs.get(i)` answering an optional, or a total
`xs.at?(i)`.

---

## 10. Raven's own `Rwindow_create` flags are unreachable through the package

**What happened.** The friendly `raven::window(title, w, h)` always passes
`R_WINDOW_DEFAULT`. `R_WINDOW_CUSTOM_HEADER`, `R_WINDOW_TRANSPARENT`,
`R_WINDOW_BORDERLESS` and `R_WINDOW_MAXIMIZED` are declared in
`raven::window` and reachable only by building the C string and the flags
oneself.

**What it cost.** The game uses the system title bar. A header bar of the
interface's own -- the shape a modern tool is drawn in -- is not available
without abandoning the package's window constructor.

**What would fix it.** `raven::window(title, w, h, flags)` with a
`raven::WindowFlags` enum, as `raven::Options` already is.

---

## 11. What the workaround cost was, measured

| | before | after |
|---|---|---|
| 1000 frames of dragged input (`perf.bot`) | 4376 ms | 4377 ms |
| 2000 idle frames | 2 ms | 2 ms |
| the map's legibility | road, rail and dead wire are three tiles of nearly the same grey | each drawn along its own direction in its own hue, with a 4-tile block grid |
| the chosen tool | the note line says "Road, $10" | the button wears the accent, the cursor says whether the placement fits |
| keyboard | arrow keys scroll (and also move a focused field's caret) | arrows scroll, digits choose a tool, space turns the clock, and all of them stand aside while the save field is focused |
| pointer | left button builds | left builds, right reads the tile |
| figures | `$16035` in one grey crowd | `$16,035` with a caption over it, in a card, with the tax rate beside it |
| demand curves | `R ................` | three bars and a `+`/`-` key |

The per-frame cost is unchanged: the renderer's extra work (a tile's three
line attributes read once instead of twice, and a grid test on two pixels in
eight) is paid for by the two divisions it no longer does, and the drawing is
measured rather than assumed.
