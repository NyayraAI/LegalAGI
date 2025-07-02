import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
TABLE_NAME = "documents"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ Supabase client initialized successfully")
