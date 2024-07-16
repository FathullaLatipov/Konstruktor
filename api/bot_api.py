import logging

from aiogram import Dispatcher, types, Bot
from fastapi import APIRouter, Request, HTTPException, Body, Response, status, BackgroundTasks

from modul.clientbot.shortcuts import get_bot_by_token
from modul.config import settings_conf
from modul.loader import main_bot, bot_session, dp

WEBHOOK_PATH_TEMPLATE = "/webhook/{token}"
WEBHOOK_URL_TEMPLATE = 'https://8bb4-212-115-114-108.ngrok-free.app/webhook/{token}'

app_router = APIRouter()

# Настройки Aiogram
bots = {'7397326527:AAHZTPHh5xanjTM9wSMcZYQZV9Tuo8A-0WQ': 'token'}


async def feed_update(token, update):
    async with Bot(token, bot_session).context(auto_close=False) as bot_:
        await dp.feed_raw_update(bot_, update)


# @app_router.post(WEBHOOK_PATH_TEMPLATE)
# async def telegram_update(token: str, background_tasks: BackgroundTasks,
#                           update: dict = Body(...)) -> Response:
#     print("here")
#     if token == main_bot.token or await get_bot_by_token(token):
#         background_tasks.add_task(feed_update, token, update)
#         return Response(status_code=status.HTTP_202_ACCEPTED)
#     return Response(status_code=status.HTTP_401_UNAUTHORIZED)


# Маршрут для обработки webhook запросов
# @app_router.post(WEBHOOK_PATH_TEMPLATE)
# async def handle_webhook(token: str, request: Request):
#     if token in bots:
#         try:
#             # Вывод заголовков и тела запроса для диагностики
#             logging.info(f"Received webhook with token: {token}")
#             logging.info(f"Headers: {request.headers}")
#
#             # Получение тела запроса
#             body = await request.body()
#             logging.info(f"Raw body: {body}")
#
#             # Проверка, что тело запроса не пустое
#             if not body:
#                 raise HTTPException(status_code=400, detail="Empty request body")
#
#             # Попытка разобрать тело запроса как JSON
#             try:
#                 body_json = await request.json()
#                 logging.info(f"Parsed JSON body: {body_json}")
#             except Exception as e:
#                 raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
#
#             # Обработка обновления
#             # update = types.Update.model_validate(body_json, context={"bot": bot})
#             dp = Dispatcher()
#
#             # # Имитация процесса обновления
#             # update = types.Update.model_validate(await request.json(), context={"bot": bot})
#             # await dp.feed_update(update)
#
#             return {"status": "ok"}
#
#         except Exception as e:
#             logging.error(f"Failed to process webhook: {e}")
#             raise HTTPException(status_code=500, detail=f"Webhook processing failed: {e}")
#
#     else:
#         logging.warning(f"Invalid token received: {token}")
#         raise HTTPException(status_code=403, detail="Invalid token")
#

# Маршрут для установки webhook
@app_router.get("/set_webhook/{token}")
async def set_webhook(token: str):
    try:
        # Создание бота с данным токеном
        bot = Bot(token=token)

        # Проверка токена через запрос к Telegram API
        await bot.get_me()  # Это вызовет ошибку, если токен недействителен

        if token not in bots:
            webhook_url = WEBHOOK_URL_TEMPLATE.format(token=token)
            logging.info(f"Setting webhook for bot with token {token}")
            logging.info(f"Webhook URL: {webhook_url}")

            await bot.set_webhook(webhook_url, allowed_updates=settings_conf.USED_UPDATE_TYPES)
            bots[token] = bot

            logging.info(f"Webhook successfully set for bot with token {token}")
            return {"status": "Webhook set", "url": webhook_url}
        else:
            logging.info(f"Webhook already set for bot with token {token}")
            return {"status": f"Webhook already set for bot with token {token}"}

    except Exception as e:
        logging.error(f"Failed to set webhook for bot with token {token}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set webhook: {e}")
