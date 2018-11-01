from datetime import datetime

import random
import json
import aiohttp
import re

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton, input_media, InputMediaDocument
from aiogram.utils import executor
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import asyncio
import logging


from messages import MESSAGES
from conf import LOG_FILENAME, TOKEN, DB_FILENAME, PROXY_AUTH, PROXY_URL, MY_ID, LIMIT_INLINE_BTN, TIME_TO_SLEEP, \
    LIMIT_ADVICE, LIMIT_JOKE, TIME_TO_SELECT, TIME_TO_VOTE
from db_map import Users, Chats, Karma, Votings, Votes

from functions import prettyUsername, add_user_chat, advices_limit_counter, jokes_limit_counter,  \
    new_voting, vote, result_votes

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO, filename=LOG_FILENAME)
loop = asyncio.get_event_loop()
bot = Bot(TOKEN, parse_mode=types.ParseMode.HTML, proxy=PROXY_URL,
          proxy_auth=PROXY_AUTH)
dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

engine = create_engine(f'sqlite:///{DB_FILENAME}')

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

limit_inline_btn = LIMIT_INLINE_BTN


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


@dp.message_handler(commands=['help'], func=lambda message: message.chat.type == 'private')
async def process_help_command(message: types.Message):
    me = await dp.bot.me
    if message.from_user.id == MY_ID:
        await message.reply(MESSAGES['super_admin_commands'].format(username=me.username), reply=False,
                            parse_mode=types.ParseMode.HTML)
    else:
        await message.reply(MESSAGES['help'], reply=False)


@dp.message_handler(commands=['start'], func=lambda message: message.chat.type == 'private')
async def process_start_command(message: types.Message):
    await message.reply(MESSAGES['start'], reply=False)


@dp.message_handler(commands=['src'])
async def process_src_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    json_msg = message.as_json()
    await message.reply("<pre>" + json.dumps(json.loads(json_msg, encoding="utf-8"), sort_keys=True, indent=4,
                                             ensure_ascii=False)
                        + "</pre>", reply=False)

@dp.message_handler(commands=['advice'])
async def process_advice_command(message: types.Message):
    if message.chat.type in ('group', 'supergroup'):
        add_user_chat(message.from_user, message.chat)
    if message.chat.type in ('group', 'supergroup') and advices_limit_counter(message.from_user.id):
        to_del = await message.reply(MESSAGES['delete_template'].format(
            text=MESSAGES['limit_advice_is_over'].format(limit=LIMIT_ADVICE), time=TIME_TO_SLEEP),reply=False)
        await message.delete()
        await asyncio.sleep(TIME_TO_SLEEP)
        await to_del.delete()
    else:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://fucking-great-advice.ru/api/random') as resp:
                    await message.reply(MESSAGES['advice_template'].format(name=prettyUsername(message.from_user.full_name,
                                                                                                message.from_user.username),
                                         advice=(json.loads(await resp.text(), encoding="utf-8")['text'])), reply=False,
                                        disable_web_page_preview=True)
                    if message.chat.type in ('group', 'supergroup'):
                        await message.delete()
            except:
                to_del = await message.reply(MESSAGES['delete_template'].format(
                                text=MESSAGES['error'], time=TIME_TO_SLEEP), reply=False)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()


