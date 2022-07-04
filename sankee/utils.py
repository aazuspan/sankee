import colorsys
import itertools

import ipywidgets as widgets
import matplotlib.colors as mc


def get_missing_keys(key_list, key_dict):
    """
    Find any keys that are present in a list that are not present in the keys of a dictionary.
    Helpful for testing if a label or palette dictionary is fully defined.
    """
    return [key for key in key_list if key not in key_dict.keys()]


def pairwise(iterable):
    """Polyfill itertools.pairwise for pre 3.10.

    https://docs.python.org/3/library/itertools.html#itertools.pairwise
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def adjust_lightness(color, amount=0.5):
    c = colorsys.rgb_to_hls(*mc.to_rgb(color))
    scaled = colorsys.hls_to_rgb(c[0], max(0, min(1, 1 - amount * c[1])), c[2])
    return rgb_to_hex(scaled)


def rgb_to_hex(rgb):
    rgb = [int(c * 255) for c in rgb]
    return "#%02x%02x%02x" % tuple(rgb)


class ColorToggleButton(widgets.Button):
    """
    The ipywidgets.ToggleButton doesn't support a `button_color` style, so this turns a standard
    ipywidgets.Button into a toggle button.
    """

    def __init__(self, *args, on_color, off_color=None, state=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state
        self.on_color = on_color
        self.off_color = off_color if off_color is not None else adjust_lightness(on_color, 0.12)

        current_color = on_color if state else off_color
        self.style.button_color = current_color

    def toggle(self):
        self.state = not self.state
        color = self.on_color if self.state else self.off_color

        self.style.button_color = color
