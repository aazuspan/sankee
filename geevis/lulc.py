import ee
import pandas as pd
import numpy as np
from plotnine import *
import plotnine


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


# TODO: Handle or raise specific error if there are values in the index that aren't listed in the labels or palette
def plot_area(data, start_label, end_label, class_labels, class_palette, max_classes=5):
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
    """
    # Count the frequency of each class at the start and end
    freq = data.apply(pd.Series.value_counts).reset_index().melt(
        id_vars="index", var_name="label", value_name="n").fillna(0)

    # Assign cover labels based on index values
    freq["cover"] = [class_labels[i] for i in freq["index"]]

    # Select the biggest classes to keep
    keep_classes = freq.groupby("cover").n.sum().sort_values(ascending=False)[
        0:max_classes].reset_index().cover.tolist()
    # Remove small classes
    freq = freq[freq.cover.isin(keep_classes)]

    # Assign a numeric period for plotting start and end as a continuous scale
    freq["period"] = np.where(freq.label.eq("start"), 0, 1)

    # Use only the labels and colors that are present in the data
    plot_labels = [v for v in class_labels.values() if v in list(freq.cover)]
    plot_palette = [v for k, v in class_palette.items()
                    if k in list(freq["index"])]

    # Assign categorical labels for plotting
    freq.cover = pd.Categorical(freq.cover, categories=plot_labels)

    return(ggplot(freq)
           + aes(x='period', y='n', fill='cover')
           + geom_area()
           + plotnine.scales.scale_fill_manual(plot_palette)
           + theme_void()
           + theme(
        legend_title=element_blank(),
        axis_text_x=element_text()
    )
        + scale_x_continuous(breaks=(0, 1), labels=(start_label, end_label))
    )
