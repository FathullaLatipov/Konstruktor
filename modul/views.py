import hashlib
import hmac
import json
import logging
import time

import requests
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.forms import ModelForm
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from .loader import bot_session
from .models import Bot, ClientBotUser, UserTG
from django.views.decorators.http import require_POST
from urllib.parse import urlencode
from .crud import crud_bot
from .config import settings_conf
from aiogram import Bot as Bot_aiogram


def index(request):
    return render(request, 'DxBot/index.html')


def web_main(request):
    current_date = timezone.now().date()
    first_day_of_current_month = current_date.replace(day=1)

    user_data = UserTG.objects.filter(created_at__lt=first_day_of_current_month).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    user_data_count = UserTG.objects.filter(interaction_count__gt=1).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Форматируем данные для JavaScript
    formatted_user_data = [
        {
            'month': item['month'].strftime('%Y-%m-%d'),
            'count': item['count']
        }
        for item in user_data
    ]
    formatted_user_data_count = [
        {
            'month': item['month'].strftime('%Y-%m-%d'),
            'count': item['count']
        }
        for item in user_data_count
    ]

    context = {
        'user_data': json.dumps(formatted_user_data),
        'user_data_count': json.dumps(formatted_user_data_count),
    }

    return render(request, 'admin-wrap-lite-master/html/index.html', context)


def profile(request):
    return render(request, 'admin-wrap-lite-master/html/pages-profile.html')


def create_bot(request):
    all_user_bot = crud_bot(request)
    context = {
        'all_user_bot': all_user_bot
    }
    return render(request, 'admin-wrap-lite-master/html/create_bot.html', context)


def error_404(request):
    return render(request, 'admin-wrap-lite-master/html/pages-error-404.html')


