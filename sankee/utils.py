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


def normalize_groups(data, group_col, count_col):
    """
    Perform group-wise data normalization to a column of values. Output values will be the proportion of all values 
    in the group.
    """
    data[count_col] = data.groupby(
        group_col)[count_col].apply(lambda x: x / x.sum())
    return data


def normalized_change(data, group_col, count_col):
    """
    Perform group-wise data normalization to a column of values. Output values will be the proportion of all values 
    in the group.
    """
    return data.groupby(group_col)[count_col].apply(lambda x: x / x.sum())


def check_plot_params(data, labels, palette):
    """
    Check for values that are present in data and are not present in labels or palette and raise an error if any are
    found.
    """
    missing_labels = get_missing_keys(data["index"], labels)
    missing_palette = get_missing_keys(data["index"], palette)

    if missing_labels:
        raise Exception(
            f"The following values are present in the data and undefined in the labels: {missing_labels}")
    if missing_palette:
        raise Exception(
            f"The following values are present in the data and undefined in the palette: {missing_palette}")


def parse_dataset(dataset=None, band=None, labels=None, palette=None):
    """
    Take a dataset, labels, and palette and check that enough parameters are defined to generate a graph. Raise an error
    if too few parameters or too many parameters are defined. Otherwise, return a dataset.
    """
    if dataset is None and any([x is None for x in [labels, palette]]):
        raise ValueError(
            "Provide either a dataset or class labels and a class palette.")
    elif dataset is not None and any([x is not None for x in [labels, palette]]):
        raise ValueError(
            "Provide only a dataset or class labels and a class palette, not both.")
    elif not dataset:
        dataset = Dataset(band, labels, palette)

    return dataset


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


def ordered_unique(input_list):
    """
    Take a list of values that may contain duplicates and return a list with only the unique values in the order they 
    were provided.
    """
    return list(dict.fromkeys(input_list))
