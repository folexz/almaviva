#  Copyright Feliks Zubarev (c) 2025.

"""
Модуль для решения Turnstile-капчи.
Содержит класс CaptchaService, который:
- устанавливает JS-хук для перехвата параметров капчи
- проверяет наличие Turnstile на странице
- отправляет задачу на решение и ожидает ответ
- возвращает токен решения
"""

import json
import os
import time

import requests

from logger.logger import info


class CaptchaService:
    """Сервис для решения капч"""

    def __init__(self):
        # Параметры Turnstile пока не получены
        self.ts_params = None
        # Загружаем API-ключ для сервиса решения капчи из окружения
        self.api_key = os.getenv("CAPTCHA_API_KEY")
        # JS-хук для перехвата параметров Turnstile через console.log
        self.hook = r"""
        const i = setInterval(()=>{
          if (window.turnstile) {
            clearInterval(i);
            window.turnstile.render = (a,b) => {
              let p = {
                type: "TurnstileTaskProxyless",
                websiteKey: b.sitekey,
                websiteURL: window.location.href,
                data: b.cData,
                pagedata: b.chlPageData,
                action: b.action,
                userAgent: navigator.userAgent
              };
              console.log(JSON.stringify(p));
              window.tsCallback = b.callback;
              return 'foo';
            };
          }
        },10);
        """

    def inject_hook(self, tab):
        """Инъекция скрипта для получения параметров CAPTCHA."""
        # Добавляем скрипт-хук на каждый загружаемый документ
        tab.Page.addScriptToEvaluateOnNewDocument(source=self.hook)
        # Логируем установку скрипта-хука
        info("Инъекция хука для получения информации о капче добавлена")

        # Обработчик console API для получения данных из скрипта-хука
        def _console(**kwargs):
            msg = kwargs["args"][0]["value"]
            try:
                data = json.loads(msg)
                if data.get("type") == "TurnstileTaskProxyless":
                    self.ts_params = data
            except:
                pass

        tab.Runtime.consoleAPICalled = _console

    def is_turnstile_available(self):
        # Проверяем, доступна ли Turnstile-капча на странице
        info("Проверяем наличие капчи")
        # Запоминаем время начала ожидания
        start = time.time()
        # Ожидаем до 5 секунд появления параметров
        while self.ts_params is None and time.time() - start < 5:
            # Параметры пока не получены, продолжаем ждать
            info("Капча еще не получена")
            # Короткая пауза перед повторной проверкой
            time.sleep(0.5)
        # Проверяем, были ли получены параметры за отведённое время
        if not self.ts_params:
            # Параметры не получены — Turnstile не найден
            info("Капча на странице не обнаружена, переходим к следующему шагу")
            # Возвращаем False, что капчи нет
            return False
        # Параметры получены — Turnstile найден
        info("Капча обнаружена")
        return True

    def solve_turnstile(self, url):
        # Формируем payload для создания задачи Turnstile через API
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "TurnstileTaskProxyless",
                "websiteURL": url,
                "websiteKey": self.ts_params["websiteKey"],
                "action": self.ts_params.get("action"),
                "data": self.ts_params.get("data"),
                "pagedata": self.ts_params.get("pagedata")
            }
        }

        # Логируем отправку задачи на решение
        info("Отправляем капчу на решение")
        # Получаем ответ от 2captcha об успешности создания задачи
        res = requests.post("https://api.2captcha.com/createTask", json=payload).json()
        if res.get("errorId") != 0:
            # Ошибка при создании задачи: выводим описание ошибки
            raise Exception(
                f"Не удалось отправить капчу на решение - ошибка отправки: {res}"
            )

        # Извлекаем ID задачи из ответа
        task_id = res.get("taskId")

        # Логируем, что задача принята сервисом
        info("Капча отправлена на решение")

        # Ожидание решения капчи: до ~200 секунд (40 циклов по 5 секунд)
        token = None
        for _ in range(40):
            # Ждем 5 секунд перед проверкой статуса
            time.sleep(5)
            # Запрашиваем статус решения по ID задачи
            r = requests.post(
                "https://api.2captcha.com/getTaskResult",
                json={"clientKey": self.api_key, "taskId": task_id},
            ).json()
            # Решение ещё не готово, продолжаем ждать
            if r.get("status") == "ready":
                token = r["solution"]["token"]
                break
            info("Ожидаем решение капчи")
        # Если по завершению цикла токен всё ещё не получен
        if not token:
            # Ошибка: решение капчи не получено в отведённое время
            raise Exception("Не удалось решить капчу")

        # Капча решена, токен получен
        info("Решение капчи получено")
        return token
