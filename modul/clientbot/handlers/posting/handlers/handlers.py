import asyncio
import os
import logging
import time
import re

from bot.all_openai import ChatGPT
import pytz
from datetime import datetime
import requests
from aiogram import Router, F, types
from aiogram.dispatcher.filters import Command
from aiogram.fsm.context import FSMContext
from dotenv import dotenv_values
from bot.markup import keyboards
from bot.services.States import Form
from bot.database import Database
from bot.markup.keyboards import secure_mode
from bot.date_d import sheduled_post

IMAGES_DIRECTORY = 'media'
logging.basicConfig(level=logging.INFO)
user_message_id = {}
user_timer_time = {}
user_post_delay = {}
user_template_value = {}
data = Database()
robot = ChatGPT()

env_vars = dotenv_values(".env")

api_token = env_vars.get("API_TOKEN")

route = Router()


"""Some Func"""


def sub(user_id):
    return data.get_user_subscription(user_id)


async def delay_post(message: types.Message, send_time) -> None:
    data.add_content(data.get_post_text(user_message_id[message.from_user.id]), send_time)
    user_id = message.from_user.id
    print(channel_id_data.get(message.from_user.id))
    now = datetime.now()
    delta = send_time - now
    if delta.total_seconds() > 0:
        await message.answer(
            f'''Публикация запланирована в канал  {channel_id_data.get(message.from_user.id)[1]} и будет опубликована в 
{send_time}''')
        await asyncio.sleep(delta.total_seconds())
        ch_id = channel_id_data.get(message.from_user.id)[0]
        m_id = user_message_id[message.from_user.id]
        media_data = data.get_post_media(m_id)
        button_data = data.get_post_url_name(m_id)
        print(ch_id, data.get_all_posts())
        print(data.get_post_url(m_id))
        if media_data is None and button_data is None:
            message_m = await message.bot.send_message(ch_id, f'''{data.get_post_text(m_id)}''',
                                                       disable_notification=keyboards.silent_mode)
            message_id = message_m.message_id
            print(message_id)
        elif media_data is not None and button_data is None:
            await message.bot.send_photo(chat_id=ch_id, photo=data.get_post_media(m_id),
                                         caption=f'''{data.get_post_text(m_id)}''',
                                         disable_notification=keyboards.silent_mode)
        elif media_data is None and button_data is not None:
            button = [[types.InlineKeyboardButton(text=button_data, url=data.get_post_url(m_id))]]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
            await message.bot.send_message(ch_id, f'''{data.get_post_text(m_id)}''',
                                           disable_notification=keyboards.silent_mode, reply_markup=keyboard)
        elif media_data is not None and button_data is not None:
            button = [[types.InlineKeyboardButton(text=button_data, url=data.get_post_url(m_id))]]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
            await message.bot.send_photo(ch_id, data.get_post_media(m_id), caption=data.get_post_text(m_id),
                                         disable_notification=keyboards.silent_mode, reply_markup=keyboard)
        else:
            await message.answer('Что-то пошло не так')
        channel_id_data.clear()


def get_timezone_info(timezone_name='Asia/Tashkent'):
    timezone = pytz.timezone(timezone_name)
    now = datetime.now()
    now_with_tz = now.astimezone(timezone)
    offset_seconds = timezone.utcoffset(now_with_tz).total_seconds()
    offset_hours = offset_seconds / 3600
    offset_sign = '+' if offset_hours >= 0 else '-'
    offset_hours = abs(offset_hours)
    offset_minutes = (offset_hours % 1) * 60
    city_name = timezone_name.split('/')[-1].replace('_', ' ')
    return f"GMT {offset_sign}{int(offset_hours)}:{int(offset_minutes):02d} {city_name}"


async def delete_post(message: types.Message, chat_id: int, message_id: int, delay: int) -> None:
    # Ожидание перед удалением сообщения
    await asyncio.sleep(delay)
    await message.bot.delete_message(chat_id, message_id)


async def add_media_video(message):
    video_more = message.video.file_id
    fileid = await message.bot.get_file(video_more)
    file_url = f"https://api.telegram.org/file/bot{api_token}/{fileid}"
    response = requests.get(file_url)

    # Сохраняем файл в локальную директорию
    file_extension = fileid.file_path.split('.')[-1]
    vidoe_path = os.path.join(IMAGES_DIRECTORY, f"{video_more}.{file_extension}")

    with open(vidoe_path, "wb") as f:
        f.write(response.content)


async def add_media_photo(message):
    image_more = message.photo[-1].file_id
    fileid = await message.bot.get_file(image_more)
    file_url = f"https://api.telegram.org/file/bot{api_token}/{fileid}"
    response = requests.get(file_url)

    # Сохраняем файл в локальную директорию
    image_path = os.path.join(IMAGES_DIRECTORY, f"photo_{image_more}.jpg")
    with open(image_path, "wb") as image_file:
        image_file.write(response.content)


async def update_title(message: types.Message, new_title: str):
    media_data = data.get_post_media(user_message_id[message.from_user.id])
    await message.answer(new_title, reply_markup=keyboards.create_post_kb(media_data))


"""Command-Handlers"""


# Command_Handlers -> Start
@route.message(Command('start'))
async def start(message: types.Message):
    data.add_user(message.from_user.id, message.from_user.first_name)
    await message.answer('''<b>bot - это простой и удобный бот для отложенного постинга.

Бот позволяет: 

🕔 Планировать выход публикаций в ваших каналах

🗑 Автоматически удалять их по расписанию

👩‍🎨 Создавать и настраивать посты любого формата

👀 И многое другое</b>
''', reply_markup=keyboards.main_menu_kb(), parse_mode='HTML')


# Command_Handlers -> Post_Create
@route.message(Command('post'))
@route.message(F.text.lower() == 'создать пост')
async def process_chanel_command(message: types.Message, state: FSMContext) -> None:
    print(channel_id_data.get(message.from_user.id))
    print(len(data.get_all_chanels_name_from_user_id(message.from_user.id)))
    if len(data.get_all_chanels_name_from_user_id(message.from_user.id)) > 1:
        await message.answer('Выберите канал', reply_markup=keyboards.choose_channel(
            data.get_all_chanels_name_from_user_id(message.from_user.id)))
    elif len(data.get_all_chanels_name_from_user_id(message.from_user.id)) == 1:
        await message.answer(
            f"""<b>Отправьте боту то, что хотите опубликовать в канале {data.get_chanel_name(message.from_user.id)}</b><blockquote>Или вы можете создать пост 
C помощью Искуственного интелекта(chat-gpt 4 и Dall-E).</blockquote>""",
            reply_markup=keyboards.ai(), parse_mode='HTML')
        await state.set_state(Form.create_post)
    else:
        await state.set_state(Form.wait_for_forward)
        await message.answer(
            '''<b>Чтобы подключить канал, сделайте bot его администратором, дав следующие права:
            <blockquote>
✅ Отправка сообщений

✅ Удаление сообщений

✅ Редактирование сообщений
            </blockquote>
            
А затем перешлите любое сообщение из канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.</b>''',
            parse_mode='HTML')


channel_id_data = {}


@route.callback_query(F.data.in_(['create_ai', 'create_media_ai']))
async def create_ai(callback: types.CallbackQuery, state: FSMContext) -> None:
    if sub(callback.from_user.id):
        if callback.data == 'create_ai':
            await callback.message.edit_text(
                f'''<b>Отправьте боту тему для поста
<blockquote>Или вы можете создать несколько постов и отложить их .</blockquote></b>''', parse_mode='HTML',
                reply_markup=keyboards.delay_ai())
            await state.set_state(Form.create_ai_post)
        elif callback.data == 'create_media_ai':
            await callback.message.edit_text(
                f'''<b>Отправьте боту текс для фото</b>''', parse_mode='HTML')
            await state.set_state(Form.add_media_ai)
    else:
        if callback.data == 'create_media_ai':
            await state.clear()
            await callback.message.edit_text(
                f'''<b>Купите подписку для использования Искуственного интелекта
                    <blockquote>Купить можно через настройки</blockquote></b>''', parse_mode='HTML',
                reply_markup=keyboards.back())
        else:
            await callback.message.edit_text(
                f'''<b>Купите подписку для использования Искуственного интелекта
                    <blockquote>Купить можно через настройки</blockquote></b>''', parse_mode='HTML')
            await state.clear()


