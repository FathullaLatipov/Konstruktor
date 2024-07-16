from aiogram.utils.keyboard import InlineKeyboardBuilder
from clientbot.handlers.horoscope.data.callback_datas import EasternAnimals


def inline_builder(
    text: str | list[str],
    callback_data: str | list[str],
    sizes: int | list[int]=2,
    **kwargs
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    text = [text] if isinstance(text, str) else text
    callback_data = [callback_data] if isinstance(callback_data, str) else callback_data
    sizes = [sizes] if isinstance(sizes, int) else sizes

    [
        builder.button(text=txt, callback_data=cb)
        for txt, cb in zip(text, callback_data)
    ]

    builder.adjust(*sizes)
    return builder.as_markup(**kwargs)

def eastern_horoscope_animals_builder() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    items = {
        "Мышь": EasternAnimals(animal="mouse"),
        "Бык": EasternAnimals(animal="bull"),
        "Тигр": EasternAnimals(animal="tiger"),
        "Кролик": EasternAnimals(animal="rabbit"),
        "Дракон": EasternAnimals(animal="dragon"),
        "Змея": EasternAnimals(animal="snake"),
        "Лошадь": EasternAnimals(animal="horse"),
        "Коза": EasternAnimals(animal="goat"),
        "Обезьяна": EasternAnimals(animal="monkey"),
        "Петух": EasternAnimals(animal="rooster"),
        "Собака": EasternAnimals(animal="dog"),
        "Свинья": EasternAnimals(animal="pig"),
    }

    [
        builder.button(text=key, callback_data=value)
        for key, value in items.items()
    ]
    builder.adjust(4)
    return builder.as_markup()