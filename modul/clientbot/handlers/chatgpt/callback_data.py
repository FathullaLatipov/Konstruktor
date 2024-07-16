from aiogram.dispatcher.filters.callback_data import CallbackData

class ChatGPTCallbackData(CallbackData, prefix="ChatGPTCallbackData"):
    model: str
    use_context: bool = None

class SpeechVoiceCallbackData(CallbackData, prefix="SpeechVoiceCallbackData"):
    voice: str
    
class AIBalanceCallbackData(CallbackData, prefix="AIBalanceCallbackData"):
    action: str
    gt: int = None
    rub: int = None
    
class AIAgreeCallbackData(CallbackData, prefix="AIBalanceCallbackData"):
    agree: bool
    video_id: str = None
    cost: int = None
    message_id: int = None
    
class AssistantAICallbackdata(CallbackData, prefix="assistant_ai"):
    action: str
    data: int = None