# Changelog

## 0.2.0 — unreleased

- Device-instance firmware transition controls: explicit opt-in for effect,
  direction, duration and automatic rotation, capability validation and readback.
  Blank fields preserve device values; zero/off remain explicit choices.

- Optional per-board native collection rotation for cores with the native
  playlist SDK. Timed collections become ordered firmware slots; left/right
  navigation survives background content refreshes.
- Stable owned slot identities, actual selected-page feedback, staged updates,
  persistent-order retries, reboot/missing-slot recovery and capacity-aware opt-out.
- Preserve other apps and their disabled state. Default mode remains available
  on core 10.2.0; selecting native mode on an older core reports upgrade guidance.
- Native behavior is covered by loopback firmware tests. Physical button and
  installed native-mode validation await a released supporting core.

## 0.1.0 — unreleased

First version: shows FiestaBoard pages on a Ulanzi TC001 (32 × 8) running
AWTRIX NG. Adapted from Oliver Rummeyer's Ulanzi TC002 plugin (0.2.0).

- Plugin id `ulanzi_tc001`, device model `ulanzi_tc001`, `fiestaboard_version`
  `>=10.2.0`.
- A **Text size** setting: one row of 8 characters (3×5) or one row of 5 (5×7).
- Each page is one plain 32 × 8 bitmap pushed as an app in the clock's
  rotation (no layout, no double-size drawing: the TC001 has neither).
  Transitions are streamed as paced frames.
- Tells a TC001 apart: `boardType` `awtrixng` and a 32 × 8 panel
  (`/api/v1/capabilities`). A TC002 and a wider ESP32 build are refused with a
  message that says why.
- Find my clock and Test connection accept only a 32 × 8 AWTRIX NG panel.
- Hardware checks on AWTRIX NG 1.2.2: all 256 framebuffer pixels match for
  RGB edges, both fonts, and resend after a simulated transport failure.
  Physical LED inspection and installed FiestaBoard checks remain pending.
- The diagnostic tool stops without writing when connection or device
  compatibility checks fail; regression coverage includes TC002, a wider
  matrix, and a server error.
