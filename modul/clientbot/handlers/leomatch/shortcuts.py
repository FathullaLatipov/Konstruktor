from dataclasses import dataclass

from aiogram.types import ReplyKeyboardMarkup
from django.core.files import File
from django.db.models import Q, F

from modul.models import LeoMatchLikesBasketModel, SexEnum, User, LeoMatchModel, MediaTypeEnum, UserTG
from aiogram import Bot, types
from modul.clientbot.shortcuts import get_bot_by_username, get_current_bot
from modul.clientbot.handlers.leomatch.keyboards.inline_kb import write_profile
from modul.clientbot import shortcuts
from modul.config import settings_conf
from modul.loader import bot_session
from asgiref.sync import sync_to_async


@sync_to_async
def get_client(uid: int):
    print(UserTG.objects.filter(uid=uid).first(), "qwerty")
    return UserTG.objects.filter(uid=uid).first()




@sync_to_async
def get_leo_match(user):
    print(LeoMatchModel.objects.filter(user=user).first())
    return LeoMatchModel.objects.filter(user=user).first()


async def get_leo(uid: int):
    user = await get_client(uid)
    if user:
        leo = await get_leo_match(user)
        return leo
    return None


@sync_to_async
def filter_leos_sync(kwargs, age_range, sex, leo_me_id):
    return LeoMatchModel.objects.filter(
        blocked=False,
        age__range=age_range,
        search=True,
        active=True,
        **kwargs
    ).exclude(
        Q(which_search__in=[sex, SexEnum.ANY.value]) | Q(id=leo_me_id)
    ).annotate(order=F('random')).order_by('order')[:50]

@sync_to_async
def get_user_uid_sync(leo):
    return leo.user.uid


async def get_leos_id(me: int):
    users_id = []
    leo_me = await get_leo(me)
    kwargs = {}
    if leo_me.which_search != SexEnum.ANY.value:
        kwargs['sex'] = leo_me.which_search
    age_range = (leo_me.age - 3, leo_me.age + 3)
    leos = await filter_leos_sync(kwargs, age_range, leo_me.sex, leo_me.id)
    for leo in leos:
        user_uid = await get_user_uid_sync(leo)
        users_id.append(user_uid)
    return users_id


async def exists_leo(uid: int):
    return await get_leo(uid) is not None


@sync_to_async
def create_leomatch(user, photo, media_type, sex, age, full_name, about_me, city, which_search, bot_username):
    print(f"User: {user}")
    print(f"Photo: {photo}")
    print(f"Media Type: {media_type}")
    print(f"Sex: {sex}")
    print(f"Age: {age}")
    print(f"Full Name: {full_name}")
    print(f"About Me: {about_me}")
    print(f"City: {city}")
    print(f"Which Search: {which_search}")
    print(f"Bot Username: {bot_username}")

    # Ensure the user exists
    if not UserTG.objects.filter(uid=user.uid).exists():
        print(f"UserTG with pk {user.uid} does not exist.")
        raise ValueError(f"UserTG with pk {user.uid} does not exist.")

    return LeoMatchModel.objects.create(
        user=user,
        photo=photo,
        media_type=media_type,
        sex=sex,
        age=age,
        full_name=full_name,
        about_me=about_me,
        city=city,
        which_search=which_search,
        bot_username=bot_username
    )


async def add_leo(uid: int, photo: str, media_type: str, sex: str, age: int, full_name: str, about_me: str, city: str,
                  which_search: str, bot_username: str):
    client = await get_client(uid)
    # bot = await shortcuts.get_bot_by_username(bot_username)
    # async with Bot(token=bot.token, session=bot_session).context(auto_close=False) as bot_:
    #     format_m = "jpg" if media_type == "PHOTO" else "mp4"
    #     await bot_.download(photo, f"/Users/ibragimkadamzanov/PycharmProjects/pythonProject21/modul/clientbot/data/leo{uid}.{format_m}")
    info = await create_leomatch(client, photo, media_type, sex, age, full_name, about_me, city, which_search,
                                 bot_username)


@sync_to_async
def save_model_sync(model):
    model.save()


async def update_leo(uid: int, photo: str, media_type: str, sex: str, age: int, full_name: str, about_me: str,
                     city: str, which_search: str):
    leo = await get_leo(uid)
    bot = await shortcuts.get_bot_by_username(leo.bot_username)
    print(media_type)

    # async with Bot(token=bot.token, session=bot_session).context(auto_close=False) as bot_:
    #     format_m = "jpg" if media_type == "PHOTO" else "mp4"
    #     photo_path = f"clientbot/data/leo{uid}.{format_m}"
    #     await bot_.download(photo, photo_path)

    # with open(photo_path, 'rb') as f:
    #     django_file = File(f)
    #     await sync_to_async(leo.photo.save)(f"{uid}.{format_m}", django_file)

    leo.media_type = media_type
    leo.sex = sex
    leo.age = age
    leo.full_name = full_name
    leo.about_me = about_me
    leo.city = city
    leo.which_search = which_search

    leo.save()


async def show_media(bot: Bot, to_account: int, from_account: int, text_before: str = "",
                     reply_markup: types.ReplyKeyboardMarkup = None):
    account = await get_leo(from_account)
    account_user = account.user
    account_id = account_user.uid
    text = f"{text_before}\r\n{account.full_name} {account.age}, г {account.city}\n\n{account.about_me}"
    if account.media_type.value == MediaTypeEnum.VIDEO_NOTE.value:
        await bot.send_video_note(to_account, video_note=types.FSInputFile(f"clientbot/data/leo/{account_id}.mp4"),
                                  reply_markup=reply_markup)
        await bot.send_message(to_account, text=text)
    elif account.media_type.value == MediaTypeEnum.VIDEO.value:
        await bot.send_video(to_account, video=types.FSInputFile(f"clientbot/data/leo/{account_id}.mp4"),
                             reply_markup=reply_markup)
        await bot.send_message(to_account, text=text)
    elif account.media_type.value == MediaTypeEnum.PHOTO.value:
        await bot.send_photo(to_account, photo=types.FSInputFile(f"clientbot/data/leo/{account_id}.jpg"), caption=text)
    else:
        await bot.send_message(to_account, text=text)


