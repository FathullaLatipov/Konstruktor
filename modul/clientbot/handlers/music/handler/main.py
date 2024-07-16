from aiogram import Bot
from aiogram.types import Message, CallbackQuery, URLInputFile
from modul.clientbot.handlers.music.data import callback_data
from modul.clientbot.handlers.music.data.states import SearchMusic
from modul.clientbot.handlers.music.keyboards.inline_kb import artist_btn, artist_music_btn, chart_music_btn, new_music_btn, \
    search_music_btn, top_music_btn
from modul.clientbot.handlers.music.keyboards.reply_kb import music_main_menu
from modul.clientbot.utils.functs import return_main
from modul.clientbot.utils.music_downloader import music_downloader
from modul.clientbot.shortcuts import add_to_analitic_data
from modul.config import scheduler
from modul.loader import client_bot_router, shazam, bot_session
from aiogram.fsm.context import FSMContext
from shazamio import GenreMusic, Serialize
from shazamio.schemas.artists import ArtistQuery
from shazamio.schemas.enums import ArtistView
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __


def init_client():
    async def download_music(user_id: int, data: dict, bot: Bot):
        async with Bot(token=bot.token, session=bot_session).context(auto_close=False) as _bot:
            try:
                track = await shazam.track_about(track_id=data['track_id'])
                serialized = Serialize.track(track)
                try:
                    url, artist_id = await music_downloader(
                        title=serialized.title,
                        ringtone=serialized.ringtone
                    )
                except Exception as e:
                    await _bot.send_message(user_id, _("Не удалось загрузить песню\n{serialized}\n{e}").format(
                        serialized=serialized.title, e=e))
                    return
                bot_info = await bot.get_me()
                bot_username = bot_info.username
                btn = await artist_btn(artist_id=artist_id, key=data['track_id'])
                await add_to_analitic_data(bot_username, "music", ignore_domain=True)
                await _bot.send_chat_action(user_id, "upload_audio")
                await _bot.send_audio(
                    chat_id=user_id,
                    audio=URLInputFile(url, filename=f"{serialized.title}.mp3", timeout=150),
                    caption=_("{serialized_title} - {serialized_subtitle}\n Скачано через бота @{bot_username}").format(
                        serialized_title=serialized.title, serialized_subtitle=serialized.subtitle,
                        bot_username=bot_username),
                    title=f"{serialized.title}",
                    request_timeout=150,
                    performer=serialized.subtitle,
                    reply_markup=btn
                )
            except Exception as e:
                await _bot.send_message(user_id, _("Не удалось загрузить песню\n{e}").format(e=e))


    @client_bot_router.message(text=__("🔙 Назад"))
    async def music_menu(message: Message, state: FSMContext):
        await return_main(message, state)


    @client_bot_router.message(text=__("🎧 Музыка"))
    async def music_menu(message: Message, state: FSMContext):
        await state.clear()
        text = (
            _("👋 Привет\n\n"
              "🎧Я создан любителями музыки!\n\n"
              "🤖Я могу:\n\n"
              "🔝┏ Загрузить лучшую музыку\n"
              "🆕┣ Скачать новую музыку\n"
              "🤳┣ Воспроизведение музыки офлайн\n"
              "🔍┗ Загрузить музыку по вашему запросу\n\n"
              "‼️ Вместе со мной ты попадешь в мир музыки ‼️\n")
        )
        await message.answer(text, reply_markup=await music_main_menu())


    @client_bot_router.callback_query(callback_data.Artist.filter())
    async def artists_music(query: CallbackQuery, callback_data: callback_data.Artist):
        artist_id = int(callback_data.artist_id)
        about_artist = await shazam.artist_about(
            artist_id,
            query=ArtistQuery(
                views=[
                    ArtistView.TOP_SONGS,
                ],
            ),
        )
        try:
            serialized = Serialize.artist_v2(about_artist)
            tracks = []
            if len(serialized.data) <= 0:
                await query.answer(_("😔  Песен не найдено!"), show_alert=True)
                return

            for i in serialized.data[0].views.top_songs.data[:5]:
                tracks.append({
                    "key": i.attributes.play_params.id,
                    "title": i.attributes.name,
                    "subtitle": i.attributes.artist_name,
                    "ringtone": i.attributes.previews[0].url
                })

            btn = await artist_music_btn(tracks=tracks)
            await query.message.answer((_("🎵 Песни")), reply_markup=btn)
        except Exception as e:
            await query.message.answer(_("Не удалось получить данные"), )


    @client_bot_router.callback_query(callback_data.ArtistMusic.filter())
    async def artist_music(query: CallbackQuery, callback_data: callback_data.ArtistMusic):
        title = callback_data.title
        tracks = await shazam.search_track(query=title, limit=1)
        track_id = tracks["tracks"]["hits"][0]["key"]
        scheduler.add_job(download_music, args=(query.from_user.id, {
            "track_id": track_id,
        },), id=f"music-{query.from_user.id}-{track_id}", replace_existing=False, max_instances=1)
        await query.message.answer(text=_("Ваш запрос принят, ожидайте результата"))


    @client_bot_router.callback_query(callback_data.Lyrics.filter())
    async def lyrics(query: CallbackQuery, callback_data: dict):
        key = callback_data.key
        track = await shazam.track_about(track_id=key)
        serialized = Serialize.track(track)
        for section in serialized.sections:
            if section.type == "LYRICS":
                lyrics_text = "\n".join(section.text)
                await query.message.answer(lyrics_text)
                return
        await query.answer(_("😔Текст не найден!"), show_alert=True)


    @client_bot_router.message(text=__("🔥Чарт Музыка"), state="*")
    async def chart_music(message: Message):
        top_pop_in_the_world = await shazam.top_world_genre_tracks(
            genre=GenreMusic.POP, limit=10
        )
        btn = await chart_music_btn(top_pop_in_the_world)
        await message.answer((_("🔥Чарт Музыка")), reply_markup=btn)


    @client_bot_router.callback_query(callback_data.ChartMusic.filter(), state="*")
    async def chart_music_cb_handler(query: CallbackQuery, callback_data: callback_data.ChartMusic):
        key = callback_data.key
        offset = int(callback_data.offset)
        if key == "next_l":
            offset += 10
        elif key == "prev":
            offset -= 10
        else:
            if callback_data.download:
                scheduler.add_job(download_music, args=(query.from_user.id, {
                    "track_id": key,
                },), id=f"music-{query.from_user.id}-{key}", replace_existing=False, max_instances=1)
                await query.message.answer(text=_("Ваш запрос принят, ожидайте результата"))
            else:
                await query.message.answer(text=(_("Загрузить эту песню невозможно!!")))
            return

        top_pop_in_the_world = await shazam.top_world_genre_tracks(
            genre=GenreMusic.POP, limit=10, offset=offset
        )
        btn = await chart_music_btn(top_pop_in_the_world, offset=offset)
        await query.message.edit_reply_markup(reply_markup=btn)


    @client_bot_router.message(commands=["top"], state="*")
    @client_bot_router.message(text=__("🎙Лучшая музыка"), state="*")
    async def get_top_musics(message: Message, state: FSMContext):
        await state.clear()
        top_world_tracks = await shazam.top_world_tracks(limit=10)
        btn = await top_music_btn(top_world_tracks)
        await message.answer(text=(_("🎙Лучшая музыка")), reply_markup=btn)


    @client_bot_router.callback_query(callback_data.TopMusic.filter(), state="*")
    async def top_music_callback(call: CallbackQuery, callback_data: callback_data.TopMusic):
        offset = int(callback_data.offset)
        key = callback_data.key
        if key == "next_l":
            offset += 10
        elif key == "prev":
            offset -= 10
        else:
            if callback_data.download:
                scheduler.add_job(download_music, args=(call.from_user.id, {
                    "track_id": key,
                },), id=f"music-{call.from_user.id}-{key}", replace_existing=False, max_instances=1)
                await call.message.answer(text=_("Ваш запрос принят, ожидайте результата"))
            else:
                await call.message.answer(text=_("Не удалось загрузить"))
            return

        top_world_tracks = await shazam.top_world_tracks(limit=10, offset=offset)
        btn = await top_music_btn(top_world_tracks, offset=offset)
        await call.message.edit_reply_markup(reply_markup=btn)


    @client_bot_router.message(commands=["search"], state="*")
    @client_bot_router.message(text=__("🔍Поиск"), state="*")
    async def search_music(message: Message, state: FSMContext):
        await state.clear()
        await message.answer((_("🔍Введите поисковый запрос:")))
        await state.set_state(SearchMusic.waiting_for_music_name)


    @client_bot_router.message(state=SearchMusic.waiting_for_music_name)
    async def search_music_name(message: Message, state: FSMContext):
        await state.update_data(music_name=message.text)
        tracks = await shazam.search_track(query=message.text, limit=10)
        if len(tracks.keys()) > 0:
            await message.answer(text=(_("🔍Поиск")), reply_markup=await search_music_btn(tracks))
            await state.set_state(SearchMusic.waiting_for_music_choice)
        else:
            await message.answer(text=_("Песни не найдены!\n\nПопробуйте другой запрос!"))


    @client_bot_router.callback_query(callback_data.SearchMusic.filter(), state=SearchMusic.waiting_for_music_choice)
    async def search_music_cb_handler(query: CallbackQuery, callback_data: callback_data.SearchMusic, state: FSMContext):
        key = callback_data.key
        offset = int(callback_data.offset)
        if key == "next_l":
            offset += 10
        elif key == "prev":
            offset -= 10
        else:
            if callback_data.download:
                scheduler.add_job(download_music, args=(query.from_user.id, {
                    "track_id": key,
                },), id=f"music-{query.from_user.id}-{key}", replace_existing=False, max_instances=1)
                await query.message.answer(text=_("Ваш запрос принят, ожидайте результата"))
            else:
                await query.message.answer(text=_("Загрузить эту песню невозможно!!"))
            return
        data = await state.get_data()
        tracks = await shazam.search_track(
            query=data.get("music_name"), limit=10, offset=offset
        )
        try:
            await query.message.edit_reply_markup(reply_markup=await search_music_btn(tracks, offset=offset))
        except:
            await query.message.answer(query.message.text, reply_markup=await search_music_btn(tracks, offset=offset))


    @client_bot_router.message(commands=["new"], state="*")
    @client_bot_router.message(text=__("🎧Новые песни"), state="*")
    async def new_music(message: Message):
        new_music = await shazam.related_tracks(track_id=549952578, limit=10)
        btn = await new_music_btn(new_music)
        await message.answer(text=_("🎧Новые песни"), reply_markup=btn)


    @client_bot_router.callback_query(callback_data.NewMusic.filter(), state="*")
    async def new_music_cb_handler(query: CallbackQuery, callback_data: callback_data.NewMusic):
        key = callback_data.key
        offset = int(callback_data.offset)
        if key == "next_l":
            offset += 10
        elif key == "prev":
            offset -= 10
        else:
            if callback_data.download:
                scheduler.add_job(download_music, args=(query.from_user.id, {
                    "track_id": key,
                }), id=f"music-{query.from_user.id}-{key}", replace_existing=False, max_instances=1)
                await query.message.answer(text=_("Ваш запрос принят, ожидайте результата"))
            else:
                await query.message.answer(text=_("Загрузить эту песню невозможно!!"))
            return

        new_music = await shazam.related_tracks(track_id=549952578, limit=10, offset=offset)
        btn = await new_music_btn(new_music, offset=offset)
        await query.message.edit_reply_markup(reply_markup=btn)
