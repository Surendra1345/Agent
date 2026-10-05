import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

api_key = os.getenv("Api-Key") or os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OpenRouter API key (Api-Key) is not set in the environment")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))
TEMPERATURE = 0