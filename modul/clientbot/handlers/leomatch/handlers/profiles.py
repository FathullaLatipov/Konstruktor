from modul.clientbot.handlers.leomatch.data.state import LeomatchProfiles
from modul.clientbot.handlers.leomatch.shortcuts import bot_show_profile_db, clear_all_likes, delete_like, get_leo, \
    get_leos_id, get_first_like, leo_set_like, show_media, show_profile_db
from modul.clientbot.handlers.leomatch.keyboards.inline_kb import profile_alert, profile_alert_action, \
    profile_like_action, \
    profile_view_action, write_profile
from modul.clientbot.handlers.leomatch.keyboards.reply_kb import cancel
from modul.clientbot.handlers.leomatch.data.callback_datas import LeomatchLikeAction, LeomatchProfileAction, \
    LeomatchProfileAlert, LeomatchProfileBlock, LikeActionEnum, ProfileActionEnum
from modul.clientbot.handlers.leomatch.handlers.shorts import manage
from modul.models import LeoMatchModel, User
from modul.config import settings_conf
from modul.loader import client_bot_router, main_bot, main_bot_router
from aiogram.fsm.context import FSMContext
from aiogram import types, F


async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔍", reply_markup=types.ReplyKeyboardRemove())
    leos = await get_leos_id(message.from_user.id)
    await state.set_data({"leos": leos})
    await next_l(message, state)


async def next_l(message: types.Message, state: FSMContext):
    data = await state.get_data()
    leos = data.get("leos")
    if len(leos) > 0:
        current = leos.pop(0)
        await state.update_data(leos=leos)
        await show_profile_db(message, current, keyboard=profile_view_action(current))
        await state.set_state(LeomatchProfiles.LOOCK)
    else:
        await message.answer(("Нет больше пользователей"))
        await manage(message, state)


async def next_like(message: types.Message, state: FSMContext):
    data = await state.get_data()
    me = data.get("me")
    if not me:
        me = message.from_user.id
    leo = await get_first_like(me)
    if leo:
        user_leo = await leo.from_user
        user = await user_leo.user
        try:
            await show_profile_db(message, user.uid, profile_like_action(user.uid), leo.message)
            await state.set_state(LeomatchProfiles.MANAGE_LIKE)
        except:
            await delete_like(user.uid, me)
            await next_like(message, state)
    else:
        leo_me = await get_leo(me)
        await state.clear()
        await message.answer(("Нет больше лайков"))
        leo_me.count_likes = 0
        await leo_me.save()


async def like(message: types.Message, state: FSMContext, from_uid: int, to_uid: int, msg: str = None):
    await message.answer(("Лайк отправлен"), reply_markup=types.ReplyKeyboardRemove())
    await leo_set_like(from_uid, to_uid, msg)
    await next_l(message, state)


@client_bot_router.callback_query(LeomatchProfileAction.filter(), LeomatchProfiles.LOOCK)
async def choose_percent(query: types.CallbackQuery, state: FSMContext, callback_data: LeomatchProfileAction):
    await query.message.edit_reply_markup()
    await state.update_data(me=query.from_user.id)
    if callback_data.action == ProfileActionEnum.LIKE:
        await like(query.message, state, query.from_user.id, callback_data.user_id)
    elif callback_data.action == ProfileActionEnum.MESSAGE:
        await query.message.answer(("Введите сообщение или отправьте видео (макс 15 сек)"), reply_markup=cancel())
        await state.update_data(selected_id=callback_data.user_id)
        await state.set_state(LeomatchProfiles.INPUT_MESSAGE)
    elif callback_data.action == ProfileActionEnum.REPORT:
        try:
            await query.message.delete()
        except:
            pass
        await query.message.answer(
            ("Вы точно хотите подать жалобу? Учтите, если жалоба будет необоснованной то вы сами можете быть забанены"),
            reply_markup=profile_alert(query.from_user.id, callback_data.user_id))
    elif callback_data.action == ProfileActionEnum.SLEEP:
        pass
    elif callback_data.action == ProfileActionEnum.DISLIKE:
        await next_l(query.message, state)