@dp.message_handler(commands=['joke'])
async def process_joke_command(message: types.Message):
    if message.chat.type in ('group', 'supergroup'):
        add_user_chat(message.from_user, message.chat)
    if message.chat.type in ('group', 'supergroup') and jokes_limit_counter(message.chat.id):
        to_del = await message.reply(MESSAGES['delete_template'].format(
            text=MESSAGES['limit_joke_is_over'].format(limit=LIMIT_JOKE), time=TIME_TO_SLEEP), reply=False)
        await message.delete()
        await asyncio.sleep(TIME_TO_SLEEP)
        await to_del.delete()
    else:
        async with aiohttp.ClientSession() as session:
            i = random.randint(0, 2300)
            try:
                if message.chat.type in ('group', 'supergroup'):
                    await message.delete()
                async with session.get('http://developerslife.ru/top/{page}?json=true'.format(page=i),
                                       verify_ssl=False) as resp:
                    if resp.status == 200:
                        response = json.loads(await resp.text())['result']
                        j = random.randint(0, len(response) - 1)
                        if message.chat.type in ('group', 'supergroup'):
                            inline_kb = None
                        else:
                            inline_kb = InlineKeyboardMarkup(row_width=1)
                            inline_btn = InlineKeyboardButton('🔄', callback_data='next-joke')
                            inline_kb.add(inline_btn)
                        await bot.send_document(chat_id=message.chat.id, caption=response[j]['description'],
                                                document=response[j]['videoURL'], reply_markup=inline_kb)
                    else:
                        to_del = await message.reply(MESSAGES['delete_template'].format(
                                text=MESSAGES['error'], time=TIME_TO_SLEEP), reply=False)
                        await asyncio.sleep(TIME_TO_SLEEP)
                        await to_del.delete()
            except:
                to_del = await message.reply(MESSAGES['delete_template'].format(
                                text=MESSAGES['error'], time=TIME_TO_SLEEP), reply=False)
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('next-joke') and c.message.chat.type == 'private')
async def process_callback_next_joke(callback_query: types.CallbackQuery):
    if callback_query.message.edit_date:
        lastUpdated = callback_query.message.edit_date
    else:
        lastUpdated = callback_query.message.date
    now = datetime.now()
    if (now - lastUpdated).total_seconds() > 5:
        async with aiohttp.ClientSession() as session:
            i = random.randint(0, 2300)
            async with session.get('http://developerslife.ru/top/{page}?json=true'.format(page=i),
                                   verify_ssl=False) as resp:
                response = json.loads(await resp.text())['result']
                j = random.randint(0, len(response) - 1)
                if callback_query.message.chat.type in ('group', 'supergroup'):
                    inline_kb = None
                else:
                    inline_kb = InlineKeyboardMarkup(row_width=1)
                    inline_btn = InlineKeyboardButton('🔄', callback_data='next-joke')
                    inline_kb.add(inline_btn)
                await bot.edit_message_media(chat_id=callback_query.message.chat.id,
                                             media=InputMediaDocument(response[j]['videoURL'],
                                                                      caption=response[j]['description']),
                                             message_id=callback_query.message.message_id,
                                             reply_markup=inline_kb)
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['wait'])


@dp.message_handler(commands=['me'])
async def process_me_command(message: types.Message):
    if message.chat.type in ('group', 'supergroup'):
        add_user_chat(message.from_user, message.chat)
    chat_text = ''
    for user in Session.query(Karma).filter(Karma.user_id == message.from_user.id).all():
        current_chat = Session.query(Chats).filter(Chats.chat_id == user.chat_id).one()
        chat_text = chat_text + MESSAGES['user_karma'].format(name=current_chat.name, karma=str(user.karma)) + '\n'
    try:
        await bot.send_message(message.from_user.id, MESSAGES['chat_list'].format(text=chat_text),
                               disable_web_page_preview=True)
        await message.delete()
    except:
        to_del = await message.reply(MESSAGES['delete_template'].format(
            text=MESSAGES['only_private'], time=TIME_TO_SLEEP), reply=False)
        await message.delete()
        await asyncio.sleep(TIME_TO_SLEEP)
        await to_del.delete()


@dp.message_handler(commands=['users'])
async def process_user_list_command(message: types.Message):
    if message.from_user.id == MY_ID:
        text = ''
        for chat in Session.query(Chats).all():
            chat_text = ''
            for user in Session.query(Karma).filter(Karma.chat_id == chat.chat_id).all():
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                chat_text = chat_text + MESSAGES['user_karma'].format(name=prettyUsername(current_user.name,
                                                                                          current_user.username),
                                                                      karma=str(user.karma))
            text = text + MESSAGES['user_chat_list'].format(text=chat_text, name=chat.name)
        await message.reply(MESSAGES['user_list'].format(text=text), reply=False, disable_web_page_preview=True)


