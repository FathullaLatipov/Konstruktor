from aiogram.dispatcher.fsm.state import StatesGroup, State

class CountryState(StatesGroup):
    search = State()


class ProductState(StatesGroup):
    search = State()

