from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional

# SQLAlchemy imports
from sqlalchemy import Column, Float, String, DateTime, Integer, select, create_engine
from sqlalchemy.orm import Session, Mapped, mapped_column, DeclarativeBase, MappedAsDataclass


@dataclass
class email:
    send_alerts: bool
    src: str
    dst: list[str]
    email_key: str


@dataclass
class sms:
    send_alerts: bool
    src: str
    dst: list[str]
    twilio_account_sid: str
    twilio_auth_token: str


@dataclass
class Config:
    urls: list[str]
    email: email
    sms: sms
    db_user: str
    db_password: str

# format is postgresql://username:password@host:port/database


# format is postgresql://username:password@host:port/database
def get_engine(user: str = 'postgres', password: str = 'password', host: str = 'localhost', port: str = '5432', database: str = 'craigslist', echo: bool = False):
    SQLALCHEMY_DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{database}'
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=echo)
    return engine


class Base(MappedAsDataclass, DeclarativeBase):
    pass


def get_db(table_name: str):
    class db_listing_entry(Base):
        __tablename__ = f'cl_table_{table_name}'
        id: Mapped[int] = mapped_column(Integer, init=False,  primary_key=True)
        link: Mapped[str] = mapped_column(String)
        title: Mapped[str] = mapped_column(String)
        cl_id: Mapped[str] = mapped_column(String)
        screenshot_path: Mapped[Optional[str]] = mapped_column(String)
        time_posted: Mapped[str] = mapped_column(String)
        location: Mapped[str] = mapped_column(String)
        time_scraped: Mapped[str] = mapped_column(String)

        def __repr__(self):
            return f'link: {self.link}\ntitle: {self.title}\nid: {self.cl_id}\nscreenshot_path: {self.screenshot_path}\ntime_posted: {self.time_posted}\nlocation: {self.location}\ntime_scraped: {self.time_scraped}'

    return db_listing_entry