@dp.message_handler(commands=['leave'])
async def process_user_list_command(message: types.Message):
    if message.from_user.id == MY_ID:
        await bot.leave_chat(message.chat.id)


@dp.message_handler(commands=['add'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_add_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)


@dp.message_handler(commands=['dislike'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_dislike_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == message.from_user.id:
            to_del = await message.reply(MESSAGES['delete_template'].format(
                text=MESSAGES['not_for_self'], time=TIME_TO_SLEEP), reply=False)
            await message.delete()
            await asyncio.sleep(TIME_TO_SLEEP)
            await to_del.delete()
        else:
            add_user_chat(message.reply_to_message.from_user, message.chat)
            vote_id = new_voting(message.from_user.id, message.reply_to_message.from_user.id, 0, message.chat.id)
            user_prettyname = prettyUsername(message.from_user.full_name, message.from_user.username)
            likes = Session.query(Users).filter(Users.user_id == message.reply_to_message.from_user.id).one()
            likes_prettyname = prettyUsername(likes.name, likes.username)
            users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
            users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
            no_list = ''
            for user in users_no:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
            yes_list = ''
            for user in users_yes:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
            inline_kb = InlineKeyboardMarkup(row_width=1)
            inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)),
                                                  callback_data='yes-dislike-' + str(vote_id))
            inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-dislike-' + str(vote_id))
            inline_kb.add(inline_btn_yes, inline_btn_no)
            await message.delete()
            text = MESSAGES['dislike_select'].format(user=user_prettyname,
                                                     likes=likes_prettyname,
                                                     yes=str(len(users_yes)),
                                                     no=str(len(users_no)),
                                                     list_yes=yes_list,
                                                     list_no=no_list,
                                                     time=TIME_TO_VOTE)
            mess = await message.reply(text, reply=False, disable_web_page_preview=True,
                                                      reply_markup=inline_kb)
            await asyncio.sleep(TIME_TO_VOTE * 60)
            likes = Session.query(Users).filter(Users.user_id == message.reply_to_message.from_user.id).one()
            likes_prettyname = prettyUsername(likes.name, likes.username)
            users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
            users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
            no_list = ''
            for user in users_no:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
            yes_list = ''
            for user in users_yes:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
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
            await bot.edit_message_text(text, mess.chat.id, mess.message_id, disable_web_page_preview=True,
                                        reply_markup=None)
    else:
        users = Session.query(Karma).filter(and_((Karma.chat_id == message.chat.id), (Karma.user_id != message.from_user.id)))\
            .order_by(Karma.id).limit(limit_inline_btn).all()
        inline_kb = InlineKeyboardMarkup(row_width=1)
        count = Session.query(Karma).filter(and_((Karma.chat_id == message.chat.id), (Karma.user_id != message.from_user.id)))\
            .count()
        for user in users:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            inline_btn = InlineKeyboardButton(current_user.name, callback_data='dislike-' + str(round(message.from_user.id))
                                                                               + '-' + str(round(current_user.user_id)))
            inline_kb.add(inline_btn)
        if count > limit_inline_btn:
            inline_btn_1 = InlineKeyboardButton(' ', callback_data='none')
            inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
            inline_btn_3 = InlineKeyboardButton('>', callback_data='next-d-' + str(round(message.from_user.id))
                                                                               + '-' + str(round(user.id)))
            inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
        to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['dislike_keyboard'].format(
            name=prettyUsername(message.from_user.full_name, message.from_user.username)),
                                                                        time=TIME_TO_SELECT),
                                     reply=False, disable_web_page_preview=True, reply_markup=inline_kb)
        await message.delete()
        await asyncio.sleep(TIME_TO_SELECT)
        try:
            await to_del.delete()
        except:
            pass


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('dislike-'))
async def process_callback_dislike(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        vote_id = new_voting(callback_query.from_user.id, code, 0, callback_query.message.chat.id)
        user_prettyname = prettyUsername(callback_query.from_user.full_name, callback_query.from_user.username)
        likes = Session.query(Users).filter(Users.user_id == code).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-dislike-' + str(vote_id))
        inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-dislike-' + str(vote_id))
        inline_kb.add(inline_btn_yes, inline_btn_no)
        await callback_query.message.delete()
        text = MESSAGES['dislike_select'].format(user=user_prettyname,
                                              likes=likes_prettyname,
                                              yes=str(len(users_yes)),
                                              no=str(len(users_no)),
                                              list_yes=yes_list,
                                              list_no=no_list,
                                              time=TIME_TO_VOTE)
        mess = await callback_query.message.reply(text, reply=False, disable_web_page_preview=True,
                                                  reply_markup=inline_kb)
        await asyncio.sleep(TIME_TO_VOTE*60)
        likes = Session.query(Users).filter(Users.user_id == code).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
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
        if await bot.edit_message_text(text, mess.chat.id, mess.message_id, disable_web_page_preview=True,
                                    reply_markup=None):
            await bot.delete_message(mess.chat.id, mess.message_id)
            await bot.send_message(mess.chat.id, text, disable_web_page_preview=True)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('yes-dislike-'))
