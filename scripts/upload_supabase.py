# scripts/upload_supabase.py
from supabase import create_client
import os, pathlib

SUPABASE_URL = "https://<tu_project_ref>.supabase.co"
SUPABASE_KEY = "<tu_anon_or_service_key>"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET = "inventa-assets"
OUT_DIR = pathlib.Path("build")

for file in OUT_DIR.glob("*.lite.geojson"):
    with open(file, "rb") as f:
        path = f"data/{file.name}"
        supabase.storage.from_(BUCKET).upload(path, f, {"content-type": "application/geo+json"})
        public_url = supabase.storage.from_(BUCKET).get_public_url(path)
        print("Subido:", file.name)
        print("URL:", public_url)
