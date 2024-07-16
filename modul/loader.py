from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Router, Bot, Dispatcher

bot_session = AiohttpSession()
# from shazamio import Shazam

main_bot = Bot(token="996043954:AAGbwv9SCRyklY4-hMsy3yMkZsiDJbDJ6YU", session=bot_session)
dp = Dispatcher()

client_bot_router = Router()
main_bot_router = Router()

# shazam = Shazam()/
