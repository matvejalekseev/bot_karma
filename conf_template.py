#Не забудь переименовать в conf.py
mode = "test" # или "prom"
telegrambot_test = "token bot for test"
telegrambot_prom = "token bot for prom"
payments_test = "payments token bot for test"
payments_prom = "payments token bot for prom"
db_filename_test = "db file name example test_database.db for test"
db_filename_prom = "db file name example prom_database.db for prom"
log_filename_test = "log file name example test.log for test"
log_filename_prom = "log file name example prom.log for prom"

#По mode(Тест/Пром) выставляем значения настроек
if mode == "prom":
    TOKEN = telegrambot_prom
    PAYMENTS_PROVIDER_TOKEN = payments_prom
    DB_FILENAME = db_filename_prom
    LOG_FILENAME = log_filename_prom
else:
    TOKEN = telegrambot_test
    PAYMENTS_PROVIDER_TOKEN = payments_test
    DB_FILENAME = db_filename_test
    LOG_FILENAME = log_filename_test

#Идентификатор личных сообщений в integer
MY_ID = 1
#Путь до папки с медиа бота
MEDIA_DIRECTORY = "./media"
#Путь до папки с логом
LOG_DIRECTORY = "./logs"