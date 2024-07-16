import os
import django
from aiogram.filters import CommandStart
from django.core.wsgi import get_wsgi_application
from fastapi import FastAPI, Body, status, Response, BackgroundTasks
from aiogram import Bot
from aiogram.types import Update, Message
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'constructor.settings')
django.setup()

# Import other necessary components after Django setup
from modul.bot.main_bot.main import init_bot_handlers
from modul.clientbot.handlers.main import init_client_bot_handlers
from modul.clientbot.handlers.leomatch.handlers.start import init_client_dv
from modul.clientbot.handlers.leomatch.shortcuts import get_client
# from modul.clientbot.handlers.music.handler.main import init_client
from modul.helpers.filters import setup_main_bot_filter
from modul.clientbot.shortcuts import get_bot_by_token
from modul.config import settings_conf, scheduler
from modul.loader import main_bot, main_bot_router, client_bot_router, dp, bot_session
from api.bot_api import app_router

# Initialize FastAPI application
app = FastAPI(docs_url='/')

# Setup Django WSGI application
application = get_wsgi_application()

app.include_router(app_router)


def setup_routers():
    # Сначала инициализируем обработчики
    init_bot_handlers()
    init_client_bot_handlers()
    init_client_dv()
    # init_client()

    # Затем настраиваем фильтры
    setup_main_bot_filter(main_bot_router, client_bot_router)

    # После этого подключаем роутеры к диспетчеру
    dp.include_router(main_bot_router)
    dp.include_router(client_bot_router)


@app.on_event("startup")
async def on_startup():
    setup_routers()
    webhook_url = settings_conf.WEBHOOK_URL.format(token=main_bot.token)
    webhook_info = await main_bot.get_webhook_info()

    if webhook_info.url != webhook_url:
        print(webhook_info)
        await main_bot.set_webhook(webhook_url, allowed_updates=settings_conf.USED_UPDATE_TYPES)

    # await main_bot.delete_webhook()
    # await dp.start_polling(main_bot)
    scheduler.start()
    scheduler.print_jobs()


WEB_SERVER_HOST = "127.0.0.1"


# @client_bot_router.message(CommandStart())
# async def on_start(message: Message):
#     await message.answer("все работает")


async def feed_update(token, update):
    async with Bot(token, bot_session).context(auto_close=False) as bot_:
        await dp.feed_raw_update(bot_, update)


@app.post(settings_conf.WEBHOOK_PATH)
async def telegram_update(token: str, background_tasks: BackgroundTasks,
                          update: dict = Body(...)) -> Response:
    print("here")
    if token == main_bot.token or await get_bot_by_token(token):
        background_tasks.add_task(feed_update, token, update)
        return Response(status_code=status.HTTP_202_ACCEPTED)
    return Response(status_code=status.HTTP_401_UNAUTHORIZED)


@app.on_event("shutdown")
async def on_shutdown():
    if hasattr(bot_session, 'close'):
        await bot_session.close()
    scheduler.remove_all_jobs()
    scheduler.shutdown()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
