import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# --- Construct the Database URL using environment variables ---
# Using f-string for clear assembly
safe_password = quote_plus(DB_PASSWORD)
DATABASE_URL = (
    f"postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# db_url = "postgresql://postgres:Keval%40postgre015@localhost:5432/EventManagement"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit = False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()