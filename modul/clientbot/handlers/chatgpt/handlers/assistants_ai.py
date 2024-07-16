from aiogram import Bot, flags
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message
from clientbot.handlers.chatgpt.callback_data import AssistantAICallbackdata
from clientbot.handlers.chatgpt.keyboards.inline_kbrds import menu_btn, under_menu_btn
from clientbot.handlers.chatgpt.keyboards.reply_kbrds import back_btn, get_chatgt_main_kbrd
from clientbot.handlers.chatgpt.states import AssistantAIChatStates
from clientbot.shortcuts import get_user
from loader import client_bot_router
from config import settings
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from utils.cp import CalculatePrice
from utils.more_func import json_loader
from utils.assistants_ai import Assistants_AI

assistant = Assistants_AI(settings.AI_ASSISTANT_KEY)    
    
@client_bot_router.message(text='🤖 Ассистент')
@flags.rate_limit(key="on_start")
async def on_start(message: Message, state: FSMContext):
    await message.answer('Добро пожаловать у вас есть уникальная возможность попробовать AssistantAI', reply_markup=menu_btn())
    
@client_bot_router.callback_query(AssistantAICallbackdata.filter())
async def select_category(query: CallbackQuery, callback_data: AssistantAICallbackdata, state: FSMContext):
    if callback_data.action == 'select_category':
        category = json_loader("Category")[callback_data.data]
        await state.set_data({'category': category})
        await query.message.edit_text(text=f'Отлично теперь выберите себе что то из - {category}', reply_markup=under_menu_btn(callback_data.data))
    elif callback_data.action == 'select_under_category':
        if not callback_data.data:
            await query.message.edit_text('Добро пожаловать у вас есть уникальная возможность попробовать AssistantAI', reply_markup=menu_btn())
            return
        data = await state.get_data()
        category = data['category']
        name = json_loader()['UnderCategories'][category][callback_data.data]
        await query.message.edit_text(text=f"Задай свой вопрос - {name}")
        assistant.create_assistant(**json_loader()[name])
        assistant.add_thread()
        await state.set_state(AssistantAIChatStates.chat)
        
@client_bot_router.message(state=AssistantAIChatStates.chat)
async def chat_with_assistant(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Окончить сеанс':
        await message.answer(text='Спасибо за диалог хорошего дня !', reply_markup=get_chatgt_main_kbrd())
        await message.answer('Добро пожаловать у вас есть уникальная возможность попробовать AssistantAI', reply_markup=menu_btn())
        return
    if message.text:
        client = await get_user(message.from_user.id)
        if client.current_ai_limit < 1:
            await message.answer('У вас недостаточно средств для использования данной услуги', reply_markup=get_chatgt_main_kbrd())
            await state.clear()
            return
        try:
            if not assistant.can_run(message.text):
                await message.answer('Вы ввели запрещенные слова', reply_markup=get_chatgt_main_kbrd())
                await state.clear()
                return
        except Exception as e:
            await message.answer(e)
            await state.clear()
            return
        sticker = await message.answer(text='⏳')
        assistant.add_message(message=message.text)
        assistant.run_programmer()
        answer = assistant.check_status_run()
        if answer:
            bot_db = await client.bot
            cp = CalculatePrice(bot_db.percent)
            stars = cp.calc_price_ai(len(message.text), len(answer))
            client.current_ai_limit -= stars.COUNT_STARS
            await client.save()
            answer += f"\n\nСтоимость данного запроса составила {stars.COUNT_STARS} ⭐️\nОстаток: {client.current_ai_limit} ⭐️"
            await message.answer(answer, reply_markup=back_btn())
        else:
            await message.answer("Сервер не ответил", reply_markup=back_btn())
        await bot.delete_message(message.from_user.id, message_id=sticker.message_id)