async def process_callback_dislike_yes(callback_query: types.CallbackQuery):
    add_user_chat(callback_query.from_user, callback_query.message.chat)
    vote_id = int(re.findall(r'\d+', callback_query.data)[0])
    if vote(callback_query.from_user.id, vote_id, 1):
        code = Session.query(Votings).filter(Votings.id == vote_id).one()
        user = Session.query(Users).filter(Users.user_id == code.init_user_id).one()
        user_prettyname = prettyUsername(user.name, user.username)
        likes = Session.query(Users).filter(Users.user_id == code.candidate_user_id).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        count_user_in_chat = Session.query(Karma).filter(Karma.chat_id == callback_query.message.chat.id).count()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-dislike-' + str(vote_id))
        inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-dislike-' + str(vote_id))
        inline_kb.add(inline_btn_yes, inline_btn_no)
        if count_user_in_chat == len(users_yes) + len(users_no) + 1:
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
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            await bot.send_message(callback_query.message.chat.id, text, disable_web_page_preview=True)
        else:
            text = MESSAGES['dislike_select'].format(user=user_prettyname,
                                                  likes=likes_prettyname,
                                                  yes=str(len(users_yes)),
                                                  no=str(len(users_no)),
                                                  list_yes=yes_list,
                                                  list_no=no_list,
                                                  time=TIME_TO_VOTE)
            await bot.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                                    disable_web_page_preview=True, reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_one_vote'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('no-dislike-'))
async def process_callback_dislike_no(callback_query: types.CallbackQuery):
    add_user_chat(callback_query.from_user, callback_query.message.chat)
    vote_id = int(re.findall(r'\d+', callback_query.data)[0])
    if vote(callback_query.from_user.id, vote_id, 0):
        code = Session.query(Votings).filter(Votings.id == vote_id).one()
        user = Session.query(Users).filter(Users.user_id == code.init_user_id).one()
        user_prettyname = prettyUsername(user.name, user.username)
        likes = Session.query(Users).filter(Users.user_id == code.candidate_user_id).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        count_user_in_chat = Session.query(Karma).filter(Karma.chat_id == callback_query.message.chat.id).count()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-dislike-' + str(vote_id))
        inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-dislike-' + str(vote_id))
        inline_kb.add(inline_btn_yes, inline_btn_no)
        if count_user_in_chat == len(users_yes) + len(users_no) + 1:
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
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            await bot.send_message(callback_query.message.chat.id, text, disable_web_page_preview=True)
        else:
            text = MESSAGES['dislike_select'].format(user=user_prettyname,
                                                  likes=likes_prettyname,
                                                  yes=str(len(users_yes)),
                                                  no=str(len(users_no)),
                                                  list_yes=yes_list,
                                                  list_no=no_list,
                                                  time=TIME_TO_VOTE)
            await bot.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                                    disable_web_page_preview=True, reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_one_vote'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('next-d-'))
