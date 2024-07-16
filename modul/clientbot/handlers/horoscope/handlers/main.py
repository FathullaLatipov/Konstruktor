from contextlib import suppress

from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
import pendulum
from clientbot.handlers.horoscope.functs.statistic import add_statistic

from clientbot.handlers.horoscope.keyboards.reply import main_horoscope_menu, zodiac_signs_builder
from clientbot.handlers.horoscope.functs.parser import HoroscopeParser
from clientbot.handlers.horoscope.functs.gen_image import make_horoscope_image
from clientbot.handlers.horoscope.data.states import PeriodForm
from loader import client_bot_router

hparser = HoroscopeParser()


@client_bot_router.message(text="♈️ Гороскоп")
@client_bot_router.message(state=PeriodForm.day, text=__("Вернуться"))
@client_bot_router.message(state=PeriodForm.month, text=__("Вернуться"))
@client_bot_router.message(state=PeriodForm.tomorrow, text=__("Вернуться"))
async def horoscope(message: Message | CallbackQuery, state: FSMContext) -> None:
    await message.answer(_("Добро пожаловать, {full_name}!").format(full_name=message.from_user.full_name),
                         reply_markup=await main_horoscope_menu())


@client_bot_router.message(
    F.text.in_([__("🔮 Гороскоп на каждый день"), __("🔮 Гороскоп на месяц"), __("🔮 Гороскоп на завтра")])
)
@client_bot_router.callback_query(F.data == "look_horoscope")
async def horoscope(message: Message | CallbackQuery, state: FSMContext) -> None:
    period = _("день")
    msg_text = _("день") if isinstance(message, CallbackQuery) else message.text
    pattern = {
        "photo": "https://i.imgur.com/th5YkKr.jpg",
        "caption": _("<b>🔮 Выберите Ваш знак зодиака, чтобы узнать гороскоп на {period}:</b>").format(period=period),
        "reply_markup": zodiac_signs_builder()
    }

    if msg_text.endswith(_("месяц")):
        await state.set_state(PeriodForm.month)
        period = _("месяц")
    elif msg_text.endswith(_("завтра")):
        await state.set_state(PeriodForm.tomorrow)
        period = _("завтра")
    else:
        await state.set_state(PeriodForm.day)

    if isinstance(message, CallbackQuery):
        return await message.message.answer_photo(**pattern)
    await message.answer_photo(**pattern)


@client_bot_router.message(
    F.text.in_([
        _("♈ Овен"), _("♉ Телец"), _("♊ Близнецы"), _("♋ Рак"),
        _("♌ Лев"), _("♍ Дева"), _("♎ Весы"), _("♏ Скорпион"),
        _("♐ Стрелец"), _("♑ Козерог"), _("♒ Водолей"), _("♓ Рыбы")
    ]),
    flags={"dont_clear": "dont_clear_state"})
async def horoscope_show(message: Message, state: FSMContext, bot: Bot) -> None:
    await message.answer(_("Подождите, формируется гороскоп"))
    current_state = await state.get_state()
    if current_state not in [PeriodForm.day.state, PeriodForm.month.state, PeriodForm.tomorrow.state]:
        return
    cs_name = current_state.split(":")[1]

    if cs_name == "month":
        hr = await hparser.get_horoscope(message.text[2:], period="month")
        current_date = _("{message} на текущий месяц").format(message=message.text)
    elif cs_name == "day":
        hr = await hparser.get_horoscope(message.text[2:])
        current_date = _("{message} на {pendu}").format(message=message.text, pendu=pendulum.now().to_date_string())
    elif cs_name == "tomorrow":
        hr = await hparser.get_horoscope(message.text[2:], period="tomorrow")
        current_date = _("{message} на {pendu}").format(message=message.text,
                                                        pendu=pendulum.tomorrow().to_date_string())

    horoscope_text = hr["text"].split("\n")
    numbers = ""

    with suppress(IndexError):
        numbers = (
            _("🤑 Бизнес: {hr1} "
              "💖 Любовь: {hr2} "
              "🍀 Цифра дня: {hr3}").format(hr1=hr['numbers'][0], hr2=hr['numbers'][1], hr3=hr['numbers'][2])
        )

    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer_photo(
        photo=
        BufferedInputFile(
            await make_horoscope_image(
                horoscope_text[0] if len(horoscope_text[0]) < 450 else horoscope_text[1],
                cs_name
            ),
            f"{message.from_user.id}"
        ),
        caption=
        f"{current_date}\n\n"
        f"🔮 {horoscope_text[0]}\n\n"
        f"🔮 {horoscope_text[1]}\n\n"
        f"{numbers}",
        parse_mode="Markdown"
    )
    me = await bot.get_me()
    await add_statistic(me.username)
