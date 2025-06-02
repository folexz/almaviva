#  Copyright Feliks Zubarev (c) 2025.
"""
Модуль логирования.
Содержит:
- Функцию log для вывода сообщений разных уровней с цветовой маркировкой
- Вспомогательные функции info, warning, error для каждого уровня
- Функцию telegram для отправки одиночного сообщения в Telegram
"""

import io
import os
import time
from datetime import datetime

import requests

# ANSI-код для сброса цвета вывода
RESET = "\033[0m"
# Словарь соответствия уровней логов ANSI-кодам цветов
COLORS = {
    "DEBUG": "\033[34m",  # Blue
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
}


# Основная функция логирования с учётом уровня, цвета и метки времени
def log(level, msg, *args, **kwargs):
    """Generic log with timestamp, level, and color."""
    # Формируем строку текущего времени
    ts = time.strftime("%H:%M:%S")
    color = COLORS.get(level, "")
    # Выводим сообщение в консоль с цветом
    print(f"{color}{ts} {level}: {msg}{RESET}", *args, **kwargs)


# Логирование уровня INFO
def info(msg, *args, **kwargs):
    """Info-level log."""
    log("INFO", msg, *args, **kwargs)


# Логирование уровня WARNING
def warning(msg, *args, **kwargs):
    """Warning-level log."""
    log("WARNING", msg, *args, **kwargs)


# Логирование уровня ERROR
def error(msg, *args, **kwargs):
    """Error-level log."""
    log("ERROR", msg, *args, **kwargs)


# Публичная функция для отправки одиночного сообщения через Telegram-бота
def telegram(msg: str, *args, **kwargs):
    """Public function to send a single message via the 'public' Telegram bot."""
    text = msg.format(*args, **kwargs) if (args or kwargs) else msg

    url = f"https://api.telegram.org/bot{os.getenv("TELEGRAM_BOT_TOKEN")}/sendMessage"
    payload = {"chat_id": os.getenv("TELEGRAM_CHAT_ID"), "text": text}

    try:
        requests.post(url, data=payload)
    except Exception as e:
        error(e)
        pass