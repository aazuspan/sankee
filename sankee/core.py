import sys
from typing import Any, Dict, List, Tuple, Union

import ee
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from sankee import utils
from sankee.sampling import collect_sankey_data


def sankify(
    image_list: List[ee.Image],
    band: str,
    labels: Dict[int, str],
    palette: Dict[int, str],
    region: Union[None, ee.Geometry] = None,
    label_list: Union[None, List[str]] = None,
    exclude: Union[None, List[int]] = None,
    max_classes: Union[None, int] = None,
    n: int = 500,
    title: Union[None, str] = None,
    scale: Union[None, int] = None,
    seed: int = 0,
    dataset: Any = None,
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
        The labels associated with each value of all images in image_list. Every value in the images
        must be included as a key in the labels dictionary.
    palette : dict
        The colors associated with each value of all images in image_list. Every value in the images
        must be included as a key in the palette dictionary.
    region : ee.Geometry, default None
        A region to generate samples within. The region must overlap all images. If none is
        provided, the geometry of the first image will be used. For this to work, images must be
        bounded.
    label_list : List[str], default None
        An ordered list of labels corresponding to the images. The list must be the same length as
        image_list. If none is provided, sequential numeric labels will be automatically assigned
        starting at 0. Labels are displayed on-hover on the Sankey nodes.
    exclude : list[int], default None
        An optional list of pixel values to exclude from the plot. Excluded values must be raw pixel
        values rather than class labels. This can be helpful if the region is dominated by one or
        more unchanging classes and the goal is to visualize changes in smaller classes.
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
    dataset : None
        Unused parameter that will be removed in a future release. If you have a Dataset object to
        sankify, use `Dataset.sankify` instead.

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

    if dataset is not None:
        raise ValueError(
            "`sankee.sankify` no longer supports a `dataset` parameter. Use "
            "`Dataset.sankify` instead."
        )

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
    )
    cleaned_data = _clean_data(sample_data, exclude, max_classes)

    check_data_is_compatible(labels, cleaned_data)

    return _generate_sankey_plot(cleaned_data, labels, palette, title)


def _clean_data(
    data: pd.DataFrame, exclude: List[int] = None, max_classes: Union[None, int] = None
) -> pd.DataFrame:
    """
    Perform some cleaning on data before plotting by excluding unwanted classes and limiting the
    number of classes.

    Parameters
    ----------
    data : pd.DataFrame
        A dataframe in which each row represents as single sample point and columns represent the
        class of that point in each image of an image list.
    exclude : List[int]
        A list of class values to remove from the dataframe.
    max_classes : int
        The maximum number of unique classes to include in the dataframe. If more classes are
        present, the smallest classes will be omitted from the plot. If max_classes is None, no
        classes will be dropped.

    Returns
    -------
    pd.DataFrame
        A cleaned dataframe.
    """
    data = data.dropna()

    if exclude:
        data = data[~data.isin(exclude).any(axis=1)]
    if max_classes:
        data = utils.drop_small_classes(data, max_classes)

    return data


def check_data_is_compatible(labels: Dict[int, str], data: pd.DataFrame) -> None:
    """Check for values that are present in data and are not present in labels and raise an error if
    any are found.
    """
    missing_keys = []

    for _, col in data.iteritems():
        missing_keys += utils.get_missing_keys(col, labels)

    if missing_keys:
        raise Exception(
            "The following values are present in the data and undefined in the labels and palette:"
            f" {np.unique(missing_keys)}"
        )


def _generate_sankey_plot(
    data: pd.DataFrame, labels: Dict[int, str], palette: Dict[int, str], title: str
) -> go.Figure:
    (
        node_labels,
        link_labels,
        node_palette,
        link_palette,
        label,
        source,
        target,
        value,
    ) = _format_for_sankey(data, labels, palette)
    return _plot(
        node_labels,
        link_labels,
        node_palette,
        link_palette,
        label,
        source,
        target,
        value,
        title=title,
    )


def _format_for_sankey(
    data: pd.DataFrame, labels: Dict[int, str], palette: Dict[int, str]
) -> Tuple:
    """
    Take a dataframe of data representing classified sample points and return all parameters needed
    to generate a Sankey plot. This is done by looping through columns in groups of two representing
    start and end conditions and reformating data to match the Plotly Sankey input parameters.

    Parameters
    ----------
    data : pd.DataFrame
        A dataframe in which each row represents as single sample point and columns represent the
        columns represent classes over an arbitrary number of time periods.
    labels : Dict[int, str]
        A dictionary mapping class values to their corresponding labels.
    palette : Dict[int, str]
        A dictionary mapping class values to their corresponding colors.

    Returns
    -------
    Tuple
        A tuple of the following parameters: node_labels, link_labels, node_palette, link_palette,
        label, source, target, values.
    """
    formatted_data = _group_and_format_data(data, labels)

    node_labels = _build_node_labels(formatted_data)
    link_labels = _build_link_labels(formatted_data)
    label = _build_labels(formatted_data)

    source = formatted_data.source.tolist()
    target = formatted_data.target.tolist()
    value = formatted_data.value.tolist()

    def get_color(label):
        return palette[[k for k, v in labels.items() if v == label][0]]

    node_palette = [get_color(lab) for lab in label]
    link_palette = [get_color(i) for i in [label[j] for j in source]]

    return (node_labels, link_labels, node_palette, link_palette, label, source, target, value)


