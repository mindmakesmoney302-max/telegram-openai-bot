
import os
import openai
import asyncio
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

async def get_openai_response(messages):
    try:
        response = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful assistant."}] + messages,
                max_tokens=300
            )
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
