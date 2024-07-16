from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from clientbot.handlers.chatgpt.callback_data import AIAgreeCallbackData, AIBalanceCallbackData, ChatGPTCallbackData, \
    SpeechVoiceCallbackData
from clientbot.handlers.chatgpt.data import get_ai_pricing


def get_kbrd_chat_type(model: str, use_context: bool = True):
    kbrd = InlineKeyboardBuilder()
    if use_context:
        kbrd.add(InlineKeyboardButton(text=_("с контекстом"),
                                      callback_data=ChatGPTCallbackData(model=model, use_context=True).pack()))
        kbrd.add(InlineKeyboardButton(text=_("без контекста"),
                                      callback_data=ChatGPTCallbackData(model=model, use_context=False).pack()))
    else:
        kbrd.add(InlineKeyboardButton(text=_("Попробовать"), callback_data=ChatGPTCallbackData(model=model).pack()))
    return kbrd.as_markup(resize_keyboard=True)


def get_kbrd_speech_voices():
    kbrd = InlineKeyboardBuilder()
    voices = [
        'alloy', 'echo', 'nova', 'fable', 'shimmer'
    ]
    kbrd.row(
        *[
            InlineKeyboardButton(text=voice, callback_data=SpeechVoiceCallbackData(voice=voice).pack()) for voice in
            voices
        ],
        width=2,
    )
    kbrd.row(InlineKeyboardButton(text=_("Отмена"), callback_data=SpeechVoiceCallbackData(voice="cancel").pack()),
             width=1, )
    return kbrd.as_markup(resize_keyboard=True)


def get_kbrd_ai_cabinet():
    kbrd = InlineKeyboardBuilder()
    kbrd.row(
        InlineKeyboardButton(text=_("Пополнить баланс"),
                             callback_data=AIBalanceCallbackData(action="balance-list").pack()),
        width=1,
    )
    return kbrd.as_markup(resize_keyboard=True)


def get_kbrd_agree(video_id: str, cost: int, message_id: int):
    kbrd = InlineKeyboardBuilder()
    kbrd.row(
        InlineKeyboardButton(text=_("✅ Согласен"),
                             callback_data=AIAgreeCallbackData(video_id=video_id, cost=cost, agree=True,
                                                               message_id=message_id).pack()),
        InlineKeyboardButton(text=_("❌ Отмена"), callback_data=AIAgreeCallbackData(agree=False).pack()),
        width=1,
    )
    return kbrd.as_markup(resize_keyboard=True)


async def get_kbrd_ai_balance(user_id, percent: float):
    kbrd = InlineKeyboardBuilder()
    data = await get_ai_pricing(user_id, percent)
    kbrd.row(
        *[
            InlineKeyboardButton(text=f"{item['gt']} ⭐ = {item['rub']} ₽",
                                 callback_data=AIBalanceCallbackData(action="balance", gt=item['gt'],
                                                                     rub=item['rub']).pack()) for item in data
        ],
        width=2,
    )
    kbrd.row(InlineKeyboardButton(text=_("Отменить"), callback_data=AIBalanceCallbackData(action="cancel").pack()),
             width=1)
    return kbrd.as_markup(resize_keyboard=True)


def get_kbrd_help(support_url: str):
    kbrd = InlineKeyboardBuilder()
    kbrd.row(InlineKeyboardButton(text=_("❔ FAQ"), callback_data="ai-faq"), width=1)
    kbrd.row(InlineKeyboardButton(text=_("👤 Служба поддержки"), url=support_url), width=1)
    return kbrd.as_markup(resize_keyboard=True)


def get_kbrd_faq():
    kbrd = InlineKeyboardBuilder()
    kbrd.row(InlineKeyboardButton(text=_("🤖 Что умеет бот?"), callback_data="ai-faq-about-bot"), width=1)
    kbrd.row(InlineKeyboardButton(text=_("⚡️ Что такое ⭐️?"), callback_data="ai-faq-about-gt"), width=1)
    kbrd.row(InlineKeyboardButton(text=_("💲 Почему это платно?"), callback_data="ai-faq-why-donate"), width=1)
    kbrd.row(InlineKeyboardButton(text=_("💳 Как пополнить баланс?"), callback_data="ai-faq-how-refill-balance"),
             width=1)
    kbrd.row(InlineKeyboardButton(text=_("🔙 Назад"), callback_data="ai-help"), width=1)
    return kbrd.as_markup(resize_keyboard=True)


def get_kbrd_cancel_to_ai_faq():
    kbrd = InlineKeyboardBuilder()
    kbrd.add(InlineKeyboardButton(text=_("🔙 Назад"), callback_data="ai-faq"))
    return kbrd.as_markup(resize_keyboard=True)
