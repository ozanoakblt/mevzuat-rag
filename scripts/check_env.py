from dotenv import load_dotenv
import os

load_dotenv()
key = os.environ.get("GEMINI_API_KEY")
print("GEMINI_API_KEY yuklendi mi:", bool(key))
print("Uzunluk:", len(key) if key else 0)
print("GROQ_API_KEY yuklendi mi (kontrol icin):", bool(os.environ.get("GROQ_API_KEY")))
