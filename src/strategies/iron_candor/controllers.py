from PyInquirer import Token, prompt, style_from_dict
from dacite import from_dict

from src.strategies.iron_candor.models import ConfigModel
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


class BackTester:
    def __init__(self):
        pass

    def get_config(self) -> ConfigModel:
        questions = [
            {
                'type': 'checkbox',
                'name': 'tickers',
                'message': 'List of tickers to be processed!',
                'choices': [
                    { 'name': 'BANKNIFTY' }
                ]
            }
        ]

        config = prompt(questions=questions, style=STYLE)

        return from_dict(data_class=ConfigModel, data=config)

    def run(self):
        config = self.get_config()
