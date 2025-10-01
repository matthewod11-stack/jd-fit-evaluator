from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    gh_token: str | None = os.getenv("GH_TOKEN")
    gh_job_id: str | None = os.getenv("GH_JOB_ID")
    embed_model_path: str | None = os.getenv("EMBED_MODEL_PATH")
    embed_ctx: int = int(os.getenv("EMBED_CTX", "4096"))

settings = Settings()
