import asyncio
import uuid
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database.models import Base, User, UserRole, Flag, Experiment, ExperimentStatus

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@pytest.fixture
async def session():
    async with SessionLocal() as s:
        yield s
        await s.rollback()

@pytest.fixture
async def users(session):
    admin = User(email="admin@test", hashed_password="x", full_name="Admin", role=UserRole.ADMIN)
    exp = User(email="exp@test", hashed_password="x", full_name="Exp", role=UserRole.EXPERIMENTER, min_approvals_required=2)
    appr = User(email="appr@test", hashed_password="x", full_name="Appr", role=UserRole.APPROVER)
    exp.allowed_approvers.append(appr)

    session.add_all([admin, exp, appr])
    await session.commit()
    return admin, exp, appr

@pytest.fixture
async def flag(session):
    f = Flag(key="checkout_btn", default_value={"enabled": False})
    session.add(f)
    await session.commit()
    return f