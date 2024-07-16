from aiogram.utils.i18n import gettext as _

from aiogram import Bot, flags, types
from clientbot.handlers.chatgpt.callback_data import AIAgreeCallbackData, AIBalanceCallbackData, ChatGPTCallbackData, \
    SpeechVoiceCallbackData
from aiogram.dispatcher.fsm.context import FSMContext
from clientbot.handlers.chatgpt.handlers.main import run_ai_vidio_summary
from clientbot.handlers.chatgpt.keyboards.inline_kbrds import get_kbrd_ai_balance, get_kbrd_cancel_to_ai_faq, \
    get_kbrd_faq, get_kbrd_help
from clientbot.handlers.chatgpt.keyboards.reply_kbrds import cancel_input_prompt
from clientbot.handlers.chatgpt.states import AIState
from clientbot.keyboards.reply_kb import refill_balance_methods
from clientbot.shortcuts import get_bot_by_token, get_user
from db import models
from clientbot.data.states import RefillAmount
from config import settings, scheduler
from utils.aaio.AAIO import AAIO
from loader import client_bot_router


@client_bot_router.callback_query(ChatGPTCallbackData.filter())
@flags.rate_limit(key="ChatGPTCallbackData")
async def social_network(query: types.CallbackQuery, state: FSMContext, callback_data: ChatGPTCallbackData):
    text = _("Введите текс")
    if callback_data.model == 'gpt4':
        text = _("Введите запрос для GPT4")
    elif callback_data.model == 'gpt3':
        text = _("Введите запрос для GPT3")
    elif callback_data.model == 'dalle':
        text = _("Введите описание для DALL-E")
    elif callback_data.model == 'assistant':
        text = _("Введите запрос для голосового ассистента")
    elif callback_data.model == 'text-to-speech':
        text = _("Введите текст для преобразования в аудио")
    elif callback_data.model == 'speech-to-text':
        text = _("Отправьте аудио для преобразования в текст")
    elif callback_data.model == 'youtube_transcription':
        text = _(
            "Если у вас есть интересное видео на YouTube, которое вы хотели бы исследовать более глубоко, предлагаем вам уникальную возможность. Поделитесь с нами ссылкой на ваше видео, и наш инновационный сервис транскрибации преобразует аудиовизуальный контент в письменный текст.\r\n\r\n" \
            "Просто вставьте URL вашего видео в поле ниже, и мы займемся магией расшифровки. Вскоре вы получите полный текстовый отчет о том, что было сказано, позволяя вам анализировать информацию, делать заметки или цитировать интересующие вас моменты.\r\n\r\n" \
            "Мы ценим ваше время и стремимся сделать доступ к информации максимально удобным. Пожалуйста, введите ссылку на видео, и дайте нам возможность облегчить ваше погружение в мир знаний и открытий.")
    elif callback_data.model == 'google_search':
        text = _("Введите запрос и я что-то сделаю")
    await query.message.delete()
    await query.message.answer(text=text, reply_markup=cancel_input_prompt())
    await state.update_data(model=callback_data.model, use_context=callback_data.use_context)
    await state.set_state(AIState.input_prompt)


@client_bot_router.callback_query(AIAgreeCallbackData.filter())
@flags.rate_limit(key="AIAgreeCallbackData")
async def social_network(query: types.CallbackQuery, state: FSMContext, callback_data: AIAgreeCallbackData):
    if callback_data.agree:
        bot = Bot.get_current()
        bot_db = await get_bot_by_token(bot.token)
        user_id = query.from_user.id
        user = await get_user(user_id)
        if user.current_ai_limit < callback_data.cost:
            await query.message.edit_text(
                _("У вас недостаточно ⭐️ для выполнения запроса!"),
                reply_markup=await get_kbrd_ai_balance(user_id, bot_db.percent)
            )
            return
        user.current_ai_limit -= callback_data.cost
        await user.save()
        scheduler.add_job(run_ai_vidio_summary, args=(
        bot.token, user_id, callback_data.video_id, callback_data.message_id, callback_data.cost),
                          id=f"ai-{user_id}-{callback_data.video_id}", replace_existing=False, max_instances=1),
    else:
        await query.message.edit_text(_("Отменено!"), )
        await state.clear()


