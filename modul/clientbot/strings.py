from collections import OrderedDict
from typing import List
from aiogram import html

QUANTITY_ERROR = "⛔️ Пожалуйста введите значение в диапазоне чисел от {min} до {max}"
API_ERROR = "⛔️ Возникла проблема, пожалуйста попробуйте позже"
HAS_ACTIVE_ORDER = "You have active order with this link. Please wait until order being completed."
HAS_ACTIVE_ORDER_RU = "У вас есть активный заказ по этой ссылке. Пожалуйста, дождитесь завершения заказа."
BACK = ("Назад")
SKIP = "Пропустить"
NEW_ORDER_INFO = ("⚠️ Пожалуйста перед тем как заказать услугу перепроверьте её:\n"
                  "🔗 Ссылка на ваш аккаунт: {link}\n"
                  "💰 Сумма: {price} ₽\n"
                  "{additional}\n"
                  "Продолжить?")
ORDER_SUCCEEDED = ("✨Заказ № <b>{}</b> успешно оплачен и принят в работу. "
                   "Отследить его можно нажав кнопку «Мои заказы». "
                   "Если вы допустили какую-то ошибку, то заказ отменятся и деньги вернутся на баланс бота.")
BALANCE = ("💲 Ваш баланс: {balance}₽\n"
           "🏷 Ваш id: <code>{uid}</code>")
BALANCE_CHARGED = "🎊 Ваш баланс успешно пополнен на {} ₽"
CANCELLED = "Отменено."
CANCEL = "Отмена"
WAIT = "Подождите пожалуйста"
PAID = "PAID"
NOT_PAID = "NOT_PAID"
COMPLETED = "Completed"
PARTIAL = "Partial"
IN_PROGRESS = 'In progress'
PROCESSING = "Processing"
PENDING = 'Pending'
ORDER_CANCELED = "Canceled"
ORDER_STATUS = {
    COMPLETED: "Выполнен",
    PARTIAL: "Частично",
    IN_PROGRESS: "В процессе",
    PROCESSING: "В процессе",
    PENDING: "В ожидании",
    ORDER_CANCELED: "Отменён",
}
NOT_COMPLETED = [IN_PROGRESS, PENDING, PROCESSING]
SERVICE_DETAILS = ("<b>ℹ️ Описание по сервису({service_id}):</b>\n\n"
                   "📜 Услуга: <b><u>{service}</u></b>\n\n"
                   "{description}\n\n"
                   "🕔 Среднее время завершения: {compilation_time}\n\n"
                   "💸 Цена{quantity}: <b><u>{price} ₽</u></b>\n\n"
                   "📉 Минимальное: <b><u>{min}</u></b>\n"
                   "📈 Максимальное: <b><u>{max}</u></b>\n\n")
PARTNERS_INFO = ("<b>Партнёрская программа</b>\n\n"
                 "Даёт возможность хорошо заработать, с каждого потенциального клиента."
                 "Все чисто и прозрачно.Если ваш реферал пополнит баланс от 1000руб, "
                 "то вы получите 50руб.\n\n"
                 "<b>Ваши приглашённые:</b>\n\n"
                 "Приглашено всего: {}\n"
                 "Заработано с рефералов: {} ₽\n"
                 "Ваша партнёрская ссылка: \n"
                 "https://t.me/{}?start={}")
INFO = ("{username} - уникальный сервис для СММ\n\n"
        "Наши преимущества:\n"
        "✔️ Низкие цены\n"
        "✔️ Полная автоматизация\n"
        "✔️ Быстрота и удобство\n"
        "✔️ Разнообразие сервисов и стран\n"
        "✔️ Партнёрская программа\n"
        "✔️ Постоянные обновления\n"
        "✔️ Отзывчивая поддержка")
CHOOSE_SOCIAL = "📂 Выберите социальную сеть для накрутки"
STATISTICS = ("Пользователей всего: {users}\n"
              "Новые пользователи: {new_users}\n"
              "Заработано всего: {earned}\n"
              "Прибыль(Сегодня): {earned_today}\n"
              "Заказов за сегодня: {orders}\n")
BROADCAST = ("🗣 Отправьте одно сообщение которое хотите разослать всем пользователям. "
             "Отправка сообщения занимает около {} секунды")

BROADCAST_RESULT = (
    "✅️ Доставлено: {succeed}\n"
    "⛔️ Не доставлено: {failed}"
)

MAIN_MENU = ("Главное меню")

ORDER_DETAILS = (
    "🧾 Заказ №: {order_id}\n"
    "📂 Категория: {category}\n"
    "📊 Статус: {status}\n"
    "📝 Выполнено: {done} из {quantity}\n"
    "⬇️ Ссылка: {link}\n"
    "💵 Стоимость: {rate} ₽\n"
    "📅 Дата: {date}\n"
    "🔁 Повторить {url}\n"
)
SMM_CATEGORIES = [
    "Instagram",
    "Telegram",
    "TikTok",
    "Facebook",
    "YouTube",
    "Rutube",
    "Twitter",
    "Reddit",
    "SoundCloud",
    "Spotify",
    "ВК",
    "Одноклассники",
    "Discord",
    "Web трафик",
    "Яндекс.Дзен",
    "Likee",
    "Twitch",
    "Private",
    "OnlyFans",
    "Yappy",
    "Социальные сигналы",
    "Linkedin",
    "Snapchat",
    "Threads"
]

