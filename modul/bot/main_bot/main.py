import asyncio

from aiogram import Router, Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from modul.config import settings_conf
from modul.loader import main_bot_router, client_bot_router

import requests

# Замените <bot_token> на ваш токен
bot_token = '996043954:AAGbwv9SCRyklY4-hMsy3yMkZsiDJbDJ6YU'
webhook_url = 'https://8bb4-212-115-114-108.ngrok-free.app/login/'



# set_webhook_url = f'https://api.telegram.org/bot{bot_token}/setWebhook'
# response = requests.post(set_webhook_url, data={'url': webhook_url})

def init_bot_handlers():


    @main_bot_router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext, ):
        print(message.from_user.id)
        user = message.from_user
        telegram_id = user.id
        first_name = user.first_name
        last_name = user.last_name or "Не указано"
        username = user.username or "Не указано"

        # Получение фотографии профиля пользователя
        user_photos = await message.bot.get_user_profile_photos(telegram_id)
        photo_link = None
        if user_photos.total_count > 0:
            photo_id = user_photos.photos[0][-1].file_id  # Получаем последнюю (самую большую) фотографию
            photo_url = await message.bot.get_file(photo_id)
            photo_link = f"https://api.telegram.org/file/bot{settings_conf.BOT_TOKEN}/{photo_url.file_path}"

        # Генерация ссылки для регистрации
        registration_url = (
            f"{settings_conf.WEBHOOK_URL}?"
            f"id={telegram_id}&first_name={first_name}&last_name={last_name}&username={username}"
        )
        if photo_link:
            registration_url += f"&photo_url={photo_link}"

        button = [[InlineKeyboardButton(text="Регистрация", url=registration_url)]]

        kb = InlineKeyboardMarkup(inline_keyboard=button)

        # Отправка приветственного сообщения
        await message.answer(f"Привет, {first_name}! Нажмите на эту кнопку для регистрации\n", reply_markup=kb)

# async def main_bot():
#     bot = Bot(token="996043954:AAGbwv9SCRyklY4-hMsy3yMkZsiDJbDJ6YU")
#     dp = Dispatcher()
#     dp.include_router(main_bot_router)
#     await bot.delete_webhook()
#     await dp.start_polling(bot)
#
#
# if __name__ == "__main__":
#     asyncio.run(main_bot())
