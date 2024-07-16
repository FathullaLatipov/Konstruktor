from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from shazamio import Serialize
from modul.clientbot.handlers.music.data.callback_data import Artist, ArtistMusic, ChartMusic, Lyrics, NewMusic, SearchMusic, \
    TopMusic


async def top_music_btn(tracks, offset=0):
    markup = InlineKeyboardBuilder()
    for track in tracks["tracks"]:
        serialized = Serialize.track(track)
        text = f"{serialized.title} - {serialized.subtitle}"
        cb = TopMusic(key=serialized.key, offset=offset, download=True).pack()

        if serialized.ringtone is None:
            text = "❌ " + text
            cb = TopMusic(key=serialized.key, offset=offset, download=False).pack()

        markup.row(InlineKeyboardButton(text=text, callback_data=cb), width=1)
    nav = [InlineKeyboardButton(text="➡️", callback_data=TopMusic(key="next_l", offset=offset, download=False).pack())]
    if offset != 0:
        nav.insert(0, InlineKeyboardButton(text="⬅️",
                                           callback_data=TopMusic(key="prev", offset=offset, download=False).pack()))
    markup.row(*nav, width=2)

    return markup.as_markup()


async def chart_music_btn(tracks, offset=0):
    markup = InlineKeyboardBuilder()
    for track in tracks["tracks"]:
        serialized = Serialize.track(track)
        text = f"{serialized.title} - {serialized.subtitle}"
        cb = ChartMusic(key=serialized.key, offset=offset, download=True).pack()

        if serialized.ringtone is None:
            text = "❌ " + text
            cb = ChartMusic(key=serialized.key, offset=offset, download=False).pack()

        markup.row(InlineKeyboardButton(text=text, callback_data=cb), width=1)

    nav = [InlineKeyboardButton(text="➡️", callback_data=ChartMusic(key="next_l", offset=offset, download=False).pack())]
    if offset != 0:
        nav.insert(0, InlineKeyboardButton(text="⬅️",
                                           callback_data=ChartMusic(key="prev", offset=offset, download=False).pack()))
    markup.row(*nav, width=2)

    return markup.as_markup()


async def new_music_btn(tracks, offset=0):
    markup = InlineKeyboardBuilder()
    for track in tracks["tracks"]:
        serialized = Serialize.track(track)
        text = f"{serialized.title} - {serialized.subtitle}"
        cb = NewMusic(key=serialized.key, offset=offset, download=True).pack()

        if serialized.ringtone is None:
            text = "❌ " + text
            cb = NewMusic(key=serialized.key, offset=offset, download=False).pack()

        markup.row(InlineKeyboardButton(text=text, callback_data=cb), width=1)

    if len(tracks["tracks"]) == 0:
        return markup

    nav = [InlineKeyboardButton(text="➡️", callback_data=NewMusic(key="next_l", offset=offset, download=False).pack())]
    if offset != 0:
        nav.insert(0, InlineKeyboardButton(text="⬅️",
                                           callback_data=NewMusic(key="prev", offset=offset, download=False).pack()))
    markup.row(*nav, width=2)

    return markup.as_markup()


async def search_music_btn(tracks, offset=0):
    markup = InlineKeyboardBuilder()
    if 'tracks' in tracks:
        for track in tracks["tracks"]["hits"]:
            text = track["share"]["subject"]
            cb = SearchMusic(key=track['key'], offset=offset, download=True).pack()
            if 'apple' not in track["stores"] or 'previewurl' not in track["stores"]["apple"]:
                text = "❌ " + text
                cb = SearchMusic(
                    key=track['key'], offset=offset, download=False
                ).pack()

            markup.row(InlineKeyboardButton(text=text, callback_data=cb), width=1)

    nav = [InlineKeyboardButton(text="➡️", callback_data=SearchMusic(key="next_l", offset=offset, download=False).pack())]
    if offset != 0:
        nav.insert(0, InlineKeyboardButton(text="⬅️",
                                           callback_data=SearchMusic(key="prev", offset=offset, download=False).pack()))
    markup.row(*nav, width=2)

    return markup.as_markup()


async def artist_btn(artist_id, key=None):
    markup = InlineKeyboardBuilder()
    cb = Artist(artist_id=artist_id).pack()
    markup.add(InlineKeyboardButton(text="👤 Performers", callback_data=cb))
    if key is not None:
        markup.row(InlineKeyboardButton(text="📃 Lyrics", callback_data=Lyrics(key=key).pack()), width=1)
    return markup.as_markup()


async def artist_music_btn(tracks: list[dict]):
    markup = InlineKeyboardBuilder()
    for track in tracks:
        markup.row(InlineKeyboardButton(text=f"{track['title']} - {track['subtitle']}",
                                        callback_data=ArtistMusic(title=track['title']).pack()), width=1)
    return markup.as_markup()
