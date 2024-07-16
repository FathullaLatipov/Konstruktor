from aiogram.types import Message
from aiogram import html, Bot
from aiogram.fsm.context import FSMContext
from modul.clientbot.keyboards import reply_kb

async def return_main(msg: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await msg.answer(
        f"Добро пожаловать, {html.quote(msg.from_user.full_name)}",
        reply_markup=await reply_kb.main_menu(msg.from_user.id, bot)
    )       
    return 