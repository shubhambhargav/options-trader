import collections

import pandas as pd


def round_nearest(number: float, unit: float):
    return round(number / unit) * unit


def csv_text_to_dict(text_data: str):
    split_data = text_data.split('\n')
    
    headers = split_data[0].split(',')
    resp_data = []
    
    for data in split_data[1:]:
        if not data:
            continue
        
        resp_data.append(dict(zip(headers, data.split(','))))
        
    return resp_data


def flatten_dict(data: dict, parent_key: str = '', sep: str = '__') -> dict:
    """Flatten incoming data item.

    Args:
        data (dict): data
        parent_key (str): (default: {''})
        sep (str): (default: {'__'})

    Returns:
        (dict): Transformed data item
    """
    items = []

    for key, value in data.items():
        key = key.lower()
        new_key = parent_key + sep + key if parent_key else key

        if isinstance(value, collections.MutableMapping):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, str(value) if isinstance(value, list) else value))

    return dict(items)


def dict_array_to_df(dict_array: list):
    resp_data = []

    for dict_value in dict_array:
        resp_data.append(flatten_dict(data=dict_value))

    return resp_data
