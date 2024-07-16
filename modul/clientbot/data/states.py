# from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.fsm.state import StatesGroup, State


class Broadcast(StatesGroup):
    message = State()
    confirmation = State()


class Transfer(StatesGroup):
    transfer = State()
    amount = State()


class Order(StatesGroup):
    link = State()
    current_step = State()
    confirm = State()

class Payment(StatesGroup):
    amount = State()

class RefillAmount(StatesGroup):
    amount = State()
    method = State()
    crypto = State()


class BroadcastState(StatesGroup):
    message = State()
    confirmation = State()


class ChangePhoto(StatesGroup):
    photo = State()


class ChangeChannelLink(StatesGroup):
    link = State()


class ChangeAdmin(StatesGroup):
    uid = State()


class ChangeSupport(StatesGroup):
    username_or_uid = State()


class Post(StatesGroup):
    buttons = State()


class AddSubscriptionChat(StatesGroup):
    chat_id = State()

class Download(StatesGroup):
    download = State()    
    
class Chat(StatesGroup):
    menu = State()
    text = State()
    image = State()
    
    
class PromocodeState(StatesGroup):
    set_sum = State()
    refill = State()
    confirm_add = State()
    set_count = State()
    set_code = State()
    input_code = State()