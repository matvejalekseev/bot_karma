from aiosocksy import Socks5Auth

#Не забудь переименовать в conf.py
#Основыне режимы
mode = "test" #или "prom"
use_proxy = False# или True
#Настройки
#Токен бота
telegrambot_test = "token bot for test"
telegrambot_prom = "token bot for prom"
#Настройка файла БД
db_filename_test = "db file name example test_database.db for test"
db_filename_prom = "db file name example prom_database.db for prom"
#Токен бота для приема платежей
payments_test = "payments token bot for test"
payments_prom = "payments token bot for prom"
#Файл для вывода логов
log_filename_test = "log file name example test.log for test"
log_filename_prom = "log file name example prom.log for prom"

#Идентификатор личных сообщений в integer
MY_ID = 1
#Данные главного админа
MY_NAME = "Name"
MY_USERNAME = "Username"
#Путь до папки с медиа бота
MEDIA_DIRECTORY = "./media"
#Путь до папки с логом
LOG_DIRECTORY = "./logs"

#Настройка proxy
proxy_url = 'socks5://ip:port'
proxy_login = 'login'
proxy_password = 'password'

#По use_proxy настраиваем работу с прокси
if use_proxy:
    PROXY_URL = proxy_url
    PROXY_AUTH = Socks5Auth(login=proxy_login, password=proxy_password)
else:
    PROXY_URL = None
    PROXY_AUTH = None

#По mode(Тест/Пром) выставляем значения настроек
if mode == "prom":
    TOKEN = telegrambot_prom
    PAYMENTS_PROVIDER_TOKEN = payments_prom
    DB_FILENAME = db_filename_prom
    LOG_FILENAME = os.path.join(LOG_DIRECTORY, log_filename_prom)
else:
    TOKEN = telegrambot_test
    PAYMENTS_PROVIDER_TOKEN = payments_test
    DB_FILENAME = db_filename_test
    LOG_FILENAME = os.path.join(LOG_DIRECTORY, log_filename_test)