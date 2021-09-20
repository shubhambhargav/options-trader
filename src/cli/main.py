import click
from PyInquirer import Token, Separator, prompt, style_from_dict

from src.logger import LOGGER

STYLE = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})


def ask_bluechip_option_selling_config():
    questions = [
        {
            'type': 'confirm',
            'name': 'is_order_enabled',
            'message': 'Enable automated ordering?',
            'default': True
        },
        {
            'type': 'confirm',
            'name': 'is_order_profit_booking_enabled',
            'message': 'Close profited (90%+ profit) option positions?',
            'default': False
        },
        {
            'type': 'checkbox',
            'name': 'stocks',
            'message': 'List of stocks to be processed!',
            'choices': [
                Separator('= Public Sector ='),
                { 'name': 'COALINDIA' },
                Separator('= Banking & Finance ='),
                { 'name': 'HDFC', 'checked': True },
                { 'name': 'ICICIBANK' },
                { 'name': 'IDFCFIRSTB' },
                { 'name': 'HDFCBANK', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'M&MFIN' },
                { 'name': 'KOTAKBANK'},
                { 'name': 'BANDHANBNK' },
                Separator('= Insurance ='),
                { 'name': 'HDFCLIFE', 'custom_filters': { 'minimum_dip': 3 } },
                Separator('= FMCG ='),
                { 'name': 'HEROMOTOCO' },
                { 'name': 'TITAN', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'PIDILITIND', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'ASIANPAINT', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'MRF', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'HINDUNILVR', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'MARUTI' },
                { 'name': 'NESTLEIND' },
                Separator('= Emerging Market ='),
                { 'name': 'HDFCAMC', 'custom_filters': { 'minimum_dip': 3 } },
                Separator('= Tech ='),
                { 'name': 'INFY', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'TCS', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'NAUKRI' },
                { 'name': 'COFORGE' },
                { 'name': 'MINDTREE' },
                { 'name': 'LTI' },
                { 'name': 'HCLTECH' },
                Separator('= Uncategorized ='),
                { 'name': 'DRREDDY' },
                { 'name': 'TATACHEM' },
                { 'name': 'RELIANCE', 'custom_filters': { 'minimum_dip': 3 } },
                { 'name': 'BHARTIARTL' },
                { 'name': 'PVR' },
                { 'name': 'ITC', 'custom_filters': { 'minimum_dip': 3 } },
            ]
        }
    ]

    return prompt(questions=questions, style=STYLE)


@click.command()
def main():
    LOGGER.info('Welcome to your personal trader!')

    config = ask_bluechip_option_selling_config()

    print(config)