SMM_CATEGORIES_EMOJIS = [
    "📸", "✈️", "🎞", "📓", "🎥", "🎥", "🔗", "🎛", "📲", "👋", "🎼", "", "🔈", "🌐", "", "❤️", "🌴", "", "🍓", "", "🌐", "", "🐶", ""
]

QUANTITY_COUNT_INFO = "⌨️ Введите количество накрутки. В вашем случае минимальное количество " \
                      "для накрутки {min}, а максимальное {max}"


class ServiceType:
    DEFAULT = "Default"
    PACKAGE = "Package"
    CUSTOM_COMMENTS = "Custom Comments"
    MENTIONS_USER_FOLLOWERS = "Mentions User Followers"
    CUSTOM_COMMENTS_PACKAGE = "Custom Comments Package"
    COMMENT_LIKES = "Comment Likes"
    POLL = "Poll"
    INVITES_FROM_GROUPS = "Invites from Groups"
    SUBSCRIPTIONS = "Subscriptions"


SERVICE_STEPS = {
    ServiceType.DEFAULT: OrderedDict({
        "quantity": {"description": QUANTITY_COUNT_INFO, "optional": False, "ru": "Количество"},
        # "runs": {"description": "Runs to deliver", "optional": True, "ru": "работает"},
        # "interval": {"description": "Введите время выполнения заказа в минутах:", "optional": True, "ru": "Интервал"}
    }),
    ServiceType.PACKAGE: {},
    ServiceType.CUSTOM_COMMENTS: OrderedDict({
        "comments": {"description": "Список комментариев, 1 в строке", "optional": False,
                     "ru": "Комментарии", "type": "line"}
    }),
    ServiceType.MENTIONS_USER_FOLLOWERS: OrderedDict({
        "quantity": {"description": QUANTITY_COUNT_INFO, "optional": False, "ru": "Количество"},
        "usernames": {"description": "Список имен пользователей, 1 в строке", "optional": False,
                      "ru": "Имена пользователей", "type": "line"},
    }),
    ServiceType.CUSTOM_COMMENTS_PACKAGE: OrderedDict({
        "comments": {"description": "Список комментариев, 1 в строке", "optional": False,
                     "ru": "Комментарии", "type": "line"}
    }),
    ServiceType.COMMENT_LIKES: OrderedDict({
        "quantity": {"description": QUANTITY_COUNT_INFO, "optional": False, "ru": "Количество"},
        "usernames": {"description": "Список имен пользователей, 1 в строке", "optional": False,
                      "ru": "Имена пользователей", "type": "line"},
    }),
    ServiceType.POLL: OrderedDict({
        "quantity": {"description": QUANTITY_COUNT_INFO, "optional": False, "ru": "Количество"},
        "answer_number": {"description": "Ответ номер опроса", "optional": False, "ru": "Номер ответа"},

    }),
    ServiceType.INVITES_FROM_GROUPS: OrderedDict({
        "quantity": {"description": QUANTITY_COUNT_INFO, "optional": False, "ru": "Количество"},
        "groups": {"description": "Список групп, 1 в строке", "optional": False, "ru": "Группы", "type": "line"},
    }),
    ServiceType.SUBSCRIPTIONS: OrderedDict({
        "usernames": {"description": "Список имен пользователей, 1 в строке", "optional": False,
                      "ru": "Имена пользователей", "type": "line"},
        "min": {"description": "Количество мин", "optional": False, "ru": "Минимум"},
        "max": {"description": "Максимальное количество", "optional": False, "ru": "Максимум"},
        "posts": {"description": "Количество новых сообщений", "optional": False, "ru": "Посты"},
        "delay": {"description": ("Задержка в минутах. "
                                  "Возможные значения: 0, 5, 10, 15, 30, 60, 90, 120, "
                                  "150, 180, 210, 240, 270, 300, 360, 420, 480, 540, 600."),
                  "optional": False, "ru": "Задержка в минутах"},
        "expiry ": {"description": "Срок действия. Формат д/м/г", "optional": True, "ru": "Срок действия"},

    })
}

def get_subscription_chats(is_turned_on: bool, chats: list = None):
    text = "Статус: ✅ включен\n" if is_turned_on else "Статус: ☑️ выключен\n"
    text += "\nЧаты:\n"
    for idx, chat in enumerate(chats, 1):
        text += f"{idx}) {html.link(chat.title, chat.invite_link)}\n"
    return text


def get_order_details(orders: List, page=1, page_count=1):
    text = f"📦 Страница {page} из {page_count}\n\n"
    for order in orders:
        text += ORDER_DETAILS.format(
            order_id=order.order_id,
            category=order.category,
            status=ORDER_STATUS[order.status],
            done=order.quantity - order.remains if order.remains is not None else 0,
            link=order.link or "",
            quantity=order.quantity,
            rate=f"{order.price:.2f}",
            date=order.created_at.strftime("%m/%d/%Y, %H:%M:%S"),
            url=f"/order_{order.order_id}"
        )
        text += "\n"
    return text