@route.message(Form.add_media_ai)
async def add_media_ai(message: types.Message, state: FSMContext) -> None:
    waiting = await message.answer("Генерирую изображение ...")
    if message.content_type == 'text':
        try:
            media_data = data.get_post_media(user_message_id[message.from_user.id])
            response = robot.text_to_picture(message.text)
            # await add_media_photo(message)

            await message.bot.send_photo(chat_id=message.chat.id, photo=response.data[0].url,
                                         caption=data.get_post_text(user_message_id[message.from_user.id]),
                                         reply_markup=keyboards.create_post_kb(media_data))
            m_id = user_message_id[message.from_user.id]
            data.update_media(m_id, response.data[0].url)
            await state.clear()
        except:
            await message.delete()
            await message.answer(
                "Не удалось сгенерировать изображение. Возможно, в запросе имеется запрещенный контент")
            m_id = user_message_id[message.from_user.id]
            media_data = data.get_post_media(m_id)
            await message.answer(f'''{data.get_post_text(m_id)}''', parse_mode='Markdown',
                                 reply_markup=keyboards.create_post_kb(media_data))


@route.message(Form.create_ai_post)
async def create_ai_post(message: types.Message, state: FSMContext) -> None:
    m_id = message.message_id
    ch_id = channel_id_data.get(message.from_user.id)[0]
    user_message_id[message.from_user.id] = m_id

    await state.clear()

    user_id = message.from_user.id
    if message.text:
        gpt_answer = robot.chat_gpt(user_id=user_id, message=message.text)
        data.add_post_text(ch_id, gpt_answer, m_id)
        media_data = data.get_post_media(m_id)
        await message.answer(f'''{gpt_answer}''', parse_mode='Markdown',
                             reply_markup=keyboards.create_post_kb(media_data))
    else:
        await message.answer(text='Я могу обробатывать только текст ! /start')


@route.callback_query(F.data.startswith('choose_'))
async def process_callback_channel(callback: types.CallbackQuery, state: FSMContext) -> None:
    for i in data.get_all_chanels_name_ch_id_from_user_id(callback.from_user.id):
        print(data.get_all_chanels_name_ch_id_from_user_id(callback.from_user.id))
        if i[0] == callback.data.split('_')[1]:
            channel_id_data[callback.from_user.id] = [i[1], i[0]]
            await callback.message.edit_text(f"""<b>Отправьте боту то, что хотите опубликовать в канале {i[0]}</b>
<blockquote>Или вы можете создать пост с помощью Искуственного интелекта(chat-gpt 4 и Dall-E).</blockquote>""",
                                             reply_markup=keyboards.ai(), parse_mode='HTML')
            await state.set_state(Form.create_post)


# State Create_post
@route.message(Form.create_post)
async def create_post(message: types.Message, state: FSMContext) -> None:
    post_text_list = message.text.split(' ')
    post_text = ' '.join(str(x) for x in post_text_list)
    print(channel_id_data.get(message.from_user.id)[0])
    m_id = message.message_id
    ch_id = channel_id_data.get(message.from_user.id)[0]

    # database.add_post_text(ch_id, post_text, m_id)

    data.add_post_text(ch_id, post_text, m_id)
    user_message_id[message.from_user.id] = m_id

    await state.clear()
    media_data = data.get_post_media(m_id)
    await message.answer(f"{data.get_post_text(m_id)}", reply_markup=keyboards.create_post_kb(media_data))


# Command_Handlers -> Update Post
@route.message(Command('update_post'))
@route.message(F.text.lower() == 'изменить пост')
async def update_post_message(message: types.Message, state: FSMContext):
    if data.get_all_chanels_name_from_user_id(message.from_user.id):
        await message.answer('''✍️ ИЗМЕНЕНИЕ ПОСТА
    
    Перешлите пост из вашего канала где бот является админом(если он не  является админом сделайте бота админом), который хотите отредактировать.''',
                             reply_markup=keyboards.back1())
        await state.set_state(Form.get_post_to_update)
    else:
        await message.answer('Чтобы подключить канал, сделайте bot его администратором, дав следующие права:\n\n✅ '
                             'Отправка сообщений\n✅ Удаление сообщений\n✅ Редактирование сообщений\n\nА затем перешлите '
                             'любое сообщение из канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.')
        await state.set_state(Form.wait_for_forward)


# State get_post_to_update
@route.message(Form.get_post_to_update)
async def get_post_to_update(message: types.Message, state: FSMContext):
    if message.forward_from_chat:
        try:
            forwarded_message = message.forward_from_message_id
            user_message_id[message.from_user.id] = forwarded_message
            data.update_message_id(message.message_id, forwarded_message)
            await message.bot.copy_message(chat_id=message.chat.id, from_chat_id=message.forward_from_chat.id,
                                           reply_markup=keyboards.update_post_kb(), message_id=forwarded_message)
        except Exception as e:
            print(Exception, e)


"""CallBack-Handler"""


# CallBack Handler
@route.callback_query(F.data == 'comments')
async def bell(callback: types.CallbackQuery) -> None:
    keyboards.comment_mode = not keyboards.comment_mode
    media_data = data.get_post_media(user_message_id[callback.from_user.id])
    await callback.message.edit_reply_markup(reply_markup=keyboards.create_post_kb(media_data))


@route.callback_query(F.data == 'secure')
async def bell(callback: types.CallbackQuery) -> None:
    keyboards.secure_mode = not keyboards.secure_mode
    media_data = data.get_post_media(user_message_id[callback.from_user.id])
    await callback.message.edit_reply_markup(reply_markup=keyboards.create_post_kb(media_data))


@route.callback_query(F.data == 'securev2')
async def bell(callback: types.CallbackQuery) -> None:
    keyboards.secure_mode = not keyboards.secure_mode
    await callback.message.edit_reply_markup(reply_markup=keyboards.update_post_kb())


@route.callback_query(F.data == 'bell')
async def bell(callback: types.CallbackQuery, state: FSMContext) -> None:
    keyboards.silent_mode = not keyboards.silent_mode
    media_data = data.get_post_media(user_message_id[callback.from_user.id])
    await callback.message.edit_reply_markup(reply_markup=keyboards.create_post_kb(media_data))


@route.callback_query(F.data == 'back')
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    if data.get_post_media(user_message_id[callback.from_user.id]) is None:
        await state.clear()
        media_data = data.get_post_media(user_message_id[callback.from_user.id])
        await callback.message.edit_text(f"{data.get_post_text(user_message_id[callback.from_user.id])}",
                                         reply_markup=keyboards.create_post_kb(media_data))

    elif data.get_post_media(user_message_id[callback.from_user.id]) is not None:
        media_data = data.get_post_media(user_message_id[callback.from_user.id])
        await state.clear()
        await callback.message.delete()
        await callback.message.answer_photo(media_data,
                                            caption=data.get_post_text(user_message_id[callback.from_user.id]),
                                            reply_markup=keyboards.create_post_kb(media_data))


@route.callback_query(F.data == 'back1')
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text('Действие отменено')


# CallBack Handler
@route.callback_query(F.data == 'delete_timer')
async def timer(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(''' ТАЙМЕР УДАЛЕНИЯ

Вы можете установить через какое время после выхода поста, он будет удалён.

Отправьте боту время, через которое нужно удалить пост либо выберите один из предложенных вариантов.
''', reply_markup=keyboards.buttons_timer_to_delete())


@route.callback_query(F.data.in_(['back_no', '5', '15', '30', '1hour', '2hour', '4hour', '6hour', '12hour',
                                  '24hour', '36hour', '48hour', '3day', '5day', '7day', '14day']))
async def timer(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    print(user_id)
    if callback.data == 'back_no':
        await callback.message.edit_text(text=f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb('нет'))
    elif callback.data == '5':
        user_timer_time[user_id] = 300
        print(user_timer_time[user_id])
        await callback.message.edit_text(text=f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb('5 минут'))
    elif callback.data == '15':
        user_timer_time[user_id] = 900
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='15 минут'))
    elif callback.data == '30':
        user_timer_time[user_id] = 1800
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='30 минут'))
    elif callback.data == '1hour':
        user_timer_time[user_id] = 3600
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='1 час'))
    elif callback.data == '2hour':
        user_timer_time[user_id] = 7200
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='2 часа'))
    elif callback.data == '4hour':
        user_timer_time[user_id] = 14400
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='4 часа'))
    elif callback.data == '6hour':
        user_timer_time[user_id] = 21600
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='6 часов'))
    elif callback.data == '12hour':
        user_timer_time[user_id] = 43200
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='12 часов'))
    elif callback.data == '24hour':
        user_timer_time[user_id] = 86400
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='24 часа'))
    elif callback.data == '36hour':
        user_timer_time[user_id] = 129600
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='36 часов'))
    elif callback.data == '48hour':
        user_timer_time[user_id] = 172800
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='48 часов'))
    elif callback.data == '3day':
        user_timer_time[user_id] = 259200
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='3 дня'))
    elif callback.data == '5day':
        user_timer_time[user_id] = 432000
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='5 дней'))
    elif callback.data == '7day':
        user_timer_time[user_id] = 604800
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='7 дней'))
    elif callback.data == '14day':
        user_timer_time[user_id] = 1209600
        await callback.message.edit_text(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb(edit_text='14 дней'))


