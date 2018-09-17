from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Numeric, unique=True)
    username = Column('username', String(255))
    name = Column('name', String(255))
    status = Column('status', Integer) # 0 - Пользователь, 1 - Админ

    def __init__(self, user_id, username=None, name=None, status=0):
        self.user_id = user_id
        self.name = name
        self.username = username
        self.status = status

    def set_name(self, name):
        self.name = name

    def set_username(self, username):
        self.username = username

class Chats(Base):
    __tablename__ = 'Chats'
    id = Column(Integer, primary_key=True)
    chat_id = Column('chat_id', Numeric, unique=True)
    name = Column('name', String(255))
    status = Column('status', Integer)

    def __init__(self, chat_id, name=None, status=0):
        self.chat_id = chat_id
        self.name = name
        self.status = status

    def set_name(self, name):
        self.name = name

class Karma(Base):
    __tablename__ = 'Karma'
    id = Column(Integer, primary_key=True)
    chat_id = Column('chat_id', Numeric, ForeignKey('Chats.chat_id'))
    user_id = Column('user_id', Numeric, ForeignKey('Users.user_id'))
    karma = Column('karma', Integer)
    __table_args__ = (UniqueConstraint('user_id', 'chat_id', name='_chat_event_uc'),)

    def __init__(self, chat_id, user_id, karma=0):
        self.chat_id = chat_id
        self.user_id = user_id
        self.karma = karma

class MediaIds(Base):
    __tablename__ = 'MediaIds'
    id = Column(Integer, primary_key=True)
    media_id = Column('media_id', String(255), unique=True)
    type = Column('type', String(255))
    caption = Column('caption', String(255))
    json = Column('json', String(255))

    def __init__(self, media_id, type, json, caption=None):
        self.media_id = media_id
        self.type = type
        self.json = json
        self.caption = caption