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
from db_map import Users, Chats, Karma

from functions import prettyUsername, add_user_chat, advices_limit_counter, jokes_limit_counter,  \
    new_voting, vote, karma_in_chat_text, current_state_vote, pagination_voting, trigger, triggers_list, new_trigger, \
    delete_trigger, change_chat_status, chat_status
from antimat import matfilter

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
    await message.delete()

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
    await message.delete()


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
            mess_inner = current_state_vote(TIME_TO_VOTE, vote_id)
            await message.delete()
            mess = await message.reply(mess_inner[0], reply=False, disable_web_page_preview=True,
                                       reply_markup=mess_inner[1])
            await asyncio.sleep(TIME_TO_VOTE * 60)
            mess_inner = current_state_vote(TIME_TO_VOTE, vote_id, end=1)
            try:
                await bot.delete_message(mess.chat.id, mess.message_id)
            finally:
                await bot.send_message(mess.chat.id, mess_inner[0], disable_web_page_preview=True)
    else:
        keyboard = pagination_voting(0, message.chat.id, message.from_user.id, limit_inline_btn, '0', 'next')
        to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['dislike_keyboard'].format(
            name=prettyUsername(message.from_user.full_name, message.from_user.username)),
                                                                        time=TIME_TO_SELECT),
                                     reply=False, disable_web_page_preview=True, reply_markup=keyboard)
        await message.delete()
        await asyncio.sleep(TIME_TO_SELECT)
        try:
            await to_del.delete()
        except:
            pass


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
            vote_id = new_voting(message.from_user.id, message.reply_to_message.from_user.id, '1', message.chat.id)
            mess_inner = current_state_vote(TIME_TO_VOTE, vote_id)
            await message.delete()
            mess = await message.reply(mess_inner[0], reply=False, disable_web_page_preview=True,
                                                      reply_markup=mess_inner[1])
            await asyncio.sleep(TIME_TO_VOTE * 60)
            mess_inner = current_state_vote(TIME_TO_VOTE, vote_id, end=1)
            try:
                await bot.delete_message(mess.chat.id, mess.message_id)
            finally:
                await bot.send_message(mess.chat.id, mess_inner[0], disable_web_page_preview=True)
    else:
        keyboard = pagination_voting(0, message.chat.id, message.from_user.id, limit_inline_btn, '1', 'next')
        to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['like_keyboard'].format(
            name=prettyUsername(message.from_user.full_name, message.from_user.username)),
                                                                        time=TIME_TO_SELECT),
                                     reply=False, disable_web_page_preview=True, reply_markup=keyboard)
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
        mess_inner = current_state_vote(TIME_TO_VOTE, vote_id)
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        mess = await callback_query.message.reply(mess_inner[0], reply=False, disable_web_page_preview=True,
                                                  reply_markup=mess_inner[1])
        await asyncio.sleep(TIME_TO_VOTE * 60)
        mess_inner = current_state_vote(TIME_TO_VOTE, vote_id, end=1)
        try:
            await bot.delete_message(mess.chat.id, mess.message_id)
        finally:
            await bot.send_message(mess.chat.id, mess_inner[0], disable_web_page_preview=True)
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('dislike-'))
async def process_callback_dislike(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        vote_id = new_voting(callback_query.from_user.id, code, 0, callback_query.message.chat.id)
        mess_inner = current_state_vote(TIME_TO_VOTE, vote_id)
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        mess = await callback_query.message.reply(mess_inner[0], reply=False, disable_web_page_preview=True,
                                                  reply_markup=mess_inner[1])
        await asyncio.sleep(TIME_TO_VOTE * 60)
        mess_inner = current_state_vote(TIME_TO_VOTE, vote_id, end=1)
        try:
            await bot.delete_message(mess.chat.id, mess.message_id)
        finally:
            await bot.send_message(mess.chat.id, mess_inner[0], disable_web_page_preview=True)
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('yes-'))
async def process_callback_dislike_yes(callback_query: types.CallbackQuery):
    add_user_chat(callback_query.from_user, callback_query.message.chat)
    vote_id = int(re.findall(r'\d+', callback_query.data)[0])
    if vote(callback_query.from_user.id, vote_id, 1):
        mess_inner = current_state_vote(TIME_TO_VOTE, vote_id)
        await bot.edit_message_text(mess_inner[0], callback_query.message.chat.id, callback_query.message.message_id,
                                    disable_web_page_preview=True, reply_markup=mess_inner[1])
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_one_vote'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('no-'))
async def process_callback_dislike_yes(callback_query: types.CallbackQuery):
    add_user_chat(callback_query.from_user, callback_query.message.chat)
    vote_id = int(re.findall(r'\d+', callback_query.data)[0])
    if vote(callback_query.from_user.id, vote_id, 0):
        mess_inner = current_state_vote(TIME_TO_VOTE, vote_id)
        await bot.edit_message_text(mess_inner[0], callback_query.message.chat.id, callback_query.message.message_id,
                                    disable_web_page_preview=True, reply_markup=mess_inner[1])
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['only_one_vote'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('next-'))
async def process_callback_next(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        type = re.findall(r'\d+', callback_query.data)[2]
        keyboard = pagination_voting(code, callback_query.message.chat.id, callback_query.from_user.id, limit_inline_btn,
                                     type,
                                     'next')
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=keyboard)
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.callback_query_handler(func=lambda c: c.data and c.data.startswith('prev-'))
async def process_callback_prev(callback_query: types.CallbackQuery):
    user = re.findall(r'\d+', callback_query.data)[0]
    if str(callback_query.from_user.id) == user:
        code = re.findall(r'\d+', callback_query.data)[1]
        type = re.findall(r'\d+', callback_query.data)[2]
        keyboard = pagination_voting(code, callback_query.message.chat.id, callback_query.from_user.id,
                                     limit_inline_btn,
                                     type,
                                     'prev')
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=keyboard)
        await bot.answer_callback_query(callback_query.id, '')
    else:
        await bot.answer_callback_query(callback_query.id, MESSAGES['not_for_you'])


