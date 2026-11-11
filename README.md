# SimCity, in Botlish

A playable graphical clone of the original 1989 SimCity, written in Botlish and
drawn with the Raven GUI library. Everything -- the terrain, the power network,
the roads, the demand curves, the taxes, the drawing -- is implemented in
Botlish in this directory. Nothing is a picture and nothing is shuffled in
from another language.

## What you have

    botlish-linux-x86_64   the supplied Botlish compiler and toolchain
    raven-0.4.0.botpkg    the supplied Raven GUI package
    raven-0.3.1.botpkg    the Raven package the game was first written against
    botlish.json          the project manifest (raven is its one dependency)
    .bot_modules/         raven, installed by the package manager
    simcity.bot           the entry point: the windowed game
    simcity/              the program
      city.bot            the city as a value: its grid, its money, its clock
      actions.bot         what the player does: place, clear, spend
      sim.bot             one month of city time
      scenario.bot        the six cities the tests build
      rng.bot             the deterministic randomness the game is allowed
      render.bot          the city as pixels
      screen.bot          the raw layer: a texture's buffer, and nothing else
      toolbar.bot         the palette of tools
      skin.bot            how the game looks: its theme, its cards, its figures
      words.bot           the figures of a city, as the labels on the screen read
      app.bot             the window, the controls, and the loop that runs both
    tests.bot             the headless suite for the city (38 cases)
    labels.bot            the headless suite for the letters on the map (6 cases)
    crossings.bot         the headless suite for one line crossing another (13 cases)
    saves.bot             saving a city to a file and reading it back (5 cases)
    gametest.bot          the windowed game, exercised with no display
    inputtest.bot         what the pointer, the keys and the wheel do (16 cases)
    shot.bot              the window on a real display, played and photographed
    sight.bot             the map is drawn, checked on the real renderer
    bench.bot             the deterministic performance report
    perf.bot              the input cost per frame, measured against the old code
    guiplay.bot           the game played on a real display, and read back
    tools/                order.py, dedupe.py, undupe.py: helpers used while
                          writing the sources (a module's top level is ordered
                          callee-first, and the duplicated comments an earlier
                          reordering pass left behind are removed by undupe.py)
    SIMCITY-RAVEN-0.4-MIGRATION-MILESTONE-1.md    the migration report
    UX-IMPROVEMENT-REPORT.md                      what the UI pass cost, and
                          what Botlish and the raven package got in its way

## Building and running

Put the toolchain and the package in this directory, instal the package once:

    ./botlish-linux-x86_64 add raven-0.4.0.botpkg -replace

Then build and run the game:

    ./botlish-linux-x86_64 -backend cranelift simcity.bot

`interp` and `compile` cannot call C, so a native backend is required; Raven
needs one. The window opens on your X display and is drawn through Vulkan --
the lavapipe software renderer is enough:

    sudo apt-get install gcc libc6-dev libx11-6 libvulkan1 mesa-vulkan-drivers

A standalone executable beside the program:

    ./botlish-linux-x86_64 native deploy -target linux-x86_64 -out dist
    cp simcity.bot game.bot
    ./botlish-linux-x86_64 -emit-native-executable -runtime-path '$ORIGIN/lib' game.bot
    mv game dist/simcity
    ./dist/simcity

The entry point is copied first because `-emit-native-executable` names the
executable after its input's basename, and `simcity` is this program's own
module directory: building `simcity.bot` in place asks the linker to write over
a directory. This was true of the 0.3.1 tree as well; it is a defect of the
documented command, not of the migration.

## Playing

| what | how |
|---|---|
| choose a tool | click its button on the right, or press its number: 1 to 9
  for the nine things you build and 0 for the bulldozer |
| build | click the map; drag to run a road or a line -- a press is one placement, however long the button is held |
| read a tile without inspecting it | right-click it, or pick the inspector and left-click |
| cross a power line over a road or a rail | lay the wire on the tile the road
  or rail already holds: the tile keeps both, and power still runs through |
| move the view | arrow keys, or the four buttons under the map: a screen at a
  step, and never past the edge of the map |
| save a city | type a filename in the field, press Save |
| load a city | the same field, then Load |
| follow the pointer | the tile under it is drawn as a pale preview: its frame is
  green where the tool fits, amber where the treasury cannot pay for it, and
  red where the ground refuses it -- so a placement is settled before the
  button goes down |
| read a tile without inspecting it | the single letter it carries: R, C, I the
  zones, P and N the power plants, O police, F fire, K park. The key is on
  the palette |
| set the tax rate | the spin box at the bottom, with the rate shown in the
  header above it |
| see the budget | the Budget button: taxes, upkeep, balance |
| pause, march, rush | the three buttons on the right, or the space bar |
| put the tool down | Escape |

Every button carries the sentence it is worth over the pointer: a palette of
thirteen prices is a thing to memorise and a tooltip is a thing to read.

