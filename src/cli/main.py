import click
from PyInquirer import prompt
from dacite.core import from_dict

from src.logger import LOGGER
from src.strategies import BluechipOptionsSeller, Strangler
from src.strategies.strangling.models import ConfigV2Model

REPR_BLUECHIP_OPTIONS_SELLER = 'bluechip_options_seller'

# TODO: Build the following dynamically
STARTEGY_MAP = {
    'Bluechip Options Seller': BluechipOptionsSeller,
    'Indices Daily Strangler': Strangler
}


@click.command()
@click.option('--strategy', default=None, help='Strategy to be executed')
@click.option('--tickersymbol', type=str, help='Stocks / Indices to trade')
@click.option('--strangle_gap', type=int, help='Points to be strangled with')
@click.option('--stoploss_pnl', type=int, help='PnL to stop at')
@click.option('--is_mock_run', type=bool, help='To run as a mock or not?')
def main(*args, **kwargs):
    LOGGER.info('Welcome to your personal trader!')

    strategy = kwargs.get('strategy')

    if not strategy:
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

    if strategy != 'Indices Daily Strangler':
        raise ValueError('Unexpected strategy found, only Indices Daily Strangler is supported!')

    strategy = STARTEGY_MAP[strategy]

    kwargs = dict((k, v) for k, v in kwargs.items() if v)

    config = from_dict(data_class=ConfigV2Model, data=kwargs)

    strategy(config=config).run()