async def process_callback_next(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        users = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id > code))).order_by(Karma.id).limit(limit_inline_btn).all()
        count = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id <= code))).count()
        inline_kb = InlineKeyboardMarkup(row_width=1)
        for user in users:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            inline_btn = InlineKeyboardButton(current_user.name,
                                              callback_data='dislike-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(current_user.user_id)))
            inline_kb.add(inline_btn)
        inline_btn_1 = InlineKeyboardButton('<', callback_data='prev-d-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(code))
        inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
        if count > limit_inline_btn:
            inline_btn_3 = InlineKeyboardButton('>', callback_data='next-d-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(user.id)))
        else:
            inline_btn_3 = InlineKeyboardButton(' ', callback_data='none')
        inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('prev-d-'))
async def process_callback_prev(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        users = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id <= code))).order_by(Karma.id).limit(limit_inline_btn).all()
        count = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id <= code))).count()
        inline_kb = InlineKeyboardMarkup(row_width=1)
        for user in users:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            inline_btn = InlineKeyboardButton(current_user.name, callback_data='dislike-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(current_user.user_id)))
            inline_kb.add(inline_btn)
        if count > limit_inline_btn:
            inline_btn_1 = InlineKeyboardButton('<', callback_data='prev-d-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(user.id)))
        else:
            inline_btn_1 = InlineKeyboardButton(' ', callback_data='none')
        inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
        inline_btn_3 = InlineKeyboardButton('>', callback_data='next-d-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(code))
        inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.message_handler(commands=['like'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_like_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == message.from_user.id:
            to_del = await message.reply(MESSAGES['delete_template'].format(
                text=MESSAGES['not_for_self'], time=TIME_TO_SLEEP), reply=False)
            await message.delete()
            await asyncio.sleep(TIME_TO_SLEEP)
            await to_del.delete()
        else:
            add_user_chat(message.reply_to_message.from_user, message.chat)
            vote_id = new_voting(message.from_user.id, message.reply_to_message.from_user.id, 0, message.chat.id)
            user_prettyname = prettyUsername(message.from_user.full_name, message.from_user.username)
            likes = Session.query(Users).filter(Users.user_id == message.reply_to_message.from_user.id).one()
            likes_prettyname = prettyUsername(likes.name, likes.username)
            users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
            users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
            no_list = ''
            for user in users_no:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
            yes_list = ''
            for user in users_yes:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
            inline_kb = InlineKeyboardMarkup(row_width=1)
            inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)),
                                                  callback_data='yes-like-' + str(vote_id))
            inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-like-' + str(vote_id))
            inline_kb.add(inline_btn_yes, inline_btn_no)
            await message.delete()
            text = MESSAGES['like_select'].format(user=user_prettyname,
                                                     likes=likes_prettyname,
                                                     yes=str(len(users_yes)),
                                                     no=str(len(users_no)),
                                                     list_yes=yes_list,
                                                     list_no=no_list,
                                                     time=TIME_TO_VOTE)
            mess = await message.reply(text, reply=False, disable_web_page_preview=True,
                                                      reply_markup=inline_kb)
            await asyncio.sleep(TIME_TO_VOTE * 60)
            likes = Session.query(Users).filter(Users.user_id == message.reply_to_message.from_user.id).one()
            likes_prettyname = prettyUsername(likes.name, likes.username)
            users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
            users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
            no_list = ''
            for user in users_no:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
            yes_list = ''
            for user in users_yes:
                current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
                yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
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
            await bot.edit_message_text(text, mess.chat.id, mess.message_id, disable_web_page_preview=True,
                                        reply_markup=None)
    else:
        users = Session.query(Karma).filter(and_((Karma.chat_id == message.chat.id),
                                                 (Karma.user_id != message.from_user.id)))\
            .order_by(Karma.id).limit(limit_inline_btn).all()
        inline_kb = InlineKeyboardMarkup(row_width=1)
        count = Session.query(Karma).filter(and_((Karma.chat_id == message.chat.id),
                                                 (Karma.user_id != message.from_user.id))).count()
        for user in users:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            inline_btn = InlineKeyboardButton(current_user.name, callback_data='like-' + str(round(message.from_user.id))
                                                                               + '-' + str(round(current_user.user_id)))
            inline_kb.add(inline_btn)
        if count > limit_inline_btn:
            inline_btn_1 = InlineKeyboardButton(' ', callback_data='none')
            inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
            inline_btn_3 = InlineKeyboardButton('>', callback_data='next-l-' + str(round(message.from_user.id))
                                                                               + '-' + str(round(user.id)))
            inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
        to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['like_keyboard'].format(
            name=prettyUsername(message.from_user.full_name, message.from_user.username)),
                                                                        time=TIME_TO_SELECT),
                                     reply=False, disable_web_page_preview=True, reply_markup=inline_kb)
        await message.delete()
        await asyncio.sleep(TIME_TO_SELECT)
        try:
            await to_del.delete()
        except:
            pass


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('like-'))
async def process_callback_like(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        vote_id = new_voting(callback_query.from_user.id, code, 1, callback_query.message.chat.id)
        user_prettyname = prettyUsername(callback_query.from_user.full_name, callback_query.from_user.username)
        likes = Session.query(Users).filter(Users.user_id == code).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-like-' + str(vote_id))
        inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-like-' + str(vote_id))
        inline_kb.add(inline_btn_yes, inline_btn_no)
        await callback_query.message.delete()
        text = MESSAGES['like_select'].format(user=user_prettyname,
                                              likes=likes_prettyname,
                                              yes=str(len(users_yes)),
                                              no=str(len(users_no)),
                                              list_yes=yes_list,
                                              list_no=no_list,
                                              time=TIME_TO_VOTE)
        mess = await callback_query.message.reply(text, reply=False, disable_web_page_preview=True,
                                                  reply_markup=inline_kb)
        await asyncio.sleep(TIME_TO_VOTE*60)
        likes = Session.query(Users).filter(Users.user_id == code).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
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
        if await bot.edit_message_text(text, mess.chat.id, mess.message_id, disable_web_page_preview=True,
                                    reply_markup=None):
            await bot.delete_message(mess.chat.id, mess.message_id)
            await bot.send_message(mess.chat.id, text, disable_web_page_preview=True)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('yes-like-'))
