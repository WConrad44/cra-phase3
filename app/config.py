import os

API_TOKEN = os.getenv("API_TOKEN", "dev-token")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cra.db")
MAX_BODY_BYTES = 64 * 1024
