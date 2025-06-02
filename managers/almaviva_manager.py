#  Copyright Feliks Zubarev (c) 2025.
"""
Основной модуль управления процессом проверки визовых слотов.
Содержит класс AlmavivaManager, который:
- управляет запуском и завершением браузера;
- устанавливает хуки и слушатели для Cloudflare и капчи;
- выполняет логику входа, валидации OTP и проверки доступности слотов;
- отправляет уведомление и завершает сессию.
"""

from services.almaviva_service import AlmavivaService, BASE_URL
from services.captcha_service import CaptchaService
from services.chrome_service import ChromeService
from services.telegram_service import TelegramService


# Менеджер интеграции всех сервисов для проверки и уведомления
class AlmavivaManager:
    def __init__(self):
        # Инициализация: создаем экземпляры всех сервисов
        self.captcha_service = CaptchaService()
        self.almaviva_service = AlmavivaService()
        self.chrome_service = ChromeService()
        self.telegram_service = TelegramService()

    def run(self):
        try:
            # Подключаемся к браузеру Chrome через CDP
            self.chrome_service.connect()
            # Добавляем слушатель запросов для автоматического обновления заголовков
            self.almaviva_service.add_headers_listener(self.chrome_service.tab)
            # Внедряем JS-хук для перехвата параметров капчи и Cloudflare
            self.captcha_service.inject_hook(self.chrome_service.tab)
            # Открываем главную страницу визового центра
            self.chrome_service.open_main_page()

            # Проверяем, не заблокирован ли доступ от Cloudflare
            self.chrome_service.check_if_blocked()

            # Проверяем наличие Turnstile-капчи на странице
            if self.captcha_service.is_turnstile_available():
                # Решаем капчу с помощью сервиса 2captcha
                captcha_token = self.captcha_service.solve_turnstile(BASE_URL)
                # Внедряем полученный капча-токен в страницу
                self.chrome_service.inject_captcha_token(captcha_token)

            # Получаем текущий токен авторизации из куки браузера
            token = self.chrome_service.check_current_login()
            if token:
                # Сохраняем найденный валидный токен в сервисе Almaviva
                self.almaviva_service.token = token
            # Если токен не найден, выполняем полный вход в учетную запись
            else:
                # Выполняем запрос авторизации через API Almaviva
                login_data = self.almaviva_service.login(self.chrome_service.tab)
                # Инъекция полученных куки в браузер для сессии
                self.chrome_service.inject_cookies(login_data)

            # Проверяем доступность визовых слотов на сайте
            is_available = self.almaviva_service.check_availability(
                self.chrome_service.tab
            )
            # Отправляем уведомление о результате проверки
            self.telegram_service.send_telegram_message(is_available)
            # Завершаем сессию браузера и CDP
            self.chrome_service.finish()
        except Exception as e:
            # При ошибке завершаем сессию перед пробросом исключения
            self.chrome_service.finish()
            raise e
