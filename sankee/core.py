import ee
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from sankee import utils

# Temporary property name to store image labels in
LABEL_PROPERTY = "sankee_label"


def sankify(
    image_list,
    region,
    band,
    labels,
    palette,
    label_list=None,
    exclude=None,
    max_classes=None,
    n=100,
    title=None,
    scale=None,
    seed=0,
    dataset=None,
):
    """
    Perform sampling, data cleaning and reformatting, and generation of a Sankey plot of land cover change over a time
    series of images within a region.

    Parameters
    ----------
    image_list : List[ee.Image]
        An ordered list of images representing a time series of classified data. Each image will be sampled to generate 
        the Sankey plot. Any length of list is allowed, but lists with more than 3 or 4 images may produce unusable plots.
    region : ee.Geometry 
        A region to generate samples within.
    band : str
        The name of the band in all images of image_list that contains classified data.
    labels : dict
        The labels associated with each value of all images in image_list. Every value in the images must be included as a 
        key in the labels dictionary.
    palette : dict
        The colors associated with each value of all images in image_list. Every value in the images must be included as a 
        key in the palette dictionary.
    label_list : List[str], default None
        An ordered list of labels corresponding to the images. The list must be the same length as image_list. If none 
        is provided, sequential numeric labels will be automatically assigned starting at 0. Labels are displayed on-hover 
        on the Sankey nodes.
    exclude : list[int], default None
        An optional list of pixel values to exclude from the plot. Excluded values must be raw pixel values rather than class 
        labels. This can be helpful if the region is dominated by one or more unchanging classes and the goal is to visualize 
        changes in smaller classes.
    max_classes : int, default None 
        If a value is provided, small classes will be removed until max_classes remain. Class size is calculated based on total 
        times sampled in the time series.
    n : int, default 100
        The number of sample points to randomly generate for characterizing all images. More samples will provide more 
        representative data but will take longer to process.
    title : str, default None
        An optional title that will be displayed above the Sankey plot.
    scale : int, default None 
        The scale in image units to perform sampling at. If none is provided, GEE will attempt to use the image's nominal scale, 
        which may cause errors depending on the image projection.
    seed : int, default 0
        The seed value used to generate repeatable results during random sampling.
    dataset : None
        Unused parameter that will be removed in a future release. Included only to raise deprecation errors. If you have a 
        Dataset object to sankify, use `Dataset.sankify` instead.

    Returns
    -------
    plotly.graph_objs._figure.Figure
        An interactive Sankey plot.
    """
    if dataset is not None:
        raise ValueError("sankee.sankify no longer supports a `dataset` parameter. Instead use `Dataset.sankify`.")

    label_list = label_list if label_list is not None else list(range(len(image_list)))
    label_list = [str(l) for l in label_list]
    if len(label_list) != len(image_list):
        raise ValueError("The number of labels must match the number of images.")

    labeled_images = _label_images(image_list, label_list)
    sample_data = _collect_sample_data(labeled_images, region, band, label_list, n, scale, seed)
    cleaned_data = _clean_data(sample_data, exclude, max_classes)

    check_data_is_compatible(labels, cleaned_data)

    return _generate_sankey_plot(cleaned_data, labels, palette, title)


def _label_images(image_list, label_list):
    """
    Take a list of images and assign provided labels to each. Return the labeled images as an
    ImageCollection.
    """
    labeled = []
    for img, label in zip(image_list, label_list):
        labeled.append(img.set(LABEL_PROPERTY, label))
    
    return ee.ImageCollection(labeled)


