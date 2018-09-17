from sqlalchemy import create_engine
from conf import DB_FILENAME, LOG_FILENAME, LOG_DIRECTORY, MEDIA_DIRECTORY, MY_ID
import os
from db_map import Base
from db_map import MediaTypes, Users
from sqlalchemy.orm import scoped_session, sessionmaker

#Создаем папку для лога
if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

#Создаем папку для медиа
if not os.path.exists(MEDIA_DIRECTORY):
    os.makedirs(MEDIA_DIRECTORY)
if not os.path.exists(os.path.join(MEDIA_DIRECTORY, "pics")):
    os.makedirs(os.path.join(MEDIA_DIRECTORY, "pics"))
if not os.path.exists(os.path.join(MEDIA_DIRECTORY, "videos")):
    os.makedirs(os.path.join(MEDIA_DIRECTORY, "videos"))
if not os.path.exists(os.path.join(MEDIA_DIRECTORY, "files")):
    os.makedirs(os.path.join(MEDIA_DIRECTORY, "files"))
if not os.path.exists(os.path.join(MEDIA_DIRECTORY, "ogg")):
    os.makedirs(os.path.join(MEDIA_DIRECTORY, "ogg"))

#Создаем файл для лога
if not os.path.isfile(f'./' + LOG_FILENAME):
    f = open(LOG_FILENAME, 'w+')

#Настрйока для SQLite3
engine = create_engine(f'sqlite:///{DB_FILENAME}')

#Создаем файл для базы данных
if not os.path.isfile(f'./{DB_FILENAME}'):
    Base.metadata.create_all(engine)

    #Заполнение базы справочниками
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    #Справочник типов Медиа сообщений
    video = MediaTypes(name='video')
    pic = MediaTypes(name="photo")
    file = MediaTypes(name="document")
    ogg = MediaTypes(name="voice")

    Session.add(video)
    Session.add(pic)
    Session.add(file)
    Session.add(ogg)

    Session.commit()

    # Добавление администратора
    admin = Users(user_id=MY_ID, status=1, name='Алексеев Матвей', username='alekseevmatvej')

    Session.add(admin)

    Session.commit()

    # Закрываем сессию
    Session.close()