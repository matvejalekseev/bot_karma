hello = 'Добрый день, {name}\n'
start = 'Все доступные функции используются в определенных чатах, не обижайся'
help = start
error = 'Ошибка'
joke_another_type = 'Только gif и картинки'
like = '''\
{name} - молодец!
Добавим в карму добра!
'''
dislike = '{name}, ну как так то? Ну сколько можно?'
new_chat = '''\
Рад приветсвовать всех в чате <b>{name}</b>

Нас тут <b>{count}</b>

Давайте знакомиться и все дружно нажмём {command}
'''
karma = '''\
Вот такая ситуация в чате <b>{name}</b>

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
chat_list = '''\
Список чатов
{text}
'''
user_chat_list = '''\
*{name}*
{text}
'''
user_karma = '{name} <b>{karma}</b>\n'
super_admin_commands = '''\
Ты главный админ и можешь добавлять бота в другие чаты и использовать команды:
/admin - Назначить админа, просто сделай reply сообщения пользователя, которого хочешь сделать админом, отправив команду /admin@{username}
/admins - Посмотреть всех админов
/users - Посмотреть всех пользователей во всех чатах
/admin_delete - Разжаловать админа, просто сделай reply сообщения пользователя, которого хочешь разжаловать, отправив команду /admin_delete@{username}
'''
admin_commands = '''\
Ты админ и можешь добавлять бота в другие чаты и использовать команды:
/admin - Назначить админа, просто сделай reply сообщения пользователя, которого хочешь сделать админом, отправив команду /admin@{username}
/admin_delete - Разжаловать админа, просто сделай reply сообщения пользователя, которого хочешь разжаловать, отправив команду /admin_delete@{username}
'''

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
        'super_admin_commands': super_admin_commands,
        'admin_commands': admin_commands,
        'chat_list': chat_list,
        'joke_another_type': joke_another_type,
}