@dp.message_handler(commands=['karma'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_like_command(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    to_del = await message.reply(karma_in_chat_text(message.chat.id, TIME_TO_SELECT), reply=False,
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
        chat = Chats(name=message.chat.title, chat_id=message.chat.id, status=0)
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


@dp.message_handler(commands=['restrict'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_restrict_command(message: types.Message):
    if message.from_user.id == MY_ID:
        if message.reply_to_message.from_user.id:
            await bot.restrict_chat_member(message.chat.id,
                                           message.reply_to_message.from_user.id,
                                           can_send_messages=False,
                                           can_add_web_page_previews=False,
                                           can_send_media_messages=False,
                                           can_send_other_messages=False)
            to_del = await message.reply_to_message.reply(MESSAGES['delete_template'].format(
                text=MESSAGES['ban_user'].format(time=TIME_TO_SELECT), time=TIME_TO_SLEEP),
                disable_web_page_preview=True)
            await message.delete()
            await asyncio.sleep(TIME_TO_SLEEP)
            await to_del.delete()
            await asyncio.sleep(TIME_TO_SELECT-TIME_TO_SLEEP)
            await bot.restrict_chat_member(message.chat.id,
                                           message.reply_to_message.from_user.id,
                                           can_send_messages=True,
                                           can_add_web_page_previews=True,
                                           can_send_media_messages=True,
                                           can_send_other_messages=True)
    else:
        await message.delete()


@dp.message_handler(commands=['trigger'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_restrict_command(message: types.Message):
    if message.reply_to_message:
        name = message.text[9:]
        if len(name) == 0:
            to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['error_name_trigger'],
                                                                            time=TIME_TO_SLEEP),
                                         disable_web_page_preview=True, reply=False)
            await message.delete()
            await asyncio.sleep(TIME_TO_SLEEP)
            await to_del.delete()
        elif len(name) > 29:
            to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['error_name_trigger'],
                                                                            time=TIME_TO_SLEEP),
                                         disable_web_page_preview=True, reply=False)
            await message.delete()
            await asyncio.sleep(TIME_TO_SLEEP)
            await to_del.delete()
        else:
            if message.reply_to_message.animation:
                if message.reply_to_message.caption:
                    text = message.reply_to_message.caption
                else:
                    text = ''
                new_trigger(name, text, message.chat.id,
                            message.reply_to_message.animation.file_id,
                            'animation')
                to_del = await message.reply_to_message.reply(
                    MESSAGES['delete_template'].format(text=MESSAGES['trigger_save'],
                                                       time=TIME_TO_SLEEP),
                    disable_web_page_preview=True)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
            elif message.reply_to_message.sticker:
                new_trigger(name, None, message.chat.id,
                            message.reply_to_message.sticker.file_id,
                            'sticker')
                to_del = await message.reply_to_message.reply(
                    MESSAGES['delete_template'].format(text=MESSAGES['trigger_save'],
                                                       time=TIME_TO_SLEEP),
                    disable_web_page_preview=True)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
            elif message.reply_to_message.document:
                if message.reply_to_message.caption:
                    text = message.reply_to_message.caption
                else:
                    text = ''
                new_trigger(name, text, message.chat.id,
                            message.reply_to_message.document.file_id,
                            'document')
                to_del = await message.reply_to_message.reply(
                    MESSAGES['delete_template'].format(text=MESSAGES['trigger_save'],
                                                       time=TIME_TO_SLEEP),
                    disable_web_page_preview=True)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
            elif message.reply_to_message.photo:
                if message.reply_to_message.caption:
                    text = message.reply_to_message.caption
                else:
                    text = ''
                new_trigger(name, text, message.chat.id,
                            message.reply_to_message.photo[len(message.reply_to_message.photo) - 1].file_id,
                            'photo')
                to_del = await message.reply_to_message.reply(
                    MESSAGES['delete_template'].format(text=MESSAGES['trigger_save'],
                                                       time=TIME_TO_SLEEP),
                    disable_web_page_preview=True)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
            elif message.reply_to_message.text:
                if len(message.reply_to_message.html_text) == 0:
                    to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['error_text_trigger'],
                                                                                    time=TIME_TO_SLEEP),
                                                 disable_web_page_preview=True, reply=False)
                    await message.delete()
                    await asyncio.sleep(TIME_TO_SLEEP)
                    await to_del.delete()
                elif len(message.reply_to_message.html_text) > 4095:
                    to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['error_text_trigger'],
                                                                                    time=TIME_TO_SLEEP),
                                                 disable_web_page_preview=True, reply=False)
                    await message.delete()
                    await asyncio.sleep(TIME_TO_SLEEP)
                    await to_del.delete()
                else:
                    new_trigger(name, message.reply_to_message.html_text, message.chat.id, None,'text')
                    to_del = await message.reply_to_message.reply(
                        MESSAGES['delete_template'].format(text=MESSAGES['trigger_save'],
                                                           time=TIME_TO_SLEEP),
                        disable_web_page_preview=True)
                    await message.delete()
                    await asyncio.sleep(TIME_TO_SLEEP)
                    await to_del.delete()
            else:
                await message.delete()
    else:
        mess = triggers_list(message.chat.id)
        to_del = await message.reply(MESSAGES['delete_template'].format(text=mess, time=TIME_TO_SLEEP*10),
                                         disable_web_page_preview=True, reply=False)
        await message.delete()
        await asyncio.sleep(TIME_TO_SLEEP*10)
        await to_del.delete()


