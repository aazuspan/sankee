import ee
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from geevis import utils


def sample_change(start_img, end_img, band, region, n=100, scale=None):
    """
    Randomly sample values of two images to quantify change over time.

    :param ee.Image start_img: An image representing starting conditions. The image should contain classified values
    representing dictinct classes such as land cover types.
    :param ee.Image end_img: An image representing ending conditions.
    :param str band: The name of the band of start_img and end_img that contains the class value.
    :param ee.Geometry region: The region to sample.
    :param int n: The number of sample points to extract. More points will take longer to run but generate more
    representative cover statistics.
    :param int scale: The scale to sample point statistics at. Generally, this should be the nominal scale of the
    start and end image.
    :return pd.DataFrame: A dataframe in which each row represents as single sample point with the starting class
    in the "start" column and the ending class in the "end" column.
    """
    # TODO: Deal with missing scale variable (or see how GEE deals with a null argument)
    start_img = start_img.set({"label": "start"})
    end_img = end_img.set({"label": "end"})
    images = ee.ImageCollection.fromImages([start_img, end_img])

    samples = ee.FeatureCollection.randomPoints(region, n)

    def extract_values(point):
        # Set the location to extract values at
        geom = point.geometry()

        def extract(img, feature):
            # Extract the cover value at the point
            cover = img.reduceRegion(ee.Reducer.first(), geom, scale).get(band)
            # Get the user-defined label that was stored in the image
            label = img.get('label')

            # Set a property where the name is the label and the value is the extracted cover
            return ee.Feature(feature).set(label, cover)

        return ee.Feature(images.iterate(extract, point))

    sample_data = samples.map(extract_values)

    data = pd.DataFrame.from_dict(
        [feat["properties"] for feat in ee.Feature(sample_data).getInfo()["features"]])

    return data[["start", "end"]]


def check_plot_params(data, labels, palette):
    """
    Check for values that are present in data and are not present in labels or palette and raise an error if any are
    found.
    """
    missing_labels = utils.get_missing_keys(data["index"], labels)
    missing_palette = utils.get_missing_keys(data["index"], palette)

    if missing_labels:
        raise Exception(
            f"The following values are present in the data and undefined in the labels: {missing_labels}")
    if missing_palette:
        raise Exception(
            f"The following values are present in the data and undefined in the palette: {missing_palette}")


# TODO: Add a parameter for normalizing areas for when classes above max_classes are removed.
def plot_area(data, start_label, end_label, class_labels, class_palette, max_classes=5, normalize=True):
    """
    Generate a stacked area plot showing how the sampled area of cover changed from a start condition to an end
    condition.

    :param pd.DataFrame data: A dataframe in which each row represents as single sample point with the starting class
    in the "start" column and the ending class in the "end" column.
    :param str start_label: A label to describe the starting conditions, such as "prefire" or "2012".
    :param str end_label: A label to describe the ending conditions, sucsh as "postfire" or "2015".
    :param dict class_labels: A dictionary where keys are the class index values and the values are corresponding
    labels. Every class index in the sample dataset must be included in class_labels.
    :param dict class_palette: A dictionary where keys are the class index values and the values are corresponding
    colors. Every class index in the sample dataset must be included in class_palette.
    :param int max_classes: The maximum number of unique classes to include in the plot. If more classes are present,
    the smallest classes will be omitted from the plot.
    :param bool normalize: If true, the total area in each group will be normalized to 1. If classes are removed due
    to fit max classes, this will rescale the remaining classes.
    """
    # Count the frequency of each class at the start and end
    freq = data.apply(pd.Series.value_counts).reset_index().melt(
        id_vars="index", var_name="label", value_name="n").fillna(0)

    # Check for missing values in labels or palette
    check_plot_params(freq, class_labels, class_palette)

    # Select the biggest classes to keep
    keep_classes = freq.groupby("index").n.sum().sort_values(ascending=False)[
        0:max_classes].reset_index()["index"].tolist()
    # Remove small classes
    freq = freq[freq["index"].isin(keep_classes)]

    if normalize:
        freq = utils.normalize_groups(freq, "label", "n")

    x = ["start", "end"]
    y = list(zip(*[freq[freq.label == label].n for label in x]))

    plot_labels = [class_labels[i] for i in freq["index"]]
    plot_palette = [class_palette[i] for i in freq["index"]]

    fig, ax = plt.subplots()
    ax.stackplot(x, y, labels=plot_labels, colors=plot_palette)

    # Hide plot frame
    for spine in ax.spines.keys():
        ax.spines[spine].set_visible(False)
    # Hide y-axis
    ax.yaxis.set_visible(False)
    # Set tick font size
    plt.setp(ax.get_xticklabels(), fontsize=18)

    # This suppresses a warning about using non-fixed ticks
    tick_loc = ax.get_xticks()
    ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(tick_loc))
    # Set the tick labels
    ax.xaxis.set_ticklabels(['Immediate', 'Delayed'])

    handles, labels = ax.get_legend_handles_labels()
    # Reverse legend order
    plt.legend(handles[::-1], labels[::-1],
               loc='center left', bbox_to_anchor=(1, 0.5),
               fontsize=16,
               frameon=False
               )
    return fig
