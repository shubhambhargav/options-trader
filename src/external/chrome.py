from . import browser_cookie3


def get_cookie_dict():
    cookie_jar = browser_cookie3.chrome(domain_name='kite.zerodha.com')
    cookie_dict = {}

    for cookie in cookie_jar:
        cookie_dict[cookie.name] = cookie.value

    return cookie_dict
