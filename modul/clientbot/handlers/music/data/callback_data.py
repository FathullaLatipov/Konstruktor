from aiogram.filters.callback_data import CallbackData

class TopMusic(CallbackData, prefix="top_music"):
    key: str
    offset: int
    download: bool


class ChartMusic(CallbackData, prefix="chart_music"):
    key: str
    offset: int
    download: bool


class NewMusic(CallbackData, prefix="new_music"):
    key: str
    offset: int
    download: bool


class SearchMusic(CallbackData, prefix="search_music"):
    key: str
    offset: int
    download: bool


class ArtistMusic(CallbackData, prefix="artist_music"):
    title: str


class Language(CallbackData, prefix="language"):
    language: str


class Artist(CallbackData, prefix="artist"):
    artist_id: int


class Lyrics(CallbackData, prefix="lyrics"):
    key: str