async def process_callback_like_yes(callback_query: types.CallbackQuery):
    add_user_chat(callback_query.from_user, callback_query.message.chat)
    vote_id = int(re.findall(r'\d+', callback_query.data)[0])
    if vote(callback_query.from_user.id, vote_id, 1):
        code = Session.query(Votings).filter(Votings.id == vote_id).one()
        user = Session.query(Users).filter(Users.user_id == code.init_user_id).one()
        user_prettyname = prettyUsername(user.name, user.username)
        likes = Session.query(Users).filter(Users.user_id == code.candidate_user_id).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        count_user_in_chat = Session.query(Karma).filter(Karma.chat_id == callback_query.message.chat.id).count()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-like-' + str(vote_id))
        inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-like-' + str(vote_id))
        inline_kb.add(inline_btn_yes, inline_btn_no)
        if count_user_in_chat == len(users_yes) + len(users_no) + 1:
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
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            await bot.send_message(callback_query.message.chat.id, text, disable_web_page_preview=True)
        else:
            text = MESSAGES['like_select'].format(user=user_prettyname,
                                                  likes=likes_prettyname,
                                                  yes=str(len(users_yes)),
                                                  no=str(len(users_no)),
                                                  list_yes=yes_list,
                                                  list_no=no_list,
                                                  time=TIME_TO_VOTE)
            await bot.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                                    disable_web_page_preview=True, reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_one_vote'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('no-like-'))
