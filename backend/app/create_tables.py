from app.database import initialize_database


print("Creating ASHA database tables...")

initialize_database()

print("✅ Tables created successfully!")