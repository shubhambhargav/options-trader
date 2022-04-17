import os
import json
from dataclasses import asdict, is_dataclass

from typing import List

from dacite import from_dict

from src.apps.nse.models.options import HistoricalOptionModel
from src.apps.kite.models.instruments import CandleModel, EnrichedInstrumentModel, InstrumentModel
from settings import CACHE_TYPE

CACHE_FOLDER = './.trader-cache'
DISK_CACHE_TYPE = 'disk'

# Following is a patch due to the limitations of python getargspec with annotations
FUNCTION_MODAL_MAP = {
    'get_historical_data': List[HistoricalOptionModel],
    'get_instrument': InstrumentModel,
    'enrich_instruments': List[EnrichedInstrumentModel],
    'enrich_options': List[HistoricalOptionModel],
    'get_instrument_price_details': CandleModel
}


class Cache:
    def __init__(self, func):
        self._func = func.__func__

        func_name = self._func.__name__

        self._return_model = FUNCTION_MODAL_MAP[func_name]
        self._cache_loc = f'{CACHE_FOLDER}/{func_name}.txt'
        self._memory = {}

        if CACHE_TYPE != DISK_CACHE_TYPE:
            return

        if not os.path.exists(CACHE_FOLDER):
            os.makedirs(CACHE_FOLDER)

        self.load()

    def memory(self):
        return self._memory

    def load(self):
        if CACHE_TYPE != DISK_CACHE_TYPE:
            return

        if not os.path.exists(self._cache_loc):
            return

        with open(self._cache_loc, 'r') as fileop:
            self._memory = json.loads(fileop.read())

    def dump(self):
        if CACHE_TYPE != DISK_CACHE_TYPE:
            return

        with open(self._cache_loc, 'w+') as fileop:
            fileop.write(json.dumps(self._memory))

    def __call__(self, *args, **kwargs):
        # Cache will not be used for latest data fetching i.e. no on_date value in the function
        if not kwargs.get('on_date') and self._func.__name__ != 'get_historical_data':
            return self._func(*args, **kwargs)

        # Note that the memory optimization only supports kwargs as of now
        hash_key = ('|'.join([str(elem) for elem in kwargs.values()]))

        if hash_key in self._memory:
            ret_val = self._memory[hash_key]

            if is_dataclass(self._return_model):
                return from_dict(data_class=self._return_model, data=ret_val)

            # Assuming that the non dataclass response is a list with a dataclass as an element
            data_model = self._return_model.__args__[0]

            return [from_dict(data_class=data_model, data=elem) for elem in ret_val]

        ret_val = self._func(*args, **kwargs)

        if is_dataclass(self._return_model):
            self._memory = asdict(ret_val)
        else:
            # Assuming that the non dataclass response is a list with a dataclass as an element
            self._memory[hash_key] = [asdict(elem) for elem in ret_val]

        self.dump()

        return ret_val
