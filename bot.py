from datetime import datetime

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ContentType
from aiogram.utils import executor
from aiogram.utils.markdown import bold
from sqlalchemy import create_engine, update, delete, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import asyncio
import logging
import os

from telebot.apihelper import leave_chat

from messages import MESSAGES
from conf import LOG_FILENAME, LOG_DIRECTORY, TOKEN, DB_FILENAME
from db_map import Users, Chats, Karma
from utils import AdminStates

from functions import *

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO)
loop = asyncio.get_event_loop()
bot = Bot(TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

engine = create_engine(f'sqlite:///{DB_FILENAME}')

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

current_shown_dates = {}


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(MESSAGES['help'], reply=False)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(MESSAGES['start'], reply=False)


@dp.message_handler(commands=['like'])
async def process_like_command(message: types.Message):
    me = await dp.bot.me
    from_user = message.reply_to_message.from_user
    if message.reply_to_message and (message.chat.type == 'group' or message.chat.type == 'supergroup') and \
            Session.query(Users).filter(and_(Users.user_id == from_user.id, Users.status == 1)).all() \
            and not from_user.id == me.id:
        karma = Session.query(Karma).filter(and_((Karma.user_id == from_user.id), (Karma.chat_id == message.chat.id))).one()
        if karma:
            karma.karma += 1
            Session.commit()
            await message.reply(MESSAGES['like'].format(name=prettyUsername(n=from_user.full_name,
                        un=from_user.username)), reply=False, disable_web_page_preview=True)

@dp.message_handler(commands=['dislike'])
async def process_like_command(message: types.Message):
    me = await dp.bot.me
    from_user = message.reply_to_message.from_user
    if message.reply_to_message and (message.chat.type == 'group' or message.chat.type == 'supergroup') and \
            Session.query(Users).filter(and_(Users.user_id == message.from_user.id, Users.status == 1)).all() \
            and not from_user.id == me.id:
        karma = Session.query(Karma).filter(and_((Karma.user_id == from_user.id), (Karma.chat_id == message.chat.id))).one()
        if karma:
            karma.karma -= 1
            Session.commit()
            await message.reply(MESSAGES['dislike'].format(name=prettyUsername(n=from_user.full_name,
                        un=from_user.username)), reply=False, disable_web_page_preview=True)

@dp.message_handler(commands=['table'])
async def process_like_command(message: types.Message):
    if Session.query(Users).filter(and_(Users.user_id == message.from_user.id, Users.status == 1)).all():
        text = ''
        for karma in Session.query(Karma).filter(Karma.chat_id == message.chat.id).all():
            user = Session.query(Users).filter(Users.user_id == karma.user_id).one()
            text = text + str(prettyUsername(user.name, user.username)) + ' *' + str(karma.karma) + '*\n'
        await message.reply(MESSAGES['table'].format(name=message.chat.title) + text,
                            reply=False, disable_web_page_preview=True)

@dp.message_handler(content_types=ContentType.NEW_CHAT_MEMBERS | ContentType.GROUP_CHAT_CREATED)
async def process_autoleave(message: types.Message):
    me = await dp.bot.me
    ids_new_members = []
    for member in message.new_chat_members:
        ids_new_members.append(member.id)
    if me.id in ids_new_members:
        if Session.query(Users).filter(and_(Users.user_id == message.from_user.id), (Users.status == 1)).all() and \
                (message.chat.type == 'group' or message.chat.type == 'supergroup'):
            await bot.send_message(message.chat.id, MESSAGES['new_chat'].format(name=message.chat.title))
            chat = Chats(name=message.chat.title, chat_id=message.chat.id)
            Session.add(chat)
            Session.commit()
        else:
            await bot.leave_chat(message.chat.id)


@dp.message_handler()
async def process_add_chatmember(message: types.Message):
    print(str(message))
    user = message.from_user
    chat = message.chat
    if not Session.query(Users).filter(Users.user_id == message.from_user.id).all():
        user = Users(user_id=user.id, name=user.full_name, username=user.username)
        Session.add(user)
        Session.commit()
    if not Session.query(Karma).filter(and_((Karma.user_id == user.id), (Karma.chat_id == chat.id))).all():
        karma = Karma(user_id=user.id, chat_id=chat.id)
        Session.add(karma)
        Session.commit()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
