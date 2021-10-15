import click
from PyInquirer import prompt

from src.logger import LOGGER
from src.strategies import BluechipOptionsSeller, Strangler

REPR_BLUECHIP_OPTIONS_SELLER = 'bluechip_options_seller'

# TODO: Build the following dynamically
STARTEGY_MAP = {
    'Bluechip Options Seller': BluechipOptionsSeller,
    'Indices Daily Strangler': Strangler
}


@click.command()
def main():
    LOGGER.info('Welcome to your personal trader!')

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
