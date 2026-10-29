"""The connection check and the between-writes poll against the mock clock."""

from __future__ import annotations

import pytest

from src.plugins import CancelToken, OutputHostBlocked

from .conftest import grid


def test_a_tc001_connects(clock, make_plugin):
    result = make_plugin().check_connection()
    assert result.success
    assert result.message == f"Connected to the TC001 at {clock.host} (AWTRIX NG 1.2.2)."
    assert result.details == {"version": "1.2.2", "hostname": "awtrixng-ab34cd", "currentApp": "Time"}
    assert clock.calls() == [("GET", "/api/v1/device"), ("GET", "/api/v1/capabilities")]


def test_a_tc002_is_refused_and_pointed_at_its_plugin(clock, make_plugin):
    clock.board_type = "tc002"
    result = make_plugin().check_connection()
    assert not result.success and result.failure == "bad_response"
    assert result.message == f"{clock.host} is a Ulanzi TC002, not a TC001."
    assert "Use the Ulanzi TC002 (AWTRIX NG) display instead." in result.troubleshooting
    assert ("GET", "/api/v1/capabilities") not in clock.calls()


def test_a_wider_esp32_build_is_refused(clock, make_plugin):
    clock.panel_width = 64
    result = make_plugin().check_connection()
    assert not result.success and result.failure == "bad_response"
    assert result.message == (
        f"{clock.host} is an AWTRIX NG clock 64 x 8; this display draws on the TC001's 32 x 8."
    )


def test_two_panels_of_32_are_a_wider_build_too(clock, make_plugin):
    clock.panels = 2
    assert "64 x 8;" in make_plugin().check_connection().message


def test_an_unknown_board_type_is_not_like_awtrix_ng(clock, make_plugin):
    clock.board_type = "esp8266"
    result = make_plugin().check_connection()
    assert not result.success and result.message.endswith("answered, but not like AWTRIX NG.")
    assert result.error == "boardType 'esp8266'"


@pytest.mark.parametrize("fault", ["no_display", "not_json"])
def test_capabilities_without_a_display_are_not_like_awtrix_ng(clock, make_plugin, fault):
    clock.capabilities_fault = fault
    result = make_plugin().check_connection()
    assert not result.success and result.failure == "bad_response"
    assert result.message == f"{clock.host} answered, but not like AWTRIX NG."
    assert any("Update AWTRIX NG" in step for step in result.troubleshooting)


def test_a_capabilities_500_is_a_server_error(clock, make_plugin):
    clock.fail_paths = ("/api/v1/capabilities",)
    assert make_plugin().check_connection().failure == "server_error"


def test_a_capabilities_401_is_auth(clock, make_plugin):
    clock.capabilities_fault = "unauthorized"
    result = make_plugin().check_connection()
    assert result.failure == "auth" and result.message == f"{clock.host} asks for a password."


def test_a_capabilities_timeout_is_a_timeout(clock, make_plugin):
    clock.capabilities_fault = "hang"
    result = make_plugin().check_connection()
    assert result.failure == "timeout"
    assert result.message == f"{clock.host} accepted the connection but did not answer."


def test_a_fenced_capabilities_read_is_blocked(clock, make_plugin, monkeypatch):
    plugin = make_plugin()
    monkeypatch.setattr(plugin, "_panel_size", lambda: (_ for _ in ()).throw(OutputHostBlocked(clock.host)))
    assert plugin.check_connection().failure == "blocked"


@pytest.mark.parametrize(
    ("mode", "failure"),
    [("http_500", "server_error"), ("garbage", "bad_response"), ("other_json", "bad_response")],
)
def test_a_device_that_is_not_a_working_clock_fails_the_check(clock, make_plugin, mode, failure):
    clock.mode = mode
    result = make_plugin().check_connection()
    assert not result.success and result.failure == failure


def test_a_password_is_asked_for(clock, make_plugin):
    clock.password = "s3cret"
    assert make_plugin().check_connection().failure == "auth"
    assert make_plugin(username="admin", password="s3cret").check_connection().success


def test_an_unreachable_or_silent_clock(clock, make_plugin):
    assert make_plugin(host="127.0.0.1:9").check_connection().failure == "unreachable"
    clock.mode = "hang"
    assert make_plugin().check_connection().failure == "timeout"


def test_no_address(make_plugin):
    result = make_plugin(host="").check_connection()
    assert not result.success and result.error == "No address"


def test_a_fenced_host_is_never_contacted(clock, make_plugin, monkeypatch):
    monkeypatch.setenv("FIESTABOARD_OUTPUTS_ALLOW_HOSTS", "192.0.2.99")
    result = make_plugin().check_connection()
    assert result.failure == "blocked"
    assert clock.requests == []


def test_the_host_setting_is_normalised(clock, make_plugin):
    plugin = make_plugin(host=f"HTTP://{clock.host}/some/path")
    assert plugin.host == clock.host
    assert plugin.device_key() == clock.host


# --- poll_device ------------------------------------------------------------------------------


def test_a_quiet_clock_has_no_news(clock, make_plugin):
    plugin = make_plugin()
    plugin.write(grid(1), native=None, cancel=CancelToken())
    assert plugin.poll_device() is None
    assert plugin.poll_device() is None


def test_a_restart_is_reported_so_core_sends_the_page_again(clock, make_plugin):
    plugin = make_plugin()
    plugin.write(grid(1), native=None, cancel=CancelToken())
    assert plugin.poll_device() is None

    clock.restart()
    poll = plugin.poll_device()

    assert poll is not None and poll.restarted
    assert plugin.poll_device() is None


def test_a_restart_long_ago_is_still_seen(clock, make_plugin):
    plugin = make_plugin()
    plugin.poll_device()
    was, seen_at = plugin._uptime
    # Last read an hour ago; the clock has been up ten minutes.
    plugin._uptime = (was, seen_at - 3600)
    clock.uptime_offset = -was + 600
    poll = plugin.poll_device()
    assert poll is not None and poll.restarted


def test_answering_again_after_a_failed_push_is_reported(clock, make_plugin):
    plugin = make_plugin()
    clock.mode = "http_500"
    plugin.write(grid(1), native=None, cancel=CancelToken())
    assert plugin.poll_device() is None  # still failing: nothing to say

    clock.mode = "ok"
    poll = plugin.poll_device()
    assert poll is not None and poll.restarted
    assert plugin.poll_device() is None


def test_no_address_or_no_answer_has_no_news(clock, make_plugin):
    assert make_plugin(host="").poll_device() is None
    assert make_plugin(host="127.0.0.1:9").poll_device() is None

