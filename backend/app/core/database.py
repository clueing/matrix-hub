from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        # Enable WAL mode for high-concurrency SQLite
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.run_sync(Base.metadata.create_all)

        # 针对既有 accounts 表自适应追加粉丝数、点赞数、关注数字段
        res = await conn.execute(text("PRAGMA table_info(accounts);"))
        existing_cols = [r[1] for r in res.fetchall()]
        for col, col_type in [
            ("followers_count", "INTEGER DEFAULT 0"),
            ("likes_count", "INTEGER DEFAULT 0"),
            ("following_count", "INTEGER DEFAULT 0")
        ]:
            if col not in existing_cols:
                await conn.execute(text(f"ALTER TABLE accounts ADD COLUMN {col} {col_type};"))
