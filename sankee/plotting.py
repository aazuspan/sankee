import sys
from collections import namedtuple
from typing import Dict, List, Union

import ee
import ipywidgets as widgets
import pandas as pd
import plotly.graph_objects as go

from sankee import utils
from sankee.sampling import collect_sankey_data

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
    image_list: List[ee.Image],
    band: str,
    labels: Dict[int, str],
    palette: Dict[int, str],
    region: Union[None, ee.Geometry] = None,
    label_list: Union[None, List[str]] = None,
    max_classes: Union[None, int] = None,
    n: int = 500,
    title: Union[None, str] = None,
    scale: Union[None, int] = None,
    seed: int = 0,
) -> go.Figure:
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

    Returns
    -------
    plotly.graph_objs._figure.Figure
        An interactive Sankey plot.
    """
    # Older versions of geemap are incompatible with sankee v0.1.0 and pass the wrong positional
    # arguments.
    if isinstance(band, ee.Geometry) and "geemap" in sys.modules:
        raise ValueError(
            "Your versions of `geemap` and `sankee` are incompatible. Please update geemap to the "
            "latest version (pip install -U geemap)."
        ) from None

    if region is None:
        region = image_list[0].geometry()

    label_list = label_list if label_list is not None else list(range(len(image_list)))
    label_list = [str(label) for label in label_list]
    if len(label_list) != len(image_list):
        raise ValueError("The number of labels must match the number of images.")
    if len(set(label_list)) != len(label_list):
        raise ValueError("All labels in the `label_list` must be unique.")

    sample_data = collect_sankey_data(
        image_list=image_list,
        image_labels=label_list,
        region=region,
        band=band,
        n=n,
        scale=scale,
        seed=seed,
        include=list(labels.keys()),
    )

    return SankeyPlot(
        data=sample_data,
        labels=labels,
        palette=palette,
        title=title,
        max_classes=max_classes,
    )


class SankeyPlot(widgets.DOMWidget):
    def __init__(
        self,
        data: pd.DataFrame,
        labels: Dict[int, str],
        palette: Dict[int, str],
        title: str,
        max_classes: int = None,
    ):
        self.data = data
        self.labels = labels
        self.palette = palette
        self.title = title

        self.max_classes = max_classes
        self.hide = []

        self.dataframe = self.generate_dataframe(data)
        self.plot = self.generate_plot()
        self.gui = self.generate_gui()

    def get_active_classes(self) -> pd.Series:
        """Return all unique active, visibile class values after filtering."""
        df = self.generate_filtered_dataframe()

        return df[["source", "target"]].melt().value.unique()

    def get_all_classes(self) -> pd.Series:
        """Return all unique class values before any filtering."""
        return self.dataframe[["source", "target"]].melt().value.unique()

    def generate_filtered_dataframe(self) -> pd.DataFrame:
        """Apply filtering to the sample data, recalculating values like class percentages."""
        data = self.data.copy()

        if self.hide:
            hide_mask = pd.concat([(data == i).any(axis=1) for i in self.hide], axis=1).any(axis=1)
            data = data[~hide_mask]

        if self.max_classes is not None:
            class_counts = data.melt().value.value_counts()
            keep_classes = class_counts[: self.max_classes].index.tolist()
            data = data[data.isin(keep_classes).all(axis=1)]

        return self.generate_dataframe(data)

    def generate_plot_parameters(self, df: pd.DataFrame) -> SankeyParameters:
        """Generate Sankey plot parameters from a formatted, cleaned dataframe"""
        # Assign a unique, sequential ID to each year-class combo, regardless of source/target
        # assignment. The order of the IDs determines the plotting order (top to bottom).
        all_classes = pd.DataFrame(
            {
                "year": pd.concat([df.source_year, df.target_year]),
                "class": pd.concat([df.source, df.target]),
            }
        )

        def sort_func(classes: pd.Series) -> pd.Series:
            return classes.apply(lambda c: df[df.source.eq(c)].total.mean())

        # Sort the class-year combos by the total samples so that IDs will be assigned from largest
        # to smallest, which determines the sankey plot order
        all_classes = all_classes.sort_values(by=["class"], key=sort_func, ascending=False)

        all_classes["id"] = all_classes.groupby(["year", "class"], sort=False).ngroup()
        all_classes = all_classes.drop_duplicates().reset_index(drop=True)
        all_classes["label"] = all_classes["class"].apply(lambda k: self.labels[k]).tolist()
        all_classes["color"] = all_classes["class"].apply(lambda k: self.palette[k]).tolist()

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

    def generate_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convert raw sampling data to a formatted dataframe"""
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
        df["total"] = df.groupby(["source_year", "source"]).changed.transform(sum)
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
            return f"{row.proportion:.0%} of {row.source_label} {verb} {row.target_label}"

        # Describe the class changes
        df["link_label"] = df.apply(build_link_label, axis=1)

        return df

    @staticmethod
    def drop_small_classes(data: pd.DataFrame, keep_classes: int) -> pd.DataFrame:
        """Remove small classes until a maximum number of classes is reached."""
        class_order = (
            data.groupby("target")
            .sum()
            .sort_values(by="changed", ascending=False)
            .reset_index()
            .target
        )
        keep = class_order[:keep_classes]

        return data[data.target.isin(keep) & data.source.isin(keep)]

    @property
    def _view_name(self):
        """When the Sankey object is displayed by IPython, render the plot"""
        return self.gui._view_name

    @property
    def _model_id(self):
        """When the Sankey object is displayed by IPython, render the plot"""
        return self.gui._model_id

    def update_layout(self, *args, **kwargs):
        """Pass layout changes to the plot. This is primarily kept for compatibility with geemap."""
        self.plot.update_layout(*args, **kwargs)

    def generate_gui(self):
        BUTTON_HEIGHT = "24px"
        BUTTON_WIDTH = "24px"

        unique_classes = self.get_all_classes()
        max_classes = max(len(unique_classes), 2)

        classes_slider = widgets.IntSlider(
            value=0, description="Min size:", min=0, max=max_classes - 2, step=1, readout=False
        )

        def update_max_classes(change):
            self.max_classes = max_classes - change["new"]
            update_plot()

        classes_slider.observe(update_max_classes, names="value")

        def toggle_button(button):
            button.toggle()

            class_name = button.tooltip
            class_id = [key for key in self.labels.keys() if self.labels[key] == class_name][0]

            if not button.state:
                self.hide.append(class_id)
            # A button can be disabled without being hidden if the only connecting class is
            # hidden
            elif class_id in self.hide:
                self.hide.remove(class_id)

            update_plot()

        def update_plot():
            """Swap new data into the plot"""
            new_plot = self.generate_plot()
            self.plot.data[0].link = new_plot.data[0].link
            self.plot.data[0].node = new_plot.data[0].node

            # Turn off buttons if class isn't visible
            for button in buttons:
                button.disabled = button.state and not any(
                    [button.tooltip in label for label in self.plot.data[0].node.label]
                )

        buttons = []
        for i in unique_classes:
            label = self.labels[i]
            on_color = self.palette[i]
            state = i in self.get_active_classes()

            button = utils.ColorToggleButton(tooltip=label, on_color=on_color, state=state)
            button.layout.width = BUTTON_WIDTH
            button.layout.height = BUTTON_HEIGHT

            button.on_click(toggle_button)
            buttons.append(button)

        def reset_plot(change):
            classes_slider.value = 0

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
        open_button.on_click(lambda _: self.plot.show(renderer="browser"))

        button_box = widgets.HBox([*buttons, widgets.Label("|"), reset_button, open_button])

        gui = widgets.VBox(
            [
                self.plot,
                widgets.VBox(
                    [button_box, classes_slider], layout=widgets.Layout(align_items="center")
                ),
            ]
        )

        return gui

    def generate_plot(self) -> go.Figure:
        df = self.generate_filtered_dataframe()
        params = self.generate_plot_parameters(df)

        shadow_color = "#76777a"
        label_style = f"""
            color: #fff;
            font-weight: 600;
            letter-spacing: -1px;
            text-shadow:
                0 0 4px black,
                -1px 1px 0 {shadow_color},
                1px 1px 0 {shadow_color},
                1px -1px 0 {shadow_color},
                -1px -1px 0 {shadow_color};
        """

        title_style = """
            color: #fff;
            font-weight: 900;
            word-spacing: 10px;
            letter-spacing: 3px;
            text-shadow:
                0 0 1px black,
                0 0 2px black,
                0 0 4px black;
        """

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=30,
                        thickness=20,
                        line=dict(color="#000000", width=1),
                        customdata=params.node_labels,
                        hovertemplate="%{customdata}<extra></extra>",
                        label=[f"<span style='{label_style}'>{s}</span>" for s in params.label],
                        color=params.node_palette,
                    ),
                    link=dict(
                        source=params.source,
                        target=params.target,
                        line=dict(color="#909090", width=1),
                        value=params.value,
                        color=params.link_palette,
                        customdata=params.link_labels,
                        hovertemplate="%{customdata} <extra></extra>",
                    ),
                )
            ]
        )

        fig.update_layout(
            title_text=f"<span style='{title_style}'>{self.title}</span>" if self.title else None,
            font_size=16,
            title_x=0.5,
            paper_bgcolor="rgba(0, 0, 0, 0)",
        )

        return go.FigureWidget(fig)