import aiohttp
from datetime import datetime

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.utils.markdown import bold
from aiosocksy import Socks5Auth
from sqlalchemy import create_engine, update, delete, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import asyncio
import logging
import os

from telebot.apihelper import leave_chat

from messages import MESSAGES
from conf import LOG_FILENAME, LOG_DIRECTORY, TOKEN, DB_FILENAME, PROXY_AUTH, PROXY_URL
from db_map import Users, Chats, Karma
from utils import AdminStates

from functions import *

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO)
loop = asyncio.get_event_loop()
bot = Bot(TOKEN, parse_mode=types.ParseMode.MARKDOWN, proxy=PROXY_URL,
          proxy_auth=PROXY_AUTH)
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
    if (message.chat.type == 'group' or message.chat.type == 'supergroup') and Session.query(Users).filter(
            and_(Users.user_id == message.from_user.id, Users.status == 1)).all():
        if message.reply_to_message and not message.reply_to_message.from_user.id == me.id:
            karma = Session.query(Karma).filter(and_((Karma.user_id == message.reply_to_message.from_user.id),
                                                     (Karma.chat_id == message.chat.id))).one()
            if karma:
                karma.karma += 1
                Session.commit()
                await message.reply(MESSAGES['like'].format(name=prettyUsername(
                    n=message.reply_to_message.from_user.full_name, un=message.reply_to_message.from_user.username)),
                    reply=False, disable_web_page_preview=True)
        elif not message.reply_to_message:
            users = Session.query(Karma).filter(Karma.chat_id == message.chat.id).all()
            inline_kb_full = InlineKeyboardMarkup(row_width=1)
            for user in users:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                inline_btn = InlineKeyboardButton(current_user.name, callback_data='like-' +
                                                                                   str(round(current_user.user_id)))
                inline_kb_full.add(inline_btn)
            await message.reply(MESSAGES['like_keyboard'], reply=False, disable_web_page_preview=True,
                                reply_markup=inline_kb_full)

@dp.message_handler(commands=['dislike'])
async def process_like_command(message: types.Message):
    me = await dp.bot.me
    if (message.chat.type == 'group' or message.chat.type == 'supergroup') and Session.query(Users).filter(
            and_(Users.user_id == message.from_user.id, Users.status == 1)).all():
        if message.reply_to_message and not message.reply_to_message.from_user.id == me.id:
            karma = Session.query(Karma).filter(and_((Karma.user_id == message.reply_to_message.from_user.id),
                                                     (Karma.chat_id == message.chat.id))).one()
            if karma:
                karma.karma -= 1
                Session.commit()
                await message.reply(MESSAGES['dislike'].format(name=prettyUsername(
                    n=message.reply_to_message.from_user.full_name, un=message.reply_to_message.from_user.username)),
                    reply=False, disable_web_page_preview=True)
        elif not message.reply_to_message:
            users = Session.query(Karma).filter(Karma.chat_id == message.chat.id).all()
            inline_kb_full = InlineKeyboardMarkup(row_width=1)
            for user in users:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                inline_btn = InlineKeyboardButton(current_user.name, callback_data='dislike-' +
                                                                                   str(round(current_user.user_id)))
                inline_kb_full.add(inline_btn)
            await message.reply(MESSAGES['dislike_keyboard'], reply=False, disable_web_page_preview=True,
                                reply_markup=inline_kb_full)


