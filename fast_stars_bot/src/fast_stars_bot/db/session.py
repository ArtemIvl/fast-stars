from config.settings import settings
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

engine = create_async_engine(
    settings.DB_URL,
    echo=False,
    pool_size=50,         
    max_overflow=50,      
    pool_pre_ping=True
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