async def show_profile(message: types.Message, uid: int, full_name: str, age: int, city: str, about_me: str, url: str,
                       type: str, keyboard=None, comment: str = None):
    text = f"\n\nВам сообщение: {comment}" if comment else ""
    caption = f"{full_name}, {age}, {city}\n{about_me}{text}"
    kwargs = {}
    if keyboard:
        kwargs['reply_markup'] = keyboard
    try:
        await message.answer_video(types.FSInputFile(f"modul/clientbot/data/leo{uid}.mp4"), )
        await message.answer(caption, **kwargs)
    except:
        await message.answer_photo(types.FSInputFile(f"modul/clientbot/data/leo{uid}.jpg"), caption=caption, **kwargs)


async def bot_show_profile(to_uid: int, from_uid: int, full_name: str, age: int, city: str, about_me: str, url: str,
                           type: str, username: str, keyboard=None):
    leo = await get_leo(to_uid)
    bot = await get_bot_by_username(leo.bot_username)
    caption = f"{full_name}, {age}, {city}\n{about_me}"
    kwargs = {}
    if keyboard:
        kwargs['reply_markup'] = keyboard
    async with Bot(bot.token, bot_session, parse_mode="HTML").context(auto_close=False) as bot_:
        await bot_.send_message(to_uid, "Есть взаимная симпатия!")
        if type == "PHOTO" or type == MediaTypeEnum.PHOTO:
            await bot_.send_photo(to_uid, types.FSInputFile(f"clientbot/data/leo/{from_uid}.jpg"), caption=caption,
                                  **kwargs)
        elif type == "VIDEO" or type == MediaTypeEnum.VIDEO:
            await bot_.send_video(to_uid, types.FSInputFile(f"clientbot/data/leo/{from_uid}.mp4"), caption=caption,
                                  **kwargs)

        is_username = False
        if username:
            link = username
            is_username = True
        else:
            link = from_uid
        try:
            await bot_.send_message(to_uid, ("Начнинай общаться!"), reply_markup=write_profile(link, is_username))
        except:
            await bot_.send_message(to_uid,
                                    ("Извините, Вы не сможете начать общение так как у пользователя приватный аккаунт"))


async def show_profile_db(message: types.Message, uid: int, keyboard=ReplyKeyboardMarkup, comment: str = None):
    leo = await get_leo(uid)
    await show_profile(message, uid, f'{leo.full_name}', leo.age, leo.city, leo.about_me, leo.photo, leo.media_type,
                       keyboard=keyboard, comment=comment)


async def bot_show_profile_db(to_uid: int, uid: int, keyboard=types.ReplyKeyboardMarkup):
    leo = await get_leo(uid)
    user = await leo.user
    await bot_show_profile(to_uid, uid, f'{leo.full_name}', leo.age, leo.city, leo.about_me, leo.photo, leo.media_type,
                           user.username, keyboard=keyboard)


async def update_profile(uid: int, kwargs: dict):
    leo = await get_leo(uid)
    for key, value in kwargs.items():
        setattr(leo, key, value)
    leo.save()


@sync_to_async
def create_like(from_uid: int, to_uid: int, message: str = None):
    return LeoMatchLikesBasketModel.objects.create(
        from_user=get_leo(from_uid),
        to_user=get_leo(to_uid),
        message=message,
    )


async def leo_set_like(from_uid: int, to_uid: int, message: str = None):
    info = await create_like(from_uid, to_uid, message)
    return await info


@sync_to_async
def get_likes_count_sync(user):
    return LeoMatchLikesBasketModel.objects.filter(to_user=user, done=False).all().count()


async def get_likes_count(uid: int):
    info = await get_likes_count_sync(await get_leo(uid))
    return info


@sync_to_async
def get_distinkt_likes_sync():
    leos = LeoMatchLikesBasketModel.objects.filter(done=False).all()
    return leos


async def get_distinkt_likes():
    leos = await get_distinkt_likes_sync()
    return await leos.distinct()


@sync_to_async
def get_first_like_sync(user):
    return LeoMatchLikesBasketModel.objects.filter(to_user=user, done=False).first()


@sync_to_async
def clear_all_likes_sync(user):
    return LeoMatchLikesBasketModel.objects.filter(to_user=user, done=False).update(done=True)


@sync_to_async
def delete_like_sync(user1, user2):
    return LeoMatchLikesBasketModel.objects.filter(from_user=user1, to_user=user2).delete()


async def get_first_like(uid: int):
    info = await get_first_like_sync(await get_leo(uid))
    return await info


async def clear_all_likes(uid: int):
    info = await clear_all_likes_sync(await get_leo(uid))
    return await info


async def delete_like(from_uid: int, to_uid: int):
    info = await delete_like_sync(await get_leo(from_uid), await get_leo(to_uid))
    return await info


@dataclass
class Analitics:
    count_users: int
    count_man: int
    count_female: int


async def get_analitics(bot_username: str = None):
    kwargs = {}
    if bot_username:
        kwargs['bot_username'] = bot_username
    users = LeoMatchModel.objects.filter(**kwargs, active=True, search=True).all()
    man = users.objects.filter(sex=SexEnum.MALE)
    female = users.objects.filter(sex=SexEnum.FEMALE)
    return Analitics(await users.count(), await man.count(), await female.count())
