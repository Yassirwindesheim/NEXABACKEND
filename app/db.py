import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Load .env variables before anything else
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# ✅ ensure it uses asyncpg (avoid psycopg2 import errors)
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Create async session factory
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Dependency to get DB session
async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
