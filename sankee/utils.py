import numpy as np
import pandas as pd


def feature_collection_to_dataframe(fc):
    """
    Extract and return FeatureCollection properties as a Pandas dataframe.
    """
    return pd.DataFrame.from_dict([feat["properties"] for feat in fc.toList(fc.size()).getInfo()])


def normalized_change(data, group_col, count_col):
    """
    Perform group-wise data normalization to a column of values. Output values will be the proportion of all values
    in the group.
    """
    return data.groupby(group_col)[count_col].apply(lambda x: x / x.sum())


def get_missing_keys(key_list, key_dict):
    """
    Find any keys that are present in a list that are not present in the keys of a dictionary. Helpful for testing if a
    label or palette dictionary is fully defined.
    """
    return [key for key in key_list if key not in key_dict.keys()]


def drop_small_classes(data, keep_classes):
    """
    Remove small classes until a maximum number of classes is reached.

    :param pd.DataFrame data: A dataframe in which each row represents as single sample point and columns represent
    the class of that point at various times.
    :param int keep_classes: The maximum number of unique classes to retain. If more classes are present, the smallest
    classes will be removed.
    :return pd.DataFrame: A dataframe with rows that belong to the largest classes.
    """
    class_counts = data.melt().groupby("value").size().reset_index(name="n")
    largest_classes = class_counts.sort_values(by="n", ascending=False).value[:keep_classes].tolist()
    dropped_data = data[data.isin(largest_classes).all(axis=1)]

    return dropped_data
