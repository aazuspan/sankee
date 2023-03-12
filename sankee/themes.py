from typing import Dict, Union


class Theme:
    def __init__(
        self,
        label_style: Union[None, str] = None,
        title_style: Union[None, str] = None,
        node_kwargs: Union[None, Dict] = None,
        link_kwargs: Union[None, Dict] = None,
    ):
        self.label_style = label_style
        self.title_style = title_style
        self.node_kwargs = node_kwargs if node_kwargs is not None else {}
        self.link_kwargs = link_kwargs if link_kwargs is not None else {}


DEFAULT = Theme(
    node_kwargs=dict(
        pad=30,
        thickness=10,
        line=dict(color="#505050", width=1.5),
    ),
    link_kwargs=dict(
        line=dict(color="#909090", width=1),
    ),
    label_style="""
        color: #fff;
        font-weight: 600;
        letter-spacing: -1px;
        text-shadow:
            0 0 4px black,
            -1px 1px 0 #76777a,
            1px 1px 0 #76777a,
            1px -1px 0 #76777a,
            -1px -1px 0 #76777a;
    """,
    title_style="""
        color: #fff;
        font-weight: 900;
        word-spacing: 10px;
        letter-spacing: 3px;
        text-shadow:
            0 0 1px black,
            0 0 2px black,
            0 0 4px black;
    """,
)


D3 = Theme(
    node_kwargs=dict(line=dict(width=1), pad=20, thickness=15),
    link_kwargs=dict(color="rgba(120, 120, 120, 0.25)"),
)

SIMPLE = Theme(
    node_kwargs=dict(line=dict(width=0), pad=60, thickness=30),
    link_kwargs=dict(color="rgba(120, 120, 120, 0.25)"),
    label_style="""
        color: #666666;
        font-size: 18px;
        color: #666666;
    """,
    title_style="""
        color: #666666;
        font-size: 24px;
        font-weight: 900;
    """,
)


THEMES = {
    "default": DEFAULT,
    "d3": D3,
    "simple": SIMPLE,
}


def load_theme(theme_name):
    if theme_name not in THEMES:
        raise ValueError(f"Theme `{theme_name}` not found. Choose from {list(THEMES.keys())}.")
    return THEMES[theme_name]
