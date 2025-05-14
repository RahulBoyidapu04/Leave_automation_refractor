import openai
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Set API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Simple test call
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
    ]
)

print(response['choices'][0]['message']['content'])
