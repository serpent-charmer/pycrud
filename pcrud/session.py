import os
from typing import Annotated
from fastapi import Depends

from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

DB_URL = os.getenv("DB_URL") or "127.0.0.1"
DATABASE_URL = f"postgresql+asyncpg://crud_admin:password@{DB_URL}/crud_project"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_version(myses: SessionDependency):
    stmt = text("SELECT VERSION()")
    result = await myses.execute(stmt)
    return {"message": result.scalars().one()}
