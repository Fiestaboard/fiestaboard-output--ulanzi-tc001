"""Rendering: core's 32 x 8 layout is the panel, in either face.

Core binds a board to a copy of the model with its chosen face swapped in
(``board_device_model`` / ``bind_board``); the plugin lays out from
``self.device_model`` and needs no font code of its own.
"""

from __future__ import annotations

from plugins.ulanzi_tc001 import PANEL_HEIGHT, PANEL_WIDTH

from src.led.matrix import BOARD_COLORS, LedBitmapLayer, model_with_led_font

from .conftest import MANIFEST, build, grid

WIDTH, HEIGHT = 32, 8


def pixel(pixels: bytes, x: int, y: int) -> tuple[int, int, int]:
    i = (y * WIDTH + x) * 3
    return tuple(pixels[i : i + 3])


def lit_columns(pixels: bytes) -> list[int]:
    return [x for x in range(WIDTH) if any(any(pixel(pixels, x, y)) for y in range(HEIGHT))]


def lit_rows(pixels: bytes) -> list[int]:
    return [y for y in range(HEIGHT) if any(any(pixel(pixels, x, y)) for x in range(WIDTH))]


def cells_drawn(pixels: bytes, cell_width: int) -> int:
    """How many *cell_width*-pixel cells across the panel have a lit pixel."""
    cols = set(lit_columns(pixels))
    return sum(1 for c in range(WIDTH // cell_width) if cols & set(range(c * cell_width, (c + 1) * cell_width)))


def board(face: str):
    """A plugin the way core builds it for a board whose output_config font is *face*."""
    plugin = build({"host": "192.0.2.10", "font": face})
    model = MANIFEST.output.model(0)
    plugin.bind_board(device_model=dict(model_with_led_font(model, face)))
    return plugin


def letters(count: int) -> list[list[int]]:
    return [list(range(1, count + 1))]  # codes 1.. are A, B, C ...


def test_a_frame_is_32x8_rgb888():
    pixels = build({"host": "192.0.2.10"}).render(grid(1))
    assert (PANEL_WIDTH, PANEL_HEIGHT) == (WIDTH, HEIGHT)
    assert len(pixels) == 32 * 8 * 3


def test_8_characters_fit_at_3x5():
    pixels = board("3x5").render(letters(8))
    assert len(pixels) == 32 * 8 * 3
    assert cells_drawn(pixels, 4) == 8
    assert lit_rows(pixels) == [1, 2, 3, 4, 5]


def test_5_characters_fit_at_5x7():
    plugin = board("5x7")
    layout = plugin.layout([[0] * 5])
    assert (layout.grid.rows, layout.grid.cols) == (1, 5)
    pixels = plugin.render(letters(5))
    assert len(pixels) == 32 * 8 * 3
    assert cells_drawn(pixels, 6) == 5
    assert lit_rows(pixels) == [0, 1, 2, 3, 4, 5, 6]


def test_colour_tiles_draw_in_board_colours():
    pixels = board("3x5").render([[63] + [0] * 7])
    red = tuple(int(BOARD_COLORS["red"][i : i + 2], 16) for i in (1, 3, 5))
    assert pixel(pixels, 1, 3) == red
    assert pixel(pixels, 20, 3) != red


def test_a_canvas_layer_draws_over_the_text():
    class Frame(list):
        layers = (LedBitmapLayer(x=0, y=0, width=2, height=2, rgba=bytes([0, 255, 0, 255]) * 4),)

    plugin = build({"host": "192.0.2.10"})
    plain = plugin.render(letters(8))
    layered = plugin.render(Frame(letters(8)))
    assert layered != plain
    assert pixel(layered, 0, 0) == pixel(layered, 1, 1) == (0, 255, 0)
    assert pixel(plain, 0, 0) != (0, 255, 0)


def test_nothing_is_squeezed_the_layout_is_the_panel():
    import plugins.ulanzi_tc001 as module

    assert not hasattr(module, "squeeze")
    assert not hasattr(module, "GAP_ROW")


def test_rich_cells_and_codes_draw_the_same_page():
    from src.plugins import cells_from_codes

    plugin = build({"host": "192.0.2.10"})
    codes = [[8, 9, 0, 63, 1, 2, 3, 4]]
    assert plugin.render(codes) == plugin.render(cells_from_codes(codes))