@route.callback_query(F.data == 'post_delay')
async def post_delay(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.post_delay)
    await callback.message.edit_text(text=f''' ОТЛОЖИТЬ ПОСТ
Отправьте время выхода поста  в любом удобном формате, например:

<boa>18:30 04.08.2023
''', reply_markup=keyboards.back())


@route.message(Form.post_delay)
async def post_delay_state(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_post_delay[user_id] = message.text
    delay = user_post_delay[user_id]
    send_time = datetime.strptime(delay, '%H:%M %d.%m.%Y')
    await state.clear()
    await asyncio.create_task(delay_post(message, send_time))


@route.callback_query(F.data == 'update_text')
async def update_state_text(callback: types.CallbackQuery, state: FSMContext) -> None:
    if data.get_post_media(user_message_id[callback.from_user.id]):
        await callback.message.delete()
        await callback.message.answer('''Введите новый текст для поста''', reply_markup=keyboards.back())
        await state.set_state(Form.update_posts_text)
    else:
        await callback.message.edit_text('''Введите новый текст для поста''', reply_markup=keyboards.back())
        await state.set_state(Form.update_posts_text)


# State Update_Post_Text
@route.message(Form.update_posts_text)
async def update_post_text(message: types.Message, state: FSMContext):
    post_text_list = message.text.split(' ')
    post_text = ' '.join(str(x) for x in post_text_list)
    m_id = user_message_id[message.from_user.id]
    data.update_text(m_id, post_text)
    await state.clear()
    if data.get_post_media(m_id):
        media_data = data.get_post_media(m_id)
        await message.answer_photo(photo=data.get_post_media(m_id), caption=f"{post_text}",
                                   reply_markup=keyboards.create_post_kb(media_data))
    else:
        await update_title(message, post_text)


@route.callback_query(F.data == 'update_textv2')
async def update_state_text(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.message.answer('''Введите новый текст для поста''', reply_markup=keyboards.back_change())
    await state.set_state(Form.update_posts_textv2)


# State update_posts_textv2
@route.message(Form.update_posts_textv2)
async def update_post_text(message: types.Message, state: FSMContext):
    post_text_list = message.text.split(' ')
    post_text = ' '.join(str(x) for x in post_text_list)
    m_id = user_message_id[message.from_user.id]
    data.update_text(m_id, post_text)

    await state.clear()
    await message.answer(f"{post_text}", reply_markup=keyboards.update_post_kb())


@route.callback_query(F.data == 'add_media')
async def add_media_post(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.add_media_st)
    await callback.message.edit_text(
        '''<b>Чтобы прикрепить медиа к сообщению, отправьте фото, видео, GIF-анимацию, документ или видеосообщение весом 
не более 5 МБ.
<blockquote>Или вы можете создать фото с помощью Искуственного интелекта</blockquote></b>''',
        reply_markup=keyboards.photo_ai(), parse_mode='HTML')


@route.message(Form.add_media_st)
async def add_media_post_st(message: types.Message, state: FSMContext) -> None:
    if message.photo:
        media_data = data.get_post_media(user_message_id[message.from_user.id])

        await add_media_photo(message)

        await message.bot.send_photo(chat_id=message.chat.id, photo=message.photo[-1].file_id,
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.create_post_kb(media_data))
        m_id = user_message_id[message.from_user.id]
        data.update_media(m_id, message.photo[-1].file_id)
        await state.clear()
    elif message.video:
        await add_media_video(message)

        media_data = data.get_post_media(user_message_id[message.from_user.id])
        m_id = user_message_id[message.from_user.id]
        data.update_media(message.video.file_id, m_id)
        await message.bot.send_video(message.chat.id, message.video.file_id,
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.create_post_kb(media_data))
        await state.clear()
    else:
        await message.bot.send_message(message.chat.id, "Это не медиа-файл.")


@route.callback_query(F.data == 'add_mediav2')
async def add_media_post(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.add_media_stv2)
    await callback.message.edit_text(
        '''Чтобы прикрепить медиа к сообщению, отправьте фото, видео, GIF-анимацию, документ или видеосообщение весом 
        не более 5 МБ.''',
        reply_markup=keyboards.back_change())


@route.message(Form.add_media_stv2)
async def add_media_post_st(message: types.Message, state: FSMContext) -> None:
    if message.photo:
        media_data = data.get_post_media(user_message_id[message.from_user.id])
        await add_media_photo(message)
        await message.bot.send_photo(message.chat.id, message.photo[-1].file_id,
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.update_post_kb())
        m_id = user_message_id[message.from_user.id]
        data.update_media(m_id, message.photo[-1].file_id)
        await state.clear()
    elif message.video:
        media_data = data.get_post_media(user_message_id[message.from_user.id])
        m_id = user_message_id[message.from_user.id]
        data.update_media(message.video.file_id, m_id)
        await message.bot.send_video(message.chat.id, message.video.file_id,
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.update_post_kb())
        await state.clear()
    else:
        await message.bot.send_message(message.chat.id, "Это не медиа-файл.")


@route.callback_query(F.data == 'url_buttons')
async def get_text_for_button(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.get_url_button_text)
    if data.get_post_media(user_message_id[callback.from_user.id]):
        await callback.message.answer(f'''Отправьте текст для url-кнопки''', reply_markup=keyboards.back())
    else:
        await callback.message.delete()
        await callback.message.answer(f'''Отправьте текст для url-кнопки''', reply_markup=keyboards.back())


@route.message(Form.get_url_button_text)
async def get_text_for_button(message: types.Message, state: FSMContext) -> None:
    button_text = message.text
    print(message.message_id)
    data.update_url_name(user_message_id[message.from_user.id], button_text)
    print(user_message_id[message.from_user.id])

    await state.set_state(Form.get_url_button_url)
    await message.answer('Теперь введите URL для кнопки.', reply_markup=types.ForceReply())


@route.message(Form.get_url_button_url)
async def get_url_button(message: types.Message, state: FSMContext) -> None:
    button_url = message.text
    data.update_link(user_message_id[message.from_user.id], button_url)
    await state.clear()

    if data.get_post_media(user_message_id[message.from_user.id]) is None:
        media_data = data.get_post_media(user_message_id[message.from_user.id])
        print(message.message_id)
        print(user_message_id[message.from_user.id])
        await message.answer(f'''{data.get_post_text(user_message_id[message.from_user.id])}''',
                             reply_markup=keyboards.create_post_kb(media_data))
    elif data.get_post_media(user_message_id[message.from_user.id]) is not None:
        media_data = data.get_post_media(user_message_id[message.from_user.id])
        await message.bot.send_photo(message.chat.id, data.get_post_media(user_message_id[message.from_user.id]),
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.create_post_kb(media_data))


@route.callback_query(F.data == 'url_buttonv2')
async def get_text_for_button(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.get_url_button_text2)
    if data.get_post_media(user_message_id[callback.from_user.id]):
        print(user_message_id)
        await callback.message.delete()
        await callback.message.answer(f'''Отправьте текст для url-кнопки''', reply_markup=keyboards.back_change())
    else:
        await callback.message.edit_text(f'''Отправьте текст для url-кнопки''', reply_markup=keyboards.back_change())
        print(user_message_id[callback.message.from_user.id])


@route.message(Form.get_url_button_text2)
async def get_text_for_button(message: types.Message, state: FSMContext) -> None:
    button_text = message.text
    print(user_message_id)
    print(message.message_id)
    print(data.get_post())
    data.update_url_name(user_message_id[message.from_user.id], button_text)
    await state.set_state(Form.get_url_button_url2)
    await message.answer('Теперь введите URL для кнопки.', reply_markup=types.ForceReply())


@route.message(Form.get_url_button_url2)
async def get_url_button(message: types.Message, state: FSMContext) -> None:
    button_url = message.text
    data.update_link(user_message_id[message.from_user.id], button_url)
    await state.clear()

    if data.get_post_media(user_message_id[message.from_user.id]) is None:
        media_data = data.get_post_media(user_message_id[message.from_user.id])
        await message.answer(f'''{data.get_post_text(user_message_id[message.from_user.id])}''',
                             reply_markup=keyboards.update_post_kb())
    elif data.get_post_media(user_message_id[message.from_user.id]) is not None:
        media_data = data.get_post_media(user_message_id[message.from_user.id])
        await message.bot.send_photo(message.chat.id, data.get_post_media(user_message_id[message.from_user.id]),
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.update_post_kb())


@route.callback_query(F.data == 'return_to_main_menu')
async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.message.answer('''Создание поста отменено''')
    data.delete_post(user_message_id[callback.from_user.id])


@route.callback_query(F.data == 'return_to_main_menu2')
async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.message.answer('''Изменение поста отменено''')
    data.delete_post(user_message_id[callback.from_user.id])


@route.callback_query(F.data == 'next_l')
async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    user_id = callback.message.message_id
    chat_id = data.get_chanel_id(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer(f''' НАСТРОЙКИ ОТПРАВКИ
                
Пост готов к публикации в канале {data.get_chanel_name(callback.from_user.id)}.

Настройте его перед отправкой.''', reply_markup=keyboards.settings_post_kb('нет'))


@route.callback_query(F.data == 'post_publish')
async def post_publish(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        f'''Пост опубликован в канале {channel_id_data.get(callback.from_user.id)[1]}.''')
    m_id = user_message_id[callback.from_user.id]
    media_data = data.get_post_media(m_id)
    ch_id = channel_id_data.get(callback.from_user.id)
    button_data = data.get_post_url_name(m_id)
    print(data.get_post_url(m_id))
    if user_timer_time.keys():
        print(user_timer_time[callback.from_user.id])
        delay = user_timer_time[callback.from_user.id]
    else:
        print(user_timer_time)
        delay = 0
    # url = f"https://t.me/{database.get_chanel_name(889121031)}/{callback.message.message_id}"
    if media_data is None and button_data is None:
        message_m = await callback.message.bot.send_message(ch_id[0], f'''{data.get_post_text(m_id)}''',
                                                            disable_notification=keyboards.silent_mode)

        message_id = message_m.message_id
        data.update_message_id(m_id, message_id)

        print(data.get_post())
        print(message_id)
        if secure_mode:
            await callback.message.bot.pin_chat_message(chat_id=ch_id[0], message_id=message_id)
        if delay:
            await delete_post(callback.message, chat_id=ch_id[0], message_id=message_id, delay=delay)
        # await message_m.delete()
    elif media_data is not None and button_data is None:
        message_m = await callback.message.bot.send_photo(chat_id=ch_id[0], photo=data.get_post_media(m_id),
                                                          caption=f'''{data.get_post_text(m_id)}''',
                                                          disable_notification=keyboards.silent_mode)

        message_id = message_m.message_id
        data.update_message_id(m_id, message_id)
        if secure_mode:
            await callback.message.bot.pin_chat_message(chat_id=ch_id[0], message_id=message_id)
        if delay > 0:
            await delete_post(callback.message, chat_id=ch_id[0], message_id=message_id, delay=delay)
    elif media_data is None and button_data is not None:
        button = [[types.InlineKeyboardButton(text=button_data, url=data.get_post_url(m_id))]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        message_m = await callback.message.bot.send_message(ch_id[0], f'''{data.get_post_text(m_id)}''',
                                                            disable_notification=keyboards.silent_mode,
                                                            reply_markup=keyboard)
        message_id = message_m.message_id
        data.update_message_id(m_id, message_id)
        if secure_mode:
            await callback.message.bot.pin_chat_message(chat_id=ch_id[0], message_id=message_id)
        if delay > 0:
            await delete_post(callback.message, chat_id=ch_id[0], message_id=message_id, delay=delay)
    elif media_data is not None and button_data is not None:
        button = [[types.InlineKeyboardButton(text=button_data, url=data.get_post_url(m_id))]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        message_m = await callback.message.bot.send_photo(ch_id[0], data.get_post_media(m_id),
                                                          caption=data.get_post_text(m_id),
                                                          disable_notification=keyboards.silent_mode,
                                                          reply_markup=keyboard)
        message_id = message_m.message_id
        data.update_message_id(m_id, message_id)
        if secure_mode:
            await callback.message.bot.pin_chat_message(chat_id=ch_id[0], message_id=message_id)
        if delay > 0:
            await delete_post(callback.message, chat_id=ch_id[0], message_id=message_id, delay=delay)


@route.message(Form.wait_for_forward)
async def chanel_id(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        print(channel_id, data.get_chanel_id(user_id), user_id)
        if channel_id not in data.get_all_chanels_name_from_user_id(user_id):
            data.add_chanel_id(channel_id, user_id, message.forward_from_chat.title)
            print('wqe')
            await state.clear()
            channel_id_data[message.from_user.id] = [message.forward_from_chat.id, message.forward_from_chat.title]
            await process_chanel_command(message, state)
        elif channel_id == data.get_chanel_id(user_id):
            await state.clear()
            await process_chanel_command(message, state)
    else:
        await message.bot.send_message(message.chat.id, "Пожалуйста, перешлите сообщение из канала.")


@route.message(Form.wait_for_forward_2)
async def chanel_id(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        print(channel_id, data.get_chanel_id(user_id), user_id)
        if channel_id not in data.get_all_chanels_name_from_user_id(user_id):
            data.add_chanel_id(channel_id, user_id, message.forward_from_chat.title)
            print('wqe')
            await state.clear()
            await message.bot.send_message(message.chat.id, f"Канал успешно добавлен")
            await message.answer('''<b>💌 НАСТРОЙКИ

В этом разделе вы можете настроить работу с ботом, с отдельным каналом, а также добавить новый канал в Тест.</b>''',
                                 parse_mode='HTML',
                                 reply_markup=keyboards.settings(data.get_all_chanels_name_from_user_id(user_id)))

    else:
        await message.bot.send_message(message.chat.id, "Пожалуйста, перешлите сообщение из канала.")


@route.callback_query(F.data == 'unfasten_media')
async def unfasten_media(callback: types.CallbackQuery, state: FSMContext) -> None:
    media_data = data.delete_post_photo(user_message_id[callback.from_user.id])
    print(media_data)

    await callback.message.delete()
    await callback.message.answer(f'''{data.get_post_text(user_message_id[callback.from_user.id])}''',
                                  reply_markup=keyboards.create_post_kb(media_data))


@route.callback_query(F.data == 'back_change')
async def back_change(callback: types.CallbackQuery, state: FSMContext) -> None:
    if data.get_post_media(user_message_id[callback.from_user.id]) is None:
        media_data = data.get_post_media(user_message_id[callback.from_user.id])
        await callback.message.answer(f'''{data.get_post_text(user_message_id[callback.from_user.id])}''',
                                      reply_markup=keyboards.update_post_kb())
    elif data.get_post_media(user_message_id[callback.from_user.id]) is not None:
        media_data = data.get_post_media(user_message_id[callback.from_user.id])
        await callback.message.bot.send_photo(callback.message.chat.id,
                                              data.get_post_media(user_message_id[callback.from_user.id]),
                                              caption=data.get_post_text(user_message_id[callback.from_user.id]),
                                              reply_markup=keyboards.update_post_kb())


@route.callback_query(F.data == 'save_changes')
async def save_changes(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        f'''Пост успешно изменен {channel_id_data.get(callback.from_user.id)[1]}.''')
    ch_id = channel_id_data.get(callback.from_user.id)[0]
    m_id = user_message_id[callback.from_user.id]
    print(m_id)
    media_data = data.get_post_media(m_id)
    button_data = data.get_post_url_name(m_id)
    if media_data is None and button_data is None:
        await callback.message.bot.edit_message_text(chat_id=ch_id, message_id=m_id,
                                                     text=f'''{data.get_post_text(m_id)}''')
    elif media_data is not None and button_data is None:
        await callback.message.bot.delete_message(chat_id=ch_id, message_id=m_id)
        await callback.message.bot.send_photo(chat_id=ch_id, photo=data.get_post_media(m_id),
                                              caption=f'''{data.get_post_text(m_id)}''',
                                              disable_notification=keyboards.silent_mode)
    elif media_data is None and button_data is not None:
        button = [[types.InlineKeyboardButton(text=button_data, url=data.get_post_url(m_id))]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.bot.edit_message_text(ch_id, f'''{data.get_post_text(m_id)}''', reply_markup=keyboard)
    elif media_data is not None and button_data is not None:
        button = [[types.InlineKeyboardButton(text=button_data, url=data.get_post_url(m_id))]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.bot.delete_message(chat_id=ch_id, message_id=m_id)
        await callback.message.bot.send_photo(ch_id, data.get_post_media(m_id), caption=data.get_post_text(m_id),
                                              reply_markup=keyboard)


@route.message(Command('/templates'))
@route.message(F.text.lower() == 'шаблоны')
async def templates(message: types.Message, state: FSMContext) -> None:
    print(data.get_all_chanels_name_from_user_id(message.from_user.id))
    if data.get_all_chanels_name_from_user_id(message.from_user.id):
        await message.answer('''🏷 ШАБЛОНЫ
Сохраняйте заготовки для постов или рекламных креативов. Для шаблонов вы можете заменять ссылки по одному нажатию, а затем пересылать.
        ''', reply_markup=keyboards.templates_kb_ch(data.get_all_chanels_name_from_user_id(message.from_user.id)))
    else:
        await message.answer('Сначала добавьте канал')


user_temp_ch_id = {}


async def create_template_func(callback):
    for i in data.get_all_chanels_name_ch_id_from_user_id(callback.from_user.id):
        user_template_value[callback.from_user.id] = callback.data.split('_')[1]
        user_temp_ch_id[callback.from_user.id] = [i[1], i[0]]
        if i[0] == callback.data.split('_')[1]:
            await callback.message.edit_text(f'''🏷 ШАБЛОНЫ

Сохраняйте заготовки для постов или рекламных креативов. Для шаблонов вы можете заменять ссылки по одному нажатию, а затем пересылать.

Выберите шаблон для канала {i[0]} или создайте новый.''', reply_markup=keyboards.template_kb(
                data.get_all_template_post(i[1])))


@route.callback_query(F.data.startswith('template_'))
async def template(callback: types.CallbackQuery, state: FSMContext) -> None:
    await create_template_func(callback)


user_temp_post_publish = {}


@route.callback_query(F.data.startswith('postemp_'))
async def template(callback: types.CallbackQuery, state: FSMContext) -> None:
    user_temp_post_publish[callback.from_user.id] = callback.data.split('_')[1]
    for i in data.get_all_template_post(user_temp_ch_id.get(callback.from_user.id)[0]):
        print(i)
        if i[2] == callback.data.split('_')[1]:
            await callback.message.delete()

            await callback.message.answer('''Выберите, что сделать с шаблоном.''',
                                          reply_markup=keyboards.template_kb_edit())


@route.callback_query(F.data.in_(['create_template', 'back_to_create_tamp', 'delete_temp_post', 'post_temp_publish']))
async def create_template(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data == 'create_template':
        await state.set_state(Form.templates)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='Назад', callback_data='back_to_create_tamp')]])
        await callback.message.edit_text('Отправьте боту шаблон, который вы хотите сохранить.', reply_markup=keyboard)
    elif callback.data == 'back_to_create_tamp':
        user_value = user_template_value.get(callback.from_user.id)
        for i in data.get_all_chanels_name_from_user_id(callback.from_user.id):
            if i[0] == user_value:
                print(data.get_all_template_post(user_temp_ch_id.get(callback.from_user.id)[0]))
                await callback.message.edit_text(f'''🏷 ШАБЛОНЫ

Сохраняйте заготовки для постов или рекламных креативов. Для шаблонов вы можете заменять ссылки по одному нажатию, а затем пересылать.

Выберите шаблон для канала {i[0]} или создайте новый.''', reply_markup=keyboards.template_kb(
                    data.get_all_template_post(user_temp_ch_id.get(callback.from_user.id)[0])))
    elif callback.data == 'delete_temp_post':
        user_value = user_template_value.get(callback.from_user.id)
        for i in data.get_all_chanels_name_from_user_id(callback.from_user.id):
            if i[0] == user_value:
                for j in data.get_all_template_post(channel_id_data.get(callback.from_user.id)[0]):
                    print(j, j[2], j[3], j[4], j[5])
                    print(callback.data.split('_')[1])
                    if j[2]:
                        data.delete_template_post(user_temp_ch_id.get(callback.from_user.id)[0], j[2])
                        await callback.message.edit_text(f'''Шаблон удален.''')
            else:
                await callback.message.edit_text(f'''Шаблон не удален.''')
    elif callback.data == 'post_temp_publish':
        for i in data.get_all_template_post(channel_id_data.get(callback.from_user.id)[0]):
            print(i, i[2], i[3], i[4], i[5])
            if i[2] == user_temp_post_publish.get(callback.from_user.id):
                if i[3] is not None and i[4] is not None and i[5] is not None:
                    buttons = [[types.InlineKeyboardButton(text=f"{i[4]}", url=i[5])]]
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
                    await callback.message.answer('''Отправляю пост...''')
                    media = i[3]
                    await callback.message.bot.send_photo(chat_id=user_temp_ch_id.get(callback.from_user.id)[0],
                                                          photo=media, caption=i[2],
                                                          reply_markup=keyboard)
                elif i[3] is None and i[4] is not None:
                    await callback.message.answer('''Отправляю пост...''')
                    buttons = [[types.InlineKeyboardButton(text=f"{i[4]}", url=i[5])]]
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
                    await callback.message.bot.send_message(chat_id=user_temp_ch_id.get(callback.from_user.id)[0],
                                                            text=i[2], reply_markup=keyboard)
                elif i[3] is not None and i[4] is None:
                    await callback.message.answer('''Отправляю пост...''')
                    media = i[3]
                    await callback.message.bot.send_photo(chat_id=user_temp_ch_id.get(callback.from_user.id)[0],
                                                          photo=media, caption=i[2])
                elif i[3] is None and i[4] is None:
                    await callback.message.answer('''Отправляю пост...''')
                    media = None
                    print(user_temp_ch_id.get(callback.from_user.id))
                    print(user_post_temp.get(callback.from_user.id))
                    print(media)
                    # if len(user_post_temp.get(callback.from_user.id)) > 2:
                    await callback.message.bot.send_message(chat_id=user_temp_ch_id.get(callback.from_user.id)[0],
                                                            text=i[2])


user_post_temp = {}


@route.message(Form.templates)
async def templates(message: types.Message, state: FSMContext) -> None:
    if message.forward_from_chat or message.forward_from:
        forwarded_message = message.reply_to_message
        print(user_message_id)
        print(forwarded_message)
        if isinstance(message.reply_markup, types.InlineKeyboardMarkup):
            data.add_template(user_temp_ch_id.get(message.from_user.id)[0], message.text or message.caption)
            data.update_template_media(ch_id=user_temp_ch_id.get(message.from_user.id)[0],
                                       media=message.photo[-1].file_id or None)
            data.update_template_link(ch_id=user_temp_ch_id.get(message.from_user.id)[0],
                                      link=message.reply_markup.inline_keyboard[0][0].url)
            data.update_template_url_name(user_temp_ch_id.get(message.from_user.id)[0],
                                          message.reply_markup.inline_keyboard[0][0].text)
            user_post_temp[message.from_user.id] = [message.text or message.caption, message.photo,
                                                    message.reply_markup.inline_keyboard[0][0].url,
                                                    message.reply_markup.inline_keyboard[0][0].text]
            print(user_post_temp[message.from_user.id])
            user_message_id[message.from_user.id] = forwarded_message
            await message.bot.copy_message(chat_id=message.chat.id, from_chat_id=message.forward_from_chat.id,
                                           reply_markup=keyboards.add_template_kb(
                                               text=message.reply_markup.inline_keyboard[0][0].text,
                                               url=message.reply_markup.inline_keyboard[0][0].url),
                                           message_id=message.forward_from_message_id)
        else:
            user_post_temp[message.from_user.id] = [message.text or message.caption, message.photo]
            print(user_post_temp[message.from_user.id])
            user_message_id[message.from_user.id] = forwarded_message
            await message.bot.copy_message(chat_id=message.chat.id, from_chat_id=message.forward_from_chat.id,
                                           message_id=message.forward_from_message_id,
                                           reply_markup=keyboards.add_template_kb())
        data.add_template(user_temp_ch_id.get(message.from_user.id)[0], message.text or message.caption)
        data.update_template_media(user_temp_ch_id.get(message.from_user.id)[0], message.photo[-1].file_id or None)
        print(data.get_all_template_post(user_temp_ch_id.get(message.from_user.id)[0]))
    # except Exception as e:
    #     print(Exception, e)
    #     await message.answer('Не удалось переслать пост. Попробуйте еще раз.')


async def add_template_menu(message, text, url_text=None, url=None, user_id=None):
    print(user_post_temp.get(user_id))
    if user_post_temp.get(user_id)[1]:
        await message.delete()
        media = (user_post_temp.get(user_id)[1])[-1].file_id
        await message.answer_photo(photo=media, caption=text,
                                   reply_markup=keyboards.add_template_kb(url_text, url, media))
    else:
        media = None
        print(media)
        if len(user_post_temp.get(user_id)) > 2:
            await message.answer(text, reply_markup=keyboards.add_template_kb(url_text, url, media))
        else:
            await message.edit_text(text, reply_markup=keyboards.add_template_kb(url_text, url, media))


@route.callback_query(F.data.in_(['change_description_template', 'add_media_template',
                                  'url_buttons_template', 'next_template', 'unfasten_media_template',
                                  'back_temp_post', 'back_to_templates']))
async def template(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data == 'change_description_template':
        if user_post_temp.get(callback.from_user.id)[1]:
            await callback.message.delete()
            await callback.message.answer('''Введите новый текст для поста''', reply_markup=keyboards.back_temp_post())
            await state.set_state(Form.description_template)
        else:
            await callback.message.edit_text('''Введите новый текст для поста''',
                                             reply_markup=keyboards.back_temp_post())
            await state.set_state(Form.description_template)
    elif callback.data == 'add_media_template':
        await state.set_state(Form.media_template)
        if user_post_temp.get(callback.from_user.id)[1]:
            await callback.message.delete()
            await callback.message.answer(
                '''Чтобы прикрепить медиа к сообщению, отправьте фото, видео, GIF-анимацию, документ или видеосообщение весом 
            не более 5 МБ.''',
                reply_markup=keyboards.back_temp_post())
        else:
            await callback.message.edit_text(
                '''Чтобы прикрепить медиа к сообщению, отправьте фото, видео, GIF-анимацию, документ или видеосообщение весом 
            не более 5 МБ.''',
                reply_markup=keyboards.back_temp_post())
    elif callback.data == 'back_temp_post':
        await state.clear()
        if len(user_post_temp.get(callback.from_user.id)) > 2:
            await add_template_menu(text=user_post_temp.get(callback.from_user.id)[0], message=callback.message,
                                    url_text=user_post_temp.get(callback.from_user.id)[3],
                                    url=user_post_temp.get(callback.from_user.id)[2], user_id=callback.from_user.id)
        else:
            await add_template_menu(text=user_post_temp.get(callback.from_user.id)[0], message=callback.message,
                                    user_id=callback.from_user.id)
    elif callback.data == 'unfasten_media_template':
        user_post_temp.get(callback.from_user.id).pop(1)
        user_post_temp.get(callback.from_user.id).insert(1, None)
        print(user_post_temp.get(callback.from_user.id))
        if len(user_post_temp.get(callback.from_user.id)) > 2:
            await add_template_menu(text=user_post_temp.get(callback.from_user.id)[0], message=callback.message,
                                    url_text=user_post_temp.get(callback.from_user.id)[3],
                                    url=user_post_temp.get(callback.from_user.id)[2], user_id=callback.from_user.id)
        else:
            await add_template_menu(text=user_post_temp.get(callback.from_user.id)[0], message=callback.message,
                                    user_id=callback.from_user.id)
    elif callback.data == 'url_buttons_template':
        await state.set_state(Form.url_buttons_template)
        if user_post_temp.get(callback.from_user.id)[1]:
            await callback.message.delete()
            await callback.message.answer(f'''Отправьте url для url-кнопки''', reply_markup=keyboards.back_temp_post())
        else:
            await callback.message.edit_text(f'''Отправьте url для url-кнопки''',
                                             reply_markup=keyboards.back_temp_post())
    elif callback.data == 'next_template':
        print(data.get_all_template_post(channel_id_data.get(callback.from_user.id)[0]))
        await callback.message.delete()
        user_value = user_template_value.get(callback.from_user.id)
        for i in data.get_all_chanels_name_from_user_id(callback.from_user.id):
            if i[0] == user_value:
                await callback.message.answer(f'''🏷 ШАБЛОНЫ

Сохраняйте заготовки для постов или рекламных креативов. Для шаблонов вы можете заменять ссылки по одному нажатию, а затем пересылать.

Выберите шаблон для канала {i[0]} или создайте новый.''', reply_markup=keyboards.template_kb(
                    data.get_all_template_post(user_temp_ch_id.get(callback.from_user.id)[0])))
    elif callback.data == 'back_to_templates':
        if data.get_all_chanels_name_from_user_id(callback.from_user.id):
            await callback.message.edit_text('''🏷 ШАБЛОНЫ
Сохраняйте заготовки для постов или рекламных креативов. Для шаблонов вы можете заменять ссылки по одному нажатию, а затем пересылать.
                ''', reply_markup=keyboards.templates_kb_ch(
                data.get_all_chanels_name_from_user_id(callback.from_user.id)))


# State Update_Post_Text
@route.message(Form.description_template)
async def update_post_text(message: types.Message, state: FSMContext) -> None:
    post_text_list = message.text.split(' ')
    post_text = ' '.join(str(x) for x in post_text_list)
    print(post_text)
    ch_id = channel_id_data.get(message.from_user.id)[0]
    print(ch_id)
    user_post_temp.get(message.from_user.id)[0] = post_text
    data.update_template_text(ch_id, post_text)
    await state.clear()
    if len(user_post_temp.get(message.from_user.id)) > 2:
        await add_template_menu(text=post_text, message=message, url_text=user_post_temp.get(message.from_user.id)[3],
                                url=user_post_temp.get(message.from_user.id)[2], user_id=message.from_user.id)
    else:
        await add_template_menu(text=post_text, message=message, user_id=message.from_user.id)


@route.message(Form.media_template)
async def add_media_post_st(message: types.Message, state: FSMContext) -> None:
    if message.photo:
        ch_id = channel_id_data.get(message.from_user.id)[0]
        user_post_temp.get(message.from_user.id).insert(1, message.photo)
        user_post_temp.get(message.from_user.id).remove(None)
        print(user_post_temp.get(message.from_user.id))
        if len(user_post_temp.get(message.from_user.id)) > 2:
            await add_template_menu(text=user_post_temp.get(message.from_user.id)[0], message=message,
                                    url_text=user_post_temp.get(message.from_user.id)[3],
                                    url=user_post_temp.get(message.from_user.id)[2], user_id=message.from_user.id)
        else:
            await add_template_menu(text=user_post_temp.get(message.from_user.id)[0], message=message,
                                    user_id=message.from_user.id)

        data.update_template_media(ch_id, message.photo[-1].file_id)
        await state.clear()
    elif message.video:
        await add_media_video(message)

        media_data = data.get_post_media(user_message_id[message.from_user.id])
        m_id = user_message_id[message.from_user.id]
        data.update_media(message.video.file_id, m_id)
        await message.bot.send_video(message.chat.id, message.video.file_id,
                                     caption=data.get_post_text(user_message_id[message.from_user.id]),
                                     reply_markup=keyboards.create_post_kb(media_data))
        await state.clear()
    else:
        await message.bot.send_message(message.chat.id, "Это не медиа-файл.")


@route.message(Form.url_buttons_template)
async def get_text_for_button(message: types.Message, state: FSMContext) -> None:
    button_text = message.text
    if len(user_post_temp.get(message.from_user.id)) > 2:
        user_post_temp.get(message.from_user.id)[2] = button_text
    else:
        user_post_temp.get(message.from_user.id).insert(2, button_text)
    print(message.message_id)
    data.update_template_link(data.get_chanel_id(message.from_user.id), button_text)
    print(user_message_id[message.from_user.id])

    await state.set_state(Form.url_buttons_template_url)
    await message.answer('Теперь введите текст для кнопки.', reply_markup=types.ForceReply())


@route.message(Form.url_buttons_template_url)
async def get_url_button(message: types.Message, state: FSMContext) -> None:
    button_text = message.text
    print(user_post_temp.get(message.from_user.id))
    print(button_text)
    if len(user_post_temp.get(message.from_user.id)) > 3:
        user_post_temp.get(message.from_user.id)[3] = button_text
    else:
        user_post_temp.get(message.from_user.id).append(button_text)
    data.update_template_url_name(user_message_id[message.from_user.id], button_text)
    print(user_post_temp.get(message.from_user.id))
    await state.clear()
    await add_template_menu(text=user_post_temp.get(message.from_user.id)[0], message=message,
                            url_text=user_post_temp.get(message.from_user.id)[3],
                            url=user_post_temp.get(message.from_user.id)[2], user_id=message.from_user.id)


@route.callback_query(F.data.startswith('date_'))
async def button_handler(callback: types.CallbackQuery):
    date = datetime.strptime(callback.data.split("_")[1], '%Y-%m-%d')
    message_text = f"<b>🗓 КОНТЕНТ-ПЛАН\n\nНа {date.strftime('%d %B')} в канале qwert запланирован  пост.</b>"
    message_text2 = f"<b>🗓 КОНТЕНТ-ПЛАН\n\nНа {date.strftime('%d %B')} в канале qwert не запланирован  пост.</b>"
    keyboard = keyboards.create_date_keyboard(date, data=data.get_all_content())
    print(date)
    if data.get_all_content():
        for i in data.get_all_content():
            sheduled_post[i[2][:10]] = i[1]
            print(sheduled_post, 123, )
            keyboard = keyboards.create_date_keyboard(date, data=data.get_all_content())
            schedul = sheduled_post.get(date.strftime('%Y-%m-%d'))

            await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode='HTML')

    else:
        keyboard = keyboards.create_date_keyboard(date)
        await callback.message.edit_text(message_text2, reply_markup=keyboard, parse_mode='HTML')
    # await callback.message.edit_text(message_text, reply_markup=keyboard, parse_mode='HTML')
    # Получаем дату из callback_data


message_sent = True


@route.message(Command('/content'))
@route.message(F.text.lower() == 'контент план')
async def content_p(message: types.Message) -> None:
    global message_sent
    date = datetime.now()
    keyboard = keyboards.create_date_keyboard(datetime.now().date(), data=data.get_all_content())
    if data.get_all_chanels_name_from_user_id(message.from_user.id):
        print(data.get_all_content())
        if data.get_all_content():
            for i in data.get_all_content():
                print(data.get_all_content())
                sheduled_post[i[2][:10]] = i[1]
                schedul = sheduled_post.get(date.strftime('%Y-%m-%d'))
                keyboard = keyboards.create_date_keyboard(datetime.now().date(), data=data.get_all_content())
                if schedul:
                    if message_sent:
                        message_text = f"<b>🗓 КОНТЕНТ-ПЛАН\n\nНа {date.strftime('%d %B')} в канале {data.get_chanel_name(message.from_user.id)} запланирован  пост.</b>"
                        await message.answer(message_text, reply_markup=keyboard, parse_mode='HTML')
                        message_sent = False
        else:
            print(data.get_all_content())
            message_text = f"<b>🗓 КОНТЕНТ-ПЛАН\n\nНа {date.strftime('%d %B')} в канале {data.get_chanel_name(message.from_user.id)} не запланирован  пост.</b>"
            await message.answer(message_text, reply_markup=keyboard, parse_mode='HTML')
    else:

        await message.answer('Контент план пока не запланирован', parse_mode='HTML')


delete_chanel_ = {}


@route.callback_query(F.data.startswith('addchannel_'))
async def edit_chanel_call(callback: types.CallbackQuery):
    await callback.answer()
    add_chanel_id = callback.data.split("_")[1]
    delete_chanel_[callback.from_user.id] = add_chanel_id
    for i in data.get_all_chanels_name_from_user_id(callback.from_user.id):
        print(callback.data.split("_")[1])
        if i[0] == callback.data.split("_")[1]:
            await callback.message.edit_text(text=f'''{add_chanel_id}''', reply_markup=keyboards.edit_chanel())


@route.callback_query(F.data.in_(['add_channel', 'back_settings', 'delete_chanel', 'back_to_settings']))
async def add_chanel_call(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'add_channel':
        await state.set_state(Form.wait_for_forward_2)
        await callback.message.edit_text('''<b>Чтобы подключить канал, сделайте @posted его администратором, дав следующие права:
    
    ✅ Отправка сообщений
    ✅ Удаление сообщений
    ✅ Редактирование сообщений
    
    А затем перешлите любое сообщение из канала в диалог с ботом либо отправьте публичную ссылку на ваш канал.</b>''',
                                         parse_mode='HTML', reply_markup=keyboards.back_to_settings())
    elif callback.data == 'back_settings':
        await callback.message.edit_text('''<b>💌 НАСТРОЙКИ

В этом разделе вы можете настроить работу с ботом, с отдельным каналом, а также добавить новый канал в Тест.</b>''',
                                         parse_mode='HTML', reply_markup=keyboards.settings(
                data.get_all_chanels_name_from_user_id(callback.from_user.id)))
    elif callback.data == 'delete_chanel':
        await state.set_state(Form.wait_to_delete)
        await callback.message.edit_text('''<b>Чтобы удалить канал, перешлите любое сообщение из канала.</b>''',
                                         parse_mode='HTML', reply_markup=keyboards.back_to_settings())
    elif callback.data == 'back_to_settings':
        await callback.message.edit_text('''<b>💌 НАСТРОЙКИ

В этом разделе вы можете настроить работу с ботом, с отдельным каналом, а также добавить новый канал в Тест.</b>''',
                                         parse_mode='HTML', reply_markup=keyboards.settings(
                data.get_all_chanels_name_from_user_id(callback.from_user.id)))


@route.message(Form.wait_to_delete)
async def delete_chanel(message: types.Message, state: FSMContext):
    if message.forward_from_chat:
        for i in data.get_all_chanels_name_ch_id_from_user_id(message.from_user.id):
            print(i[0][0])
            if message.forward_from_chat.id == i[1]:
                data.delete_chanel(message.forward_from_chat.id)
                await state.clear()
                await message.answer('Канал удален')
                await message.answer('''<b>💌 НАСТРОЙКИ

                В этом разделе вы можете настроить работу с ботом, с отдельным каналом, а также добавить новый канал в Тест.</b>''',
                                     parse_mode='HTML', reply_markup=keyboards.settings(
                        data.get_all_chanels_name_from_user_id(message.from_user.id)))
                delete_chanel_.clear()
        else:
            print(data.get_all_chanels_id_from_user_id(message.from_user.id)[0])
            print(message.forward_from_chat.id)
            await message.answer('Вы не можете удалить этот канал', reply_markup=keyboards.settings(
                data.get_all_chanels_name_from_user_id(message.from_user.id)))
    else:
        await message.answer('Пожалуйста, перешлите сообщение из канала.')


@route.message(Command('/settings'))
@route.message(F.text.lower() == 'настройки')
async def settings_p(message: types.Message) -> None:
    await message.answer('''<b>💌 НАСТРОЙКИ

В этом разделе вы можете настроить работу с ботом, с отдельным каналом, а также добавить новый канал в Тест.</b>''',
                         parse_mode='HTML',
                         reply_markup=keyboards.settings(data.get_all_chanels_name_from_user_id(message.from_user.id)))


async def wh():
    while True:
        time.sleep(15)
        print(channel_id_data)


user_data_ai = {}


# some func
async def separetor(text, ran):
    posts_list = []

    # Разделить строку на отдельные посты
    for post in text.split('\n\n'):
        # Найти номер и текст поста
        for j in range(1, int(ran) + 1):
            post_parts = post.split(f"Пост {j}.")
            if len(post_parts) == 2:  # Проверяем, что удалось разделить на две части
                post_number, post_text = post_parts
                posts_list.append((post_number.strip(), post_text.strip()))
    return posts_list


# handlers
@route.callback_query(F.data == 'delay_ai')
async def delay_ai(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text('<b>Сколько постов создать?</b>', parse_mode='HTML')
    await state.set_state(Form.delay_ai)


@route.message(Form.delay_ai)
async def delay_ai(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_data_ai[user_id] = [message.text]
    await message.answer('''<b>Какая тема поста?</b>''', parse_mode='HTML')
    await state.set_state(Form.delay_ai_theme)


@route.message(Form.delay_ai_theme)
async def delay_ai_theme(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_data_ai[user_id].append(message.text)
    print(user_data_ai)
    print(user_data_ai)
    await message.answer('''<b>C каким интервалом отправлять пост?</b>
<blockquote>В формате "часы:минуты:секунды"</blockquote>''', parse_mode='HTML')
    await state.set_state(Form.delay_ai_time)


def check_time_format(time_str):
    # Регулярное выражение для проверки формата времени
    pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):([0-5]?[0-9]):([0-5]?[0-9])$')
    if re.match(pattern, time_str):
        return True
    else:
        return False


user_data_photo_ai = {}


@route.message(Form.delay_ai_time)
async def delay_ai_time(message: types.Message, state: FSMContext) -> None:
    if message.text:
        user_id = message.from_user.id
        user_data_ai[user_id].append(message.text)
        print(user_data_ai, user_data_ai.get(user_id)[2])
        check_time = check_time_format(message.text)
        print(check_time)
        m_id = message.message_id

        if check_time:
            waiting = await message.answer("Генерирую посты ...")
            try:
                # print(robot.text_to_picture_for_post(promt=user_data_ai.get(user_id)[1],
                #                                      count=int(user_data_ai.get(user_id)[0])))
                response = robot.text_to_picture_for_post(promt=user_data_ai.get(user_id)[1],
                                                          count=int(user_data_ai.get(user_id)[0]), user_id=user_id)
                print(response)
                gpt_answer = robot.chat_gpt_for_post(user_id=user_id, message=user_data_ai.get(user_id)[1],
                                                     count=user_data_ai.get(user_id)[0])
                await waiting.delete()
                message_to_post = await separetor(gpt_answer, user_data_ai.get(user_id)[0])
                user_data_ai[user_id].append(message.text)
                ch_id = channel_id_data.get(message.from_user.id)[0]
                for i in message_to_post:
                    # user_message_id[message.from_user.id] = [m_id + 1 for _ in range(int(i[0]))]
                    data.add_post_text(ch_id, i[1], m_id)
                    # print(user_message_id[message.from_user.id])
                media_data = data.get_post_media(m_id)
                # await message.answer_photo(caption=f'''{message_to_post[0][1]}''', photo=response.data[0].url,
                #                            parse_mode='Markdown',
                #                            reply_markup=keyboards.post_ai(response.data[0].url))
                await message.answer(f'''{message_to_post[0][1]}  
[ссылка на фото](%s)''' % response[0], parse_mode='Markdown',
                                     reply_markup=keyboards.post_ai(response[0]))
                user_data_ai[user_id].append(message_to_post)
                ai_photo = response
                user_data_ai[user_id].append(ai_photo)
                print(user_data_ai)
                await state.clear()
            except:
                gpt_answer = robot.chat_gpt_for_post(user_id=user_id, message=user_data_ai.get(user_id)[1],
                                                     count=user_data_ai.get(user_id)[0])
                print(gpt_answer)
                message_to_post = await separetor(gpt_answer, user_data_ai.get(user_id)[0])
                print(message_to_post)
                user_data_ai[user_id].append(message.text)
                ch_id = channel_id_data.get(message.from_user.id)[0]
                for i in message_to_post:
                    data.add_post_text(ch_id, i[1], m_id)
                    print(data.get_all_posts())
                media_data = data.get_post_media(m_id)
                await message.answer('''<b>Неудалось сгенерировать фото</b>''', parse_mode='HTML')

                await message.answer(f'''{message_to_post[0][1]}''', parse_mode='Markdown',
                                     reply_markup=keyboards.post_ai())
                user_data_ai[user_id].append(message_to_post)
                print(user_data_ai)
                await state.clear()
    else:
        await message.answer('''<b>Неверный формат времени</b>''', parse_mode='HTML')


user_counting = {}


@route.callback_query(F.data.in_(['further_ai', 'return_ai', 'update_textv3', 'back_post_ai', 'delete_mediav3']))
async def publish_posts_ai(callback: types.CallbackQuery, state: FSMContext) -> None:
    user_data = user_data_ai.get(callback.from_user.id)
    message_to_post = user_data[4]
    counting = await state.get_state()  # Получаем значение counting из состояния
    photo = user_data[5]
    if counting is None:
        counting = 0  # Устанавливаем начальное значение, если counting еще не было установлено
    else:
        counting = int(counting)  # Преобразуем значение counting в int

    print(message_to_post, counting)

    if callback.data == 'further_ai':
        if len(message_to_post) > counting:
            print(counting)
            counting += 1
            await state.set_state(str(counting))
            user_counting[callback.from_user.id] = counting
            if photo[counting]:
                await callback.message.edit_text(
                    f'''{message_to_post[counting][1]} [cсылка на фото](%s)''' % photo[counting],
                    reply_markup=keyboards.post_ai(photo[counting]), parse_mode='Markdown')
            else:
                await callback.message.edit_text(f'''{message_to_post[counting][1]}''',
                                                 reply_markup=keyboards.post_ai(), parse_mode='Markdown')
    elif callback.data == 'return_ai':
        print(counting)
        if counting > 0:
            counting -= 1
            await state.set_state(str(counting))
            user_counting[callback.from_user.id] = counting
            if photo[counting]:
                await callback.message.edit_text(
                    f'''{message_to_post[counting][1]} [cсылка на фото](%s)''' % photo[counting],
                    reply_markup=keyboards.post_ai(photo[counting]), parse_mode='Markdown')
            else:
                await callback.message.edit_text(f'''{message_to_post[counting][1]}''',
                                                 reply_markup=keyboards.post_ai(), parse_mode='Markdown')
    elif callback.data == 'back_post_ai':
        if photo[counting]:
            await callback.message.edit_text(
                f'''{message_to_post[counting][1]} [cсылка на фото](%s)''' % photo[counting],
                reply_markup=keyboards.post_ai(photo[counting]), parse_mode='Markdown')
        else:
            await callback.message.edit_text(f'''{message_to_post[counting][1]}''',
                                             reply_markup=keyboards.post_ai(), parse_mode='Markdown')

    elif callback.data == 'update_textv3':
        await callback.message.edit_text('''Отправьте новый текст для поста''', reply_markup=keyboards.back_post_ai())
        await state.set_state(Form.COUNTING_STATE)
    elif callback.data == 'delete_mediav3':
        if photo:
            photo.pop(user_counting[callback.from_user.id])
            photo.insert(user_counting[callback.from_user.id], None)
            print(photo)
            await callback.message.edit_text(f'''{message_to_post[counting][1]} ''',
                                             reply_markup=keyboards.post_ai(photo[counting]), parse_mode='Markdown')
    # Сохраняем значение counting в состоянии, преобразуя его обратно в строку


@route.message(Form.COUNTING_STATE)
async def update_counting_state(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_data_ai[user_id][4][user_counting[user_id]] = ['""', message.text]
    photo = user_data_ai.get(user_id)[5]
    if photo[user_counting[user_id]]:
        await message.answer(f'{message.text} [cсылка на фото](%s)' % photo[user_counting[user_id]],
                             parse_mode='Markdown', reply_markup=keyboards.post_ai(photo[user_counting[user_id]]))
        await state.clear()
    else:
        await message.answer(f'{message.text}', parse_mode='Markdown',
                             reply_markup=keyboards.post_ai(photo[user_counting[user_id]]))
        await state.clear()


@route.callback_query(F.data.in_(['publish_posts_ai']))
async def publish_posts_ai(callback: types.CallbackQuery, state: FSMContext) -> None:
    ch_id = channel_id_data.get(callback.from_user.id)[0]
    if callback.data == 'publish_posts_ai':
        time_str = user_data_ai.get(callback.from_user.id)[3]
        hours, minutes, seconds = map(int, time_str.split(":"))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        user_data = user_data_ai.get(callback.from_user.id)[4]
        photo = user_data_ai.get(callback.from_user.id)[5]
        user_id = callback.from_user.id
        await callback.message.edit_text(f'''Отправляю посты...''')
        for i in range(len(user_data)):
            if photo[i]:
                await asyncio.sleep(total_seconds)
                await callback.message.bot.send_message(ch_id, f'{user_data[i][1]} [cсылка на фото](%s)' % photo[i],
                                                        parse_mode='Markdown')
            else:
                await asyncio.sleep(total_seconds)
                await callback.message.bot.send_message(ch_id, f'''{user_data[i][1]}''', parse_mode='Markdown')


@route.message(Command('/help'))
@route.message(F.text.lower() == 'помощь')
async def help_p(message: types.Message) -> None:
    await message.answer('В разработке')
