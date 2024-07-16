from aiogram import types
from aiogram.utils.i18n import gettext

from clientbot.utils.smm import get_service
from clientbot import shortcuts, strings
from clientbot.keyboards import inline_kb
from loader import client_bot_router


@client_bot_router.message(state="*")
async def order_id_handler(message: types.Message):
    if message.text and message.text.startswith("/order_"):
        parts = message.text.split("_")
        if len(parts) == 2:
            order_id = parts[1]
            if order_id.isdigit():
                order_retry = await shortcuts.get_order_retry(order_id)
                service = await get_service(order_retry.service)
                if not service:
                    await message.answer(gettext("Услуга не доступна"))
                    return
                if int(service.min) == 1 and int(service.max) == 1:
                    service_price = float(service.rate)
                else:
                    service_price = shortcuts.calculate_service_price(service)
                price, _, _ = await shortcuts.calculate_price(message.from_user.id, service_price)
                await message.answer(
                    strings.SERVICE_DETAILS.format(
                        service_id=service.service,
                        service=service.name,
                        quantity="" if int(service.min) == 1 and int(service.max) == 1 else " за 1000",
                        price=f"{price:.2f}",
                        min=int(service.min),
                        max=int(service.max),
                        description=service.description,
                        compilation_time=service.time
                    ),
                    reply_markup=inline_kb.service_chose(
                        order_retry.smm, order_retry.category, service.service)
                )
            else:
                await message.answer(gettext("Номер заказа должен быть цифрами"))
        else:
            await message.answer(gettext("Не верное  кол-во аргументов!"))