import os
import json
from dataclasses import asdict

from typing import List

from dacite import from_dict

from src.apps.nse.models.options import HistoricalOptionModel

CACHE_FOLDER = './.trader-cache'

# Following is a patch due to the limitations of python getargspec with annotations
FUNCTION_MODAL_MAP = {
    'get_historical_data': List[HistoricalOptionModel]
}


class Cache:
    def __init__(self, func):
        self._func = func.__func__

        func_name = self._func.__name__

        self._return_model = FUNCTION_MODAL_MAP[func_name]
        self._cache_loc = f'{CACHE_FOLDER}/{func_name}.txt'
        self._memory = {}

        if not os.path.exists(CACHE_FOLDER):
            os.makedirs(CACHE_FOLDER)

        self.load()

    def memory(self):
        return self._memory

    def load(self):
        if not os.path.exists(self._cache_loc):
            return

        with open(self._cache_loc, 'r') as fileop:
            self._memory = json.loads(fileop.read())

    def dump(self):
        with open(self._cache_loc, 'w+') as fileop:
            fileop.write(json.dumps(self._memory, indent=4))

    def __call__(self, *args, **kwargs):
        # Note that the memory optimization only supports kwargs as of now
        hash_key = ('|'.join([str(elem) for elem in kwargs.values()]))

        if hash_key in self._memory:
            ret_val = self._memory[hash_key]

            if self._return_model.__origin__ is list:
                data_model = self._return_model.__args__[0]

                return [from_dict(data_class=data_model, data=elem) for elem in ret_val]

            return from_dict(data_class=self._return_model, data=ret_val)

        ret_val = self._func(*args, **kwargs)

        if self._return_model.__origin__ is list:
            self._memory[hash_key] = [asdict(elem) for elem in ret_val]
        else:
            self._memory = asdict(ret_val)

        self.dump()

        return ret_val
