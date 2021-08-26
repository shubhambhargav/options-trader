import requests

from ._variables import VARIABLES


def get_gtt():
    headers = {
        'Authorization': f"enctoken {VARIABLES.CONFIG['auth_token']}"
    }

    response = requests.get(
        'https://kite.zerodha.com/oms/gtt/triggers',
        headers=headers
    )

    if response.status_code != 200:
        raise ValueError('Failed to get existing GTT from Kite')

    return response.json()['data']

