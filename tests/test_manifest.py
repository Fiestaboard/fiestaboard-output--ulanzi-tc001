"""The manifest and the device data agree with what the plugin does."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.plugins import led_spec_for_model

from .conftest import _ERRORS, COLS, MANIFEST, ROWS

ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_JSON = json.loads((ROOT / "manifest.json").read_text())


def test_the_manifest_loads_as_an_output_plugin():
    assert _ERRORS == []
    assert MANIFEST.id == "ulanzi_tc001"
    assert MANIFEST.name == "Ulanzi TC001 (AWTRIX NG)"
    assert MANIFEST.version == "0.1.0"
    assert MANIFEST.plugin_type == "output"
    assert _MANIFEST_JSON["fiestaboard_version"] == ">=10.2.0"


def test_the_capabilities_come_from_the_tc001_model():
    caps = MANIFEST.output.capabilities
    assert caps.technology == "led_matrix"
    assert caps.delivery == "push"
    assert caps.animation == "stream"
    assert caps.min_interval_ms == 1000
    assert caps.read_back.supported is False
    assert caps.native_transitions == frozenset()
    assert caps.device_models == ("ulanzi_tc001",)


def test_the_model_is_the_panel_itself():
    model = MANIFEST.output.model(0)
    assert model["label"] == "Ulanzi TC001 (AWTRIX NG)"
    assert model["family"] == "awtrix_ng"
    assert model["geometry"] == {"kind": "pixels", "width": 32, "height": 8}
    assert model["color"] == {"kind": "rgb", "bitDepth": 24}
    assert model["font"] == "3x5" and model["charset"] == "led_3x5"
    spec = led_spec_for_model(model)
    assert (spec.width, spec.height, spec.font) == (32, 8, "3x5")


def test_the_text_size_is_offered_in_the_model_and_the_settings():
    model = MANIFEST.output.model(0)
    assert model["layoutOptions"]["font"] == {"allowed": ["3x5", "5x7"], "default": "3x5"}
    font = MANIFEST.output.settings_schema["properties"]["font"]
    assert font["type"] == "string" and font["title"] == "Text size"
    assert font["enum"] == ["3x5", "5x7"]
    assert font["enumNames"] == ["Small — 8 characters", "Large — 5 characters"]
    assert font["default"] == "3x5"


def test_the_board_is_one_row_of_eight_and_one_of_five_in_the_large_face():
    from src.outputs.geometry import grid_floor, model_cell_grid
    from src.led.matrix import model_with_led_font
    from src.outputs.geometry import resolve_content_grid

    model = MANIFEST.output.model(0)
    assert model_cell_grid(model, None) == (ROWS, COLS) == (1, 8)
    assert (ROWS, COLS) >= grid_floor(model)
    assert resolve_content_grid(model, None, None) == (1, 8)
    assert resolve_content_grid(model_with_led_font(model, "5x7"), None, None) == (1, 5)


def test_only_the_password_is_secret():
    props = MANIFEST.output.settings_schema["properties"]
    assert set(props) == {
        "host",
        "app_name",
        "show_on_change",
        "duration_s",
        "font",
        "tile_gap",
        "block_padding",
        "fade_style",
        "username",
        "password",
    }
    secret = {name for name, p in props.items() if p.get("secret") or p.get("ui:widget") == "password"}
    assert secret == {"password"}


def test_the_address_field_is_a_device_picker_bound_to_find_my_clock():
    host = MANIFEST.output.settings_schema["properties"]["host"]
    assert host["ui:widget"] == "device-picker"
    assert host["ui:options"] == {"action": "find_awtrix", "value_key": "host", "label_key": "label"}
    actions = [a.id for a in MANIFEST.output.actions]
    assert actions == ["find_awtrix", "test_connection"]


def test_the_app_name_pattern_is_the_clocks():
    app_name = MANIFEST.output.settings_schema["properties"]["app_name"]
    # The clock's names, or none: FiestaBoard's settings form leaves the default out, and an
    # empty field then means FiestaBoard rather than failing to save.
    assert app_name["pattern"] == "^([A-Za-z0-9_-]{1,32})?$"
    assert re.match(app_name["pattern"], "")
    assert app_name["default"] == "FiestaBoard"


def test_the_display_catalog_finds_it_by_device_and_firmware():
    display = _MANIFEST_JSON["display"]
    assert display["manufacturer"] == "Ulanzi"
    assert display["models"] == ["TC001"]
    assert "TC001" in display["keywords"]
    assert "AWTRIX NG" in display["keywords"]


def test_the_data_package_has_the_manifests_version_and_only_the_device_data():
    package = json.loads((ROOT / "package.json").read_text())
    assert package["version"] == _MANIFEST_JSON["version"]
    assert package["files"] == ["output/*.json"]
    assert package["private"] is True
