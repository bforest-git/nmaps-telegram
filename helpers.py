from telegram import ReplyKeyboardMarkup, Update
from config import main_menu
from phrases import MENU_SUBSCRIBE, MENU_UNSUBSCRIBE


def get_keyboard(_update: Update, subscribed: bool) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(main_menu.copy(),
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    if subscribed:
        keyboard.keyboard.append([MENU_UNSUBSCRIBE])
    else:
        keyboard.keyboard.append([MENU_SUBSCRIBE])
    return keyboard
