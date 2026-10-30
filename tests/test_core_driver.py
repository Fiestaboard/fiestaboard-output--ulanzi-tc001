"""Core's driver adapter in front of the plugin, against the mock clock.

The plugin never spaces writes itself; core's floor (``min_interval_ms``
1000, keyed by ``device_key()``) does. This drives the plugin the way a board
does and checks the clock sees exactly what core lets through.
"""

from __future__ import annotations

import pytest

from src import plugins
from src.outputs.plugin_driver import OutputPluginDriver

from .conftest import grid


def test_core_keeps_the_one_second_floor_between_writes(clock, make_plugin):
    now = [10_000.0]
    driver = OutputPluginDriver(make_plugin(), clock=lambda: now[0])

    first = driver.send_characters(grid(1), with_outcome=True)
    assert (first.success, first.was_sent) == (True, True)

    now[0] += 0.5
    second = driver.send_characters(grid(2), with_outcome=True)
    assert second.throttled and not second.was_sent
    assert len(clock.pushes()) == 1


def test_a_dead_clock_is_a_failed_write_core_can_report(clock, make_plugin):
    clock.mode = "http_500"
    driver = OutputPluginDriver(make_plugin())
    result = driver.send_characters(grid(1), with_outcome=True)
    assert (result.success, result.was_sent) == (False, False)
    assert driver.last_write_error


def test_core_streams_a_page_change_through_the_models_flip(clock, make_plugin):
    now = [20_000.0]
    driver = OutputPluginDriver(make_plugin(), clock=lambda: now[0])
    assert driver.takes_transitions
    driver.send_characters(grid(1))
    now[0] += 2.0
    clock.clear()

    result = driver.render(grid(2), with_outcome=True)

    assert (result.success, result.was_sent) == (True, True)
    assert len(clock.pushes()) > 1


@pytest.mark.skipif(not hasattr(OutputPluginDriver, "sync_native_playlist"), reason="Native playlist core required")
def test_core_playlist_contract_reaches_hardware_slots_and_reports_selected_page(clock, make_plugin):
    now = [30_000.0]
    driver = OutputPluginDriver(make_plugin(native_rotation=True), clock=lambda: now[0])
    value = plugins.NativePlaylist("board-test", "collection:demo", (
        plugins.NativePlaylistEntry("clock", plugins.cells_from_codes(grid(1)), 30000),
        plugins.NativePlaylistEntry("art", plugins.cells_from_codes(grid(2)), 30000),
    ))
    assert driver.native_rotation_enabled is True
    result = driver.sync_native_playlist(value, with_outcome=True)
    assert result.success and result.was_sent
    names = list(clock.apps)
    assert len(names) == 2
    assert clock.bitmap(clock.apps[names[1]]) == driver.plugin.render(grid(2))
    clock.current_app = names[1]
    assert driver.poll_device().native_selection.page_id == "art"
    now[0] += 2
    clock.clear()
    result = driver.sync_native_playlist(value, with_outcome=True)
    assert result.success and not result.was_sent
    assert clock.pushes() == [] and clock.switches() == []
    now[0] += 2
    assert driver.send_characters(grid(3), with_outcome=True).success
    assert list(clock.apps) == ["FiestaBoard"]