@dp.message_handler(commands=['dt'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_restrict_command(message: types.Message):
    if message.from_user.id == MY_ID:
        name = message.text[4:]
        delete_trigger(name, message.chat.id)
    await message.delete()

@dp.message_handler(commands=['ccs'], func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_restrict_command(message: types.Message):
    if message.from_user.id == MY_ID:
        status = int(message.text[5:])
        change_chat_status(message.chat.id, status)
    await message.delete()


@dp.edited_message_handler(func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_edit_message(message: types.Message):
    if message.text[0] == '!':
        trig = trigger(message.text[1:].lower(), message.chat.id)
        if trig:
            if trig.type == 'photo':
                await bot.send_photo(message.chat.id, trig.media_id, caption=trig.text)
            elif trig.type == 'animation':
                await bot.send_document(message.chat.id, trig.media_id, caption=trig.text)
            elif trig.type == 'sticker':
                await bot.send_sticker(message.chat.id, trig.media_id)
            elif trig.type == 'text':
                await bot.send_message(message.chat.id, trig.text, disable_web_page_preview=True)
            elif trig.type == 'document':
                await bot.send_document(message.chat.id, trig.media_id, caption=trig.text)
    elif chat_status(message.chat.id) == 1:
        if re.findall(r'\w+', message.text):
            if re.findall(r'\w+', message.text)[0].lower() == 'привет' and len(re.findall(r'\w+', message.text)) == 1:
                to_del = await bot.send_message(message.chat.id, MESSAGES['delete_template'].format(
                    text=MESSAGES['no_privet'], time=TIME_TO_SLEEP), disable_web_page_preview=True)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
            #elif len(matfilter(message.text)):
            #    admins = await bot.get_chat_administrators(message.chat.id)
            #    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
            #    if user in admins:
            #        to_del = await message.reply(MESSAGES['delete_template'].format(
            #            text=MESSAGES['antimat'], time=TIME_TO_SLEEP),
            #            disable_web_page_preview=True, reply=False)
            #        await message.delete()
            #        await asyncio.sleep(TIME_TO_SLEEP)
            #        await to_del.delete()
            #    else:
            #        await bot.restrict_chat_member(message.chat.id,
            #                                       message.from_user.id,
            #                                       can_send_messages=False,
            #                                       can_add_web_page_previews=False,
            #                                       can_send_media_messages=False,
            #                                       can_send_other_messages=False)
            #        to_del = await message.reply(MESSAGES['delete_template'].format(
            #            text=MESSAGES['ban_user'].format(time=TIME_TO_SELECT), time=TIME_TO_SLEEP),
            #            disable_web_page_preview=True, reply=False)
            #        await message.delete()
            #        await asyncio.sleep(TIME_TO_SLEEP)
            #        await to_del.delete()
            #        await asyncio.sleep(TIME_TO_SELECT - TIME_TO_SLEEP)
            #       await bot.restrict_chat_member(message.chat.id,
            #                                      message.from_user.id,
            #                                      can_send_messages=True,
            #                                       can_add_web_page_previews=True,
            #                                       can_send_media_messages=True,
            #                                       can_send_other_messages=True)
            elif re.findall(r'(?:^|\s)функционала?(?:$|\s)', message.text.lower()):
                to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['functional'],
                                                                                time=TIME_TO_SLEEP),
                                             disable_web_page_preview=True)
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()


@dp.message_handler(func=lambda message: message.chat.type in ('group', 'supergroup'))
async def process_another_message(message: types.Message):
    add_user_chat(message.from_user, message.chat)
    i = random.randrange(500)
    if message.text[0] == '!':
        trig = trigger(message.text[1:].lower(), message.chat.id)
        if trig:
            if trig.type == 'photo':
                await bot.send_photo(message.chat.id, trig.media_id, caption=trig.text)
            elif trig.type == 'animation':
                await bot.send_document(message.chat.id, trig.media_id, caption=trig.text)
            elif trig.type == 'sticker':
                await bot.send_sticker(message.chat.id, trig.media_id)
            elif trig.type == 'text':
                await bot.send_message(message.chat.id, trig.text, disable_web_page_preview=True)
            elif trig.type == 'document':
                await bot.send_document(message.chat.id, trig.media_id, caption=trig.text)
    elif chat_status(message.chat.id) == 1:
        if re.findall(r'\w+', message.text):
            if re.findall(r'\w+', message.text)[0].lower() == 'привет' and len(re.findall(r'\w+', message.text)) == 1:
                to_del = await bot.send_message(message.chat.id, MESSAGES['delete_template'].format(
                    text=MESSAGES['no_privet'], time=TIME_TO_SLEEP), disable_web_page_preview=True)
                await message.delete()
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
            #elif len(matfilter(message.text)):
            #    admins = await bot.get_chat_administrators(message.chat.id)
            #    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
            #    if user in admins:
            #        to_del = await message.reply(MESSAGES['delete_template'].format(
            #            text=MESSAGES['antimat'], time=TIME_TO_SLEEP),
            #            disable_web_page_preview=True, reply=False)
            #        await message.delete()
            #        await asyncio.sleep(TIME_TO_SLEEP)
            #        await to_del.delete()
            #    else:
            #        await bot.restrict_chat_member(message.chat.id,
            #                                       message.from_user.id,
            #                                       can_send_messages=False,
            #                                       can_add_web_page_previews=False,
            #                                       can_send_media_messages=False,
            #                                       can_send_other_messages=False)
            #        to_del = await message.reply(MESSAGES['delete_template'].format(
            #            text=MESSAGES['ban_user'].format(time=TIME_TO_SELECT), time=TIME_TO_SLEEP),
            #            disable_web_page_preview=True, reply=False)
            #        await message.delete()
            #        await asyncio.sleep(TIME_TO_SLEEP)
            #        await to_del.delete()
            #        await asyncio.sleep(TIME_TO_SELECT - TIME_TO_SLEEP)
            #        await bot.restrict_chat_member(message.chat.id,
            #                                       message.from_user.id,
            #                                       can_send_messages=True,
            #                                       can_add_web_page_previews=True,
            #                                       can_send_media_messages=True,
            #                                      can_send_other_messages=True)
            elif re.findall(r'(?:^|\s)функционала?(?:$|\s)', message.text.lower()):
                to_del = await message.reply(MESSAGES['delete_template'].format(text=MESSAGES['functional'],
                                                                                time=TIME_TO_SLEEP),
                                             disable_web_page_preview=True)
                await asyncio.sleep(TIME_TO_SLEEP)
                await to_del.delete()
        elif i == 1:
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
