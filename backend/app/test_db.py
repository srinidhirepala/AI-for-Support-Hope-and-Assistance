from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Find ASHA/.env from backend/app/test_db.py
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

import os

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Using .env: {ENV_FILE}")
print(f"Database URL found: {DATABASE_URL is not None}")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database();"))
        database_name = result.scalar()

        print("✅ Database connection successful!")
        print(f"Connected to: {database_name}")

except Exception as e:
    print("❌ Database connection failed!")
    print(e)