The window is a screen of its own, drawn in Raven's dark theme with the one
accent this game's own map palette uses: a header of figures (treasury,
people, jobs, tax, date, tempo), the demand curves as bars, the map beside
the palette, and a status line at the bottom whose colour says what kind of
thing it is reporting. An island at the top of the window repeats the latest
sentence for a moment and folds back.

A new town is 64 by 64 tiles and the window shows 32 by 22 of them, so the city
is four times the viewport and the view has to move. Arrow keys scroll it; the
wheel scrolls it too, one step a line, which is the same step. Raven 0.4.0
reports a watched window's keys, buttons, pointer and wheel as events, so a key
press is one event however long the key is held and the auto-repeat Raven sends
while it is held is not acted on: a held key scrolls once and waits, and the
four buttons under the map do the same for a player who would rather click.

Save writes the whole city -- every tile attribute, the bank, and the clock --
to a text file of fixed-width decimal fields, so a save is a file you can read.
Load puts it back and answers with what it did; a file that is not a save leaves
the city alone.

Start with the loop the game means you to learn: a road along a tile, a power
line beside it, a coal plant at the end, and residential, commercial and
industrial blocks alongside. Build no power and nothing grows; build no road
and nothing is served; tax to the maximum and what you built walks away.

## Testing

    ./botlish-linux-x86_64 -backend cranelift tests.bot     # the city, 38 cases
    ./botlish-linux-x86_64 -backend cranelift labels.bot    # the map's letters, 6 cases
    ./botlish-linux-x86_64 -backend cranelift crossings.bot # one line over another, 13 cases
    ./botlish-linux-x86_64 -backend cranelift saves.bot     # a city to a file and back, 5 cases
    ./botlish-linux-x86_64 -backend cranelift gametest.bot  # the window, no display
    ./botlish-linux-x86_64 -backend cranelift inputtest.bot # what input does, 16 cases
    ./botlish-linux-x86_64 -backend cranelift shot.bot      # the window, played and photographed
    ./botlish-linux-x86_64 -backend cranelift sight.bot     # the map, on the real renderer
    ./botlish-linux-x86_64 -backend cranelift bench.bot     # the performance report
    ./botlish-linux-x86_64 -backend cranelift perf.bot      # the input cost per frame
    ./botlish-linux-x86_64 -backend cranelift guiplay.bot   # the game on a display

`tests.bot`, `labels.bot` and `crossings.bot` print PASS or FAIL per case and a
count. `saves.bot` does the same, and writes a real file: it is a program rather
than a suite, because a case that touches a file needs the store's context and a
function that needs a context cannot be passed as a value -- which is what a
suite's registration is. `inputtest.bot` is a program for the same reason: a
case needs Raven's context, and it drives the game through Raven's own synthetic
input (`inject_move`, `inject_button`, `inject_wheel`, `inject_key`) and the
game's own event step, so what it checks is what the game runs. `perf.bot` runs
the same workload as the `perf_old.bot` of the pre-migration tree (kept beside
this one for the comparison) and reports the frames' cost. `guiplay.bot` needs a
display and plays the real window, reading the city and the window's pixels
back. `shot.bot` is a display program too: it plays six short scenes into the
real window and writes each frame's pixels to a `.png`-less RGBA file beside
it, which is how the interface in this repository's report was looked at.

`tests.bot`, `labels.bot` and `crossings.bot` print PASS or FAIL per case and a
count. `saves.bot` does the same, and writes a real file: it is a program rather
than a suite, because a case that touches a file needs the store's context and a
function that needs a context cannot be passed as a value -- which is what a
suite's registration is.
`gametest.bot` drives the same window headlessly and prints the map's size,
whether all four corners of the map are reachable, what a click spent, what the
inspector says, that the map is an image widget, and that the palette's bottom
edge is inside the window -- a control laid out below the window is never
drawn and can never be clicked, so a palette that overflows its row makes its
lower half unreachable. Shrink the window below the palette and that figure
answers 0, so the check has teeth.
`sight.bot` needs the real renderer (a display and Mesa's software Vulkan driver
are enough) and answers whether the map's first draw changed the window's
pixels: with the texture going into a widget that is not an image, it answers 0. `bench.bot` prints the map's size, how
much of it is developed, and how long a thousand months took.

## What is implemented, what is not

`GAME-DESIGN.md` has the simulation rules and what was left out or simplified.
`RESULTS.md` has the measured numbers. `BOTLISH-EXPERIENCE.md` has what the
language was like to write this in. `TOOLCHAIN-REPORT.md` is a report on the
deficiencies of Botlish and Raven, written for whoever maintains them: each one
is a thing that actually happened to this project, with what it cost and what
would fix it. `UX-IMPROVEMENT-REPORT.md` is the same for the pass that themed
the interface: what the friendly module does not wrap, what the generated
binding refuses, and what the two cost.
`SIMCITY-RAVEN-0.4-MIGRATION-MILESTONE-1.md` is the report of the migration to
Raven 0.4.0: what the new package changed, what the game now does instead of
polling, what it still does natively, and what was measured before and after.
