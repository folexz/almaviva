#  Copyright Feliks Zubarev (c) 2025.

"""
almaviva_service.py — модуль для работы с API визового сервиса Almaviva.
Содержит класс AlmavivaService, который:
- перехватывает и обновляет заголовки запросов
- строит JS-выражения для fetch-запросов через DevTools Protocol
- выполняет вход в учетную запись
- проверяет доступность слотов на сайте.
"""

import json
import os

from logger.logger import info

# API endpoints
BASE_URL = "https://ru.almaviva-visa.services"
LOGIN_URL = f"{BASE_URL}/api/login"
AVAILABILITY_URL = f"{BASE_URL}/api/getDisponibilityi?siteId="

# Маппинг статусов заявлений на человеко-читаемые сообщения
STATUS_MAPPING = {
    "IS_HUB_SP": "Ваши документы получены в центральном операционном офисе",
    "IS_CONS": "Ваши документы находятся на рассмотрении в Генеральном консульстве Италии в Москве",
    "TREATMENT": "Ваше визовое заявление обрабатывается в Визовом центре в г. ",
    "OS_SP_HUB": "Ваши документы находятся в пути в центральный операционный офис",
    "OS_HUB_CR": "Ваш паспорт передан в курьерскую службу",
    "IS_HUB": "Ваш паспорт готов к отправке в Визовый центр в г. ",
    "CANCELLED": "Ваша запись отменена.",
    "CREATED": "Ваша запись была создана в Визовом центре в г.",
    "OS_CONS_HUB": "Ваше визовое заявление рассмотрено, паспорт передан в центральный операционный офис",
    "IS_SP": "Ваш паспорт готов к получению в Визовом центре в г. ",
    "OS_HUB_SP": "Ваш паспорт находится в пути в Визовый центр в г. ",
    "OS_SP_CLI": "Ваш паспорт был получен в Визовом центре в г. ",
    "OS_HUB_CONS": "Ваши документы переданы в Генеральное консульство Италии в Москве",
}


