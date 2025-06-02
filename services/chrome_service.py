#  Copyright Feliks Zubarev (c) 2025.

"""
Модуль для управления браузером Chrome через DevTools Protocol (CDP).
Содержит класс ChromeService, который:
- подключается к отладчику Chrome
- открывает страницы и проверяет блокировки
- управляет куки и токенами авторизации
- завершает работу с вкладкой
"""

import base64
import json
import re
import time

import pychrome

from logger.logger import info
from services.almaviva_service import BASE_URL


class ChromeService:
    """Сервис для работы с Chrome через CDP."""

    # Инициализация сервиса: таб и заголовки еще не созданы
    def __init__(self):
        self.tab = None
        self.headers = {}

    def connect(self):
        """Подключение к локальному отладчику Chrome."""
        # Подключаемся к локальному дебаг-порту Chrome через CDP
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        # Создаем новую вкладку в браузере для управления
        self.tab = browser.new_tab()
        # Запускаем сессию CDP на этой вкладке
        self.tab.start()
        # Включаем домен Page для управления страницей
        self.tab.Page.enable()
        # Включаем домен Network для перехвата запросов
        self.tab.Network.enable()
        # Включаем домен Runtime для исполнения JS-кода
        self.tab.Runtime.enable()
        # Логируем готовность Chrome к работе
        info("Chrome готов к работе")

    def open_main_page(self):
        # Навигация на главный URL визового центра
        info("Открываем главную страницу визового центра")
        # Отправляем команду перехода на основной сайт
        self.tab.Page.navigate(url=BASE_URL)
        # Ждем загрузки страницы после навигации
        time.sleep(3)

    def check_if_blocked(self):
        # Начинаем проверку наличия блокировки Cloudflare
        info("Проверка на блокировку от Cloudflare")
        # Выполняем JS в контексте страницы, проверяя текст на предмет блокировки
        block_resp = self.tab.Runtime.evaluate(
            expression='document.body.innerText.includes("Sorry, you have been blocked")'
        )
        # Если текст содержит сообщение о блокировке, выбрасываем исключение
        if block_resp.get("result", {}).get("value", False):
            raise Exception("Произошла блокировка от CloudFlare")
        # Логируем, что блокировка не найдена
        else:
            info("Блокировка не обнаружена")

    def check_current_login(self):
        """Проверка и возврат существующего токена из куки."""
        # Проверяем наличие и актуальность токена авторизации в куки
        info("Проверка текущего логина")
        # Получаем строку cookie из браузера
        cookie_resp = self.tab.Runtime.evaluate(expression="document.cookie")
        cookies = cookie_resp.get("result", {}).get("value", "")
        # Ищем в cookie auth-token
        m = re.search(r"auth-token=([^;]+)", cookies)
        auth_token = None
        if m:
            auth_token = m.group(1)
            info("Найден текущий логин, проверка актуальности")
        # Если токен найден, проверяем его срок действия
        if auth_token:
            try:
                # Декодируем payload JWT и извлекаем поле exp
                payload_b64 = auth_token.split(".")[1] + "=" * (
                    -len(auth_token.split(".")[1]) % 4
                )
                payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
                exp = payload.get("exp", 0)
                # Логируем, что токен все еще действителен
                if exp > int(time.time()):
                    info("Текущий логин еще актуален")
                    # Возвращаем валидный токен
                    return auth_token
            # При ошибке проверки срока действия перезапускаем процедуру входа
            except Exception:
                info(
                    "Не удалось проверить срок действия токена, выполняем повторный вход"
                )
                return None
        return None

    def inject_cookies(self, login_data):
        """Инъекция ответа в куки."""
        # Начинаем инъекцию токена и данных пользователя в куки
        info("Сохраняем ответ по пользователю в куки")
        # Извлекаем accessToken из ответа логина
        token = login_data.get("accessToken")

        # Если токена нет, выбрасываем исключение
        if not token:
            raise Exception("Токен при сохранении пользователя в куки не найден")

        # Декодируем payload токена для получения exp
        payload_b64 = token.split(".")[1] + "=" * (-len(token.split(".")[1]) % 4)
        exp = json.loads(base64.urlsafe_b64decode(payload_b64)).get("exp", 0)
        # Вычисляем время жизни токена в секундах
        ttl = max(exp - int(time.time()), 0)
        # Устанавливаем cookie auth-token в браузере
        self.tab.Runtime.evaluate(
            expression=f'document.cookie="auth-token={token}; Path=/; Max-Age={ttl}";'
        )
        # Устанавливаем cookie с данными пользователя
        user_json = json.dumps(login_data)
        self.tab.Runtime.evaluate(
            expression=f'document.cookie="auth-user="+encodeURIComponent({user_json})+"; Path=/; Max-Age={ttl}";'
        )
        # Логируем, что пользователь сохранен в куки
        info("Пользователь сохранен в куках")

    def inject_captcha_token(self, captcha_token):
        # Отправляем токен капчи в окно страницы
        self.tab.Runtime.evaluate(expression=f'window.tsCallback("{captcha_token}");')
        # Логируем ожидание загрузки после ввода капчи
        info("Ждем загрузки страницы после инъекции капчи")
        # Пауза для завершения загрузки страницы
        time.sleep(3)

    def finish(self):
        # Начало процесса завершения работы с вкладкой
        info("Завершаем работу с вкладкой")
        # Отключаем домен Page перед остановкой
        try:
            self.tab.Page.disable()
        except Exception:
            pass
        # Отключаем домен Network перед остановкой
        try:
            self.tab.Network.disable()
        except Exception:
            pass
        # Отключаем домен Runtime перед остановкой
        try:
            self.tab.Runtime.disable()
        except Exception:
            pass
        # Останавливаем сессии CDP и WebSocket
        self.tab.stop()
        # Логируем завершение работы с вкладкой
        info("Работа с вкладкой завершена, завершаем выполнение скрипта")
