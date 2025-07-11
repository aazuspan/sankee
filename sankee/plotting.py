from __future__ import annotations

from collections import namedtuple
from typing import Literal

import ee
import ipywidgets as widgets
import pandas as pd
import plotly.graph_objects as go

from sankee import sampling, themes, utils

SankeyParameters = namedtuple(
    "SankeyParameters",
    [
        "node_labels",
        "link_labels",
        "node_palette",
        "link_palette",
        "label",
        "source",
        "target",
        "value",
    ],
)


def sankify(
    image_list: list[ee.Image],
    band: str,
    labels: dict[int, str],
    palette: dict[int, str],
    region: None | ee.Geometry = None,
    label_list: None | list[str] = None,
    max_classes: None | int = None,
    n: int = 500,
    title: None | str = None,
    scale: None | int = None,
    seed: int = 0,
    label_type: None | Literal["class", "percent", "count"] = "class",
    theme: str | themes.Theme = "default",
) -> SankeyPlot:
    """
    Generate an interactive Sankey plot showing land cover change over time from a series of images.

    Parameters
    ----------
    image_list : List[ee.Image]
        An ordered list of images representing a time series of classified data. Each image will be
        sampled to generate the Sankey plot. Any length of list is allowed, but lists with more than
        3 or 4 images may produce unusable plots.
    band : str
        The name of the band in all images of image_list that contains classified data.
    labels : dict
        The labels associated with each value of all images in image_list. Any values not defined
        in the labels will be dropped from the sampled data.
    palette : dict
        The colors associated with each value of all images in image_list.
    region : ee.Geometry, default None
        A region to generate samples within. The region must overlap all images. If none is
        provided, the geometry of the first image will be used. For this to work, images must be
        bounded.
    label_list : List[str], default None
        An ordered list of labels corresponding to the images. The list must be the same length as
        image_list. If none is provided, sequential numeric labels will be automatically assigned
        starting at 0. Labels are displayed on-hover on the Sankey nodes.
    max_classes : int, default None
        If a value is provided, small classes will be removed until max_classes remain. Class size
        is calculated based on total times sampled in the time series.
    n : int, default 500
        The number of sample points to randomly generate for characterizing all images. More samples
        will provide more representative data but will take longer to process.
    title : str, default None
        An optional title that will be displayed above the Sankey plot.
    scale : int, default None
        The scale in image units to perform sampling at. If none is provided, GEE will attempt to
        use the image's nominal scale, which may cause errors depending on the image projection.
    seed : int, default 0
        The seed value used to generate repeatable results during random sampling.
    label_type : str, default "class"
        The type of label to display for each link, one of "class", "percent", "count", or None.
        Selecting "class" will use the class label, "percent" will use the proportion of sampled
        pixels in each class, and "count" will use the number of sampled pixels in each class.
        None will disable link labels.
    theme : str or Theme
        The theme to apply to the Sankey diagram. Can be the name of a built-in theme (e.g. "d3") or
        a custom `sankee.Theme` object.

    Returns
    -------
    SankeyPlot
        An interactive Sankey plot widget.
    """
    if region is None:
        region = image_list[0].geometry()

    label_list = label_list if label_list is not None else list(range(len(image_list)))
    label_list = [str(label) for label in label_list]
    if len(label_list) != len(image_list):
        raise ValueError("The number of labels must match the number of images.")
    if len(set(label_list)) != len(label_list):
        raise ValueError("All labels in the `label_list` must be unique.")

    data, samples = sampling.generate_sample_data(
        image_list=image_list,
        image_labels=label_list,
        band=band,
        scale=scale,
        include=list(labels.keys()),
        max_classes=max_classes,
        region=region,
        n=n,
        seed=seed,
    )

    return SankeyPlot(
        data=data,
        labels=labels,
        palette=palette,
        title=title,
        samples=samples,
        label_type=label_type,
        theme=theme,
    )


