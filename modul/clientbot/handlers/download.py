from aiogram import html, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from clientbot import shortcuts
from clientbot.data.states import Download
from db.models import TaskModel, TaskType
from loader import client_bot_router, bot_session
from config import scheduler
from clientbot.keyboards.reply_kb import download_main_menu, main_menu
import yt_dlp
import os


@client_bot_router.message(text=__("Назад"), state=Download.download)
async def music_menu(message: Message, state: FSMContext):
    await message.answer(
        _("Добро пожаловать, {full_name}").format(full_name=html.quote(message.from_user.full_name)),
        reply_markup=await main_menu(message.from_user.id)
    )
    await state.clear()


@client_bot_router.message(text=__("🌐 Скачать видео"))  # удалить через неделю
async def music_menu(message: Message, state: FSMContext):
    await message.answer(_("Этот пункт изменился, пожалуйста, нажмите /start, чтобы обновить панель"))


@client_bot_router.message(text=__("🎥 Скачать видео"))
async def music_menu(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Download.download)
    # await message.answer("Пришлите ссылку на Youtube или ТикТок видео и я его скачаю для вас", reply_markup=await download_main_menu())
    user_name = f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
    await message.answer(
        _("🤖 Привет, {user_name}! Я бот-загрузчик.\r\n\r\n"
          "Я могу скачать фото/видео/аудио/файлы/архивы с *Youtube, Instagram, TikTok, Facebook, SoundCloud, Vimeo, Вконтакте, Twitter и 1000+ аудио/видео/файловых хостингов*. Просто пришли мне URL на публикацию с медиа или прямую ссылку на файл.").format(
            user_name=user_name),
        reply_markup=await download_main_menu(),
        parse_mode="Markdown"
    )


@client_bot_router.message(state=Download.download)
async def youtube_download_handler(message: Message, bot: Bot):
    await message.answer(_('📥 Скачиваю...'))
    if not message.text:
        await message.answer(_('Пришлите ссылку на видео'))
        return
    if 'streaming' in message.text:
        await message.answer(_('Извините, но я не могу скачать стримы'))
        return
    me = await bot.get_me()
    await shortcuts.add_to_analitic_data(me.username, message.text)
    if 'instagram' in message.text:
        new_url = message.text.replace('www.', 'dd')
        await message.answer(
            _('{new_url}\r\nВидео скачано через бота @{username}').format(new_url=new_url, username=me.username))
        return
    client = await shortcuts.get_user(message.from_user.id)
    await TaskModel.create(
        client=client,
        task_type=TaskType.DOWNLOAD_MEDIA,
        data={
            "url": message.text,
        }
    )
