#  Copyright Feliks Zubarev (c) 2025.

"""
Модуль управления значениями переменных окружения.
Содержит класс EnvironmentManager с методами:
- fill_default_values: интерактивно заполняет флаги окружения по умолчанию;
"""

import os
import json

from logger.logger import info, warning


class EnvironmentManager:
    @staticmethod
    def prompt_int_range(prompt_text, min_val, max_val):
        """
        Запрашивает у пользователя целое число в диапазоне [min_val, max_val].
        """
        while True:
            val = input(f"{prompt_text}").strip()
            try:
                num = int(val)
                if min_val <= num <= max_val:
                    return str(num)
            except ValueError:
                pass
            warning(f"Неверное значение. Введите целое число от {min_val} до {max_val}.")

    @staticmethod
    def prompt_nonempty(prompt_text):
        """
        Запрашивает у пользователя непустую строку.
        """
        while True:
            val = input(f"{prompt_text}").strip()
            if val:
                return val
            warning("Значение не может быть пустым. Попробуйте снова.")

    @staticmethod
    def prompt_city_selection():
        """
        Предлагает пользователю выбрать город из списка и возвращает (id, name).
        """
        cities = {
            7: "Екатеринбург",
            8: "Нижний Новгород",
            9: "Ростов-на-Дону",
            10: "Новосибирск",
            11: "Казань",
            12: "Самара",
            14: "Москва",
            16: "Краснодар"
        }
        while True:
            print("Доступные города для проверки:")
            for city_id, description in cities.items():
                print(f"  {city_id}: {description}")
            val = input("Введите идентификатор города (число): ").strip()
            try:
                num = int(val)
                if num in cities:
                    return str(num), cities[num]
            except ValueError:
                pass
            warning("Неверный идентификатор. Пожалуйста, введите число из списка.")

    @staticmethod
    def get_check_interval_value():
        """
        Запрашивает у пользователя значение CHECK_INTERVAL и возвращает его строкой.
        """
        return EnvironmentManager.prompt_int_range(
            "Введите частоту проверки в минутах (целое число от 1 до 1440): ", 1, 1440
        )

    @staticmethod
    def get_email_value():
        """
        Запрашивает у пользователя значение EMAIL и возвращает его.
        """
        return EnvironmentManager.prompt_nonempty("Введите вашу почту в Almaviva: ")

    @staticmethod
    def get_password_value():
        """
        Запрашивает у пользователя значение PASSWORD и возвращает его.
        """
        return EnvironmentManager.prompt_nonempty("Введите ваш пароль в Almaviva: ")

    @staticmethod
    def get_city_value():
        """
        Запрашивает у пользователя выбор города и возвращает (CITY_ID, CITY_NAME).
        """
        return EnvironmentManager.prompt_city_selection()

    @staticmethod
    def get_captcha_key_value():
        """
        Запрашивает у пользователя значение CAPTCHA_API_KEY и возвращает его.
        """
        return EnvironmentManager.prompt_nonempty("Введите ключ API в 2Captcha: ")

    @staticmethod
    def get_telegram_token_value():
        """
        Запрашивает у пользователя значение TELEGRAM_BOT_TOKEN и возвращает его.
        """
        return EnvironmentManager.prompt_nonempty("Введите токен Telegram бота: ")

    @staticmethod
    def get_telegram_chat_id_value():
        """
        Запрашивает у пользователя значение TELEGRAM_CHAT_ID и возвращает его.
        """
        return EnvironmentManager.prompt_nonempty("Введите идентификатор чата в Telegram: ")

    # Интерактивная установка значений переменных окружения по умолчанию
    @staticmethod
    def fill_default_values():
        print(
            """
            Скрипт умеет проверять наличие мест в Almaviva Россия, и отправлять информацию о наличии мест в Telegram.
            Вся информация по переменным окружения доступна в README проекта.
            """
        )

        config_path = os.path.join(os.path.dirname(__file__), "env_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            info("Найдены сохранённые значения:")
            for k, v in saved.items():
                info(f"  {k} = {v}")

            # Меню для работы с сохранёнными значениями
            while True:
                print("\nВыберите действие:")
                print("  1: Изменить отдельные значения")
                print("  2: Использовать сохранённые и начать работу")
                choice = input("Ваш выбор (1/2): ").strip()
                if choice == "2":
                    for k, v in saved.items():
                        os.environ.setdefault(k, v)
                    print("Используются предыдущие значения. Скрипт готов к запуску.")
                    return
                elif choice == "1":
                    # Меню для изменения отдельных переменных
                    while True:
                        print("\nЧто изменить:")
                        print("  1: Интервал проверки")
                        print("  2: Почта Almaviva")
                        print("  3: Пароль Almaviva")
                        print("  4: Город для проверки")
                        print("  5: Ключ 2Captcha")
                        print("  6: Токен Telegram бота")
                        print("  7: Идентификатор Telegram чата")
                        print("  8: Продолжить")
                        field_choice = input("Ваш выбор (1-8): ").strip()
                        if field_choice == "1":
                            saved["CHECK_INTERVAL"] = EnvironmentManager.get_check_interval_value()
                        elif field_choice == "2":
                            saved["EMAIL"] = EnvironmentManager.get_email_value()
                        elif field_choice == "3":
                            saved["PASSWORD"] = EnvironmentManager.get_password_value()
                        elif field_choice == "4":
                            new_id, new_name = EnvironmentManager.get_city_value()
                            saved["CITY_ID"] = new_id
                            saved["CITY_NAME"] = new_name
                        elif field_choice == "5":
                            saved["CAPTCHA_API_KEY"] = EnvironmentManager.get_captcha_key_value()
                        elif field_choice == "6":
                            saved["TELEGRAM_BOT_TOKEN"] = EnvironmentManager.get_telegram_token_value()
                        elif field_choice == "7":
                            saved["TELEGRAM_CHAT_ID"] = EnvironmentManager.get_telegram_chat_id_value()
                        elif field_choice == "8":
                            # Сохраняем обновлённые значения и выставляем в окружение
                            with open(config_path, "w", encoding="utf-8") as f:
                                json.dump(saved, f, ensure_ascii=False, indent=4)
                            for k, v in saved.items():
                                os.environ.setdefault(k, v)
                            info("Значения сохранены.")
                            return
                        else:
                            warning("Неверный выбор. Введите цифру от 1 до 8.")

        # Для первого запуска: собираем все значения в словарь
        new_values = {}

        new_values["CHECK_INTERVAL"] = EnvironmentManager.get_check_interval_value()
        new_values["EMAIL"] = EnvironmentManager.get_email_value()
        new_values["PASSWORD"] = EnvironmentManager.get_password_value()
        city_id, city_name = EnvironmentManager.get_city_value()
        new_values["CITY_ID"] = city_id
        new_values["CITY_NAME"] = city_name
        new_values["CAPTCHA_API_KEY"] = EnvironmentManager.get_captcha_key_value()
        new_values["TELEGRAM_BOT_TOKEN"] = EnvironmentManager.get_telegram_token_value()
        new_values["TELEGRAM_CHAT_ID"] = EnvironmentManager.get_telegram_chat_id_value()
        # Сохраняем все значения в окружение и в файл
        for k, v in new_values.items():
            os.environ.setdefault(k, v)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(new_values, f, ensure_ascii=False, indent=4)
        info("Значения сохранены")
