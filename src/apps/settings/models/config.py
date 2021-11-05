from dataclasses import dataclass


@dataclass
class ConfigModel:
    kite_auth_token: str
    sensibull_access_token: str
    tickertape_csrf_token: str
    tickertape_jwt_token: str
    telegram_bot_token: str
    telegram_chat_id: int
