from aiogram.dispatcher.filters.callback_data import CallbackData


class ProfileSettings(CallbackData, prefix="horoscope-profile"):
    action: str
    value: str | None = None


class EasternAnimals(CallbackData, prefix="horoscope-east"):
    animal: str