


from clientbot.shortcuts import get_bot_by_token
from db.models import ClientBotUser, GPTRecordModel, GPTTypeEnum


async def add_record(bot_token: str, user_id: int, message: str, type: GPTTypeEnum):
    client = await ClientBotUser.filter(uid=user_id).first()
    bot = await get_bot_by_token(bot_token)
    if client and bot:
        await GPTRecordModel.create(
            user = client,
            bot = bot,
            message = message,
            type = type,
        )