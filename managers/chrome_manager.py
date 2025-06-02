#  Copyright Feliks Zubarev (c) 2025.

"""
Модуль для управления процессом Chrome.
Содержит класс ChromeManager, который:
- запускает Chrome с remote-debugging портом и пользовательским профилем
- при необходимости добавляет прокси-конфигурацию через Squid;
- ожидает готовности DevTools Protocol
- корректно завершает процесс
"""

import os
import subprocess
import time
from subprocess import DEVNULL

import requests

from logger.logger import info

# Менеджер процесса Chrome: отвечает за запуск и остановку браузера Chrome
class ChromeManager:
    """
    Менеджер для управления процессом Chrome.
    """

    def __init__(self):
        # Инициализация: процесс Chrome пока не создан
        self.process = None
        self.city_id = os.getenv("CITY_ID")

    def start(self):
        """
        Запускает процесс Chrome.
        """
        # Определяем путь к профилю Chrome
        profile_dir = os.path.expanduser('~') + f'/almaviva-chrome-profiles/city-{self.city_id}'
        # Если директории профиля нет, создаём её пустой
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir, exist_ok=True)

        cmd = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--remote-debugging-port=9222",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-sync"
        ]
        # Запускаем процесс Chrome
        self.process = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)
        # Логируем запуск и начинаем ожидание DevTools Protocol
        info("Chrome запущен, ожидаем запуска локального отладчика")

        # Ожидаем готовности локального отладчика на порту 9222
        for i in range(15):
            try:
                # Проверяем доступность DevTools API
                requests.get("http://127.0.0.1:9222/json/version", timeout=1)
                info("Локальный отладчик Chrome готов к работе")
                break
            except Exception:
                # Задержка перед повторной попыткой подключения
                time.sleep(1)
        # Если не удалось подключиться после 15 попыток — завершаем процесс и выдаём ошибку
        else:
            self.stop()
            raise Exception("Не удалось подключиться к локальному отладчику Chrome")

    def stop(self):
        """
        Останавливает процесс Chrome.
        """
        # Проверяем, запущен ли процесс Chrome для корректного завершения
        if self.process:
            try:
                # Отправляем сигнал завершения процессу Chrome
                self.process.terminate()
                self.process.wait()
                self.process = None
                time.sleep(3)
                # Ждём 3 секунды для полного завершения процесса
                # Логируем успешное завершение работы Chrome
                info("Chrome остановлен")
            except Exception as e:
                # Обрабатываем ошибки при остановке процесса Chrome
                raise Exception(f"Ошибка при остановке процесса Chrome - {e}")
