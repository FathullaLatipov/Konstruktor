from aiogram.dispatcher.fsm.state import StatesGroup, State


class PeriodForm(StatesGroup):
    day = State()
    month = State()
    tomorrow = State()