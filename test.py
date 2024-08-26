import os
from config import Config

from openai import OpenAI

api_key=Config.OPENAI_API_KEY
api_model=Config.OPENAI_MODEL

client = OpenAI(api_key=api_key)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ], model=api_model
)
# Извлечение первого (и единственного) выбора
first_choice = chat_completion.choices[0]

# Извлечение текста сообщения
message_content = first_choice.message.content

# Печать сообщения
print(message_content)