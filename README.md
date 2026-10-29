# Ulanzi TC001 Output Plugin

Shows your FiestaBoard pages on a **Ulanzi TC001** running
[AWTRIX NG](https://github.com/Blueforcer/awtrix-ng), over your local
network. The board becomes an app in the clock's rotation, beside the
clock's own apps and scripts.

The TC001 is a 32 × 8 pixel clock: one row of 8 characters in the small
(3×5) text size, or one row of 5 in the large (5×7) one. Pick the size with
the **Text size** setting.

> **Not yet tried on a real TC001 (0.1.0).** Everything here follows the
> AWTRIX NG documentation and was tested against a mock clock. The
> [Verify on your clock](#verify-on-your-clock) table lists what still needs a
> real device.

## Requirements

- FiestaBoard 10.2.0 or later
- A Ulanzi TC001 running AWTRIX NG, on the same network as FiestaBoard. See
  [AWTRIX NG](https://github.com/Blueforcer/awtrix-ng) for how to install it
  on the clock.
- Nothing to install on the clock, and no cloud service or account

**AWTRIX NG only.** AWTRIX 3 and Ulanzi's own firmware are not supported.

## Quick start

1. Install AWTRIX NG on the clock (see its documentation) and join the clock to your Wi-Fi.
2. In FiestaBoard, add an output board and choose **Ulanzi TC001 (AWTRIX NG)**.
3. Press **Find my clock**, or type its IP address (find the address in your
   router or the clock's web UI).
4. Press **Test connection**. A TC001 answers
   `Connected to the TC001 at <address> (AWTRIX NG <version>).`
5. Pick a **Text size** and save. The board joins the clock's rotation.

## Text size and pages for the clock

The panel is one row of lights, so a page is one line of text.

| Text size | Characters | Look |
|---|---|---|
| Small (3×5) | 8 | Fits the longest words; the default. |
| Large (5×7) | 5 | Taller letters, shorter lines. |

Only a single row of 8 (or 5) characters is drawn, so write pages for the
clock on purpose: a short word or a number, such as `72F` or `GATE 4`. Use a
transition (flip, slide, wipe, fade) to move between pages.

## How it behaves

- The board is a **pushed app** in the clock's rotation
  (`PUT /api/v1/apps/pushed/<name>`), so the clock's own apps keep running
  beside it. With **Show on change** on, the clock switches to the board
  whenever its page changes.
- Each page is one 32 × 8 bitmap. A transition is streamed as a short run of
  frames, at most five a second.
- Pushed apps live in the clock's RAM. FiestaBoard notices a restart (the
  clock's uptime goes back) and sends the page again.
- Only the TC001 is accepted. A Ulanzi TC002 is refused and pointed at its own
  plugin, and an AWTRIX NG clock whose panel is not 32 pixels wide is refused
  with its width.

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

## Find my clock

Searches your local network (the one you browse FiestaBoard from, then the
one FiestaBoard is on, or a network you enter such as `192.0.2.0/24`) for
AWTRIX NG clocks, and lists the ones that are 32 pixels wide. A clock whose
web UI asks for a password cannot be found this way: type its address.

## Test connection

Checks the address, the password, that the device is an AWTRIX NG clock, and
that its panel is 32 × 8. If it fails, the message says which.

## Removing a board

Delete the board in FiestaBoard. The app stays on the clock until the clock
restarts, or you delete it:

```sh
curl -X DELETE http://192.0.2.60/api/v1/apps/FiestaBoard
```

## Verify on your clock

These follow the documentation and are not yet confirmed on a TC001.

| Check | Expected |
|---|---|
| A page draws as a full 32 × 8 bitmap, unscaled, with no cut or offset | Every light matches the preview |
| `GET /api/v1/device` | `boardType` is `awtrixng`; `GET /api/v1/capabilities` has `display.width` 32 and `display.height` 8 |
| A streamed transition | Runs smoothly at the 5 frames a second the plugin sends; try `tools/try_device.py` and read the timings |
| The `enlargeApps` setting | Has no effect on this board: the TC001 draws real pixels |

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
| `tools/try_device.py` | The one-off check against a real clock (shows 32 × 8 frames and times each request) |

## Licence and credits

MIT.

Adapted from Oliver Rummeyer's
[Ulanzi TC002 plugin](https://github.com/rummeyer/fiestaboard-output--ulanzi-tc002) (MIT).

AWTRIX NG is by [Blueforcer](https://github.com/Blueforcer/awtrix-ng).
