from datetime import timedelta, datetime, timezone
import pytz
import locale
from bot.database import Database
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot.date_d import sheduled_post

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

db = Database()

silent_mode = False
secure_mode = False
comment_mode = True
media_mode = True
auto_repeat = True

time_zone = 'Asia/Tashkent'
current_time = datetime.now(timezone.utc)

desired_timezone_obj = pytz.timezone(time_zone)
current_time_desired_tz = current_time.astimezone(desired_timezone_obj)
print(current_time_desired_tz)
print(current_time)

# Форматируем время и часовой пояс
formatted_time = current_time_desired_tz.strftime("%H:%M")
formatted_time_zone = str(time_zone)


def settings(data):
    if data:
        buttons = [
            [
                InlineKeyboardButton(text='💰Оплата подписки', callback_data='subscription')
            ],
            [
                InlineKeyboardButton(text=f'{i[0]}', callback_data=f"addchannel_{i[0]}") for i in data
            ],
            [
                InlineKeyboardButton(text="➕Добавить канал", callback_data="add_channel"),
            ],
            [
                InlineKeyboardButton(text=f"Часовой пояс: {formatted_time_zone}({formatted_time})",
                                     callback_data="delete_channel"),
            ]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    else:
        buttons = [
            [
                InlineKeyboardButton(text='💰Оплата подписки', callback_data='subscription')
            ],
            [
                InlineKeyboardButton(text="➕Добавить канал", callback_data="add_channel"),
            ],
            [
                InlineKeyboardButton(text=f"Часовой пояс: {formatted_time_zone}({formatted_time})",
                                     callback_data="delete_channel"),
            ]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard


def main_menu_kb():
    kb = [
        [
            KeyboardButton(text="Создать пост"),
            KeyboardButton(text="Изменить пост"),
        ],
        [
            # KeyboardButton(text="Шаблоны"),
            KeyboardButton(text="Контент план"),
        ],
        [
            KeyboardButton(text="Настройки"),
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    return keyboard


def create_post_kb(media):
    ch_text = InlineKeyboardButton(text="Изменить текст", callback_data="update_text")
    add_med = InlineKeyboardButton(text="Добавить медиа", callback_data="add_media")
    unfasten_media = InlineKeyboardButton(text="Убрать медиа", callback_data="unfasten_media")
    bell = InlineKeyboardButton(text="🔔", callback_data="bell")
    url_button = InlineKeyboardButton(text="URL-кнопки", callback_data="url_buttons")
    comments = InlineKeyboardButton(text="✅️Комментарии", callback_data="comments")
    secure = InlineKeyboardButton(text="☑️Закрепить", callback_data="secure")
    return_to_main_menu = InlineKeyboardButton(text="Отмена", callback_data="return_to_main_menu")
    next_n = InlineKeyboardButton(text="Далее", callback_data="next_l")
    buttons = [
        [
            ch_text,

        ],
        [
            add_med,
        ],
        [
            bell,
            url_button,

        ],
        [
            secure,

        ],
        [
            return_to_main_menu,
            next_n,
        ]

    ]

    if media:
        print(media)
        buttons[1][0].text = 'Убрать медиа'
        buttons[1][0].callback_data = 'unfasten_media'
        if silent_mode:
            buttons[2][0].text = "🔕️"
        elif not silent_mode:
            buttons[2][0].text = "🔔"
        if secure_mode:
            buttons[3][0].text = "✅️Закрепить"
        elif not secure_mode:
            buttons[3][0].text = "☑️️Закрепить"
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    else:
        if silent_mode:
            buttons[2][0].text = "🔕️"
        elif not silent_mode:
            buttons[2][0].text = "🔔"
        if secure_mode:
            buttons[3][0].text = "✅️Закрепить"
        elif not secure_mode:
            buttons[3][0].text = "☑️️Закрепить"
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard


def update_post_kb():
    buttons = [
        [
            InlineKeyboardButton(text="Изменить текст", callback_data="update_textv2"),
        ],
        [InlineKeyboardButton(text="Добавить медиа", callback_data="add_mediav2")],

        [InlineKeyboardButton(text="URL-кнопки", callback_data="url_buttonv2"),
         InlineKeyboardButton(text="☑️Закрепить", callback_data="securev2")],
        [InlineKeyboardButton(text="Сохранить изменения", callback_data="save_changes"),
         InlineKeyboardButton(text="Отмена", callback_data="return_to_main_menu2")],
    ]
    if secure_mode:
        buttons[2][1].text = "✅️Закрепить"
    elif not secure_mode:
        buttons[2][1].text = "☑️Закрепить"
    if media_mode:
        buttons[1][0].text = "Добавить медиа"
    elif not media_mode:
        buttons[1][0].text = "Открепить медиа"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def settings_post_kb(edit_text):
    buttons = [
        [
            InlineKeyboardButton(text=f"Таймер удаления: {edit_text}", callback_data="delete_timer"),
        ],
        [
            InlineKeyboardButton(text="Отложить", callback_data="post_delay"),
            InlineKeyboardButton(text="Опубликовать", callback_data="post_publish"),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="back"),
        ]
    ]
    # elif edit_text:
    #     buttons[0][0].text = f"Таймер удаления: 5"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def back():
    buttons = [
        [
            InlineKeyboardButton(text="<-Назад", callback_data="back"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def photo_ai():
    buttons = [
        [
            InlineKeyboardButton(text="Создать фото с помощью AI", callback_data="create_media_ai"),
        ],
        [
            InlineKeyboardButton(text="<-Назад", callback_data="back"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def back1():
    buttons = [
        [
            InlineKeyboardButton(text="<-Назад", callback_data="back1"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def back_change():
    buttons = [
        [
            InlineKeyboardButton(text="<-Назад", callback_data="back_change"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def buttons_timer_to_delete():
    buttons = [
        [
            InlineKeyboardButton(text="нет", callback_data="back_no"),
            InlineKeyboardButton(text="5 минут", callback_data="5"),
            InlineKeyboardButton(text="15 минут", callback_data="15"),
            InlineKeyboardButton(text="30 минут", callback_data="30"),
        ],
        [
            InlineKeyboardButton(text="1 ч", callback_data="1hour"),
            InlineKeyboardButton(text="2 ч", callback_data="2hour"),
            InlineKeyboardButton(text="4 ч", callback_data="4hour"),
            InlineKeyboardButton(text="6 ч", callback_data="6hour"),
        ],
        [
            InlineKeyboardButton(text="12 ч", callback_data="12hour"),
            InlineKeyboardButton(text="24 ч", callback_data="24hour"),
            InlineKeyboardButton(text="36 ч", callback_data="36hour"),
            InlineKeyboardButton(text="48 ч", callback_data="48hour"),
        ],
        [
            InlineKeyboardButton(text="3 д", callback_data="3day"),
            InlineKeyboardButton(text="5 д", callback_data="5day"),
            InlineKeyboardButton(text="7 д", callback_data="7day"),
            InlineKeyboardButton(text="14 д", callback_data="14day"),
        ]
    ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def templates_kb_ch(data):
    buttons = [
        [
            InlineKeyboardButton(text=i[0], callback_data=f"template_{i[0]}") for i in data
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def template_kb(data):
    if data:
        buttons = [[InlineKeyboardButton(text=f"{i[2]}", callback_data=f"postemp_{i[2]}") for i in data],
                   [InlineKeyboardButton(text="Cоздать шаблон", callback_data="create_template")],
                   [InlineKeyboardButton(text="Назад", callback_data="back_to_templates")],
                   ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard
    else:
        buttons = [
            [
                InlineKeyboardButton(text="Cоздать шаблон", callback_data="create_template")
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data="back_to_templates")
            ]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return keyboard


def add_template_kb(text=None, url=None, media=None):
    if text:
        buttons = [
            [
                InlineKeyboardButton(text=text, url=url),
            ],
            [
                InlineKeyboardButton(text='Изменить текст', callback_data='change_description_template'),
            ],
            [
                InlineKeyboardButton(text='Добавить медиа', callback_data='add_media_template'),
            ],
            [
                InlineKeyboardButton(text='Url-кнопки', callback_data='url_buttons_template'),
            ],
            [
                InlineKeyboardButton(text='Отмена', callback_data='back_to_create_tamp'),
                InlineKeyboardButton(text='Готово', callback_data='next_template'),
            ]

        ]
        if media:
            buttons[2][0].text = 'Убрать медиа'
            buttons[2][0].callback_data = 'unfasten_media_template'
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            return keyboard
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            return keyboard
    else:
        buttons = [
            [
                InlineKeyboardButton(text='Изменить текст', callback_data='change_description_template'),
            ],
            [
                InlineKeyboardButton(text='Добавить медиа', callback_data='add_media_template'),
            ],
            [
                InlineKeyboardButton(text='Url-кнопки', callback_data='url_buttons_template'),
            ],
            [
                InlineKeyboardButton(text='Отмена', callback_data='back_temp_post'),
                InlineKeyboardButton(text='Готово', callback_data='next_template'),
            ]

        ]
        if media:
            buttons[1][0].text = 'Убрать медиа'
            buttons[1][0].callback_data = 'unfasten_media_template'
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            return keyboard
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            return keyboard


def back_temp_post():
    buttons = [
        [
            InlineKeyboardButton(text="<-Назад", callback_data="back_temp_post"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def template_kb_edit():
    buttons = [
        [
            InlineKeyboardButton(text="Опублитковать", callback_data="post_temp_publish"),
            InlineKeyboardButton(text='Изменть', callback_data='change_post_template'),
        ],
        [
            InlineKeyboardButton(text='Удалить', callback_data='delete_temp_post')
        ],
        [
            InlineKeyboardButton(text="Отмена", callback_data="back_to_create_tamp"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


short_weekday_names = {
    0: 'Пн',
    1: 'Вт',
    2: 'Ср',
    3: 'Чт',
    4: 'Пт',
    5: 'Сб',
    6: 'Вс'
}


# Функция для создания клавиатуры с кнопками дат
def create_date_keyboard(selected_date, data=None):
    # Получаем даты для вчерашнего, сегодняшнего и завтрашнего дня
    yesterday = selected_date - timedelta(days=1)
    tomorrow = selected_date + timedelta(days=1)

    # Форматируем текст для кнопок
    yesterday_text = f"<-{short_weekday_names[yesterday.weekday()]}, {yesterday.strftime('%d %B')}"
    today_text = f"{short_weekday_names[selected_date.weekday()]}, {selected_date.strftime('%d %B')}"
    tomorrow_text = f"{short_weekday_names[tomorrow.weekday()]}, {tomorrow.strftime('%d %B')}->"
    if db.get_all_content():
        for i in db.get_all_content():
            for j in db.get_all_content():

                print(db.get_all_content())
                schedul = sheduled_post.get(selected_date.strftime('%Y-%m-%d'))
                print(selected_date.strftime('%Y-%m-%d') == i[2][:10])
                print(selected_date.strftime('%Y-%m-%d'), j[2][:10])
                print(schedul)
                print(sheduled_post)
                if schedul:
                    if data:
                        buttons = [
                            [
                                InlineKeyboardButton(text=f'{i[1]}', callback_data=f"datepost_{i[1]}") for i in data if
                                i[2][:10] == selected_date.strftime('%Y-%m-%d')
                            ],
                            [InlineKeyboardButton(text=yesterday_text,
                                                  callback_data=f"date_{yesterday.strftime('%Y-%m-%d')}"),
                             InlineKeyboardButton(text=today_text,
                                                  callback_data=f"date_{selected_date.strftime('%Y-%m-%d')}"),
                             InlineKeyboardButton(text=tomorrow_text,
                                                  callback_data=f"date_{tomorrow.strftime('%Y-%m-%d')}")]
                        ]
                        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                        return keyboard
    # else:
    #     # Создаем кнопки
    #     buttons = [
    #         [InlineKeyboardButton(text=yesterday_text, callback_data=f"date_{yesterday.strftime('%Y-%m-%d')}"),
    #          InlineKeyboardButton(text=today_text, callback_data=f"date_{selected_date.strftime('%Y-%m-%d')}"),
    #          InlineKeyboardButton(text=tomorrow_text, callback_data=f"date_{tomorrow.strftime('%Y-%m-%d')}")]
    #     ]
    #     keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    #     return keyboard
    buttons = [
        [InlineKeyboardButton(text=yesterday_text, callback_data=f"date_{yesterday.strftime('%Y-%m-%d')}"),
         InlineKeyboardButton(text=today_text, callback_data=f"date_{selected_date.strftime('%Y-%m-%d')}"),
         InlineKeyboardButton(text=tomorrow_text, callback_data=f"date_{tomorrow.strftime('%Y-%m-%d')}")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

    # Создаем разметку клавиатуры


def back_to_settings():
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data="back_settings"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def edit_chanel():
    buttons = [
        [
            InlineKeyboardButton(text='Убрать канал', callback_data='delete_chanel'),
            InlineKeyboardButton(text="Назад", callback_data="back_to_settings"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def choose_channel(data):
    buttons = [
        [
            InlineKeyboardButton(text=f'{i[0]}', callback_data=f"choose_{i[0]}") for i in data
        ]
    ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons)
    return keyboard


def ai():
    buttons = [
        [
            InlineKeyboardButton(text="Создать с помощью AI", callback_data="create_ai"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def delay_ai():
    buttons = [
        [
            InlineKeyboardButton(text="Создать несколько постов и отложить", callback_data="delay_ai"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard


def post_ai(media=None):
    if media:
        buttons = [
            [
                InlineKeyboardButton(text="Изменить текст", callback_data="update_textv3"),
            ],
            [
                InlineKeyboardButton(text="Убрать медиа", callback_data="delete_mediav3"),
            ],
            [InlineKeyboardButton(text="Назад", callback_data="return_ai"),
             InlineKeyboardButton(text="Далее", callback_data="further_ai")],
            [
                InlineKeyboardButton(text="Опубликовать", callback_data="publish_posts_ai")
            ]
        ]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
        return keyboard
    else:
        buttons = [
            [
                InlineKeyboardButton(text="Изменить текст", callback_data="update_textv3"),
            ],
            [InlineKeyboardButton(text="Назад", callback_data="return_ai"),
             InlineKeyboardButton(text="Далее", callback_data="further_ai")],
            [
                InlineKeyboardButton(text="Опубликовать", callback_data="publish_posts_ai")
            ]
        ]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
        return keyboard

def back_post_ai():
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data="back_post_ai"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
    return keyboard