async def process_callback_like_no(callback_query: types.CallbackQuery):
    add_user_chat(callback_query.from_user, callback_query.message.chat)
    vote_id = int(re.findall(r'\d+', callback_query.data)[0])
    if vote(callback_query.from_user.id, vote_id, 0):
        code = Session.query(Votings).filter(Votings.id == vote_id).one()
        user = Session.query(Users).filter(Users.user_id == code.init_user_id).one()
        user_prettyname = prettyUsername(user.name, user.username)
        likes = Session.query(Users).filter(Users.user_id == code.candidate_user_id).one()
        likes_prettyname = prettyUsername(likes.name, likes.username)
        users_yes = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 1))).all()
        users_no = Session.query(Votes).filter(and_((Votes.vote_id == vote_id), (Votes.answer == 0))).all()
        count_user_in_chat = Session.query(Karma).filter(Karma.chat_id == callback_query.message.chat.id).count()
        no_list = ''
        for user in users_no:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            no_list = no_list + '\n' + prettyUsername(current_user.name, current_user.username)
        yes_list = ''
        for user in users_yes:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            yes_list = yes_list + '\n' + prettyUsername(current_user.name, current_user.username)
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_btn_yes = InlineKeyboardButton('Да - ' + str(len(users_yes)), callback_data='yes-like-' + str(vote_id))
        inline_btn_no = InlineKeyboardButton('Нет - ' + str(len(users_no)), callback_data='no-like-' + str(vote_id))
        inline_kb.add(inline_btn_yes, inline_btn_no)
        if count_user_in_chat == len(users_yes) + len(users_no) + 1:
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
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            await bot.send_message(callback_query.message.chat.id, text, disable_web_page_preview=True)
        else:
            text = MESSAGES['like_select'].format(user=user_prettyname,
                                                  likes=likes_prettyname,
                                                  yes=str(len(users_yes)),
                                                  no=str(len(users_no)),
                                                  list_yes=yes_list,
                                                  list_no=no_list,
                                                  time=TIME_TO_VOTE)
            await bot.edit_message_text(text, callback_query.message.chat.id, callback_query.message.message_id,
                                    disable_web_page_preview=True, reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_one_vote'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('next-l-'))
async def process_callback_next(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        users = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id > code))).order_by(Karma.id).limit(limit_inline_btn).all()
        count = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id <= code))).count()
        inline_kb = InlineKeyboardMarkup(row_width=1)
        for user in users:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            inline_btn = InlineKeyboardButton(current_user.name,
                                              callback_data='like-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(current_user.user_id)))
            inline_kb.add(inline_btn)
        inline_btn_1 = InlineKeyboardButton('<', callback_data='prev-l-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(code))
        inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
        if count > limit_inline_btn:
            inline_btn_3 = InlineKeyboardButton('>', callback_data='next-l-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(user.id)))
        else:
            inline_btn_3 = InlineKeyboardButton(' ', callback_data='none')
        inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('prev-l-'))
async def process_callback_prev(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        users = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id <= code))).order_by(Karma.id).limit(limit_inline_btn).all()
        count = Session.query(Karma).filter(and_((Karma.chat_id == callback_query.message.chat.id),
                                                 (Karma.user_id != callback_query.from_user.id),
                                                 (Karma.id <= code))).count()
        inline_kb = InlineKeyboardMarkup(row_width=1)
        for user in users:
            current_user = Session.query(Users).filter(Users.user_id == user.user_id).one()
            inline_btn = InlineKeyboardButton(current_user.name, callback_data='like-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(current_user.user_id)))
            inline_kb.add(inline_btn)
        if count > limit_inline_btn:
            inline_btn_1 = InlineKeyboardButton('<', callback_data='prev-l-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(round(user.id)))
        else:
            inline_btn_1 = InlineKeyboardButton(' ', callback_data='none')
        inline_btn_2 = InlineKeyboardButton(' ', callback_data='none')
        inline_btn_3 = InlineKeyboardButton('>', callback_data='next-l-' + str(round(callback_query.from_user.id))
                                                                           + '-' + str(code))
        inline_kb.row(inline_btn_1, inline_btn_2, inline_btn_3)
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=inline_kb)
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.message_handler(commands=['karma'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_like_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    text = ''
    i = 1
    count = Session.query(Karma).filter(Karma.chat_id == message.chat.id).count()
    for karma in Session.query(Karma).filter(Karma.chat_id == message.chat.id).order_by(Karma.karma.desc()).all():
        user = Session.query(Users).filter(Users.user_id == karma.user_id).one()
        if i == 1:
            text = text + '\n👑 ' + MESSAGES['user_karma'].format(name=prettyUsername(user.name, user.username),
                                                    karma=str(karma.karma))
        elif i == count:
            text = text + '\n💩 ' + MESSAGES['user_karma'].format(name=prettyUsername(user.name, user.username),
                                                               karma=str(karma.karma))
        else:
            text = text + '\n' + MESSAGES['user_karma'].format(name=prettyUsername(user.name, user.username),
                                                               karma=str(karma.karma))
        i += 1
    to_del = await message.reply(MESSAGES['delete_template'].format(
        text=MESSAGES['karma'].format(name=message.chat.title, text=text), time=TIME_TO_SELECT), reply=False,
        disable_web_page_preview=True)
    await message.delete()
    await asyncio.sleep(TIME_TO_SELECT)
    await to_del.delete()


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('none'))
async def process_callback_none(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id, '')


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
                                                                                count=str(count),
                                                                                command='/add@' + me.username))
            add_user_chat(me, message.chat)
        else:
            await bot.leave_chat(message.chat.id)


