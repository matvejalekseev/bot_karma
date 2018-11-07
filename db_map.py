from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Numeric, unique=True)
    username = Column('username', String(255))
    name = Column('name', String(255))
    status = Column('status', Integer)# 0 - Пользователь, 1 - Админ
    last_advice = Column('last_advice', DateTime(timezone=True), default=func.now())
    count_advice = Column('count_requests', Integer, default=0)


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
    last_joke = Column('last_joke', DateTime(timezone=True), default=func.now())
    count_joke = Column('count_joke', Integer, default=0)

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


class Votings(Base):
    __tablename__ = 'Votings'
    id = Column(Integer, primary_key=True)
    chat_id = Column('chat_id', Numeric, ForeignKey('Chats.chat_id'))
    init_user_id = Column('init_user_id', Numeric, ForeignKey('Users.user_id'))
    candidate_user_id = Column('candidate_user_id', Numeric, ForeignKey('Users.user_id'))
    type = Column('type', Integer, default=1) #0 - Дизлайк, 1 - Лайк

    def __init__(self, id, chat_id, init_user_id, candidate_user_id, type):
        self.id = id
        self.chat_id = chat_id
        self.init_user_id = init_user_id
        self.candidate_user_id = candidate_user_id
        self.type = type


class Votes(Base):
    __tablename__ = 'Votes'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Numeric, ForeignKey('Users.user_id'))
    vote_id = Column('vote_id', Numeric, ForeignKey('Votings.id'))
    answer = Column('answer', Integer, default=1) #0 - Нет, 1 - Да

    def __init__(self, vote_id, user_id, answer):
        self.vote_id = vote_id
        self.user_id = user_id
        self.answer = answer


class Triggers(Base):
    __tablename__ = 'Triggers'
    id = Column(Integer, primary_key=True)
    chat_id = Column('chat_id', Numeric, ForeignKey('Chats.chat_id'))
    text = Column('text', String(4096))
    name = Column('name', String(30))
    type = Column('type', String(30))
    media_id = Column('media_id', String(100))

    def __init__(self, chat_id, text, name, type=None, media_id=None):
        self.chat_id = chat_id
        self.text = text
        self.name = name
        self.type = type
        self.media_id = media_id