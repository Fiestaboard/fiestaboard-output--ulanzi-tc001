"""Native app rotation over real loopback HTTP; no hardware or AI calls."""
from types import SimpleNamespace
from threading import Event

import pytest

from src import plugins
from src.plugins import CancelToken, cells_from_codes

pytestmark = pytest.mark.skipif(not hasattr(plugins, "NativePageSelection"), reason="Native playlist core SDK required")

from .conftest import grid


def playlist(*pages, reference="collection:demo", duration=30000):
    return SimpleNamespace(board_id="board-test", reference_id=reference, entries=tuple(
        SimpleNamespace(page_id=page_id, cells=cells_from_codes(grid(code)), duration_ms=duration)
        for page_id, code in pages
    ))


def sync(plugin, value):
    return plugin.sync_native_playlist(value, cancel=CancelToken())


def owned(clock):
    return [name for name in clock.apps if name.startswith("fb_")]


def test_timed_members_become_ordered_slots_with_full_pixels_and_duration(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    result = sync(plugin, playlist(("clock", 1), ("art", 2)))
    assert result.success and result.was_sent
    names = owned(clock)
    assert len(names) == 2
    assert [clock.bitmap(clock.apps[n]) for n in names] == [plugin.render(grid(1)), plugin.render(grid(2))]
    assert [clock.apps[n]["durationMs"] for n in names] == [30000, 30000]
    assert clock.order[-2:] == names
    assert clock.current_app == names[0]


def test_refresh_preserves_button_selection_and_deduplicates_payloads(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    value = playlist(("clock", 1), ("art", 2))
    sync(plugin, value)
    names = owned(clock)
    clock.current_app = names[1]  # a firmware-side button selected the second app
    clock.clear()
    result = sync(plugin, value)
    assert result.success and not result.was_sent
    assert clock.pushes() == [] and clock.switches() == []
    assert clock.current_app == names[1]
    result = sync(plugin, playlist(("clock", 3), ("art", 2)))
    assert result.success
    assert len(clock.pushes()) == 1 and clock.switches() == []
    assert clock.current_app == names[1]


def test_reorder_cleanup_preserves_foreign_apps_and_disabled_battery(make_plugin, clock):
    clock.apps["other_owner"] = {"text": "OTHER"}
    clock.order = ["Time", "other_owner", "Battery"]
    clock.disabled = ["Battery", "Date"]
    plugin = make_plugin(native_rotation=True)
    sync(plugin, playlist(("clock", 1), ("art", 2)))
    old = owned(clock)
    result = sync(plugin, playlist(("art", 2), reference="art", duration=0))
    assert result.success
    assert owned(clock) == [old[1]]
    assert clock.order == ["Time", "other_owner", "Battery", "Date", "Temperature", "Humidity", old[1]]
    assert set(clock.disabled) == {"Battery", "Date"}
    assert clock.apps["other_owner"] == {"text": "OTHER"}


def test_capacity_failure_does_not_change_existing_rotation(make_plugin, clock):
    clock.apps.update({f"foreign{i}": {"text": str(i)} for i in range(49)})
    plugin = make_plugin(native_rotation=True)
    result = sync(plugin, playlist(("clock", 1), ("art", 2)))
    assert not result.success
    assert len(clock.apps) == 49 and clock.order == []
    assert not any(method != "GET" for method, _ in clock.calls())


def test_reboot_restores_slots_and_process_restart_preserves_selected_member(make_plugin, clock):
    first = make_plugin(native_rotation=True)
    value = playlist(("clock", 1), ("art", 2))
    sync(first, value)
    names = owned(clock)
    clock.current_app = names[1]
    second = make_plugin(native_rotation=True)
    clock.clear()
    assert sync(second, value).success
    assert clock.current_app == names[1] and clock.switches() == []
    clock.restart()
    assert sync(second, value).success
    assert owned(clock) == names
    assert clock.current_app == names[0]


def test_recreated_opt_out_retires_only_owned_slots_after_legacy_push(make_plugin, clock):
    clock.apps["foreign"] = {"text": "KEEP"}
    clock.disabled = ["Battery"]
    sync(make_plugin(native_rotation=True), playlist(("clock", 1), ("art", 2)))
    legacy = make_plugin(native_rotation=False)
    result = legacy.write(grid(3), native=None, cancel=CancelToken())
    assert result.success
    assert not owned(clock)
    assert clock.apps["foreign"] == {"text": "KEEP"}
    assert clock.bitmap(clock.apps[legacy.app_name]) == legacy.render(grid(3))
    assert clock.disabled == ["Battery"]


def test_partial_push_stays_out_of_rotation_and_retry_converges(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    value = playlist(("clock", 1), ("art", 2))
    def fail_second(method, path, body, index):
        if method == "PUT" and "/pushed/" in path and clock.apps:
            clock.fail_paths = (path,)
    clock.on_request = fail_second
    assert not sync(plugin, value).success
    assert all(name in clock.disabled for name in owned(clock))
    assert clock.current_app == "Time"
    clock.on_request = None
    clock.fail_paths = ()
    # A process restart during an interrupted update must also converge.
    assert sync(make_plugin(native_rotation=True), value).success
    assert len(owned(clock)) == 2
    assert not set(owned(clock)) & set(clock.disabled)


def test_missing_slot_is_reported_as_restart_and_current_member_as_feedback(make_plugin, clock):
    from src import plugins
    if not hasattr(plugins, "NativePageSelection"):
        pytest.skip("Selection feedback needs the native playlist core SDK")
    plugin = make_plugin(native_rotation=True)
    sync(plugin, playlist(("clock", 1), ("art", 2)))
    names = owned(clock)
    clock.current_app = names[1]
    news = plugin.poll_device()
    assert news.native_selection.page_id == "art"
    assert news.restarted is False
    del clock.apps[names[0]]
    assert plugin.poll_device().restarted is True
    clock.current_app = "Battery"
    assert plugin.poll_device().native_selection.page_id is None


def test_default_legacy_output_does_not_touch_other_owners_native_slots(make_plugin, clock):
    clock.apps["fb_000000000000_111111111111"] = {"text": "FOREIGN"}
    plugin = make_plugin()
    assert plugin.write(grid(1), native=None, cancel=CancelToken()).success
    assert clock.apps["fb_000000000000_111111111111"] == {"text": "FOREIGN"}


def test_cancel_before_sync_performs_no_device_requests(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    event = Event()
    event.set()
    token = CancelToken(event)
    result = plugin.sync_native_playlist(playlist(("clock", 1)), cancel=token)
    assert result.superseded and not result.was_sent
    assert clock.calls() == []


def test_duplicate_page_uses_one_payload_and_repeated_order_slot(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    assert sync(plugin, playlist(("clock", 1), ("art", 2), ("clock", 1))).success
    names = owned(clock)
    assert len(names) == 2
    assert clock.order[-3:] == [names[0], names[1], names[0]]


def test_foreign_active_slot_is_not_stolen_by_refresh(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    sync(plugin, playlist(("clock", 1)))
    clock.current_app = "Time"
    clock.clear()
    assert sync(plugin, playlist(("clock", 2))).success
    assert clock.current_app == "Time" and clock.switches() == []


@pytest.mark.parametrize("board_type,width", [("tc002", 52), ("awtrixng", 64)])
def test_wrong_hardware_receives_no_native_writes(make_plugin, clock, board_type, width):
    clock.board_type, clock.panel_width = board_type, width
    assert not sync(make_plugin(native_rotation=True), playlist(("clock", 1))).success
    assert all(method == "GET" for method, _ in clock.calls())


def test_fifty_apps_fit_but_one_more_preserves_them(make_plugin, clock):
    clock.apps.update({f"foreign{i}": {"text": str(i)} for i in range(49)})
    plugin = make_plugin(native_rotation=True)
    assert sync(plugin, playlist(("clock", 1))).success
    clock.clear()
    assert not sync(plugin, playlist(("clock", 1), ("art", 2))).success
    assert len(clock.apps) == 50
    assert all(method == "GET" for method, _ in clock.calls())


def test_empty_playlist_retires_owned_slots_without_removing_foreign_apps(make_plugin, clock):
    clock.apps["foreign"] = {"text": "KEEP"}
    plugin = make_plugin(native_rotation=True)
    sync(plugin, playlist(("clock", 1)))
    assert sync(plugin, playlist()).success
    assert not owned(clock) and clock.apps == {"foreign": {"text": "KEEP"}}


def test_old_core_rejects_opt_in_with_upgrade_guidance_without_writing(make_plugin, clock, monkeypatch):
    import plugins.ulanzi_tc001 as output
    monkeypatch.setattr(output, "NativePageSelection", None)
    plugin = make_plugin(native_rotation=True)
    check = plugin.check_connection()
    assert not check.success and "upgrade" in check.message.lower()
    assert not plugin.write(grid(1), native=None, cancel=CancelToken()).success
    assert clock.calls() == []


def test_firmware_modules_do_not_block_native_or_legacy_output(make_plugin, clock):
    clock.modules = ["helper_library"]
    plugin = make_plugin(native_rotation=True)
    assert sync(plugin, playlist(("clock", 1))).success
    assert plugin.write(grid(2), native=None, cancel=CancelToken()).success
    assert "helper_library" not in clock.order
    assert not any(method == "DELETE" and path.endswith("helper_library") for method, path in clock.calls())


def test_full_native_capacity_can_opt_out_to_legacy_slot(make_plugin, clock):
    value = playlist(*[(f"page{i}", 1) for i in range(50)])
    assert sync(make_plugin(native_rotation=True), value).success
    plugin = make_plugin(native_rotation=False)
    assert plugin.write(grid(2), native=None, cancel=CancelToken()).success
    assert list(clock.apps) == ["FiestaBoard"]
    assert clock.bitmap(clock.apps["FiestaBoard"]) == plugin.render(grid(2))


@pytest.mark.parametrize("recreate", [False, True])
def test_applied_but_unsaved_order_is_retried_until_persisted(make_plugin, clock, recreate):
    plugin = make_plugin(native_rotation=True)
    assert sync(plugin, playlist(("clock", 1), ("art", 2))).success
    clock.unsaved_order_once = True
    reordered = playlist(("art", 2), ("clock", 1))
    assert not sync(plugin, reordered).success
    assert clock.saved_order != clock.order
    if recreate:
        plugin = make_plugin(native_rotation=True)
    assert sync(plugin, reordered).success
    assert clock.saved_order == clock.order
    assert clock.saved_disabled == clock.disabled


def test_module_with_owned_name_is_never_overwritten(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    value = playlist(("clock", 1))
    assert sync(plugin, value).success
    name = owned(clock)[0]
    clock.apps.clear()
    clock.modules = [name]
    clock.clear()
    assert not sync(plugin, value).success
    assert all(method == "GET" for method, _ in clock.calls())


def test_cancellation_during_validation_is_superseded_without_more_requests(make_plugin, clock):
    plugin = make_plugin(native_rotation=True)
    event = Event()
    token = CancelToken(event)
    clock.on_request = lambda *_: event.set()
    with plugin.http.cancel_scope(token):
        result = plugin.sync_native_playlist(playlist(("clock", 1)), cancel=token)
    assert result.superseded and not plugin._upload_failed
    assert clock.calls() == [("GET", "/api/v1/device")]
