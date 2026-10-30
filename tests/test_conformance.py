"""FiestaBoard core's output-plugin conformance suite, run against this plugin.

The suite plays core and clock both: it routes the plugin's device helper
(``self.http``) to its fake transport, so the plugin's real request code runs.
Core decodes pushed frames only for plugins that play a ``sequence``; this
plugin streams, so that rule is skipped and ``decode`` is not exercised by
the suite. ``decode`` is kept (it matches a pushed bitmap against the uniform
grids) for a core that does; the frame pixels are checked in test_writes.py.

The pacing constants stay at their shipped values here: conformance is about
the plugin as it ships.
"""

from __future__ import annotations

from functools import cache

from plugins.ulanzi_tc001 import AwtrixNGTC001

from src.outputs.conformance import OutputConformanceSuite

from .conftest import PLUGIN_DIR, grid
from .conftest import render as render_frame
from .mock_awtrix import MockAwtrix


@cache
def _uniform_grids() -> dict[bytes, tuple[tuple[int, ...], ...]]:
    grids = {}
    for code in range(72):
        frame = grid(code)
        grids.setdefault(render_frame(frame), tuple(tuple(row) for row in frame))
    return grids


def decode(payload):
    if not isinstance(payload, dict) or "draw" not in payload:
        return None
    found = _uniform_grids().get(MockAwtrix.bitmap(payload))
    return None if found is None else [list(row) for row in found]


def make_plugin(board_id, config, transport):
    # The suite routes self.http to its fake device itself.
    if not getattr(transport, "_awtrix_inventory", False):
        original = transport.http_send

        def http_send(request):
            # Preserve the suite's latency, recording and injected failures;
            # specialize only the actual firmware inventory response shape.
            response = original(request)
            if request.method == "GET" and request.url.endswith("/api/v1/apps"):
                response._content = b"[]"
            return response

        transport.http_send = http_send
        transport._awtrix_inventory = True
    return AwtrixNGTC001(board_id, config)


def test_the_plugin_is_conformant():
    report = OutputConformanceSuite(
        plugin_dir=PLUGIN_DIR,
        factory=make_plugin,
        config={"host": "192.0.2.10", "username": "admin", "password": "s3cret-pass"},
        decode=decode,
    ).assert_conformant()
    # Every rule ran (device_key's secret check included) except sequence.
    assert sorted(report.skipped) == ["sequence: [ulanzi_tc001] animation is 'stream'"], report.skipped
