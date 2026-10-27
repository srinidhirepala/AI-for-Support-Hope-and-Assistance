from sqlalchemy import text

from app.database import DATABASE_URL, engine

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

        print("Database connection successful.")
        print(f"Connected using: {DATABASE_URL.split(':', 1)[0]}")

except Exception as error:
    print("Database connection failed.")
    print(error)
    raise