from contextlib import suppress

from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from modul.clientbot.keyboards import reply_kb
from modul.loader import client_bot_router


# from  import client_bot_router


# @client_bot_router.callback_query(text="cancel", state="*")
# async def cancel(c: types.CallbackQuery, state: FSMContext):
#     with suppress(TelegramBadRequest):
#         await c.message.delete()
#     await state.clear()


@client_bot_router.message(Command("cancel"))
@client_bot_router.message(F.text == "Отмена")
async def cancel_state(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=("Отменено"),
        reply_markup=await reply_kb.main_menu(message.from_user.id)
    )
