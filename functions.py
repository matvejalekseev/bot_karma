from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from messages import MESSAGES
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import scoped_session, sessionmaker
from db_map import Users, Chats, Karma, Votings, Votes, Triggers
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


def prettyUsername(n, un):
    try:
        if is_str(un):
            user = '<a href="https://t.me/' + un + '">' + n + '</a>'
        else:
            user = n
        return user
    except:
        return MESSAGES['error']


def pagination_voting(code, chat_id, user_id, limit, type_vote, type_step):
    if type_step == 'next':
        users = Session.query(Karma).filter(and_((Karma.chat_id == chat_id),
                                                 (Karma.user_id != user_id),
                                                 (Karma.id > code))).order_by(Karma.id).limit(limit).all()
    else:
        users = Session.query(Karma).filter(and_((Karma.chat_id == chat_id),
                                                 (Karma.user_id != user_id),
                                                 (Karma.id <= code))).order_by(Karma.id).limit(limit).all()
    count_next = Session.query(Karma).filter(and_((Karma.chat_id == chat_id),
                                             (Karma.user_id != user_id),
                                             (Karma.id > code))).count()
    count_prev = Session.query(Karma).filter(and_((Karma.chat_id == chat_id),
                                                (Karma.user_id != user_id),
                                                (Karma.id <= code))).count()
    count = Session.query(Karma).filter(and_((Karma.chat_id == chat_id),
                                                  (Karma.user_id != user_id))).count()
    if type_vote == '1':
        command = 'like-'
    else:
        command = 'dislike-'
    inline_kb = InlineKeyboardMarkup(row_width=1)
    for user in users:
        current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
        inline_btn = InlineKeyboardButton(current_user.name, callback_data=command + str(round(user_id)) + '-'
                                                                          + str(round(current_user.user_id)))
        inline_kb.add(inline_btn)
    if code == 0:
        inline_btn_1 = InlineKeyboardButton(' ', callback_data='none')
    elif count_prev <= limit and type_step == 'prev':
        inline_btn_1 = InlineKeyboardButton(' ', callback_data='none')
    else:
        inline_btn_1 = InlineKeyboardButton('<', callback_data='prev-' + str(round(user_id)) + '-' + str(code)
                                                               + '-' + str(type_vote))
    inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
    if count_next > limit or type_step == 'prev':
        inline_btn_3 = InlineKeyboardButton('>', callback_data='next-' + str(round(user_id)) + '-'
                                                               + str(round(user.id))
                                                               + '-' + str(type_vote))
    else:
        inline_btn_3 = InlineKeyboardButton(' ', callback_data='none')
    if count > limit:
        inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
    return inline_kb


def current_state_vote(time, vote_id, end=0):
    voting = Session.query(Votings).filter(Votings.id == vote_id).one()

    user = Session.query(Users).filter(Users.user_id == voting.init_user_id).one()
    user_prettyname = prettyUsername(user.name, user.username)

    likes = Session.query(Users).filter(Users.user_id == voting.candidate_user_id).one()
    likes_prettyname = prettyUsername(likes.name, likes.username)

    users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
    users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
    yes_list = ''
    for user in users_yes:
        current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
        yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)

    count_user_in_chat = Session.query(Karma).filter(Karma.chat_id == voting.chat_id).count()
    no_list = ''
    for user in users_no:
        current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
        no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)

    inline_kb = InlineKeyboardMarkup(row_width=1)
    inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-' + str(vote_id))
    inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-' + str(vote_id))
    inline_kb.add(inline_btn_yes, inline_btn_no)
    if voting.type == 1:
        if end == 1 or count_user_in_chat == len(users_yes) + len(users_no) + 1:
            if result_votes(vote_id):
                text = MESSAGES['like_result_yes'].format(likes=likes_prettyname,
                                                          yes=str(len(users_yes)),
                                                          no=str(len(users_no)),
                                                          list_yes=yes_list,
                                                          list_no=no_list)
            else:
                text = MESSAGES['like_result_no'].format(likes=likes_prettyname,
                                                         yes=str(len(users_yes)),
                                                         no=str(len(users_no)),
                                                         list_yes=yes_list,
                                                         list_no=no_list)
            return text, None
        else:
            text = MESSAGES['like_select'].format(user=user_prettyname,
                                                  likes=likes_prettyname,
                                                  yes=str(len(users_yes)),
                                                  no=str(len(users_no)),
                                                  list_yes=yes_list,
                                                  list_no=no_list,
                                                  time=time)
            return text, inline_kb
    else:
        if end == 1 or count_user_in_chat == len(users_yes) + len(users_no) + 1:
            if result_votes(vote_id):
                text = MESSAGES['dislike_result_yes'].format(likes=likes_prettyname,
                                                          yes=str(len(users_yes)),
                                                          no=str(len(users_no)),
                                                          list_yes=yes_list,
                                                          list_no=no_list)
            else:
                text = MESSAGES['dislike_result_no'].format(likes=likes_prettyname,
                                                         yes=str(len(users_yes)),
                                                         no=str(len(users_no)),
                                                         list_yes=yes_list,
                                                         list_no=no_list)
            return text, None
        else:
            text = MESSAGES['dislike_select'].format(user=user_prettyname,
                                                  likes=likes_prettyname,
                                                  yes=str(len(users_yes)),
                                                  no=str(len(users_no)),
                                                  list_yes=yes_list,
                                                  list_no=no_list,
                                                  time=time)
            return text, inline_kb


