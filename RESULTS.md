# Results

What was compiled, what was run, and what it did.

## What compiled

| file | what it is | result |
|---|---|---|
| `simcity.bot` | the windowed game | compiles on `cranelift`; a real X11 window opens and the frame loop runs |
| `tests.bot` | the city, 38 cases | compiles; **38 passed, 0 failed** |
| `labels.bot` | the letters on the map, 6 cases | compiles; **6 passed, 0 failed** |
| `crossings.bot` | the lines that may share a tile, 11 cases | compiles; **11 passed, 0 failed** |
| `saves.bot` | a city written to a file and read back, 5 cases | compiles; **5 passed, 0 failed** |
| `gametest.bot` | the window, no display | compiles; all four figures printed and correct |
| `bench.bot` | the performance report | compiles; the figures below printed |

Every source file in `simcity/` compiles as part of those four. `interp` and
`compile` are not used for the game because Raven calls C and only the native
backends can; the model alone does compile and run on `interp`, and did while it
was being written.

## What the tests assert

The 38 cases cover, in the order the model's own test file lists them:

* **construction and spending** -- a road costs what the palette says; a zone
  is its whole 3 by 3; a second zone cannot overlap the first; a road and a
  zone cannot be built on water; the treasury stops a build the city cannot
  pay for.
* **bulldozing** -- a zone goes away, a power line goes away, clearing bare
  ground costs nothing, and bulldozing a grown block takes its residents with
  it.
* **power** -- a lone zone has none; a plant and a line light the block on it;
  a break in the line cuts the power behind it; a city's generating capacity
  is one figure per plant, not one per tile.
* **roads** -- a road that reaches the edge serves its blocks; a road that
  reaches nothing serves nobody; a zone with no road near it is not served.
* **growth and decline** -- a served, powered town grows to 1260 residents with
  every zone at level 5; a town cut off from power stops growing; a town with no
  road stops growing; a town taxed to the maximum wants far less and declines;
  industry next door makes the ground beside the works worth less than across
  town; a city that cannot pay goes dark.
* **money** -- the treasury moves with a build; a year's income less its upkeep
  is the year's balance; maintenance is charged every month.
* **determinism** -- the same seed and the same actions give the same city; a
  different seed gives a different map; the months run on their own clock.
* **shared state** -- two cities do not share their tiles; building in one does
  not spend another's money; two cities simulate independently.
* **no window** -- the simulation needs no display to grow a city.

Each case compares a model output -- a population, a level, a fund, a boolean
-- and not a process exit.

## The six scenarios, as they came out

One town, built the same way each time, with one thing changed. Numbers are
after 180 months of the scripted build (216 for the power failure, 276 for the
tax and the pollution, 240 for the no-money one):

| scenario | residents | funds | demand R / C / I | zone levels R / C / I | what it shows |
|---|---|---|---|---|---|
| A healthy growth | 1260 | 28,405 | 100 / 100 / 100 | 5 / 5 / 5 | power, road, balanced zoning and 7% tax: the city fills up and pays for itself |
| B power failure | 0 | 24,746 | 92 / 52 / 52 | 0 / 0 / 0 | cut the one wire and every block goes dark and leaves |
| C no road | 0 | 13,050 | 92 / 52 / 52 | 0 / 0 / 0 | a road that never reaches the edge serves nobody |
| D excessive tax | 0 | 23,899 | -63 / -18 / -24 | 0 / 4 / 0 | 20% tax collapses residential demand and the residents leave |
| E industrial smoke | 1260 | 30,077 | 100 / 100 / 100 | 5 / 5 / 5 | land beside the works is worth 75, across town 129 |
| F no money | 0 | -21,895 | 92 / 52 / 52 | 0 / 0 / 0 | three plants and two posts the city cannot keep: the treasury empties and every zone goes dark |

E is the one to read twice. The same city that grows in A, with an industrial
block moved next door to its housing: the housing still reaches level 5, because
the city has jobs to offer, but the ground under the plume is worth 54 points
less than the ground across town, and a city where the industry had arrived
before the housing would have left that ground empty.

## Performance

Measured by `bench.bot`, which builds the town the scenarios build, lets it grow
for 400 months, and then advances 1000 more while timing them. Raven is started
headless only because that is the portable way to read a clock; the null
renderer draws nothing and no frame is uploaded:

    the map is 48 by 48 tiles                 2304 tiles
    developed tiles 27                       3 zones, all at level 5
    residents 1260
    funds 88,725
    months advanced 1400
    1000 months took 20,353 ms
    one month takes 20,353 microseconds      20.4 ms a month