class AlmavivaService:
    """Сервис для вызовов API Almaviva."""

    def _on_request(self, **kwargs):
        """Сохраняем заголовки первого запроса к визовому сервису."""
        req = kwargs.get("request", {})
        url = req.get("url", "")
        if url.startswith(BASE_URL):
            self.headers = req.get("headers", {})
            info("Обновлены хэдеры для запроса")

    def _build_fetch_expression(self, url, method="GET", return_type="text", body=None):
        """
        Строит JS-выражение для fetch-запроса через CDP.
        method: "GET" или "POST"
        return_type: "text" или "json"
        """
        headers_json = json.dumps(self.headers)
        # Добавляем Content-Type при наличии тела запроса
        content_line = (
            'h["Content-Type"] = "application/json";' if body is not None else ""
        )
        # Добавляем Authorization только если передан token
        auth_line = f'h["Authorization"] = "Bearer {self.token}";' if self.token else ""
        body_str = (
            f", body: JSON.stringify({json.dumps(body)})" if body is not None else ""
        )
        if return_type == "status":
            return f"""
                (async () => {{
                    const h = {headers_json};
                    {auth_line}
                    {content_line}
                    const r = await fetch("{url}", {{
                        method: "{method}",
                        headers: h,
                        credentials: "include"{body_str}
                    }});
                    return r.status;
                }})()
            """
        elif return_type == "json":
            return f"""
                (async () => {{
                    const h = {headers_json};
                    {auth_line}
                    {content_line}
                    const r = await fetch("{url}", {{
                        method: "{method}",
                        headers: h,
                        credentials: "include"{body_str}
                    }});
                    return r.status === 200 ? JSON.stringify(await r.json()) : {{"error": "json stringify failed"}};
                }})()
            """
        else:
            # return_type == "text"
            return f"""
                (async () => {{
                    const h = {headers_json};
                    {auth_line}
                    {content_line}
                    const r = await fetch("{url}", {{
                        method: "{method}",
                        headers: h,
                        credentials: "include"{body_str}
                    }});
                    return r.status === 200 ? await r.text() : "false";
                }})()
            """

    # Инициализация сервиса: HTTP-заголовки и токен еще не заданы
    def __init__(self):
        self.headers = {}
        self.token = None

        # Загружаем учетные данные для входа из переменных окружения
        self.mail = os.getenv("EMAIL")
        self.password = os.getenv("PASSWORD")
        self.city_id = os.getenv("CITY_ID")
        self.city_name = os.getenv("CITY_NAME")

    # Добавляем слушатель на события сети для обновления заголовков
    def add_headers_listener(self, tab):
        tab.Network.requestWillBeSent = self._on_request

    def login(self, tab):
        # Устанавливаем базовые заголовки для запроса входа
        self.headers["Referer"] = f"{BASE_URL}/signin"
        self.headers["Origin"] = BASE_URL
        # Строим JavaScript-выражение для выполнения POST-запроса авторизации
        expr = self._build_fetch_expression(
            LOGIN_URL,
            method="POST",
            return_type="json",
            body={
                "email": self.mail,
                "password": self.password,
                "lang": "en",
            },
        )
        info("Входим в учетную запись")
        resp = tab.Runtime.evaluate(expression=expr, awaitPromise=True)

        result_value = resp.get("result", {}).get("value")
        if result_value is None:
            raise Exception("Не удалось получить ответ при авторизации")

        if isinstance(result_value, str):
            try:
                json_data = json.loads(result_value)
            except json.JSONDecodeError as e:
                raise Exception(f"Некорректный JSON при авторизации: {e}")
        elif isinstance(result_value, dict):
            json_data = result_value
        else:
            raise Exception("Неизвестный формат ответа при авторизации")

        # Сохраняем токен в сервисе
        self.token = json_data.get("accessToken")
        if self.token:
            info("Вход в учетную запись прошел успешно")
            return json_data
        else:
            raise Exception("Не удалось войти в учетную запись")

    # Проверка доступности визовых слотов на сайте
    def check_availability(self, tab):
        # Устанавливаем заголовки для запроса слотов
        self.headers["Referer"] = f"{BASE_URL}/appointment"
        self.headers["Accept-Language"] = "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        # Строим JavaScript-выражение для проверки доступности слотов
        expr = self._build_fetch_expression(AVAILABILITY_URL + self.city_id)
        info(expr)
        info(f"Проверяем слоты по г. {self.city_name}")
        resp = tab.Runtime.evaluate(
            expression=expr,
            awaitPromise=True,
        )
        result = str(resp.get("result", {}).get("value", "")).lower().strip() == "true"
        if len(str(resp.get("result", {}).get("value", "")).lower().strip()) != 0:
            info(f'{f"Места в г. {self.city_name} есть" if result else f"Мест в г. {self.city_name} нет"}')
            return result
        else:
            raise Exception(f"При получении мест для г. {self.city_name} произошла ошибка")

    # Получение статуса визового заявления
    def get_application_status(self, tab):
        # Заголовки для запроса профиля
        self.headers["Referer"] = f"{BASE_URL}/profile/group"
        self.headers["Accept-Language"] = "ru"

        # Получаем id пользователя
        expr_profile = self._build_fetch_expression(
            f"{BASE_URL}/api/user/profile", return_type="json"
        )
        resp = tab.Runtime.evaluate(expression=expr_profile, awaitPromise=True)
        value = resp.get("result", {}).get("value")
        if value is None:
            raise Exception("Не удалось получить профиль пользователя")
        if isinstance(value, str):
            profile_data = json.loads(value)
        else:
            profile_data = value
        user_id = profile_data.get("id")
        if not user_id:
            raise Exception("В ответе профиля нет id пользователя")

        # Получаем список заявлений по id пользователя
        expr_group = self._build_fetch_expression(
            f"{BASE_URL}/api/group/client/{user_id}", return_type="json"
        )
        resp_group = tab.Runtime.evaluate(expression=expr_group, awaitPromise=True)
        value = resp_group.get("result", {}).get("value")
        if value is None:
            raise Exception("Не удалось получить список заявлений")
        if isinstance(value, str):
            groups = json.loads(value)
        else:
            groups = value
        if not groups:
            raise Exception("Ответ по заявлениям пуст")
        first = groups[0]
        site_name = first.get("site", {}).get("name", "")
        folders = first.get("folders", [])
        if not folders:
            raise Exception("Не найдены данные о статусе заявления")
        status_code = folders[0].get("status", "")
        return status_code, site_name