def karma_in_chat_text(chat_id, time):
    text = ''
    i = 1
    chat = Session.query(Chats).filter(Chats.chat_id == chat_id).one()
    max = Session.query(func.max(Karma.karma).label('max')).filter(Karma.chat_id == chat_id).one().max
    min = Session.query(func.min(Karma.karma).label('min')).filter(Karma.chat_id == chat_id).one().min
    for karma in Session.query(Karma).filter(Karma.chat_id == chat_id).order_by(Karma.karma.desc()).all():
        user = Session.query(Users).filter(Users.user_id == karma.user_id).one()
        if karma.karma == max:
            text = text + '\n👑 ' + MESSAGES['user_karma'].format(name=prettyUsername(user.name, user.username),
                                                                  karma=str(karma.karma))
        elif karma.karma == min:
            text = text + '\n💩 ' + MESSAGES['user_karma'].format(name=prettyUsername(user.name, user.username),
                                                                  karma=str(karma.karma))
        else:
            text = text + '\n' + MESSAGES['user_karma'].format(name=prettyUsername(user.name, user.username),
                                                               karma=str(karma.karma))
        i += 1
    return MESSAGES['delete_template'].format(text=MESSAGES['karma'].format(name=chat.name, text=text),
                                              time=time)


def new_trigger(name, text, chat_id, media_id, type):
    if not Session.query(Triggers).filter(and_((Triggers.name == name), (Triggers.chat_id == chat_id))).all():
        trigger_current = Triggers(chat_id=chat_id, name=name.lower(), text=text, media_id=media_id, type=type)
        session = Session()
        try:
            session.add(trigger_current)
            session.commit()
        finally:
            session.close()
    else:
        session = Session()
        trigger_current = session.query(Triggers).filter(and_((Triggers.name == name), (Triggers.chat_id == chat_id)))\
            .one()
        trigger_current.text = text.lower()
        trigger_current.media_id = media_id
        trigger_current.type = type
        try:
            session.commit()
        finally:
            session.close()


def triggers_list(chat_id):
    text = ''
    list = Session.query(Triggers).filter(Triggers.chat_id == chat_id).all()
    if len(list) > 0:
        for trigger in list:
            text = text + '!' + trigger.name + '\n'
        return MESSAGES['triggers_list'].format(text=text)
    else:
        return MESSAGES['empty_triggers_list']


def trigger(name, chat_id):
    if Session.query(Triggers).filter(and_((Triggers.name == name), (Triggers.chat_id == chat_id))).all():
        session = Session()
        trigger_current = session.query(Triggers).filter(and_((Triggers.name == name), (Triggers.chat_id == chat_id))) \
            .one()
        return trigger_current
    else:
        return None


def delete_trigger(name, chat_id):
    if Session.query(Triggers).filter(and_((Triggers.name == name), (Triggers.chat_id == chat_id))).all():
        Session.query(Triggers).filter(and_((Triggers.name == name), (Triggers.chat_id == chat_id))).delete()
        Session.commit()


def change_chat_status(chat_id, status):
    if Session.query(Chats).filter(Chats.chat_id == chat_id).all():
        session = Session()
        chat = session.query(Chats).filter(Chats.chat_id == chat_id).one()
        chat.status = status
        try:
            session.commit()
        finally:
            session.close()


def chat_status(chat_id):
    if Session.query(Chats).filter(Chats.chat_id == chat_id).all():
        chat = Session.query(Chats).filter(Chats.chat_id == chat_id).one()
        return chat.status