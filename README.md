# Установка
Python 3.6 - https://www.python.org</br>
```wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tgz```
```tar -xvf Python-3.6.3.tgz```
```cd Python-3.6.3```
```./configure```
```make```
```make install```
```python3.6 -V```

SQLAlchemy - http://www.sqlalchemy.org/</br>
```pip3.6 install -U SQLAlchemy```

aiogram - https://aiogram.readthedocs.io/en/latest/index.html</br>
```pip3.6 install -U aiogram```

aiosocksy - https://pypi.org/project/aiosocksy/</br>
```pip3.6 install -U aiosocksy```

# Первый запуск
Настройка файла conf.py шаблон - conf_template.py</br>
```nano conf_template.py```</br>
Выполнение инициализирующего скрипта</br>
```python3 init.py```</br>
Выполнение загрузки медиа</br>
```python3 upload_media.py```</br>