import numpy as np
from sankee.datasets import Dataset


def get_missing_keys(key_list, key_dict):
    """
    Find any keys that are present in a list that are not present in the keys of a dictionary. Helpful for testing if a 
    label or palette dictionary is fully defined.
    """
    missing = []
    for key in key_list:
        if key not in key_dict.keys():
            missing.append(key)
    return missing


def normalized_change(data, group_col, count_col):
    """
    Perform group-wise data normalization to a column of values. Output values will be the proportion of all values 
    in the group.
    """
    return data.groupby(group_col)[count_col].apply(lambda x: x / x.sum())


def check_plot_params(data, dataset):
    """
    Check for values that are present in data and are not present in labels or palette and raise an error if any are
    found.
    """
    missing_labels = []
    missing_palette = []

    for _, col in data.iteritems():
        missing_labels += get_missing_keys(col, dataset.labels)
        missing_palette += get_missing_keys(col, dataset.palette)

    if missing_labels:
        raise Exception(
            f"The following values are present in the data and undefined in the labels: {np.unique(missing_labels)}")
    if missing_palette:
        raise Exception(
            f"The following values are present in the data and undefined in the palette: {np.unique(missing_palette)}")


def test_params(dataset, image_list, label_list):
    """
    Run tests to ensure user parameters are usable.
    """
    if not dataset.band:
        raise ValueError("Provide dataset or band.")
    if not dataset.labels:
        raise ValueError("Provide dataset or labels.")
    if not dataset.palette:
        raise ValueError("Provide dataset or palette.")
    if len(label_list) != len(image_list):
        raise ValueError(
            "Length of label list must match length of image list.")
    return 0


def drop_classes(data, max_classes, metric="area"):
    """
    Remove small classes until a maximum number of classes is reached.

    :param pd.DataFrame data: A dataframe in which each row represents as single sample point and columns represent
    the class of that point at various times.
    :param int max_classes: The maximum number of unique classes to retain. If more classes are present, the smallest
    classes will be removed.
    :return pd.DataFrame: A dataframe with rows that belong to the largest classes.
    """
    class_counts = data.melt().groupby("value").size().reset_index(name="n")
    largest_classes = class_counts.sort_values(
        by="n", ascending=False).value[0:max_classes].tolist()

    dropped_data = data[data.isin(largest_classes)].dropna()

    return dropped_data


def build_dataset(dataset=None, band="", labels=None, palette=None):
    """
    Take either a dataset or some combination of band, labels, and palette and return a dataset. If a dataset is
    provided, it will be returned unchanged. 
    """
    labels = labels if labels else {}
    palette = palette if palette else {}

    # Replace any dataset parameters with provided parameters
    if dataset:
        if band:
            dataset.band = band
        if labels:
            dataset.labels = labels
        if palette:
            dataset.palette = palette
    else:
        dataset = Dataset(collection_name=None, band=band,
                          labels=labels, palette=palette)

    return dataset


def build_label_list(image_list, label_list=None):
    """
    Take an image list and an optional label list. If a label list is provided, elements will be cast to string. If not,
    a label list will be generated using sequential numbers to match the image list.
    """
    if not label_list:
        label_list = [i for i in range(len(image_list))]
    # Cast every element in label list to string since GEE can't handle that
    label_list = [str(x) for x in label_list]

    return label_list
