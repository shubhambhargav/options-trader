from dataclasses import dataclass
from typing import Optional


@dataclass
class ConfigModel:
    kite_auth_token: str
    console_session: Optional[str]
    zerodha_x_csrf_token: Optional[str]
    sensibull_access_token: str
    tickertape_csrf_token: Optional[str]
    tickertape_jwt_token: Optional[str]
    telegram_bot_token: str
    telegram_chat_id: int
