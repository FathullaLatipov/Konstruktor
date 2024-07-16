from io import BytesIO
from aiohttp import ClientSession
from PIL import Image, ImageDraw, ImageFont
import pendulum
import textwrap
from aiogram.utils.i18n import gettext as _


async def make_horoscope_image(bot_username: str, text: str, tomorrow: str = "today") -> bytes:
    async with ClientSession() as session:
        response = await session.get("https://i.imgur.com/SXGAxtk.jpg")
        img = Image.open("clientbot/handlers/horoscope/data/SXGAxtk.jpg")

        month_name = {
            1: _('января'),
            2: _('февраля'),
            3: _('марта'),
            4: _('апреля'),
            5: _('мая'),
            6: _('июня'),
            7: _('июля'),
            8: _('августа'),
            9: _('сентября'),
            10: _('октября'),
            11: _('ноября'),
            12: _('декабря')
        }

        day_font = ImageFont.truetype("clientbot/data/arial.ttf", 120)
        date_name_font = ImageFont.truetype("clientbot/data/arial.ttf", 60)
        text_font = ImageFont.truetype("clientbot/data/arial.ttf", 40)
        footer_font = ImageFont.truetype("clientbot/data/arial.ttf", 30)

        draw = ImageDraw.Draw(img)
        draw.text(
            (30, 30), str(pendulum.now().day) if tomorrow != "tomorrow" else str(pendulum.tomorrow().day),
            font=day_font, stroke_width=1, stroke_fill="#000000"
        )
        draw.text(
            (30, 150), month_name[pendulum.now().month if tomorrow != "tomorrow" else pendulum.tomorrow().month],
            font=date_name_font, stroke_width=1, stroke_fill="#000000"
        )
        draw.text(
            (img.width / 2, img.height / 2), "\n".join(textwrap.wrap(text, 40)),
            font=text_font, anchor="mm", align="center", stroke_width=1, stroke_fill="#000000"
        )
        draw.text(
            (img.width / 2, img.height - 30), f"@{bot_username}",
            font=footer_font, anchor="mm", align="center", fill="#767785"
        )

        buffered_image = BytesIO()
        img.save(buffered_image, "PNG")
        return buffered_image.getvalue()
