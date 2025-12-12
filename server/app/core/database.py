from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class (we use this to create DB sessions)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Dependency to get DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
