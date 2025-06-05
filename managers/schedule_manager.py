#  Copyright Feliks Zubarev (c) 2025.
"""
Модуль для периодического управления задачей проверки мест.
Содержит класс ScheduleManager с методом job, который:
- запускает ProcessManager и AlmavivaManager
- обрабатывает ошибки CDP и общие исключения
- останавливает процесс корректно
"""

import os
from datetime import datetime

from pychrome import CallMethodException

from logger.logger import error, info
from managers.almaviva_manager import AlmavivaManager
from managers.environment_manager import EnvironmentManager
from managers.process_manager import ProcessManager


# Менеджер расписания задач по проверке доступности мест
class ScheduleManager:
    # Основная задача, выполняемая по расписанию
    @staticmethod
    def job():
        info(f'Проверяем места в Almaviva г. {os.getenv("CITY_NAME")}')

        pm = None
        # Подготовка ProcessManager для запуска процессов
        try:
            # Создаем менеджера процессов
            pm = ProcessManager()
            # Запускаем необходимые процессы (браузер, прокси)
            pm.start()
            # Создаем менеджера Almaviva для проверки мест
            almaviva = AlmavivaManager()
            # Выполняем основной рабочий процесс проверки мест
            almaviva.run()
        # Игнорируем специфичные ошибки CDP при выполнении
        except CallMethodException as e:
            pass
        # Обрабатываем общие ошибки и логируем их
        except Exception as e:
            error(f"Выполнение скрипта завершено из-за ошибки: {e}")
        # Гарантированное завершение: остановка процесса и логирование
        finally:
            try:
                # Останавливаем процессы если менеджер был создан
                if pm:
                    pm.stop()
                # Логируем успешное выполнение скрипта
                info("Скрипт выполнен успешно")
            # Игнорируем ошибки CDP при остановке
            except CallMethodException as e:
                pass
            # Обрабатываем ошибки при остановке и логируем
            except Exception as e:
                error(f"Выполнение скрипта завершено из-за ошибки: {e}")
