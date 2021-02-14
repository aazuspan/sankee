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


def normalize_groups(data, group_col, count_col="n"):
    """
    Perform group-wise data normalization to a column of values. Output values will be the proportion of all values 
    in the group.
    """
    data[count_col] = data.groupby(
        group_col)[count_col].apply(lambda x: x / x.sum())
    return data
