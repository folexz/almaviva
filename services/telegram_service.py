#  Copyright Feliks Zubarev (c) 2025.
import datetime

from logger.logger import info, telegram

import os


class TelegramService:
    @staticmethod
    def send_telegram_message(is_available):
        # Формируем заголовок push-уведомления
        title = f'Almaviva в г. {os.getenv("CITY_NAME")}'

        # Если места доступны, готовим приоритетное уведомление
        if is_available:
            body_text = f"места ЕСТЬ"
        else:
            # Если мест нет, формируем соответствующее уведомление
            body_text = f"мест нет"

        # Отправляем текстовую нотификацию в Telegram
        try:
            info("Отправили сообщение в телеграм")
            telegram(f"{title} - {body_text}")
        except Exception as e:
            raise Exception(f"Не удалось отправить сообщение в телеграм - ошибка: {e}")

    @staticmethod
    def send_status_message(text):
        try:
            info("Отправили сообщение в телеграм")
            telegram(text)
        except Exception as e:
            raise Exception(f"Не удалось отправить сообщение в телеграм - ошибка: {e}")
