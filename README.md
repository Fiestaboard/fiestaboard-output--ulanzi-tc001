# Ulanzi TC001 Output Plugin

Shows your FiestaBoard pages on a **Ulanzi TC001** running
[AWTRIX NG](https://github.com/Blueforcer/awtrix-ng), over your local
network. The board becomes an app in the clock's rotation, beside the
clock's own apps and scripts.

The TC001 is a 32 × 8 pixel clock: one row of 8 characters in the small
(3×5) text size, or one row of 5 in the large (5×7) one. Pick the size with
the **Text size** setting.

> **Work in progress (0.1.0).** This plugin is adapted from the Ulanzi TC002
> plugin and still being reworked for the TC001's smaller panel: rendering, the
> push payload and device recognition are not final, and it has not been
> tried on a real TC001. It needs FiestaBoard 10.2.0 or later (the first
> release that allows a 1 × 5 LED board).

## Requirements

- FiestaBoard 10.2.0 or later
- A Ulanzi TC001 running AWTRIX NG, on the same network as FiestaBoard
- Nothing to install on the clock, and no cloud service or account

**AWTRIX NG only.** AWTRIX 3 and Ulanzi's own firmware are not supported.

## Settings

| Setting | Default | |
|---|---|---|
| Clock address | — | IP address or local name, as `192.0.2.60` or `awtrixng-a1b2c3.local`. |
| App name | `FiestaBoard` | The app's name in the rotation. Letters, digits, `-` and `_`, at most 32. |
| Show on change | on | Switch the clock to the board whenever its page changes. |
| Display time | the clock's | Seconds the board stays on screen in the rotation. |
| Text size | Small — 8 characters | Or Large — 5 characters. |
| Tile style | Gaps | Seamless lights the line between two tiles of the same colour. |
| Block padding | Off | 1 pixel grows highlighted text's background by a pixel on every side. |
| Fade style | Through black | Or Blend. |
| User name, Password | — | Only when the clock's web UI asks for a password. Stored as a secret. |

## Development

Tests run against a FiestaBoard core checkout that has the 1 × 5 LED floor
(branch `feat/small-led-boards`, `main` from 10.2.0):

```sh
./run_tests.sh /path/to/FiestaBoard
```

They use a mock clock on 127.0.0.1 (`tests/mock_awtrix.py`); a network fence
refuses any other host. The suite includes FiestaBoard's output-plugin
conformance suite.

| File | Contents |
|---|---|
| `__init__.py` | The plugin: rendering, pushing, streaming, discovery, restart detection |
| `manifest.json` | Plugin id `ulanzi_tc001`, the board settings and actions |
| `output/device-models.json` | The `ulanzi_tc001` device model: 32 × 8 pixels, 3×5 or 5×7 font, 5 fps stream |
| `tools/try_device.py` | The one-off check against a real clock |

## Licence and credits

MIT. Adapted from the
[Ulanzi TC002 plugin](https://github.com/rummeyer/fiestaboard-output--ulanzi-tc002)
by Oliver Rummeyer (MIT, © 2026 Oliver Rummeyer). AWTRIX NG is by
[Blueforcer](https://github.com/Blueforcer/awtrix-ng).
