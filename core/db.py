import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL oder SUPABASE_KEY ist nicht gesetzt!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
