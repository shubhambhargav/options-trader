import click
from PyInquirer import prompt
from dacite.core import from_dict

from src.logger import LOGGER
from src.strategies import BluechipOptionsSeller, Strangler, TaxHarvester
from src.strategies.strangling.models import ConfigV2Model
from src.strategies.bluechip_options_selling.models import (
    ConfigModel as BluechipOptionsSellingConfig,
    AutomationConfig as BluechipOptionsSellingAutomationConfig
)

REPR_BLUECHIP_OPTIONS_SELLER = 'Bluechip Options Seller'
REPR_INDICES_DAILY_STRANGLER = 'Indices Daily Strangler'
REPR_TAX_HARVESTER = 'Tax Harvester'

# TODO: Build the following dynamically
STARTEGY_MAP = {
    REPR_BLUECHIP_OPTIONS_SELLER: BluechipOptionsSeller,
    REPR_INDICES_DAILY_STRANGLER: Strangler,
    REPR_TAX_HARVESTER: TaxHarvester
}

# TODO: Make the following option addition dynamic

"""
Sample commands:
Indices Daily Strangler
----
python run.py --strategy 'Indices Daily Strangler' --tickersymbol NIFTY --strangle_gap 200 --stoploss_pnl -1000 --is_mock_run true --number_of_lots 1

Bluechip Options Seller
----
python run.py --strategy 'Bluechip Options Seller' --stocks COALINDIA
"""

@click.command()
@click.option('--strategy', default=None, help='Strategy to be executed')
# Following are Indices Daily Strangler options
@click.option('--tickersymbol', type=str, help='Stocks / Indices to trade')
@click.option('--strangle_gap', type=int, help='Points to be strangled with')
@click.option('--stoploss_pnl', type=int, help='PnL to stop at')
@click.option('--is_mock_run', type=bool, help='To run as a mock or not?')
@click.option('--number_of_lots', type=int, help='Number of lots to be traded')
# Following are Bluechip Options Seller options
@click.option('--is_order_enabled', type=bool, default=True, help='Ordering to be enabled')
@click.option('--is_order_profit_booking_enabled', type=bool, default=True, help='Profit booking to be enabled')
@click.option('--stocks', type=str, help='List of tickersymbols to be processed')
@click.option('--is_automated', type=bool, default=True, help='List of tickersymbols to be processed')
def main(*args, **kwargs):
    LOGGER.info('Welcome to your personal trader!')

    strategy_name = kwargs.get('strategy')

    if not strategy_name:
        questions = [
            {
                'type': 'list',
                'name': 'strategy',
                'message': 'Pick the strategy to execute',
                'choices': STARTEGY_MAP.keys(),
                'filter': lambda val: STARTEGY_MAP[val]
            }
        ]

        startegy = prompt(questions=questions)['strategy']

        startegy().run()

        return

    if strategy_name not in STARTEGY_MAP.keys():
        raise ValueError(
            'Unexpected strategy found, only %s are supported!' % ','.join(STARTEGY_MAP.keys())
        )

    if strategy_name == REPR_INDICES_DAILY_STRANGLER:
        strategy: Strangler = STARTEGY_MAP[strategy_name]

        kwargs = dict((k, v) for k, v in kwargs.items() if v)

        config = from_dict(data_class=ConfigV2Model, data=kwargs)

        strategy(config=config).run()
    elif strategy_name == REPR_BLUECHIP_OPTIONS_SELLER:
        strategy: BluechipOptionsSeller = STARTEGY_MAP[strategy_name]

        kwargs = dict((k, v) for k, v in kwargs.items() if v)
        kwargs['stocks'] = [
            { 'tickersymbol': stock } for stock in kwargs['stocks'].split(',')
        ]

        config = from_dict(data_class=BluechipOptionsSellingConfig, data=kwargs)

        config.automation_config = BluechipOptionsSellingAutomationConfig()

        strategy(config=config).run()
    elif strategy_name == REPR_TAX_HARVESTER:
        strategy: TaxHarvester = STARTEGY_MAP[strategy_name]

        strategy.harvest_tax()
    else:
        raise ValueError('Unexpected strategy found: %s!' % strategy_name)
