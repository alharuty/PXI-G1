import os
from openai import OpenAI as GroqClient
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = GroqClient(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_summary(prompt: str, language: str = "en") -> str:
    full_prompt = (
        f"You are a financial analyst. Based on the following prompt, "
        f"generate a detailed and informative financial article in {language}.\n\n"
        f"Do not explain what language you're using. Output the result only with the newest information you have and exactly what the user asks you..\n\n"
        f"Prompt: {prompt}"
    )

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()