@dp.message_handler(commands=['table'])
async def process_like_command(message: types.Message):
    if Session.query(Users).filter(and_(Users.user_id == message.from_user.id, Users.status == 1)).all():
        text = ''
        for karma in Session.query(Karma).filter(Karma.chat_id == message.chat.id).order_by(Karma.karma.desc()).all():
            user = Session.query(Users).filter(Users.user_id == karma.user_id).one()
            text = text + str(prettyUsername(user.name, user.username)) + ' *' + str(karma.karma) + '*\n'
        await message.reply(MESSAGES['table'].format(name=message.chat.title) + text,
                            reply=False, disable_web_page_preview=True)


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('like-'))
async def process_callback_like(callback_query: types.CallbackQuery):
    code = callback_query.data[5:]
    if Session.query(Users).filter(and_(Users.user_id == callback_query.from_user.id, Users.status == 1)).all():
        if Session.query(Karma).filter(and_((Karma.user_id == code),
                                                 (Karma.chat_id == callback_query.message.chat.id))).all():
            karma = Session.query(Karma).filter(and_((Karma.user_id == code),
                                                 (Karma.chat_id == callback_query.message.chat.id))).one()
            karma.karma += 1
            Session.commit()
            user = Session.query(Users).filter(Users.user_id == karma.user_id).one()
            await bot.edit_message_text(MESSAGES['like'].format(name=prettyUsername(
                    n=user.name, un=user.username)), callback_query.message.chat.id,
                                        callback_query.message.message_id, disable_web_page_preview=True)
        else:
            await bot.edit_message_text(MESSAGES['error'], callback_query.message.chat.id,
                                        callback_query.message.message_id)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_admin'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('dislike-'))
async def process_callback_like(callback_query: types.CallbackQuery):
    code = callback_query.data[8:]
    if Session.query(Users).filter(and_(Users.user_id == callback_query.from_user.id, Users.status == 1)).all():
        if Session.query(Karma).filter(and_((Karma.user_id == code),
                                                 (Karma.chat_id == callback_query.message.chat.id))).all():
            karma = Session.query(Karma).filter(and_((Karma.user_id == code),
                                                 (Karma.chat_id == callback_query.message.chat.id))).one()
            karma.karma -= 1
            Session.commit()
            user = Session.query(Users).filter(Users.user_id == karma.user_id).one()
            await bot.edit_message_text(MESSAGES['dislike'].format(name=prettyUsername(
                    n=user.name, un=user.username)), callback_query.message.chat.id,
                                        callback_query.message.message_id, disable_web_page_preview=True)
        else:
            await bot.edit_message_text(MESSAGES['error'], callback_query.message.chat.id,
                                        callback_query.message.message_id)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_admin'])


@dp.message_handler(content_types=ContentType.NEW_CHAT_MEMBERS)
async def process_autoleave_new_members(message: types.Message):
    me = await dp.bot.me
    ids_new_members = []
    for member in message.new_chat_members:
        ids_new_members.append(member.id)
    if me.id in ids_new_members:
        if Session.query(Users).filter(and_(Users.user_id == message.from_user.id), (Users.status == 1)).all() and \
                (message.chat.type == 'group' or message.chat.type == 'supergroup'):
            Session.query(Chats).filter(Chats.chat_id == message.chat.id).delete()
            chat = Chats(name=message.chat.title, chat_id=message.chat.id)
            Session.add(chat)
            Session.commit()
            count = await bot.get_chat_members_count(message.chat.id)
            await bot.send_message(message.chat.id, MESSAGES['new_chat'].format(name=message.chat.title,
                                                                                count=str(count)))
        else:
            await bot.leave_chat(message.chat.id)


@dp.message_handler(content_types=ContentType.GROUP_CHAT_CREATED)
async def process_autoleave_new_chat(message: types.Message):
    if Session.query(Users).filter(and_(Users.user_id == message.from_user.id), (Users.status == 1)).all():
        chat = Chats(name=message.chat.title, chat_id=message.chat.id)
        Session.add(chat)
        Session.commit()
        count = await bot.get_chat_members_count(message.chat.id)
        await bot.send_message(message.chat.id, MESSAGES['new_chat'].format(name=message.chat.title,
                                    count=str(count)))
    else:
        await bot.leave_chat(message.chat.id)


@dp.message_handler()
async def process_add_chatmember(message: types.Message):
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
