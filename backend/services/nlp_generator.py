import os
from openai import OpenAI as GroqClient

client = GroqClient(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def generate_summary(prompt: str, language: str = "en") -> str:
    full_prompt = f"Summarize this financial text in {language}:\n\n{prompt}"

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()
