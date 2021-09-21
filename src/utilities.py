import collections
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta, TH

import pandas as pd

TRADINGSYMBOL_META = re.compile('(?P<instrument>[A-Z]+)(?P<datetime>[A-Z0-9]{5})(?P<type>[A-Z0-9]+)')


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


def unflatten_dict(data: dict, sep: str = '__') -> dict:
    """Flatten incoming data item.

    Args:
        data (dict): data
        sep (str): (default: {'__'})

    Returns:
        (dict): Transformed data item
    """
    tranformed_data = dict()

    for key, value in data.items():
        parts = key.split(sep)
        d = tranformed_data

        for part in parts[:-1]:
            if part not in d:
                d[part] = dict()

            d = d[part]

        d[parts[-1]] = value

    return tranformed_data


def tradingsymbol_to_meta(tradingsymbol: str):
    metadata = TRADINGSYMBOL_META.match(tradingsymbol)

    if not metadata:
        raise ValueError('Could not retrieve metadata for %s' % tradingsymbol)

    metadata_dict = metadata.groupdict()

    if 'PE' in metadata_dict['type']:
        metadata_dict['option_price'] = float(metadata_dict['type'].replace('PE', ''))
        metadata_dict['type'] = 'OPT'

    return metadata_dict


def get_last_thursday_for_derivative(datetime_str: str):
    datetime_obj = datetime.strptime(datetime_str, '%d%b')
    today = datetime.today()
    current_year = today.year
    # Year is determined based on the derivative expiry
    # since Jan, Feb would be in the next year, year + 1 is used
    datetime_obj = datetime(
        year=current_year + 1 if datetime_obj.month in [1, 2] else current_year,
        month=datetime_obj.month,
        day=datetime_obj.day
    )

    for i in range(1, 6):
        t = datetime_obj + relativedelta(weekday=TH(i))

        if t.month != datetime_obj.month:
            # Since t is exceeded we need last one  which we can get by subtracting -2 since it is already a Thursday.
            t = t + relativedelta(weekday=TH(-2))

            break

    return t


def divide_chunks(input_list: list, chunk_size: int):
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]
