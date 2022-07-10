import itertools

import ipywidgets as widgets


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


class ColorToggleButton(widgets.Button):
    """
    The ipywidgets.ToggleButton doesn't support a `button_color` style, so this turns a standard
    ipywidgets.Button into a toggle button.
    """

    def __init__(self, *args, on_color, off_color=None, state=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state
        self.on_color = on_color
        # Set an alpha value for the default off color
        self.off_color = off_color if off_color is not None else f"{on_color}20"
        current_color = on_color if state else self.off_color
        self.style.button_color = current_color
        self.layout.border = f"1px dashed {self.on_color}"

    def toggle(self):
        self.state = not self.state
        self.update()

    def update(self):
        color = self.on_color if self.state else self.off_color
        self.style.button_color = color
