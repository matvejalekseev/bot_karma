from messages import MESSAGES
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import scoped_session, sessionmaker
from db_map import Users, Chats, Karma, Votings, Votes
from conf import DB_FILENAME, MY_ID, LIMIT_ADVICE, LIMIT_JOKE
from pytz import timezone
from datetime import datetime

engine = create_engine(f'sqlite:///{DB_FILENAME}')
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
UTC = timezone('UTC')

def date_now():
    return datetime.now(UTC).date()


def time_now():
    return datetime.now(UTC)


def is_str(s):
    if s is None or s == 'None' or s == '':
        return False
    else:
        return True


def advices_limit_counter(id):
    if id == MY_ID:
        return False
    else:
        if Session.query(Users).filter(Users.user_id == id).one():
            session = Session()
            user_current = session.query(Users).filter(Users.user_id == id).one()
            if user_current.last_advice.date() == date_now():
                if user_current.count_advice >= LIMIT_ADVICE:
                    return True
                else:
                    user_current.count_advice += 1
                    try:
                        session.commit()
                    finally:
                        session.close()
                    return False
            else:
                user_current.last_advice = time_now()
                user_current.count_advice = 1
                try:
                    session.commit()
                finally:
                    session.close()
                return False
        else:
            return True


def jokes_limit_counter(id):
    if Session.query(Chats).filter(Chats.chat_id == id).one():
        session = Session()
        chat_current = session.query(Chats).filter(Chats.chat_id == id).one()
        if chat_current.last_joke.date() == date_now():
            if chat_current.count_joke >= LIMIT_JOKE:
                return True
            else:
                chat_current.count_joke += 1
                try:
                    session.commit()
                finally:
                    session.close()
                return False
        else:
            chat_current.last_joke = time_now()
            chat_current.count_joke = 1
            try:
                session.commit()
            finally:
                session.close()
            return False
    else:
        return True


def vote(user, vote, answer):
    if Session.query(Votes).filter(and_(Votes.user_id == user, Votes.vote_id == vote)).all():
        return False
    else:
        vote = Votes(vote_id=vote, user_id=user, answer=answer)
        session = Session()
        try:
            session.add(vote)
            session.commit()
        finally:
            session.close()
        return True


def result_votes(vote):
    if Session.query(Votes).filter(Votes.vote_id == vote).all():
        yes = Session.query(Votes).filter(and_(Votes.answer == 1, Votes.vote_id == vote)).count()
        no = Session.query(Votes).filter(and_(Votes.answer == 0, Votes.vote_id == vote)).count()
        voting = Session.query(Votings).filter(Votings.id == vote).one()
        if yes > no and yes > 1:
            session = Session()
            karma = session.query(Karma).filter(and_((Karma.user_id == voting.candidate_user_id),
                                                     (Karma.chat_id == voting.chat_id))).one()
            if voting.type == 1:
                karma.karma += 1
            else:
                karma.karma -= 1
            try:
                session.commit()
            finally:
                session.close()
            return True
        else:
            return False
    else:
        return False


def new_voting(init, candidate, type, chat):
    try:
        id = Session.query(func.max(Votings.id).label('id')).one().id + 1
    except:
        id = 1
    voting = Votings(id=id, init_user_id=init, candidate_user_id=candidate, type=type, chat_id=chat)
    session = Session()
    try:
        session.add(voting)
        session.commit()
    finally:
        session.close()
    vote = Votes(vote_id=id, user_id=init, answer=1)
    session = Session()
    try:
        session.add(vote)
        session.commit()
    finally:
        session.close()
    return id


def add_user_chat(user, chat):
    if not Session.query(Users).filter(Users.user_id == user.id).all():
        user_current = Users(user_id=user.id, name=user.full_name, username=user.username)
        session = Session()
        try:
            session.add(user_current)
            session.commit()
        finally:
            session.close()
    else:
        session = Session()
        user_current = session.query(Users).filter(Users.user_id == user.id).one()
        user_current.username = user.username
        user_current.name = user.full_name
        try:
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
            user = '<a href="https://t.me/' + un + '">' + n + '</a>'
        else:
            user = n
        return user
    except:
        return MESSAGES['error']