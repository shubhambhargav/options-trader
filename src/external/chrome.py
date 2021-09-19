from . import browser_cookie3


def get_cookie_dict(domain_name: str):
    cookie_jar = browser_cookie3.chrome(domain_name=domain_name)
    cookie_dict = {}

    for cookie in cookie_jar:
        cookie_dict[cookie.name] = cookie.value

    return cookie_dict
