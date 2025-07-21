import os

from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

env_file = Path(".env")
if env_file.exists():
    load_dotenv(override=True)


def get_supabase_client():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials missing")
    return create_client(SUPABASE_URL, SUPABASE_KEY)
