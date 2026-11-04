# The game's rules

What this simulation does, in the order a month does it. Every number named
here is a constant at the top of `simcity/sim.bot`, so changing a balance is
one edit and a test says which balance it expects.

## The map

A map is a grid of WIDTH by HEIGHT tiles; the game starts a 48 by 48 map. Each
tile's terrain is one of water, grass, trees or rough ground, made by a
deterministic value noise of the seed (`simcity/city.bot`'s `land_of`): two
lattices over 32-tile cells, blended for the water's shape, and one for trees
and one for rough ground. Nothing about a map is random at play time, so the
same seed is the same land every run.

Buildable ground is everything but water. Trees and rough ground are cleared by
the bulldozer for $1 a tile.

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

## Disasters

Not implemented. There is no fire, flood or earthquake beyond the fire risk a
works carries, which pushes land value down and nothing else.

## What is left out

* Rail works as a road does, for connectivity, and has no distinct behaviour.
* There are no zones' distinct uses of land beyond the zoning categories.
* There is no water supply, no schools, no hospitals, no stadiums, no ports and
  no airports.
* There is no save and load.
* There are no city history graphs, no minimap, and no overlays beyond the
  preview of the tile under the pointer.
* The tax rate is a single figure, not three categories.
