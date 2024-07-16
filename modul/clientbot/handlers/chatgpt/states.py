from aiogram.dispatcher.fsm.state import StatesGroup, State


class AIState(StatesGroup):
    input_prompt = State()
    
class AssistantAIChatStates(StatesGroup):
    chat = State()