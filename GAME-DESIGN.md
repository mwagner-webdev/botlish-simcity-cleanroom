# The game's rules

What this simulation does, in the order a month does it. Every number named
here is a constant at the top of `simcity/sim.bot`, so changing a balance is
one edit and a test says which balance it expects.

## The map

A map is a grid of WIDTH by HEIGHT tiles; the game starts a 64 by 64 map and
the window shows 32 by 22 of them, so the city is four times the viewport. Each
tile's terrain is one of water, grass, trees or rough ground, made by a
deterministic value noise of the seed (`simcity/city.bot`'s `land_of`): two
lattices over 32-tile cells, blended for the water's shape, and one for trees
and one for rough ground. Nothing about a map is random at play time, so the
same seed is the same land every run.

Buildable ground is everything but water. Trees and rough ground are cleared by
the bulldozer for $1 a tile.

## The view

The view is a window onto the map, not the map itself. It moves by the arrow
keys and by four buttons under the map, a screen at a step and with two rows of
overlap so a scroll never replaces the view with one that shares nothing with
it. It stops at the map's edge: a view showing ground that is not on the map
shows nothing.

The keys are polled rather than reported. Raven's event bridge carries named
actions and value changes and nothing else, and Raven has no key-state query of
its own, so `simcity::screen::key_down` is asked once a frame -- the same
mechanism the mouse uses. A key held down moves the view one step and then waits
for a release, because the mask of keys is stored between frames and a press is
a bit that is set now and was not set before.

## Saving and loading

A save is a text file of fixed-width decimal fields, written and read through
Raven's own file calls. `simcity/store` is the only module that knows them, for
the same reason `simcity::screen` is the only module that knows how a texture
reaches Raven: the raw authority a FFI needs stays in one file where a reader
can see all of it. The format is `simcity/save`'s:

    "SIMCITY1\n"       the magic
    WIDTH      4 digits
    HEIGHT     4 digits
    BANK       15 slots, 11 digits each: the value plus 10 billion, so a slot
                may hold a negative balance and still be one fixed-width field
    then 15 tile attributes in a fixed order, each a 3-character tag, a newline,
    and one fixed-width field per tile

Fixed widths are the point: Botlish has no split and no parse, so a format that
needs neither is the format to have. A field is its digits with zeroes in front,
and a reader takes it by position alone. The tags are the order's own check -- a
reader that expected land and found the zone's tag has a file that is not this
format, and says so rather than reading a city that is quietly wrong.

A save holds every attribute and not only the ones a player made: power, road
access and the environment are recomputed by the next month, but a city loaded
before that month should look exactly like the one that was saved. A value that
would not fit its field is clamped, because a wider field would move every field
after it; the only quantity that can reach the ceiling is the smoke or the crime
of a heavily built city, and one point of smoke is cheaper than a corrupt save.

## A month

One tick is one month of city time. A month runs, in this order:

1. power, from the plants outwards along the wires;
2. the transport network, inwards from the map's edge, and with it which zones
   have somewhere to travel to;
3. the environment: pollution, crime, fire risk and land value;
4. development: each zone block grows or shrinks by what the city is short of;
5. the budget: taxes in, upkeep out, and the year's figures.

The environment (3, 3 in the list) runs every third month. Smoke, crime and land
value are slow quantities next to power, road access and growth; gating them
keeps a month well inside a tenth of a second, and the gate is on the tick
count, so the sequence of months that run them is itself deterministic.

## Power

A power line conducts, and so does a plant. Power runs out of a plant's block
along the wires and dies where the wire stops. A zone block is supplied when
one of its own nine tiles stands beside a live line, and the whole block is
then supplied, because it is one set of grounds. A supplied building does not
pass anything on: the wire is the network, exactly as in the game being copied,
so cutting a line cuts the power behind it.

Propagation runs to a fixed point over the tile list. A sweep in one direction
advances one tile per pass, so a line forty tiles long would need forty passes;
the sweeps therefore alternate direction, and converge in a handful. The pass
count is bounded by the map's own extent in case a path is long.

A block that is not served (below) and not supplied shrinks: its development
falls one level a month until it has none.

## Transport

The network is the roads and the rails, and it is only connected where it
reaches the edge of the map: a ring of roads with no way out of the county
serves nobody. A zone block is served when a tile of it stands beside the
connected network; a served block serves the rest of itself, because it is one
set of grounds.

There is no vehicle-by-vehicle traffic model. What there is instead is a
capacity signal: a tile of a served block carries jobs or residents, and the
land value of a busy block falls by a little for each of them, because a
crowded street is worth less than an empty one. That is the whole of traffic:
it pushes land value down, land value pushes residential demand down, and
residential demand decides whether housing grows.

## Development, and demand

Each zone block has a level, 0 to 5, and holds 28 residents per developed tile
when it is residential, 22 jobs per tile when it is commercial, and 18 jobs per
tile when it is industrial. A level-5 residential block of nine tiles therefore
houses 252.

Demand is three figures from -100 to 100, one per zoning category, each cut by
the tax rate:

* residential demand is jobs short of people, plus a bonus for what the ground
  near the block is worth;
* commercial demand is customers short of shops;
* industrial demand is trade short of industry.

A block whose category is short of grows a level; a category with too much and
the block loses one. The thresholds are 60 to grow and 45 to shrink. A block
only answers a shortfall when it is supplied, served, and the treasury is not
in deficit; otherwise it shrinks.

What presses on a block is measured over the three by three tiles around it,
not over the whole city: the worst smoke, the worst crime, and what the nearby
ground is worth. That is why industry next door to housing makes the housing
stagnate, and industry across town does not.

## The environment

Pollution comes off developed industrial tiles, one point per tile per month per
level. Trees take points out of the air, and what is left drifts to the four
neighbours and decays. A works saturates its own block, and the ground a tile or
two away carries a visible amount; across town there is none.

Crime is carried by developed blocks, more where there is smoke, and is taken
away by a police post inside its radius. Fire risk is carried by industry, and
is taken away by a fire post. A post only works where it is developed (level
above 0), supplied, and served.

Land value adds for water and trees and parks, and for being near the middle of
the map, and takes away for smoke, crime and congestion. Land value feeds
residential demand.

## Money

The city starts with $20,000.

| what | cost |
|---|---|
| road | $10 a tile |
| power line | $5 a tile |
| rail | $20 a tile |
| residential zone | $50 for the whole 3 by 3 |
| commercial zone | $200 |
| industrial zone | $200 |
| coal plant | $3000 |
| nuclear plant | $5000 |
| police post, fire post | $500 |
| park | $10 |
| bulldozer | $1 a tile |

Upkeep is charged a year: a road, a power line and a rail per tile; a plant, a
post and any other structure once. Tax income is population times the rate, over
ten, charged a year. Both are divided by twelve and charged every month; the
year's income, upkeep and balance are written into the city's bank when the
year turns over.

The city cannot spend what it does not have: a placement that costs more than
the treasury leaves the city unchanged and says so. But a city may go into
deficit on upkeep, and once the treasury is negative no zone block grows --
the one permanent consequence of overspending.

## Crossings

A tile's lines are one array each, so a crossing is a tile holding two of them
rather than a third attribute, and what may share a tile is the whole rule:

| what is already on the tile | a road | a power line | a rail |
|---|---|---|---|
| a road | joined | **crosses** | refused |
| a power line | **crosses** | joined | **crosses** |
| a rail | refused | **crosses** | joined |

A power line is the one line that crosses everything, which is why it is the
line that makes zoning in the original a puzzle: it has to reach every block,
and the roads it must cross are laid wherever the player likes. A rail may
not cross a road at all -- a train does not share a carriageway with a car --
and the refusal says so, because "the ground is not clear" on a tile that looks
empty is the kind of answer that makes a player click the same tile for a
minute. A line laid on a line of its own kind joins it rather than making a
second, so dragging a wire along an existing wire costs one wire's price.

Both networks run through a crossing: power conducts along the wire under the
carriageway, and traffic travels along the road over the wire, so a block at
the far end of a run of road is served through the tile the power line crosses.

A crossing is drawn with the carriageway's colour and the wire as a stripe of
its own ink along it, in the direction the wire runs -- which is read from the
wire's neighbours, because a stripe that stopped at the road would make the
line look broken. `crossings.bot` tests the rules, both networks through a
crossing, and the stripe's pixels.

## Disasters

Not implemented. There is no fire, flood or earthquake beyond the fire risk a
works carries, which pushes land value down and nothing else.

## What is drawn on a tile

The map is one texture, eight pixels to a tile. Eight pixels is the size a
single letter needs: each tile that carries an object draws a five by five box
of pixels at the top-left of its tile, and the box is one letter's bitmap. The
letter is decided from the city, not from the drawing:

| letter | what stands there |
|---|---|
| R | a residential zone, whatever its level |
| C | a commercial zone |
| I | an industrial zone |
| P | a coal plant |
| N | a nuclear plant |
| O | a police post |
| F | a fire post |
| K | a park |
| none | bare ground, roads, rails, power lines, water |

The ground, the roads and the wires carry no letter because they are read by
their shape and colour, and a letter over them would only hide which is which.
The key is printed on the palette, so a player never has to inspect a tile to
tell a coal plant from a nuclear one. `labels.bot` tests the decisions and the
drawing both: that a residential tile carries a letter and a road does not,
that housing's letter and industry's are not the same shape under two names,
and that a tile rendered on its own carries exactly as many pixels of label ink
as its letter sets.

## What is left out

* Rail works as a road does, for connectivity, and has no distinct behaviour
  beyond the one rule that matters: it may not cross a road.
* There are no zones' distinct uses of land beyond the zoning categories.
* There is no water supply, no schools, no hospitals, no stadiums, no ports and
  no airports.
* One save file at a time, named by the player in a field: no file dialog, no
  list of cities, no autosave. Raven has a file dialog and the save path goes
  through a text field rather than it, because the dialog's descriptor is a C
  struct this game would have to declare by hand.
* There are no city history graphs, no minimap, and no overlays beyond the
  preview of the tile under the pointer.
* The tax rate is a single figure, not three categories.
