from aiogram.fsm.state import StatesGroup, State


class SearchMusic(StatesGroup):
    waiting_for_music_name = State()
    waiting_for_music_choice = State()
