import math
from typing import Dict, List
from bs4 import BeautifulSoup
from openai import OpenAI
from openai.types.chat import ChatCompletion
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
from pytube import YouTube

OPENAI_COMPLETION_OPTIONS = {
    "temperature": 0.1,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "timeout": 60.0,
}

PRICING = {
    "gpt4": {
        "with_context": 4,
        "without_context": 3,
        
        "cost_with_context": 0.003,
        "cost_without_context": 0.002,
    },
    "gpt3": {
        "with_context": 2,
        "without_context": 1,
    },
    "dalle": {
        "without_context": 12,
    },
    "assistant": {
        "without_context": 10,
    },
    "text-to-speech": {
        "without_context": 3,
    },
    "speech-to-text": {
        "without_context": 2,
    },
    "youtube_transcription": {
        "minutes": 10,
        "without_context": 2,
    },
    "google_search": {
        "without_context": 5,
    },
}

MODEL_TYPE = {
    "gpt4": "gpt-4-1106-preview",
    "gpt3": "gpt-3.5-turbo-1106",
    "dalle": "dall-e-3",
    "assistant": "",
    "youtube_transcription": "",
    "text-to-speech": "whisper-1",
    "speech-to-text": "tts-1",
}


class ChatGPT:
    openai: OpenAI
    user_contexts: Dict[int, List[str]] = {}
    def __init__(self, token: str):
        self.openai = OpenAI(api_key=token)
    
    def can_run(self, input: str):
        try:
            response = self.openai.moderations.create(
                input = input,
                timeout=10,
            )
            return not any([moder.flagged for moder in response.results])
        except Exception as e:
            raise Exception(f"OpenAI не ответил на запрос. Попробуйте позже. (Звездочки вернулись) ({e})")
    
    def update_context(self, user_id: int, message: str):
        if user_id in self.user_contexts:
            self.user_contexts[user_id].append(message)
        else:
            self.user_contexts[user_id] = []
            self.user_contexts[user_id].append(message)

    def get_all_contexts(self, user_id):
        return self.user_contexts.get(user_id)

    def chat_gpt(self, user_id: int, message: str, model: str = 'gpt-3.5-turbo-1106', context: bool = False):
        if not self.can_run(message):
            raise Exception("Ваш запрос был заблокирован модераторами.")
        msg_context = {"role": "user", "content": message}
        user_context = ((self.get_all_contexts(user_id) or []) if context else []) + [msg_context]  
        response: ChatCompletion = self.openai.chat.completions.create(
            model=model,
            messages=user_context,
            **OPENAI_COMPLETION_OPTIONS
        )
        response.usage.total_tokens
        if len(response.choices) > 0:
            answer = response.choices[0].message.content
            if context:
                self.update_context(user_id, msg_context)
                self.update_context(user_id, {"role": "assistant", "content": answer})
            return answer, response.usage.total_tokens

    def text_to_picture(self, promt):
        if not self.can_run(promt):
            raise Exception("Ваш запрос был заблокирован модераторами.")        
        response = self.openai.images.generate(model="dall-e-3", prompt=promt)
        return response

    def edit_picture(self, image_byres):
        response = self.openai.images.create_variation(
            image=image_byres,
            n=2
        )
        image_url = response.data[0].url
        return image_url

    def audio_to_text(self, audio_bytes):
        transcript = self.openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_bytes,
            response_format="text"
        )
        return transcript
    
    def text_to_audio(self, voice: str, text: str):
        if not self.can_run(text):
            raise Exception("Ваш запрос был заблокирован модераторами.")        
        response = self.openai.audio.speech.create(model="tts-1", voice=voice, input=text)
        return response
    
    @staticmethod
    def get_youtube_duration(link: str):
        yt = YouTube(link)
        return math.ceil(yt.length / 60)
            
    def extract_youtube_transcript(self, user_id, video_id):
        try:            
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en', 'ja', 'ko', 'de', 'fr', 'ru', 'zh-TW', 'zh-CN', 'zh-Hant', 'zh-Hans'])
            transcript_text = ' '.join([item['text'] for item in transcript.fetch()])
            result, tokens = self.chat_gpt(user_id=user_id, message=transcript_text+' summarize')
            return result
        except Exception as e:
            print(f"Error: {e}")
            raise Exception( "no transcript")
        
    def google_search(self, user_id, what):
        base_url = "https://www.google.com/search"
        params = {"q": what}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.select(".tF2Cxc")
            limited_results = results[:5]
            all_link = []
            for i in limited_results:
                all_link.append(i)
            return self.chat_gpt(user_id=user_id, message=f'Вопрос в том, {what}. Ответ такой: {all_link}. 1. Перефразируйте и ответьте на вопрос. 2. Составляйте пронумерованные ответы со ссылками.')
        except requests.exceptions.HTTPError as errh:
            print("HTTP Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("Error:", err)