def _group_and_format_data(data: pd.DataFrame, labels: List[str]) -> pd.DataFrame:
    """
    Take raw data, group it into groups of two, and generate a formatted dataframe.
    """
    current_index = 0

    dfs = []
    for group in _group_columns(data):
        sankified = _reformat_group(data, group, labels, start_index=current_index)
        # The start index of the next column group will be the end index of this column group. This
        # sets the index offset to achieve that.
        current_index = sankified.target.min()
        dfs.append(sankified)

    return pd.concat(dfs)


def _group_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Yield all groups of two adjacent columns from a dataframe.
    """
    for i in range(data.columns.size - 1):
        group_indexes = [i, i + 1]
        yield data.iloc[:, group_indexes]


def _reformat_group(
    raw_data: pd.DataFrame, group_data: pd.DataFrame, labels: List[str], start_index: int = 0
) -> pd.DataFrame:
    column_list = group_data.columns.tolist()

    # Transform the data to get counts of each combination of condition
    sankey_data = group_data.groupby(group_data.columns.tolist()).size().reset_index(name="value")

    # Calculate normalized change from start to end condition
    sankey_data["change"] = utils.normalized_change(sankey_data, column_list[0], "value")

    sankey_data = _assign_unique_indexes(raw_data, sankey_data, start_index)

    # Assign labels to each source and target
    sankey_data["source_label"] = sankey_data.iloc[:, 0].apply(lambda i: labels[i])
    sankey_data["target_label"] = sankey_data.iloc[:, 1].apply(lambda i: labels[i])

    # Store the labels of the time series periods
    sankey_data["source_period"] = column_list[0]
    sankey_data["target_period"] = column_list[1]

    return sankey_data[
        [
            "source",
            "target",
            "value",
            "change",
            "source_label",
            "target_label",
            "source_period",
            "target_period",
        ]
    ]


def _assign_unique_indexes(
    raw_data: pd.DataFrame, sankey_data: pd.DataFrame, start_index: int
) -> pd.DataFrame:
    column_list = sankey_data.columns.tolist()

    # Get lists of unique source and target classes
    unique_source = pd.unique(raw_data[column_list[0]].values.flatten()).tolist()
    unique_target = pd.unique(raw_data[column_list[1]].values.flatten()).tolist()

    # Generate a unique index for each source and target
    sankey_data["source"] = sankey_data.iloc[:, 0].apply(
        lambda x: unique_source.index(x) + start_index
    )
    # Offset the target IDs by the last source class to prevent overlap with source IDs
    sankey_data["target"] = sankey_data.iloc[:, 1].apply(
        lambda x: unique_target.index(x) + sankey_data.source.max() + 1
    )

    return sankey_data


def _build_node_labels(data: pd.DataFrame) -> List[str]:
    """
    Build a list of period labels for nodes, corresponding to the link indexes.
    """
    labels = pd.concat([data.source, data.target])
    periods = pd.concat([data.source_period, data.target_period])
    combined = pd.DataFrame({"label": labels, "period": periods})
    return combined.groupby("label").period.first().tolist()


def _build_link_labels(data: pd.DataFrame) -> List[str]:
    """
    Build strings describing the change in states for each row of the dataframe.
    """
    link_labels = []
    for _, row in data.iterrows():
        verb = "remained" if row.source_label == row.target_label else "became"
        link_label = f"{round(row.change * 100)}% of {row.source_label} {verb} {row.target_label}"
        link_labels.append(link_label)
    return link_labels


def _build_labels(data: pd.DataFrame) -> List[str]:
    max_id = data.target.max()
    # Build empty placeholder labels for each class
    label = [None for i in range(max_id + 1)]

    for _, row in data.iterrows():
        # Iteratively replace the placeholder labels with correct labels for each index
        label[row.source] = row.source_label
        label[row.target] = row.target_label

    return label


def _plot(
    node_labels, link_labels, node_palette, link_palette, label, source, target, value, title=None
) -> go.Figure:
    """
    Generate a Sankey plot of land cover change over an arbitrary number of time steps.
    """
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=30,
                    thickness=20,
                    line=dict(color="#000000", width=1),
                    customdata=node_labels,
                    hovertemplate="%{customdata}<extra></extra>",
                    label=label,
                    color=node_palette,
                ),
                link=dict(
                    source=source,
                    target=target,
                    line=dict(color="#909090", width=1),
                    value=value,
                    color=link_palette,
                    customdata=link_labels,
                    hovertemplate="%{customdata} <extra></extra>",
                ),
            )
        ]
    )

    fig.update_layout(
        title_text=f"<b>{title}</b>" if title else None,
        font_size=16,
        title_x=0.5,
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )

    return fig
