import urllib3
from pytube import YouTube
from shazamio import Serialize
from loader import shazam

async def music_downloader(title: str, ringtone: str):
    recognized_track = await shazam.recognize_song(urllib3.PoolManager().request('GET', ringtone).data)
    result = Serialize.full_track(data=recognized_track)
    artist_id = recognized_track['track']['artists'][0]['adamid']
    youtube_data = await shazam.get_youtube_data(link=result.track.youtube_link)
    serialized_youtube = Serialize.youtube(data=youtube_data)
    yt = YouTube(serialized_youtube.uri)
    return yt.streams.filter(only_audio=True).get_audio_only().url, artist_id