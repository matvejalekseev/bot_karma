from sqlalchemy import create_engine
from conf import DB_FILENAME, LOG_FILENAME, LOG_DIRECTORY, MY_ID, MY_USERNAME, MY_NAME
import os
from db_map import Base
from db_map import Users
from sqlalchemy.orm import scoped_session, sessionmaker

#Создаем папку для лога
if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

#Создаем файл для лога
if LOG_FILENAME:
    if not os.path.isfile(f'./{LOG_FILENAME}'):
        f = open(LOG_FILENAME, 'w+')

#Настрйока для SQLite3
engine = create_engine(f'sqlite:///{DB_FILENAME}')

#Создаем файл для базы данных
if not os.path.isfile(f'./{DB_FILENAME}'):
    Base.metadata.create_all(engine)

    #Заполнение базы справочниками
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    # Добавление администратора
    admin = Users(user_id=MY_ID, status=1, name=MY_NAME, username=MY_USERNAME)

    Session.add(admin)

    Session.commit()

    # Закрываем сессию
    Session.close()