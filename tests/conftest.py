"""Shared fixtures: a mock AWTRIX NG clock on loopback and plugins pointed at it.

Every test talks to :class:`~tests.mock_awtrix.MockAwtrix` on 127.0.0.1; the
network fence (pytest-socket, ``--allow-hosts=127.0.0.1``) refuses anything
else, so no test can reach a real clock.

``make_plugin`` builds an :class:`AwtrixNGTC001` the way core does (the manifest's
``output`` block bound, ``open()`` called) and shortens the pacing constants
so tests run fast. Tests that are *about* pacing set them back explicitly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from plugins.ulanzi_tc001 import AwtrixNGTC001

from src.plugins.manifest import load_manifest

from .mock_awtrix import MockAwtrix

PLUGIN_DIR = Path(__file__).resolve().parent.parent
MANIFEST, _ERRORS = load_manifest(PLUGIN_DIR / "manifest.json")

#: The board's grid: 1 row x 8 columns of the 3x5 face on the 32 x 8 model.
ROWS, COLS = 1, 8


def grid(code: int) -> list[list[int]]:
    return [[code] * COLS for _ in range(ROWS)]


def render(frame) -> bytes:
    """A frame (0-71 codes or rich cells) as the 32 x 8 RGB888 a bound plugin sends."""
    return build({"host": "192.0.2.10"}).render(frame)


@pytest.fixture
def clock():
    device = MockAwtrix().start()
    yield device
    device.stop()


def build(config: dict, *, fast: bool = True) -> AwtrixNGTC001:
    plugin = AwtrixNGTC001("board-test", config)
    if MANIFEST is not None and MANIFEST.output is not None:
        plugin.bind_manifest(MANIFEST.output)
    if fast:
        plugin.STREAM_STEP_S = 0.0
        plugin.CONNECT_TIMEOUT_S = 0.5
        plugin.READ_TIMEOUT_S = 0.5
    plugin.open()
    return plugin


@pytest.fixture
def make_plugin(clock):
    built: list[AwtrixNGTC001] = []

    def factory(fast: bool = True, **config) -> AwtrixNGTC001:
        config.setdefault("host", clock.host)
        plugin = build(config, fast=fast)
        built.append(plugin)
        return plugin

    yield factory
    for plugin in built:
        plugin.close()
