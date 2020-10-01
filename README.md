# Установка
Python 3.6 - https://www.python.org</br>
```wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tgz```</br>
```tar -xvf Python-3.6.3.tgz```</br>
```cd Python-3.6.3```</br>
```./configure```</br>
```make```</br>
```make install```</br>
```python3.6 -V```</br>

SQLAlchemy - http://www.sqlalchemy.org/</br>
```pip3.6 install -U SQLAlchemy```

aiogram - https://aiogram.readthedocs.io/en/latest/index.html</br>
```pip3.6 install -U aiogram```

aiosocksy - https://pypi.org/project/aiosocksy/</br>
```pip3.6 install -U aiosocksy```

flask - http://flask.pocoo.org/</br>
```pip3.6 install -U flask```

bs4</br>
```pip3.6 install -U bs4```

# Первый запуск
Настройка файла conf.py шаблон - conf_template.py</br>
```nano conf_template.py```</br>
Выполнение инициализирующего скрипта</br>
```python3 init.py```</br>
Добавление в базу индексов:</br>
```CREATE UNIQUE INDEX votings_index_ids on Votings (id);```</br>
```CREATE UNIQUE INDEX votes_index_ids on Votes (id);```</br>
```CREATE UNIQUE INDEX chats_index_ids on Chats (id);```</br>
```CREATE UNIQUE INDEX karma_index_ids on Karma (id);```</br>
```CREATE UNIQUE INDEX triggers_index_ids on Triggers (id);```</br>
```CREATE UNIQUE INDEX users_index_ids on Users (id);```</br>
```CREATE UNIQUE INDEX users_index_user_ids on Users (user_id);```</br>
```CREATE UNIQUE INDEX triggers_index_name_chat_ids on Triggers (name, chat_id);```</br>

DICT для списка слов формируется вот так:</br>
```
import requests
rs = requests.get('http://www.7english.ru/dictionary.php?id=2000&letter=all')

from bs4 import BeautifulSoup
root = BeautifulSoup(rs.content, 'html.parser')

en_ru_items = []
en_items = []

for tr in root.select('tr'):
    # У строк в таблице перевода есть аттрибут onmouseover
    if 'onmouseover' not in tr.attrs:
        continue

    td_list = [td.text.strip() for td in tr.select('td')]

    # Количество ячеек в таблице со словами -- 9
    if len(td_list) != 9 or not td_list[1] or not td_list[5]:
        continue

    en = td_list[1]

    # Русские слова могут быть перечислены через запятую 'ты, вы',
    # а нам достаточно одного слова
    # 'ты, вы' -> 'ты'
    ru = td_list[5].split(', ')[0]

    en_ru_items.append((en, ru))
    en_items.append(en)

print(en_items)
```
