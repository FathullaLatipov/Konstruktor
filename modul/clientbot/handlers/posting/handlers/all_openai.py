import os
from openai import OpenAI
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

api_key = env_vars.get("API_KEY")

client = OpenAI(api_key=api_key)

OPENAI_COMPLETION_OPTIONS = {
    "temperature": 0.1,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "timeout": 60.0,
}


class ChatGPT:
    user_contexts = {}

    def update_context(self, user_id, message):
        if user_id in self.user_contexts:
            self.user_contexts[user_id].append(message)
        else:
            self.user_contexts[user_id] = []
            self.user_contexts[user_id].append(message)

    def get_all_contexts(self, user_id):
        if user_id in self.user_contexts:
            result = self.user_contexts[user_id]
            return result
        return None

    def chat_gpt(self, user_id, message, gpt='gpt-3.5-turbo-1106', context=False):
        if context is False:

            try:
                response = client.chat.completions.create(
                    model=gpt,
                    messages=[{"role": "system", "content": "Ты профессиональный Контент-менеджер"},
                              {"role": "user", "content": f"Напиши  пост на тему {message}"}],
                    **OPENAI_COMPLETION_OPTIONS
                )

                print(f'user_id: {user_id} send --> {message}\n'
                      f'assistant: {response.choices[0].message.content}')

                return response.choices[0].message.content

            except Exception as e:
                print(e)
        elif context is True:
            user_context = self.get_all_contexts(user_id)
            if user_context:

                var = user_context + [{"role": "user", "content": message}]

                response = client.chat.completions.create(
                    model=gpt,
                    messages=var,
                    **OPENAI_COMPLETION_OPTIONS
                )

                self.update_context(user_id, {"role": "user", "content": message})
                self.update_context(user_id, {"role": "assistant", "content": response.choices[0].message.content})

                print(f'user_id: {user_id} all_chat: {self.get_all_contexts(user_id)}')
                return response.choices[0].message.content

            else:
                try:
                    response = client.chat.completions.create(
                        model=gpt,
                        messages=[{"role": "user", "content": message}],
                        **OPENAI_COMPLETION_OPTIONS
                    )
                    self.update_context(user_id, {"role": "user", "content": message})
                    self.update_context(user_id, {"role": "assistant", "content": response.choices[0].message.content})

                    print(f'user_id: {user_id} start -- > {self.get_all_contexts(user_id)}')
                    return response.choices[0].message.content

                except:
                    return None

    def chat_gpt_for_post(self, user_id, message, count, gpt='gpt-3.5-turbo-1106', context=False):
        if context is False:

            try:
                response = client.chat.completions.create(
                    model=gpt,
                    messages=[{"role": "system", "content": "Ты профессиональный Контент-менеджер"},
                              {"role": "user", "content": f'Напиши {count} постов на тему {message} и выдавал в формате Пост 1. тема поста и так далее, и без приветствия,и без \n и отступов'}],
                    **OPENAI_COMPLETION_OPTIONS
                )

                print(f'user_id: {user_id} send --> {message}\n'
                      f'assistant: {response.choices[0].message.content}')

                return response.choices[0].message.content

            except Exception as e:
                print(e)
        elif context is True:
            user_context = self.get_all_contexts(user_id)
            if user_context:

                var = user_context + [{"role": "user", "content": message}]

                response = client.chat.completions.create(
                    model=gpt,
                    messages=var,
                    **OPENAI_COMPLETION_OPTIONS
                )

                self.update_context(user_id, {"role": "user", "content": message})
                self.update_context(user_id, {"role": "assistant", "content": response.choices[0].message.content})

                print(f'user_id: {user_id} all_chat: {self.get_all_contexts(user_id)}')
                return response.choices[0].message.content

            else:
                try:
                    response = client.chat.completions.create(
                        model=gpt,
                        messages=[{"role": "user", "content": message}],
                        **OPENAI_COMPLETION_OPTIONS
                    )
                    self.update_context(user_id, {"role": "user", "content": message})
                    self.update_context(user_id, {"role": "assistant", "content": response.choices[0].message.content})

                    print(f'user_id: {user_id} start -- > {self.get_all_contexts(user_id)}')
                    return response.choices[0].message.content

                except:
                    return None

    def text_to_picture(self, promt):

        try:
            response = client.images.generate(model="dall-e-3", prompt=promt, n=1, size="1024x1024", quality="standard")
            return response

        except:
            pass

    def text_to_picture_for_post(self, promt, count, user_id):
        img = {user_id: []}
        try:
            for i in range(count):
                response = client.images.generate(model="dall-e-3", prompt=promt, n=1, size="1024x1024", quality="standard")
                img[user_id].append(response.data[0].url)
            return img[user_id]

        except:
            pass

    def edit_picture(self, image):
        response = client.images.create_variation(
            image=open(image, "rb"),
            n=2
        )

        image_url = response.data[0].url
        response.close()
        os.remove(image)
        return image_url

    def audio_to_text(self, audio_name):

        try:
            audio_file = open(audio_name, "rb")
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            audio_file.close()
            os.remove(audio_name)
            return transcript

        except:
            pass

    def text_to_audio(self, voice, text):

        try:
            response = client.audio.speech.create(model="tts-1", voice=voice, input=text)
            return response

        except:
            pass
