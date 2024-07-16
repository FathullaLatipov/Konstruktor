from aiogram import Bot

from modul import models
from modul.config import settings_conf
from modul.loader import bot_session


def crud_bot(request):
    if request.method == 'POST':
        if request.POST['status'] == 'new':
            new__bot(request)
        elif request.POST['status'] == 'delete':
            delete_bot(request.POST['id'])
        elif request.POST['status'] == 'update':
            update_sushi(request)
        elif request.POST['status'] == 'by_id':
            return models.Bot.objects.all().values().order_by('id')
        elif request.POST['status'] == 'by_name':
            return models.Bot.objects.all().values().order_by('token')

    all_bot = models.Bot.objects.all().values()
    return all_bot


async def sub_process_bot(token: str, uid: int):
    url = settings_conf.WEBHOOK_URL.format(token=token)
    async with Bot(token, session=bot_session).context(auto_close=False) as bot:
        await bot.set_webhook(url, allowed_updates=settings_conf.USED_UPDATE_TYPES)
    return True

def new__bot(request):
    token = request.POST['token']
    owner = request.POST['owner']
    with Bot(token=token, session=bot_session).context(auto_close=False) as bot:
        bot_me = bot.get_me()
        bot_username = bot_me.username
        bot = models.Bot(token=token, owner=owner, user_name=bot_username)
        bot.save()


def delete_bot(id):
    bot = models.Bot.objects.get(id=id)
    bot.delete()


def update_sushi(request):
    if request.method == 'POST':
        bot = models.Bot.objects.get(id=request.POST['id'])
        bot.token = request.POST['token']
        module = request.POST['modul']
        module2 = f"enable_{module}"
        bot.enable_download = False
        bot.enable_leo = False
        bot.enable_chatgpt = False
        bot.enable_horoscope = False
        bot.enable_anon = False
        bot.enable_sms = False
        bot.module2 = True
        bot.save()
