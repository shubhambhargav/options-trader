
from dacite.core import from_dict

from src.cli.main import main
from src.strategies.bluechip_options_selling.controllers import BluechipOptionsSeller
from src.strategies.bluechip_options_selling.models import (
    ConfigModel as BluechipOptionsSellingConfig,
    AutomationConfig as BluechipOptionsSellingAutomationConfig
)


def lambda_handler(event: dict, _):
    config = {
        'is_order_enabled': True,
        'is_order_profit_booking_enabled': True,
        'is_automated': True,
        'stocks': [
            { 'tickersymbol': stock } for stock in [
                'ASIANPAINT', 'BHARTIARTL', 'COALINDIA', 'DRREDDY', 'HDFC', 'HDFCAMC', 'HDFCBANK',
                'HEROMOTOCO', 'HINDUNILVR', 'ICICIBANK', 'INFY', 'ITC', 'KOTAKBANK', 'MARUTI', 'MRF',
                'NESTLEIND', 'PIDILITIND', 'PVR', 'RELIANCE', 'TATASTEEL', 'TCS', 'TITAN'
            ]
        ]
    }

    config = from_dict(data_class=BluechipOptionsSellingConfig, data=config)

    config.automation_config = BluechipOptionsSellingAutomationConfig()

    BluechipOptionsSeller(config=config).run()


if __name__ == '__main__':
    main()
