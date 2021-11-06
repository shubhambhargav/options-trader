

def get_cookie_dict(domain_name: str):
    # The following is added within the scope of the function to ensure that it is only called
    # during the local run as the server run doesn't required cookie retrieval
    from . import browser_cookie3

    cookie_jar = browser_cookie3.chrome(domain_name=domain_name)
    cookie_dict = {}

    for cookie in cookie_jar:
        cookie_dict[cookie.name] = cookie.value

    return cookie_dict