class SankeyPlot(widgets.DOMWidget):
    def __init__(
        self,
        *,
        data: pd.DataFrame,
        labels: dict[int, str],
        palette: dict[int, str],
        title: str,
        samples: ee.FeatureCollection,
        label_type: None | Literal["class", "percent", "count"],
        theme: str | themes.Theme,
    ):
        self.data, self.labels, self.palette = self._merge_duplicate_classes(data, labels, palette)

        self.title = title
        self.samples = samples
        self.label_type = label_type
        self.theme = theme if isinstance(theme, themes.Theme) else themes.load_theme(theme)

        self.hide = []
        # Initialized by `self.generate_plot`
        self.df = None
        self.plot = self._generate_figurewidget()
        self.gui = self._generate_gui()

    def _merge_duplicate_classes(self, data, labels, palette):
        """
        Combine classes with duplicated labels and colors into a single class.

        This allows classes that are distinct in the sampled image to be aggregated at the plotting
        stage, which is more efficient.
        """
        # A mapping of (color, label) to the first sampled value associated with that pair.
        running_map: dict[tuple[str, str], int] = {}
        remap: dict[int, int] = {}

        # If a label-color pair is repeated with different values, remap the values to the first
        # occurrence of that label-color pair.
        for key, label, color in zip(labels.keys(), labels.values(), palette.values()):
            if (color, label) in running_map:
                prev_key = running_map[(color, label)]
                remap[key] = prev_key
            else:
                running_map[(color, label)] = key

        # Grab the distinct color and label with their associated value
        palette = {v: k[0] for k, v in running_map.items()}
        labels = {v: k[1] for k, v in running_map.items()}
        # Apply the value remapping to merge classes
        data = data.replace(remap)

        return data, labels, palette

    def _get_sorted_classes(self) -> pd.Series:
        """Return all unique class values, sorted by the total number of observations."""
        start_count = (
            self.df.loc[:, ["source", "total"]]
            .groupby("source")
            .mean()
            .reset_index()[["source", "total"]]
            .rename(columns={"source": "class", "total": "count"})
        )
        end_count = (
            self.df.loc[:, ["target", "changed"]]
            .groupby("target")
            .sum()
            .reset_index()[["target", "changed"]]
            .rename(columns={"target": "class", "changed": "count"})
        )
        total_count = pd.concat([start_count, end_count]).groupby("class").sum().reset_index()

        return total_count.sort_values(by="count", ascending=False)["class"].reset_index(drop=True)

    def _get_active_classes(self) -> pd.Series:
        """Return all unique active, visibile class values after filtering."""
        return self.df[["source", "target"]].melt().value.unique()

    def _generate_plot_parameters(self) -> SankeyParameters:
        """Generate Sankey plot parameters from a formatted, cleaned dataframe"""
        df = self.df.copy()

        source_df = df[["source", "source_year"]].rename(
            columns={"source": "class", "source_year": "year"}
        )
        target_df = df[["target", "target_year"]].rename(
            columns={"target": "class", "target_year": "year"}
        )
        all_classes = pd.concat([source_df, target_df])

        all_classes = all_classes.drop_duplicates().reset_index(drop=True)
        all_classes["color"] = all_classes["class"].apply(lambda k: self.palette[k]).tolist()
        all_classes["id"] = all_classes.groupby(["year", "class"], sort=False).ngroup()

        # Join the sequential class-year IDs to the dataframe
        df["source_id"] = pd.merge(
            left=df,
            right=all_classes,
            how="left",
            left_on=["source_year", "source"],
            right_on=["year", "class"],
        )["id"]
        df["target_id"] = pd.merge(
            left=df,
            right=all_classes,
            how="left",
            left_on=["target_year", "target"],
            right_on=["year", "class"],
        )["id"]

        # Calculate the proportion of each class in each year
        melted = self.data.melt(var_name="year")
        melted = melted.groupby(["year", "value"]).size().reset_index(name="count")
        melted["proportion_of_total"] = (
            melted.groupby("year")["count"]
            .transform(lambda x: x / x.sum())
            .apply(lambda x: f"{x:.0%}")
        )
        all_classes = all_classes.merge(
            melted, left_on=["year", "class"], right_on=["year", "value"]
        )

        if self.label_type == "class":
            all_classes["label"] = all_classes["class"].apply(lambda k: self.labels[k])
        elif self.label_type == "percent":
            all_classes["label"] = all_classes["proportion_of_total"]
        elif self.label_type == "count":
            all_classes["label"] = all_classes["count"]
        elif not self.label_type:
            all_classes["label"] = ""
        else:
            raise ValueError(
                "Invalid label_type. Choose from 'class', 'percent', 'count', or None."
            )

        return SankeyParameters(
            node_labels=all_classes.year,
            link_labels=df.link_label,
            node_palette=all_classes.color,
            link_palette=df.source_color,
            label=all_classes.label,
            source=df.source_id,
            target=df.target_id,
            value=df.changed,
        )

    def _generate_dataframe(self) -> pd.DataFrame:
        """Convert raw sampling data to a formatted dataframe"""
        data = self.data.copy()

        if self.hide:
            hide_mask = pd.concat([(data == i).any(axis=1) for i in self.hide], axis=1).any(axis=1)
            data = data[~hide_mask]

        permutations = []
        # Get all unique class-year combinations
        for source, target in utils.pairwise(data.columns):
            permutations += list(
                zip([source] * len(data), [target] * len(data), data[source], data[target])
            )
        df = pd.DataFrame(permutations, columns=["source_year", "target_year", "source", "target"])

        # Count the unique combinations of all four fields
        df = (
            df.groupby(["source_year", "target_year", "source", "target"])
            .size()
            .reset_index()
            .rename(columns={0: "changed"})
        )
        # Count the total number of source samples in each year
        df["total"] = df.groupby(["source_year", "source"]).changed.transform("sum")
        # Calculate what percent of the source samples went into each target class
        df["proportion"] = df["changed"] / df["total"]

        # Join the class labels and colors to the class IDs
        df["source_label"] = df.source.apply(lambda k: self.labels[k])
        df["target_label"] = df.target.apply(lambda k: self.labels[k])
        df["source_color"] = df.source.apply(lambda k: self.palette[k])
        df["target_color"] = df.target.apply(lambda k: self.palette[k])

        def build_link_label(row: pd.Series) -> str:
            # Early exit in case all classes are excluded
            if row.shape[0] == 0:
                return ""

            verb = "remained" if row.source == row.target else "became"
            pct = f"{row.proportion:.0%}"
            return f"<b>{pct}</b> of <b>{row.source_label}</b> {verb} <b>{row.target_label}</b>"

        # Describe the class changes
        df["link_label"] = df.apply(build_link_label, axis=1)

        return df

    @property
    def _view_name(self):
        """When the Sankey object is displayed by IPython, render the plot"""
        return self.gui._view_name

    @property
    def _model_id(self):
        """When the Sankey object is displayed by IPython, render the plot"""
        return self.gui._model_id

    def update_layout(self, *args, **kwargs):
        """Pass layout changes to the plot."""
        # This is primarily kept for compatibility with geemap
        self.plot.update_layout(*args, **kwargs)

    def _generate_gui(self):
        BUTTON_HEIGHT = "24px"
        BUTTON_WIDTH = "24px"

        unique_classes = self._get_sorted_classes()

        def toggle_button(button):
            button.toggle()

            class_name = button.tooltip
            class_id = next(key for key in self.labels.keys() if self.labels[key] == class_name)

            if not button.state:
                self.hide.append(class_id)
            else:
                self.hide.remove(class_id)

            update_plot()

        def update_plot():
            """Swap new data into the plot."""
            new_sankey = self._generate_sankey()
            self.plot.data[0].link = new_sankey.link
            self.plot.data[0].node = new_sankey.node

        buttons = []
        active_classes = self._get_active_classes()
        for i in unique_classes:
            label = self.labels[i]
            on_color = self.palette[i]
            state = i in active_classes

            button = utils.ColorToggleButton(tooltip=label, on_color=on_color, state=state)
            button.layout.width = BUTTON_WIDTH
            button.layout.height = BUTTON_HEIGHT

            button.on_click(toggle_button)
            buttons.append(button)

        def reset_plot(_):
            for button in buttons:
                if not button.state:
                    button.click()

        reset_button = widgets.Button(
            icon="refresh",
            tooltip="Reset plot",
            layout=widgets.Layout(height=BUTTON_HEIGHT, width=BUTTON_WIDTH, padding="0 0 0 3px"),
        )
        reset_button.on_click(reset_plot)

        open_button = widgets.Button(
            icon="external-link",
            tooltip="Open in new tab",
            layout=widgets.Layout(height=BUTTON_HEIGHT, width=BUTTON_WIDTH, padding="0 0 0 3px"),
        )
        open_button.on_click(
            lambda _: self.plot.update_layout(width=None, height=None).show(renderer="browser")
        )

        button_box = widgets.HBox([*buttons, widgets.Label("|"), reset_button, open_button])

        gui = widgets.VBox(
            [
                self.plot,
                widgets.VBox([button_box], layout=widgets.Layout(align_items="center")),
            ]
        )

        return gui

    def _generate_sankey(self) -> go.Figure:
        """Generate the Sankey plot based on the currently visible classes."""
        self.df = self._generate_dataframe()
        # Explicitly return an empty Sankey plot if all classes are hidden to avoid widget update
        # errors.
        if len(self.df) == 0:
            return go.Sankey()

        params = self._generate_plot_parameters()

        node_kwargs = dict(
            customdata=params.node_labels,
            hovertemplate="<b>%{customdata}</b><extra></extra>",
            label=[f"<span style='{self.theme.label_style}'>{s}</span>" for s in params.label],
            color=params.node_palette,
        )
        link_kwargs = dict(
            source=params.source,
            target=params.target,
            value=params.value,
            color=params.link_palette,
            customdata=params.link_labels,
            hovertemplate="%{customdata} <extra></extra>",
        )

        return go.Sankey(
            arrangement="snap",
            node={**node_kwargs, **self.theme.node_kwargs},
            link={**link_kwargs, **self.theme.link_kwargs},
        )

    def _generate_figurewidget(self) -> go.FigureWidget:
        """Generate the FigureWidget that wraps the Sankey plot."""
        fig = go.FigureWidget(data=[self._generate_sankey()])

        fig.update_layout(
            title_text=f"<span style='{self.theme.title_style}'>{self.title}</span>"
            if self.title
            else None,
            font_size=16,
            title_x=0.5,
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

        return fig