The town holds 27 developed tiles out of 2304 -- a deliberately small
developed city, because the requirement is a *representative* developed city and
not an empty one. What dominates is not its size:

* **the networks, 12.2 ms a month (58%).** Power and road propagation to a fixed
  point over the tile list, plus the two passes that clear and seed them.
* **the environment, 7.4 ms a month (35%).** Pollution, crime, fire, land value,
  each a pass over every tile.
* **the rest, 1.5 ms a month (7%).** Demand, growth, the budget.

### What was optimised, and by how much

| change | months of 1000, ms |
|---|---|
| the first working version | 47,824 |
| one pass to clear and seed a network, where there were two | 44,721 |
| residents, jobs and upkeep in one scan, where there were three | 42,284 |
| sweeps taken alternately in each direction | 18,765 |
| water and trees searched within two and three tiles, not four and five | 19,154 |

The direction of the sweeps was the whole of it. A propagation taken in one
direction over the tile list advances one tile per pass, so a line forty tiles
long needed forty passes -- and the pass count was the cost. Alternating the
direction converges in a handful of passes for any path, and the pass count is
still bounded by the map's extent in case a path is long. The other changes are
real but worth a fifth of that.

### What this means for play

### What the bigger map costs

The game now starts a 64 by 64 map instead of 48 by 48, and the simulation's
passes over the tile list are its whole cost, so a month is dearer:

| map | one month |
|---|---|
| 48 by 48 (2,304 tiles, what `bench.bot` measures) | 20.4 ms |
| 64 by 64 (4,096 tiles, what the game starts) | 32.7 ms |

32.7 ms a month is 7% of the CPU at the game's normal speed (a month every half
a second) and 33% at rush (a month every tenth of a second), with the frame's
upload of a 32 by 22 viewport on top. That is the trade for a city four times
the viewport instead of two, and it is one constant in `simcity/app.bot` to
change back. `bench.bot` still measures 48 by 48, so the two figures are the
same benchmark before and after.

Rendering is extra and separate: a whole viewport of 32 by 22 tiles is 811,008
bytes of texture, redrawn only when the city or the pointer's tile changes.

## What was run, and what was not

| claim | status |
|---|---|
| the model compiles | yes |
| the city's 38 tests pass | yes, run |
| the view scrolls, and only when a key is pressed | yes, run: `gametest.bot`
  injects an arrow key, calls the loop's own `read_keys`, and answers that the
  view moved one step in x and none in y, and that a second read with the key
  still down moves it no further |
| a city saved to a file comes back as it was | yes, run: `gametest.bot` presses
  the game's own Save, replaces the city with a different one, presses Load, and
  answers that the funds, the road count and the month are the ones that were
  saved. `saves.bot` does the same at the module level, and refuses a file that
  is not a save and an empty one |
| a power line crosses a road and a rail | yes, run: `crossings.bot`, 11 cases.
  With the crossing rule weakened in either direction three cases fail, and
  with a crossing tile made to stop carrying traffic or power the case that
  covers it fails, so the suite has teeth in both directions |
| a rail may not cross a road | yes, run: the same suite, and the refusal is
  named in the status line rather than answered "the ground is not clear" |
| the map's letters carry a letter, and are drawn | yes, run: `labels.bot`, 6
  cases, including one that renders one tile alone and counts its pixels of
  label ink. With the glyph guard weakened the same case fails, so it has
  teeth |
| every control of the palette is inside the window | yes, run:
  `gametest.bot` reads the palette's bottom edge back and compares it with the
  window's height, answering 1. Shrink the window below the palette and the
  same program answers 0 |
| the window compiles | yes |
| a real X11 window opens and the frame loop runs | yes, run: the process stays alive with the window open until the timeout kills it |
| the window, driven with synthetic input, builds on a click | yes, run: `gametest.bot` |
| the pointer aims at every tile of the map | yes, run: the map's four corners are read back on it |
| the map is actually drawn, not blank | yes, run: `sight.bot` reads the window's pixels back on the real
  renderer and the first draw changes them. With the bug reintroduced the same
  program answers 0, so the check has teeth |
| the window, driven by a human hand | not run |
| the game's advance while the player is idle | yes: a timer ticks every tenth of
  a second, and 40 headless frames of the loop's own `month` advance 8 simulated
  months, which is the tempo set |
