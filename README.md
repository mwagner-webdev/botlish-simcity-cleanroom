# SimCity, in Botlish

A playable graphical clone of the original 1989 SimCity, written in Botlish and
drawn with the Raven GUI library. Everything -- the terrain, the power network,
the roads, the demand curves, the taxes, the drawing -- is implemented in
Botlish in this directory. Nothing is a picture and nothing is shuffled in
from another language.

## What you have

    botlish-linux-x86_64   the supplied Botlish compiler and toolchain
    raven-0.3.1.botpkg    the supplied Raven GUI package
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
      screen.bot          the raw layer: textures, and polling the mouse
      toolbar.bot         the palette of tools
      words.bot           the figures of a city, as the labels on the screen read
      app.bot             the window, the controls, and the loop that runs both
    tests.bot             the headless suite for the city (38 cases)
    labels.bot            the headless suite for the letters on the map (6 cases)
    gametest.bot          the windowed game, exercised with no display
    sight.bot             the map is drawn, checked on the real renderer
    bench.bot             the deterministic performance report
    tools/                order.py, dedupe.py: helpers used while writing the sources
                          (a module's top level is ordered callee-first, and the
                          duplicates they remove are development debris)

## Building and running

Put the toolchain and the package in this directory, instal the package once:

    ./botlish-linux-x86_64 add raven-0.3.1.botpkg

Then build and run the game:

    ./botlish-linux-x86_64 -backend cranelift simcity.bot

`interp` and `compile` cannot call C, so a native backend is required; Raven
needs one. The window opens on your X display and is drawn through Vulkan --
the lavapipe software renderer is enough:

    sudo apt-get install gcc libc6-dev libx11-6 libvulkan1 mesa-vulkan-drivers

A standalone executable beside the program:

    ./botlish-linux-x86_64 native deploy -target linux-x86_64 -out dist
    ./botlish-linux-x86_64 -emit-native-executable -runtime-path '$ORIGIN/lib' simcity.bot
    mv simcity dist/
    ./dist/simcity

## Playing

| what | how |
|---|---|
| choose a tool | click its button on the right |
| build | click the map; drag to run a road or a line |
| move the view | arrow keys |
| follow the pointer | the tile under it is drawn as a pale preview |
| read a tile without inspecting it | the single letter it carries: R, C, I the
  zones, P and N the power plants, O police, F fire, K park. The key is on the
  palette |
| set the tax rate | the spin box at the bottom |
| see the budget | the Budget button: taxes, upkeep, balance |
| pause, march, rush | the three buttons on the right |
| a new town | the New town button |

Start with the loop the game means you to learn: a road along a tile, a power
line beside it, a coal plant at the end, and residential, commercial and
industrial blocks alongside. Build no power and nothing grows; build no road
and nothing is served; tax to the maximum and what you built walks away.

## Testing

    ./botlish-linux-x86_64 -backend cranelift tests.bot     # the city, 38 cases
    ./botlish-linux-x86_64 -backend cranelift labels.bot    # the map's letters, 6 cases
    ./botlish-linux-x86_64 -backend cranelift gametest.bot  # the window, no display
    ./botlish-linux-x86_64 -backend cranelift sight.bot     # the map, on the real renderer
    ./botlish-linux-x86_64 -backend cranelift bench.bot     # the performance report

`tests.bot` prints PASS or FAIL per case and a count, and so does `labels.bot`.
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
language was like to write this in.
