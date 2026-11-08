# Baseline (Raven 0.3.1, compiler bdd5e3d)

Recorded before any migration edits. Compiler: `botlish-linux-x86_64`
(revision bdd5e3d, front end 5dad9886a0a2fb70-5155727, Tcl 9.0.1, native
backend packaged).

## Headless suites

| suite | result | wall time |
|---|---|---|
| tests.bot (city) | 38 passed, 0 failed | 50.4 s |
| labels.bot | 6 passed, 0 failed | - |
| crossings.bot | 13 passed, 0 failed | - |
| saves.bot (persistence) | 5 passed, 0 failed | - |
| gametest.bot (headless window) | all checks 1 / expected | - |
| sight.bot (real renderer) | frame 1040x620, image widget 1, first draw changed the window 1 | - |

(README claims 11 crossings cases; the suite actually runs 13.)

## Benchmark (bench.bot, deterministic seed)

    the map is 48 by 48 tiles
    developed tiles 27
    residents 1260
    funds 88725
    months advanced 1400
    1000 months took 20912 ms
    one month takes 20912 microseconds

## Graphical build/run

`./botlish-linux-x86_64 -backend cranelift simcity.bot` compiles and opens a
window on DISPLAY=:0 (lavapipe software Vulkan present: lvp_icd.json). The
program runs its event loop until killed (timeout 30 s, exit 124), so a window
does open and the loop is live.

## Observations

* The compiler prints each program's value after the program finishes
  (" value: V", Compilerpedia `cli.output`). It was *not* printed for
  simcity.bot only because the process was still running when the timeout
  killed it. Verified with a trivial program.
* No compiler-newer-than-supplied is used; the only other botlish executable
  in the home directory is a different (older) build and was not used.