| the game's own frame loop, complete | not exercised to the end |
| a save driven by a human hand choosing a file | not run: the file dialog
  Raven offers is not wired up, and a player names the file in a field instead |

## Defects found by driving the window, and fixed

* **The cursor could only reach the map's diagonal.** `simcity::screen`'s
  `mouse_at` passed the same C pointer as both out-parameters of
  `Rwindow_get_mouse_position`, so Raven wrote the mouse's y over its x and
  the second slot stayed zero: the game read (y, 0) and the pointer's tile
  only ever ran along one line. The cell now holds two pointers, one per
  float, and the pointer can be aimed at every tile. `gametest.bot` reads all
  four corners of the map and answers 1111 (every one of them is on the map's
  viewport) -- and the map is now 416 by 304, so its tiles are squares rather
  than the 416 by 486 rectangles it drew before.
* **The map vanished entirely.** Holding the map's aspect ratio meant putting it
  in a size box, and `Game.map` was pointed at the *box*; the texture was then
  uploaded into a container that is not an image, so it drew nothing and the
  map's area was blank. The map and the palette now each sit in their own size
  box, and `Game.map` names the image widget inside the map's box -- which is
  both the widget the texture goes into and the widget whose rect the pointer
  is aimed at. `gametest.bot` asserts the kind, and `sight.bot` still answers 1
  after the wrapping.
* **The inspect tool never said anything.** `Tool::Inspect` was handed to
  `simcity::actions::place`, where it is not a line tool or a zone tool, so it
  fell through to the zone branch and was refused as "the ground is not
  clear". `read_mouse` now asks for the tile's description instead
  (`simcity::words::show_tile`), which says what stands on the tile, its zone
  level, and the four conditions that decide its future: power, road access,
  smoke, crime and worth.
* **The window opened too small and the palette's lower half was unreachable.**
  The window was 940 by 460, holding a map 416 by 304 over a palette whose
  natural height was 486: a column of twenty controls in a 304-point slot is
  laid out below the window's bottom edge, so it is never drawn and can never
  be clicked. The palette is now three short columns (208 points tall), the
  window is 940 by 560, and `gametest.bot` reads the palette's bottom edge back
  and answers 1 -- it answers 0 with the window shrunk below the palette, so
  the check has teeth.
* **Nothing on the map could be read without inspecting it.** A zone block at
  level 0 is one flat colour, and a coal plant and a nuclear plant were two
  more. The map's tiles now each carry a single letter (R, C, I, P, N, O, F, K),
  drawn from a five by five bitmap font built in the renderer, with the key on
  the palette. `labels.bot` tests it: a residential tile carries a letter, a
  road carries none, and a tile rendered on its own carries exactly as many
  pixels of label ink as its letter sets.
* **The window opened too small and the palette's lower half was unreachable.**
  (Fixed in the commit before this one.) The palette now also declares its own
  natural height, and `gametest.bot` reads it back: 208 points wanted against
  386 held. Shrink the row the palette sits in and that figure answers 0.
* **The letters leaked off their tile.** The first version of the glyph
  read its pixel by naming a bit position and guarding only that position, so
  a pixel one row or one column outside the letter's box could still be read:
  the R tile drew 23 pixels of label ink instead of its glyph's 14, and the
  rows were read the wrong way up. `labels.bot`'s ink count caught it. The guard
  is now on the row and the column themselves, and the letters print the right
  way up.

## What is not done

* **Save and load.** Not started.
* **Disasters.** Not started.
* **City history and graphs, minimap, overlays.** Not started. The preview of
  the tile under the pointer is the only overlay.
* **Railways as a second transport type.** Rail places and counts as a road for
  connectivity, which is all the requirement asks of it, and has no behaviour of
  its own.
* **Stadiums, ports, airports.** Not started.
* **The view cannot be moved with the keys.** `app.bot` has `with_view`, and
  nothing calls it yet: there is no key handling in the frame loop.
* **Tool costs are not shown on the buttons.** `show_cost` exists and the
  palette's buttons are named by the chosen tool's message instead.
* **Traffic as a number the player can see.** It exists only as the congestion
  term in land value. The status line does not carry a traffic figure.
* **Only eight kinds of object are labelled.** The letter is drawn for the three
  zones, the two plants, the police, the fire station and the park. A road, a
  rail and a wire carry none, because their shape and colour already say which
  they are; the letter table (`simcity/render.bot`'s `glyph`) has room for more
  letters, and none of the others is drawn.
