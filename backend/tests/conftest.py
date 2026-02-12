import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base

os.environ.update(
    {
        'DATABASE_URL': 'sqlite+aiosqlite:///test.db',
        'REDIS_URL': 'redis://localhost:6379/1',
        'JWT_SECRET_KEY': 'test-secret-key-minimum-32-chars-long',
        'POSTGRES_PASSWORD': 'test',
        'DB_PASSWORD': 'test',
        'DEMO_UNLOCK_CODE': '314159',
        'FULL_TELEGRAM_IDS': '111111',
        'DEMO_TELEGRAM_IDS': '222222',
    }
)


@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine('sqlite+aiosqlite:///test.db', echo=False)
    import app.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        yield client