def _collect_sample_data(image_list, region, band, label_list, n=100, scale=None, seed=0):
    """
    Randomly sample values of a list of images to quantify change over time.

    :param ee.ImageCollection image_list: A collection of labeled, classified ee.Images representing change over time.
    :param ee.Geometry region: The region to sample.
    :param str band: The name of the band of start_img and end_img that contains the class value.
    :param list label_list: A list of labels associated with each image in image_list. If not provided, numeric labels
    will be automatically generated starting at 0.
    :param int n: The number of sample points to extract. More points will take longer to run but generate more
    representative cover statistics.
    :param int scale: The scale to sample point statistics at. Generally, this should be the nominal scale of the
    start and end image.
    :param int seed: Random seed used to generate sample points.
    :return pd.DataFrame: A dataframe in which each row represents as single sample point and columns represent the
    class of that point in each image of the image list.
    """
    samples = ee.FeatureCollection.randomPoints(region, n, seed)

    sample_data = _extract_values_from_images_at_points(image_list, samples, band, scale)

    try:
        data = utils.feature_collection_to_dataframe(sample_data)
    except ee.EEException as e:
        # ee may raise an error if the band name isn't valid. This is a bit of a hack to catch that since ee doesn't
        # raise more specific errors.
        if band in e.args[0]:
            raise ValueError(
                f'"{band}" is not a valid band name. Check that the dataset band name exists for all images.'
            )
        else:
            raise e

    _check_for_missing_samples(data, label_list)

    return data[label_list]


def _check_for_missing_samples(data, label_list):
    """
    Check that the sampled data has a column for each label in the label list. If not, it may be that sampling occured
    outside of the image bounds.
    """
    missing_labels = [label for label in label_list if label not in data.columns]
    if missing_labels:
        raise Exception(f"No valid samples were collected in these images: {missing_labels}. Check that the sampling"\
        " region overlaps the image bounds.")


def _extract_values_from_images_at_points(image_list, sample_points, band, scale):
    """
    Take a collection of images and a collection of sample points and extract image values to each sample point. The image
    values will be stored in a property based on the image label.
    """

    def extract_values_from_images_at_one_point(point):
        point_location = ee.Element.geometry(point)

        def extract_value_from_image_at_one_point(img, feature):
            cover = ee.Image(img).reduceRegion(ee.Reducer.first(), point_location, scale).get(band)
            # Get the user-defined label that was stored in the image
            label = ee.Image(img).get(LABEL_PROPERTY)

            # Set a property where the name is the label and the value is the extracted cover
            return ee.Feature(feature).set(label, cover)

        return ee.Feature(image_list.iterate(extract_value_from_image_at_one_point, point))

    sample_data = sample_points.map(extract_values_from_images_at_one_point)

    return sample_data


def _clean_data(data, exclude=None, max_classes=None):
    """
    Perform some cleaning on data before plotting by excluding unwanted classes and limiting the number of classes.

    :param pd.DataFrame data: A dataframe in which each row represents as single sample point and columns represent the
    class of that point in each image of an image list.
    :param list exclude: A list of class values to remove from the dataframe.
    :param int max_classes: The maximum number of unique classes to include in the dataframe. If more classes are present,
    the smallest classes will be omitted from the plot. If max_classes is None, no classes will be dropped.
    :return pd.DataFrame: The input dataframe with cleaning applied.
    """
    data = data.dropna()
    
    if exclude:
        data = data[~data.isin(exclude).any(axis=1)]
    if max_classes:
        data = utils.drop_small_classes(data, max_classes)

    return data


def check_data_is_compatible(labels, data):
    """
    Check for values that are present in data and are not present in labels and raise an error if any are
    found.
    """
    missing_keys = []

    for _, col in data.iteritems():
        missing_keys += utils.get_missing_keys(col, labels)

    if missing_keys:
        raise Exception(
            f"The following values are present in the data and undefined in the labels and palette: {np.unique(missing_keys)}"
        )


def _generate_sankey_plot(data, labels, palette, title):
    node_labels, link_labels, node_palette, link_palette, label, source, target, value = _format_for_sankey(
        data, labels, palette
    )
    return _plot(node_labels, link_labels, node_palette, link_palette, label, source, target, value, title=title)


