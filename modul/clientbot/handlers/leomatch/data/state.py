from aiogram.fsm.state import StatesGroup, State


class LeomatchRegistration(StatesGroup):
    BEGIN = State()
    AGE = State()
    SEX = State()
    CITY = State()
    FULL_NAME = State()
    WHICH_SEARCH = State()
    ABOUT_ME = State()
    SEND_PHOTO = State()
    FINAL = State()


class LeomatchMain(StatesGroup):
    WAIT = State()
    PROFILES = State()
    MY_PROFILE = State()
    PROFILE_MANAGE = State()
    SLEEP = State()
    SET_DESCRIPTION = State()
    SET_PHOTO = State()


class LeomatchProfiles(StatesGroup):
    LOOCK = State()
    INPUT_MESSAGE = State()
    MANAGE_LIKES = State()
    MANAGE_LIKE = State()
