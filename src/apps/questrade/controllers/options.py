from typing import List
import json

from dacite import from_dict
from questrade_api import Questrade

from src.logger import LOGGER

from ..models import OptionFilterModel, OptionQuoteModel, OptionModel
from ..client import QuestradeClient

Q = QuestradeClient().initialize()

OPTION_QUOTES_BATCHSIZE = 100


def split(list_a, chunk_size):
    chunked_list = []

    for i in range(0, len(list_a), chunk_size):
        chunked_list.append(list_a[i:i + chunk_size])

    return chunked_list


class OptionsController:
    @staticmethod
    def get_option_quotes(ids: List[int], option_filters: List[OptionFilterModel] = []) -> List[OptionQuoteModel]:
        if len(ids) > OPTION_QUOTES_BATCHSIZE:
            chunked_ids = split(ids, OPTION_QUOTES_BATCHSIZE)
        else:
            chunked_ids = [ids]

        option_quotes: List[OptionQuoteModel] = []

        for chunk in chunked_ids:
            market_quotes = Q.markets_options(
                optionIds=chunk,
                filters=[option_filter.to_json() for option_filter in option_filters]
            )

            for row in market_quotes['optionQuotes']:
                option_quotes.append(from_dict(data_class=OptionQuoteModel, data=row))

        return option_quotes

    @staticmethod
    def get_options(symbol_id: int) -> List[OptionModel]:
        option_chain = Q.symbol_options(id=symbol_id)

        options: List[OptionModel] = []

        for row in option_chain['optionChain']:
            options.append(from_dict(data_class=OptionModel, data=row))

        return options
