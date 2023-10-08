from dataclasses import dataclass
from typing import Optional

@dataclass
class GoogleSheetConfigModel:
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    universe_domain: str

@dataclass
class ConfigModel:
    kite_auth_token: Optional[str]
    console_session: Optional[str]
    zerodha_x_csrf_token: Optional[str]
    sensibull_access_token: Optional[str]
    tickertape_csrf_token: Optional[str]
    tickertape_jwt_token: Optional[str]
    telegram_bot_token: str
    telegram_chat_id: int
    questrade_refresh_token: Optional[str]
    questrade_account_id: Optional[int]
    google_sheet_config: Optional[GoogleSheetConfigModel]
    google_sheet_name: Optional[str]
    google_sheet_worksheet_id: Optional[int]
    # questrade_access_token: Optional[str]