@client_bot_router.callback_query(SpeechVoiceCallbackData.filter())
@flags.rate_limit(key="SpeechVoiceCallbackData")
async def social_network(query: types.CallbackQuery, state: FSMContext, callback_data: SpeechVoiceCallbackData):
    text = _("Введите текст для озвучки: ")
    await query.message.delete()
    await query.message.answer(text=text, reply_markup=cancel_input_prompt())
    await state.update_data(model="text-to-speech", voice=callback_data.voice)
    await state.set_state(AIState.input_prompt)


@client_bot_router.callback_query(AIBalanceCallbackData.filter())
@flags.rate_limit(key="AIBalanceCallbackData")
async def social_network(query: types.CallbackQuery, state: FSMContext, callback_data: AIBalanceCallbackData):
    if callback_data.action == 'balance-list':
        bot = Bot.get_current()
        bot_bd = await get_bot_by_token(bot.token)
        await query.message.edit_text(
            _("└ Количество 🌟:"),
            reply_markup=await get_kbrd_ai_balance(query.from_user.id, bot_bd.percent)
        )
    elif callback_data.action == 'balance':
        await state.update_data(amount=callback_data.rub)
        await state.update_data(gt=callback_data.gt)
        await state.update_data(type="gpt")
        await query.message.answer(_("Выберите платежную систему"), reply_markup=await refill_balance_methods(False))
        await state.set_state(RefillAmount.method)
    elif callback_data.action == 'cancel':
        await query.message.edit_text(
            _("Отменено!"),
        )


@client_bot_router.callback_query(text='ai-faq')
@flags.rate_limit(key="ai-faq")
async def social_network(query: types.CallbackQuery):
    await query.message.edit_text(_("❔ Часто задаваемые вопросы:"), reply_markup=get_kbrd_faq())


@client_bot_router.callback_query(text='ai-faq-about-bot')
@flags.rate_limit(key="ai-faq-about-bot")
async def social_network(query: types.CallbackQuery):
    await query.message.edit_text(
        _("🤖 Что умеет бот?\n\n_└ Бот умеет отвечать на любые вопросы (GPT-4 Turbo), генерировать изображения (DALL·E 3), озвучивать текст (TTS), превращать аудио в текст (Whisper) и многое другое._"),
        parse_mode="Markdown", reply_markup=get_kbrd_cancel_to_ai_faq())


@client_bot_router.callback_query(text='ai-faq-about-gt')
@flags.rate_limit(key="ai-faq-about-gt")
async def social_network(query: types.CallbackQuery):
    await query.message.edit_text(
        _("⚡️ Что такое ⭐️?\n\n_└ ⭐️ — это токен внутри бота, необходимый для взаимодействия с моделями искусственного интеллекта._"),
        parse_mode="Markdown", reply_markup=get_kbrd_cancel_to_ai_faq())


@client_bot_router.callback_query(text='ai-faq-why-donate')
@flags.rate_limit(key="ai-faq-why-donate")
async def social_network(query: types.CallbackQuery):
    await query.message.edit_text(
        _("💲 Почему это платно?\n\n_└ Бот использует платные API на платформе OpenAI, которые необходимы для его работы._"),
        parse_mode="Markdown", reply_markup=get_kbrd_cancel_to_ai_faq())


@client_bot_router.callback_query(text='ai-faq-how-refill-balance')
@flags.rate_limit(key="ai-faq-how-refill-balance")
async def social_network(query: types.CallbackQuery):
    text = _("💳 Как пополнить баланс?\n\n")
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    methods = aaio.get_payment_methods()
    for method in methods.list:
        text += f"▫️ {method.name}\n"
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=get_kbrd_cancel_to_ai_faq())


@client_bot_router.callback_query(text='ai-faq-back')
@flags.rate_limit(key="ai-faq-back")
async def social_network(query: types.CallbackQuery):
    await query.message.edit_text(_("❔ Часто задаваемые вопросы:"), parse_mode="Markdown",
                                  reply_markup=get_kbrd_cancel_to_ai_faq())


@client_bot_router.callback_query(text='ai-help')
async def music_menu(query: types.CallbackQuery):
    bot = Bot.get_current()
    bot_db = await get_bot_by_token(bot.token)
    owner: models.MainBotUser = await bot_db.owner
    user: models.User = await owner.user
    link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.uid}"
    await query.message.edit_text(_("ℹ️ Помощь:"), reply_markup=get_kbrd_help(link))
