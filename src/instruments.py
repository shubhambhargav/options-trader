from dataclasses import asdict
from datetime import datetime, timedelta

from dacite.core import from_dict
from src.controllers import instruments

import pandas as pd

from ._variables import VARIABLES
from . import technical_indicators
from .models import StockOfInterest
from .controllers import InstrumentsController


def get_enriched_instruments_df(insturments_of_interest: list):
    enriched_instruments =  InstrumentsController.enrich_instruments(
        instruments=[from_dict(data_class=StockOfInterest, data=instrument) for instrument in insturments_of_interest]
    )

    return pd.DataFrame(enriched_instruments)
