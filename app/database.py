# database.py
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Session, create_engine


# Твои настройки (вынеси их сюда же)
class Setting(BaseSettings):
    db: str
    key: str
    postgres_password: str
    model_config = SettingsConfigDict(env_file=".env")


setting = Setting()  # type: ignore
engine = create_engine(setting.db)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
