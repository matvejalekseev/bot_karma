from aiogram.utils.helper import Helper, HelperMode, ListItem


class AdminStates(Helper):
    mode = HelperMode.snake_case

    #add new chat
    STATE_NEW_CHAT = ListItem()