def _format_for_sankey(data, labels, palette):
    """
    Take a dataframe of data representing classified sample points and return all parameters needed to generate a
    Sankey plot. This is done by looping through columns in groups of two representing start and end conditions and
    reformating data to match the Plotly Sankey input parameters.

    :param pd.DataFrame data: A dataframe in which each row represents as single sample point and columns represent
    classes over an arbitrary number of time periods.
    :param dict labels: A dictionary where keys are the class index values and the values are corresponding
    labels. Every class index in the sample dataset must be included in labels.
    :param dict palette: A dictionary where keys are the class index values and the values are corresponding
    colors. Every class index in the sample dataset must be included in palette.
    :return tuple: A tuple of values used in Sankey plotting in the following order: node labels, link labels, node
    palette, link palette, labels, source, target, and values.
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

    node_palette = [get_color(l) for l in label]
    link_palette = [get_color(i) for i in [label[j] for j in source]]

    return (node_labels, link_labels, node_palette, link_palette, label, source, target, value)


def _group_and_format_data(data, labels):
    """
    Take raw data, group it into groups of two, and generate a formatted dataframe.
    """
    current_index = 0

    dfs = []
    for group in _group_columns(data):
        sankified = _reformat_group(data, group, labels, start_index=current_index)
        # The start index of the next column group will be the end index of this column group. This sets the index
        # offset to achieve that.
        current_index = sankified.target.min()
        dfs.append(sankified)

    return pd.concat(dfs)


def _group_columns(data):
    """
    Yield all groups of two adjacent columns from a dataframe.
    """
    for i in range(data.columns.size - 1):
        group_indexes = [i, i + 1]
        yield data.iloc[:, group_indexes]


def _reformat_group(raw_data, group_data, labels, start_index=0):
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
        ["source", "target", "value", "change", "source_label", "target_label", "source_period", "target_period"]
    ]


def _assign_unique_indexes(raw_data, sankey_data, start_index):
    column_list = sankey_data.columns.tolist()

    # Get lists of unique source and target classes
    unique_source = pd.unique(raw_data[column_list[0]].values.flatten()).tolist()
    unique_target = pd.unique(raw_data[column_list[1]].values.flatten()).tolist()

    # Generate a unique index for each source and target
    sankey_data["source"] = sankey_data.iloc[:, 0].apply(lambda x: unique_source.index(x) + start_index)
    # Offset the target IDs by the last source class to prevent overlap with source IDs
    sankey_data["target"] = sankey_data.iloc[:, 1].apply(
        lambda x: unique_target.index(x) + sankey_data.source.max() + 1
    )

    return sankey_data


def _build_node_labels(data):
    """
    Build a list of period labels for nodes, corresponding to the link indexes.
    """
    labels = pd.concat([data.source, data.target])
    periods = pd.concat([data.source_period, data.target_period])
    combined = pd.DataFrame({"label": labels, "period": periods})
    return combined.groupby("label").period.first().tolist()


def _build_link_labels(data):
    return [_build_link_label(row.source_label, row.target_label, row.change) for _, row in data.iterrows()]


def _build_link_label(start_class, end_class, change):
    """
    Build a string describing the change from one state to another in a row of data.
    """
    verb = "remained" if start_class == end_class else "became"
    link_label = f"{round(change * 100)}% of {start_class} {verb} {end_class}"

    return link_label


def _build_labels(data):
    max_id = data.target.max()
    # Build empty placeholder labels for each class
    label = [None for i in range(max_id + 1)]

    for _, row in data.iterrows():
        # Iteratively replace the placeholder labels with correct labels for each index
        label[row.source] = row.source_label
        label[row.target] = row.target_label

    return label


def _plot(node_labels, link_labels, node_palette, link_palette, label, source, target, value, title=None):
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
        title_text=f"<b>{title}</b>" if title else None, font_size=16, title_x=0.5, paper_bgcolor="rgba(0, 0, 0, 0)"
    )

    return fig