@client_bot_router.message(F.text == ("Отменить"), LeomatchProfiles.INPUT_MESSAGE)
async def bot_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    leos: list = data.get("leos")
    leos.insert(0, data.get("selected_id"))
    await state.update_data(selected_id=None, leos=leos)
    await message.answer(("Отменено"), reply_markup=types.ReplyKeyboardRemove())
    await next_l(message, state)


@client_bot_router.message(LeomatchProfiles.INPUT_MESSAGE)
async def bot_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_id = data.get("selected_id")
    await state.update_data(selected_id=None)
    await state.set_state("*")
    msg = None
    if message.text:
        msg = message.text
    elif message.video_note:
        msg = message.video_note.file_id
    else:
        await message.answer(("Пожалуйста, напишите текст или отправьте видео"))
        return
    await like(message, state, message.from_user.id, selected_id, msg)


@client_bot_router.message(F.text == ("Да"), LeomatchProfiles.MANAGE_LIKES)
async def bot_start(message: types.Message, state: FSMContext):
    await message.answer(("Вот акканты, кому Вы понравились:"), reply_markup=types.ReplyKeyboardRemove())
    await next_like(message, state)


@client_bot_router.message(F.text == ("Нет"), LeomatchProfiles.MANAGE_LIKES)
async def bot_start(message: types.Message):
    await message.answer(("Все лайки удалены"), reply_markup=types.ReplyKeyboardRemove())
    await clear_all_likes(message.from_user.id)


@client_bot_router.callback_query(LeomatchProfileAction.filter(), LeomatchProfiles.MANAGE_LIKE)
async def choose_percent(query: types.CallbackQuery, state: FSMContext, callback_data: LeomatchLikeAction):
    try:
        await query.message.edit_reply_markup()
    except:
        pass
    if callback_data.action == LikeActionEnum.LIKE:
        leo = await get_leo(callback_data.user_id)
        link = ""
        client = await leo.user

        is_username = False
        if client.username:
            link = client.username
            is_username = True
        else:
            link = client.uid
        try:
            await bot_show_profile_db(callback_data.user_id, query.from_user.id)
        except:
            await next_like(query.message, state)
        try:
            await query.message.answer(("Начнинай общаться!"), reply_markup=write_profile(link, is_username))
        except:
            await query.message.answer(
                ("Извините, Вы не сможете начать общение так как у пользователя приватный аккаунт"))
    elif callback_data.action == LikeActionEnum.REPORT:
        pass
    await state.set_data({"me": query.from_user.id})
    await delete_like(callback_data.user_id, query.from_user.id)
    await next_like(query.message, state)


@client_bot_router.callback_query(LeomatchProfileAlert.filter(), LeomatchProfiles.LOOCK)
async def choose_percent(query: types.CallbackQuery, state: FSMContext, callback_data: LeomatchProfileAlert):
    if callback_data.action == "yes":
        sender: LeoMatchModel = await get_leo(callback_data.sender_id)
        account: LeoMatchModel = await get_leo(callback_data.account_id)
        sender_user: User = await sender.user
        account_user: User = await account.user
        await show_media(main_bot, settings_conf.ADMIN, callback_data.account_id)
        await main_bot.send_message(
            chat_id=settings_conf.ADMIN,
            text=("Пользователь: @{sender_user} ({sender_user_id}) пожаловался на \n"
                  "Пользователя: @{account_user} ({account_user_id})\n").format(sender_user=sender_user.username,
                                                                                sender_user_id=sender_user.uid,
                                                                                account_user=account_user.username,
                                                                                account_user_id=account_user.uid),
            reply_markup=profile_alert_action(callback_data.sender_id, callback_data.account_id)
        )
        await query.message.edit_text(("Жалоба отправлена"))
    await state.update_data(me=query.from_user.id)
    await next_l(query.message, state)
