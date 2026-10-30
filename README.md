# Ulanzi TC001 Output Plugin

Shows your FiestaBoard pages on a **Ulanzi TC001** running
[AWTRIX NG](https://github.com/Blueforcer/awtrix-ng), over your local
network. The board becomes an app in the clock's rotation, beside the
clock's own apps and scripts.

The TC001 is a 32 × 8 pixel clock: one row of 8 characters in the small
(3×5) text size, or one row of 5 in the large (5×7) one. Pick the size with
the **Text size** setting.

> **Development preview (0.1.0).** Direct hardware tests on AWTRIX NG 1.2.2
> matched all 256 framebuffer pixels for RGB edge patterns and both fonts.
> FiestaBoard integration still requires the pending small-LED support;
> 10.1.20 cannot create this clock's one-row board. See
> [Verify on your clock](#verify-on-your-clock) for evidence and remaining checks.

## Requirements

- FiestaBoard 10.2.0 or later
- A Ulanzi TC001 running AWTRIX NG, on the same network as FiestaBoard. See
  [AWTRIX NG](https://github.com/Blueforcer/awtrix-ng) for how to install it
  on the clock.
- Nothing else to install on the clock, and no cloud service or account

**AWTRIX NG only.** AWTRIX 3 and Ulanzi's own firmware are not supported.

## Quick start

1. In FiestaBoard, open **Displays → Marketplace** and install **Ulanzi
   TC001 (AWTRIX NG)**. Where it is not listed yet, paste
   `https://github.com/Fiestaboard/fiestaboard-output--ulanzi-tc001` under
   **Bring your own display** (or use **Integrations → Marketplace → Add from
   Git**). Or from a terminal:

   ```sh
   curl -X POST http://<fiestaboard>:4420/api/plugins/install \
     -H "Content-Type: application/json" \
     -d '{"repository": "https://github.com/Fiestaboard/fiestaboard-output--ulanzi-tc001"}'
   ```

2. Install AWTRIX NG on the clock (see its documentation) and join the clock
   to your Wi-Fi.
3. Add an output board and choose **Ulanzi TC001 (AWTRIX NG)**.
4. Press **Find my clock**, or type its IP address (find the address in your
   router or the clock's web UI).
5. Press **Test connection**. A TC001 answers
   `Connected to the TC001 at <address> (AWTRIX NG <version>).`
6. Pick a **Text size** and save. The board joins the clock's rotation.

## Troubleshooting

If **Test connection** says the clock answered, but not like AWTRIX NG:

- Check that the address is an AWTRIX NG clock, not AWTRIX 3 or Ulanzi's firmware.
- Update AWTRIX NG to a current release: older ones do not report their
  panel (`display` in `/api/v1/capabilities`).

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
  plugin, and an AWTRIX NG clock whose panel is not 32 × 8 is refused
  with its size.

## Settings

| Setting | Default | |
|---|---|---|
| Clock address | — | IP address or local name, as `192.0.2.60` or `awtrixng-a1b2c3.local`. |
| App name | `FiestaBoard` | The app's name in the rotation. Letters, digits, `-` and `_`, at most 32. |
| Show on change | on | Switch the clock to the board whenever its page changes. |
| Native collection rotation | off | Let AWTRIX rotate timed collection pages and navigate them with its buttons. Requires a core with native playlist support; released 10.2.0 supports the default mode only. |
| Display time | the clock's | Seconds the board stays on screen in the rotation. |
| Text size | Small — 8 characters | Or Large — 5 characters. |
| Tile style | Gaps | Seamless lights the line between two tiles of the same colour. |
| Block padding | Off | 1 pixel grows highlighted text's background by a pixel on every side. |
| Fade style | Through black | Or Blend. |
| User name, Password | — | Only when the clock's web UI asks for a password. Stored as a secret. |

## Native collection rotation (optional)

With a core that supports native playlists, enable **Native collection rotation**
in this board's settings. An active single page becomes one native slot; a timed
collection becomes one slot per member, in collection order with the collection's
display interval. Left/right buttons select the previous/next native app, and
AWTRIX supplies transitions. Random and rule collections keep FiestaBoard's normal
rotation. **Show on change** applies to normal output, not background native refreshes.
Leave AWTRIX's automatic app rotation enabled and **Block buttons** off to use
both timed rotation and physical navigation. The plugin preserves these global
firmware settings and its transition choice.

FiestaBoard refreshes pixels without switching away from the app you selected.
It reports the selected member after the next device poll. Data sources retain
their own refresh cadence, including hourly generated art; changing slots does
not generate another image. Pausing FiestaBoard stops updates but does not stop
the clock's autonomous rotation. Notifications and on-demand firmware scripts can
temporarily take over navigation.

Slots have stable `fb_<board hash>_<page hash>` names. FiestaBoard manages those
slots' order and enabled state; edit their collection in FiestaBoard. Other apps,
their relative order, and disabled native apps such as Battery are preserved.
New slots stay disabled until their upload completes. Turning the option off or
switching to normal output removes only this board's native slots. The clock has
a shared limit of 50 pushed apps; if the new collection cannot fit without
discarding existing content, synchronization fails and retries after space is freed.
Opting out at full capacity first retires this board's native slots to make room
for the normal slot. If that replacement upload fails, a later retry restores it;
unrelated apps are never deleted to make space.

Pushed content lives in RAM. FiestaBoard restores missing slots after a reboot or
reconnection; order and disabled names are persistent. Updates are not a firmware
transaction, so interrupted updates may temporarily leave disabled reserved names;
the next successful sync reconciles them. Do not reuse FiestaBoard's managed slot
names for scripts or other senders. Existing installations keep the default mode.
The first normal write after startup reads the app inventory to reconcile any
owned slots left by an earlier native session. A failed persistent order save is
retried even when the clock already shows the requested order in RAM.

## Find my clock

Searches your local network (the one you browse FiestaBoard from, then the
one FiestaBoard is on, or a network you enter such as `192.0.2.0/24`) for
AWTRIX NG clocks, and lists the ones whose panel is 32 × 8. A clock whose
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

If the clock's web UI asks for a password:

```sh
curl -u <user>:<password> -X DELETE http://192.0.2.60/api/v1/apps/FiestaBoard
```

## Verify on your clock

Checked on a real TC001 running AWTRIX NG 1.2.2 on 2026-10-29, using
the standalone plugin with core's small-LED branch. These are HTTP and
device-framebuffer checks, not a physical inspection of the LEDs or a
completed FiestaBoard installation.

| Check | Result |
|---|---|
| Full 32 × 8 RGB bitmap, all four edges, small and large text | `/api/v1/display/screen` matched all 256 expected pixels in every case |
| Device identity | `boardType` is `awtrixng`, version `1.2.2`; capabilities report 32 × 8 |
| Streamed flip transition | All 13 frame requests accepted; most took 53–131 ms, one took 1122 ms. Smooth sustained 5 fps is not established |
| Recovery after one simulated transport failure | Poll requested a resend; the real device's recovered frame matched all 256 pixels |
| Physical LEDs, real power cycle, installed config persistence | Still need verification |

The diagnostic tool stops after a failed connection or compatibility check,
without writing to the device.

The AWTRIX NG `enlargeApps` setting is TC002-only and does not apply to the
TC001.

## Development

Tests run against FiestaBoard **10.2.0**, the first released core with the
1 × 5 LED floor and matching FiestaUI 8.15.0 previews. CI pins `v10.2.0`;
its `core_ref` workflow input can test another branch, tag, or commit.
FiestaBoard 10.1.20 and earlier are not compatible.

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
