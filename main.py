"""
Точка входа в скрипт.

Этот модуль:
- Заполняет переменные окружения значениями по умолчанию.
- Настраивает периодический запуск задачи из ScheduleManager.
- Запускает главный цикл, который выполняет запланированные задачи.
"""

#  Copyright Feliks Zubarev (c) 2025.

import time

import schedule

import os

import logger.logger
from managers.environment_manager import EnvironmentManager
from managers.schedule_manager import ScheduleManager

if __name__ == "__main__":
    # Заполняем переменные окружения значениями по умолчанию, если они не заданы
    EnvironmentManager.fill_default_values()

    # Планируем выполнение задачи
    time_interval = os.getenv("CHECK_INTERVAL")
    schedule.every(int(time_interval)).minutes.do(ScheduleManager.job)

    # Запускаем бесконечный цикл для обработки запланированных задач
    while True:
        schedule.run_pending()
        # Проверяем, есть ли задачи, которые нужно выполнить в текущий момент
        time.sleep(1)
        # Ждём 1 секунду, чтобы не перегружать процессор
