from aiogram.types import CallbackQuery, Message
from clientbot.handlers.horoscope.data.callback_datas import ProfileSettings
from clientbot.handlers.horoscope.keyboards.inline import inline_builder
from clientbot.shortcuts import get_user
from loader import client_bot_router
from aiogram import F
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __


@client_bot_router.message(text=__("🎩 Профиль"))
@client_bot_router.callback_query(ProfileSettings.filter(F.action == "settings"))
async def profile(message: Message | CallbackQuery, callback_data: ProfileSettings | None = None):
    user = await get_user(message.from_user.id)

    alert = ("😁", _("Включены")) if user.enable_horoscope_everyday_alert else ("😴", _("Выключены"))
    alert_for_kb = _("😴 Выключить уведомления") if user.enable_horoscope_everyday_alert else _("😁 Включить уведомления")

    if isinstance(message, CallbackQuery):
        if callback_data.value == "change_alert":
            if user.enable_horoscope_everyday_alert:
                alert = ("😴", _("Выключены"))
                alert_for_kb = _("😁 Включить уведомления")
            else:
                alert = ("😁", _("Включены"))
                alert_for_kb = _("😴 Выключить уведомления")
            user.enable_horoscope_everyday_alert = not user.enable_horoscope_everyday_alert
            await user.save()

        await message.answer()
        return await message.message.edit_text(
            _("ID: <code>{usre_id}</code>\n"
              "Ежедневные уведомления: <b>{alert1} {alert2}</b>").format(usre_id=message.from_user.id, alert1=alert[0],
                                                                         alert2=alert[1]),
            reply_markup=inline_builder(
                alert_for_kb,
                ProfileSettings(action="settings", value="change_alert").pack()
            )
        )
    await message.answer(
        _("ID: <code>{usre_id}</code>\n"
          "Ежедневные уведомления: <b>{alert1} {alert2}</b>").format(usre_id=message.from_user.id, alert1=alert[0],
                                                                     alert2=alert[1]),
        reply_markup=inline_builder(
            alert_for_kb,
            ProfileSettings(action="settings", value="change_alert").pack()
        )
    )
