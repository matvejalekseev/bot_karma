from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MediaIds(Base):
    __tablename__ = 'MediaIds'
    id = Column(Integer, primary_key=True)
    file_id = Column('file_id', String(255))
    filename = Column('filename', String(255))
    type = Column('type', Integer, ForeignKey('MediaTypes.id'), nullable=False)
    upload_date = Column('upload_date', DateTime)
    __table_args__ = (UniqueConstraint('type', 'filename', name='_type_file_uc'),)

    def __init__(self, file_id, filename, type):
        self.file_id = file_id
        self.filename = filename
        self.type = type
        self.upload_date = datetime.now()


class MediaTypes(Base):
    __tablename__ = 'MediaTypes'
    id = Column(Integer, primary_key=True)
    name = Column('name', String(255), unique=True)

    def __init__(self, name):
        self.name = name


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