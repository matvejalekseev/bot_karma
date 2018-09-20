from messages import MESSAGES
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from db_map import Users, Chats, Karma, MediaIds
from conf import DB_FILENAME, MY_ID

engine = create_engine(f'sqlite:///{DB_FILENAME}')
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def is_str(s):
    if s is None or s == 'None' or s == '':
        return False
    else:
        return True


def is_admin_in_chat(id, chat_id):
    if id == MY_ID:
        return True
    else:
        if Session.query(Karma).filter(and_(Karma.user_id == id, Karma.status == 1, Karma.chat_id == chat_id)).one():
            return True
        else:
            return False


def add_user_chat(user, chat):
    if not Session.query(Users).filter(Users.user_id == user.id).all():
        user_current = Users(user_id=user.id, name=user.full_name, username=user.username)
        session = Session()
        try:
            session.add(user_current)
            session.commit()
        finally:
            session.close()
    if not Session.query(Karma).filter(and_((Karma.user_id == user.id), (Karma.chat_id == chat.id))).all():
        karma = Karma(user_id=user.id, chat_id=chat.id)
        session = Session()
        try:
            session.add(karma)
            session.commit()
        finally:
            session.close()


def prettyUsername(n,un):
    try:
        if is_str(un):
            user = '<a href="https://t.me/' + un +'">' + n + '</a>'
        else:
            user = n
        return user
    except:
        return MESSAGES['error']