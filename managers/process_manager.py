#  Copyright Feliks Zubarev (c) 2025.

"""
Модуль для управления процессами, необходимыми для работы скрипта.
Содержит класс ProcessManager, который:
- подключает и завершает сессию Chrome через CDP;
- задаёт необходимые паузы между этапами.
"""

import os
import time

from logger.logger import info
from managers.chrome_manager import ChromeManager


# Менеджер процессов: отвечает за запуск и остановку всех необходимых сервисов
class ProcessManager:
    """
    Оркестрирует старт и стоп процессов, необходимых для работы скрипта.
    """

    # Инициализация: создаём экземпляры менеджеров Squid и Chrome
    def __init__(self):
        # Initialize individual managers
        self.chrome = ChromeManager()

    def start(self):
        """
        Стартует необходимые для скрипта процессы.
        """
        try:
            # Стартуем браузер Chrome через CDP
            self.chrome.start()
            time.sleep(2)
            # Логируем успешный запуск всех процессов
            info("Все процессы запущены, 2 секунды таймаута для открытия всех окон")
        # Обрабатываем ошибки при запуске процессов
        except Exception as e:
            raise Exception(f"Ошибка при попытке запустить процессы - {e}")

    def stop(self):
        """
        Останавливает процессы, открытые ранее.
        """
        try:
            # Останавливаем браузер Chrome
            self.chrome.stop()
            # Логируем успешное завершение работы всех процессов
            info("Все процессы остановлены")
        # Обрабатываем ошибки при остановке процессов
        except Exception as e:
            raise Exception(f"Ошибка при попытке остановить все процессы - {e}")
