# Changelog

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
