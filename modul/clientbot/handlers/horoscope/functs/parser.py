from typing import Literal, Any
from dataclasses import dataclass

from aiohttp import ClientSession, StreamReader
from bs4 import BeautifulSoup as BS
from fake_useragent import UserAgent


@dataclass
class HoroscopeData:
    date: str
    text: str


class HoroscopeParser:

    def __init__(self) -> None:
        pass

    def _get_sign(self, sign: str) -> str:
        zodiac_signs = {
            "Овен": "Aries",
            "Телец": "Taurus",
            "Близнецы": "Gemini",
            "Рак": "Cancer",
            "Лев": "Leo",
            "Дева": "Virgo",
            "Весы": "Libra",
            "Скорпион": "Scorpio",
            "Стрелец": "Sagittarius",
            "Козерог": "Capricorn",
            "Водолей": "Aquarius",
            "Рыбы": "Pisces"
        }
        return zodiac_signs.get(sign).lower()

    async def get_horoscope(self, sign: str, period: str="today") -> str:
        async with ClientSession(headers={"User-Agent": UserAgent().random}) as session:
            response = await session.get(f"https://horo.mail.ru/prediction/{self._get_sign(sign)}/{period}/")
            soup = BS(await response.text(), "html.parser")

            text_items = soup.find_all(
                "div", class_="article__item article__item_alignment_left article__item_html"
            )
            number_items = soup.find_all(
                "div", class_="p-score-day__item"
            )

            main_text = []
            for item in text_items:
                item.find("p")
                main_text.append(item.text)

            numbers = [
                item.find("span", class_="p-score-day__item__value__inner").text.strip()
                for item in number_items
            ]
            return {"text": "".join(main_text), "numbers": numbers}