def get_bot_username(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['ok']:
            bot_username = data['result']['username']
            return bot_username
        else:
            print("Error:", data['description'])
    else:
        print("Failed to connect to Telegram API.")


logger = logging.getLogger(__name__)


class BotForm(ModelForm):
    class Meta:
        model = Bot
        fields = ['token']

    def clean_token(self):
        token = self.cleaned_data['token']
        try:
            Bot.objects.get(token=token)
            raise ValidationError('Токен уже существует.')
        except Bot.DoesNotExist:
            return token


from aiogram.types import BotCommand


@login_required
@csrf_exempt
@require_POST
def save_token(request):
    form = BotForm(request.POST)
    if form.is_valid():
        token = form.cleaned_data['token']
        try:
            bot_username = get_bot_username(token)
            url = settings_conf.WEBHOOK_URL.format(token=token)

            # Создаем объект Bot
            bot = Bot.objects.create(token=token, owner=request.user, username=bot_username)

            # Установка вебхука
            try:
                async def set_webhook_and_save():
                    bot_instance = Bot_aiogram(token, session=bot_session)
                    await bot_instance.set_webhook(url, allowed_updates=settings_conf.USED_UPDATE_TYPES)
                    await bot_instance.close()

                import asyncio
                asyncio.run(set_webhook_and_save())

                bot.save()
                logger.info(f"Bot token {token} saved successfully with webhook {url}.")

                # Вернуть JSON-ответ при успешном сохранении
                return redirect('create_bot')

            except Exception as e:
                bot.delete()  # Удаляем запись, если не удалось установить вебхук
                logger.error(f"Error setting webhook for bot {bot_username}: {e}")
                return JsonResponse({'status': 'error', 'message': f"Failed to set webhook: {str(e)}"})

        except ValidationError as e:
            logger.error(f"Invalid token {token}: {e}")
            return JsonResponse({'status': 'error', 'message': f"Invalid token: {str(e)}"})

    else:
        logger.error(f"Invalid form submission: {form.errors}")
        return JsonResponse({'status': 'error', 'message': 'Invalid form submission.', 'errors': form.errors})

    return HttpResponseBadRequest("Invalid request method. Use POST.")


User = get_user_model()


# def save_telegram_image(url):
#     response = requests.get(url)
#     if response.status_code == 200:
#         # Извлечем имя файла из URL
#         filename = url.split('/')[-1]
#         # Создадим имя файла с суффиксом времени для уникальности
#         unique_filename = f"{slugify(filename.split('.')[0])}_{int(time.time())}.{filename.split('.')[-1]}"
#
#         image = User()
#         image.profile_image.save(unique_filename, ContentFile(response.content), save=True)
#         image.save()
#
#         return image
#     else:
#         print("Failed to download image")
#         return None


def telegram_login(request):
    telegram_id = request.GET.get('id')
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    username = request.GET.get('username')
    # try:
    #     photo_url = request.GET.get('photo_url')
    #     telegram_image_url = photo_url
    # except:
    #     pass

    if not telegram_id:
        return redirect('login')  # Если нет ID, перенаправляем на обычную страницу логина

    user, created = User.objects.get_or_create(uid=telegram_id)

    if created:
        user.username = username or str(telegram_id)  # Генерация имени пользователя, если его нет
        user.first_name = first_name
        user.last_name = last_name
        user.save()
    # saved_image = save_telegram_image(telegram_image_url)

    login(request, user)  # Авторизация пользователя
    return redirect('profile')  # Перенаправление на главную страницу после логина


@login_required
@csrf_exempt
@require_POST
def update_bot_settings(request):
    bot_token = request.POST.get('bot_token')
    module = request.POST.get('module')

    bot = get_object_or_404(Bot, token=bot_token, owner=request.user)

    # Обновляем настройки бота в зависимости от выбранного модуля
    if module == 'leo':
        bot.enable_sms = False
        bot.enable_leo = True
        bot.enable_chatgpt = False
        bot.enable_horoscope = False
        bot.enable_anon = False
    # Добавьте другие условия для других модулей

    bot.save()

    return JsonResponse({'status': 'success', 'message': 'Настройки бота обновлены'})


@login_required
@csrf_exempt
@require_POST
def toggle_bot(request):
    bot_token = request.POST.get('bot_token')
    action = request.POST.get('action')  # 'on' или 'off'

    bot = get_object_or_404(Bot, token=bot_token, owner=request.user)

    if action == 'on':
        # Включаем бота (устанавливаем вебхук)
        url = settings_conf.WEBHOOK_URL.format(token=bot_token)
        try:
            async def set_webhook():
                bot_instance = Bot_aiogram(bot_token, session=bot_session)
                await bot_instance.set_webhook(url, allowed_updates=settings_conf.USED_UPDATE_TYPES)
                await bot_instance.close()

            import asyncio
            asyncio.run(set_webhook())

            bot.bot_enable = True
            bot.save()
            return JsonResponse({'status': 'success', 'message': 'Бот включен', 'new_status': 'on'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ошибка при включении бота: {str(e)}'})
    elif action == 'off':
        # Выключаем бота (удаляем вебхук)
        try:
            async def delete_webhook():
                bot_instance = Bot_aiogram(bot_token, session=bot_session)
                await bot_instance.delete_webhook()
                await bot_instance.close()

            import asyncio
            asyncio.run(delete_webhook())

            bot.bot_enable = False
            bot.save()
            return JsonResponse({'status': 'success', 'message': 'Бот выключен', 'new_status': 'off'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ошибка при выключении бота: {str(e)}'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Неверное действие. Попробуйте ещё раз'})


@login_required
@csrf_exempt
@require_POST
def delete_bot(request):
    bot_token = request.POST.get('bot_token')

    bot = get_object_or_404(Bot, token=bot_token, owner=request.user)

    try:
        # Удаляем вебхук перед удалением бота
        async def delete_webhook():
            bot_instance = Bot_aiogram(bot_token, session=bot_session)
            await bot_instance.delete_webhook()
            await bot_instance.close()

        import asyncio
        asyncio.run(delete_webhook())

        # Удаляем бота из базы данных
        bot.delete()

        return JsonResponse({'status': 'success', 'message': 'Бот успешно удален'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Ошибка при удалении бота: {str(e)}'})


def statistics_view(request):
    # Получаем данные о пользователях по месяцам
    user_data = UserTG.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(
        count=Count('id')).order_by('month')
    user_data_count = UserTG.objects.filter(interaction_count__gt=1).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    print(user_data)
    context = {
        'user_data': list(user_data),
        'user_data_count': list(user_data_count),
    }

    return render(request, 'admin-wrap-lite-master/html/index.html', context)
