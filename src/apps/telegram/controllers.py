import telegram

from src.apps.settings.controllers import ConfigController


class TelegramController:
    @staticmethod
    def send_message(message: str):
        config = ConfigController.get_config()

        bot = telegram.Bot(token=config.telegram_bot_token)

        telegram \
            .Chat(id=config.telegram_chat_id, type='group', bot=bot) \
            .send_message(text=message)
