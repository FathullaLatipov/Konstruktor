import math
import os
from pathlib import Path
import re
from aiogram import Bot, flags
from aiogram.types import Message, URLInputFile, FSInputFile
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from clientbot.handlers.chatgpt.shortcuts import add_record
from clientbot.handlers.chatgpt.states import AIState
from clientbot.keyboards.reply_kb import main_menu
from clientbot.shortcuts import get_bot_by_token, get_user, have_one_module
from db import models
from clientbot.handlers.chatgpt.keyboards.reply_kbrds import get_chatgt_main_kbrd
from loader import client_bot_router, robot
from clientbot.handlers.chatgpt.keyboards.inline_kbrds import get_kbrd_agree, get_kbrd_ai_balance, get_kbrd_ai_cabinet, \
    get_kbrd_chat_type, get_kbrd_help, get_kbrd_speech_voices
from clientbot.utils.ChatGPT import MODEL_TYPE, PRICING, ChatGPT
from config import scheduler
from loader import bot_session


async def get_cabinet_text(fisrt_name: str, last_name: str, user_id: int):
    me = await get_user(user_id)
    return _("👤 Профиль: {fisrt_name} {last_name}\n\n⚡️ Баланс: {limit} ⭐").format(fisrt_name=fisrt_name or '',
                                                                                   last_name=last_name or '',
                                                                                   limit=me.current_ai_limit)


async def main_cabinet(message: Message, ):
    await message.answer(
        await get_cabinet_text(message.from_user.first_name, message.from_user.last_name, message.from_user.id),
        reply_markup=get_chatgt_main_kbrd())


@client_bot_router.message(text=__("🌐 ИИ"))
@flags.rate_limit(key="ai")
async def music_menu(message: Message, state: FSMContext):
    await main_cabinet(message)


@client_bot_router.message(text=__("🔍 Гугл поиск"))
@flags.rate_limit(key="ai-google-search")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer(
        _('🔍 Гугл поиск:\n\n'
          '🔘 Напишите запрос, а бот составит вопросы и ответит на него, предоставляя ссылки.\n\n'
          '⚡️ 1 запрос = {price} ⭐\n\n'
          'Осталось: {limit} ⭐\n\n').format(price=PRICING["google_search"]["without_context"],
                                            limit=user.current_ai_limit),
        reply_markup=get_kbrd_chat_type("google_search", use_context=False)
    )


@client_bot_router.message(text=__("🎥 Транскрипция ютуб"))
@flags.rate_limit(key="youtube-transcription")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer(
        _('🤖 Транскрипция ютуб видео :\n\n'
          '📋 Используется самая последняя языковая модель GPT-3.5 turbo.\n\n'
          '🔘 Принимает ссылку на YouTube видео.\n\n'
          '⚡️ 10 минут = {price} ⭐\n\n'
          'Осталось: {limit} ⭐\n\n').format(price=PRICING["youtube_transcription"]["without_context"],
                                            limit=user.current_ai_limit),
        reply_markup=get_kbrd_chat_type("youtube_transcription", use_context=False)
    )


@client_bot_router.message(text=__("☁ Чат с GPT-4"))
@flags.rate_limit(key="chat-gpt4")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer(
        _('🤖 GPT-4:\n\n'
          '📋 Используется самая последняя языковая модель GPT-4 Turbo.\n\n'
          '🔘 Принимает текст.\n\n'
          '🗯 Чат без контекста — не учитывает контекст, каждый ваш запрос как новый диалог.\n'
          '⚡️ 1 запрос = {price} ⭐\n\n'
          '💬 Чат с контекстом — каждый ответ с учетом контекста вашего диалога.\n'
          '⚡️ 1 запрос = {price2} ⭐\n\n'
          'Осталось: {limit} ⭐\n\n'
          '└ Выберите чат:').format(price=PRICING["gpt4"]["without_context"], price2=PRICING["gpt4"]["with_context"],
                                    limit=user.current_ai_limit),
        reply_markup=get_kbrd_chat_type("gpt4")
    )


@client_bot_router.message(text=__("☁ Чат с GPT-3.5"))
@flags.rate_limit(key="chat-gpt3.5")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer(
        _('🤖 GPT-3.5:\n\n'
          '📋 Используется самая экономически эффективная модель GPT-3.5 Turbo.\n\n'
          '🔘 Принимает текстовое сообщение.\n\n'
          '🗯 Чат без контекста — не учитывает контекст, каждый ваш запрос как новый диалог.\n'
          '⚡️ 1 запрос = {price} ⭐\n\n'
          '💬 Чат с контекстом — каждый ответ с учетом контекста вашего диалога.\n'
          '⚡️ 1 запрос = {price2} ⭐\n\n'
          'Осталось: {limit} ⭐\n\n'
          '└ Выберите чат:').format(price=PRICING["gpt3"]["without_context"], price2=PRICING["gpt3"]["with_context"],
                                    limit=user.current_ai_limit),
        reply_markup=get_kbrd_chat_type("gpt3")
    )


