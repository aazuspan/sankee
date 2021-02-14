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
