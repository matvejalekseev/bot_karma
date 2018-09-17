import os
import asyncio
import logging
from aiogram import Bot
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from db_map import MediaIds, MediaTypes
from conf import TOKEN, MY_ID, DB_FILENAME, MEDIA_DIRECTORY, LOG_FILENAME

engine = create_engine("sqlite:///" + DB_FILENAME)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

bot = Bot(token=TOKEN)

async def uploadMediaFiles(folder, method, file_attr):
    if Session.query(MediaTypes).filter(MediaTypes.name == file_attr).all():
        folder_path = os.path.join(MEDIA_DIRECTORY, folder)
        for filename in os.listdir(folder_path):
            if filename.startswith('.'):
                continue
            logging.info('Started processing ' + filename)
            with open(os.path.join(folder_path, filename), 'rb') as file:
                if Session.query(MediaIds).filter(MediaIds.filename == filename).join(MediaTypes,
                                MediaTypes.id == MediaIds.type).filter(MediaTypes.name == file_attr).all():
                    logging.info('File ' + filename + ' intype ' + file_attr + ' already exists')
                else:
                    msg = await method(MY_ID, file, disable_notification=True)
                    if file_attr == 'photo':
                        file_id = msg.photo[-1].file_id
                    else:
                        file_id = getattr(msg, file_attr).file_id
                    session = Session()
                    type = Session.query(MediaTypes).filter(MediaTypes.name == file_attr).one()
                    newItem = MediaIds(file_id=file_id, filename=filename, type=type.id)
                    try:
                        session.add(newItem)
                        session.commit()
                    except Exception as e:
                        logging.error('Couldn\'t upload {}. Error is {}'.format(filename, e))
                    else:
                        logging.info('Successfully uploaded and saved to DB file ' + filename + ' with id ' + file_id)
                    finally:
                        session.close()
    else:
        logging.error('Wrong type in ' + folder + ' folder')

loop = asyncio.get_event_loop()

tasks = [
    loop.create_task(uploadMediaFiles('pics', bot.send_photo, 'photo')),
    loop.create_task(uploadMediaFiles('videos', bot.send_video, 'video')),
    loop.create_task(uploadMediaFiles('files', bot.send_document, 'document')),
    loop.create_task(uploadMediaFiles('ogg', bot.send_voice, 'voice'))
]

wait_tasks = asyncio.wait(tasks)

loop.run_until_complete(wait_tasks)
loop.close()
Session.remove()