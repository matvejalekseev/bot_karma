hello = 'Добрый день, {name}\n'
start = 'Все доступные функции используются в определенных чатах, не обижайся'
help = start
error = 'Ошибка'
like = '''\
{name} - молодец!
Добавим в карму добра!
'''
dislike = '{name}, ну как так то? Ну сколько можно?'
new_chat = '''\
Рад приветсвовать всех в чате *{name}*

Нас тут *{count}*
'''
karma = '''\
Вот такая ситуация в чате *{name}*

{text}
'''
like_keyboard = 'Кого будем хвалить?'
dislike_keyboard = 'Кто себя плохо вёл?'
only_admin = 'Только администратор'
admin_not_me = 'Кто, кто, но только не я'
admin_not_admin = 'Кто, кто, но только не главный админ'
new_admin = 'А у нас новый админ - {name}'
delete_admin = 'Ну значит за дело - {name}'
bye = 'Прощай {name}'
admin_list = '''\
Список админов

{text}
'''
user_list = '''\
Список пользователей
{text}
'''
user_chat_list = '''\
*{name}*
{text}
'''
user_karma = '{name} *{karma}*\n'

MESSAGES = {
        'hello': hello,
        'start': start,
        'help': help,
        'error': error,
        'like': like,
        'dislike': dislike,
        'new_chat': new_chat,
        'karma': karma,
        'like_keyboard': like_keyboard,
        'only_admin': only_admin,
        'dislike_keyboard': dislike_keyboard,
        'admin_not_me': admin_not_me,
        'new_admin': new_admin,
        'admin_not_admin': admin_not_admin,
        'delete_admin': delete_admin,
        'admin_list': admin_list,
        'bye': bye,
        'user_list': user_list,
        'user_chat_list': user_chat_list,
        'user_karma': user_karma,
}