@dp.message_handler(content_types=ContentType.GROUP_CHAT_CREATED)
async def process_autoleave_new_chat(message: types.Message):
    me = await dp.bot.me
    if Session.query(Users).filter(and_(Users.user_id == message.from_user.id), (Users.status == 1)).all():
        chat = Chats(name=message.chat.title, chat_id=message.chat.id)
        Session.add(chat)
        Session.commit()
        count = await bot.get_chat_members_count(message.chat.id)
        await bot.send_message(message.chat.id, MESSAGES['new_chat'].format(name=message.chat.title,
                                                                            count=str(count),
                                                                            command='/add@' + me.username),
                               parse_mode=None)
    else:
        await bot.leave_chat(message.chat.id)


@dp.message_handler(content_types=ContentType.LEFT_CHAT_MEMBER)
async def process_kick_member(message: types.Message):
    user = message.left_chat_member
    chat = message.chat
    me = await dp.bot.me
    if not message.left_chat_member.id == me.id:
        if Session.query(Karma).filter(and_((Karma.user_id == user.id), (Karma.chat_id == chat.id))).all():
            Session.query(Karma).filter(and_((Karma.user_id == user.id), (Karma.chat_id == chat.id))).delete()
            Session.commit()
        await bot.send_message(chat.id, MESSAGES['bye'].format(name=prettyUsername(user.full_name, user.username)),
                               disable_web_page_preview=True)


@dp.message_handler(func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_rand_like_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    i = random.randrange(500)
    if message.text.lower()[:6] == 'привет' and len(message.text) in [6, 7]:
        to_del = await bot.send_message(message.chat.id, MESSAGES['delete_template'].format(
            text=MESSAGES['no_privet'], time=TIME_TO_SLEEP), disable_web_page_preview=True)
        await message.delete()
        await asyncio.sleep(TIME_TO_SLEEP)
        await to_del.delete()
    elif re.findall(r'(?:^|\s)функционала?(?:$|\s)', message.text.lower()):
        to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['functional'],
                                                                        time=TIME_TO_SLEEP),
                                     disable_web_page_preview=True)
        await asyncio.sleep(TIME_TO_SLEEP)
        await to_del.delete()
    else:
        if i == 1:
            session = Session()
            karma = session.query(Karma).filter(and_((Karma.user_id == message.from_user.id),
                                                     (Karma.chat_id == message.chat.id))).one()
            karma.karma += 1
            try:
                session.commit()
            finally:
                session.close()
            await message.reply(MESSAGES['random_like'], disable_web_page_preview=True)
        elif i == 2:
            session = Session()
            karma = session.query(Karma).filter(and_((Karma.user_id == message.from_user.id),
                                                     (Karma.chat_id == message.chat.id))).one()
            karma.karma -= 1
            try:
                session.commit()
            finally:
                session.close()
            await message.reply(MESSAGES['random_dislike'], disable_web_page_preview=True)


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
