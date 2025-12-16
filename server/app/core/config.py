import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
	# Core settings
	DATABASE_URL: str | None = os.getenv("DATABASE_URL")

	# LLM settings (global for all clients)
	LLM_MODEL: str = os.getenv("LLM_MODEL", "GPT-5.1-Codex-Max")
	LLM_ENABLE_PREVIEW: bool = os.getenv("LLM_ENABLE_PREVIEW", "true").lower() == "true"
	LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gpt")


settings = Settings()
