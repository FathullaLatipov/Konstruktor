from django.urls import path
from .views import telegram_login, index, profile, create_bot, save_token, error_404, web_main, update_bot_settings, \
    toggle_bot, delete_bot, statistics_view

urlpatterns = [
    path('', index, name='index'),  # Главная страница
    path('main/', web_main, name='main'),
    path('profile/', profile, name='profile'),  # Страница профиля
    path('create-bot/', create_bot, name='create_bot'),  # Страница создания бота
    path('save_token/', save_token, name='save_token'),  # Сохранение токена
    path('error-404/', error_404, name='error_404'),  # Страница ошибки 404
    path('login/', telegram_login, name='telegram_login'),
    path('update_bot_settings/', update_bot_settings, name='update_bot_settings'),
    path('toggle_bot/', toggle_bot, name='toggle_bot'),
    path('delete_bot/', delete_bot, name='delete_bot'),
]
