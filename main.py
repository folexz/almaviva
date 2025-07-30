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

    print("\nВыберите режим работы:")
    print("  1: Проверка слотов")
    print("  2: Проверка статуса заявления")
    choice = input("Ваш выбор (1-2): ").strip()

    if choice == "1":
        time_interval = os.getenv("CHECK_INTERVAL")
        schedule.every(int(time_interval)).minutes.do(ScheduleManager.job, "availability")
        while True:
            schedule.run_pending()
            time.sleep(1)
    elif choice == "2":
        ScheduleManager.job("status")
    else:
        print("Неверный выбор")