@client_bot_router.message(text=__("🎨 Генератор фото [DALL-E]"))
@flags.rate_limit(key="gen-dalle-photo")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer(
        _('🤖 DALL·E:\n\n'
          '📋 DALL·E 3 — это нейросеть, которая может создавать реалистичные изображения и произведения искусства на основе вашего описания.\n\n'
          '🔘 Принимает описание: текстовое или голосовое сообщение, либо фото.\n'
          '⚡️ 1 запрос = {price} ⭐\n\n'
          'Осталось: {user.current_ai_limit} ⭐').format(price=PRICING["dalle"]["without_context"],
                                                        limit=user.current_ai_limit),
        reply_markup=get_kbrd_chat_type("dalle", use_context=False)
    )


@client_bot_router.message(text=__("🗣️Голосовой помощник"))
@flags.rate_limit(key="ai-assistant")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer( \
        _('🤖 Голосовой ассистент:\n\n'
          '📋 Первый голосовой ассистент в Telegram на базе ChatGPT.\n\n'
          '🔘 Принимает голосовое сообщение.\n'
          '⚡️ 1 запрос = {price} ⭐\n\n'
          'Осталось: {limit} ⭐').format(price=PRICING["assistant"]["without_context"], limit=user.current_ai_limit),
        reply_markup=get_kbrd_chat_type("assistant", use_context=False)
    )


@client_bot_router.message(text=__("🗨️ Текст в аудио"))
@flags.rate_limit(key="text-to-speech")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer(
        _('🤖 Текст в голос:\n\n'
          '📋 Модель искусственного интеллекта, которая преобразует текст в естественно звучащий устный текст.\n'
          '⚡️ 1 запрос = {price} ⭐\n\n'
          'Осталось: {limit} ⭐\n\n'
          '└ Выберите голос:').format(price=PRICING["text-to-speech"]["without_context"], limit=user.current_ai_limit),
        reply_markup=get_kbrd_speech_voices()
    )


@client_bot_router.message(text="🔉 Аудио в текст")
@flags.rate_limit(key="speech-to-text")
async def music_menu(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    await message.answer( \
        '🤖 Голос в текст:\n\n'
        '📋 Модель ИИ, которая преобразует ваше аудио в текст.\n'
        f'⚡️ 1 запрос = {PRICING["speech-to-text"]["without_context"]} ⭐\n\n'
        f'Осталось: {user.current_ai_limit} ⭐\n\n'
        '└ Попробуйте:',
        reply_markup=get_kbrd_chat_type("speech-to-text", use_context=False)
    )


@client_bot_router.message(text=__("ℹ️ Помощь"))
@flags.rate_limit(key="ai-help")
async def music_menu(message: Message, state: FSMContext):
    bot = Bot.get_current()
    bot_db = await get_bot_by_token(bot.token)
    owner: models.MainBotUser = await bot_db.owner
    user: models.User = await owner.user
    link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.uid}"
    await message.answer(_("ℹ️ Помощь:"), reply_markup=get_kbrd_help(link))


async def run_ai_query(bot_token: str, user_id: int, message: str, context: bool, message_id: int, model_type: str,
                       voice: str = None, cost: float = None):
    async with Bot(bot_token, bot_session, parse_mode="HTML").context(auto_close=False) as bot_:
        try:
            if model_type in ['gpt4', 'gpt3']:
                await bot_.send_chat_action(user_id, "typing")
                # async with ChatActionSender.typing(chat_id=user_id) as c:
                model = MODEL_TYPE[model_type]
                gpt_answer = robot.chat_gpt(user_id=user_id, message=message, model=model, context=context)
                await bot_.send_message(user_id, gpt_answer, reply_to_message_id=message_id, parse_mode='Markdown')
                await add_record(bot_token, user_id, message, models.GPTTypeEnum.REQUEST)
            elif model_type == 'dalle':
                await bot_.send_chat_action(user_id, "upload_photo")
                pic = robot.text_to_picture(message)
                await bot_.send_photo(user_id, URLInputFile(pic.data[0].url), reply_to_message_id=message_id,
                                      parse_mode='Markdown', request_timeout=5000000)
                await add_record(bot_token, user_id, message, models.GPTTypeEnum.PICTURE)
            elif model_type == 'text-to-speech':
                await bot_.send_chat_action(user_id, "record_voice")
                audio = robot.text_to_audio(voice, message)
                name = f"{user_id}_{message_id}.ogg"
                audio.stream_to_file(name)
                await bot_.send_voice(user_id, FSInputFile(name), reply_to_message_id=message_id)
                os.remove(name)
                await add_record(bot_token, user_id, message, models.GPTTypeEnum.TEXT_TO_SPEECH)
            elif model_type == 'speech-to-text':
                await bot_.send_chat_action(user_id, "typing")
                name = f"{user_id}_{message_id}.ogg"
                await bot_.download_file(message, name)
                audio = robot.audio_to_text(Path(name))
                await bot_.send_message(user_id, audio, reply_to_message_id=message_id, parse_mode='Markdown')
                os.remove(name)
                await add_record(bot_token, user_id, message, models.GPTTypeEnum.SPEECH_TO_TEXT)
            elif model_type == 'assistant':
                await bot_.send_chat_action(user_id, "record_voice")
                name = f"{user_id}_{message_id}.ogg"
                await bot_.download_file(message, name)
                audio = robot.audio_to_text(Path(name))
                model = MODEL_TYPE["gpt4"]
                gpt_answer = robot.chat_gpt(user_id=user_id, message=audio, model=model, context=False)
                audio = robot.text_to_audio("echo", gpt_answer)
                audio.stream_to_file(f"answer-{name}")
                await bot_.send_voice(user_id, FSInputFile(f"answer-{name}"), reply_to_message_id=message_id)
                os.remove(name)
                os.remove(f"answer-{name}")
                await add_record(bot_token, user_id, message, models.GPTTypeEnum.ASSISTANT)
            elif model_type == 'google_search':
                res = robot.google_search(user_id, message)
                await bot_.send_message(user_id, res, reply_to_message_id=message_id, parse_mode='HTML')
        except Exception as e:
            user = await get_user(user_id)
            user.current_ai_limit += cost
            await user.save()
            await bot_.send_message(user_id, f"Ошибка: {e}\nМы вернули: {cost} 🌟", reply_to_message_id=message_id)


async def run_ai_vidio_summary(bot_token: str, user_id: int, video_id: str, message_id: int, cost: int):
    async with Bot(bot_token, bot_session, parse_mode="HTML").context(auto_close=False) as bot_:
        try:
            await bot_.send_chat_action(user_id, "typing")
            result = robot.extract_youtube_transcript(user_id, video_id)
            await bot_.send_message(user_id, result, reply_to_message_id=message_id, parse_mode='Markdown')
        except Exception as e:
            user = await get_user(user_id)
            user.current_ai_limit += cost
            await user.save()
            await bot_.send_message(user_id, _("Ошибка: {e}\nМы вернули: {cost} 🌟").format(e=e, cost=cost),
                                    reply_to_message_id=message_id)


@client_bot_router.message(state=AIState.input_prompt)
@flags.rate_limit(key="input-prompt")
async def music_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bot = Bot.get_current()
    bot_db = await get_bot_by_token(bot.token)
    if message.text:
        if message.text == _('Отменить ввод'):
            if have_one_module(bot_db, "chatgpt"):
                await message.answer(_("Отменено"), reply_markup=await main_menu(user_id))
            else:
                await main_cabinet(message)
            await state.clear()
            return

    user = await get_user(user_id)
    data = await state.get_data()
    model_type = data.get("model")
    voice = ""
    use_context = False
    content = ""
    if model_type == 'youtube_transcription':
        duration = ChatGPT.get_youtube_duration(message.text)
        sum = math.ceil(duration / PRICING["youtube_transcription"]["minutes"]) * PRICING["youtube_transcription"][
            "without_context"]
        video_id_match = re.search(r"(?<=v=)[^&]+|(?<=youtu.be/)[^?|\n]+", message.text)
        video_id = video_id_match.group(0) if video_id_match else None
        if video_id is None:
            await message.answer(_("Не получилось получить транскрипцию, попробуйте другую ссылку"))
        await message.answer(
            _("⌛️ продолжительность видео: {duration} минут\r\nСтоимость: {sum}⭐️").format(duration=duration, sum=sum),
            reply_markup=get_kbrd_agree(video_id, sum, message.message_id))
        return
    if model_type == 'youtube_transcription':
        content = message.text
    elif model_type == 'text-to-speech':
        voice = data.get("voice")
        content = message.text
    elif model_type in ['speech-to-text', 'assistant']:
        if not message.voice:
            await message.answer(_("Пожалуйста, отправьте голосовое сообщение"))
            return
        content = (await bot.get_file(message.voice.file_id)).file_path
    else:
        use_context = data.get("use_context")
        content = message.text
    cost = PRICING[model_type]["with_context" if use_context else "without_context"]
    if user.current_ai_limit < cost:
        bot_db = await get_bot_by_token(bot.token)
        await message.answer(_("Недостаточно средств"),
                             reply_markup=await get_kbrd_ai_balance(message.from_user.id, bot_db.percent))
        await state.clear()
        return
    user.current_ai_limit -= cost
    await user.save()
    await message.answer(
        _("Запрос принят, ожидайте ответа\nОсталось: {limit} ⭐\nВы можете продолжить ввод, чтобы получать дополнительные ответы или нажмите на кнопка 'Отменить ввод' чтобы прекратить").format(
            limit=user.current_ai_limit))
    scheduler.add_job(run_ai_query,
                      args=(bot.token, user_id, content, use_context, message.message_id, model_type, voice, cost),
                      max_instances=1, misfire_grace_time=60, coalesce=False, id=f"{user_id}_{message.message_id}",
                      replace_existing=False)


@client_bot_router.message(text=__('🔋 Баланс'))
@flags.rate_limit(key="ai-balance")
async def music_menu(message: Message, state: FSMContext):
    await message.answer(
        await get_cabinet_text(message.from_user.first_name, message.from_user.last_name, message.from_user.id),
        reply_markup=get_kbrd_ai_cabinet())
